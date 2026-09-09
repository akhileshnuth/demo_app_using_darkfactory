"""Custom password validation for the accounts app (FR-008)."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    """Reject passwords under 8 chars or missing a digit or special char.

    Registered in ``AUTH_PASSWORD_VALIDATORS`` so it applies to the signup
    form, admin user creation, and any other code path that runs
    ``validate_password`` (R6).
    """

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _(
                    "This password is too short. It must contain at least "
                    "%(min_length)d characters."
                ),
                code="password_too_short",
                params={"min_length": self.min_length},
            )
        if not re.search(r"\d", password):
            raise ValidationError(
                _("This password must contain at least one digit."),
                code="password_no_digit",
            )
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(
                _("This password must contain at least one special character."),
                code="password_no_special_character",
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_length)d characters, "
            "including at least one digit and one special character."
        ) % {"min_length": self.min_length}