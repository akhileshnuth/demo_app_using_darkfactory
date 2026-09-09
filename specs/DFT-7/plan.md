# Implementation Plan: Scaffold Django Project with Accounts, Profile & Dashboard Shell

**Branch**: `DFT-7-scaffold-django-project` | **Date**: 2026-09-09 | **Spec**: [`/specs/DFT-7/spec.md`](spec.md)

**Input**: Feature specification from `/specs/DFT-7/spec.md`

## Summary

Scaffold a server-rendered Django project from scratch that provides email/password
registration, login/logout, a profile page for editing a display name, and an
authenticated dashboard shell (sidebar, header with display name + logout, main
content area). Uses Django's built-in `django.contrib.auth`, a minimal custom
`User` model (email as `USERNAME_FIELD`, `display_name` field), a one-to-one
`Profile` model for future-scaffold data, SQLite storage, and Django's bundle
test runner. Server-rendered templates only; no frontend JS framework.

The repository currently contains no source code. This ticket creates the entire
Django scaffold (`manage.py`, project config, `accounts` and `dashboard` apps,
profile support, templates, tests).

## Technical Context

**Language/Version**: Python 3.11+ (Django 5.1 LTS). Version pinned in
`requirements.txt` as `Django>=5.1,<5.2`. Runtime is the factory sandbox (Node-only),
so Python must be installed locally by the implementer/human reviewer; dependency
install and test runs are NOT executed by the factory pipeline.

**Primary Dependencies**: Django 5.1 LTS; Django's built-in `django.contrib.auth`,
`django.contrib.sessions`, `django.contrib.messages`, `django.contrib.staticfiles`.
No third-party libraries (no `django-allauth`, no DRF). No novel runtime
dependencies — autonomy-eligible under Constitution Principle V.

**Storage**: SQLite (Django default) for development and test; configured via
`settings.DATABASES` against `DB_DIR`/`BASE_DIR`. Production DB out of scope.

**Testing**: Django's bundled test runner (`python manage.py test` /
`python -m django test`). Uses the in-memory test database, so tests run without
any external service. Because the factory sandbox ships Node only (see
`overlays/python/README.md`), the CI pipeline cannot install Python or run pytest
— the local `manage.py test` run is the verifiable authority for SC-005, and the
factory marks such tickets **UNVERIFIED** for the human approver.

**Target Platform**: Linux server; must be runnable locally. Server-rendered
Django templates, desktop-only layout (responsive/mobile not in scope per spec).

**Project Type**: web-service (server-rendered Django application).

**Performance Goals**: No meaningful performance goals for a scaffold. Registration
→ dashboard in under 2 min (SC-001); profile update reflected within 5 s (SC-002)
are human-observable UX targets, not load metrics.

**Constraints**: Admin/session/auth surface controlled by Django defaults with CSRF
enabled on all POST forms (FR-011). Python test pipeline unverified in factory
(Security/Verification gate — see Constitution Check). SECURITY_ZONES.md is still
the template default (`src/auth`, `src/payments`, `src/customers`) and does not yet
reflect this repo's Django layout — flagged for the implementer.

**Scale/Scope**: Small scaffold. Two first-party Django apps (`accounts`,
`dashboard`) plus project config, one custom User model (minimal), one Profile
model, ~2 primary templates plus a base shell.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reviewed against `constitution.md`.

- **Principle I — Spec-Kit completeness**: Full pipeline in progress (Spec →
  Plan → Tasks → Implement). This ticket continues the pipeline (previous DFT-7
  attempt stopped at implement and left no source). **PASS**.
- **Principle II — Security zones declared**: `SECURITY_ZONES.md` declares
  `src/auth` (auth), `src/payments`, `src/customers` (pii). The Django layout
  planned here does **not** use a `src/` hierarchy and puts auth/session logic and
  profile (display name, PII floor) under an `accounts`/`dashboard` app structure.
  This is a **GATE VIOLATION (unjustified today)**: the zones are still template
  defaults and do not name the actual Django auth/profile paths. Resolution: the
  plan must record the mapping of the Django auth + profile surfaces against the
  `auth`/`pii` zone recognition set and instruct the implementer to update
  `SECURITY_ZONES.md` and the factory zone map before writing auth/profile code.
- **Principle III — Human-gated merge**: Changes land via PR to protected `main`
  with human review + CI. **PASS** (enforced at repo/factory level).
- **Principle IV — Test-first**: Functional changes require tests. Standard Django
  test runner is self-contained (no service deps). Tests are planned (account,
  profile, dashboard, access control). **PASS**, with caveat that CI cannot run
  Python tests in this factory (see Security/Verification note below).
- **Principle V — No novel dependencies**: No runtime deps beyond Django itself.
  **PASS**. Autonomy-eligible.
- **Security/Verification (python overlay)**: `overlays/python/README.md` states
  the factory sandbox has no Python, no PyPI egress, and cannot run Python tests —
  such tickets are marked **UNVERIFIED**. The implementer must run
  `python manage.py test` locally and the human approver must verify SC-005 from
  that local run. Recorded as an accepted, known constraint for this ticket, not a
  silent pass.

