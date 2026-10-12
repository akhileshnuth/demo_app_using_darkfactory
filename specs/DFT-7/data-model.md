# DFT-7 Data Model

## User (`accounts.User`)

An `AbstractUser` subclass identified by email. Keep inherited password,
permissions, active/staff flags, timestamps, and groups. Remove `username`, set
`USERNAME_FIELD = "email"`, require a unique `EmailField`, and add optional
`display_name` (`CharField`, max 80). The manager normalizes email and supports
normal user/superuser creation.

## Profile (`accounts.Profile`)

One-to-one with User, `on_delete=CASCADE`, with a reverse `profile` relation.
The model remains extensible, but the initial user-facing schema exposes no
avatar or other optional fields. A profile row is created during registration;
the editable display name remains one source of truth on User and may be
rendered through the Profile relationship.

## Dashboard Shell

Not a persisted entity. It is an authenticated page structure containing a
header, navigation links to dashboard/profile/account actions, and a placeholder
main area. It may render the current user's display name/email but must never
query or accept another user's identifier.

## Relationships and ownership

- One User has at most one Profile; deleting User cascades to Profile.
- Profile and dashboard reads/writes are always scoped to the authenticated
  request user.
- Email is the account identifier and is not editable in this scaffold.

## Validation and state behavior

- Email uses Django email validation and case-insensitive duplicate detection.
- Password confirmation and configured Django password validators run on
  registration; passwords are hashed and never persisted in plaintext.
- Display name is the only editable profile field, capped at 80 characters;
  blank/whitespace-only submissions remain on the form with errors and do not
  save.
- Every state-changing POST requires CSRF. Anonymous private-route requests
  redirect to login without private content. Logout ends the session and
  redirects to login.

## Out-of-scope existing data

Later-ticket entities such as `ActivityLog`, checklist records, and vault
records are not part of DFT-7's data contract and must not expand this feature's
profile/dashboard scope.
