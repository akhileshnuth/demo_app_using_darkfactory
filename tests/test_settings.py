import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


class SettingsContractTests(SimpleTestCase):
    def load_settings(self, values):
        environment = os.environ.copy()
        for name in list(environment):
            if name.startswith(("DJANGO_", "EMAIL_", "PRIVATE_", "STATIC_ROOT")):
                environment.pop(name)
        environment.update(values)
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "import config.settings; print(config.settings.DEBUG); "
                "print(config.settings.ALLOWED_HOSTS)",
            ],
            cwd=Path(__file__).resolve().parent.parent,
            env=environment,
            capture_output=True,
            text=True,
        )

    def production_values(self):
        return {
            "DJANGO_ENV": "production",
            "DJANGO_SECRET_KEY": "deployment-only-secret",
            "DJANGO_ALLOWED_HOSTS": "app.example.com, admin.example.com",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://app.example.com",
            "DJANGO_PUBLIC_URL": "https://app.example.com",
            "DJANGO_DB_ENGINE": "django.db.backends.postgresql",
            "DJANGO_DB_NAME": "app",
            "DJANGO_DB_HOST": "db.internal",
            "DJANGO_DB_PORT": "5432",
            "DJANGO_DB_USER": "app",
            "DJANGO_DB_PASSWORD": "database-secret",
            "DJANGO_TRUST_PROXY_SSL": "true",
            "DJANGO_HSTS_SECONDS": "3600",
            "DJANGO_HSTS_INCLUDE_SUBDOMAINS": "false",
            "DJANGO_HSTS_PRELOAD": "false",
            "PRIVATE_DOCUMENT_ROOT": "/srv/app/private",
            "STATIC_ROOT": "/srv/app/static",
            "DOCUMENT_UPLOAD_MAX_BYTES": "10485760",
            "EMAIL_HOST": "smtp.example.com",
            "EMAIL_PORT": "587",
            "EMAIL_USE_TLS": "true",
            "EMAIL_USE_SSL": "false",
            "DEFAULT_FROM_EMAIL": "Vault <noreply@example.com>",
        }

    def test_production_configuration_loads_without_debug(self):
        result = self.load_settings(self.production_values())

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("False", result.stdout)

    def test_missing_production_setting_fails_without_secret_redaction(self):
        values = self.production_values()
        values.pop("DJANGO_ALLOWED_HOSTS")

        result = self.load_settings(values)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)
        self.assertNotIn("database-secret", result.stderr)

    def test_wildcard_origin_is_rejected(self):
        values = self.production_values()
        values["DJANGO_CSRF_TRUSTED_ORIGINS"] = "*"

        result = self.load_settings(values)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_CSRF_TRUSTED_ORIGINS", result.stderr)

    def test_development_keeps_sqlite_defaults(self):
        result = self.load_settings({"DJANGO_ENV": "development"})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("True", result.stdout)
