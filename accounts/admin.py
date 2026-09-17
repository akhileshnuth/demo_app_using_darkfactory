"""Admin registrations for the accounts app.

Dev convenience only — the admin is not part of this ticket's web contract.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import ActivityLog, Profile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ("email", "display_name", "is_staff", "is_active")
    search_fields = ("email", "display_name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("display_name", "first_name", "last_name")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "created_at", "updated_at")
    readonly_fields = ("display_name",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Read-only view of the per-user activity trail (DFT-14)."""

    list_display = ("user", "event_type", "description", "created_at")
    list_filter = ("event_type",)
    search_fields = ("user__email", "description")
    readonly_fields = ("user", "event_type", "description", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False