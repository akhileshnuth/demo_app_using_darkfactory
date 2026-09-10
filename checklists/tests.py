"""Tests for the checklists app (DFT-9).

Covers checklist CRUD + completion statistics (SC-001, SC-005), sharing with
read-only enforcement and revocation (SC-002, SC-006), the emergency access
flow including auto-grant (SC-003), the notification center + unread badge
(SC-004, SC-007), and authorization (FR-019, FR-020, SC-006). Uses Django's
bundled test runner with the in-memory SQLite test database.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Checklist,
    ChecklistItem,
    ChecklistShare,
    EmergencyAccessRequest,
    EmergencyContact,
    Notification,
)

User = get_user_model()


def _new_user(email, **kwargs):
    return User.objects.create_user(email=email, password="Sup3r-secret!", **kwargs)


class ChecklistLifecycleTests(TestCase):
    """Personal checklist CRUD + stats (US-1, FR-002/003/004)."""

    def setUp(self):
        self.owner = _new_user("owner@example.com", display_name="Owner")

    def test_checklist_list_requires_login(self):
        response = self.client.get(reverse("checklist_list"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("checklist_list")
        )
        self.assertNotContains(response, "New Checklist")

    def test_create_checklist_redirects_to_detail(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        response = self.client.post(
            reverse("checklist_new"), {"title": "Grocery Run"}
        )
        checklist = Checklist.objects.get(title="Grocery Run")
        self.assertRedirects(response, reverse("checklist_detail", args=[checklist.pk]))
        self.assertEqual(checklist.owner, self.owner)

    def test_create_checklist_blank_title_rejected(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        response = self.client.post(reverse("checklist_new"), {"title": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Checklist.objects.count(), 0)

    def test_list_shows_item_count_and_completion(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        checklist = Checklist.objects.create(owner=self.owner, title="Grocery Run")
        ChecklistItem.objects.create(checklist=checklist, text="Milk", position=1)
        completed = ChecklistItem.objects.create(
            checklist=checklist, text="Eggs", position=2, is_complete=True
        )
        self.assertEqual(checklist.completion_percentage, 50)
        response = self.client.get(reverse("checklist_list"))
        self.assertContains(response, "Grocery Run")
        self.assertContains(response, "2 items")
        self.assertContains(response, "50% complete")

    def test_add_item_updates_count(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        checklist = Checklist.objects.create(owner=self.owner, title="Grocery Run")
        self.client.post(
            reverse("checklist_item_create", args=[checklist.pk]),
            {"text": "Milk"},
        )
        self.assertEqual(checklist.items.count(), 1)
        self.assertEqual(checklist.items.first().text, "Milk")

    def test_toggle_completion(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        checklist = Checklist.objects.create(owner=self.owner, title="Grocery Run")
        item = ChecklistItem.objects.create(
            checklist=checklist, text="Milk", position=1
        )
        url = reverse("checklist_item_toggle", args=[checklist.pk, item.pk])
        self.client.post(url)
        item.refresh_from_db()
        self.assertTrue(item.is_complete)
        # Toggle again returns to incomplete (acceptance 4).
        self.client.post(url)
        item.refresh_from_db()
        self.assertFalse(item.is_complete)

    def test_edit_item_text(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        checklist = Checklist.objects.create(owner=self.owner, title="Grocery Run")
        item = ChecklistItem.objects.create(
            checklist=checklist, text="Milk", position=1
        )
        self.client.post(
            reverse("checklist_item_edit", args=[checklist.pk, item.pk]),
            {"text": "Oat milk"},
        )
        item.refresh_from_db()
        self.assertEqual(item.text, "Oat milk")

    def test_delete_item(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        checklist = Checklist.objects.create(owner=self.owner, title="Grocery Run")
        item = ChecklistItem.objects.create(
            checklist=checklist, text="Milk", position=1
        )
        self.client.post(reverse("checklist_item_delete", args=[checklist.pk, item.pk]))
        self.assertEqual(checklist.items.count(), 0)

    def test_delete_checklist_removes_items(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        checklist = Checklist.objects.create(owner=self.owner, title="Grocery Run")
        ChecklistItem.objects.create(checklist=checklist, text="Milk", position=1)
        self.client.post(reverse("checklist_delete", args=[checklist.pk]))
        self.assertFalse(Checklist.objects.filter(pk=checklist.pk).exists())
        self.assertEqual(ChecklistItem.objects.count(), 0)

    def test_template_quick_start_creates_prefilled_items(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        response = self.client.post(
            reverse("checklist_new"),
            {"title": "Trail trip", "template": "Travel Packing"},
        )
        checklist = Checklist.objects.get(title="Trail trip")
        self.assertRedirects(response, reverse("checklist_detail", args=[checklist.pk]))
        self.assertEqual(checklist.items.count(), 5)
        # Pre-filled items are editable (acceptance 3).
        first = checklist.items.first()
        self.client.post(
            reverse("checklist_item_edit", args=[checklist.pk, first.pk]),
            {"text": "Passport"},
        )
        first.refresh_from_db()
        self.assertEqual(first.text, "Passport")

    def test_unknown_template_rejected(self):
        self.client.login(email="owner@example.com", password="Sup3r-secret!")
        response = self.client.post(
            reverse("checklist_new"),
            {"title": "X", "template": "Not A Template"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Checklist.objects.count(), 0)


class SharingTests(TestCase):
    """Secure sharing with read-only recipients and revocation (US-2)."""

    def setUp(self):
        self.owner = _new_user("owner@example.com", display_name="Owner")
        self.recipient = _new_user("recipient@example.com", display_name="Recipient")
        self.checklist = Checklist.objects.create(owner=self.owner, title="Grocery Run")
        ChecklistItem.objects.create(checklist=self.checklist, text="Milk", position=1)

    def _login(self, email):
        self.client.login(email=email, password="Sup3r-secret!")

    def test_share_with_registered_user_creates_share_and_notifies(self):
        self._login("owner@example.com")
        response = self.client.post(
            reverse("checklist_share", args=[self.checklist.pk]),
            {"email": "recipient@example.com"},
        )
        self.assertRedirects(
            response, reverse("checklist_share", args=[self.checklist.pk])
        )
        share = ChecklistShare.objects.get(
            checklist=self.checklist, recipient=self.recipient
        )
        self.assertEqual(share.status, ChecklistShare.STATUS_ACTIVE)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.recipient, type=Notification.TYPE_SHARE
            ).exists()
        )

    def test_share_with_unregistered_email_rejected(self):
        self._login("owner@example.com")
        response = self.client.post(
            reverse("checklist_share", args=[self.checklist.pk]),
            {"email": "nobody@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No user with that email address")
        self.assertEqual(ChecklistShare.objects.count(), 0)

    def test_share_with_self_rejected(self):
        self._login("owner@example.com")
        response = self.client.post(
            reverse("checklist_share", args=[self.checklist.pk]),
            {"email": "owner@example.com"},
        )
        self.assertRedirects(
            response, reverse("checklist_share", args=[self.checklist.pk])
        )
        self.assertEqual(ChecklistShare.objects.count(), 0)

    def test_share_twice_reports_already_shared(self):
        self._login("owner@example.com")
        self.client.post(
            reverse("checklist_share", args=[self.checklist.pk]),
            {"email": "recipient@example.com"},
        )
        response = self.client.post(
            reverse("checklist_share", args=[self.checklist.pk]),
            {"email": "recipient@example.com"},
        )
        self.assertRedirects(
            response, reverse("checklist_share", args=[self.checklist.pk])
        )
        self.assertEqual(ChecklistShare.objects.count(), 1)

    def test_recipient_sees_shared_checklist_with_label(self):
        self._login("owner@example.com")
        self.client.post(
            reverse("checklist_share", args=[self.checklist.pk]),
            {"email": "recipient@example.com"},
        )
        self.client.post(reverse("logout"))
        self._login("recipient@example.com")
        response = self.client.get(reverse("checklist_shared"))
        self.assertContains(response, "Grocery Run")
        self.assertContains(response, "Shared by")
        # Recipient can view the checklist detail read-only.
        detail = self.client.get(
            reverse("checklist_detail", args=[self.checklist.pk])
        )
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Shared by")
        self.assertContains(detail, "Milk")

    def test_recipient_cannot_edit_or_add_items(self):
        self._login("owner@example.com")
        self.client.post(
            reverse("checklist_share", args=[self.checklist.pk]),
            {"email": "recipient@example.com"},
        )
        self.client.post(reverse("logout"))
        self._login("recipient@example.com")
        # Adding an item as a non-owner returns 404 (scoped to owner only).
        response = self.client.post(
            reverse("checklist_item_create", args=[self.checklist.pk]),
            {"text": "Hacked"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(self.checklist.items.first().text, "Hacked")

    def test_owner_revokes_and_recipient_loses_access_and_is_notified(self):
        self._login("owner@example.com")
        self.client.post(
            reverse("checklist_share", args=[self.checklist.pk]),
            {"email": "recipient@example.com"},
        )
        share = ChecklistShare.objects.get(checklist=self.checklist, recipient=self.recipient)
        response = self.client.post(
            reverse("checklist_share_revoke", args=[self.checklist.pk, share.pk])
        )
        self.assertRedirects(
            response, reverse("checklist_share", args=[self.checklist.pk])
        )
        share.refresh_from_db()
        self.assertEqual(share.status, ChecklistShare.STATUS_REVOKED)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.recipient, type=Notification.TYPE_REVOCATION
            ).exists()
        )
        # Recipient loses it from shared list.
        self.client.post(reverse("logout"))
        self._login("recipient@example.com")
        response = self.client.get(reverse("checklist_shared"))
        self.assertNotContains(response, "Grocery Run")

    def test_user_without_access_gets_error_not_leakage(self):
        # An unrelated user cannot view the owner's checklist (SC-006).
        outsider = _new_user("outsider@example.com")
        self._login("outsider@example.com")
        response = self.client.get(
            reverse("checklist_detail", args=[self.checklist.pk])
        )
        self.assertEqual(response.status_code, 403)


class EmergencyAccessTests(TestCase):
    """Emergency access flow (US-3, FR-009..013)."""

    def setUp(self):
        self.owner = _new_user("owner@example.com", display_name="Owner")
        self.contact = _new_user("contact@example.com", display_name="Contact")
        self.checklist = Checklist.objects.create(owner=self.owner, title="Important")
        ChecklistItem.objects.create(checklist=self.checklist, text="Vital", position=1)

    def _login(self, email):
        self.client.login(email=email, password="Sup3r-secret!")

    def test_designate_emergency_contact(self):
        self._login("owner@example.com")
        response = self.client.post(reverse("emergency"), {"email": "contact@example.com"})
        self.assertRedirects(response, reverse("emergency"))
        self.assertTrue(
            EmergencyContact.objects.filter(owner=self.owner, contact=self.contact).exists()
        )

    def test_designate_unregistered_contact_rejected(self):
        self._login("owner@example.com")
        response = self.client.post(reverse("emergency"), {"email": "nobody@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No user with that email address")
        self.assertEqual(EmergencyContact.objects.count(), 0)

    def test_designate_self_rejected(self):
        self._login("owner@example.com")
        response = self.client.post(reverse("emergency"), {"email": "owner@example.com"})
        self.assertRedirects(response, reverse("emergency"))
        self.assertEqual(EmergencyContact.objects.count(), 0)

    def test_designate_duplicate_rejected(self):
        self._login("owner@example.com")
        self.client.post(reverse("emergency"), {"email": "contact@example.com"})
        self.client.post(reverse("emergency"), {"email": "contact@example.com"})
        self.assertEqual(EmergencyContact.objects.count(), 1)

    def test_request_access_notifies_owner(self):
        self._login("owner@example.com")
        self.client.post(reverse("emergency"), {"email": "contact@example.com"})
        self.client.post(reverse("logout"))
        self._login("contact@example.com")
        response = self.client.post(
            reverse("emergency_request_create", args=[self.owner.pk])
        )
        self.assertRedirects(response, reverse("emergency_request"))
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.owner, type=Notification.TYPE_EMERGENCY_REQUEST
            ).exists()
        )

    def test_non_contact_cannot_request_access(self):
        outsider = _new_user("outsider@example.com")
        self._login("outsider@example.com")
        response = self.client.post(
            reverse("emergency_request_create", args=[self.owner.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_approve_grants_viewer_access_and_notifies_both(self):
        self._login("owner@example.com")
        self.client.post(reverse("emergency"), {"email": "contact@example.com"})
        self.client.post(reverse("logout"))
        self._login("contact@example.com")
        self.client.post(reverse("emergency_request_create", args=[self.owner.pk]))
        self.client.post(reverse("logout"))

        self._login("owner@example.com")
        request_obj = EmergencyAccessRequest.objects.get(
            owner=self.owner, requester=self.contact
        )
        response = self.client.post(
            reverse("emergency_approve", args=[request_obj.pk])
        )
        self.assertRedirects(
            response, reverse("emergency_respond", args=[request_obj.pk])
        )
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, EmergencyAccessRequest.STATUS_APPROVED)
        for email in ("owner@example.com", "contact@example.com"):
            self.assertTrue(
                Notification.objects.filter(
                    recipient=User.objects.get(email=email),
                    type=Notification.TYPE_EMERGENCY_RESPONSE,
                ).exists()
            )
        # Contact gains read-only viewer access to owner's checklists.
        self.client.post(reverse("logout"))
        self._login("contact@example.com")
        detail = self.client.get(
            reverse("checklist_detail", args=[self.checklist.pk])
        )
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Shared by")

    def test_deny_notifies_contact_and_grants_no_access(self):
        self._login("owner@example.com")
        self.client.post(reverse("emergency"), {"email": "contact@example.com"})
        self.client.post(reverse("logout"))
        self._login("contact@example.com")
        self.client.post(reverse("emergency_request_create", args=[self.owner.pk]))
        self.client.post(reverse("logout"))

        self._login("owner@example.com")
        request_obj = EmergencyAccessRequest.objects.get(
            owner=self.owner, requester=self.contact
        )
        self.client.post(reverse("emergency_deny", args=[request_obj.pk]))
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, EmergencyAccessRequest.STATUS_DENIED)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.contact, type=Notification.TYPE_EMERGENCY_RESPONSE
            ).exists()
        )
        # Contact gains no access.
        self.client.post(reverse("logout"))
        self._login("contact@example.com")
        response = self.client.get(
            reverse("checklist_detail", args=[self.checklist.pk])
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(CLA_OK_EMERGENCY_AUTO_GRANT_HOURS=0)
    def test_auto_grant_after_timeout(self):
        self._login("owner@example.com")
        self.client.post(reverse("emergency"), {"email": "contact@example.com"})
        self.client.post(reverse("logout"))
        self._login("contact@example.com")
        # Create a pending request whose deadline is already in the past (hours=0).
        self.client.post(reverse("emergency_request_create", args=[self.owner.pk]))
        request_obj = EmergencyAccessRequest.objects.get(
            owner=self.owner, requester=self.contact
        )
        self.assertEqual(request_obj.status, EmergencyAccessRequest.STATUS_PENDING)
        # Revisit the request page: lazy auto-grant triggers (FR-011, SC-003).
        self.client.get(reverse("emergency_request"))
        request_obj.refresh_from_db()
        self.assertEqual(
            request_obj.status, EmergencyAccessRequest.STATUS_AUTO_GRANTED
        )
        for email in ("owner@example.com", "contact@example.com"):
            self.assertTrue(
                Notification.objects.filter(
                    recipient=User.objects.get(email=email),
                    type=Notification.TYPE_EMERGENCY_RESPONSE,
                ).exists()
            )
        # Contact now has read-only viewer access to all owner checklists.
        detail = self.client.get(
            reverse("checklist_detail", args=[self.checklist.pk])
        )
        self.assertEqual(detail.status_code, 200)

    def test_remove_contact_cancels_pending_and_revokes_grant(self):
        # Set up an approved grant.
        self._login("owner@example.com")
        self.client.post(reverse("emergency"), {"email": "contact@example.com"})
        self.client.post(reverse("logout"))
        self._login("contact@example.com")
        self.client.post(reverse("emergency_request_create", args=[self.owner.pk]))
        self.client.post(reverse("logout"))
        self._login("owner@example.com")
        request_obj = EmergencyAccessRequest.objects.get(
            owner=self.owner, requester=self.contact
        )
        self.client.post(reverse("emergency_approve", args=[request_obj.pk]))

        # Now remove the contact.
        contact_rel = EmergencyContact.objects.get(
            owner=self.owner, contact=self.contact
        )
        response = self.client.post(
            reverse("emergency_contact_remove", args=[contact_rel.pk])
        )
        self.assertRedirects(response, reverse("emergency"))
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, EmergencyAccessRequest.STATUS_CANCELLED)
        self.assertFalse(
            EmergencyContact.objects.filter(pk=contact_rel.pk).exists()
        )
        # Contact loses granted access.
        self.client.post(reverse("logout"))
        self._login("contact@example.com")
        response = self.client.get(
            reverse("checklist_detail", args=[self.checklist.pk])
        )
        self.assertEqual(response.status_code, 403)


class NotificationCenterTests(TestCase):
    """Notification center + unread badge (US-4, FR-014/015/016)."""

    def setUp(self):
        self.owner = _new_user("owner@example.com", display_name="Owner")
        self.recipient = _new_user("recipient@example.com", display_name="Recipient")

    def _login(self, email):
        self.client.login(email=email, password="Sup3r-secret!")

    def _make_noop_notification(self):
        return Notification.objects.create(
            recipient=self.recipient,
            type=Notification.TYPE_SHARE,
            message="A shared checklist.",
        )

    def test_notification_center_requires_login(self):
        response = self.client.get(reverse("notifications"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("notifications")
        )

    def test_notification_appears_with_message_timestamp_and_unread(self):
        self._make_noop_notification()
        self._login("recipient@example.com")
        response = self.client.get(reverse("notifications"))
        self.assertContains(response, "A shared checklist.")
        self.assertContains(response, "Unread")

    def test_mark_one_read(self):
        notification = self._make_noop_notification()
        self._login("recipient@example.com")
        response = self.client.post(
            reverse("notification_read", args=[notification.pk])
        )
        self.assertRedirects(response, reverse("notifications"))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_read(self):
        n1 = self._make_noop_notification()
        n2 = Notification.objects.create(
            recipient=self.recipient,
            type=Notification.TYPE_REVOCATION,
            message="Access revoked.",
        )
        self._login("recipient@example.com")
        self.client.post(reverse("notification_read_all"))
        n1.refresh_from_db()
        n2.refresh_from_db()
        self.assertTrue(n1.is_read)
        self.assertTrue(n2.is_read)

    def test_clear_all(self):
        self._make_noop_notification()
        self._login("recipient@example.com")
        self.client.post(reverse("notification_clear"))
        self.assertEqual(Notification.objects.filter(recipient=self.recipient).count(), 0)

    def test_header_badge_shows_unread_count(self):
        self._make_noop_notification()
        Notification.objects.create(
            recipient=self.recipient,
            type=Notification.TYPE_EMERGENCY_REQUEST,
            message="Emergency request.",
        )
        self._login("recipient@example.com")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Notifications")
        self.assertContains(response, ">2<")

    def test_notification_click_marks_read_and_navigates(self):
        owner = self.recipient
        checklist = Checklist.objects.create(owner=owner, title="Shared list")
        notification = Notification.objects.create(
            recipient=owner,
            type=Notification.TYPE_SHARE,
            message="See this checklist.",
            related_checklist=checklist,
        )
        self._login("recipient@example.com")
        target = reverse("checklist_detail", args=[checklist.pk])
        response = self.client.post(
            reverse("notification_read", args=[notification.pk]),
            {"next": target},
        )
        self.assertRedirects(response, target)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)


class AuthorizationTests(TestCase):
    """Cross-account authorization (FR-019/020, SC-006)."""

    def setUp(self):
        self.owner = _new_user("owner@example.com")
        self.other = _new_user("other@example.com")

    def test_other_user_cannot_manage_owners_checklist(self):
        checklist = Checklist.objects.create(owner=self.owner, title="Secret")
        self.client.login(email="other@example.com", password="Sup3r-secret!")
        # Add-item POST returns 404 (scoped to owner).
        response = self.client.post(
            reverse("checklist_item_create", args=[checklist.pk]),
            {"text": "Intrusion"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(checklist.items.count(), 0)
        # Delete POST returns 404.
        response = self.client.post(reverse("checklist_delete", args=[checklist.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Checklist.objects.filter(pk=checklist.pk).exists())

    def test_emergency_respond_requires_owner(self):
        from django.utils import timezone

        request_obj = EmergencyAccessRequest.objects.create(
            owner=self.owner,
            requester=self.other,
            status=EmergencyAccessRequest.STATUS_PENDING,
            timeout_deadline=timezone.now() + timezone.timedelta(hours=1),
        )
        self.client.login(email="other@example.com", password="Sup3r-secret!")
        response = self.client.get(
            reverse("emergency_respond", args=[request_obj.pk])
        )
        self.assertEqual(response.status_code, 403)
