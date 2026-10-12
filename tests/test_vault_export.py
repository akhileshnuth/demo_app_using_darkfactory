import json
import zipfile
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from vault.models import Category, Document, DocumentType, Subject
from vault.services import VaultExportError


class VaultExportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="owner@example.com", password="Strong-pass1"
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@example.com", password="Strong-pass1"
        )
        self.category = Category.objects.create(name="Personal")
        self.subject = Subject.objects.create(name="Identity")
        self.document_type = DocumentType.objects.create(name="Record")
        self.document = Document.objects.create(
            owner=self.user,
            title="Passport",
            notes="Keep current",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
        )

    def _manifest(self, response):
        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            self.assertEqual(archive.testzip(), None)
            self.assertEqual(archive.namelist(), ["manifest.json"])
            return json.loads(archive.read("manifest.json"))

    def test_export_contains_owned_documents_in_valid_versioned_zip(self):
        Document.objects.create(
            owner=self.other_user,
            title="Other passport",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("vault:export_data"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="vault-export.zip"')
        manifest = self._manifest(response)
        self.assertEqual(manifest["format"], "vault-json")
        self.assertEqual(manifest["version"], 1)
        self.assertEqual([document["title"] for document in manifest["documents"]], ["Passport"])
        self.assertEqual(manifest["documents"][0]["notes"], "Keep current")

    def test_empty_vault_exports_zero_documents(self):
        self.document.delete()
        self.client.force_login(self.user)

        response = self.client.get(reverse("vault:export_data"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._manifest(response)["documents"], [])

    def test_anonymous_export_is_protected(self):
        response = self.client.get(reverse("vault:export_data"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('vault:export_data')}",
        )

    @patch("vault.views.build_vault_export", side_effect=VaultExportError("temporary problem"))
    def test_failed_export_has_no_download_headers_and_requests_retry(self, build_export):
        self.client.force_login(self.user)

        response = self.client.get(reverse("vault:export_data"))

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Content-Disposition", response)
        self.assertContains(response, "Export failed", status_code=503)
        self.assertContains(response, "Please retry", status_code=503)
