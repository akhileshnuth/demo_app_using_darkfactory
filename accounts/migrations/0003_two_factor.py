import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_activitylog")]

    operations = [
        migrations.AlterField(
            model_name="activitylog",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("login", "Login"),
                    ("share_created", "Share created"),
                    ("share_accessed", "Share accessed"),
                    ("share_revoked", "Share revoked"),
                    ("emergency_requested", "Emergency requested"),
                    ("emergency_granted", "Emergency granted"),
                    ("emergency_denied", "Emergency denied"),
                    ("two_factor_enabled", "Two-factor enabled"),
                    ("two_factor_verified", "Two-factor verified"),
                    ("two_factor_failed", "Two-factor verification failed"),
                    ("two_factor_disabled", "Two-factor disabled"),
                ],
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="TwoFactorAuth",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("secret", models.CharField(max_length=255)),
                ("enabled", models.BooleanField(default=False)),
                ("failed_attempts", models.PositiveIntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="two_factor", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="TwoFactorEnrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("secret", models.CharField(max_length=255)),
                ("expires_at", models.DateTimeField()),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="two_factor_enrollments", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="BackupCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code_hash", models.CharField(max_length=128)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="backup_codes", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="TwoFactorRecoveryRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email_verified", models.BooleanField(default=False)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_two_factor_recoveries", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="two_factor_recovery_requests", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
