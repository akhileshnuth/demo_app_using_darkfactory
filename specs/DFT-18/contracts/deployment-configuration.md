# Deployment configuration contract

Deployment injects these variables at runtime. Do not commit values or secret
`.env` files. These are the canonical application names.

| Variable | Required | Secret | Form / validation |
|---|---:|---:|---|
| `DJANGO_ENV` | all | no | Exact `development` or `production` |
| `DJANGO_SECRET_KEY` | production | yes | Nonblank, non-default signing key |
| `DJANGO_ALLOWED_HOSTS` | production | no | Comma-separated hostnames; no blank, scheme, path, or `*` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | production | no | Comma-separated complete `https://` origins; no wildcard |
| `DJANGO_PUBLIC_URL` | production | no | Absolute public `https://` URL |
| `DJANGO_DB_ENGINE` | production | no | Installed Django backend; SQLite rejected |
| `DJANGO_DB_NAME` / `DJANGO_DB_HOST` | production | no | Backend name and host; nonblank where required |
| `DJANGO_DB_PORT` | production | no | Integer 1–65535 where required |
| `DJANGO_DB_USER` / `DJANGO_DB_PASSWORD` | production | password | Backend credentials where required |
| `DJANGO_TRUST_PROXY_SSL` | production | no | Strict boolean; true only for a sanitizing HTTPS proxy |
| `DJANGO_HSTS_SECONDS` | production | no | Nonnegative rollout-approved integer |
| `DJANGO_HSTS_INCLUDE_SUBDOMAINS` / `DJANGO_HSTS_PRELOAD` | production | no | Strict booleans, only with explicit approval |
| `PRIVATE_DOCUMENT_ROOT` | production | no | Persistent writable private path outside public/static roots |
| `STATIC_ROOT` | production | no | Absolute writable static collection path |
| `DOCUMENT_UPLOAD_MAX_BYTES` | production | no | Positive bounded integer matching proxy limits |
| `EMAIL_HOST` / `EMAIL_PORT` | SMTP enabled | no | Host and port 1–65535 |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | Provider auth | password | Credentials never logged |
| `EMAIL_USE_TLS` / `EMAIL_USE_SSL` | SMTP enabled | no | Strict booleans; mutually exclusive |
| `DEFAULT_FROM_EMAIL` | Reminders enabled | no | Valid nonblank sender address |

Development retains current local defaults only after explicit
`DJANGO_ENV=development`. Production errors may name a variable and constraint,
but never reveal secret values, passwords, DSNs, or the full environment.
Operators must approve proxy trust, HSTS rollout, public hosts/origins, database
driver availability, SMTP authentication, and persistent storage/backup policy.
