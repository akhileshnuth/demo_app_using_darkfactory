# DFT-7 Data Model

**Source**: `/specs/DFT-7/spec.md` § Key Entities + FR-004, FR-005, FR-008, FR-009, FR-010

Decisions underlying this model are in [`/specs/DFT-7/research.md`](../research.md):
custom `User(AbstractUser)` keyed on email (R2), display name on User with Profile
delegating (R3), case-insensitive email uniqueness (R8), custom password validator
(R6). Schema-first note: `AUTH_USER_MODEL` is set in settings **before** any
migration is created — the repo is greenfield, so there is no swap-user-model
hazard.

---

## Entities

### 1. User — `accounts.models.User` (extends `AbstractUser`)

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `username` | *(removed)* | `None` | `AbstractUser` field suppressed; email is the identifier |
| `email` | `EmailField` | `unique=True`, `max_length=254` | Primary identifier; `USERNAME_FIELD`; case-insensitive uniqueness enforced in `forms` + manager normalization |
| `password` | *(inherited)* | hashed (Django default PBKDF2/SHA256) | Managed by `AbstractBaseUser`; never stored plaintext |
| `display_name` | `CharField` | `max_length=80`, `blank=True`, `default=""` | FR-004 "optional" display name; edit target for FR-005; profile form requires non-empty on save (acceptance scenario 2) |
| `first_name` / `last_name` | `CharField` | `blank=True` | Inherited from `AbstractUser`; unused by scaffold UI but harmless (admin only) |
| `is_active` | `BooleanField` | `default=True` | Accounts active immediately (no email verification per Assumptions) |
| `is_staff`, `is_superuser` | `BooleanField` | inherited | Admin/superuser machinery |
| `date_joined` | `DateTimeField` | `auto_now_add` | FR-004 "created" timestamp |
| `last_login` | `DateTimeField` | `null=True` | Inherited; FR-004 "last login" timestamp |

**Manager**: `accounts.models.UserManager(BaseUserManager)` — `create_user(email,
password, **extra)` and `create_superuser(...)`, both calling
`normalize_email` (lowercases the whole address, R8). Assigned as `objects`.

**Meta**:
- `AUTH_USER_MODEL = "accounts.User"` (registered in `config/settings.py`)
- `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = []`
- `ordering = ["email"]` (optional, for admin/deterministic lists)

**State transitions**:

```text
Anonymous ──signup (FR-001)──▶ active User ──login──▶ session established
                                                          │
     deactivate/delete (admin-only, not in scaffold UI) ──┘
```

No multi-step lifecycle in scope: signup creates an active account; login creates
a session; logout ends it (FR-003). Email is immutable after creation
(no change-email UI in scope).

### 2. Profile — `accounts.models.Profile`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `user` | `OneToOneField(User)` | `on_delete=CASCADE`, `related_name="profile"` | One-to-one with User (spec Key Entities) |
| `avatar_url` | `URLField` | `max_length=200`, `blank=True`, `default=""` | Placeholder for future use |
| `created_at` / `updated_at` | `DateTimeField` | `auto_now_add` / `auto_now` | Audit timestamps |

**Derived (read-only)**: `display_name` property → `self.user.display_name`.
The profile page edits `user.display_name` (FR-005); the Profile row itself gains
no UI in this ticket.

**Zero/one rule**: A `Profile` row is created for every user at signup (signal or
explicit creation in the signup view — implementation detail; existence is the
contract). The dashboard header uses `request.user.display_name`, so it works with
or without a Profile row (graceful fallback to email if display name is blank).

---

## Validation rules (mapped from requirements)

| Rule | Requirement | Enforcement point |
|---|---|---|
| Email format valid | FR-010 | `forms.EmailField` (Django `EmailValidator`) on signup + profile forms |
| Email unique (case-insensitive) | FR-009 | DB `unique=True` (exact) + `email__iexact` check in `SignUpForm.clean_email` |
| Password ≥ 8 chars, ≥ 1 digit, ≥ 1 special char | FR-008 | `accounts.validators.StrongPasswordValidator` in `AUTH_PASSWORD_VALIDATORS`; surfaced by `SignUpForm` via `validate_password` |
| Common passwords rejected | (Django default) | `CommonPasswordValidator` in `AUTH_PASSWORD_VALIDATORS` |
| Display name non-empty on save | FR-005 acceptance 2 | `ProfileForm.clean_display_name` — reject blank/whitespace-only with field error |
| Display name ≤ 80 chars | edge case | `max_length=80` on the model + form field |
| CSRF on every state-changing POST | FR-011 | Django CSRF middleware + `{% csrf_token %}` in all POST forms |

All form validation is server-side; errors render inline next to fields (FR-012)
via Django form error machinery (`{{ form.field.errors }}` in templates).

## Edge-case dispositions (from spec § Edge Cases)

| Edge case | Behavior |
|---|---|
| Password below complexity minimum | Field-level validation error; no account created (FR-008) |
| `a@b.c` malformed-but-regex-passing email | Accepted — Django's `EmailValidator` treats it as structurally valid; deep domain verification out of scope (R7) |
| Session expires mid-profile-edit (save attempt) | `login_required` redirect to `/accounts/login/?next=/profile/`; after re-login the user returns to the form, data not lost (R10) |
| Concurrent logins, same account, multiple browsers | Allowed; each browser has an independent session (R10) |
| Display name over 80 chars | Field error: "Ensure this value has at most 80 characters" |
| Tampered/expired CSRF token on protected pages | HTTP 403 from middleware before view runs (FR-011, R9) |