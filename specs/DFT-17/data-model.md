# Data Model: Protect Uploaded Documents

## Document (`vault.Document`)

Retain existing metadata and add:

- `storage_name`: nullable/blank opaque private-storage key; never a user path or public URL.
- `original_filename`: bounded display-only name, sanitized for response headers.
- `content_type`: bounded validated MIME value, used conservatively for response metadata.
- `content_size`: non-negative stored byte count.
- `content_sha256`: optional integrity checksum calculated while saving.
- `protection_state`: choices such as `legacy`, `pending`, `ready`, `expired`, `quarantined`, `deleted`.
- `protection_version` and `protection_error`: operational migration/protection metadata without content.

Owner remains required. A document is retrievable only when owner exists, state is `ready`, policy resolves, storage reference exists, the file opens, and `expiry_date` is absent or not before `timezone.localdate()`.

## DocumentCollaborator (`vault.DocumentCollaborator`)

- `document`: required foreign key to `Document`, cascading on document deletion.
- `user`: required foreign key to the custom account user, protected or restricted according to existing account-deletion policy.
- `created_at`: audit-friendly association timestamp.
- Unique constraint on `(document, user)`.

The owner is implicitly allowed and should not be duplicated as a collaborator. Form/service validation rejects inactive, missing, duplicate, or owner collaborators. Policy is evaluated from current database rows, not cached permissions.

## ActivityLog (`accounts.ActivityLog`)

Retain existing user activity fields and add/alter:

- `user`: nullable FK with `SET_NULL`; null means anonymous/unresolved requester.
- `event_type`: `DOCUMENT_ACCESS_ALLOWED` and `DOCUMENT_ACCESS_DENIED` choices.
- `document_reference`: nullable opaque document identifier; null is allowed for malformed/unresolvable identifiers.
- `actor_context`: bounded choices/values such as `authenticated`, `anonymous`, `unresolved`.
- Existing short `description`: generic reason/outcome only, never content, title, filename, path, token, or sensitive metadata.

All access outcomes are written before an allowed response streams. Failed audit persistence fails closed. Existing per-user activity views remain scoped to non-null current users; admin/operator inspection includes anonymous rows.

## State transitions

```text
legacy -> pending -> ready
pending -> quarantined (failure/cleanup)
ready -> expired (expiry enforcement/cleanup)
ready -> deleted (deletion; bytes removed or quarantined)
any unavailable state -> pending (explicit retry/re-protection only)
```

No unavailable state may be served. Filesystem cleanup is idempotent and must tolerate missing files. Database rows are not made `ready` until the private write and integrity checks succeed.

## Validation and invariants

- Upload requires authenticated owner, valid metadata, a bounded non-empty file, and a complete collaborator policy before storage is committed.
- Generated storage names cannot contain user-controlled path segments; storage root is not static/public and has restrictive permissions.
- Retrieval does not accept a storage name or filesystem path from the caller.
- Expired/deleted/corrupt/missing/unprotected documents use the same authenticated 404 response.
- Audit rows contain no document bytes or sensitive document data.
- Legacy rows and unresolved inventory items remain unavailable until explicitly re-protected and verified.
