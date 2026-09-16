"""Tests for the vault app.

Covers the stub ``SampleModel``/``AnotherModel`` helpers and the DFT-13
expiry reminder management command.  The management command tests validate
that reminders are sent independently of user logins, are idempotent
(no duplicate emails), and go through the real SMTP transport path that
Django automatically redirects to the in-memory locmem backend during
the test run.
"""

import datetime

from django.core import mail
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import AnotherModel, Document, SampleModel

User = get_user_model()


# ---------------------------------------------------------------------------
# Stub-model tests (existing scaffold – kept for backwards compatibility)
# ---------------------------------------------------------------------------


class SampleModelTests(TestCase):
    def setUp(self):
        self.sample = SampleModel.objects.create(title="Test Title")

    def test_is_expired(self):
        self.sample.created_at = datetime.datetime.now() - datetime.timedelta(days=31)
        self.sample.save()
        self.assertTrue(self.sample.is_expired())


class AnotherModelTests(TestCase):
    def setUp(self):
        self.sample = SampleModel.objects.create(title="Test Title")
        self.another = AnotherModel.objects.create(
            document=self.sample, expiry_date=datetime.date.today()
        )

    def test_is_duplicate(self):
        duplicate = AnotherModel(
            document=self.sample, expiry_date=self.another.expiry_date
        )
        self.assertTrue(duplicate.is_duplicate())


# ---------------------------------------------------------------------------
# DFT-13 helpers
# ---------------------------------------------------------------------------


def _user(email="alice@example.com", **kwargs):
    return User.objects.create_user(email=email, password="Test1234!", **kwargs)


def _category(name="Identity"):
    from .models import Category
    return Category.objects.get_or_create(name=name)[0]


def _subject(name="Personal"):
    from .models import Subject
    return Subject.objects.get_or_create(name=name)[0]


def _doctype(name="Passport"):
    from .models import DocumentType
    return DocumentType.objects.get_or_create(name=name)[0]


def _document(owner, *, expiry=None, title="Passport", **kw):
    """Shortcut to create a Document with required taxonomy FKs."""
    cat = _category(kw.get("category_name", "Identity"))
    subj = _subject(kw.get("subject_name", "Personal"))
    dt = _doctype(kw.get("doctype_name", "Passport"))
    return Document.objects.create(
        title=title,
        owner=owner,
        category=cat,
        subject=subj,
        document_type=dt,
        expiry_date=expiry,
    )


# ---------------------------------------------------------------------------
# DFT-13 – expiry reminder management command
# ---------------------------------------------------------------------------


