"""Forms for checklists, sharing, and emergency-contacts surfaces.

Validation is server-side (FR-002, FR-003, FR-006, FR-009) and errors render
inline via Django's form machinery.
"""

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Checklist, ChecklistItem

User = get_user_model()


class ChecklistForm(forms.ModelForm):
    """Create/edit a checklist title, optionally from a quick-start template."""

    template = forms.ChoiceField(required=False)

    class Meta:
        model = Checklist
        fields = ["title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        template_choices = [("", "No template (start from scratch)")]
        template_choices += [
            (name, f"{name} ({len(items)} items)")
            for name, items in getattr(settings, "CLA_OK_TEMPLATES", {}).items()
        ]
        self.fields["template"].choices = template_choices

    def clean_template(self):
        value = self.cleaned_data.get("template")
        if not value:
            return ""
        templates = getattr(settings, "CLA_OK_TEMPLATES", {})
        if value not in templates:
            raise forms.ValidationError("Unknown template.")
        return value


class ChecklistItemForm(forms.ModelForm):
    """Add or edit an item's text (FR-003)."""

    class Meta:
        model = ChecklistItem
        fields = ["text"]


class ShareForm(forms.Form):
    """Share a checklist with a registered user by email (FR-005/006)."""

    email = forms.EmailField(max_length=254, label="Recipient email")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        self.recipient = User.objects.filter(email__iexact=email).first()
        if self.recipient is None:
            raise forms.ValidationError("No user with that email address.")
        return email


class EmergencyContactForm(forms.Form):
    """Designate an emergency contact by email (FR-009)."""

    email = forms.EmailField(max_length=254, label="Emergency contact email")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        self.contact = User.objects.filter(email__iexact=email).first()
        if self.contact is None:
            raise forms.ValidationError("No user with that email address.")
        return email
