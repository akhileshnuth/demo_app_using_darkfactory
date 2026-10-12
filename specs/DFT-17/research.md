# Research: Protect Uploaded Documents

## Decision: Use private Django filesystem storage plus application streaming

**Rationale**: The repository has Django 5.2, no media storage, no retrieval endpoint, and only metadata on `Document`. Configure a dedicated storage root outside static/public serving, generate opaque server-side names, never expose `storage.url()` or a path, and return a `FileResponse` only after authorization. Django's storage and upload handlers already provide chunked I/O without a new dependency.

**Alternatives considered**: A public `FileField`/media URL was rejected because identifier or static access could bypass policy. Object storage and database BLOBs add configuration and operational complexity not approved by the constitution. Application-level encryption is a separate key-management decision, not required to close the identified access-path defect.

## Decision: Gate availability with explicit lifecycle state and two-phase cleanup

**Rationale**: Database transactions cannot atomically include filesystem writes. Create a pending row, write and verify the private object, then mark it ready; only ready rows can be retrieved. On failure delete the new object, and provide idempotent orphan/pending cleanup for process crashes. Deletion removes the authorization row first and schedules byte removal; expiry denies immediately on every request and cleanup removes or quarantines bytes.

**Alternatives considered**: Making a storage reference immediately downloadable was rejected because partial uploads could be exposed. Relying only on a scheduled expiry job was rejected because expiry must take effect at request time.

## Decision: Owner plus explicit collaborator relation is the access policy

**Rationale**: The clarification names the owner and explicitly listed per-document collaborators. A through model with a uniqueness constraint makes policy data explicit and lets retrieval query current policy on every request. Missing owner, policy, state, or storage reference fails closed.

**Alternatives considered**: Inheriting broad vault permissions or encoding collaborators in a free-form field was rejected because it is not an explicit, queryable per-document policy.

## Decision: Extend ActivityLog for anonymous, attributable document decisions

**Rationale**: `./accounts/models.py` is the existing audit destination. Make its actor FK nullable/`SET_NULL`, add document reference, actor context, and allowed/denied event types. Record the decision synchronously before an allowed stream begins; an audit write failure never permits content. Keep descriptions generic and omit titles, filenames, paths, tokens, and bytes.

**Alternatives considered**: Placeholder anonymous users pollute account identity; a second audit table duplicates the established destination; best-effort logging violates fail-closed requirements.

## Decision: Login redirect for anonymous requests and uniform 404 for authenticated failures

**Rationale**: Match the clarification and Django's existing `LoginRequiredMixin`/`LOGIN_URL`. Authenticated users receive the same non-disclosing 404 for unauthorized, missing, pending, expired, deleted, corrupt, or legacy-unavailable identifiers. The endpoint must not distinguish guessed IDs or alternate paths.

**Alternatives considered**: 403 or existence-specific errors leak resource state and were rejected.

## Decision: Default-deny legacy rollout with explicit inventory and exposure decision

**Rationale**: Existing `Document` rows have no bytes/reference and no current retrieval endpoint. Before enabling retrieval, inventory rows and all deployment storage/access paths, record an exposure-handling decision, quarantine/delete or re-protect legacy bytes, verify protected replacements, and leave unresolved items unavailable. Bulk movement belongs in resumable management commands, not schema migrations.

**Alternatives considered**: Backfilling in a migration or serving legacy files during rollout was rejected because migrations are not suitable for bulk I/O and legacy serving would preserve the exposure.

## Resolved implementation unknowns

- Storage: private local filesystem root supplied by deployment configuration; no static/media URL.
- Retrieval: one application endpoint streams only after current authorization, state, expiry, and successful audit.
- Upload: multipart `DocumentForm` with bounded file validation and explicit collaborators.
- Expiry: request-time deny using `timezone.localdate()`, with idempotent cleanup command.
- Audit: existing `ActivityLog`, nullable actor and non-content context fields.
- Testing: Django test runner and repository test layout; implementation must add security acceptance coverage.
