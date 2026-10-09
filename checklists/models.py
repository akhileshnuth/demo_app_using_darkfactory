import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class DuplicateModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('name', 'created_at'),)

    def is_duplicate(self):
        return DuplicateModel.objects.filter(name=self.name, created_at__date=datetime.date.today()).exists()


class Checklist(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="checklists",
    )
    title = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    @property
    def item_count(self):
        return self.items.count()

    @property
    def completed_count(self):
        return self.items.filter(is_complete=True).count()

    @property
    def completion_percentage(self):
        if not self.item_count:
            return 0
        return int(self.completed_count * 100 / self.item_count)

    @property
    def shared_with(self):
        return self.shares.filter(status=ChecklistShare.STATUS_ACTIVE)


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.CASCADE,
        related_name="items",
    )
    text = models.CharField(max_length=200)
    is_complete = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["checklist", "position"], name="uniq_item_position"
            )
        ]


class ChecklistShare(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_REVOKED, "Revoked"),
    )

    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_checklists",
    )
    shared_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )

    class Meta:
        ordering = ["-shared_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["checklist", "recipient"], name="uniq_share"
            )
        ]


class EmergencyContact(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
    )
    contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_emergency_contacts",
    )
    designated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-designated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "contact"], name="uniq_emergency_contact"
            )
        ]

    def clean(self):
        if self.owner_id and self.owner_id == self.contact_id:
            raise ValidationError("The owner cannot be their own emergency contact.")


class EmergencyAccessRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_DENIED = "denied"
    STATUS_AUTO_GRANTED = "auto_granted"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DENIED, "Denied"),
        (STATUS_AUTO_GRANTED, "Auto-granted"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_requests",
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_requests_made",
    )
    status = models.CharField(
        max_length=14,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    timeout_deadline = models.DateTimeField()

    class Meta:
        ordering = ["-requested_at"]

    @property
    def is_resolved(self):
        return self.status != self.STATUS_PENDING

    def resolve(self, status):
        if status not in {
            self.STATUS_APPROVED,
            self.STATUS_DENIED,
            self.STATUS_AUTO_GRANTED,
            self.STATUS_CANCELLED,
        }:
            return self.status
        resolved_at = timezone.now()
        updated = type(self).objects.filter(
            pk=self.pk, status=self.STATUS_PENDING
        ).update(status=status, resolved_at=resolved_at)
        if updated:
            self.status = status
            self.resolved_at = resolved_at
        return self.status


class Notification(models.Model):
    TYPE_SHARE = "share"
    TYPE_REVOCATION = "revocation"
    TYPE_EMERGENCY_REQUEST = "emergency_request"
    TYPE_EMERGENCY_RESPONSE = "emergency_response"
    TYPE_CHOICES = (
        (TYPE_SHARE, "Share"),
        (TYPE_REVOCATION, "Revocation"),
        (TYPE_EMERGENCY_REQUEST, "Emergency request"),
        (TYPE_EMERGENCY_RESPONSE, "Emergency response"),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.CharField(max_length=280)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_checklist = models.ForeignKey(
        Checklist,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    related_share = models.ForeignKey(
        ChecklistShare,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    related_request = models.ForeignKey(
        EmergencyAccessRequest,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )

    class Meta:
        ordering = ["-created_at"]
