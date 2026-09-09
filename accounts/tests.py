"""Tests for the accounts app.

Covers signup (FR-001, FR-008, FR-009, FR-010), login/logout (FR-002,
FR-003), profile editing (FR-005), access control (FR-007) and CSRF
protection (FR-011). Uses Django's bundled test runner with the in-memory
SQLite test database.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Profile

User = get_user_model()


class SignUpViewTests(TestCase):
    valid_payload = {
        "email": "ada@example.com",
        "password1": "Sup3r-secret!",
        "password2": "Sup3r-secret!",
    }

    def test_signup_page_renders(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create account")
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')

    def test_signup_creates_user_profile_and_redirects_to_dashboard(self):
        response = self.client.post(reverse("signup"), self.valid_payload)
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(email="ada@example.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("Sup3r-secret!"))
        self.assertTrue(Profile.objects.filter(user=user).exists())
        # The new user is logged in and can reach the dashboard.
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_signup_duplicate_email_is_rejected(self):
        User.objects.create_user(email="ada@example.com", password="Sup3r-secret!")
        payload = dict(self.valid_payload, email="ADA@example.com")
        response = self.client.post(reverse("signup"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(User.objects.count(), 1)

    def test_signup_invalid_email_is_rejected(self):
        payload = dict(self.valid_payload, email="not-an-email")
        response = self.client.post(reverse("signup"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address")
        self.assertEqual(User.objects.count(), 0)

    def test_signup_weak_passwords_are_rejected(self):
        # "Secret12": no special char; "Secret!!": no digit; "Secr1!": too short.
        for password in ("Secret12", "Secret!!", "Secr1!"):
            with self.subTest(password=password):
                User.objects.all().delete()
                payload = dict(
                    self.valid_payload,
                    password1=password,
                    password2=password,
                )
                response = self.client.post(reverse("signup"), payload)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(User.objects.count(), 0)

    def test_signup_password_mismatch_is_rejected(self):
        payload = dict(self.valid_payload, password2="Different12!")
        response = self.client.post(reverse("signup"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "didn't match")
        self.assertEqual(User.objects.count(), 0)


class LoginLogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ada@example.com", password="Sup3r-secret!"
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_login_with_valid_credentials_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": "ada@example.com", "password": "Sup3r-secret!"},
        )
        self.assertRedirects(response, reverse("dashboard"))
        # A session is established: dashboard is now reachable.
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_login_redirects_to_next_page(self):
        response = self.client.post(
            reverse("login") + "?next=" + reverse("profile"),
            {"username": "ada@example.com", "password": "Sup3r-secret!"},
        )
        self.assertRedirects(response, reverse("profile"))

    def test_login_with_wrong_password_stays_on_login_page(self):
        response = self.client.post(
            reverse("login"),
            {"username": "ada@example.com", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct")
        # No session was created.
        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            reverse("login") + "?next=" + reverse("dashboard"),
        )

    def test_login_page_redirects_authenticated_users(self):
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_logout_terminates_session_and_redirects_to_login(self):
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            reverse("login") + "?next=" + reverse("dashboard"),
        )

    def test_logout_rejects_get(self):
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ada@example.com",
            password="Sup3r-secret!",
            display_name="Ada",
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("profile")
        )

    def test_profile_post_after_logout_redirects_to_login(self):
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        self.client.post(reverse("logout"))
        response = self.client.post(
            reverse("profile"), {"display_name": "Changed"}
        )
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("profile")
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Ada")

    def test_profile_page_shows_current_display_name(self):
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ada")
        self.assertContains(response, 'value="Ada"')

    def test_profile_update_persists_and_reflects_new_name(self):
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.post(
            reverse("profile"), {"display_name": "Ada Lovelace"}
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Ada Lovelace")
        # The re-rendered page shows the new name (profile + dashboard header).
        self.assertContains(response, "Ada Lovelace")

    def test_profile_blank_display_name_is_rejected(self):
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.post(reverse("profile"), {"display_name": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Ada")

    def test_profile_display_name_over_80_chars_is_rejected(self):
        self.client.login(email="ada@example.com", password="Sup3r-secret!")
        response = self.client.post(
            reverse("profile"), {"display_name": "A" * 81}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "at most 80 characters")
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Ada")


class CsrfProtectionTests(TestCase):
    """FR-011: missing or tampered CSRF tokens yield 403 with no side effects."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="ada@example.com",
            password="Sup3r-secret!",
            display_name="Ada",
        )

    def test_login_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("login"),
            {"username": "ada@example.com", "password": "Sup3r-secret!"},
        )
        self.assertEqual(response.status_code, 403)

    def test_profile_post_with_tampered_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.login(email="ada@example.com", password="Sup3r-secret!")
        response = client.post(
            reverse("profile"),
            {
                "csrfmiddlewaretoken": "tampered-token",
                "display_name": "Changed",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Ada")

    def test_dashboard_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("dashboard"))
        self.assertEqual(response.status_code, 403)


class UserManagerTests(TestCase):
    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email="ADA@Example.COM", password="Sup3r-secret!"
        )
        self.assertEqual(user.email, "ada@example.com")

    def test_create_superuser_sets_staff_and_superuser(self):
        user = User.objects.create_superuser(
            email="root@example.com", password="Sup3r-secret!"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)