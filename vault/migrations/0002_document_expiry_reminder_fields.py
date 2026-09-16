"""Add expiry tracking fields to Document (DFT-13).

``expiry_date`` lets a document carry an optional expiry date; the
``send_expiry_reminders`` management command uses it to find documents that
are due and ``reminder_sent_at`` records that the reminder email was already
sent so repeated cron runs never send duplicates.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vault", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="expiry_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="document",
            name="reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]