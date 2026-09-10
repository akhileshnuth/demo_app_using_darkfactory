"""Tests for the vault app.

Covers models (FR-002..FR-006, FR-012, FR-013, FR-014), views (CRUD
lifecycle, auth gating FR-011, per-user scoping FR-012, delete protection,
filtering), forms (case-insensitive duplicate rejection, required-field
validation), and URL resolution. Uses Django's bundled test runner with
the in-memory SQLite test database, following the accounts/dashboard
pattern.
"""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .forms import (
    CategoryForm,
    DocumentForm,
    DocumentTypeForm,
    SubjectForm,
)
from .models import Category, Document, DocumentType, Subject

User = get_user_model()


def make_user(email="ada@example.com", **kwargs):
    return User.objects.create_user(
        email=email, password="Sup3r-secret!", **kwargs
    )


class VaultBaseTestCase(TestCase):
    """Shared fixtures: an owner plus one of each taxonomy entity."""

    def setUp(self):
        self.owner = make_user()
        self.category = Category.objects.create(
            name="Financial", description="Money matters"
        )
        self.subject = Subject.objects.create(
            name="Tax Returns", description="Annual filings"
        )
        self.document_type = DocumentType.objects.create(
            name="Invoice", description="Billing document"
        )

    def login_owner(self):
        self.client.login(
            email=self.owner.email, password="Sup3r-secret!"
        )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class CategoryModelTests(TestCase):
    def test_category_fields_created(self):
        cat = Category.objects.create(
            name="Legal", description="Legal documents"
        )
        self.assertEqual(cat.name, "Legal")
        self.assertEqual(cat.description, "Legal documents")
        self.assertTrue(cat.created_at)
        self.assertTrue(cat.updated_at)
        self.assertEqual(str(cat), "Legal")

    def test_category_name_is_unique(self):
        Category.objects.create(name="Financial")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name="Financial")


class SubjectModelTests(TestCase):
    def test_subject_fields_created(self):
        subj = Subject.objects.create(name="Contracts")
        self.assertEqual(subj.name, "Contracts")
        self.assertEqual(subj.description, "")
        self.assertTrue(subj.created_at)
        self.assertTrue(subj.updated_at)
        self.assertEqual(str(subj), "Contracts")

    def test_subject_name_is_unique(self):
        Subject.objects.create(name="Contracts")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Subject.objects.create(name="Contracts")


class DocumentTypeModelTests(TestCase):
    def test_document_type_fields_created(self):
        dt = DocumentType.objects.create(name="Receipt")
        self.assertEqual(dt.name, "Receipt")
        self.assertEqual(dt.description, "")
        self.assertTrue(dt.created_at)
        self.assertTrue(dt.updated_at)
        self.assertEqual(
            str(DocumentType._meta.verbose_name_plural), "document types"
        )
        self.assertEqual(str(dt), "Receipt")

    def test_document_type_name_is_unique(self):
        DocumentType.objects.create(name="Receipt")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DocumentType.objects.create(name="Receipt")


class DocumentModelTests(VaultBaseTestCase):
    def _make_document(self, owner=None, title="Tax Return 2025"):
        return Document.objects.create(
            title=title,
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=owner or self.owner,
        )

    def test_document_fields_and_relations(self):
        doc = self._make_document(notes="Draft copy")
        self.assertEqual(doc.title, "Tax Return 2025")
        self.assertEqual(doc.notes, "Draft copy")
        self.assertEqual(doc.category, self.category)
        self.assertEqual(doc.subject, self.subject)
        self.assertEqual(doc.document_type, self.document_type)
        self.assertEqual(doc.owner, self.owner)
        self.assertTrue(doc.created_at)
        self.assertTrue(doc.updated_at)
        self.assertEqual(str(doc), "Tax Return 2025")

    def test_document_title_unique_per_owner(self):
        self._make_document(title="Tax Return 2025")
        other = make_user(email="bob@example.com")
        # Same title by a different user is allowed.
        doc2 = self._make_document(owner=other, title="Tax Return 2025")
        self.assertEqual(Document.objects.filter(title="Tax Return 2025").count(), 2)
        self.assertEqual(doc2.owner, other)
        # Duplicate title by the same owner raises IntegrityError.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._make_document(title="Tax Return 2025")

    def test_documents_scoped_to_owner(self):
        other = make_user(email="carol@example.com")
        self._make_document(owner=other, title="Other user's doc")
        self._make_document(title="Owner doc")
        self.assertEqual(
            Document.objects.filter(owner=self.owner).count(), 1
        )


