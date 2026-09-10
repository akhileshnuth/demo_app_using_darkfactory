"""Policy logic for checklists, sharing, emergency access and notifications.

Centralises the authorization and state-transition rules so views stay thin and
the FR-019/FR-020/SC-006 guarantees are enforced in one place:

- ``can_edit``/``can_view`` gate every resource access.
- Notification creation (``notify``) and the unread badge count.
- Emergency request/approve/deny/auto-grant and contact-removal cascades.
- Share creation/revocation with notification side effects.
"""

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    ChecklistShare,
    EmergencyAccessRequest,
    Notification,
)


EMERGENCY_VIEWER_STATUSES = {
    EmergencyAccessRequest.STATUS_APPROVED,
    EmergencyAccessRequest.STATUS_AUTO_GRANTED,
}


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

def can_edit(user, checklist):
    """Only the owner may edit/delete a checklist (FR-007, FR-020)."""
    return checklist.owner_id == user.id


def can_view(user, checklist):
    """Whether ``user`` may view ``checklist``.

    Owners, active share recipients and holders of an approved/auto-granted
    emergency request against the owner may all view. Shared/emergency access is
    read-only (never grants edit).
    """
    if can_edit(user, checklist):
        return True
    if ChecklistShare.objects.filter(
        checklist=checklist,
        recipient=user,
        status=ChecklistShare.STATUS_ACTIVE,
    ).exists():
        return True
    return has_emergency_grant(user, checklist.owner)


def has_emergency_grant(user, owner):
    """True if ``user`` holds an active approved/auto-granted request on ``owner``.

    The owner and requester must both be active accounts (account deactivation
    revokes implicit access — data-model R12).
    """
    if not owner.is_active or not user.is_active:
        return False
    return EmergencyAccessRequest.objects.filter(
        owner=owner,
        requester=user,
        status__in=EMERGENCY_VIEWER_STATUSES,
    ).exists()


def can_respond_to_request(user, request_obj):
    """Only a request's owner may respond (approve/deny) — FR-020."""
    return request_obj.owner_id == user.id


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def notify(recipient, type, message, **related):
    """Create an in-app notification for ``recipient`` (FR-014)."""
    return Notification.objects.create(
        recipient=recipient,
        type=type,
        message=message,
        related_checklist=related.get("checklist"),
        related_share=related.get("share"),
        related_request=related.get("request"),
    )


def unread_notification_count(user):
    """Unread notification count for the header badge (FR-016)."""
    return Notification.objects.filter(recipient=user, is_read=False).count()


# ---------------------------------------------------------------------------
# Sharing
# ---------------------------------------------------------------------------

def share_checklist(checklist, recipient):
    """Share ``checklist`` with ``recipient``, notifying them (FR-005).

    Returns a 2-tuple ``(share, created)``. If a (possibly revoked) share row
    already exists for this checklist/recipient it is re-activated rather than
    duplicated (edge case), matching ``uniq_share``.
    """
    share = ChecklistShare.objects.filter(
        checklist=checklist, recipient=recipient
    ).first()
    if share is not None:
        created = share.status != ChecklistShare.STATUS_ACTIVE
        if created:
            share.status = ChecklistShare.STATUS_ACTIVE
            share.save(update_fields=["status"])
        return share, created
    share = ChecklistShare.objects.create(
        checklist=checklist, recipient=recipient, status=ChecklistShare.STATUS_ACTIVE
    )
    notify(
        recipient,
        Notification.TYPE_SHARE,
        f"{checklist.owner.email} shared a checklist with you: "
        f"'{checklist.title}'.",
        checklist=checklist,
        share=share,
    )
    return share, True


def revoke_share(share):
    """Revoke an active share and notify the recipient (FR-008)."""
    if share.status == ChecklistShare.STATUS_REVOKED:
        return
    share.status = ChecklistShare.STATUS_REVOKED
    share.save(update_fields=["status"])
    notify(
        share.recipient,
        Notification.TYPE_REVOCATION,
        f"{share.checklist.owner.email} revoked your access to "
        f"'{share.checklist.title}'.",
        checklist=share.checklist,
        share=share,
    )


# ---------------------------------------------------------------------------
# Emergency access
# ---------------------------------------------------------------------------

def is_emergency_contact(owner, contact):
    """Whether ``contact`` is a currently designated emergency contact of owner."""
    from .models import EmergencyContact

    return EmergencyContact.objects.filter(owner=owner, contact=contact).exists()


