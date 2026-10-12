# Implementation Plan: Document Vault Core — Categories, Subjects, Types & Documents

**Branch**: `DFT-8-document-vault-core` | **Date**: 2026-10-12 | **Spec**: [`./specs/DFT-8/spec.md`](spec.md)

## Summary

Extend the existing Django `vault` app in place (the current app is only a
list/export foundation; CRUD routes and views are still net-new). Add
staff/administrator-managed
CRUD for shared `Category`, `Subject`, and `DocumentType` records, plus
authenticated owner-scoped metadata CRUD for `Document`. Preserve the existing
`expiry_date`, `reminder_sent_at`, export, pagination, and scheduled reminder
behavior. Documents remain metadata-only: no upload, content reference, or new
storage dependency. Make `/vault/` canonical and redirect legacy
`/vault/documents/` list requests to it.

## Technical Context

- **Stack**: Python 3.11+, Django 5.2 (`Django~=5.2`), SQLite development/test DB.
- **Dependencies**: Django built-ins only; no new runtime dependency or approval request.
- **Existing integration**: `vault` is already installed and included from `config/`; `accounts.User` is `AUTH_USER_MODEL`; reminder command consumes existing document expiry fields.
- **Authorization**: logged-in users manage their own documents; `is_staff` or `is_superuser` users manage shared taxonomy. Reuse Django auth; do not redesign accounts.
- **Persistence**: existing models/migrations are present. Implementer must add only the migration needed to align field constraints and lifecycle behavior, preserving existing data and reminder fields.
- **UI/API surface**: server-rendered HTML CBVs and forms, no JSON API. Contracts are in [`./specs/DFT-8/contracts/web-contracts.md`](contracts/web-contracts.md).
- **Testing**: extend the existing Django tests, including expiry, pagination, and export regressions. The implementation agent runs `python manage.py check` and `python manage.py test` locally.
- **Unknowns resolved**: file payload is out of scope; exact supported formats/size limits therefore do not apply. Taxonomy deletion uses referential protection. Existing expiry behavior is retained. Canonical list URL is `/vault/`.

## Constitution Check

- **I — Complete Spec-Kit pipeline**: PASS. This plan supplies Phase 0 and Phase 1 outputs; Tasks, Analyze, Implement, and human-gated merge remain required.
- **II — Declared security zones**: PASS with recorded deferral. Planned paths do not begin with protected `src/auth`, `src/payments`, or `src/customers`; `SECURITY_ZONES.md` is stale for the actual `accounts/` and `vault/` PII surfaces, so a human-gated mapping follow-up is required and is not part of this plan.
- **III — Human-gated merge**: PASS. Delivery is via reviewed PR to protected `main`.
- **IV — Test-first**: PASS for design. Functional implementation must add/update automated tests before delivery; no tests are created in this planning phase.
- **V — No novel dependencies**: PASS. Use only Django and the existing standard library.

**Post-design gate**: PASS with the same security-zone mapping deferral. No unresolved clarification remains and no planned change writes a protected path.

## Planned Changes

1. `vault/models.py` and a new migration: retain four entities, required one-to-many classification FKs with `PROTECT`, per-owner document ownership, case-insensitive taxonomy/name and per-owner title rules, and existing expiry/reminder fields. Do not add a file field.
2. `vault/forms.py`: required names/classifications, duplicate validation, expiry/reminder-compatible document editing (include `expiry_date`; keep `reminder_sent_at` system-managed), and server-side inline errors.
3. `vault/mixins.py`/`vault/views.py`: reusable staff gate returning HTTP 403 for unauthorized taxonomy writes, authenticated document owner scoping, CRUD/detail/filter behavior, safe `ProtectedError` handling, and duplicate-race handling without partial saves.
4. `vault/urls.py`: namespaced canonical document list at `/vault/`; redirect `/vault/documents/` only for the old list path while preserving document detail/create/edit/delete and export routes.
5. `templates/vault/*` and `templates/base.html`: taxonomy/document lifecycle screens, classification details, filters, expiry fields, inline errors, and navigation. Keep existing export/pagination affordances.
6. `vault/admin.py` and tests: preserve admin registrations and add coverage for authorization, CRUD, validation, isolation, referential integrity, route compatibility, expiry/reminders, pagination, and export regressions. Update existing tests that reverse the old list URL, and make implementation/test changes atomic so templates do not reference absent routes.

## Project Structure

```text
./specs/DFT-8/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/web-contracts.md

./vault/
├── models.py, forms.py, mixins.py, views.py, urls.py, admin.py
└── migrations/0003_*.py (planned schema migration)

./templates/vault/ and ./templates/base.html (planned UI changes)
./tests/ (planned implementation tests; not created by this plan)
```

## Complexity Tracking

| Violation/deferral | Why needed | Simpler alternative rejected because |
|---|---|---|
| Security-zone mapping deferral | Actual `accounts/` and `vault/` surfaces are not represented by the current template-default map | Updating zone files is human-gated and changing them during this feature would alter agent permissions mid-ticket. |
