import json
from pathlib import Path

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent


class UploadPreviewTests(SimpleTestCase):
    def test_frontend_lint_script_uses_eslint_on_source_directory(self):
        package = json.loads((BASE_DIR / "frontend/package.json").read_text())

        self.assertEqual(package["scripts"]["lint"], "eslint src")

    def test_frontend_uses_recommended_eslint_rules(self):
        config = json.loads((BASE_DIR / "frontend/.eslintrc.json").read_text())

        self.assertEqual(config["extends"], "eslint:recommended")

    def test_upload_preview_displays_file_name_and_size(self):
        script = (BASE_DIR / "frontend/src/upload-preview.js").read_text()

        self.assertIn("file.name", script)
        self.assertIn("formatFileSize(file.size)", script)
        self.assertIn('input.addEventListener("change"', script)
