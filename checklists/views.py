"""Views for checklists, sharing, emergency access and notifications.

All feature endpoints require authentication (FR-019) via ``LoginRequiredMixin``.
Resource access is gated by ``services.can_view``/``can_edit``/``can_respond_to_request``
(FR-020, SC-006): a user who cannot view a checklist gets a 404 rather than data
leakage.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.db import models
from django.urls import reverse
from django.views.generic import (
    DetailView,
    FormView,
    ListView,
    TemplateView,
    View,
)

from . import services
from .forms import (
    ChecklistForm,
    ChecklistItemForm,
    EmergencyContactForm,
    ShareForm,
)
from .models import (
    Checklist,
    ChecklistItem,
    ChecklistShare,
    EmergencyAccessRequest,
    EmergencyContact,
    Notification,
)


def _checklist_or_404_view(user, pk):
    """Fetch a checklist only if the user may view it; else 404 (SC-006)."""
    checklist = get_object_or_404(Checklist, pk=pk)
    if not services.can_view(user, checklist):
        raise PermissionDenied
    return checklist


class ChecklistListView(LoginRequiredMixin, ListView):
    """The user's own checklists (FR-001)."""

    model = Checklist
    template_name = "checklists/checklist_list.html"
    context_object_name = "checklists"
    paginate_by = 20

    def get_queryset(self):
        return Checklist.objects.filter(owner=self.request.user)


class ChecklistCreateView(LoginRequiredMixin, FormView):
    """Create a new checklist, optionally from a template (FR-002/017)."""

    form_class = ChecklistForm
    template_name = "checklists/checklist_form.html"

    def get_success_url(self):
        return reverse("checklist_detail", args=[self.object.pk])

    def form_valid(self, form):
        title = form.cleaned_data["title"]
        checklist = Checklist.objects.create(owner=self.request.user, title=title)
        template_name = form.cleaned_data.get("template")
        if template_name:
            from django.conf import settings

            items = getattr(settings, "CLA_OK_TEMPLATES", {}).get(template_name, [])
            position = 0
            for text in items:
                ChecklistItem.objects.create(
                    checklist=checklist, text=text, position=position
                )
                position += 1
        self.object = checklist
        messages.success(self.request, "Checklist created.")
        return super().form_valid(form)


class _ChecklistOwnerMixin:
    """Resolve a checklist the current user owns, else 404 (FR-020)."""

    def _get_owned_checklist(self, pk):
        return get_object_or_404(Checklist, pk=pk, owner=self.request.user)


