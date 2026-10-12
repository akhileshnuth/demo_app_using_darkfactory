from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import ActivityLog
from checklists import services
from checklists.models import (
    Checklist,
    ChecklistItem,
    ChecklistShare,
    EmergencyAccessRequest,
    EmergencyContact,
    Notification,
)


class ChecklistFlowTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@example.com", password="Strong-pass1"
        )
        self.recipient = get_user_model().objects.create_user(
            email="recipient@example.com", password="Strong-pass1"
        )
        self.other = get_user_model().objects.create_user(
            email="other@example.com", password="Strong-pass1"
        )
        self.checklist = Checklist.objects.create(owner=self.owner, title="Moving")

    def test_owner_can_create_from_template_and_mutate_items(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("checklist_new"), {"title": "Trip", "template": "Grocery List"}
        )
        checklist = Checklist.objects.get(title="Trip")

        self.assertRedirects(response, reverse("checklist_detail", args=[checklist.pk]))
        self.assertEqual(checklist.item_count, 5)

        item = ChecklistItem.objects.filter(checklist=checklist).first()
        response = self.client.post(
            reverse("checklist_item_toggle", args=[checklist.pk, item.pk])
        )
        item.refresh_from_db()
        self.assertRedirects(response, reverse("checklist_detail", args=[checklist.pk]))
        self.assertTrue(item.is_complete)

    def test_non_owner_cannot_edit_but_active_share_can_view(self):
        share, _ = services.share_checklist(self.checklist, self.recipient)
        self.client.force_login(self.recipient)

        response = self.client.get(reverse("checklist_detail", args=[self.checklist.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.checklist.title)
        self.assertTrue(
            ActivityLog.objects.filter(
                user=self.recipient,
                event_type=ActivityLog.EventType.SHARE_ACCESSED,
            ).exists()
        )

        response = self.client.post(
            reverse("checklist_item_create", args=[self.checklist.pk]),
            {"text": "Not allowed"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ChecklistItem.objects.count(), 0)

        services.revoke_share(share)
        self.assertFalse(services.can_view(self.recipient, self.checklist))
        self.assertEqual(Notification.objects.filter(recipient=self.recipient).count(), 2)

    def test_invalid_item_is_not_created(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("checklist_item_create", args=[self.checklist.pk]), {"text": ""}
        )

        self.assertRedirects(response, reverse("checklist_detail", args=[self.checklist.pk]))
        self.assertFalse(ChecklistItem.objects.exists())

    def test_emergency_access_approval_and_contact_removal_revoke_access(self):
        contact = EmergencyContact.objects.create(owner=self.owner, contact=self.recipient)
        request_obj = services.request_emergency_access(self.recipient, self.owner)
        self.assertEqual(request_obj.status, EmergencyAccessRequest.STATUS_PENDING)
        self.assertFalse(services.can_view(self.recipient, self.checklist))

        self.assertTrue(services.approve_emergency_request(request_obj))
        self.assertTrue(services.can_view(self.recipient, self.checklist))
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, EmergencyAccessRequest.STATUS_APPROVED)

        services.remove_emergency_contact(contact)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, EmergencyAccessRequest.STATUS_CANCELLED)
        self.assertFalse(services.can_view(self.recipient, self.checklist))

    def test_expired_emergency_request_is_auto_granted(self):
        EmergencyContact.objects.create(owner=self.owner, contact=self.recipient)
        request_obj = EmergencyAccessRequest.objects.create(
            owner=self.owner,
            requester=self.recipient,
            timeout_deadline=timezone.now() - timedelta(minutes=1),
        )

        self.assertTrue(services._auto_grant_if_expired(request_obj))
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, EmergencyAccessRequest.STATUS_AUTO_GRANTED)
        self.assertTrue(services.can_view(self.recipient, self.checklist))

    def test_notifications_are_private_and_can_be_cleared(self):
        own = Notification.objects.create(
            recipient=self.owner,
            type=Notification.TYPE_SHARE,
            message="For owner",
        )
        Notification.objects.create(
            recipient=self.recipient,
            type=Notification.TYPE_SHARE,
            message="For recipient",
        )
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("notification_read", args=[own.pk]), {"next": "/checklists/"}
        )
        self.assertRedirects(response, "/checklists/")
        own.refresh_from_db()
        self.assertTrue(own.is_read)

        self.client.post(reverse("notification_clear"))
        self.assertFalse(Notification.objects.filter(recipient=self.owner).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.recipient).exists())

    def test_unauthenticated_checklist_routes_redirect_to_login(self):
        response = self.client.get(reverse("checklist_list"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('checklist_list')}",
        )
