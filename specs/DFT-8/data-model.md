# DFT-8 Data Model

## Category, Subject, and DocumentType

Each is a shared taxonomy entity with:

- `id` primary key
- `name` required, bounded string, globally unique and rejected case-insensitively
- optional `description`
- `created_at` and `updated_at`
- deterministic name ordering

They have a one-to-many reverse relationship from `Document`. A referenced row
cannot be deleted (`PROTECT`). Taxonomy writes require staff or superuser
authorization; authenticated users may read choices.

## Document

`Document` is a metadata-only record with:

- `owner` → `AUTH_USER_MODEL`, `CASCADE`
- required `title`, owner-scoped case-insensitive uniqueness
- optional `notes`
- required `category`, `subject`, and `document_type` FKs, each `PROTECT`
- existing optional `expiry_date` and `reminder_sent_at` fields, unchanged
- `created_at` and `updated_at`, ordered by latest update

No file field, content blob, or upload reference is introduced.

## Invariants and transitions

1. Taxonomy names are nonblank and nonduplicated within their own collection.
2. A document cannot save with missing/stale classification or without an owner.
3. Owner filtering makes another user's document indistinguishable from missing
   (404 on detail/edit/delete); taxonomy is shared.
4. Referenced taxonomy deletion is rejected without changing either record.
5. Document create/update is atomic from the user's perspective: form validation
   and database race handling occur before success redirect.
6. Expiry reminder scheduling continues to use `expiry_date` and
   `reminder_sent_at`; CRUD updates must not reset reminder state unless the
   existing reminder policy explicitly requires it.

## Migration guidance

Inspect the live schema and existing migration history before generating the
next migration. Preserve existing rows and expiry/reminder columns; use a
data-safe migration for any field-size or constraint alignment required by the
approved model. If existing taxonomy names conflict case-insensitively, fail
with a clear remediation message for human resolution rather than silently
merging or renaming rows. Do not edit historical migrations.
