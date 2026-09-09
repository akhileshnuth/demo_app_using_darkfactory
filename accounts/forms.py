"""Forms for registration, admin user management, and profile editing."""

from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password

from .models import Profile, User


class SignUpForm(forms.Form):
    """Registration form: email + password, creates the user (FR-001).

    A plain ``Form`` (not a ModelForm) so that password-strength errors
    (FR-008) attach to the ``password1`` field and render inline (FR-012).
    """

    email = forms.EmailField(
        label="Email address",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Password confirmation",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "A user with this email address already exists."
            )
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password:
            validate_password(password)
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self):
        """Create the user and their profile row, returning the user."""
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )
        Profile.objects.get_or_create(user=user)
        return user


class CustomUserCreationForm(UserCreationForm):
    """Admin add-user form keyed on email instead of username."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    """Admin change-user form keyed on email instead of username."""

    class Meta:
        model = User
        fields = ("email", "display_name")


class ProfileForm(forms.ModelForm):
    """Edit the authenticated user's display name (FR-005).

    ``required=True`` rejects blank/whitespace-only submissions (with
    ``strip=True``, whitespace collapses to an empty value, which triggers
    the required-field error inline beside the field).
    """

    display_name = forms.CharField(
        label="Display name",
        max_length=80,
        strip=True,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Your display name"}),
    )

    class Meta:
        model = User
        fields = ("display_name",)