# ---------------------------------------------------------------------------
# URL resolution tests
# ---------------------------------------------------------------------------


class UrlResolutionTests(TestCase):
    def test_all_vault_route_names_resolve(self):
        routes = {
            "vault:category_list": "/categories/",
            "vault:category_create": "/categories/new/",
            "vault:category_update": "/categories/1/edit/",
            "vault:category_delete": "/categories/1/delete/",
            "vault:subject_list": "/subjects/",
            "vault:subject_create": "/subjects/new/",
            "vault:subject_update": "/subjects/1/edit/",
            "vault:subject_delete": "/subjects/1/delete/",
            "vault:documenttype_list": "/types/",
            "vault:documenttype_create": "/types/new/",
            "vault:documenttype_update": "/types/1/edit/",
            "vault:documenttype_delete": "/types/1/delete/",
            "vault:document_list": "/documents/",
            "vault:document_create": "/documents/new/",
            "vault:document_detail": "/documents/1/",
            "vault:document_update": "/documents/1/edit/",
            "vault:document_delete": "/documents/1/delete/",
        }
        for name, path in routes.items():
            with self.subTest(name=name):
                if "1/" in path:
                    self.assertEqual(reverse(name, args=[1]), path)
                else:
                    self.assertEqual(reverse(name), path)


# ---------------------------------------------------------------------------
# Category views
# ---------------------------------------------------------------------------


