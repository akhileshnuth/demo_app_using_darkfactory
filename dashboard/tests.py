"""Tests for the dashboard shell and its access control.

Covers the shell layout (FR-006, SC-006), the header display name with
email fallback, and unauthenticated access control (FR-007, SC-003).
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class DashboardViewTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("dashboard")
        )
        # No dashboard content leaks into the redirect response (SC-003).
        self.assertNotContains(response, "sidebar")
        self.assertNotContains(response, "Welcome")

    def test_dashboard_renders_shell_for_authenticated_user(self):
        User.objects.create_user(
            email="ada@example.com",
            password="Sup3r-secret!",
            display_name="Ada",
        )
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="sidebar"')
        self.assertContains(response, 'id="header"')
        self.assertContains(response, 'id="main"')
        self.assertContains(response, "Ada")
        self.assertContains(response, "Log out")
        self.assertContains(response, reverse("dashboard"))
        self.assertContains(response, reverse("profile"))
        self.assertContains(response, reverse("logout"))

    def test_dashboard_header_falls_back_to_email(self):
        User.objects.create_user(
            email="ada@example.com", password="Sup3r-secret!"
        )
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ada@example.com")