class SendExpiryRemindersCommandTests(TestCase):
    """Validate the ``send_expiry_reminders`` management command (DFT-13)."""

    # -- basic sending -------------------------------------------------------

    def test_sends_email_for_document_expiring_within_window(self):
        owner = _user()
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        doc = _document(owner, expiry=tomorrow)
        self.assertEqual(len(mail.outbox), 0)

        call_command("send_expiry_reminders")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(tomorrow), mail.outbox[0].body)
        self.assertIn(doc.title, mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [owner.email])
        doc.refresh_from_db()
        self.assertIsNotNone(doc.reminder_sent_at)

    def test_sends_email_for_already_expired_document(self):
        """Documents that are past expiry should still be reminded."""
        owner = _user()
        yesterday = timezone.localdate() - datetime.timedelta(days=1)
        _document(owner, expiry=yesterday)

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 1)

    # -- filtering -----------------------------------------------------------

    def test_no_email_for_document_outside_window(self):
        owner = _user()
        far_future = timezone.localdate() + datetime.timedelta(days=90)
        _document(owner, expiry=far_future)

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_for_document_without_expiry(self):
        owner = _user()
        _document(owner, expiry=None)

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_for_inactive_user(self):
        owner = _user(email="gone@example.com", is_active=False)
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        _document(owner, expiry=tomorrow, title="Licence")

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 0)

    # -- idempotency ---------------------------------------------------------

    def test_running_twice_sends_only_one_email(self):
        """Core DFT-13 guarantee: repeated runs must not duplicate emails."""
        owner = _user()
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        _document(owner, expiry=tomorrow, title="Visa")

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 1)

        call_command("send_expiry_reminders")
        # Still exactly one email — reminder_sent_at blocks the second pass
        self.assertEqual(len(mail.outbox), 1)

    def test_already_reminded_document_is_skipped(self):
        owner = _user()
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        doc = _document(owner, expiry=tomorrow, title="ID Card")
        doc.reminder_sent_at = timezone.now()
        doc.save(update_fields=["reminder_sent_at"])

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 0)

    # -- --days option -------------------------------------------------------

    def test_custom_days_option(self):
        owner = _user()
        in_5_days = timezone.localdate() + datetime.timedelta(days=5)
        _document(owner, expiry=in_5_days, title="Permit")

        # Default window is 30 days, so no email with --days=3
        call_command("send_expiry_reminders", days=3)
        self.assertEqual(len(mail.outbox), 0)

        # Widen to 7 → should pick it up
        call_command("send_expiry_reminders", days=7)
        self.assertEqual(len(mail.outbox), 1)

    # -- user login independence ---------------------------------------------

    def test_sends_for_user_who_never_logged_in(self):
        """Reminders must work even if the user has never opened the app."""
        owner = _user(email="newuser@example.com")
        # Simulate never having logged in
        owner.last_login = None
        owner.save(update_fields=["last_login"])

        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        _document(owner, expiry=tomorrow, title="Birth Certificate")

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["newuser@example.com"])

    def test_sends_for_user_who_hasnt_logged_in_for_months(self):
        """The command must not gate on last_login at all."""
        owner = _user(email="inactive@example.com")
        owner.last_login = timezone.now() - datetime.timedelta(days=120)
        owner.save(update_fields=["last_login"])

        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        _document(owner, expiry=tomorrow, title="Insurance")

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 1)

    # -- email content -------------------------------------------------------

    def test_email_uses_display_name_when_set(self):
        owner = _user(email="bob@example.com", display_name="Bob")
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        _document(owner, expiry=tomorrow, title="Deed")

        call_command("send_expiry_reminders")
        self.assertIn("Hi Bob,", mail.outbox[0].body)

    def test_email_falls_back_to_email_for_greeting(self):
        owner = _user(email="carol@example.com")  # no display_name
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        _document(owner, expiry=tomorrow, title="Will")

        call_command("send_expiry_reminders")
        self.assertIn("Hi carol@example.com,", mail.outbox[0].body)

    # -- multiple documents --------------------------------------------------

    def test_multiple_documents_single_owner(self):
        owner = _user()
        t1 = timezone.localdate() + datetime.timedelta(days=1)
        t2 = timezone.localdate() + datetime.timedelta(days=5)
        _document(owner, expiry=t1, title="Passport")
        _document(owner, expiry=t2, title="Licence")

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 2)

    def test_multiple_documents_multiple_owners(self):
        a1 = _user(email="a1@example.com")
        a2 = _user(email="a2@example.com")
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        _document(a1, expiry=tomorrow, title="Doc A")
        _document(a2, expiry=tomorrow, title="Doc B")

        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 2)
        recipients = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(recipients, ["a1@example.com", "a2@example.com"])

    # -- stdout output -------------------------------------------------------

    def test_stdout_reports_count(self):
        import io

        owner = _user()
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        _document(owner, expiry=tomorrow)

        out = io.StringIO()
        call_command("send_expiry_reminders", stdout=out)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Sent 1 expiry reminder email", out.getvalue())

    # -- setting override ----------------------------------------------------

    @override_settings(EXPIRE_REMINDER_DAYS=7)
    def test_respects_expire_reminder_days_setting(self):
        owner = _user()
        in_5 = timezone.localdate() + datetime.timedelta(days=5)
        in_8 = timezone.localdate() + datetime.timedelta(days=8)
        _document(owner, expiry=in_5, title="Card A")
        _document(owner, expiry=in_8, title="Card B")

        # With EXPIRE_REMINDER_DAYS=7, only the 5-day doc qualifies
        call_command("send_expiry_reminders")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Card A", mail.outbox[0].subject)
