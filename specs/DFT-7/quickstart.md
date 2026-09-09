# DFT-7 Quickstart — Validation Guide

**Purpose**: Prove the scaffold works end-to-end. This is a run/validate guide —
implementation details live in the plan and tasks.
**References**: Route/form contracts [`contracts/web-contracts.md`](contracts/web-contracts.md);
entities & validation [`data-model.md`](data-model.md); decisions
[`research.md`](research.md).

> **Factory note**: this repo's Python overlay is not yet supported by the factory
> sandbox (`overlays/python/README.md`) — the CI pipeline cannot install Python or
> run the test suite, and this ticket ships **UNVERIFIED**. The commands below are
> the authority for SC-005 and must be run by the implementer locally; the human
> approver checks SC-005 against this run.

## Prerequisites

- Python 3.11+ on the machine running validation
- Git branch `DFT-7-scaffold-django-project` checked out
- From repo root: `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt` (installs `Django~=5.2`)

## Setup

```bash
python manage.py makemigrations          # creates accounts (User, Profile) migrations
python manage.py migrate                 # SQLite dev DB (db.sqlite3)
```

No seed data required — the flows create their own users.

## Validation scenarios (map to Success Criteria)

### 1. Scaffold is functional — SC-004

```bash
python manage.py check
python manage.py runserver 0.0.0.0:8000   # visit http://localhost:8000/
```

Expected: `manage.py`, `config/settings.py`, `config/wsgi.py`, `config/asgi.py`,
`config/urls.py` all present and the check passes with 0 issues; server starts;
root `/` confirms routing (dashboard redirect to login).

### 2. Full test suite — SC-005

```bash
python manage.py test            # Django's built-in runner, in-memory SQLite
```

Expected: **zero failures** across `accounts` (signup, login/logout, profile,
access control, CSRF-rejection) and `dashboard` (shell content, access control)
tests. Fast, no external services.

### 3. Registration → dashboard — SC-001

Manual (or with the test client): `GET /accounts/signup/` → fill email (e.g.
`ada@example.com`), password meeting FR-008 (e.g. `Sup3r-secret!`), confirm →
"Create account".

Expected: 302 to `/dashboard/`; user created; dashboard header shows the display
name (falls back to email until a display name is set). Total flow well under
2 minutes for a visitor.

Negative checks (contract reference: inline errors, FR-012):
- Re-submit same email → inline "…already exists"-style error, no duplicate
  (FR-009).
- `not-an-email` → inline format error (FR-010).
- `short1!` (no digit) / `short11` (no special) → inline password error (FR-008).

### 4. Login / logout lifecycle — FR-002, FR-003

- Log out (you'll get redirected to `/accounts/login/`), log back in with the
  same credentials → 302 to `/dashboard/` (SUCCESS).
- Wrong password → stays on login with non-field error, no session (FAILURE).
- On the dashboard, submit the logout control → 302 back to `/accounts/login/`;
  navigating to `/dashboard/` now redirects to login again.

### 5. Profile edit — FR-005, SC-002

Logged in: `GET /profile/` → change display name (e.g. "Ada Lovelace") → Save.

Expected: 200 with the new name on the profile page **and** in the dashboard
header immediately (SC-002); reload keeps the value (persisted).
Try saving an empty name → inline field error, previous value intact.

### 6. Access control — FR-007, SC-003

From an anonymous browser:
- `GET /dashboard/` → **302** to `/accounts/login/?next=/dashboard/`
- `GET /profile/` → **302** to `/accounts/login/?next=/profile/`

Expected: redirect responses contain **no protected content** (SC-003). Follow
the `?next=` after login and land back on the requested page.

### 7. CSRF — FR-011

Any POST made without a CSRF token (e.g. `curl -X POST http://localhost:8000/accounts/login/`)
→ **403 Forbidden** with no authentication side effects. All UI forms include
`{% csrf_token %}`.

## Edge-case spot checks (from spec § Edge Cases)

| Check | Expected |
|---|---|
| Password `abc` (too weak) | Inline error; no user created |
| Email `a@b.c` | Accepted (see research.md R7 — documented limitation) |
| Display name > 80 chars | Inline max-length error |
| Expired session on `/profile/` save | Redirect to login with `?next=/profile/`; after re-login the form/state is reachable again |
| Concurrent logins, two browsers | Both sessions work independently |
| POST with tampered CSRF token to `/dashboard/`/`/profile/` | 403, no state change |

## What "done" looks like (checklist)

- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test` — zero failures (SC-005)
- [ ] Signup → dashboard works (SC-001, FR-001)
- [ ] Login + logout lifecycle works (FR-002, FR-003)
- [ ] Profile edit persists & reflects in header (SC-002, FR-005)
- [ ] Dashboard shell renders sidebar/header/main (SC-006, FR-006)
- [ ] Anonymous access to `/dashboard/` & `/profile/` redirects with no leakage
      (SC-003, FR-007)
- [ ] CSRF rejection observed (FR-011)