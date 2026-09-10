# Implementation Plan: Document Vault Core — Categories, Subjects, Types & Documents

**Branch**: `DFT-8-document-vault-core` | **Date**: 2026-09-09 | **Spec**: [`/specs/DFT-8/spec.md`](spec.md)

**Input**: Feature specification from `/specs/DFT-8/spec.md`

## Summary

Add a new `vault` Django app to the existing DFT-7 scaffold that provides a
document vault with four CRUD entities: `Category`, `Subject`, `DocumentType`,
and `Document`. Categories, subjects, and types are shared organizational
taxonomies (name + optional description); documents are per-user metadata
records (title + notes) linked to one of each taxonomy entity via foreign key.
All views use Django's built-in class-based generics with `LoginRequiredMixin`,
`ModelForm`s with inline server-side validation errors, and server-rendered
templates consistent with the dashboard shell pattern.

The vault app sits alongside the existing `accounts` and `dashboard` apps. The
only cross-app touchpoints are: (1) `vault` registered in `INSTALLED_APPS`, (2)
vault URL patterns included in `config/urls.py`, (3) vault navigation links
added to `templates/base.html` sidebar, and (4) the Document model referencing
`settings.AUTH_USER_MODEL` for owner ownership. No novel runtime dependencies
beyond Django itself.

Research decisions ([`research.md`](research.md)) resolve all spec
clarifications: delete protection via `PROTECT` + `ProtectedDeleteMixin` (R1),
metadata-only documents (R2), three co-equal taxonomy models (R3), composite
per-owner title uniqueness with case-insensitive form checks + `IntegrityError`
race guards (R4, R5, R6), per-user document scoping via queryset filtering (R7),
and 17 namespaced routes under `vault:` (R10). Filtering and search use pure
queryset GET parameters (R11). Unauthenticated GETs redirect to login; POSTs
yield 405 per Django 5.2 (R12). No pagination, no optimistic locking, no file
uploads — all documented as explicit scope boundaries (R13).

## Technical Context

**Language/Version**: Python 3.11+ with Django 5.2 (`Django~=5.2` in
`requirements.txt`). SQLite for development and testing (Django default). The
factory sandbox ships Node only — Python must be installed locally by the
implementer; `manage.py test` is the SC-005 authority.

**Primary Dependencies**: Django 5.2 only. Uses `django.views.generic` (CBVs),
`django.forms.ModelForm`, `django.contrib.auth.mixins.LoginRequiredMixin`,
`django.urls.reverse_lazy`, `django.db` (`models`, `IntegrityError`,
`ProtectedError`), `django.contrib.admin` (FR-020). No third-party packages.
No novel runtime dependencies — autonomy-eligible under Constitution
Principle V.

**Storage**: SQLite (Django default) for dev and test, consistent with DFT-7.
The vault app uses standard Django ORM; no raw SQL, no special storage backends.

**Testing**: Django's bundled test runner (`python manage.py test`, in-memory
SQLite). Covers models (field constraints, uniqueness, relationships), views
(CRUD lifecycle, auth gating, per-user scoping, delete protection), forms
(case-insensitive duplicate rejection, required-field validation), and URL
resolution. Factory sandbox cannot execute Python tests (UNVERIFIED status per
R14).

**Target Platform**: Linux server; server-rendered Django templates, desktop
layout. No mobile/responsive requirements.

**Project Type**: web-service (server-rendered Django application). The vault is
a new Django app within the existing scaffold.

**Performance Goals**: No measurable performance targets. CRUD operations
completing within human-observable times (SC-001: full vault setup in <3 min).
No pagination in scope; ListView handles low-thousands of rows with
`Meta.ordering` (R13).

**Constraints**: CSRF enabled on all POST forms (FR-015). Authentication
enforced on all vault views via `LoginRequiredMixin` (FR-011). SECURITY_ZONES.md
still carries template defaults — vault `pii` zone mapping deferred to
human-gated follow-up (R15). Python tests cannot run in CI (UNVERIFIED).

**Scale/Scope**: Small feature. One new Django app (`vault`) with four models,
17 URL routes, ~8 templates, and a sidebar nav update. Approximately 400–600
lines of Python (models + views + forms + admin + tests) plus template HTML.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reviewed against `constitution.md`.

- **Principle I — Spec-Kit completeness**: Full pipeline in progress (Spec →
  Plan → Tasks → Implement). Research.md resolves all NEEDS CLARIFICATION
  items. **PASS**.

- **Principle II — Security zones declared**: `SECURITY_ZONES.md` declares
  template-default zones (`src/auth`, `src/payments`, `src/customers`) that do
  not match this repo's Django layout. The vault app introduces a
  user-generated-content surface (Document title/notes — PII). R15 in
  `research.md` maps the real surfaces (`accounts/` → `auth`/`pii`,
  `vault/` → `pii`) and records the deferral of `SECURITY_ZONES.md` update
  as human-gated follow-up. No declared zone currently matches `vault/` or
  `accounts/`, so agent writes are not denied. **PASS with recorded deferral**
  (same status as DFT-7; the vault code is the prerequisite for the zone
  update, which must happen after this ticket merges).