class CategoryViewTests(VaultBaseTestCase):
    def test_category_list_requires_login(self):
        response = self.client.get(reverse("vault:category_list"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=" + reverse("vault:category_list"),
        )

    def test_category_list_renders_existing_categories(self):
        self.login_owner()
        response = self.client.get(reverse("vault:category_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Financial")

    def test_category_create_creates_and_redirects(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:category_create"),
            {"name": "Personal", "description": "Private docs"},
        )
        self.assertRedirects(response, reverse("vault:category_list"))
        self.assertTrue(Category.objects.filter(name="Personal").exists())

    def test_category_create_duplicate_name_rejected(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:category_create"),
            {"name": "financial", "description": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "A category with this name already exists."
        )
        self.assertEqual(Category.objects.filter(name__iexact="financial").count(), 1)

    def test_category_create_empty_name_rejected(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:category_create"), {"name": "", "description": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_category_update_persists_changes(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:category_update", args=[self.category.pk]),
            {"name": "Corporate Finance", "description": "Updated"},
        )
        self.assertRedirects(response, reverse("vault:category_list"))
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Corporate Finance")
        self.assertEqual(self.category.description, "Updated")

    def test_category_delete_removes_category(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:category_delete", args=[self.category.pk])
        )
        self.assertRedirects(response, reverse("vault:category_list"))
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_category_delete_blocked_when_documents_exist(self):
        Document.objects.create(
            title="Doc",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        self.login_owner()
        response = self.client.post(
            reverse("vault:category_delete", args=[self.category.pk])
        )
        self.assertRedirects(response, reverse("vault:category_list"))
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        self.assertContains(
            self.client.get(reverse("vault:category_list")),
            "cannot be deleted",
        )


class SubjectViewTests(VaultBaseTestCase):
    def test_subject_list_requires_login(self):
        response = self.client.get(reverse("vault:subject_list"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=" + reverse("vault:subject_list"),
        )

    def test_subject_list_renders(self):
        self.login_owner()
        response = self.client.get(reverse("vault:subject_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tax Returns")

    def test_subject_create_creates_and_redirects(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:subject_create"),
            {"name": "Client Agreements", "description": ""},
        )
        self.assertRedirects(response, reverse("vault:subject_list"))
        self.assertTrue(
            Subject.objects.filter(name="Client Agreements").exists()
        )

    def test_subject_create_duplicate_name_rejected(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:subject_create"),
            {"name": "tax returns", "description": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "A subject with this name already exists."
        )

    def test_subject_update_persists_changes(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:subject_update", args=[self.subject.pk]),
            {"name": "Annual Tax Filings", "description": "Updated"},
        )
        self.assertRedirects(response, reverse("vault:subject_list"))
        self.subject.refresh_from_db()
        self.assertEqual(self.subject.name, "Annual Tax Filings")

    def test_subject_delete_removes_subject(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:subject_delete", args=[self.subject.pk])
        )
        self.assertRedirects(response, reverse("vault:subject_list"))
        self.assertFalse(
            Subject.objects.filter(pk=self.subject.pk).exists()
        )

    def test_subject_delete_blocked_when_documents_exist(self):
        Document.objects.create(
            title="Doc",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        self.login_owner()
        response = self.client.post(
            reverse("vault:subject_delete", args=[self.subject.pk])
        )
        self.assertRedirects(response, reverse("vault:subject_list"))
        self.assertTrue(Subject.objects.filter(pk=self.subject.pk).exists())


class DocumentTypeViewTests(VaultBaseTestCase):
    def test_documenttype_list_requires_login(self):
        response = self.client.get(reverse("vault:documenttype_list"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=" + reverse("vault:documenttype_list"),
        )

    def test_documenttype_list_renders(self):
        self.login_owner()
        response = self.client.get(reverse("vault:documenttype_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invoice")

    def test_documenttype_create_creates_and_redirects(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:documenttype_create"),
            {"name": "Contract", "description": ""},
        )
        self.assertRedirects(response, reverse("vault:documenttype_list"))
        self.assertTrue(
            DocumentType.objects.filter(name="Contract").exists()
        )

    def test_documenttype_create_duplicate_name_rejected(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:documenttype_create"),
            {"name": "invoice", "description": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "A document type with this name already exists."
        )

    def test_documenttype_update_persists_changes(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:documenttype_update", args=[self.document_type.pk]),
            {"name": "Purchase Order", "description": ""},
        )
        self.assertRedirects(response, reverse("vault:documenttype_list"))
        self.document_type.refresh_from_db()
        self.assertEqual(self.document_type.name, "Purchase Order")

    def test_documenttype_delete_removes_type(self):
        self.login_owner()
        response = self.client.post(
            reverse("vault:documenttype_delete", args=[self.document_type.pk])
        )
        self.assertRedirects(response, reverse("vault:documenttype_list"))
        self.assertFalse(
            DocumentType.objects.filter(pk=self.document_type.pk).exists()
        )

    def test_documenttype_delete_blocked_when_documents_exist(self):
        Document.objects.create(
            title="Doc",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        self.login_owner()
        response = self.client.post(
            reverse("vault:documenttype_delete", args=[self.document_type.pk])
        )
        self.assertRedirects(response, reverse("vault:documenttype_list"))
        self.assertTrue(
            DocumentType.objects.filter(pk=self.document_type.pk).exists()
        )


# ---------------------------------------------------------------------------
# Document views
# ---------------------------------------------------------------------------


class DocumentViewTests(VaultBaseTestCase):
    valid_payload = {}

    def setUp(self):
        super().setUp()
        self.valid_payload = {
            "title": "Quarterly Invoice Q1",
            "category": str(self.category.pk),
            "subject": str(self.subject.pk),
            "document_type": str(self.document_type.pk),
            "notes": "First invoice",
        }

    def _create_document(self, title="Quarterly Invoice Q1"):
        self.login_owner()
        payload = dict(self.valid_payload, title=title)
        response = self.client.post(
            reverse("vault:document_create"), payload
        )
        return response

    def test_document_list_requires_login(self):
        response = self.client.get(reverse("vault:document_list"))
        self.assertRedirects(
            response,
            reverse("login") + "?next=" + reverse("vault:document_list"),
        )

    def test_document_list_shows_only_own_documents(self):
        other = make_user(email="bob@example.com")
        Document.objects.create(
            title="Bob's secret doc",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=other,
        )
        self._create_document()
        response = self.client.get(reverse("vault:document_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quarterly Invoice Q1")
        self.assertNotContains(response, "Bob's secret doc")

    def test_document_create_with_all_fields(self):
        response = self._create_document()
        self.assertRedirects(response, reverse("vault:document_list"))
        doc = Document.objects.get(title="Quarterly Invoice Q1")
        self.assertEqual(doc.owner, self.owner)
        self.assertEqual(doc.category, self.category)
        self.assertEqual(doc.subject, self.subject)
        self.assertEqual(doc.document_type, self.document_type)
        self.assertEqual(doc.notes, "First invoice")

    def test_document_create_missing_required_fields(self):
        self.login_owner()
        payload = {
            "title": "No links",
            "category": "",
            "subject": "",
            "document_type": "",
            "notes": "",
        }
        response = self.client.post(
            reverse("vault:document_create"), payload
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertFalse(Document.objects.filter(title="No links").exists())

    def test_document_create_missing_title(self):
        self.login_owner()
        payload = dict(self.valid_payload, title="")
        response = self.client.post(
            reverse("vault:document_create"), payload
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_document_create_duplicate_title_per_user_rejected(self):
        self._create_document()
        self.login_owner()
        payload = dict(self.valid_payload, title="quarterly invoice q1")
        response = self.client.post(
            reverse("vault:document_create"), payload
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "A document with this title already exists."
        )

    def test_document_create_duplicate_title_allowed_for_other_user(self):
        self._create_document()
        other = make_user(email="carol@example.com")
        self.client.login(email="carol@example.com", password="Sup3r-secret!")
        payload = dict(self.valid_payload, title="Quarterly Invoice Q1")
        response = self.client.post(
            reverse("vault:document_create"), payload
        )
        self.assertRedirects(response, reverse("vault:document_list"))

    def test_document_detail_renders(self):
        self._create_document()
        doc = Document.objects.get(title="Quarterly Invoice Q1")
        response = self.client.get(
            reverse("vault:document_detail", args=[doc.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quarterly Invoice Q1")
        self.assertContains(response, "Financial")
        self.assertContains(response, "Tax Returns")
        self.assertContains(response, "Invoice")
        self.assertContains(response, "First invoice")

    def test_document_detail_not_accessible_to_other_user(self):
        self._create_document()
        doc = Document.objects.get(title="Quarterly Invoice Q1")
        other = make_user(email="dave@example.com")
        self.client.login(email="dave@example.com", password="Sup3r-secret!")
        response = self.client.get(
            reverse("vault:document_detail", args=[doc.pk])
        )
        # OwnerQuerysetMixin scopes to the authenticated user, so the other
        # user cannot see it and Django raises 404.
        self.assertEqual(response.status_code, 404)

    def test_document_update_persists_changes(self):
        doc = self._create_document()
        doc = Document.objects.get(title="Quarterly Invoice Q1")
        self.login_owner()
        response = self.client.post(
            reverse("vault:document_update", args=[doc.pk]),
            dict(self.valid_payload, title="Updated Title", notes="Revised"),
        )
        self.assertRedirects(response, reverse("vault:document_list"))
        doc.refresh_from_db()
        self.assertEqual(doc.title, "Updated Title")
        self.assertEqual(doc.notes, "Revised")

    def test_document_update_invalid_changes_rejected(self):
        doc = self._create_document()
        doc = Document.objects.get(title="Quarterly Invoice Q1")
        self.login_owner()
        response = self.client.post(
            reverse("vault:document_update", args=[doc.pk]),
            dict(self.valid_payload, title=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_document_delete_removes_document(self):
        doc = self._create_document()
        doc = Document.objects.get(title="Quarterly Invoice Q1")
        self.login_owner()
        response = self.client.post(
            reverse("vault:document_delete", args=[doc.pk])
        )
        self.assertRedirects(response, reverse("vault:document_list"))
        self.assertFalse(
            Document.objects.filter(pk=doc.pk).exists()
        )

    def test_document_list_sorted_by_most_recently_updated(self):
        doc1 = self._create_document(title="First doc")
        doc1 = Document.objects.get(title="First doc")
        doc2 = self._create_document(title="Second doc")
        doc2 = Document.objects.get(title="Second doc")
        # Touch doc2 so it becomes most recently updated.
        doc2.notes = "touched"
        doc2.save()
        response = self.client.get(reverse("vault:document_list"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertLess(
            body.index("Second doc"), body.index("First doc")
        )


# ---------------------------------------------------------------------------
# Filtering & search
# ---------------------------------------------------------------------------


class DocumentFilterTests(VaultBaseTestCase):
    def setUp(self):
        super().setUp()
        self.other_category = Category.objects.create(name="Personal")
        self.other_subject = Subject.objects.create(name="Contracts")

    def test_filter_by_category(self):
        self.login_owner()
        Document.objects.create(
            title="Financial Doc",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        Document.objects.create(
            title="Personal Doc",
            category=self.other_category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        response = self.client.get(
            reverse("vault:document_list"), {"category": self.category.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Financial Doc")
        self.assertNotContains(response, "Personal Doc")

    def test_search_by_title(self):
        self.login_owner()
        Document.objects.create(
            title="Tax Return 2024",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        Document.objects.create(
            title="Lease Agreement",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        response = self.client.get(
            reverse("vault:document_list"), {"q": "tax"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tax Return 2024")
        self.assertNotContains(response, "Lease Agreement")

    def test_clear_filters_shows_all(self):
        self.login_owner()
        Document.objects.create(
            title="Doc A",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        Document.objects.create(
            title="Doc B",
            category=self.other_category,
            subject=self.other_subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        response = self.client.get(reverse("vault:document_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Doc A")
        self.assertContains(response, "Doc B")


# ---------------------------------------------------------------------------
# Auth gating (SC-003)
# ---------------------------------------------------------------------------


class AuthGatingTests(VaultBaseTestCase):
    def _assert_vault_get_redirects(self, url_name, args=None):
        response = self.client.get(reverse(url_name, args=args or []))
        login_url = reverse("login")
        next_path = reverse(url_name, args=args or [])
        self.assertRedirects(
            response, f"{login_url}?next={next_path}"
        )

    def test_unauthenticated_gets_redirected_to_login(self):
        routes = [
            ("vault:category_list", None),
            ("vault:category_create", None),
            ("vault:category_update", [1]),
            ("vault:category_delete", [1]),
            ("vault:subject_list", None),
            ("vault:subject_create", None),
            ("vault:documenttype_list", None),
            ("vault:documenttype_create", None),
            ("vault:document_list", None),
            ("vault:document_create", None),
            ("vault:document_detail", [1]),
            ("vault:document_update", [1]),
            ("vault:document_delete", [1]),
        ]
        for name, args in routes:
            with self.subTest(name=name):
                self._assert_vault_get_redirects(name, args)

    def test_no_vault_content_leaks_in_redirect(self):
        response = self.client.get(reverse("vault:document_list"))
        self.assertEqual(response.status_code, 302)
        self.assertNotContains(response, "Financial")
        self.assertNotContains(response, "Quadratic")


# ---------------------------------------------------------------------------
# CSRF protection (FR-015)
# ---------------------------------------------------------------------------


class CsrfProtectionTests(VaultBaseTestCase):
    def test_category_create_without_csrf_rejected(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        client.login(email=self.owner.email, password="Sup3r-secret!")
        response = client.post(
            reverse("vault:category_create"),
            {"name": "NoCSRF", "description": ""},
        )
        self.assertEqual(response.status_code, 403)

    def test_document_create_without_csrf_rejected(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        client.login(email=self.owner.email, password="Sup3r-secret!")
        response = client.post(
            reverse("vault:document_create"),
            {
                "title": "NoCSRF Doc",
                "category": str(self.category.pk),
                "subject": str(self.subject.pk),
                "document_type": str(self.document_type.pk),
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Document.objects.filter(title="NoCSRF Doc").exists())


# ---------------------------------------------------------------------------
# Form-level duplicate & validation tests
# ---------------------------------------------------------------------------


class CategoryFormTests(TestCase):
    def test_duplicate_name_case_insensitive_rejected(self):
        Category.objects.create(name="Financial")
        form = CategoryForm(data={"name": "financial", "description": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("already exists", form.errors["name"][0])

    def test_empty_name_rejected(self):
        form = CategoryForm(data={"name": "", "description": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_valid_name_accepted(self):
        form = CategoryForm(data={"name": "Legal", "description": "x"})
        self.assertTrue(form.is_valid())


class SubjectFormTests(TestCase):
    def test_duplicate_name_case_insensitive_rejected(self):
        Subject.objects.create(name="Contracts")
        form = SubjectForm(data={"name": "CONTRACTS", "description": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class DocumentTypeFormTests(TestCase):
    def test_duplicate_name_case_insensitive_rejected(self):
        DocumentType.objects.create(name="Invoice")
        form = DocumentTypeForm(data={"name": "INVOICE", "description": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class DocumentFormTests(VaultBaseTestCase):
    def _form(self, data, user=None, instance=None):
        kwargs = {"data": data, "user": user or self.owner}
        if instance:
            kwargs["instance"] = instance
        return DocumentForm(**kwargs)

    def test_missing_required_fields_rejected(self):
        form = self._form(
            {
                "title": "",
                "category": "",
                "subject": "",
                "document_type": "",
                "notes": "",
            }
        )
        self.assertFalse(form.is_valid())
        for field in ("title", "category", "subject", "document_type"):
            self.assertIn(field, form.errors)

    def test_duplicate_title_case_insensitive_rejected(self):
        Document.objects.create(
            title="Tax Return",
            category=self.category,
            subject=self.subject,
            document_type=self.document_type,
            owner=self.owner,
        )
        form = self._form(
            {
                "title": "tax return",
                "category": self.category.pk,
                "subject": self.subject.pk,
                "document_type": self.document_type.pk,
                "notes": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("already exists", form.errors["title"][0])

    def test_same_title_different_user_allowed(self):
        other = make_user(email="zed@example.com")
        form = self._form(
            {
                "title": "Shared Title",
                "category": self.category.pk,
                "subject": self.subject.pk,
                "document_type": self.document_type.pk,
                "notes": "",
            },
            user=other,
        )
        self.assertTrue(form.is_valid())