class ChecklistDetailView(LoginRequiredMixin, DetailView):
    """Show a checklist's items and completion stats (FR-001/003/004)."""

    model = Checklist
    template_name = "checklists/checklist_detail.html"
    context_object_name = "checklist"

    def get_object(self, queryset=None):
        return _checklist_or_404_view(self.request.user, self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checklist = self.object
        context["is_owner"] = services.can_edit(self.request.user, checklist)
        context["item_form"] = ChecklistItemForm()
        if not context["is_owner"]:
            context["shared_by"] = checklist.owner.display_name or checklist.owner.email
        return context


class ChecklistItemCreateView(LoginRequiredMixin, _ChecklistOwnerMixin, View):
    """Add an item to a checklist (FR-003 acceptance 2). Edit access required."""

    def post(self, request, pk):
        checklist = self._get_owned_checklist(pk)
        form = ChecklistItemForm(request.POST)
        if form.is_valid():
            position = (
                checklist.items.aggregate(max_pos=models.Max("position"))[
                    "max_pos"
                ]
                or 0
            ) + 1
            ChecklistItem.objects.create(
                checklist=checklist,
                text=form.cleaned_data["text"],
                position=position,
            )
        else:
            messages.error(
                self.request,
                "Item text is required (200 characters max).",
            )
        return redirect("checklist_detail", pk=checklist.pk)


class ChecklistItemToggleView(LoginRequiredMixin, _ChecklistOwnerMixin, View):
    """Toggle an item's completion status (FR-003 acceptance 3/4). Edit access."""

    def post(self, request, pk, item_id):
        checklist = self._get_owned_checklist(pk)
        item = get_object_or_404(ChecklistItem, pk=item_id, checklist=checklist)
        item.is_complete = not item.is_complete
        item.save(update_fields=["is_complete"])
        return redirect("checklist_detail", pk=checklist.pk)


class ChecklistItemEditView(LoginRequiredMixin, _ChecklistOwnerMixin, View):
    """Edit an item's text (FR-003 acceptance 5). Edit access."""

    def post(self, request, pk, item_id):
        checklist = self._get_owned_checklist(pk)
        item = get_object_or_404(ChecklistItem, pk=item_id, checklist=checklist)
        form = ChecklistItemForm(request.POST)
        if form.is_valid():
            item.text = form.cleaned_data["text"]
            item.save(update_fields=["text"])
        else:
            messages.error(
                self.request,
                "Item text is required (200 characters max).",
            )
        return redirect("checklist_detail", pk=checklist.pk)


class ChecklistItemDeleteView(LoginRequiredMixin, _ChecklistOwnerMixin, View):
    """Delete an item (FR-003 acceptance 6). Edit access."""

    def post(self, request, pk, item_id):
        checklist = self._get_owned_checklist(pk)
        item = get_object_or_404(ChecklistItem, pk=item_id, checklist=checklist)
        item.delete()
        return redirect("checklist_detail", pk=checklist.pk)


class ChecklistDeleteView(LoginRequiredMixin, _ChecklistOwnerMixin, View):
    """Confirm-then-delete an entire checklist (FR-003 acceptance 7)."""

    def get(self, request, pk):
        checklist = self._get_owned_checklist(pk)
        return self._render_confirm(checklist)

    def post(self, request, pk):
        checklist = self._get_owned_checklist(pk)
        checklist.delete()
        messages.success(self.request, "Checklist deleted.")
        return redirect("checklist_list")

    def _render_confirm(self, checklist):
        from django.shortcuts import render

        return render(
            self.request,
            "checklists/checklist_confirm_delete.html",
            {"checklist": checklist},
        )


class ShareView(LoginRequiredMixin, _ChecklistOwnerMixin, FormView):
    """Share a checklist with a registered user and list current recipients.

    Owner-only (FR-005/006/008).
    """

    form_class = ShareForm
    template_name = "checklists/share_form.html"

    def _owned_checklist(self):
        return self._get_owned_checklist(self.kwargs["pk"])

    def get_success_url(self):
        return reverse("checklist_share", args=[self.kwargs["pk"]])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checklist = self._owned_checklist()
        context["checklist"] = checklist
        context["shares"] = checklist.shares.all()
        return context

    def form_valid(self, form):
        checklist = self._owned_checklist()
        recipient = form.recipient
        if recipient == self.request.user:
            messages.error(self.request, "You cannot share a checklist with yourself.")
            return redirect("checklist_share", pk=checklist.pk)
        share, created = services.share_checklist(checklist, recipient)
        if not created:
            messages.info(self.request, "Already shared with this user.")
        else:
            messages.success(self.request, f"Shared with {recipient.email}.")
        return super().form_valid(form)


class RevokeShareView(LoginRequiredMixin, _ChecklistOwnerMixin, View):
    """Revoke sharing for a recipient (FR-008)."""

    def post(self, request, pk, share_id):
        checklist = self._get_owned_checklist(pk)
        share = get_object_or_404(ChecklistShare, pk=share_id, checklist=checklist)
        services.revoke_share(share)
        messages.success(self.request, "Sharing revoked.")
        return redirect("checklist_share", pk=checklist.pk)


class SharedChecklistListView(LoginRequiredMixin, TemplateView):
    """Checklists shared *with* this user, labelled \"Shared by [owner]\".

    Includes active shares and emergency grants, all read-only (FR-005 acceptance 3).
    """

    template_name = "checklists/checklist_shared_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        shared_via_share = Checklist.objects.filter(
            shares__recipient=user,
            shares__status=ChecklistShare.STATUS_ACTIVE,
        ).distinct()

        granted_owners = EmergencyAccessRequest.objects.filter(
            requester=user,
            status__in=services.EMERGENCY_VIEWER_STATUSES,
        ).values_list("owner_id", flat=True)
        shared_via_emergency = Checklist.objects.filter(owner_id__in=granted_owners)

        combined_ids = (
            set(shared_via_share.values_list("id", flat=True))
            | set(shared_via_emergency.values_list("id", flat=True))
        )
        shared = Checklist.objects.filter(id__in=combined_ids)
        context["shared"] = shared
        return context


