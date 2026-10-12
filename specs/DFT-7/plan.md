# Implementation Plan: Scaffold Django Project with Accounts, Profile & Dashboard Shell

**Branch**: `DFT-7-scaffold-django-project` | **Date**: 2026-10-12 | **Spec**: [`./spec.md`](spec.md)

## Summary

DFT-7 is planned as a flat, server-rendered Django application using the
existing Django 5.2 dependency. The account journey uses email/password
registration, login, and POST logout. A custom email-keyed `User`, one-to-one
`Profile`, authenticated profile update, and protected dashboard shell provide
the minimum account experience. The repository already contains an
implementation-shaped scaffold and later-ticket extensions; this plan records
the intended DFT-7 contracts and the files that implementation/reconciliation
must own rather than changing source code here.

## Technical Context

**Language/Version**: Python 3.11+; Django 5.2 (`./requirements.txt` contains
`Django~=5.2`).

**Dependencies**: Django built-ins (`auth`, sessions, messages, staticfiles,
admin); no new runtime dependencies. Use Django's session authentication,
`LoginView`, `LogoutView`, and password validation rather than third-party auth.

**Storage**: SQLite development/test database configured by
`./config/settings.py`; production storage is out of scope.

**Application shape**: Flat project root with `./manage.py`, `./config/`,
`./accounts/`, `./dashboard/`, `./templates/`, and `./static/`. Server-rendered
HTML only; no JSON API or frontend framework.

**Testing**: Django's bundled runner (`python manage.py test`) with an isolated
SQLite test database. The Python overlay cannot run tests in the factory, so a
local implementer run and human review are required; the result is
UNVERIFIED by the factory pipeline.

**Unknowns**: None remain after the approved clarifications. Email verification,
password reset, avatar editing, responsive design, and dashboard business
widgets are explicitly out of scope.

## Constitution Check

*GATE: pass before research; re-check after design.*

- **I — Spec-Kit completeness**: PASS. This plan supplies Phase 0/1 artifacts;
  later tasks and implementation remain required to complete the pipeline.
- **II — Declared security zones**: CONDITIONAL PASS / implementation blocker.
  The current `./SECURITY_ZONES.md` still contains template paths. Before any
  auth/profile implementation or reconciliation, a human must map
  `./accounts/` authentication/session paths to `auth`, profile and
  display-name surfaces to `pii`, and mirror those rows in the factory zone
  map (`FACTORY_ZONES` or `agentguard/policies/zones/zones-v0.json`). Once
  mapped, agents must not write those files. This plan does not authorize such
  writes.
- **III — Human-gated merge**: PASS. Delivery requires a reviewed PR to
  protected `main` and passing CI/evidence.
- **IV — Test-first**: PASS for the implementation plan. Account, profile,
  dashboard, validation, CSRF, and access-control tests must accompany
  functional changes; local Python execution is the verification authority.
- **V — No novel dependencies**: PASS. The design uses only existing Django.

**Gate result**: PASS with the mandatory security-zone mapping and human gate
above. No unjustified violation is introduced.

## Planned source ownership

- `./config/settings.py`, `./config/urls.py`, `./manage.py`: Django wiring,
  `AUTH_USER_MODEL`, login redirects, middleware, and application entry point.
- `./accounts/models.py`, `./accounts/forms.py`, `./accounts/views.py`,
  `./accounts/urls.py`, `./accounts/migrations/`: email-keyed account,
  one-to-one profile, registration, login/profile forms/views, and schema.
  These are security-zone files and require human-gated work.
- `./dashboard/views.py`, `./dashboard/urls.py`: login-required dashboard shell.
- `./templates/registration/`, `./templates/dashboard/`,
  `./templates/base.html`, `./static/`: forms, navigation, shell, and neutral
  presentation; templates rendering identity data are PII review surfaces.
- `./accounts/tests.py`, `./dashboard/tests.py`: implementation tests required
  by Constitution Principle IV; no tests are created in the planning phase.

## Design artifacts

1. [`./research.md`](research.md) resolves framework, auth, model, validation,
   verification, and zone decisions.
2. [`./data-model.md`](data-model.md) defines User, Profile, and the non-record
   Dashboard Shell plus validation and ownership rules.
3. [`./contracts/web-contracts.md`](contracts/web-contracts.md) defines the
   server-rendered route and form interface.
4. [`./quickstart.md`](quickstart.md) gives runnable setup and acceptance checks.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Security-zone path mismatch | Existing declarations use template `src/...` paths while Django uses `accounts/` and templates | Proceeding without mapping violates Principle II; restructuring the repository merely to match defaults is unnecessary |
