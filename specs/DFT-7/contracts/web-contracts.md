# DFT-7 Web Contracts

Interface: server-rendered HTML; no JSON/API contract.

## Public routes

| Route | Methods | Behavior |
|---|---|---|
| `/accounts/signup/` | GET, POST | Render registration; valid submission creates User + Profile, logs in, and redirects to `/dashboard/`; invalid input returns 200 with inline errors and no save. |
| `/accounts/login/` | GET, POST | Render/authenticate email and password; success redirects to `/dashboard/` or safe `next`; failure returns form errors and no session. |
| `/accounts/logout/` | POST | CSRF-protected session termination; redirect to `/accounts/login/`. GET is not a logout contract. |

## Protected routes

| Route | Methods | Behavior |
|---|---|---|
| `/dashboard/` | GET | Login required; renders shell, navigation, current-user identity, and placeholder content. Anonymous requests redirect to login with `next`. |
| `/profile/` | GET, POST | Login required; shows and updates only the current user's display name. Invalid input returns 200 with inline errors and no persistence. |

## Cross-cutting requirements

- All POST forms include a CSRF token; missing/tampered tokens return HTTP 403.
- Protected redirects expose no private page content.
- No route accepts a user id for profile access; ownership is derived from the
  session.
- Settings contract: `AUTH_USER_MODEL=accounts.User`, `LOGIN_URL=/accounts/login/`,
  `LOGIN_REDIRECT_URL=/dashboard/`, and `LOGOUT_REDIRECT_URL=/accounts/login/`.
- Templates are `./templates/registration/`, `./templates/dashboard/`, and
  `./templates/base.html`; visual styling is minimal and neutral.

Password reset, email verification, avatar editing, APIs, and business
dashboard widgets are outside this contract.
