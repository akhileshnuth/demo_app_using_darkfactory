"""
Django settings for the DFT-7 scaffold project.

Provides email/password registration, login/logout, a profile page for
editing a display name, and an authenticated dashboard shell. Uses Django's
built-in authentication stack with a minimal custom User model keyed on
email (see ``accounts.models.User``).
"""

import os
from email.utils import parseaddr
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]

def _required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} is required")
    return value


def _boolean(name, default=None):
    value = os.environ.get(name)
    if value is None and default is not None:
        return default
    if value is None:
        raise ImproperlyConfigured(f"{name} is required and must be true or false")
    value = value.strip().lower()
    if value not in {"true", "false"}:
        raise ImproperlyConfigured(f"{name} must be true or false")
    return value == "true"


def _integer(name, minimum, maximum=None, default=None):
    value = os.environ.get(name)
    if value is None and default is not None:
        return default
    if value is None:
        raise ImproperlyConfigured(f"{name} is required")
    try:
        result = int(value.strip())
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be an integer") from exc
    if result < minimum or (maximum is not None and result > maximum):
        limit = f" and at most {maximum}" if maximum is not None else ""
        raise ImproperlyConfigured(f"{name} must be at least {minimum}{limit}")
    return result


def _list(name, *, hosts=False):
    values = [item.strip() for item in _required(name).split(",")]
    if any(not item or item == "*" for item in values):
        raise ImproperlyConfigured(f"{name} must not contain empty or wildcard values")
    for value in values:
        if hosts:
            if "://" in value or "/" in value or " " in value:
                raise ImproperlyConfigured(f"{name} contains an invalid host")
        elif _origin(value) is None:
            raise ImproperlyConfigured(f"{name} contains an invalid HTTPS origin")
    return values


def _origin(value):
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
        return None
    if parsed.query or parsed.fragment or "*" in parsed.netloc:
        return None
    try:
        parsed.port
    except ValueError:
        return None
    return value.rstrip("/")


def _absolute_path(name):
    value = Path(_required(name))
    if not value.is_absolute():
        raise ImproperlyConfigured(f"{name} must be an absolute path")
    return value.resolve()


DJANGO_ENV = os.environ.get("DJANGO_ENV", "").strip()
if DJANGO_ENV not in {"development", "production"}:
    raise ImproperlyConfigured("DJANGO_ENV must be exactly development or production")

if DJANGO_ENV == "production":
    SECRET_KEY = _required("DJANGO_SECRET_KEY")
    if SECRET_KEY.startswith("django-insecure-"):
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must not use a development key")
else:
    SECRET_KEY = os.environ.get(
        "DJANGO_SECRET_KEY", "django-insecure-dft-7-scaffold-dev-key"
    )

DEBUG = DJANGO_ENV == "development"

if DJANGO_ENV == "production":
    ALLOWED_HOSTS = _list("DJANGO_ALLOWED_HOSTS", hosts=True)
    CSRF_TRUSTED_ORIGINS = _list("DJANGO_CSRF_TRUSTED_ORIGINS")
    PUBLIC_URL = _origin(_required("DJANGO_PUBLIC_URL"))
    if PUBLIC_URL is None:
        raise ImproperlyConfigured("DJANGO_PUBLIC_URL must be an absolute HTTPS URL")
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    CSRF_TRUSTED_ORIGINS = []
    PUBLIC_URL = "http://localhost"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "dashboard",
    "checklists",
    "vault",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "checklists.context_processors.unread_notifications",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

if DJANGO_ENV == "production":
    DATABASES = {
        "default": {
            "ENGINE": _required("DJANGO_DB_ENGINE"),
            "NAME": _required("DJANGO_DB_NAME"),
            "HOST": _required("DJANGO_DB_HOST"),
            "PORT": str(_integer("DJANGO_DB_PORT", 1, 65535)),
            "USER": _required("DJANGO_DB_USER"),
            "PASSWORD": _required("DJANGO_DB_PASSWORD"),
        }
    }
    if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
        raise ImproperlyConfigured("DJANGO_DB_ENGINE must not select SQLite in production")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "accounts.validators.StrongPasswordValidator",
    },
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth flow configuration (FR-001, FR-002, FR-003, FR-007).
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# DFT-9: emergency access auto-grant window in hours (FR-011). Not user-facing.
CLA_OK_EMERGENCY_AUTO_GRANT_HOURS = 72

