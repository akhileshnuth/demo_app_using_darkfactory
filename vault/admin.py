"""Admin registrations for the vault app (FR-020).

Registers Category, Subject, DocumentType, and Document with the
Django admin for administrative management.
"""

from django.contrib import admin

from .models import Category, Document, DocumentType, Subject


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "subject", "document_type",
                    "created_at", "updated_at")
    list_filter = ("category", "subject", "document_type")
    search_fields = ("title", "owner__email")
