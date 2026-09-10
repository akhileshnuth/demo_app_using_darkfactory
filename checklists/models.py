"""Data models for the checklists app.

Implements the Key Entities from DFT-9: ``Checklist``, ``ChecklistItem``,
``ChecklistShare``, ``EmergencyContact``, ``EmergencyAccessRequest`` and
``Notification``. All reference ``settings.AUTH_USER_MODEL``
(``accounts.User``) so no change to the zoned ``accounts`` app is required.

See specs/DFT-9/data-model.md for the field contracts and state machines.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Checklist(models.Model):
    """A user's titled checklist (FR-002)."""

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

    def __str__(self):
        return self.title

    @property
    def item_count(self):
        return self.items.count()

    @property
    def completed_count(self):
        return self.items.filter(is_complete=True).count()

    @property
    def completion_percentage(self):
        total = self.item_count
        if total == 0:
            return 0
        return int(round(100 * self.completed_count / total))

    @property
    def shared_with(self):
        """Users the checklist is actively shared with."""
        return [
            share.recipient
            for share in self.shares.filter(status=ChecklistShare.STATUS_ACTIVE)
        ]


class ChecklistItem(models.Model):
    """An individual item within a checklist (FR-003)."""

    checklist = models.ForeignKey(
        Checklist, on_delete=models.CASCADE, related_name="items"
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
                fields=["checklist", "position"],
                name="uniq_item_position",
            )
        ]

    def __str__(self):
        return self.text


class ChecklistShare(models.Model):
    """A sharing relationship between a checklist owner and a recipient.

    Read-only for recipients (FR-007); ``status`` preserves share history so a
    revoked share can be re-activated without duplicating rows (FR-008).
    """

    STATUS_ACTIVE = "active"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_REVOKED, "Revoked"),
    ]

    checklist = models.ForeignKey(
        Checklist, on_delete=models.CASCADE, related_name="shares"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_checklists",
    )
    shared_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )

    class Meta:
        ordering = ["-shared_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["checklist", "recipient"],
                name="uniq_share",
            )
        ]

    def __str__(self):
        return f"{self.checklist.title} -> {self.recipient.email}"


class EmergencyContact(models.Model):
    """A designated emergency contact for a user (FR-009).

    Multiple contacts per owner are allowed; a contact must be a different
    registered user than the owner.
    """

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
                fields=["owner", "contact"],
                name="uniq_emergency_contact",
            )
        ]

    def __str__(self):
        return f"{self.owner.email} <-> {self.contact.email}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.owner_id and self.owner_id == self.contact_id:
            raise ValidationError("Cannot designate yourself as an emergency contact.")


class EmergencyAccessRequest(models.Model):
    """A request from an emergency contact for access to the owner's checklists.

    State machine (single-step, guarded transitions — see data-model R8/R9):
    ``pending`` -> ``approved`` | ``denied`` | ``auto_granted`` | ``cancelled``.
    ``approved``/``auto_granted`` grant viewer access to all of the owner's
    checklists; ``cancelled`` also revokes a previously granted access (R7).
    """

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_DENIED = "denied"
    STATUS_AUTO_GRANTED = "auto_granted"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DENIED, "Denied"),
        (STATUS_AUTO_GRANTED, "Auto-granted"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    RESOLVED_STATUSES = {
        STATUS_APPROVED,
        STATUS_DENIED,
        STATUS_AUTO_GRANTED,
        STATUS_CANCELLED,
    }

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
        max_length=14, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    timeout_deadline = models.DateTimeField()

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.owner.email} <- {self.requester.email} ({self.status})"

    @property
    def is_resolved(self):
        return self.status in self.RESOLVED_STATUSES

    def resolve(self, status):
        """Guarded single-step transition to a resolved status.

        Returns the new status, or the existing status if already resolved so a
        race cannot produce a contradictory state (R9).
        """
        if self.is_resolved:
            return self.status
        updated = (
            type(self)
            .objects.filter(pk=self.pk, status=self.STATUS_PENDING)
            .update(status=status, resolved_at=timezone.now())
        )
        if updated:
            self.status = status
            self.resolved_at = timezone.now()
            return status
        self.refresh_from_db()
        return self.status


class Notification(models.Model):
    """An in-app notification for a user (FR-014)."""

    TYPE_SHARE = "share"
    TYPE_REVOCATION = "revocation"
    TYPE_EMERGENCY_REQUEST = "emergency_request"
    TYPE_EMERGENCY_RESPONSE = "emergency_response"
    TYPE_CHOICES = [
        (TYPE_SHARE, "Share"),
        (TYPE_REVOCATION, "Revocation"),
        (TYPE_EMERGENCY_REQUEST, "Emergency request"),
        (TYPE_EMERGENCY_RESPONSE, "Emergency response"),
    ]

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
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    related_share = models.ForeignKey(
        ChecklistShare,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    related_request = models.ForeignKey(
        EmergencyAccessRequest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email}: {self.message}"
