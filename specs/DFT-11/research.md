# Research: Export and Download Vault Data

## Decision 1: Versioned ZIP package with JSON members

**Decision**: Publish `vault-export.zip` containing `manifest.json` and
`documents.json`, encoded as UTF-8. The manifest declares `format: vault-export`,
`schema_version: 1`, UTC creation/snapshot timestamps, owner identity needed to
identify the export, document count, `attachments: false`, and member byte
length/SHA-256 values. `documents.json` is a JSON array.

**Rationale**: The current vault is metadata-only. JSON preserves null dates,
timestamps, and related taxonomy values more clearly than CSV; ZIP provides one
portable file and leaves room for future members without exporting database
internals. Python's standard library is sufficient.

**Included fields**: each document includes `id`, `title`, `notes`,
`expiry_date`, `reminder_sent_at`, `created_at`, `updated_at`, `owner_id`, and
the related category, subject, and document-type `id`/`name`. No attachment,
password, session, profile, activity-log, credential, or derived “expired” data
is included. The manifest explicitly states attachments are not included.

**Alternatives considered**: CSV is less faithful for nullable/timezone-aware
values; Django fixtures expose implementation details; SQLite backup includes
other users and tables; a single JSON file is simpler but less extensible;
YAML/MessagePack add dependency or portability costs.

## Decision 2: Synchronous, bounded, in-memory lifecycle

**Decision**: Generate the complete archive in `io.BytesIO` during the
authenticated request. Materialize and serialize the owner-scoped queryset,
close the ZIP, validate members/counts/hashes, then return a `FileResponse`.
Apply a configurable maximum record/serialized size and fail explicitly when it
would be exceeded. Retain no server-side export artifact.

**Rationale**: The repository has no worker, broker, media/export storage, or
retention configuration, and the existing model has no attachments. In-memory
generation avoids security-zone writes and cleanup races. Building before HTTP
headers prevents a preparation exception from being presented as a successful
partial download.

**Alternatives considered**: Persistent/asynchronous exports would require an
export model, private storage outside zones, atomic promotion, expiry and
cleanup, and worker infrastructure. Streaming while creating a ZIP can emit
headers before the archive is finalized and can misrepresent a later failure.
These are future scale options if measured vault size exceeds the configured
bound.

## Decision 3: Consistent owner-scoped snapshot

**Decision**: Within a database transaction, capture a UTC `snapshot_at` and
fully materialize `Document.objects.filter(owner=request.user)` with
`select_related("category", "subject", "document_type", "owner")`. Serialize
that materialized set only; do not query unscoped data and filter in Python.

**Rationale**: This defines the export as one committed read snapshot rather
than a mixture of separately observed states, while enforcing isolation at the
query boundary. The snapshot timestamp is documented in the manifest.

**Alternatives considered**: Independent queries risk mixed state; a database
backup exports unrelated data and is not a user-facing format.

## Decision 4: Download and error controls

**Decision**: Keep the existing authenticated `/export/` route, add a visible
export action to the document list, return `application/zip` with a fixed safe
attachment name, `Content-Length`, `Cache-Control: no-store`, and
`X-Content-Type-Options: nosniff`. On generation/limit/validation failure,
return a normal actionable error response without attachment headers and log
only safe operational metadata.

**Rationale**: A synchronous response does not need a separate export ID or
download endpoint. `LoginRequiredMixin` denies anonymous requests, and the
owner-scoped query prevents cross-user disclosure. No generated file remains
available after the response lifecycle.

**Alternatives considered**: Persistent opaque export IDs and status endpoints
are appropriate for asynchronous large exports but add retention and cleanup
decisions that are not justified by the current metadata-only application.

## Decision 5: Security-zone treatment

The repository's declared zone documentation is stale relative to its Django
paths, so this plan does not expand or rewrite zone declarations. It avoids the
risk by never writing generated vault data to disk, including temporary files,
media, or repository paths. HTTPS/deployment protection remains an operational
requirement, and no export contents are logged.
