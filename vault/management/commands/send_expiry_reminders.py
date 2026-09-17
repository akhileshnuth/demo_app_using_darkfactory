"""Scan all vault documents and email reminders for those that expire soon.

Designed to run as a daily cron job, independent of user logins:

    0 7 * * * cd /srv/app && python manage.py send_expiry_reminders

Each document is reminded **at most once** (``reminder_sent_at`` is set after
a successful send), so repeated cron runs never produce duplicate emails.
"""

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ...models import Document


class Command(BaseCommand):
    """Email vault owners about documents expiring within the reminder window."""

    help = (
        "Scan every user's vault documents and send reminder emails for any "
        "that expire within the configured window (default 30 days). "
        "Safe to run repeatedly — each document receives at most one email."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help=(
                "Reminder window in days. Defaults to the "
                "EXPIRE_REMINDER_DAYS setting (30 when unset). "
                "Documents expiring on or before today + DAYS are flagged."
            ),
        )

    def handle(self, *args, **options):
        # ``--days 0`` is a valid window (today/expired only), so fall back
        # to the setting only when the option was not supplied at all.
        days = options["days"]
        if days is None:
            days = getattr(settings, "EXPIRE_REMINDER_DAYS", 30)
        today = timezone.localdate()
        upper_bound = today + timedelta(days=days)

        # Only active users with a usable email; only documents that
        # have a set expiry date and have not been reminded yet.
        documents = (
            Document.objects.filter(
                owner__is_active=True,
                owner__email__isnull=False,
                expiry_date__isnull=False,
                expiry_date__lte=upper_bound,
                reminder_sent_at__isnull=True,
            )
            .select_related("owner")
            .order_by("id")
        )

        sent = 0
        for document in documents:
            # atomic per-document so a crash mid-loop never silently
            # drops the reminder flag (transaction saves on success).
            with transaction.atomic():
                owner = document.owner
                subject = f"Reminder: '{document.title}' is expiring soon"
                display = owner.display_name or owner.email
                message = (
                    f"Hi {display},\n\n"
                    f"Your document '{document.title}' is set to expire on "
                    f"{document.expiry_date:%Y-%m-%d}. Please review it or "
                    f"remove it from your vault.\n\n"
                    f"Expiry reminders are sent automatically by a scheduled "
                    f"job, so you receive this even if you haven't signed in "
                    f"recently.\n"
                )
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [owner.email],
                )
                Document.objects.filter(pk=document.pk).update(
                    reminder_sent_at=timezone.now()
                )
            sent += 1

        self.stdout.write(self.style.SUCCESS(f"Sent {sent} expiry reminder email(s)."))
