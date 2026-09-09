"""URL configuration for the accounts app.

Routes are defined with explicit paths so the authentication surface
(``/accounts/signup/``, ``/accounts/login/``, ``/accounts/logout/``) and the
profile page (``/profile/``) both live here, matching the web contracts.
"""

from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("accounts/signup/", views.SignUpView.as_view(), name="signup"),
    path("accounts/login/", views.LoginView.as_view(), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]