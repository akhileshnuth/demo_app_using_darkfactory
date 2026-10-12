"""Policy logic for checklists, sharing, emergency access and notifications.

Centralises the authorization and state-transition rules so views stay thin and
the FR-019/FR-020/SC-006 guarantees are enforced in one place:

- ``can_edit``/``can_view`` gate every resource access.
- Notification creation (``notify``) and the unread badge count.
- Emergency request/approve/deny/auto-grant and contact-removal cascades.
- Share creation/revocation with notification side effects.
- Security-relevant events are recorded to ``accounts.ActivityLog`` (DFT-14)
  so each user can review their own activity.
"""

import hashlib
import secrets

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import ActivityLog

from .models import (
    Checklist,
    ChecklistShare,
    EmergencyAccessPolicy,
    EmergencyAccessSession,
    EmergencyAccessRequest,
    Notification,
    NotificationPreference,
    SecurityEvent,
)


EMERGENCY_VIEWER_STATUSES = {
    EmergencyAccessRequest.STATUS_APPROVED,
    EmergencyAccessRequest.STATUS_AUTO_GRANTED,
}


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

def can_edit(user, checklist):
    """Return whether the user owns or may contribute to the checklist."""
    if checklist.owner_id == user.id:
        return True
    return ChecklistShare.objects.filter(
        checklist=checklist,
        recipient=user,
        status=ChecklistShare.STATUS_ACTIVE,
        permission=ChecklistShare.PERMISSION_CONTRIBUTE,
    ).exists()


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
    if not has_emergency_grant(user, checklist.owner):
        return False
    policies = EmergencyAccessPolicy.objects.filter(owner=checklist.owner, enabled=True)
    if policies.exists() and not policies.filter(checklist=checklist).exists():
        return False
    return True


def has_emergency_grant(user, owner):
    """True if ``user`` holds an active approved/auto-granted request on ``owner``.

    The owner and requester must both be active accounts (account deactivation
    revokes implicit access — data-model R12).
    """
    if not owner.is_active or not user.is_active:
        return False
    requests = EmergencyAccessRequest.objects.filter(
        owner=owner,
        requester=user,
        status__in=EMERGENCY_VIEWER_STATUSES,
    )
    for request_obj in requests:
        if hasattr(request_obj, "session") and not request_obj.session.is_active:
            continue
        return True
    return False


def can_respond_to_request(user, request_obj):
    """Only a request's owner may respond (approve/deny) — FR-020."""
    return request_obj.owner_id == user.id


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def notify(recipient, type, message, **related):
    """Create an in-app notification for ``recipient`` (FR-014)."""
    preference, _ = NotificationPreference.objects.get_or_create(user=recipient)
    # Security events are always retained; optional notifications can be muted.
    optional = type not in {
        Notification.TYPE_REVOCATION,
        Notification.TYPE_EMERGENCY_REQUEST,
        Notification.TYPE_EMERGENCY_RESPONSE,
    }
    if optional and not preference.optional_enabled:
        return None
    return Notification.objects.create(
        recipient=recipient,
        type=type,
        message=message,
        related_checklist=related.get("checklist"),
        related_share=related.get("share"),
        related_request=related.get("request"),
    )


