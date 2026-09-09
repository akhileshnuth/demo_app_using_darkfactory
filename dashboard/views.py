"""Views for the dashboard shell."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    """Authenticated dashboard shell (FR-006).

    Unauthenticated requests are redirected to ``/accounts/login/?next=/dashboard/``
    by ``LoginRequiredMixin`` (FR-007, SC-003).
    """

    template_name = "dashboard/dashboard.html"