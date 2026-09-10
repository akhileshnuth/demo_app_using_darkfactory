"""Context processors for the checklists app.

Adds the unread-notification count to every template context for the header
badge (FR-016, SC-007 / SC-008). Registered in
``config.settings.TEMPLATES.OPTIONS.context_processors``.
"""

from .services import unread_notification_count


def unread_notifications(request):
    """Unread notification count for the header badge (FR-016)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"unread_notifications": 0}
    return {"unread_notifications": unread_notification_count(user)}
