import json
import zipfile
from datetime import date, datetime
from io import BytesIO

from django.conf import settings

from .models import Document


EXPORT_FORMAT = "vault-json"
EXPORT_VERSION = 1
EXPORT_FILENAME = "vault-export.zip"
MANIFEST_FILENAME = "manifest.json"
DEFAULT_MAX_DOCUMENTS = 10_000
DEFAULT_MAX_EXPORT_SIZE = 10 * 1024 * 1024


class VaultExportError(Exception):
    """Raised when a complete vault export cannot be prepared."""


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
