from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from vault.models import Category, Document, DocumentType, Subject


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ExpiryReminderCommandTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="owner@example.com",
            password="Strong-pass1",
            display_name="A Person",
        )
        self.inactive = get_user_model().objects.create_user(
            email="inactive@example.com", password="Strong-pass1", is_active=False
        )
        self.category = Category.objects.create(name="Personal")
        self.subject = Subject.objects.create(name="Identity")
        self.document_type = DocumentType.objects.create(name="Record")

    def make_document(self, owner, title, expiry_date, reminder_sent_at=None):
        return Document.objects.create(
            owner=owner,
            title=title,
            expiry_date=expiry_date,
            reminder_sent_at=reminder_sent_at,
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
        )

    def test_command_sends_eligible_documents_once(self):
        today = date.today()
        document = self.make_document(self.user, "Passport", today + timedelta(days=3))
        self.make_document(self.user, "Later", today + timedelta(days=31))
        self.make_document(self.inactive, "Inactive", today)

        with patch(
            "vault.management.commands.send_expiry_reminders.timezone.localdate",
            return_value=today,
        ):
            call_command("send_expiry_reminders", days=30)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Passport", mail.outbox[0].subject)
        document.refresh_from_db()
        self.assertIsNotNone(document.reminder_sent_at)

        with patch(
            "vault.management.commands.send_expiry_reminders.timezone.localdate",
            return_value=today,
        ):
            call_command("send_expiry_reminders", days=30)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_failure_does_not_mark_document_as_reminded(self):
        document = self.make_document(
            self.user, "Passport", date.today() + timedelta(days=1)
        )

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_HOST="127.0.0.1", EMAIL_PORT=1):
            with patch(
                "vault.management.commands.send_expiry_reminders.timezone.localdate",
                return_value=date.today(),
            ):
                with self.assertRaises(Exception):
                    call_command("send_expiry_reminders", days=30)

        document.refresh_from_db()
        self.assertIsNone(document.reminder_sent_at)
