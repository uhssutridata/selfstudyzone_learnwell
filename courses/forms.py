import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import ParentChild, ParentDetails, StudentDetails, TeacherDetails, UserProfile


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def save_profile(self, user, role):
        return UserProfile.objects.create(user=user, role=role)


class StudentRegistrationForm(RegistrationForm):
    student_name = forms.CharField(max_length=160, label="Student name")
    father_name = forms.CharField(max_length=160, label="Father’s name")
    mother_name = forms.CharField(max_length=160, label="Mother’s name")
    school_name = forms.CharField(max_length=200, label="School name")
    class_name = forms.CharField(max_length=40, label="Class")
    roll_number = forms.CharField(max_length=40, label="Roll number")
    block = forms.CharField(max_length=120)
    district = forms.CharField(max_length=120)
    state = forms.CharField(max_length=120)

    class Meta(RegistrationForm.Meta):
        fields = ("username", "student_name", "father_name", "mother_name", "school_name", "class_name", "roll_number", "block", "district", "state")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = self.save_profile(user, UserProfile.Role.STUDENT)
            StudentDetails.objects.create(profile=profile, **{key: self.cleaned_data[key] for key in (
                "student_name", "father_name", "mother_name", "school_name", "class_name", "roll_number", "block", "district", "state"
            )})
        return user


class TeacherRegistrationForm(RegistrationForm):
    subject = forms.CharField(max_length=160, label="Subject(s) you teach")
    is_private_tutor = forms.BooleanField(required=False, label="I am a private tutor")
    school_name = forms.CharField(max_length=200, required=False, label="School name where you teach")
    school_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="School address")
    mobile_number = forms.CharField(max_length=30, label="Mobile number")
    email = forms.EmailField(label="Email address")

    class Meta(RegistrationForm.Meta):
        fields = ("username", "subject", "is_private_tutor", "school_name", "school_address", "mobile_number", "email")

    def clean_mobile_number(self):
        value = self.cleaned_data["mobile_number"].strip()
        if not re.fullmatch(r"[+()\-\d\s]{7,20}", value):
            raise forms.ValidationError("Enter a valid mobile number.")
        return value

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("is_private_tutor"):
            if not cleaned.get("school_name"):
                self.add_error("school_name", "Enter your school name, or select private tutor.")
            if not cleaned.get("school_address"):
                self.add_error("school_address", "Enter your school address, or select private tutor.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = self.save_profile(user, UserProfile.Role.TEACHER)
            user.email = self.cleaned_data["email"]
            user.save(update_fields=["email"])
            TeacherDetails.objects.create(profile=profile, **{key: self.cleaned_data[key] for key in (
                "subject", "school_name", "school_address", "is_private_tutor", "mobile_number", "email"
            )})
        return user


class ParentRegistrationForm(RegistrationForm):
    parent_name = forms.CharField(max_length=160, label="Your name")
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="Your address")
    mobile_number = forms.CharField(max_length=30, label="Mobile number")
    children = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Example: Asha Kumar, Class 6"}),
        label="Children’s names and classes",
        help_text="Enter one child per line as: Name, Class",
    )

    class Meta(RegistrationForm.Meta):
        fields = ("username", "parent_name", "address", "mobile_number", "children")

    def clean_mobile_number(self):
        value = self.cleaned_data["mobile_number"].strip()
        if not re.fullmatch(r"[+()\-\d\s]{7,20}", value):
            raise forms.ValidationError("Enter a valid mobile number.")
        return value

    def clean_children(self):
        value = self.cleaned_data["children"]
        rows = []
        for line in value.splitlines():
            if not line.strip():
                continue
            if "," not in line:
                raise forms.ValidationError("Use one line per child, with a comma between their name and class.")
            name, class_name = (part.strip() for part in line.split(",", 1))
            if not name or not class_name:
                raise forms.ValidationError("Include both a child’s name and class on every line.")
            rows.append((name, class_name))
        if not rows:
            raise forms.ValidationError("Enter at least one child’s name and class.")
        return rows

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = self.save_profile(user, UserProfile.Role.PARENT)
            parent = ParentDetails.objects.create(profile=profile, parent_name=self.cleaned_data["parent_name"], address=self.cleaned_data["address"], mobile_number=self.cleaned_data["mobile_number"])
            ParentChild.objects.bulk_create([ParentChild(parent=parent, name=name, class_name=class_name) for name, class_name in self.cleaned_data["children"]])
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
