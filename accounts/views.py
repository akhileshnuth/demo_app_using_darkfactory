"""Views for registration, login, and profile editing."""

from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView

from .forms import ProfileForm, SignUpForm

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