**Gate result (pre-research)**: **PASS with one required condition** — the
`SECURITY_ZONES.md` / factory zone-map mismatch (Principle II) must be resolved
before auth/profile implementation begins. All other gates pass.

**Gate result (post-design, re-check)**: Still **PASS with the same single
condition**, now concretely scoped. Phase 0/1 resolved every `NEEDS CLARIFICATION`;
the zone gap is no longer an unknown, it is a named implementation step:

- R12 (`research.md`) maps the real sensitive surfaces to the factory's recognized
  zone set: `accounts/` auth/session logic → `auth`; `accounts/` Profile +
  dashboard header display-name rendering → `pii`. Because the factory enforces
  from *its* config (which still points at the `src/...` template defaults), no
  row currently matches this repo — writes historically were not denied, and will
  not be until the map is updated.
- **Required precondition of implementation**: update `SECURITY_ZONES.md` rows to
  the real paths and mirror them into the factory zone map
  (`agentguard/policies/zones/zones-v0.json` or `FACTORY_ZONES`) **before** the
  implement agent writes auth/profile code. Once mapped, agent writes into those
  zones are denied per Principle II and those files become human work — the
  implementer must reconcile the PR plan with that reality (i.e., the custom User
  model + auth views and profile form may need human-authored delivery, while the
  dashboard shell and scaffold config remain agent-writable).
- All other principles re-confirmed post-design: I (full pipeline in flight), III
  (PR + human merge), IV (tests planned via Django's bundled runner; local run is
  the SC-005 authority given the Python-overlay UNVERIFIED status), V (no novel
  runtime dependencies).

## Project Structure

### Documentation (this feature)

```text
specs/DFT-7/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── web-contracts.md # Server-rendered routes + template contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

The Django project is created at the repository root (flat `manage.py` convention),
with the Django project package and first-party apps as sibling top-level
directories. This matches the repo's intended flat layout and the flat app
locations referenced in the previous DFT-7 attempt (`accounts/`, `dashboard/`,
`templates/`, `manage.py`).

```text
manage.py                     # Django manage script (SC-004)
requirements.txt              # Django 5.1 LTS pinned
config/                       # Django project package (settings/urls/wsgi/asgi)
├── __init__.py
├── settings.py               # PROJECT_NAME, DB (SQLite), installed apps, auth backends
├── urls.py                   # Root URLconf -> accounts/, dashboard/, admin/
├── wsgi.py                   # SC-004
└── asgi.py                   # SC-004
accounts/                     # First-party app: user model, auth views/forms, profile
├── __init__.py
├── apps.py
├── models.py                 # User (AbstractUser) + Profile (OneToOne)
├── forms.py                  # SignUpForm, ProfileForm (server-side validation)
├── views.py                  # SignUpView, LoginView, LogoutView, ProfileView
├── urls.py                   # /accounts/signup/, /accounts/login/, /accounts/logout/, /profile/
├── admin.py
├── migrations/
└── tests.py                  # SC-005: account/profile tests
dashboard/
├── __init__.py
├── apps.py
├── views.py                  # DashboardView (login-required)
├── urls.py                   # /dashboard/
└── tests.py                  # SC-005: dashboard shell + access control
templates/                    # Server-rendered templates (SC-006)
├── base.html                 # Shell: sidebar, header (display name + logout), main
├── registration/signup.html  # Sign-up form (inline errors, FR-012)
├── registration/login.html   # Login form (inline errors, FR-012)
└── dashboard/
    ├── dashboard.html        # Main content placeholder
    └── profile.html          # Profile edit form (inline errors, FR-012)
static/                       # Minimal static asset (base CSS) for the shell
```

**Structure Decision**: Chosen **Option 2 (web application)** adapted to Django's
flat layout. Because this is a server-rendered Django app, the "frontend" is
Django templates under `templates/`, and the single backend is the Django project.
A single project package (`config/`) + two first-party apps (`accounts`,
`dashboard`) keeps the scaffold small and matches the spec's scope. The
"backend/ + frontend/" split in the template's Option 2 is not applicable here
since there is no separate JS frontend.

No novel runtime dependencies, so no package-scope walls are needed within this
scaffold beyond the Django app boundaries.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle II zone mismatch | Django auth/session and profile/display-name live under `accounts/` (server-rendered) rather than a `src/` tree | Restructuring the whole app under `src/` to match template default zones adds unneeded structure and diverges from the previous DFT-7 layout (`accounts/`, `dashboard/`, `templates/`); updating `SECURITY_ZONES.md` + factory zone map to name the real Django paths is the minimal correct fix |

## Phase 0-1 Output

Phase 0 research and Phase 1 design artifacts are generated and stored as:
- `./specs/DFT-7/research.md`
- `./specs/DFT-7/data-model.md`
- `./specs/DFT-7/contracts/web-contracts.md`
- `./specs/DFT-7/quickstart.md`
