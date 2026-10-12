# Data Model: Deployment configuration

No database tables or migrations are introduced. The model is the validated
runtime configuration assembled by `./config/settings.py`.

## Configuration mode

- **Source**: `DJANGO_ENV`.
- **Values**: exact `development` or `production`.
- **Rules**: missing, blank, or other values fail; production never falls back.
- **Lifecycle**: selected once during settings import.

## Configuration groups

- **Security**: `DJANGO_SECRET_KEY` (secret, required and non-default in
  production), secure cookies, proxy trust, and HSTS controls.
- **Network**: `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, and
  `DJANGO_PUBLIC_URL` (non-secret, explicit production restrictions).
- **Persistence**: `DJANGO_DB_ENGINE`, `DJANGO_DB_NAME`, `DJANGO_DB_HOST`,
  `DJANGO_DB_PORT`, `DJANGO_DB_USER`, and `DJANGO_DB_PASSWORD` (password secret),
  plus documented backend-specific SSL/lifetime fields.
- **Storage**: `PRIVATE_DOCUMENT_ROOT`, `STATIC_ROOT`, and positive bounded
  `DOCUMENT_UPLOAD_MAX_BYTES`; private storage must be outside public/static roots.
- **Email**: SMTP host/port/user/password, TLS/SSL flags, and
  `DEFAULT_FROM_EMAIL`; password is secret and requiredness is conditional.

## Invariants

1. Lists normalize whitespace and reject empty entries, wildcards, and malformed values.
2. Booleans accept only documented literals; malformed values fail rather than becoming false.
3. Ports and limits are integers in safe documented ranges.
4. Secrets never occur in exception text, reprs, logs, or diagnostics.
5. Complete production configuration validates before Django serves requests.
