# Implementation Plan: Protect Uploaded Documents

**Branch**: `DFT-17` | **Date**: 2026-10-12 | **Spec**: `./specs/DFT-17/spec.md`

**Input**: Feature specification from `./specs/DFT-17/spec.md`

## Summary

Add an end-to-end protected document lifecycle to the Django vault: multipart upload into a private filesystem storage root, explicit owner/collaborator policy, ready-state gating, application-mediated streaming retrieval, expiry/deletion cleanup, and fail-closed audit logging. Existing metadata-only documents remain unavailable until a documented inventory/re-protection rollout completes; no legacy bytes are served during migration.

## Technical Context

**Language/Version**: Python 3.x (repository Django application; exact deployment minor version is not pinned)

**Primary Dependencies**: Django 5.2 (`./requirements.txt`); Python standard library only; no novel runtime dependency

**Storage**: SQLite development database (`./config/settings.py`); private filesystem storage outside static/public roots, configured by an environment-backed setting; database stores opaque storage names and lifecycle metadata

**Testing**: Django test runner with the existing `./tests/` suite; tests must cover model migrations, upload, authorization, direct-path isolation, streaming, cleanup, expiry, audit failure, and legacy rollout

**Target Platform**: Linux-hosted Django web application

**Project Type**: Server-rendered Django web application

**Performance Goals**: Stream file responses without loading document bytes into application memory; bounded upload size and storage operations; no new throughput SLA is specified

**Constraints**: Every retrieval rechecks current policy and `timezone.localdate()` expiry; private storage must not expose a URL; filesystem/database operations are not one transaction, so state transitions and orphan cleanup are required; anonymous and denied requests must be auditable without content or sensitive metadata

**Scale/Scope**: Existing vault users/documents; implementation is limited to `vault`, the existing `accounts.ActivityLog`, settings, templates, URLs, management commands, migrations, and their tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-Kit completeness**: PASS — this plan supplies Phase 0 and Phase 1 artifacts; implementation must continue through Tasks, Analyze, Implement, and human-reviewed Done.
- **Security zones**: PASS — planned paths are outside the declared `src/auth`, `src/payments`, and `src/customers` zones. Do not alter those paths; private document storage is an application setting and must not be placed in a declared zone.
- **Human-gated merge**: PASS — implementation is delivered only as a reviewed PR against protected `main` with CI green.
- **Test-first**: PASS — functional changes include tests in the existing test suite; this planning run creates no tests.
- **Novel dependencies**: PASS — use Django and Python standard library; any storage provider or encryption dependency requires human approval and is out of scope.

### Post-Design Re-check

- **Spec-Kit completeness**: PASS — `research.md`, `data-model.md`, `contracts/document-access.md`, and `quickstart.md` are present; `tasks.md` remains intentionally deferred to the Tasks phase.
- **Security zones**: PASS — the design names only `./accounts`, `./vault`, `./config`, templates, tests, and feature documentation. No declared security-zone path is authorized for agent modification.
- **Human-gated merge**: PASS — rollout includes an explicit human-reviewed legacy exposure decision and the implementation remains PR/CI gated.
- **Test-first**: PASS — `quickstart.md` defines security acceptance coverage while this plan creates no test files.
- **Novel dependencies**: PASS — all choices use existing Django/Python capabilities; no dependency or encryption/key-management change is implied.

## Project Structure

### Documentation (this feature)

```text
./specs/DFT-17/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
   └── document-access.md
```

### Source Code (repository root)

```text
./accounts/
├── models.py                 # ActivityLog actor/context/event schema
├── admin.py                  # audit inspection fields
└── migrations/               # nullable actor and audit-context migration
./vault/
├── models.py                 # document state/content and collaborator policy
├── forms.py                  # multipart upload and collaborator validation
├── services.py               # private storage, authorization, audit, cleanup
├── views.py                  # upload and protected retrieval endpoints
├── urls.py                   # upload/download routes
├── management/commands/     # inventory, re-protect, expiry and orphan cleanup
└── migrations/               # additive document/policy schema migration
./config/settings.py          # private storage root and upload limits
./templates/vault/            # upload, list/detail download affordances
./tests/                      # regression and security acceptance coverage
```

**Structure Decision**: Keep the existing single Django project and put domain logic in `vault`; keep audit schema in `accounts` because `ActivityLog` is the repository's established audit destination. No new app or dependency is needed.

## Complexity Tracking

No constitution violations. The two-phase filesystem/database lifecycle and rollout commands are required because filesystem writes cannot participate in the database transaction and legacy documents have no content reference.
