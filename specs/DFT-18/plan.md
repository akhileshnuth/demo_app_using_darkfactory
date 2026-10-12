# Implementation Plan: Deployment-ready application settings

**Branch**: `DFT-18` | **Date**: 2026-10-12 | **Spec**: `./specs/DFT-18/spec.md`

**Input**: Feature specification from `./specs/DFT-18/spec.md`

## Summary

Replace development-only defaults in `./config/settings.py` with an explicit,
typed environment contract. `DJANGO_ENV` must be `development` or `production`;
development preserves current local SQLite, while production fails at startup
unless deployment-provided security, database, host/origin, URL, proxy, storage,
and enabled-email settings validate. Document the contract in
`./specs/DFT-18/contracts/deployment-configuration.md`; use Django and Python
standard-library facilities only.

## Technical Context

**Language/Version**: Python 3.x; minor version is not pinned, with Django 5.2 compatibility required

**Primary Dependencies**: Django~=5.2 and Python standard library; no new runtime dependency

**Storage**: SQLite only for explicit development; production backend/connection fields from environment; private local filesystem document storage remains supported with an explicit persistent root

**Testing**: Django test runner and existing `./tests/` suite; implementation must add settings-focused tests, but this plan creates none

**Target Platform**: Linux-hosted Django WSGI/ASGI deployment behind an explicitly declared HTTPS reverse proxy

**Project Type**: Server-rendered Django web application

**Performance Goals**: Validation completes during startup; no new request-path or throughput target

**Constraints**: Fail before serving on invalid production configuration; never log secrets; reject wildcard/empty hosts and origins; preserve local/test behavior; no unapproved dependencies

**Scale/Scope**: `./config/settings.py`, deployment documentation, and configuration tests only; no infrastructure provisioning or auth/payment/PII workflow changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-Kit completeness**: PASS — Phase 0/1 artifacts are produced; Tasks and later implementation gates remain required.
- **Security zones**: PASS with review note — planned paths are not among the placeholder rows in `./SECURITY_ZONES.md`; settings controls sessions, storage, and secrets, so implementation requires human review and must not broaden auth/PII behavior. Reconcile the zone map separately.
- **Human-gated merge**: PASS — deliver only through a reviewed PR to protected `main` with CI evidence.
- **Test-first**: PASS — implementation must add coverage for production success/failure, redaction, and host/origin restrictions; this plan adds no tests.
- **Novel dependencies**: PASS — parsing uses standard-library/Django facilities. A backend driver absent from `./requirements.txt` requires human approval and is not introduced here.

## Project Structure

### Documentation (this feature)

```text
./specs/DFT-18/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── deployment-configuration.md
```

### Source Code (repository root)

```text
./config/settings.py       # typed environment contract and startup validation
./tests/                    # settings loading, validation, and redaction tests
./specs/DFT-18/contracts/   # deployment-facing variable documentation
```

**Structure Decision**: Keep the existing single Django project. Centralize
parsing/validation helpers in `./config/settings.py` unless an existing utility
is found; do not create a new app or runtime package.

## Post-Design Constitution Re-check

- **Spec-Kit completeness**: PASS — all Phase 0/1 outputs are present; `tasks.md` is intentionally deferred.
- **Security zones**: PASS — no declared zone path is planned for autonomous modification; human review is required for security-sensitive settings behavior.
- **Human-gated merge**: PASS — implementation remains PR/CI/human-review gated.
- **Test-first**: PASS — `./specs/DFT-18/quickstart.md` specifies required automated acceptance coverage.
- **Novel dependencies**: PASS — no dependency or infrastructure change is designed.

## Complexity Tracking

No constitution violations. Conditional SMTP/storage validation and explicit
proxy/HSTS controls are required by the specification; no simpler fallback is
safe for production.
