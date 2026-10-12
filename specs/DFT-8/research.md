# DFT-8 Research Decisions

## R1 — Existing repository shape

**Decision**: Extend the already-installed `vault` app and its existing models,
templates, migrations, pagination, export, and reminder command.

**Rationale**: The repository is beyond the original scaffold: `vault` already
has taxonomy/document models, expiry fields, `send_expiry_reminders`, export,
and pagination. Replacing those surfaces would risk data loss and regressions.

**Alternatives considered**: Creating a second app or rebuilding the app would
duplicate models/routes and break existing integrations.

## R2 — Document content

**Decision**: Metadata-only records. Keep title, notes, classification, owner,
timestamps, and existing expiry/reminder fields; add no file payload or content
reference.

**Rationale**: This is explicit in the approved clarification and avoids an
unapproved storage/format/size decision.

**Alternatives considered**: `FileField`, external object storage, or a content
reference are deferred to a separate feature.

## R3 — Authorization

**Decision**: All authenticated users may browse and manage their own documents.
Only `is_staff` or `is_superuser` users may create, update, or delete shared
taxonomy records; reads can remain available to authenticated users for form
selection and browsing.

**Rationale**: This directly implements the clarification using the existing
Django user flags without changing the accounts/security model.

**Alternatives considered**: New roles/permissions or a custom authorization
service would expand scope and introduce no requirement-backed benefit.

## R4 — Referential integrity

**Decision**: Classification FKs use `PROTECT`; taxonomy delete views catch the
result and render an actionable dependency error. Unreferenced taxonomy rows and
owner-owned documents can be removed.

**Rationale**: Prevents orphaned documents and accidental cascade deletion of
shared records.

**Alternatives considered**: `CASCADE` loses documents; `SET_NULL` violates the
required one-category/one-subject/one-type invariant.

## R5 — Uniqueness and atomic validation

**Decision**: Enforce required names and case-insensitive duplicate checks in
forms, retain database uniqueness/race guards, and validate all classifications
before saving. Document title uniqueness remains owner-scoped. Invalid requests
must not partially persist.

**Rationale**: Covers both user-facing validation and concurrent writes while
matching existing model/form conventions.

**Alternatives considered**: Database-only checks are not sufficiently clear for
case variants and produce poor form errors.

## R6 — Routing compatibility

**Decision**: `/vault/` is the canonical document list. `/vault/documents/`
redirects to the canonical route; document item routes remain under
`/vault/documents/<pk>/...`, and export remains available.

**Rationale**: Implements the approved canonical URL without breaking bookmarked
detail or existing export/list consumers.

**Alternatives considered**: Keeping the old list canonical conflicts with the
clarification; removing it breaks compatibility.

## R7 — Existing behavior preservation

**Decision**: Preserve `expiry_date`, `reminder_sent_at`, reminder command
semantics, pagination, owner filtering, and export contracts while adding CRUD.

**Rationale**: Explicit clarification requires expiry/reminder preservation, and
these are already shipped repository behavior.

**Alternatives considered**: Replacing the list/form wholesale risks silently
dropping expiry fields or existing query/export behavior.

## R8 — Security-zone gate

**Decision**: Do not modify `SECURITY_ZONES.md`, factory maps, or protected source
zones in this plan. Record that actual auth/PII paths need human mapping.

**Rationale**: The constitution makes security-zone changes human-gated; the
planned feature does not write the currently protected prefixes.

**Alternatives considered**: Silently treating the stale template paths as the
real map would hide a governance gap.

## R9 — Existing-data migration safety

**Decision**: Before adding database-level case-insensitive taxonomy constraints,
the implementation must audit existing taxonomy names. If conflicting case
variants exist, the migration must fail with an actionable message (or use a
human-approved deterministic merge); it must not silently rename or delete
records. Historical migrations remain immutable.

**Rationale**: The current database already contains taxonomy rows, and an
expression unique constraint can fail during migration when old data conflicts.

**Alternatives considered**: Silent first-row-wins cleanup risks changing document
classification and violates referential integrity.
