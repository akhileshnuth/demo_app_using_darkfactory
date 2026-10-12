
# Add Import for required Libraries
import csv
import zipfile
from io import StringIO

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.generic import ListView, View

from .models import Category, Document, DocumentType, Subject


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

# Add the ExportView class
class ExportView(LoginRequiredMixin, View):
    def get(self, request):
        user_documents = Document.objects.filter(owner=request.user)

        # Create a zip file in memory
        zip_filename = 'vault_data.zip'
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={zip_filename}'

        with zipfile.ZipFile(response, 'w') as zip_file:
            # Prepare data for CSV
            csv_file_path = 'vault_data_summary.csv'
            csv_file = StringIO()
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Title', 'Type', 'Category', 'Issue Date', 'Expiry Date', 'Notes'])

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

            # Save the CSV to the zip
            zip_file.writestr(csv_file_path, csv_file.getvalue())
        return response
