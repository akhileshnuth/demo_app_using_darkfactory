"""Forms for the document vault app.

Each taxonomy entity (Category, Subject, DocumentType) has a ModelForm
with case-insensitive duplicate name validation. DocumentForm validates
required fields and enforces per-user title uniqueness.
"""

from django import forms

from .models import Category, Document, DocumentType, Subject


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]

    def clean_name(self):
        name = self.cleaned_data["name"]
        qs = Category.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "A category with this name already exists."
            )
        return name


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "description"]

    def clean_name(self):
        name = self.cleaned_data["name"]
        qs = Subject.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "A subject with this name already exists."
            )
        return name


class DocumentTypeForm(forms.ModelForm):
    class Meta:
        model = DocumentType
        fields = ["name", "description"]

    def clean_name(self):
        name = self.cleaned_data["name"]
        qs = DocumentType.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "A document type with this name already exists."
            )
        return name


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "category", "subject", "document_type", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_title(self):
        title = self.cleaned_data["title"]
        if not self.user:
            return title
        qs = Document.objects.filter(owner=self.user, title__iexact=title)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "A document with this title already exists."
            )
        return title

    def save(self, commit=True):
        doc = super().save(commit=False)
        if self.user and not doc.owner_id:
            doc.owner = self.user
        if commit:
            doc.save()
        return doc
