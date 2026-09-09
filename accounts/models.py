"""User and Profile models for the accounts app.

The custom ``User`` extends ``AbstractUser`` keyed on email (FR-002,
FR-004, FR-009); ``Profile`` is the one-to-one extension entity the spec's
Key Entities describe, holding future-scaffold data and delegating the
display name to the user account (R3).
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager for the email-keyed custom User model."""

    use_in_migrations = True

    def normalize_email(self, email):
        """Normalize by lowercasing the entire address (R8)."""
        email = super().normalize_email(email)
        return email.lower() if email else email

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """A registered account identified by email (FR-004)."""

    username = None
    email = models.EmailField("email address", unique=True, max_length=254)
    display_name = models.CharField(
        "display name", max_length=80, blank=True, default=""
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email


class Profile(models.Model):
    """One-to-one profile data extending the user account (Key Entities)."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    avatar_url = models.URLField(
        "avatar URL", max_length=200, blank=True, default=""
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__email"]

    def __str__(self):
        return f"Profile for {self.user.email}"

    @property
    def display_name(self):
        """Read-only display name, delegated to the user account (R3)."""
        return self.user.display_name