def record_security_event(actor, action, outcome, checklist=None, target_id="", **metadata):
    """Persist a minimal, queryable audit record without protected content."""
    return SecurityEvent.objects.create(
        actor=actor,
        action=action,
        outcome=outcome,
        checklist=checklist,
        target_id=str(target_id),
        metadata=metadata,
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
            ActivityLog.objects.create(
                user=checklist.owner,
                event_type=ActivityLog.EventType.SHARE_CREATED,
                description=(
                    f"Shared checklist '{checklist.title}' with "
                    f"{recipient.email}."
                ),
            )
            record_security_event(checklist.owner, "share_reactivated", "success", checklist, share.pk)
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
    ActivityLog.objects.create(
        user=checklist.owner,
        event_type=ActivityLog.EventType.SHARE_CREATED,
        description=(
            f"Shared checklist '{checklist.title}' with {recipient.email}."
        ),
    )
    record_security_event(checklist.owner, "share_created", "success", checklist, share.pk)
    return share, True


@transaction.atomic
def create_share_invitation(checklist, inviter, recipient, permission="view", expires_at=None):
    """Create a recipient-bound, single-use invitation and return ``(grant, token)``."""
    if inviter != checklist.owner or recipient == inviter:
        raise ValueError("Only the owner may share with another user.")
    if permission not in {ChecklistShare.PERMISSION_VIEW, ChecklistShare.PERMISSION_CONTRIBUTE}:
        raise ValueError("Unsupported share permission.")
    token = secrets.token_urlsafe(32)
    share, _ = ChecklistShare.objects.update_or_create(
        checklist=checklist,
        recipient=recipient,
        defaults={
            "status": ChecklistShare.STATUS_REVOKED,
            "permission": permission,
            "invitation_token_hash": hashlib.sha256(token.encode()).hexdigest(),
            "invitation_expires_at": expires_at,
            "accepted_at": None,
        },
    )
    notify(recipient, Notification.TYPE_SHARE, f"{inviter.email} invited you to a checklist.", checklist=checklist, share=share)
    record_security_event(inviter, "share_created", "invited", checklist, share.pk)
    return share, token


@transaction.atomic
def accept_share_invitation(token, recipient):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    share = ChecklistShare.objects.select_for_update().filter(
        invitation_token_hash=token_hash, recipient=recipient,
        status=ChecklistShare.STATUS_REVOKED,
    ).first()
    if share is None or (share.invitation_expires_at and share.invitation_expires_at <= timezone.now()):
        record_security_event(recipient, "share_accepted", "denied")
        return None
    share.status = ChecklistShare.STATUS_ACTIVE
    share.accepted_at = timezone.now()
    share.invitation_token_hash = ""
    share.save(update_fields=["status", "accepted_at", "invitation_token_hash"])
    record_security_event(recipient, "share_accepted", "success", share.checklist, share.pk)
    return share


def revoke_share(share):
    """Revoke an active share and notify the recipient (FR-008)."""
    if share.status == ChecklistShare.STATUS_REVOKED:
        return
    share.status = ChecklistShare.STATUS_REVOKED
    share.save(update_fields=["status"])
    ActivityLog.objects.create(
        user=share.checklist.owner,
        event_type=ActivityLog.EventType.SHARE_REVOKED,
        description=(
            f"Revoked sharing of checklist '{share.checklist.title}' "
            f"with {share.recipient.email}."
        ),
    )
    record_security_event(
        share.checklist.owner, "share_revoked", "success", share.checklist, share.pk
    )
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
            ActivityLog.objects.create(
                user=request_obj.owner,
                event_type=ActivityLog.EventType.EMERGENCY_GRANTED,
                description=(
                    f"Emergency access was auto-granted to "
                    f"{request_obj.requester.display_name or request_obj.requester.email}."
                ),
            )
            record_security_event(
                request_obj.owner, "emergency_access", "auto_granted",
                target_id=request_obj.pk,
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
    ActivityLog.objects.create(
        user=contact,
        event_type=ActivityLog.EventType.EMERGENCY_REQUESTED,
        description=f"Requested emergency access to {owner.email}'s checklists.",
    )
    record_security_event(contact, "emergency_request", "pending", target_id=request_obj.pk)
    return request_obj


def approve_emergency_request(request_obj):
    """Approve a pending request, granting viewer access (FR-013)."""
    resolved = request_obj.resolve(EmergencyAccessRequest.STATUS_APPROVED)
    if resolved != EmergencyAccessRequest.STATUS_APPROVED:
        return False
    policy = EmergencyAccessPolicy.objects.filter(
        owner=request_obj.owner, contacts=request_obj.requester, enabled=True
    ).first()
    if policy:
        EmergencyAccessSession.objects.update_or_create(
            request=request_obj,
            defaults={
                "expires_at": timezone.now() + timezone.timedelta(hours=policy.duration_hours),
                "revoked_at": None,
            },
        )
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
    ActivityLog.objects.create(
        user=request_obj.owner,
        event_type=ActivityLog.EventType.EMERGENCY_GRANTED,
        description=(
            f"Approved emergency access for "
            f"{request_obj.requester.display_name or request_obj.requester.email}."
        ),
    )
    record_security_event(
        request_obj.owner, "emergency_request", "approved", target_id=request_obj.pk
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
    ActivityLog.objects.create(
        user=request_obj.owner,
        event_type=ActivityLog.EventType.EMERGENCY_DENIED,
        description=(
            f"Denied emergency access for "
            f"{request_obj.requester.display_name or request_obj.requester.email}."
        ),
    )
    record_security_event(
        request_obj.owner, "emergency_request", "denied", target_id=request_obj.pk
    )
    return True


def revoke_emergency_session(session):
    """Revoke a released emergency session; repeated revocation is harmless."""
    if session.revoked_at is None:
        session.revoked_at = timezone.now()
        session.save(update_fields=["revoked_at"])
        record_security_event(
            session.request.owner, "emergency_session_revoked", "success",
            target_id=session.pk,
        )
    return session


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
