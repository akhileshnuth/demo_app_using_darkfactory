# Document Access Contract

The vault exposes server-rendered Django endpoints; these are the externally observable contracts for the feature.

## Upload

- **Route**: `POST /documents/create/` (authenticated; multipart form)
- **Fields**: existing document metadata, `file`, and zero or more explicit collaborator user identifiers.
- **Success**: redirect to the owner's document list/detail only after the row is `ready` and the private object is verified.
- **Failure**: validation errors or a safe service failure; no pending/partial object may be retrievable.
- **Security**: CSRF protection, bounded upload/type validation, server-generated storage key; never render a public file URL.

## Protected retrieval

- **Route**: `GET /documents/<document-id>/download/`
- **Anonymous**: redirect to the configured login URL.
- **Authenticated authorized owner/collaborator**: stream original bytes with `FileResponse`, attachment disposition, safe filename, conservative content type, and `X-Content-Type-Options: nosniff`.
- **Authenticated unauthorized or unavailable**: `404` with the same non-disclosing body for missing, guessed, altered, pending, expired, deleted, legacy, corrupt, and inaccessible IDs.
- **Audit**: every resolvable or attempted decision records an allowed/denied `ActivityLog` event before an allowed stream. Audit failure never yields bytes.

## Lifecycle operations

- **Delete**: remove authorization/database availability first; remove or quarantine bytes via on-commit cleanup and retryable orphan cleanup.
- **Expiry**: deny immediately at request time; scheduled cleanup may transition state and remove/quarantine bytes.
- **Legacy inventory/re-protection**: management commands are read-only/dry-run by default for inventory, require an explicit recorded exposure decision for mutation, and never enable retrieval for unresolved items.

## Non-contractual implementation details

Storage paths, storage names, filesystem roots, migration diagnostics, and audit descriptions are not exposed to clients.
