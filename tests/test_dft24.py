import json
import subprocess
import unittest
from pathlib import Path


class CssScriptTests(unittest.TestCase):
    frontend = Path(__file__).parents[1] / "frontend"
    css_source = frontend / "css" / "base.css"
    output = frontend / "dist" / "app.css"
    script = frontend / "scripts" / "build-css.js"

    def run_script(self, operation):
        return subprocess.run(
            ["node", str(self.script), operation],
            cwd=self.frontend,
            capture_output=True,
            text=True,
        )

    def test_manifest_exposes_css_scripts(self):
        manifest = json.loads((self.frontend / "package.json").read_text())

        self.assertEqual(manifest["scripts"]["build:css"], "node scripts/build-css.js build")
        self.assertEqual(manifest["scripts"]["lint:css"], "node scripts/build-css.js lint")
        self.assertIn("yarn lint:css && yarn build:css", manifest["scripts"]["verify"])

    def test_build_writes_joined_css_output(self):
        result = self.run_script("build")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), self.css_source.read_text())

    def test_lint_rejects_unbalanced_curly_braces(self):
        original = self.css_source.read_text()
        try:
            self.css_source.write_text(f"{original}\n.invalid {{\n")
            result = self.run_script("lint")
        finally:
            self.css_source.write_text(original)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unbalanced curly braces", result.stderr)
