from django.urls import path

from .views import DocumentDownloadView, DocumentListView, DocumentUploadView, ExportView

app_name = "vault"

urlpatterns = [
    path("documents/", DocumentListView.as_view(), name="document_list"),
    path("documents/upload/", DocumentUploadView.as_view(), name="document_upload"),
    path("documents/<int:pk>/download/", DocumentDownloadView.as_view(), name="document_download"),
    path(
        "export/",
        ExportView.as_view(),
        name="export_data",
    ),
]
