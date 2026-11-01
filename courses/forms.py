from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=UserProfile.Role.choices,
        label="I’m joining as a",
        widget=forms.Select(attrs={"class": "role-select"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "role")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.update_or_create(user=user, defaults={"role": self.cleaned_data["role"]})
        return user


class RoleAuthenticationForm(AuthenticationForm):
    role = forms.ChoiceField(
        choices=UserProfile.Role.choices,
        label="I’m logging in as a",
        widget=forms.Select(attrs={"class": "role-select"}),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.role != self.cleaned_data["role"]:
            raise forms.ValidationError(
                "That account is registered as a %(role)s. Choose the matching account type.",
                code="role_mismatch",
                params={"role": profile.get_role_display().lower()},
            )
