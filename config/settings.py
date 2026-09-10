"""
Django settings for the DFT-7 scaffold project.

Provides email/password registration, login/logout, a profile page for
editing a display name, and an authenticated dashboard shell. Uses Django's
built-in authentication stack with a minimal custom User model keyed on
email (see ``accounts.models.User``).
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Dev-only key. A real deployment must override this.
SECRET_KEY = "django-insecure-dft-7-scaffold-dev-key"

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

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