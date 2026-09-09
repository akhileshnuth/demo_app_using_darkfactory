"""URL configuration for the checklists app.

Covers the checklists, sharing, emergency-access and notifications surfaces per
the DFT-9 web contracts. All routes require authentication (enforced in views).
"""

from django.urls import path

from . import views

urlpatterns = [
    # Personal checklists
    path("checklists/", views.ChecklistListView.as_view(), name="checklist_list"),
    path("checklists/new/", views.ChecklistCreateView.as_view(), name="checklist_new"),
    path(
        "checklists/shared/",
        views.SharedChecklistListView.as_view(),
        name="checklist_shared",
    ),
    path(
        "checklists/<int:pk>/",
        views.ChecklistDetailView.as_view(),
        name="checklist_detail",
    ),
    path(
        "checklists/<int:pk>/items/",
        views.ChecklistItemCreateView.as_view(),
        name="checklist_item_create",
    ),
    path(
        "checklists/<int:pk>/items/<int:item_id>/toggle/",
        views.ChecklistItemToggleView.as_view(),
        name="checklist_item_toggle",
    ),
    path(
        "checklists/<int:pk>/items/<int:item_id>/edit/",
        views.ChecklistItemEditView.as_view(),
        name="checklist_item_edit",
    ),
    path(
        "checklists/<int:pk>/items/<int:item_id>/delete/",
        views.ChecklistItemDeleteView.as_view(),
        name="checklist_item_delete",
    ),
    path(
        "checklists/<int:pk>/delete/",
        views.ChecklistDeleteView.as_view(),
        name="checklist_delete",
    ),
    # Sharing
    path(
        "checklists/<int:pk>/share/",
        views.ShareView.as_view(),
        name="checklist_share",
    ),
    path(
        "checklists/<int:pk>/share/<int:share_id>/revoke/",
        views.RevokeShareView.as_view(),
        name="checklist_share_revoke",
    ),
    # Emergency access
    path("emergency/", views.EmergencyHomeView.as_view(), name="emergency"),
    path(
        "emergency/<int:pk>/remove/",
        views.EmergencyContactRemoveView.as_view(),
        name="emergency_contact_remove",
    ),
    path(
        "emergency/request/",
        views.EmergencyRequestView.as_view(),
        name="emergency_request",
    ),
    path(
        "emergency/request/<int:owner_id>/",
        views.EmergencyRequestCreateView.as_view(),
        name="emergency_request_create",
    ),
    path(
        "emergency/request/<int:pk>/respond/",
        views.EmergencyRespondView.as_view(),
        name="emergency_respond",
    ),
    path(
        "emergency/request/<int:pk>/approve/",
        views.ApproveEmergencyRequestView.as_view(),
        name="emergency_approve",
    ),
    path(
        "emergency/request/<int:pk>/deny/",
        views.DenyEmergencyRequestView.as_view(),
        name="emergency_deny",
    ),
    # Notifications
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path(
        "notifications/<int:pk>/read/",
        views.NotificationReadView.as_view(),
        name="notification_read",
    ),
    path(
        "notifications/read-all/",
        views.NotificationReadAllView.as_view(),
        name="notification_read_all",
    ),
    path(
        "notifications/clear/",
        views.NotificationClearView.as_view(),
        name="notification_clear",
    ),
]
