from django.urls import path

from .views import (
    CategoryCreateView, CategoryDeleteView, CategoryListView, CategoryUpdateView,
    DocumentCreateView, DocumentDeleteView, DocumentDetailView, DocumentListView,
    DocumentTypeCreateView, DocumentTypeDeleteView, DocumentTypeListView,
    DocumentTypeUpdateView, DocumentUpdateView, ExportView, LegacyDocumentListRedirect,
    SubjectCreateView, SubjectDeleteView, SubjectListView, SubjectUpdateView,
)

app_name = "vault"

urlpatterns = [
    path("vault/", DocumentListView.as_view(), name="document_list"),
    path("vault/documents/", LegacyDocumentListRedirect.as_view(), name="legacy_document_list"),
    path("vault/documents/new/", DocumentCreateView.as_view(), name="document_create"),
    path("vault/documents/<int:pk>/", DocumentDetailView.as_view(), name="document_detail"),
    path("vault/documents/<int:pk>/edit/", DocumentUpdateView.as_view(), name="document_update"),
    path("vault/documents/<int:pk>/delete/", DocumentDeleteView.as_view(), name="document_delete"),
    path("vault/categories/", CategoryListView.as_view(), name="category_list"),
    path("vault/categories/new/", CategoryCreateView.as_view(), name="category_create"),
    path("vault/categories/<int:pk>/edit/", CategoryUpdateView.as_view(), name="category_update"),
    path("vault/categories/<int:pk>/delete/", CategoryDeleteView.as_view(), name="category_delete"),
    path("vault/subjects/", SubjectListView.as_view(), name="subject_list"),
    path("vault/subjects/new/", SubjectCreateView.as_view(), name="subject_create"),
    path("vault/subjects/<int:pk>/edit/", SubjectUpdateView.as_view(), name="subject_update"),
    path("vault/subjects/<int:pk>/delete/", SubjectDeleteView.as_view(), name="subject_delete"),
    path("vault/document-types/", DocumentTypeListView.as_view(), name="documenttype_list"),
    path("vault/document-types/new/", DocumentTypeCreateView.as_view(), name="documenttype_create"),
    path("vault/document-types/<int:pk>/edit/", DocumentTypeUpdateView.as_view(), name="documenttype_update"),
    path("vault/document-types/<int:pk>/delete/", DocumentTypeDeleteView.as_view(), name="documenttype_delete"),
    path(
        "export/",
        ExportView.as_view(),
        name="export_data",
    ),
]
