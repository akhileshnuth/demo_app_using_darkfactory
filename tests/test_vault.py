from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
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


@override_settings(USE_TZ=False)
class VaultLifecycleTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="user@example.com", password="Strong-pass1"
        )
        self.staff = user_model.objects.create_user(
            email="staff@example.com", password="Strong-pass1", is_staff=True
        )
        self.category = Category.objects.create(name="Personal")
        self.subject = Subject.objects.create(name="Identity")
        self.document_type = DocumentType.objects.create(name="Record")

    def test_staff_can_create_update_and_delete_taxonomy(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("vault:category_create"), {"name": "Finance", "description": ""}
        )
        category = Category.objects.get(name="Finance")
        self.assertRedirects(response, reverse("vault:category_list"))

        response = self.client.post(
            reverse("vault:category_update", args=[category.pk]),
            {"name": "Money", "description": ""},
        )
        self.assertRedirects(response, reverse("vault:category_list"))
        self.assertTrue(Category.objects.filter(name="Money").exists())

        response = self.client.post(
            reverse("vault:category_delete", args=[category.pk])
        )
        self.assertRedirects(response, reverse("vault:category_list"))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_non_staff_cannot_change_taxonomy(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("vault:category_create"), {"name": "Finance"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Category.objects.filter(name="Finance").exists())

    def test_document_lifecycle_is_owner_scoped_and_classified(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("vault:document_create"),
            {
                "title": "Passport",
                "category": self.category.pk,
                "subject": self.subject.pk,
                "document_type": self.document_type.pk,
                "notes": "Keep current",
                "expiry_date": "2030-01-01",
            },
        )
        document = Document.objects.get(title="Passport")
        self.assertRedirects(response, reverse("vault:document_list"))
        self.assertEqual(document.owner, self.user)
        self.assertEqual(document.expiry_date.isoformat(), "2030-01-01")

        response = self.client.get(
            reverse("vault:document_update", args=[document.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_taxonomy_in_use_cannot_be_deleted(self):
        document = Document.objects.create(
            owner=self.user,
            title="Passport",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
        )
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("vault:category_delete", args=[self.category.pk])
        )
        self.assertRedirects(response, reverse("vault:category_list"))
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        document.refresh_from_db()

    def test_legacy_document_list_redirects_to_canonical_url(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("vault:legacy_document_list"))
        self.assertRedirects(response, reverse("vault:document_list"), status_code=301)
