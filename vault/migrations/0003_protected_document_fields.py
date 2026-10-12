import django.db.models.deletion
import vault.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vault", "0002_document_expiry_reminder_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="content",
            field=models.FileField(blank=True, max_length=500, null=True, upload_to=vault.models.private_document_path),
        ),
        migrations.AddField(
            model_name="document",
            name="protection_status",
            field=models.CharField(choices=[("legacy", "Legacy"), ("pending", "Pending protection"), ("ready", "Ready"), ("deleted", "Deleted")], default="legacy", max_length=16),
        ),
        migrations.AddField(
            model_name="document",
            name="collaborators",
            field=models.ManyToManyField(blank=True, related_name="shared_vault_documents", to=settings.AUTH_USER_MODEL),
        ),
    ]
