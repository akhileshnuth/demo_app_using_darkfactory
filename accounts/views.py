"""Views for registration, login, profile editing, and the activity log."""

from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, UpdateView

from .forms import ProfileForm, SignUpForm
from .models import ActivityLog

User = get_user_model()


class SignUpView(FormView):
    """Registration page: creates an account and logs the user in (FR-001)."""

    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class LoginView(AuthLoginView):
    """Login page using the email-based user model (FR-002)."""

    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        ActivityLog.objects.create(
            user=self.request.user,
            event_type=ActivityLog.EventType.LOGIN,
            description="Signed in.",
        )
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    """Display and edit the authenticated user's display name (FR-005).

    Unauthenticated requests are redirected to ``/accounts/login/?next=/profile/``
    by ``LoginRequiredMixin`` (FR-007). On success the page re-renders with
    the updated value visible in both the page and the dashboard header.
    """

    model = User
    form_class = ProfileForm
    template_name = "dashboard/profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.save()
        return self.render_to_response(self.get_context_data(form=form))


class ActivityView(LoginRequiredMixin, ListView):
    """The authenticated user's recent activity log (DFT-14).

    Lists the signed-in user's own security-relevant events (logins; share
    create/open/revoke; emergency access request/grant/deny) newest first.
    The queryset is scoped to ``request.user`` so a user never sees anyone
    else's activity.
    """

    model = ActivityLog
    template_name = "dashboard/activity.html"
    context_object_name = "activities"
    paginate_by = 50

    def get_queryset(self):
        return ActivityLog.objects.filter(user=self.request.user)