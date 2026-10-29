from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View
from pathlib import Path

from .forms import CategoryForm, DocumentForm, DocumentTypeForm, SubjectForm
from .mixins import OwnerQuerysetMixin, ProtectedDeleteMixin, StaffRequiredMixin
from .models import Category, Document, DocumentType, Subject
from .services import (
    DocumentAccessError,
    EXPORT_FILENAME,
    VaultExportError,
    authorize_document_access,
    build_vault_export,
    save_uploaded_document,
)


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


class DocumentDetailView(OwnerQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Document
    template_name = "vault/document_detail.html"
    context_object_name = "document"


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "vault/document_form.html"
    success_url = reverse_lazy("vault:document_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error("title", "A document with this title already exists.")
            return self.form_invalid(form)


class DocumentUpdateView(OwnerQuerysetMixin, LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "vault/document_form.html"
    success_url = reverse_lazy("vault:document_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error("title", "A document with this title already exists.")
            return self.form_invalid(form)


class DocumentDeleteView(OwnerQuerysetMixin, LoginRequiredMixin, DeleteView):
    model = Document
    template_name = "vault/document_confirm_delete.html"
    success_url = reverse_lazy("vault:document_list")


class TaxonomyListView(LoginRequiredMixin, ListView):
    context_object_name = "objects"

    def get_context_object_name(self, object_list):
        return self.context_object_name


class CategoryListView(TaxonomyListView):
    model = Category
    template_name = "vault/category_list.html"
    context_object_name = "categories"


class SubjectListView(TaxonomyListView):
    model = Subject
    template_name = "vault/subject_list.html"
    context_object_name = "subjects"


class DocumentTypeListView(TaxonomyListView):
    model = DocumentType
    template_name = "vault/documenttype_list.html"
    context_object_name = "document_types"


class TaxonomyCreateView(StaffRequiredMixin, CreateView):
    template_name = "vault/%(model_name)s_form.html"
    success_url = reverse_lazy("vault:category_list")

    def get_success_url(self):
        return reverse_lazy("vault:%s_list" % self.model._meta.model_name)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error("name", "A record with this name already exists.")
            return self.form_invalid(form)


class CategoryCreateView(TaxonomyCreateView):
    model, form_class = Category, CategoryForm
    template_name = "vault/category_form.html"


class SubjectCreateView(TaxonomyCreateView):
    model, form_class = Subject, SubjectForm
    template_name = "vault/subject_form.html"


class DocumentTypeCreateView(TaxonomyCreateView):
    model, form_class = DocumentType, DocumentTypeForm
    template_name = "vault/documenttype_form.html"


class TaxonomyUpdateView(StaffRequiredMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy("vault:%s_list" % self.model._meta.model_name)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error("name", "A record with this name already exists.")
            return self.form_invalid(form)


class CategoryUpdateView(TaxonomyUpdateView):
    model, form_class = Category, CategoryForm
    template_name = "vault/category_form.html"


class SubjectUpdateView(TaxonomyUpdateView):
    model, form_class = Subject, SubjectForm
    template_name = "vault/subject_form.html"


class DocumentTypeUpdateView(TaxonomyUpdateView):
    model, form_class = DocumentType, DocumentTypeForm
    template_name = "vault/documenttype_form.html"


class TaxonomyDeleteView(StaffRequiredMixin, ProtectedDeleteMixin, DeleteView):
    def get_success_url(self):
        return reverse_lazy("vault:%s_list" % self.model._meta.model_name)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, self.protected_message)
            return redirect(self.get_success_url())


class CategoryDeleteView(TaxonomyDeleteView):
    model, template_name = Category, "vault/category_confirm_delete.html"


class SubjectDeleteView(TaxonomyDeleteView):
    model, template_name = Subject, "vault/subject_confirm_delete.html"


class DocumentTypeDeleteView(TaxonomyDeleteView):
    model, template_name = DocumentType, "vault/documenttype_confirm_delete.html"


class LegacyDocumentListRedirect(View):
    def get(self, request):
        return redirect("vault:document_list", permanent=True)

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


class DocumentUploadView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "vault/document_upload.html", {"form": DocumentForm(user=request.user)})

    def post(self, request):
        form = DocumentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                save_uploaded_document(form, request.user)
            except DocumentAccessError:
                form.add_error("content", "The document could not be protected and stored.")
            else:
                return redirect("vault:document_list")
        return render(request, "vault/document_upload.html", {"form": form}, status=400)


class DocumentDownloadView(View):
    def get(self, request, pk):
        try:
            document = authorize_document_access(pk, request.user)
        except DocumentAccessError:
            if not request.user.is_authenticated:
                return redirect(f"/accounts/login/?next={request.path}")
            raise Http404
        try:
            response = FileResponse(document.content.open("rb"), as_attachment=True,
                                    filename=Path(document.content.name).name)
        except (OSError, ValueError):
            raise Http404
        response["Cache-Control"] = "private, no-store"
        return response
