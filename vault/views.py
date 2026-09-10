"""Views for the document vault app.

Provides CRUD class-based views for Category, Subject, DocumentType,
and Document entities. All views require authentication via
``LoginRequiredMixin`` (FR-011). Document views are scoped to the
authenticated user (FR-012). Taxonomy views are shared across all users.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import (
    CategoryForm,
    DocumentForm,
    DocumentTypeForm,
    SubjectForm,
)
from .mixins import OwnerQuerysetMixin, ProtectedDeleteMixin
from .models import Category, Document, DocumentType, Subject


# ---------------------------------------------------------------------------
# Category views
# ---------------------------------------------------------------------------


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "vault/category_list.html"
    context_object_name = "categories"
    paginate_by = 50


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "vault/category_form.html"
    success_url = reverse_lazy("vault:category_list")


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "vault/category_form.html"
    success_url = reverse_lazy("vault:category_list")


class CategoryDeleteView(ProtectedDeleteMixin, LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "vault/category_confirm_delete.html"
    success_url = reverse_lazy("vault:category_list")


# ---------------------------------------------------------------------------
# Subject views
# ---------------------------------------------------------------------------


class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = "vault/subject_list.html"
    context_object_name = "subjects"
    paginate_by = 50


class SubjectCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "vault/subject_form.html"
    success_url = reverse_lazy("vault:subject_list")


class SubjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = "vault/subject_form.html"
    success_url = reverse_lazy("vault:subject_list")


class SubjectDeleteView(ProtectedDeleteMixin, LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = "vault/subject_confirm_delete.html"
    success_url = reverse_lazy("vault:subject_list")


# ---------------------------------------------------------------------------
# DocumentType views
# ---------------------------------------------------------------------------


class DocumentTypeListView(LoginRequiredMixin, ListView):
    model = DocumentType
    template_name = "vault/documenttype_list.html"
    context_object_name = "document_types"
    paginate_by = 50


class DocumentTypeCreateView(LoginRequiredMixin, CreateView):
    model = DocumentType
    form_class = DocumentTypeForm
    template_name = "vault/documenttype_form.html"
    success_url = reverse_lazy("vault:documenttype_list")


class DocumentTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = DocumentType
    form_class = DocumentTypeForm
    template_name = "vault/documenttype_form.html"
    success_url = reverse_lazy("vault:documenttype_list")


class DocumentTypeDeleteView(
    ProtectedDeleteMixin, LoginRequiredMixin, DeleteView
):
    model = DocumentType
    template_name = "vault/documenttype_confirm_delete.html"
    success_url = reverse_lazy("vault:documenttype_list")


# ---------------------------------------------------------------------------
# Document views
# ---------------------------------------------------------------------------


class DocumentListView(OwnerQuerysetMixin, LoginRequiredMixin, ListView):
    model = Document
    template_name = "vault/document_list.html"
    context_object_name = "documents"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "category", "subject", "document_type"
        )
        category_id = self.request.GET.get("category")
        subject_id = self.request.GET.get("subject")
        doc_type_id = self.request.GET.get("document_type")
        q = self.request.GET.get("q")
        if category_id:
            qs = qs.filter(category_id=category_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if doc_type_id:
            qs = qs.filter(document_type_id=doc_type_id)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["subjects"] = Subject.objects.all()
        ctx["document_types"] = DocumentType.objects.all()
        ctx["current_filters"] = {
            "category": self.request.GET.get("category", ""),
            "subject": self.request.GET.get("subject", ""),
            "document_type": self.request.GET.get("document_type", ""),
            "q": self.request.GET.get("q", ""),
        }
        return ctx


class DocumentCreateView(OwnerQuerysetMixin, LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "vault/document_form.html"
    success_url = reverse_lazy("vault:document_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class DocumentDetailView(OwnerQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Document
    template_name = "vault/document_detail.html"
    context_object_name = "document"


class DocumentUpdateView(OwnerQuerysetMixin, LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "vault/document_form.html"
    success_url = reverse_lazy("vault:document_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class DocumentDeleteView(OwnerQuerysetMixin, LoginRequiredMixin, DeleteView):
    model = Document
    template_name = "vault/document_confirm_delete.html"
    success_url = reverse_lazy("vault:document_list")
