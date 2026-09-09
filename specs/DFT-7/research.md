# DFT-7 Research & Design Decisions

**Phase 0 output** — resolves all `NEEDS CLARIFICATION` items from the Technical
Context and records best-practice decisions for the Django scaffold. Each entry
follows *Decision / Rationale / Alternatives considered*.

Date: 2026-09-09

---

## R1. Django & Python versions

**Decision**: Django 5.2 LTS (extended-support release), `Django~=5.2` in
`requirements.txt`; Python 3.11+ (3.12/3.13 both supported by Django 5.2).

**Rationale**: Django 5.2 is the current LTS line as of the ticket date, giving
security support into 2028. LTS is the right choice for a scaffold that other
tickets will build on. Python 3.11+ is the minimum supported by Django 5.2 and is
widely available.

**Alternatives considered**: Django 6.x (latest feature line — shorter support,
unneeded churn for a scaffold); Django 4.2 LTS (older, still supported but a
greenfield scaffold gains nothing from pinning two LTS generations back).

## R2. User model strategy (email login + display name)

**Decision**: Minimal custom `User(AbstractUser)` in the `accounts` app:
`username = None`, `USERNAME_FIELD = "email"`, `email = EmailField(unique=True)`,
`display_name = CharField(max_length=80, blank=True)`, `REQUIRED_FIELDS = []`,
with a small `UserManager(BaseUserManager)` implementing `create_user` /
`create_superuser`. Registered via `AUTH_USER_MODEL = "accounts.User"` in settings.

**Rationale**: FR-002 mandates login by email; FR-009 mandates unique email;
FR-004 puts display name on the user account. Subclassing `AbstractUser` keeps the
full permissions/admin machinery while swapping the identifier to email — the
"minimal custom extension" the spec's Assumptions allow. Because the repo is
greenfield, the custom model is set *before* any migration exists, avoiding the
classic "can't swap user model after first migration" trap.

**Alternatives considered**: Stock `django.contrib.auth.User` — impossible: it
keys on `username`, and FR-002 requires email login. Full `AbstractBaseUser` +
`PermissionsMixin` custom model — the canonical email-login recipe, but more
boilerplate than a scaffold needs when `AbstractUser` already provides groups,
permissions, and admin registrations.

## R3. Profile entity modeling

**Decision**: `Profile` as a separate `OneToOneField(user)` model in `accounts`,
holding `avatar_url = URLField(blank=True)` (placeholder for future) plus a
read-only `display_name` property that delegates to `user.display_name`. The
display name itself is persisted on `User` (FR-004 lists it as a user account
attribute), and the profile form edits `user.display_name`.

**Rationale**: The spec's Key Entities define a Profile one-to-one with User that
"may diverge in future features". Keeping the display name on `User` makes it
available as `request.user.display_name` in the dashboard header without a profile
fetch, while the Profile row gives future tickets a place to grow (avatar, bio)
without schema churn. One source of truth — no sync problem.

**Alternatives considered**: Storing display name on Profile only — requires a
profile fetch on every user render (header), couples auth display to profile; a
profile-less user (post-signup) has no display name until a Profile row is
created. Duplicating on both — sync bugs for zero benefit.

## R4. App structure & project layout

**Decision**: Flat Django project at repo root: `manage.py`, project package
`config/` (settings, urls, wsgi, asgi), first-party apps `accounts/` (User model,
auth views/forms, Profile model) and `dashboard/` (dashboard shell view), global
`templates/` and `static/` directories.

**Rationale**: Matches Django's default `django-admin startproject`/`startapp`
output (closest to what SC-004's "scaffold files generated and functional"
implies), keeps the layout flat like the previous DFT-7 attempt
(`accounts/`, `dashboard/`, `templates/`, `manage.py`), and splits the two
concerns the spec names (accounts/profile vs dashboard shell) into two apps.

**Alternatives considered**: Monolithic single app — fewer files but blurs the
spec's accounts/profile/dashboard separation. Inner `src/` hierarchy — adds
structure the factory's zone defaults reference (`src/auth`) but that the repo
root never used; rejected in Complexity Tracking.

