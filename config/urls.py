"""Root URL configuration for the scaffold project.

Routes are defined with explicit paths so ``accounts`` owns the
authentication and profile surface (``/accounts/signup/``,
``/accounts/login/``, ``/accounts/logout/``, ``/profile/``) and
``dashboard`` owns the authenticated dashboard shell (``/dashboard/``).
``checklists`` owns the DFT-9 checklists, sharing, emergency-access and
notification surfaces (``/checklists/``, ``/emergency/``, ``/notifications/``).
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("dashboard.urls")),
    path("", include("checklists.urls")),
]