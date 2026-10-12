from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from vault.forms import CategoryForm, DocumentForm
from vault.models import Category, Document, DocumentType, Subject


class VaultFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="owner@example.com", password="Strong-pass1"
        )
        self.other = get_user_model().objects.create_user(
            email="other@example.com", password="Strong-pass1"
        )
        self.category = Category.objects.create(name="Personal")
        self.subject = Subject.objects.create(name="Identity")
        self.document_type = DocumentType.objects.create(name="Record")
        self.document = Document.objects.create(
            owner=self.user,
            title="Passport",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
        )

    def test_document_filters_are_scoped_and_invalid_filter_is_ignored(self):
        Document.objects.create(
            owner=self.other,
            title="Other passport",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("vault:document_list"),
            {"q": "pass", "category": str(self.category.pk), "subject": "invalid"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["documents"]), [self.document])
        self.assertNotContains(response, "Other passport")

    def test_document_form_rejects_duplicate_title_for_same_owner(self):
        form = DocumentForm(
            data={
                "title": "passport",
                "category": self.category.pk,
                "subject": self.subject.pk,
                "document_type": self.document_type.pk,
                "notes": "",
            },
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("A document with this title already exists.", form.errors["title"])

    def test_category_form_rejects_case_insensitive_duplicate(self):
        form = CategoryForm(data={"name": "PERSONAL", "description": ""})

        self.assertFalse(form.is_valid())
        self.assertIn("A category with this name already exists.", form.errors["name"])

    def test_anonymous_document_list_is_protected(self):
        response = self.client.get(reverse("vault:document_list"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('vault:document_list')}",
        )

    def test_export_returns_a_complete_archive(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("vault:export_data"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
