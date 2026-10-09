# DFT-23 Research

## Model restoration

**Decision**: Restore `Checklist`, `ChecklistItem`, `ChecklistShare`,
`EmergencyContact`, `EmergencyAccessRequest`, and `Notification` in
`./checklists/models.py`. Match fields, foreign-key targets, delete behavior,
related names, choices, ordering, constraints, and helper API to
`./checklists/migrations/0001_initial.py` and `./specs/DFT-9/data-model.md`.
Restore the helpers already consumed by views/services/templates: checklist
counts/percentage/active shares; share status constants; notification type
constants; emergency status constants, `is_resolved`, guarded `resolve`; and
self-designation validation for emergency contacts.

**Rationale**: The migration defines the database schema, while application code
relies on model constants and methods. A schema-only reconstruction would still
leave runtime failures. Restoring the existing contract removes the crash without
new behavior.

**Alternatives considered**: Restoring only `Checklist`/`ChecklistShare` was
rejected because all six models are imported or referenced by existing flows.
Defensive optional-relation behavior was rejected by the approved clarification.
Rewriting the migration was rejected because it already defines the schema.

## Migration strategy

**Decision**: Do not create a migration initially. Run
`python manage.py makemigrations checklists --check`; create one only if Django
reports a genuine schema difference.

**Rationale**: `./checklists/migrations/0001_initial.py` already contains all six
tables, fields, relations, choices, ordering, and unique constraints. Methods and
properties do not alter schema.

## Test-file scope

**Decision**: Delete exactly these eight tracked files:

- `./accounts/tests.py`
- `./checklists/tests.py`
- `./dashboard/tests.py`
- `./vault/tests.py`
- `./tests/dashboard.test.js`
- `./tests/document_list.test.js`
- `./tests/export.test.js`
- `./overlays/node/tests/clamp.test.ts`

Retain `./overlays/node/vitest.config.ts`, package/configuration files, and all
non-test source. Re-check tracked files before deletion.

**Rationale**: This is the explicit DFT-23 convention: app-level `tests.py` and
recognized `.test.js`/`.test.ts` files. Configuration and runtime source are not
test files.

## Validation and security

Run `python manage.py check`, the migration drift check, and tracked-file scope
inspection. No tests are added and the approved end state contains none. Planned
paths do not match declared security prefixes in `./SECURITY_ZONES.md`.
