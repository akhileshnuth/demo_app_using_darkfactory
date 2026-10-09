from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from vault.models import Category, Document, DocumentType, Subject


@override_settings(USE_TZ=False)
class DocumentPaginationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="owner@example.com", password="Strong-password-123"
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@example.com", password="Strong-password-123"
        )
        self.category = Category.objects.create(name="Personal")
        self.subject = Subject.objects.create(name="Identity")
        self.document_type = DocumentType.objects.create(name="Record")
        for number in range(21):
            Document.objects.create(
                owner=self.user,
                title=f"Document {number:02d}",
                category=self.category,
                subject=self.subject,
                document_type=self.document_type,
            )
        Document.objects.create(
            owner=self.other_user,
            title="Someone else's document",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
        )
        self.client.force_login(self.user)

    def test_first_page_has_twenty_documents_and_navigation(self):
        response = self.client.get(reverse("vault:document_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["documents"]), 20)
        self.assertEqual(response.context["page_obj"].number, 1)
        self.assertContains(response, "Page 1 of 2")
        self.assertContains(response, 'aria-label="Next page"')

    def test_next_page_has_remaining_document_and_previous_link(self):
        response = self.client.get(
            reverse("vault:document_list"), {"page": 2, "q": "Document"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["documents"]), 1)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertContains(response, "page=1&amp;q=Document")

    def test_out_of_range_page_is_clamped(self):
        response = self.client.get(reverse("vault:document_list"), {"page": 999})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(len(response.context["documents"]), 1)

    def test_empty_results_have_no_pagination_controls(self):
        Document.objects.filter(owner=self.user).delete()

        response = self.client.get(reverse("vault:document_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No documents found.")
        self.assertNotContains(response, 'aria-label="Document pages"')

    def test_documents_are_scoped_to_current_user(self):
        response = self.client.get(reverse("vault:document_list"))

        self.assertNotContains(response, "Someone else's document")
