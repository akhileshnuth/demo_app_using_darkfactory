# Implementation Plan: Document List Pagination

**Branch**: `DFT-19` | **Date**: 2026-10-09 | **Spec**: [`./spec.md`](spec.md)

**Input**: Feature specification from [`./spec.md`](spec.md)

## Summary

Add server-side pagination to the existing authenticated document list. The
implementation will apply owner scoping and existing GET filters before a
fixed 20-item Django paginator, expose first/previous/next/last controls, and
preserve non-page query parameters in navigation URLs. Invalid pages clamp to
a valid page and empty results retain the current empty-list state. No schema
or dependency changes are needed.

## Technical Context

**Language/Version**: Python 3.11+; Django 5.2 (`Django~=5.2`)

**Primary Dependencies**: Django built-in `ListView`/`Paginator`, templates, and ORM; no new dependencies

**Storage**: Existing SQLite-backed Django ORM; no migration

**Testing**: Django bundled test runner (`python manage.py test`); implementation phase adds pagination coverage

**Target Platform**: Linux server, server-rendered HTML

**Project Type**: Django web application

**Performance Goals**: Query and render one 20-document page; avoid loading the full result set into the template

**Constraints**: Preserve owner isolation, existing filters/order/document markup, empty state, and no novel runtime dependency

**Scale/Scope**: One existing vault list view/template plus URL wiring if required; fixed 20-document pages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reviewed against `./.specify/memory/constitution.md`.

- **Principle I — Complete Spec-Kit pipeline**: PASS. This plan includes
  research, data model, web contract, and validation guide; tasks and
  implementation remain later pipeline phases.
- **Principle II — Security zones**: PASS with recorded repository-state
  caveat. The planned paths are `vault/`, `templates/vault/`, and `config/`;
  the checked-in `SECURITY_ZONES.md` only lists non-existent template paths.
  The document surface is user data, so human review should reconcile the
  real vault PII mapping after implementation; this plan does not alter zone
  configuration.
- **Principle III — Human-gated merge**: PASS. Delivery remains a reviewed PR
  to protected `main`.
- **Principle IV — Test-first**: PASS. The implementation must add/adjust
  tests for all pagination boundaries and query/ownership behavior; this plan
  creates no tests.
- **Principle V — No novel dependencies**: PASS. Django built-ins only.

**Gate result (pre-research)**: PASS with the recorded security-zone mapping
caveat; no unresolved technical unknowns remain after the approved
clarifications and repository inspection.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
vault/
├── views.py                 # document list query, filtering, and pagination
├── urls.py                  # existing list route, if missing in current scaffold
└── mixins.py                # existing owner-scoped queryset

templates/vault/
└── document_list.html       # filter-preserving pagination controls and state

config/
└── urls.py                  # include vault routes if the existing route is absent

specs/DFT-19/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/web-contracts.md
```

**Structure Decision**: Extend the flat Django `vault` app and centralized
`templates/vault/` layout already used by the repository. The current checkout
has an incomplete vault list/view URL scaffold, so implementation tasks must
first establish the existing document-list route/context without changing the
feature's scope. Pagination remains server-side and uses Django's built-in
generic-view contract.

## Complexity Tracking

No constitution violations requiring a complexity exception were identified.

## Post-design Constitution Re-check

- Principle I: **PASS** — all Phase 0/1 artifacts are present; tasks remain
  intentionally deferred to the tasks phase.
- Principle II: **PASS with recorded caveat** — no declared path currently
  matches the planned files, but human review must reconcile vault document
  data with the repository/factory PII zone map.
- Principle III: **PASS** — PR and human merge gate unchanged.
- Principle IV: **PASS** — required implementation tests are specified in the
  research and quickstart artifacts; no tests are created in planning.
- Principle V: **PASS** — no dependency or storage change.

**Post-design gate result**: PASS with the same recorded security-zone caveat.
