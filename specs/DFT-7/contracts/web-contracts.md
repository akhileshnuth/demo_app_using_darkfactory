# DFT-7 Web Contracts — Routes & Forms

**Source**: `/specs/DFT-7/spec.md` FR-001…FR-012; see also
[`/specs/DFT-7/data-model.md`](../data-model.md) for the entities these contracts
read/write and [`/specs/DFT-7/research.md`](../research.md) for the auth-view
decisions (R5, R9).

Interface type: **server-rendered HTML web application** (no JSON API, no CLI).
The contract below is the full externally visible surface: URL routes, allowed
methods, authentication gate, redirect behavior, and form field contracts. All
state-changing requests (POST) are CSRF-protected (FR-011); a missing/tampered
token yields **HTTP 403** before the view runs.

## Settings contract (must hold, else routes below break)

| Setting | Value |
|---|---|
| `AUTH_USER_MODEL` | `accounts.User` |
| `LOGIN_URL` | `/accounts/login/` |
| `LOGIN_REDIRECT_URL` | `/dashboard/` |
| `LOGOUT_REDIRECT_URL` | `/accounts/login/` |
| `ALLOWED_HOSTS` | `["localhost", "127.0.0.1", "testserver"]` (dev) |

## Routes

### Public (no session required)

**`GET /accounts/signup/`** — registration form.  
**`POST /accounts/signup/`** — create account (FR-001).
- Auth gate: none.
- Success: creates active `User` (+ `Profile` row), logs the user in, redirects
  **302 → `/dashboard/`** (FR-001 acceptance 1).
- Failure (invalid email / duplicate email / weak password / missing fields):
  re-renders `200` with **inline field errors** (FR-012); no account created
  (FR-008, FR-009; acceptance 2 & 3).
- Form fields (HTML `<form method="post">`): `email`, `password1` (validation
  errors for FR-008 shown beside it), `password2` (confirmation mismatch shown
  beside it). CSRF token required.

**`GET /accounts/login/`** — login form (FR-002).  
**`POST /accounts/login/`** — authenticate + establish session.
- Auth gate: none (visiting while logged in redirects to `LOGIN_REDIRECT_URL`).
- Success: `302 → /dashboard/` (or to the `?next=` URL when redirected from a
  protected page).
- Failure (unknown email / wrong password / inactive user): re-renders `200` with
  a non-field error ("Please enter a correct email and password…"); **no session
  created** (acceptance 2).
- Form fields: `username` (renders as email via the email-based auth backend),
  `password`. CSRF token required.

### Session-terminating

**`POST /accounts/logout/`** — terminate session (FR-003), then **GET-redirect
302 → `/accounts/login/`** (acceptance 3).
- Auth gate: none required at URL level, but the header control is only rendered
  to authenticated users.
- POST-only (Django 5.x `LogoutView` rejects GET with 405) — the dashboard header
  logout is a POST form carrying a CSRF token, not an anchor link.

### Protected (login required — FR-007)

**`GET /dashboard/`** — dashboard shell (FR-006).
- Auth gate: **any unauthenticated request → 302 `/accounts/login/?next=/dashboard/`**;
  zero page content in the redirect response (SC-003).
- Renders `base.html` shell: sidebar nav (Dashboard, Profile placeholder links),
  header showing `request.user.display_name` (fall back to email when blank) plus
  the logout control, main content area with placeholder content (SC-006).

**`GET /profile/`** — profile view (FR-005).
**`POST /profile/`** — update display name.
- Auth gate: **any unauthenticated request → 302 `/accounts/login/?next=/profile/`**.
- Success: display name persisted; re-render `200` with the updated value visible
  in header + profile page (acceptance 1; SC-002).
- Failure (blank display name): re-render `200` with inline field error "This
  field is required."-style message beside the field (acceptance 2); nothing
  persisted. Display name > 80 chars → inline max-length error.
- Form fields: `display_name`. CSRF token required.

## HTTP status summary

| Route | Method | Auth | Success | Errors |
|---|---|---|---|---|
| `/accounts/signup/` | GET/POST | none | 302 → `/dashboard/` | 200 + inline errors |
| `/accounts/login/` | GET/POST | none | 302 → `/dashboard/` (or `next`) | 200 + non-field error |
| `/accounts/logout/` | POST | none (POST-only, 405 on GET) | 302 → `/accounts/login/` | — |
| `/dashboard/` | GET | **required** | 200 shell | 302 → login?next |
| `/profile/` | GET/POST | **required** | 200 page / persisted | 302 → login?next; 200 + inline errors |
| any POST with bad/missing CSRF | — | — | — | **403** |

## Template surface (SC-006)

- `templates/base.html` — shell: `sidebar` (nav), `header` (display name +
  logout POST form), `main` (block). Base CSS in `static/`.
- `templates/registration/signup.html`, `templates/registration/login.html` —
  extend base but render outside the shell (public, no shell chrome leakage).
- `templates/dashboard/dashboard.html` (main-area placeholder),
  `templates/dashboard/profile.html` (edit form with inline errors).

## Non-contract surface (explicitly out of scope)

- No JSON/REST API; no schema/OpenAPI.
- `/admin/` is Django's stock admin (dev convenience only, not part of this
  ticket's contract).
- No email-verification endpoints, no password-reset flow.