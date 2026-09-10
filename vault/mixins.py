"""Reusable mixins for the vault app views.

``OwnerQuerysetMixin`` scopes document querysets to the current user.
``ProtectedDeleteMixin`` blocks deletion of taxonomy entities that have
assigned documents.
"""

from django.contrib import messages
from django.db import ProtectedError
from django.shortcuts import redirect


class OwnerQuerysetMixin:
    """Filter the queryset to the current user's documents only (FR-012)."""

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class ProtectedDeleteMixin:
    """Block deletion when related objects prevent it (PROTECT FK).

    On ``ProtectedError`` the user is redirected back with an error message
    added to ``messages`` instead of the affected object being deleted.
    """

    protected_message = (
        "This item cannot be deleted because it is in use by existing documents."
    )

    def delete(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, self.protected_message)
            return redirect(self.get_success_url())
