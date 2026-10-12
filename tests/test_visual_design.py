from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class VisualDesignTests(TestCase):
    def test_shared_shell_exposes_accessible_navigation_and_focus_target(self):
        user = get_user_model().objects.create_user(
            email="person@example.com", password="Strong-pass1"
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, 'class="skip-link"')
        self.assertContains(response, 'aria-label="Main navigation"')
        self.assertContains(response, 'id="main"')

    def test_visual_system_defines_shared_states_and_small_viewport_rules(self):
        stylesheet = Path(__file__).resolve().parents[1] / "static" / "css" / "base.css"
        css = stylesheet.read_text()

        for rule in (
            ":focus-visible",
            "button:hover",
            "button:disabled",
            ".empty",
            ".messages",
            "prefers-reduced-motion",
            "forced-colors",
            "@media (max-width: 600px)",
        ):
            self.assertIn(rule, css)

        self.assertIn("--color-accent", css)
        self.assertIn("--color-surface", css)