## R5. Auth views: use Django's built-ins

**Decision**: `django.contrib.auth.views.LoginView` and `LogoutView` for
login/logout; a custom `SignUpForm` + write-your-own signup view (function or
`CreateView`) for registration; a custom `ProfileForm` (ModelForm over
`display_name`) with a `login_required` profile view. Settings wired as
`LOGIN_URL = "/accounts/login/"`, `LOGIN_REDIRECT_URL = "/dashboard/"`,
`LOGOUT_REDIRECT_URL = "/accounts/login/"`.

**Rationale**: Django's login/logout views already implement authenticate-then-
session and session-flush + redirect (FR-002, FR-003) with CSRF and messages
handled. Custom code is limited to what Django does not ship: registration
(FR-001) and profile edit (FR-005).

**Alternatives considered**: Third-party `django-allauth` — excluded by the spec's
Assumptions (built-in auth only). Custom login/logout views from scratch — pure
reimplementation of well-tested framework behavior, against Django best practice.

## R6. Password strength (FR-008)

**Decision**: Custom `accounts/validators.py` implementing Django's
`BasePasswordValidator` contract: reject passwords shorter than 8 characters or
missing at least one digit or at least one special character (non-alphanumeric).
Registered in `AUTH_PASSWORD_VALIDATORS` alongside Django's built-in
`UserAttributeSimilarityValidator` / `MinimumLengthValidator(8)` /
`CommonPasswordValidator` / `NumericPasswordValidator`. Applied automatically by
the `SignUpForm` password field (validators are part of Django's form field
`validators` chain via `validate_password`).

**Rationale**: FR-008 is a concrete policy Django's defaults do not encode
(digit + special char), so it must be a first-party validator. Inline field
errors (FR-012) fall out of Django's form error machinery for free.

**Alternatives considered**: Regex only inside the form `clean_password` — works,
but a standalone validator is reusable by `createsuperuser` and admin and is the
idiomatic Django extension point.

## R7. Email validation (FR-010) and the `a@b.c` edge case

**Decision**: Django's `EmailField` / `forms.EmailField` with the default
`EmailValidator` for both registration and profile paths.

**Rationale**: Satisfies FR-010 with the framework-standard validator.