# DFT-9: code-defined quick-start checklist templates (FR-017). No admin UI.
CLA_OK_TEMPLATES = {
    "Grocery List": ["Milk", "Eggs", "Bread", "Coffee", "Butter"],
    "Travel Packing": [
        "Passport / ID",
        "Toiletries",
        "Chargers",
        "Medications",
        "Comfortable shoes",
    ],
    "Meeting Agenda": [
        "Welcome & introductions",
        "Review previous action items",
        "New business",
        "Decisions & owners",
        "Next steps & wrap-up",
    ],
}

# DFT-13: expiry reminders run from a scheduled management command
# (``manage.py send_expiry_reminders``), not from dashboard page loads.
# Documents with an expiry date inside this many days are reminded by email.
# The window can also be overridden per run with the command's ``--days``
# option.
EXPIRE_REMINDER_DAYS = 30

# DFT-13: real SMTP transport for reminder emails. During tests Django replaces
# this backend with the in-memory ``locmem`` backend automatically.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
if DJANGO_ENV == "production":
    EMAIL_HOST = _required("EMAIL_HOST")
    EMAIL_PORT = _integer("EMAIL_PORT", 1, 65535)
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "").strip()
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    if bool(EMAIL_HOST_USER) != bool(EMAIL_HOST_PASSWORD):
        raise ImproperlyConfigured(
            "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD must be supplied together"
        )
    EMAIL_USE_TLS = _boolean("EMAIL_USE_TLS")
    EMAIL_USE_SSL = _boolean("EMAIL_USE_SSL")
    if EMAIL_USE_TLS and EMAIL_USE_SSL:
        raise ImproperlyConfigured("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be true")
    DEFAULT_FROM_EMAIL = _required("DEFAULT_FROM_EMAIL")
    if "@" not in parseaddr(DEFAULT_FROM_EMAIL)[1]:
        raise ImproperlyConfigured("DEFAULT_FROM_EMAIL must contain a valid address")
else:
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
    EMAIL_PORT = _integer("EMAIL_PORT", 1, 65535, default=25)
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = _boolean("EMAIL_USE_TLS", default=False)
    EMAIL_USE_SSL = _boolean("EMAIL_USE_SSL", default=False)
    DEFAULT_FROM_EMAIL = os.environ.get(
        "DEFAULT_FROM_EMAIL", "Vault Reminders <noreply@localhost>"
    )

# DFT-17: never place document bytes below a static or public media root.
if DJANGO_ENV == "production":
    PRIVATE_DOCUMENT_ROOT = _absolute_path("PRIVATE_DOCUMENT_ROOT")
    STATIC_ROOT = _absolute_path("STATIC_ROOT")
    if (
        PRIVATE_DOCUMENT_ROOT == STATIC_ROOT
        or STATIC_ROOT in PRIVATE_DOCUMENT_ROOT.parents
        or PRIVATE_DOCUMENT_ROOT in STATIC_ROOT.parents
    ):
        raise ImproperlyConfigured("PRIVATE_DOCUMENT_ROOT must be outside STATIC_ROOT")
    DOCUMENT_UPLOAD_MAX_BYTES = _integer("DOCUMENT_UPLOAD_MAX_BYTES", 1, 1024 * 1024 * 1024)
else:
    PRIVATE_DOCUMENT_ROOT = Path(
        os.environ.get("PRIVATE_DOCUMENT_ROOT", BASE_DIR / "private_documents")
    )
    STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles"))
    DOCUMENT_UPLOAD_MAX_BYTES = _integer(
        "DOCUMENT_UPLOAD_MAX_BYTES", 1, 1024 * 1024 * 1024, default=10 * 1024 * 1024
    )
MEDIA_ROOT = PRIVATE_DOCUMENT_ROOT

if DJANGO_ENV == "production":
    TRUST_PROXY_SSL = _boolean("DJANGO_TRUST_PROXY_SSL")
    if not TRUST_PROXY_SSL:
        raise ImproperlyConfigured(
            "DJANGO_TRUST_PROXY_SSL must be true for the HTTPS proxy topology"
        )
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = _integer("DJANGO_HSTS_SECONDS", 0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _boolean("DJANGO_HSTS_INCLUDE_SUBDOMAINS")
    SECURE_HSTS_PRELOAD = _boolean("DJANGO_HSTS_PRELOAD")
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
