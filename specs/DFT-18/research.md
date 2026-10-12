# Research: Deployment-ready application settings

## Decisions

### Explicit mode and standard-library parsing

Require `DJANGO_ENV` with exact values `development` or `production`; reject
missing/unknown values. Add small helpers in `./config/settings.py` for required
strings, strict booleans, comma-separated lists, bounded integers, and URL/host
validation. Raise configuration errors naming the variable, never its value.

This fixes the current hard-coded `DEBUG`, `SECRET_KEY`, hosts, and SQLite and
avoids a new dependency. A default-to-development selector and third-party
settings package are rejected by FR-001/FR-008, FR-012, and the constitution.

### Development SQLite and production database contract

Keep `BASE_DIR / "db.sqlite3"` only for explicit development. Production
requires non-SQLite `DJANGO_DB_ENGINE` plus `DJANGO_DB_NAME`, `DJANGO_DB_HOST`,
`DJANGO_DB_PORT`, `DJANGO_DB_USER`, and `DJANGO_DB_PASSWORD` as applicable to
the selected backend, with documented optional SSL/lifetime fields. Use
Django's native `DATABASES` shape; do not add a driver. The runtime image must
provide a compatible driver, and adding one to `./requirements.txt` needs human
approval. Discrete fields are preferred over a DSN to avoid secret leakage and
an unapproved parser.

### Explicit public boundary and HTTPS topology

Production requires nonempty `DJANGO_ALLOWED_HOSTS` (hostnames only, no `*`),
nonempty `DJANGO_CSRF_TRUSTED_ORIGINS` (complete `https://` origins, no
wildcards), and an absolute HTTPS `DJANGO_PUBLIC_URL`. Require strict
`DJANGO_TRUST_PROXY_SSL`; set forwarded-protocol trust only when the proxy
overwrites/sanitizes `X-Forwarded-Proto`, then enable redirects and secure
cookies. HSTS values are explicit and rollout-approved rather than silently
preloaded. Unconditional forwarded-header trust is rejected as spoofable.

### Operational settings and redaction

Production requires a non-default `DJANGO_SECRET_KEY`, explicit private
`PRIVATE_DOCUMENT_ROOT`, `STATIC_ROOT`, upload limit, and documented URL values.
SMTP host, port, sender, and explicit TLS/SSL mode are required when expiry
reminders are enabled; TLS and SSL are mutually exclusive, and credentials are
required only when the provider requires authentication. Errors identify names
and constraints but never values, passwords, DSNs, or environment dumps.

### Repository findings resolved

`./config/settings.py` is the sole settings module loaded by `./manage.py`,
`./config/wsgi.py`, and `./config/asgi.py`. Existing consumers include SMTP
expiry reminders, private document storage, upload limits, and Django's
database/session/static subsystems. Existing tests rely on the test database,
`locmem` email, and `MEDIA_ROOT` overrides; the design preserves those seams.
No extension hooks are registered because `./.specify/extensions.yml` is absent.
`./SECURITY_ZONES.md` has placeholder paths that omit settings; this plan does
not alter the zone map, but human review remains required for security behavior.