**Edge-case disposition**: `a@b.c` passes Django's default `EmailValidator`
(single-letter TLDs are structurally valid per the validator's regex) — the spec's
edge case flags exactly this. Decision: **accept** for the scaffold. The spec's
FR-010 requires *format* validation, which Django provides; real-world MX/domain
verification is an email-service concern explicitly out of scope ("no email
verification flow"). Recorded as a known limitation.

**Alternatives considered**: Custom tightening regex (`[a-z]+\.[a-z]{2,}`-style)
— rejects legitimate addresses, adds maintenance, and goes beyond the
requirement's letter.

## R8. Duplicate email & case normalization (FR-009)

**Decision**: `UserManager.normalize_email` lowercases the whole address
(Django's default lowercases only the domain), and the signup form checks email
uniqueness with a case-insensitive `email__iexact` query so `A@B.com` vs
`a@b.com` are treated as the same account. DB `unique=True` remains the final
enforcement.

**Rationale**: Prevents both exact and case-variant duplicates (FR-009) with the
smallest code surface: one manager override + one form check.

**Alternatives considered**: DB `citext`/functional indexes — SQLite dev story
complicates this; over-engineering for a scaffold. Case-sensitive uniqueness only
— leaves `A@B.com` and `a@b.com` as two accounts, a duplicate-account leak.

## R9. CSRF (FR-011) and tampered-token edge case

**Decision**: Stock Django CSRF middleware (enabled by default); `{% csrf_token %}`
in every POST form (signup, login, logout, profile). No `@csrf_exempt` anywhere.

**Rationale**: Django's middleware already rejects missing/tampered/expired
tokens with HTTP 403 before a view runs — satisfying FR-011 with zero custom code.

**Dependencies (edge cases)**: Django 5.x's `LogoutView` only accepts POST, so the
header logout control is a POST form (CSRF-protected), not a link. This also means
the "click logout" acceptance scenario exercises FR-011/FR-003 together.

## R10. Session expiry & concurrent logins (edge cases)

**Decision**: Default session behavior. `SESSION_COOKIE_AGE` untouched (~2-week
rolling expiry, browser-session cookie unless changed). Concurrent sessions from
multiple browsers are allowed.

**Rationale**: An expired session on a protected page yields the standard
`login_required` redirect to `/accounts/login/?next=<page>` — save attempts are
never lost to a 500; the user re-authenticates and is returned to the form. This
matches the spec's edge-case expectation. Concurrent logins are not restricted by
any requirement; Django supports them natively.

**Alternatives considered**: Single-session enforcement (session-flush on new
login) — requires custom session middleware and contradicts no requirement but
solves no stated problem; deferred.

## R11. Verification strategy under the Python-overlay constraint

**Decision**: Tests run with Django's bundled runner: `python manage.py test`
(in-memory SQLite test DB; zero external services). The implementer must run the
suite locally and report results; the factory pipeline cannot (its sandbox ships
Node only, no Python/PyPI — `overlays/python/README.md`), so this ticket is
labelled **UNVERIFIED** for the human approver.

**Rationale**: SC-005 ("test suite passes with zero failures") remains verifiable
— by the implementer's local run and the human approving the PR — even though CI
cannot execute Python. Honest and explicit per the overlay README.

**Alternatives considered**: Silent failure (skip tests) — violates Principle IV.
Node-based test emulation — fiction. Waiting for the factory's Python profile —
blocks an otherwise autonomy-eligible ticket.

## R12. Security-zone mapping (Constitution Principle II)

**Decision**: Record the zone mapping explicitly and act on it in implementation,
because `SECURITY_ZONES.md` currently carries the template-default rows
(`src/auth:auth`, `src/payments:payments`, `src/customers:pii`) that name paths
this repo does not have. The real sensitive surfaces are:

| Actual path | Zone name | Why |
|---|---|---|
| `accounts/models.py` (User), `accounts/forms.py`, `accounts/views.py` (auth), `accounts/urls.py` | `auth` | Session/authentication logic lives here |
| `accounts/models.py` (Profile), `accounts/forms.py` (ProfileForm), dashboard header rendering of display name | `pii` | Display name is personal data (PII floor) |

Required implementation step: update `SECURITY_ZONES.md` to name the real Django
paths and mirror them into the factory zone map (`FACTORY_ZONES` /
`agentguard/policies/zones/zones-v0.json`). Until the factory config is updated,
**no zone actually matches any path in this repo** (the factory enforces from its
own config, which still points at `src/...`), so the previous DFT-7 attempt's
writes were not blocked. Per Principle II, once zones are mapped, agent writes
inside them are denied and those files become human work — the implement agent
must reconcile this with the PR plan.

**Alternatives considered**: Restructure the app under `src/` so the existing zone
rows match — rejected (empty structure churn, contradicts the flat layout for
scaffold-fidelity, and leaves `accounts` auth still unmapped). Leave zones
unamended and proceed — rejected: Principle II is explicit that an unmapped
sensitive surface is exactly the state that must not be assumed.

**Gate status**: Pre-research **CONDITIONAL PASS** — the zone-mapping step above
is a named precondition of implementation. Re-checked after Phase 1 (see
`plan.md` Constitution Check).

---

## Dependency & integration notes

- **Django built-ins used**: `django.contrib.auth` (auth views, user manager
  machinery, password validators), `django.contrib.sessions`, `django.contrib.messages`,
  `django.contrib.staticfiles`, `django.contrib.admin` (dev convenience).
- **No third-party runtime packages**: `requirements.txt` contains only `Django`.
- **Integrations**: none external — this is a self-contained server-rendered app
  (SQLite, local templates, bundled static).