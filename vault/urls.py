from django.urls import path

from .views import DocumentListView, ExportView

app_name = "vault"

urlpatterns = [
    path("documents/", DocumentListView.as_view(), name="document_list"),
    path(
        "export/",
        ExportView.as_view(),
        name="export_data",
    ),
]
