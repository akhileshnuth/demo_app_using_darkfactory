import json
import zipfile
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from accounts.models import ActivityLog
from .models import Document, document_today


EXPORT_FORMAT = "vault-json"
EXPORT_VERSION = 1
EXPORT_FILENAME = "vault-export.zip"
MANIFEST_FILENAME = "manifest.json"
DEFAULT_MAX_DOCUMENTS = 10_000
DEFAULT_MAX_EXPORT_SIZE = 10 * 1024 * 1024


class VaultExportError(Exception):
    """Raised when a complete vault export cannot be prepared."""


class DocumentAccessError(Exception):
    """Raised when a protected document cannot be safely accessed."""


def _audit_document_access(document_reference, user, allowed, reason):
    try:
        ActivityLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            event_type=(
                ActivityLog.EventType.DOCUMENT_ACCESS_ALLOWED
                if allowed else ActivityLog.EventType.DOCUMENT_ACCESS_DENIED
            ),
            description=f"Document access {'allowed' if allowed else 'denied'}: {reason}",
            document_reference=str(document_reference),
            context={"outcome": "allow" if allowed else "deny", "reason": reason},
        )
    except Exception as error:
        raise DocumentAccessError("The access decision could not be audited.") from error


def authorize_document_access(document_id, user):
    """Return a document only when its current policy and lifecycle allow it."""
    document = Document.objects.filter(pk=document_id).prefetch_related("collaborators").first()
    if document is None:
        _audit_document_access(document_id, user, False, "unresolved")
        raise DocumentAccessError("Document unavailable.")
    authenticated = getattr(user, "is_authenticated", False)
    allowed = authenticated and document.is_available() and (
        user.pk == document.owner_id or document.collaborators.filter(pk=user.pk).exists()
    )
    if not allowed:
        _audit_document_access(document.pk, user, False, "policy")
        raise DocumentAccessError("Document unavailable.")
    _audit_document_access(document.pk, user, True, "policy")
    return document


def save_uploaded_document(form, user):
    upload = form.cleaned_data.get("content")
    if upload is None or upload.size > getattr(settings, "DOCUMENT_UPLOAD_MAX_BYTES", 10 * 1024 * 1024):
        raise DocumentAccessError("A valid document upload is required.")
    document = form.save(commit=False)
    document.owner = user
    document.protection_status = Document.ProtectionStatus.PENDING
    try:
        with transaction.atomic():
            document.save()
            form.save_m2m()
            if not document.content:
                raise DocumentAccessError("The document was not stored.")
            document.protection_status = Document.ProtectionStatus.READY
            document.save(update_fields=["protection_status", "updated_at"])
    except Exception:
        if document.pk and document.content:
            document.content.delete(save=False)
        if document.pk:
            document.delete()
        raise
    return document


def cleanup_expired_documents():
    documents = Document.objects.filter(
        expiry_date__lt=document_today(),
        protection_status=Document.ProtectionStatus.READY,
    )
    count = 0
    for document in documents:
        if document.content:
            document.content.delete(save=False)
        document.content = None
        document.protection_status = Document.ProtectionStatus.DELETED
        document.save(update_fields=["content", "protection_status", "updated_at"])
        count += 1
    return count


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _document_data(document):
    return {
        "id": document.pk,
        "title": document.title,
        "notes": document.notes,
        "expiry_date": _json_value(document.expiry_date),
        "created_at": _json_value(document.created_at),
        "updated_at": _json_value(document.updated_at),
        "category": {
            "id": document.category_id,
            "name": document.category.name,
            "description": document.category.description,
        },
        "subject": {
            "id": document.subject_id,
            "name": document.subject.name,
            "description": document.subject.description,
        },
        "document_type": {
            "id": document.document_type_id,
            "name": document.document_type.name,
            "description": document.document_type.description,
        },
    }


def _validate_archive(content):
    try:
        with zipfile.ZipFile(BytesIO(content), "r") as archive:
            if archive.testzip() is not None:
                raise VaultExportError("The generated export failed its integrity check.")
            if archive.namelist() != [MANIFEST_FILENAME]:
                raise VaultExportError("The generated export has an invalid package.")
            manifest = json.loads(archive.read(MANIFEST_FILENAME))
            if (
                manifest.get("format") != EXPORT_FORMAT
                or manifest.get("version") != EXPORT_VERSION
                or not isinstance(manifest.get("documents"), list)
            ):
                raise VaultExportError("The generated export has an invalid manifest.")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise VaultExportError("The generated export failed validation.") from error


def build_vault_export(user):
    """Build and validate one complete, owner-scoped vault snapshot in memory."""
    max_documents = getattr(settings, "VAULT_EXPORT_MAX_DOCUMENTS", DEFAULT_MAX_DOCUMENTS)
    max_size = getattr(settings, "VAULT_EXPORT_MAX_SIZE", DEFAULT_MAX_EXPORT_SIZE)
    documents = list(
        Document.objects.filter(owner=user)
        .select_related("category", "subject", "document_type")
        .order_by("pk")
    )
    if len(documents) > max_documents:
        raise VaultExportError("This vault is too large to export. Please retry later.")

    manifest = {
        "format": EXPORT_FORMAT,
        "version": EXPORT_VERSION,
        "documents": [_document_data(document) for document in documents],
    }
    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_FILENAME, payload)
    content = buffer.getvalue()
    if len(content) > max_size:
        raise VaultExportError("This vault export is too large to download. Please retry later.")
    _validate_archive(content)
    return content
