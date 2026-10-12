from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountDashboardTests(TestCase):
    def test_registration_logs_user_in_and_opens_dashboard(self):
        response = self.client.post(
            reverse("signup"),
            {
                "email": "person@example.com",
                "password1": "Strong-pass1",
                "password2": "Strong-pass1",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertTrue(
            get_user_model().objects.filter(email="person@example.com").exists()
        )

    def test_private_routes_redirect_unauthenticated_visitors(self):
        for route_name in ("dashboard", "profile"):
            response = self.client.get(reverse(route_name))

            self.assertRedirects(
                response,
                f"{reverse('login')}?next={reverse(route_name)}",
            )

    def test_authenticated_user_can_update_own_profile(self):
        user = get_user_model().objects.create_user(
            email="person@example.com",
            password="Strong-pass1",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("profile"),
            {"display_name": "A Person"},
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.display_name, "A Person")
        self.assertContains(response, "A Person")

    def test_dashboard_contains_profile_and_logout_entry_points(self):
        user = get_user_model().objects.create_user(
            email="person@example.com",
            password="Strong-pass1",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("profile"))
        self.assertContains(response, reverse("logout"))
