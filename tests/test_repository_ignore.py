import os
import subprocess
import sys
from pathlib import Path

from django.test import TestCase


BASE_DIR = Path(__file__).resolve().parent.parent


class RepositoryIgnoreTests(TestCase):
    def assertIgnored(self, path):
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", path],
            cwd=BASE_DIR,
            check=False,
        )

        self.assertEqual(result.returncode, 0, path)

    def assertNotIgnored(self, path):
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", path],
            cwd=BASE_DIR,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0, path)

    def test_database_sidecars_and_private_documents_are_ignored(self):
        for path in (
            "db.sqlite3",
            "db.sqlite3-shm",
            "db.sqlite3-wal",
            "db.sqlite3-journal",
            "private_documents/report.pdf",
            "private_documents/nested/report.pdf",
        ):
            self.assertIgnored(path)

    def test_local_secrets_are_ignored_but_example_is_not(self):
        for path in (".env", ".env.local", "credentials.pem", "server.key"):
            self.assertIgnored(path)

        self.assertNotIgnored(".env.example")

    def test_secret_key_is_loaded_from_the_environment(self):
        environment = os.environ.copy()
        environment["SECRET_KEY"] = "test-environment-secret"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import config.settings; print(config.settings.SECRET_KEY)",
            ],
            cwd=BASE_DIR,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "test-environment-secret")