class EmergencyHomeView(LoginRequiredMixin, FormView):
    """The owner's emergency-contact management page (FR-009 acceptance 1)."""

    form_class = EmergencyContactForm
    template_name = "checklists/emergency_contacts.html"

    def get_success_url(self):
        return reverse("emergency")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contacts"] = EmergencyContact.objects.filter(
            owner=self.request.user
        )
        return context

    def form_valid(self, form):
        contact = form.contact
        if contact == self.request.user:
            messages.error(self.request, "You cannot designate yourself as an emergency contact.")
            return redirect("emergency")
        if EmergencyContact.objects.filter(
            owner=self.request.user, contact=contact
        ).exists():
            messages.info(self.request, "Already an emergency contact.")
            return redirect("emergency")
        EmergencyContact.objects.create(owner=self.request.user, contact=contact)
        messages.success(self.request, f"Added {contact.email} as an emergency contact.")
        return super().form_valid(form)


class EmergencyContactRemoveView(LoginRequiredMixin, View):
    """Remove an emergency contact, cancelling/revoking their access (acceptance 6)."""

    def post(self, request, pk):
        contact = get_object_or_404(
            EmergencyContact, pk=pk, owner=request.user
        )
        services.remove_emergency_contact(contact)
        messages.success(self.request, "Emergency contact removed.")
        return redirect("emergency")


class EmergencyRequestView(LoginRequiredMixin, TemplateView):
    """The contact's emergency-access page (viewer/contact side)."""

    template_name = "checklists/emergency_request.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        contexts = []
        for ec in EmergencyContact.objects.filter(contact=user):
            request_obj = (
                EmergencyAccessRequest.objects.filter(owner=ec.owner, requester=user)
                .order_by("-requested_at")
                .first()
            )
            status = None
            if request_obj is not None:
                if request_obj.status == EmergencyAccessRequest.STATUS_PENDING:
                    # Lazy auto-grant on read (FR-011/SC-003).
                    services._auto_grant_if_expired(request_obj)
                status = request_obj.status
            contexts.append(
                {
                    "contact": ec,
                    "owner": ec.owner,
                    "request": request_obj,
                    "status": status,
                }
            )
        context["contexts"] = contexts
        return context


class EmergencyRequestCreateView(LoginRequiredMixin, View):
    """Request emergency access from an owner (contact side, FR-010)."""

    def post(self, request, owner_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        owner = get_object_or_404(User, pk=owner_id)
        created = services.request_emergency_access(request.user, owner)
        if created is None:
            raise PermissionDenied
        return redirect("emergency_request")


class EmergencyRespondView(LoginRequiredMixin, TemplateView):
    """Owner's response page for a specific request (approve/deny)."""

    template_name = "checklists/emergency_respond.html"

    def _get_request(self):
        request_obj = get_object_or_404(
            EmergencyAccessRequest, pk=self.kwargs["pk"]
        )
        if not services.can_respond_to_request(self.request.user, request_obj):
            raise PermissionDenied
        return request_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_obj = self._get_request()
        services._auto_grant_if_expired(request_obj)
        context["emergency_request"] = request_obj
        return context


class ApproveEmergencyRequestView(LoginRequiredMixin, View):
    """Approve an emergency access request (FR-013 acceptance 3)."""

    def post(self, request, pk):
        request_obj = get_object_or_404(EmergencyAccessRequest, pk=pk)
        if not services.can_respond_to_request(self.request.user, request_obj):
            raise PermissionDenied
        if not services.approve_emergency_request(request_obj):
            messages.info(self.request, "This request has already been resolved.")
        return redirect("emergency_respond", pk=request_obj.pk)


class DenyEmergencyRequestView(LoginRequiredMixin, View):
    """Deny an emergency access request (FR-013 acceptance 4)."""

    def post(self, request, pk):
        request_obj = get_object_or_404(EmergencyAccessRequest, pk=pk)
        if not services.can_respond_to_request(self.request.user, request_obj):
            raise PermissionDenied
        if not services.deny_emergency_request(request_obj):
            messages.info(self.request, "This request has already been resolved.")
        return redirect("emergency_respond", pk=request_obj.pk)


class NotificationListView(LoginRequiredMixin, ListView):
    """The notification center (FR-014 acceptance 1/2)."""

    model = Notification
    template_name = "checklists/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 50

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationReadView(LoginRequiredMixin, View):
    """Mark one notification read (FR-015 acceptance 3)."""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, recipient=request.user
        )
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        target = request.POST.get("next")
        if target and target.startswith("/") and not target.startswith("//"):
            return HttpResponseRedirect(target)
        return redirect("notifications")


class NotificationReadAllView(LoginRequiredMixin, View):
    """Mark all notifications read (acceptance 4)."""

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        return redirect("notifications")


class NotificationClearView(LoginRequiredMixin, View):
    """Clear all notifications (acceptance 5)."""

    def post(self, request):
        Notification.objects.filter(recipient=request.user).delete()
        return redirect("notifications")
