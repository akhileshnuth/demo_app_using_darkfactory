from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.test import RequestFactory

from accounts.models import ActivityLog, Profile
from accounts.views import ActivityView


class AccountFlowTests(TestCase):
    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("signup"),
            {
                "email": "person@example.com",
                "password1": "Strong-pass1",
                "password2": "Different-pass1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn&#x27;t match.")
        self.assertFalse(get_user_model().objects.exists())

    def test_signup_rejects_duplicate_email_case_insensitively(self):
        get_user_model().objects.create_user(
            email="person@example.com", password="Strong-pass1"
        )

        response = self.client.post(
            reverse("signup"),
            {
                "email": "PERSON@example.com",
                "password1": "Strong-pass1",
                "password2": "Strong-pass1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with this email address already exists.")
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_signup_creates_profile(self):
        self.client.post(
            reverse("signup"),
            {
                "email": "person@example.com",
                "password1": "Strong-pass1",
                "password2": "Strong-pass1",
            },
        )

        user = get_user_model().objects.get(email="person@example.com")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_login_records_activity_and_wrong_password_is_rejected(self):
        user = get_user_model().objects.create_user(
            email="person@example.com", password="Strong-pass1"
        )

        response = self.client.post(
            reverse("login"),
            {"username": user.email, "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ActivityLog.objects.exists())

        response = self.client.post(
            reverse("login"),
            {"username": user.email, "password": "Strong-pass1"},
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(ActivityLog.objects.get().event_type, ActivityLog.EventType.LOGIN)

    @override_settings(USE_TZ=False)
    def test_activity_is_scoped_to_authenticated_user(self):
        user = get_user_model().objects.create_user(
            email="person@example.com", password="Strong-pass1"
        )
        other = get_user_model().objects.create_user(
            email="other@example.com", password="Strong-pass1"
        )
        ActivityLog.objects.create(
            user=user,
            event_type=ActivityLog.EventType.LOGIN,
            description="Own activity",
        )
        ActivityLog.objects.create(
            user=other,
            event_type=ActivityLog.EventType.LOGIN,
            description="Other activity",
        )
        request = RequestFactory().get(reverse("activity"))
        request.user = user
        view = ActivityView()
        view.request = request

        activities = list(view.get_queryset())

        self.assertEqual(activities, list(ActivityLog.objects.filter(user=user)))
        self.assertEqual([activity.description for activity in activities], ["Own activity"])