- **Principle III — Human-gated merge**: All changes land via PR to protected
  `main` with human review + CI. **PASS** (enforced at repo/factory level).

- **Principle IV — Test-first**: Functional changes ship with tests. The vault
  app includes tests for models, views, forms, and URL resolution covering all
  success criteria. Standard Django test runner is self-contained (no service
  deps). **PASS**, with caveat that CI cannot run Python tests in this factory
  (UNVERIFIED status — same as DFT-7).

- **Principle V — No novel dependencies**: No runtime deps beyond Django itself.
  `requirements.txt` stays `Django~=5.2`. **PASS**. Autonomy-eligible.

**Gate result (pre-research)**: **PASS with recorded deferral** on Principle II
(zone map update deferred to human follow-up after vault code exists).

**Gate result (post-design, re-check)**: **PASS with the same recorded
deferral**. All NEEDS CLARIFICATION items resolved in research.md. The vault
app introduces no new dependencies, no new security zone violations, and no
changes to the existing `accounts` or `dashboard` app code beyond a sidebar
template link addition.

## Project Structure

### Documentation (this feature)

```text
specs/DFT-8/
├── plan.md              # This file
├── research.md          # Phase 0 — all NEEDS CLARIFICATION resolved
├── data-model.md        # Phase 1 — entities, constraints, edge cases
├── quickstart.md        # Phase 1 — validation scenarios
├── contracts/           # Phase 1 — route/form contracts
│   └── web-contracts.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

The `vault` app is a new top-level Django app alongside `accounts` and
`dashboard`, matching the flat layout established in DFT-7. Templates follow the
existing `templates/<app>/` convention.

```text
vault/                              # NEW — Document Vault app (FR-001)
├── __init__.py
├── apps.py                         # VaultConfig
├── models.py                       # Category, Subject, DocumentType, Document
├── forms.py                        # CategoryForm, SubjectForm, DocumentTypeForm, DocumentForm
├── views.py                        # 17 CBVs: CRUD for 4 entities + filter mixin
├── urls.py                         # app_name = "vault"; 17 routes (R10)
├── admin.py                        # Admin registrations for all 4 models (FR-020)
├── mixins.py                       # OwnerQuerysetMixin, ProtectedDeleteMixin
├── migrations/
│   └── __init__.py                 # + 0001_initial.py (auto-generated)
└── tests.py                        # Models, views, forms, URL tests (SC-005)

templates/
├── base.html                       # MODIFIED — sidebar gains vault nav links (FR-018)
├── vault/                          # NEW — vault templates
│   ├── category_list.html          # Shared taxonomy list pattern
│   ├── category_form.html          # Shared taxonomy create/edit form
│   ├── category_confirm_delete.html# Shared taxonomy delete confirmation
│   ├── subject_list.html
│   ├── subject_form.html
│   ├── subject_confirm_delete.html
│   ├── documenttype_list.html
│   ├── documenttype_form.html
│   ├── documenttype_confirm_delete.html
│   ├── document_list.html          # Document list with filter form (User Story 6)
│   ├── document_form.html          # Document create/edit form
│   ├── document_detail.html        # Document detail view
│   └── document_confirm_delete.html# Document delete confirmation
└── dashboard/
    ├── dashboard.html              # UNCHANGED
    └── profile.html                # UNCHANGED

config/
├── settings.py                     # MODIFIED — "vault" added to INSTALLED_APPS (FR-016)
└── urls.py                         # MODIFIED — path("", include("vault.urls")) (FR-017)

accounts/                           # UNCHANGED
dashboard/                          # UNCHANGED
```

**Structure Decision**: Option 3 (web application with server-rendered
templates) adapted to Django's flat layout. The `vault/` app directory follows
the same convention as `accounts/` and `dashboard/`. Templates are centralized
under `templates/` (matching DFT-7's `DIRS`-based template config) rather than
inside the app directory, so the `templates/vault/` directory mirrors the
`templates/dashboard/` pattern. `APP_DIRS = True` in settings also allows
app-level templates, but the centralized approach matches the existing pattern.

The three taxonomy entities (Category, Subject, DocumentType) share an identical
field shape and near-identical form/view/template patterns. They are NOT
abstracted into a shared base class or generic — three concrete models, three
concrete forms, three concrete view sets — because DRY indirection adds
complexity with no persistence benefit (R3). The templates use a consistent
naming convention (`<entity>_list.html`, `<entity>_form.html`,
`<entity>_confirm_delete.html`) for easy navigation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle II zone map deferral (DFT-7 carryover + new vault pii surface) | Vault `Document` model holds user-generated personal data (title/notes); `SECURITY_ZONES.md` and factory zone map must name real paths (`vault/` → `pii`) | Updating the zone map inside this ticket would deny agent writes to `vault/` mid-implementation — the vault code must exist first, then the zone map is updated as human follow-up. Recorded deferral with explicit rationale (R15) |
