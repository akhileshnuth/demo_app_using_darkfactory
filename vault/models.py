import datetime
from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class SampleModel(models.Model):
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return self.created_at < datetime.datetime.now() - datetime.timedelta(days=30)


class AnotherModel(models.Model):
    document = models.ForeignKey(SampleModel, on_delete=models.CASCADE)
    expiry_date = models.DateField()

    def is_duplicate(self):
        return AnotherModel.objects.filter(expiry_date=self.expiry_date).exists()


class Category(models.Model):
    """Document taxonomy: a single top-level vault category."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Document taxonomy: a subject/domain a document belongs to."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    """Document taxonomy: the kind of document (e.g. passport, licence)."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "document type"
        verbose_name_plural = "document types"

    def __str__(self):
        return self.name


class Document(models.Model):
    """A document stored in a user's vault.

    ``expiry_date`` is optional (not every document expires); when set, the
    ``send_expiry_reminders`` management command emails the owner as the date
    approaches. ``reminder_sent_at`` records when that email was dispatched so
    the cron-driven command never sends a duplicate reminder for the same
    document.
    """

    title = models.CharField(max_length=300)
    notes = models.TextField(blank=True, default="")
    expiry_date = models.DateField(blank=True, null=True)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="documents"
    )
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.PROTECT, related_name="documents"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vault_documents",
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="documents"
    )

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("title"), "owner", name="vault_document_title_owner_unique"
            )
        ]

    def __str__(self):
        return self.title
