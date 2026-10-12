import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_two_factor")]

    operations = [
        migrations.AlterField(
            model_name="activitylog",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name="activity_logs", to="accounts.user"),
        ),
        migrations.AddField(
            model_name="activitylog",
            name="context",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="activitylog",
            name="document_reference",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
    ]
