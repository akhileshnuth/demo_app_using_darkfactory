"""URL configuration for the vault app.

All routes are namespaced under ``vault:`` (R10). Provides list, create,
update, and delete routes for Category, Subject, and DocumentType, plus
list, create, detail, update, and delete routes for Document.
"""

from django.urls import path

from . import views

app_name = "vault"

urlpatterns = [
    # Category CRUD
    path(
        "categories/",
        views.CategoryListView.as_view(),
        name="category_list",
    ),
    path(
        "categories/new/",
        views.CategoryCreateView.as_view(),
        name="category_create",
    ),
    path(
        "categories/<int:pk>/edit/",
        views.CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    # Subject CRUD
    path(
        "subjects/",
        views.SubjectListView.as_view(),
        name="subject_list",
    ),
    path(
        "subjects/new/",
        views.SubjectCreateView.as_view(),
        name="subject_create",
    ),
    path(
        "subjects/<int:pk>/edit/",
        views.SubjectUpdateView.as_view(),
        name="subject_update",
    ),
    path(
        "subjects/<int:pk>/delete/",
        views.SubjectDeleteView.as_view(),
        name="subject_delete",
    ),
    # DocumentType CRUD
    path(
        "types/",
        views.DocumentTypeListView.as_view(),
        name="documenttype_list",
    ),
    path(
        "types/new/",
        views.DocumentTypeCreateView.as_view(),
        name="documenttype_create",
    ),
    path(
        "types/<int:pk>/edit/",
        views.DocumentTypeUpdateView.as_view(),
        name="documenttype_update",
    ),
    path(
        "types/<int:pk>/delete/",
        views.DocumentTypeDeleteView.as_view(),
        name="documenttype_delete",
    ),
    # Document CRUD
    path(
        "documents/",
        views.DocumentListView.as_view(),
        name="document_list",
    ),
    path(
        "documents/new/",
        views.DocumentCreateView.as_view(),
        name="document_create",
    ),
    path(
        "documents/<int:pk>/",
        views.DocumentDetailView.as_view(),
        name="document_detail",
    ),
    path(
        "documents/<int:pk>/edit/",
        views.DocumentUpdateView.as_view(),
        name="document_update",
    ),
    path(
        "documents/<int:pk>/delete/",
        views.DocumentDeleteView.as_view(),
        name="document_delete",
    ),
]
