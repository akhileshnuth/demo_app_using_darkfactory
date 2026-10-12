"""Views for registration, login, profile editing, and the activity log."""

from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, UpdateView

from .forms import ProfileForm, SignUpForm, TwoFactorCodeForm
from .models import ActivityLog, TwoFactorAuth
from .services import complete_enrollment, start_enrollment, verify_login_factor

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
        user = form.get_user()
        if TwoFactorAuth.objects.filter(user=user, enabled=True).exists():
            self.request.session["two_factor_login_user"] = user.pk
            self.request.session["two_factor_login_backend"] = user.backend
            self.request.session.set_expiry(300)
            return redirect("two_factor_login")
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


class TwoFactorEnrollView(LoginRequiredMixin, FormView):
    template_name = "registration/two_factor_enroll.html"
    form_class = TwoFactorCodeForm
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            enrollment, uri = start_enrollment(request.user)
            request.session["two_factor_enrollment"] = enrollment.pk
            request.session["two_factor_uri"] = uri
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["provisioning_uri"] = self.request.session.get("two_factor_uri", "")
        return context

    def form_valid(self, form):
        from .models import TwoFactorEnrollment

        enrollment = TwoFactorEnrollment.objects.filter(pk=self.request.session.get("two_factor_enrollment")).first()
        result = complete_enrollment(self.request.user, enrollment, form.cleaned_data["code"]) if enrollment else False
        if not result:
            form.add_error(None, "That verification code is invalid or expired. Please try again.")
            return self.form_invalid(form)
        self.request.session.pop("two_factor_enrollment", None)
        self.request.session.pop("two_factor_uri", None)
        return render(self.request, "registration/two_factor_backup.html", {"backup_codes": result})


class TwoFactorLoginView(FormView):
    template_name = "registration/two_factor_login.html"
    form_class = TwoFactorCodeForm

    def form_valid(self, form):
        user_id = self.request.session.get("two_factor_login_user")
        user = User.objects.filter(pk=user_id).first()
        if not user or not verify_login_factor(user, form.cleaned_data["code"]):
            form.add_error(None, "The verification code is invalid. Try again or use a backup code.")
            return self.form_invalid(form)
        login(self.request, user, backend=self.request.session.pop("two_factor_login_backend", None))
        self.request.session.pop("two_factor_login_user", None)
        return redirect("dashboard")

    def get_success_url(self):
        return reverse_lazy("dashboard")
