from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import ActivityLog
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


@override_settings(MEDIA_ROOT="/tmp/dft17-private-documents")
class ProtectedDocumentTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="protected-owner@example.com", password="Strong-pass1"
        )
        self.collaborator = get_user_model().objects.create_user(
            email="collaborator@example.com", password="Strong-pass1"
        )
        self.other = get_user_model().objects.create_user(
            email="protected-other@example.com", password="Strong-pass1"
        )
        category = Category.objects.create(name="Protected")
        subject = Subject.objects.create(name="Private")
        document_type = DocumentType.objects.create(name="Upload")
        self.upload = SimpleUploadedFile("secret.txt", b"private document")
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("vault:document_upload"),
            {"title": "Secret", "category": category.pk, "subject": subject.pk,
             "document_type": document_type.pk, "content": self.upload,
             "collaborators": [self.collaborator.pk]},
        )
        self.assertEqual(response.status_code, 302)
        self.document = Document.objects.get(title="Secret")

    def test_only_owner_and_collaborator_can_download(self):
        url = reverse("vault:document_download", args=[self.document.pk])
        self.client.force_login(self.other)
        denied = self.client.get(url)
        self.assertEqual(denied.status_code, 404)
        self.client.force_login(self.collaborator)
        allowed = self.client.get(url)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(b"".join(allowed.streaming_content), b"private document")

    def test_anonymous_download_redirects_and_access_is_audited_without_content(self):
        self.client.logout()
        response = self.client.get(
            reverse("vault:document_download", args=[self.document.pk])
        )
        self.assertEqual(response.status_code, 302)
        event = ActivityLog.objects.filter(
            event_type=ActivityLog.EventType.DOCUMENT_ACCESS_DENIED
        ).latest("created_at")
        self.assertIsNone(event.user)
        self.assertNotIn("private document", event.description)
        self.assertNotIn("private document", str(event.context))

    def test_expired_document_is_not_retrievable(self):
        self.document.expiry_date = "2000-01-01"
        self.document.save(update_fields=["expiry_date"])
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("vault:document_download", args=[self.document.pk])
        )
        self.assertEqual(response.status_code, 404)
