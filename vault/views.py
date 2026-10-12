
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import ListView, View

from .models import Category, Document, DocumentType, Subject
from .services import EXPORT_FILENAME, VaultExportError, build_vault_export


class DocumentListView(LoginRequiredMixin, ListView):
    """Show the current user's documents in fixed-size pages."""

    model = Document
    template_name = "vault/document_list.html"
    context_object_name = "documents"
    paginate_by = 20
    page_kwarg = "page"

    def get_queryset(self):
        queryset = Document.objects.filter(owner=self.request.user)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(title__icontains=query)

        for parameter, field in (
            ("category", "category_id"),
            ("subject", "subject_id"),
            ("document_type", "document_type_id"),
        ):
            value = self.request.GET.get(parameter)
            if value and value.isdigit():
                queryset = queryset.filter(**{field: value})
        return queryset

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(queryset, page_size)
        page_number = self.request.GET.get(self.page_kwarg, 1)
        page = paginator.get_page(page_number)
        return paginator, page, page.object_list, page.has_other_pages()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["subjects"] = Subject.objects.all()
        context["document_types"] = DocumentType.objects.all()
        context["current_filters"] = {
            "q": self.request.GET.get("q", ""),
            "category": self.request.GET.get("category", ""),
            "subject": self.request.GET.get("subject", ""),
            "document_type": self.request.GET.get("document_type", ""),
        }
        query = self.request.GET.copy()
        query.pop(self.page_kwarg, None)
        context["pagination_query"] = query.urlencode()
        return context

class ExportView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            content = build_vault_export(request.user)
        except VaultExportError as error:
            return HttpResponse(
                f"Export failed: {error} Please retry.",
                status=503,
                content_type="text/plain",
            )

        response = HttpResponse(content, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{EXPORT_FILENAME}"'
        return response

        if False:
            for document in user_documents:
                # Save document file to zip
                document_file_path = document.file.name
                zip_file.write(document_file_path, document_file.name)
                # Add a row to the CSV
                csv_writer.writerow([
                    document.title,
                    document.document_type,
                    document.category,
                    document.issue_date,
                    document.expiry_date,
                    document.notes,
                ])
