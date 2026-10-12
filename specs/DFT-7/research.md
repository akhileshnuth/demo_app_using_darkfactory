# DFT-7 Research

**Date**: 2026-10-12

## R1 — Runtime and dependency

**Decision**: Support Python 3.11+ and Django 5.2 via the existing
`Django~=5.2` requirement.

**Rationale**: This is the approved clarification and the repository's actual
dependency constraint. Django's built-in auth, sessions, messages, CSRF, and
staticfiles are sufficient.

**Alternatives considered**: Django 5.1 or Django 6.x (do not match the
approved constraint); `django-allauth` (novel dependency and unnecessary).

## R2 — Authentication flow

**Decision**: Use a custom `accounts.User(AbstractUser)` with `username = None`,
unique email as `USERNAME_FIELD`, and Django session authentication. Implement
registration with `SignUpForm`/`SignUpView`, use Django `LoginView`, and use
POST-only Django `LogoutView` with CSRF.

**Rationale**: Meets the clarified self-service email/password flow while
retaining Django's password hashing, session rotation, redirect, and security
behavior.

**Alternatives considered**: Full `AbstractBaseUser` (more boilerplate), custom
login/logout (duplicates framework behavior), and third-party identity/auth
packages (out of scope).

## R3 — Profile representation

**Decision**: Keep `accounts.Profile` as a one-to-one, extensible model. Expose
only `User.display_name` through `ProfileForm`; do not expose avatar or other
fields. Create a profile for newly registered users and scope profile access to
`request.user` without an incoming user id.

**Rationale**: Exactly matches the clarification and prevents IDOR-style access
to another user's profile while leaving a future extension point.

**Alternatives considered**: A profile lookup by URL id (unnecessary exposure),
display name duplicated on Profile (sync risk), or exposing avatar now (outside
scope).

## R4 — Validation and private-route behavior

**Decision**: Use Django form validation, configured password validators, CSRF
middleware/tokens on every POST, and `LoginRequiredMixin` for dashboard/profile.
Anonymous requests redirect to `LOGIN_URL` with `next`; invalid submissions
re-render with inline errors and do not save.

**Rationale**: These are framework-native controls that satisfy FR-003,
FR-006, FR-007, and FR-008 with minimal bespoke code.

**Alternatives considered**: Manual authorization checks and unprotected GET
logout; both increase omission/CSRF risk.

## R5 — Verification

**Decision**: Validate with `python manage.py check`, migrations, and
`python manage.py test` locally, plus browser/test-client journeys for signup →
dashboard, login/logout, profile update, invalid input, CSRF, and anonymous
redirects.

**Rationale**: The repository's Python overlay cannot install or execute Python
in the factory, so human-run local evidence is required and must be marked
UNVERIFIED by the pipeline.

**Alternatives considered**: Skipping tests or substituting Node tests; neither
would verify Django behavior.

## R6 — Security-zone mapping

**Decision**: Before implementation, map `./accounts/` auth/session code and
auth migrations to `auth`; map Profile persistence/forms and templates that
render display name/email to `pii`; mirror the mapping in the factory zone map.

**Rationale**: `./SECURITY_ZONES.md` currently names nonexistent template paths,
while the constitution says enforcement comes from the factory map. Human-gated
work is mandatory for the actual sensitive files.

**Alternatives considered**: Proceeding with unmapped paths (violates Principle
II) or moving the project under `src/` (unnecessary structural churn).
