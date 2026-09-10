"""Admin registrations for the checklists app.

Dev convenience only — the admin is not part of this ticket's web contract.
"""

from django.contrib import admin

from .models import (
    Checklist,
    ChecklistItem,
    ChecklistShare,
    EmergencyAccessRequest,
    EmergencyContact,
    Notification,
)


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "created_at", "updated_at")
    search_fields = ("title", "owner__email")


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("checklist", "text", "is_complete", "position")
    list_filter = ("is_complete",)


@admin.register(ChecklistShare)
class ChecklistShareAdmin(admin.ModelAdmin):
    list_display = ("checklist", "recipient", "status", "shared_at")
    list_filter = ("status",)


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("owner", "contact", "designated_at")


@admin.register(EmergencyAccessRequest)
class EmergencyAccessRequestAdmin(admin.ModelAdmin):
    list_display = ("owner", "requester", "status", "requested_at", "resolved_at")
    list_filter = ("status",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "type", "message", "is_read", "created_at")
    list_filter = ("type", "is_read")