def _auto_grant_if_expired(request_obj):
    """Lazy auto-grant: resolve an expired pending request (FR-011, SC-003).

    If ``request_obj`` is pending and its deadline has passed, resolve to
    ``auto_granted`` and notify both parties. Returns True if a grant happened.
    """
    if (
        request_obj.status == EmergencyAccessRequest.STATUS_PENDING
        and request_obj.timeout_deadline <= timezone.now()
    ):
        resolved = request_obj.resolve(EmergencyAccessRequest.STATUS_AUTO_GRANTED)
        if resolved == EmergencyAccessRequest.STATUS_AUTO_GRANTED:
            notify(
                request_obj.owner,
                Notification.TYPE_EMERGENCY_RESPONSE,
                f"Emergency access was auto-granted to "
                f"{request_obj.requester.display_name or request_obj.requester.email} "
                "after no response.",
                request=request_obj,
            )
            notify(
                request_obj.requester,
                Notification.TYPE_EMERGENCY_RESPONSE,
                "Your emergency access request was auto-granted after the owner "
                "did not respond.",
                request=request_obj,
            )
            return True
    return False


def request_emergency_access(contact, owner):
    """Create (or re-surface) an emergency access request (FR-010).

    ``contact`` must be a designated emergency contact of ``owner``, otherwise
    None is returned. If an unresolved request already exists it is returned
    instead of duplicated. If that pending request has expired it is
    auto-granted (lazy, R8). Otherwise a new pending request is created and the
    owner notified (FR-012).
    """
    if not is_emergency_contact(owner, contact):
        return None

    latest = (
        EmergencyAccessRequest.objects.filter(owner=owner, requester=contact)
        .order_by("-requested_at")
        .first()
    )
    if latest is not None and not latest.is_resolved:
        _auto_grant_if_expired(latest)
        return latest

    hours = getattr(settings, "CLA_OK_EMERGENCY_AUTO_GRANT_HOURS", 72)
    timeout_deadline = timezone.now() + timezone.timedelta(hours=hours)
    request_obj = EmergencyAccessRequest.objects.create(
        owner=owner,
        requester=contact,
        status=EmergencyAccessRequest.STATUS_PENDING,
        timeout_deadline=timeout_deadline,
    )
    notify(
        owner,
        Notification.TYPE_EMERGENCY_REQUEST,
        f"{contact.display_name or contact.email} has requested emergency access "
        "to your checklists.",
        request=request_obj,
    )
    return request_obj


def approve_emergency_request(request_obj):
    """Approve a pending request, granting viewer access (FR-013)."""
    resolved = request_obj.resolve(EmergencyAccessRequest.STATUS_APPROVED)
    if resolved != EmergencyAccessRequest.STATUS_APPROVED:
        return False
    notify(
        request_obj.requester,
        Notification.TYPE_EMERGENCY_RESPONSE,
        f"{request_obj.owner.email} approved your emergency access request.",
        request=request_obj,
    )
    notify(
        request_obj.owner,
        Notification.TYPE_EMERGENCY_RESPONSE,
        f"You approved emergency access for "
        f"{request_obj.requester.display_name or request_obj.requester.email}.",
        request=request_obj,
    )
    return True


def deny_emergency_request(request_obj):
    """Deny a pending request (FR-013). Grants no access."""
    resolved = request_obj.resolve(EmergencyAccessRequest.STATUS_DENIED)
    if resolved != EmergencyAccessRequest.STATUS_DENIED:
        return False
    notify(
        request_obj.requester,
        Notification.TYPE_EMERGENCY_RESPONSE,
        f"{request_obj.owner.email} denied your emergency access request.",
        request=request_obj,
    )
    return True


@transaction.atomic
def remove_emergency_contact(emergency_contact):
    """Remove a designated emergency contact (acceptance 6).

    In one transaction: pending requests are cancelled, any granted
    (approved/auto-granted) access is revoked, and the relationship is deleted.
    The removed contact is notified if they held access.
    """
    from .models import EmergencyContact

    granted_before = EmergencyAccessRequest.objects.filter(
        owner=emergency_contact.owner,
        requester=emergency_contact.contact,
        status__in=EMERGENCY_VIEWER_STATUSES,
    ).exists()

    EmergencyAccessRequest.objects.filter(
        owner=emergency_contact.owner,
        requester=emergency_contact.contact,
        status=EmergencyAccessRequest.STATUS_PENDING,
    ).update(
        status=EmergencyAccessRequest.STATUS_CANCELLED,
        resolved_at=timezone.now(),
    )
    EmergencyAccessRequest.objects.filter(
        owner=emergency_contact.owner,
        requester=emergency_contact.contact,
        status__in=EMERGENCY_VIEWER_STATUSES,
    ).update(
        status=EmergencyAccessRequest.STATUS_CANCELLED,
        resolved_at=timezone.now(),
    )

    if granted_before:
        notify(
            emergency_contact.contact,
            Notification.TYPE_EMERGENCY_RESPONSE,
            f"{emergency_contact.owner.email} removed you as an emergency contact "
            "and revoked your emergency access.",
        )

    EmergencyContact.objects.filter(pk=emergency_contact.pk).delete()
