from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies = [
        ("vault", "0002_document_expiry_reminder_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="subject",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="documenttype",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                Lower("name"), name="vault_category_name_ci_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="subject",
            constraint=models.UniqueConstraint(
                Lower("name"), name="vault_subject_name_ci_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="documenttype",
            constraint=models.UniqueConstraint(
                Lower("name"), name="vault_document_type_name_ci_unique"
            ),
        ),
    ]
