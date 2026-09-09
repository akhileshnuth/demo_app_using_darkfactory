"""Models for the document vault app.

Provides the four core entities: Category, Subject, DocumentType, and
Document. Categories, subjects, and types are shared organizational
taxonomies with globally unique names. Documents are per-user metadata
records linked to one of each taxonomy entity via foreign key.
"""

from django.conf import settings
from django.db import models


class Category(models.Model):
    """Top-level organizational unit in the vault (FR-002)."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Topic or sub-area within the vault (FR-003)."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    """Classification label for documents (FR-004)."""

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
    """Central entity of the vault — a document metadata record (FR-005)."""

    title = models.CharField(max_length=300)
    notes = models.TextField(blank=True, default="")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="documents"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="documents"
    )
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.PROTECT, related_name="documents"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vault_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower("title"),
                "owner",
                name="vault_document_title_owner_unique",
            )
        ]

    def __str__(self):
        return self.title
