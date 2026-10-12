from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import BackupCode, TwoFactorAuth
from accounts.services import complete_enrollment, start_enrollment, totp_code, verify_login_factor


class TwoFactorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="person@example.com", password="Strong-pass1"
        )

    def test_enrollment_requires_valid_totp_and_creates_hashed_backup_codes(self):
        enrollment, _ = start_enrollment(self.user)

        self.assertFalse(complete_enrollment(self.user, enrollment, "000000"))
        codes = complete_enrollment(self.user, enrollment, totp_code(enrollment.secret))

        self.assertEqual(len(codes), 10)
        self.assertTrue(TwoFactorAuth.objects.get(user=self.user).enabled)
        self.assertEqual(BackupCode.objects.filter(user=self.user).count(), 10)
        self.assertNotIn(
            codes[0], BackupCode.objects.filter(user=self.user).first().code_hash
        )

    def test_login_requires_factor_and_backup_codes_are_single_use(self):
        enrollment, _ = start_enrollment(self.user)
        codes = complete_enrollment(self.user, enrollment, totp_code(enrollment.secret))

        self.assertFalse(verify_login_factor(self.user, "111111"))
        self.assertTrue(verify_login_factor(self.user, codes[0]))
        self.assertFalse(verify_login_factor(self.user, codes[0]))

    def test_password_login_redirects_to_factor_challenge(self):
        enrollment, _ = start_enrollment(self.user)
        complete_enrollment(self.user, enrollment, totp_code(enrollment.secret))

        response = self.client.post(
            reverse("login"),
            {"username": self.user.email, "password": "Strong-pass1"},
        )

        self.assertRedirects(response, reverse("two_factor_login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_unenrolled_password_login_is_unchanged(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.email, "password": "Strong-pass1"},
        )

        self.assertRedirects(response, reverse("dashboard"))
