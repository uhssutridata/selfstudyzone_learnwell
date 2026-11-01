import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import CheckboxSelectMultiple

from .models import ExamResult, HomeworkStatus, ParentDetails, StudentDetails, TeacherDetails, UserProfile

TEACHING_SUBJECTS = [
    ("mathematics", "Mathematics"),
    ("science", "Science"),
    ("english", "English"),
    ("social_studies", "Social Studies"),
    ("hindi", "Hindi"),
    ("computer_science", "Computer Science"),
    ("art_design", "Art and Design"),
    ("business_economics", "Business and Economics"),
    ("other", "Other"),
]


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username"
        self.fields["username"].help_text = "Choose a suggestion below or enter your own."
        self.fields["username"].widget.attrs.update({"autocomplete": "username", "data-username-input": "true"})

    def save_profile(self, user, role):
        return UserProfile.objects.create(user=user, role=role)


class StudentRegistrationForm(RegistrationForm):
    student_name = forms.CharField(max_length=160, label="Student name")
    block = forms.CharField(max_length=120)
    district = forms.CharField(max_length=120)
    father_name = forms.CharField(max_length=160, label="Father’s name")
    mother_name = forms.CharField(max_length=160, label="Mother’s name")
    school_name = forms.CharField(max_length=200, label="School name")
    class_name = forms.CharField(max_length=40, label="Class")
    roll_number = forms.CharField(max_length=40, label="Roll number")
    block = forms.CharField(max_length=120)
    district = forms.CharField(max_length=120)
    state = forms.CharField(max_length=120)

    class Meta(RegistrationForm.Meta):
        fields = ("student_name", "username", "father_name", "mother_name", "school_name", "class_name", "roll_number", "block", "district", "state")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = self.save_profile(user, UserProfile.Role.STUDENT)
            StudentDetails.objects.create(profile=profile, **{key: self.cleaned_data[key] for key in (
                "student_name", "father_name", "mother_name", "school_name", "class_name", "roll_number", "block", "district", "state"
            )})
        return user


class TeacherRegistrationForm(RegistrationForm):
    full_name = forms.CharField(max_length=160, label="Your name")
    block = forms.CharField(max_length=120, required=False, label="Block (optional)")
    district = forms.CharField(max_length=120, required=False, label="District (optional)")
    state = forms.CharField(max_length=120, required=False, label="State (optional)")
    subjects = forms.MultipleChoiceField(
        choices=TEACHING_SUBJECTS,
        widget=CheckboxSelectMultiple,
        label="Select the subjects you teach",
        error_messages={"required": "Select at least one subject."},
    )
    other_subject = forms.CharField(max_length=160, required=False, label="Other subject (if applicable)")
    is_private_tutor = forms.BooleanField(required=False, label="I am a private tutor")
    school_name = forms.CharField(max_length=200, required=False, label="School name where you teach")
    school_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="School address")
    mobile_number = forms.CharField(max_length=30, label="Mobile number")
    email = forms.EmailField(label="Email address")

    class Meta(RegistrationForm.Meta):
        fields = ("full_name", "username", "subjects", "other_subject", "is_private_tutor", "school_name", "school_address", "mobile_number", "email", "block", "district", "state")

    def clean(self):
        cleaned = super().clean()
        if "other" in cleaned.get("subjects", []) and not cleaned.get("other_subject", "").strip():
            self.add_error("other_subject", "Enter the subject you selected as Other.")
        return cleaned

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
            user.first_name = self.cleaned_data["full_name"]
            user.save(update_fields=["email", "first_name"])
            labels = dict(TEACHING_SUBJECTS)
            subjects = [labels[value] for value in self.cleaned_data["subjects"] if value != "other"]
            if "other" in self.cleaned_data["subjects"]:
                subjects.append(self.cleaned_data["other_subject"].strip())
            TeacherDetails.objects.create(
                profile=profile,
                subject=", ".join(subjects),
                **{key: self.cleaned_data[key] for key in (
                    "school_name", "school_address", "is_private_tutor", "mobile_number", "email", "block", "district", "state"
                )},
            )
        return user


class ParentRegistrationForm(RegistrationForm):
    parent_name = forms.CharField(max_length=160, label="Your name")
    block = forms.CharField(max_length=120, required=False, label="Block (optional)")
    district = forms.CharField(max_length=120, required=False, label="District (optional)")
    state = forms.CharField(max_length=120, required=False, label="State (optional)")
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="Your address")
    mobile_number = forms.CharField(max_length=30, label="Mobile number")

    class Meta(RegistrationForm.Meta):
        fields = ("parent_name", "username", "address", "mobile_number", "block", "district", "state")

    def clean_mobile_number(self):
        value = self.cleaned_data["mobile_number"].strip()
        if not re.fullmatch(r"[+()\-\d\s]{7,20}", value):
            raise forms.ValidationError("Enter a valid mobile number.")
        return value

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = self.save_profile(user, UserProfile.Role.PARENT)
            parent = ParentDetails.objects.create(profile=profile, parent_name=self.cleaned_data["parent_name"], address=self.cleaned_data["address"], mobile_number=self.cleaned_data["mobile_number"], block=self.cleaned_data["block"], district=self.cleaned_data["district"], state=self.cleaned_data["state"])
        return user


class StudentSearchForm(forms.Form):
    q = forms.CharField(max_length=160, label="Student name", widget=forms.SearchInput(attrs={"placeholder": "Search by student name"}))


class ExamResultForm(forms.ModelForm):
    marks_obtained = forms.DecimalField(max_digits=7, decimal_places=2, min_value=0)
    maximum_marks = forms.DecimalField(max_digits=7, decimal_places=2, min_value=0.01)

    class Meta:
        model = ExamResult
        fields = ("exam_name", "marks_obtained", "maximum_marks", "passed")
        labels = {"passed": "Passed the exam"}

    def clean(self):
        cleaned = super().clean()
        obtained = cleaned.get("marks_obtained")
        maximum = cleaned.get("maximum_marks")
        if obtained is not None and maximum is not None and obtained > maximum:
            self.add_error("marks_obtained", "Marks obtained cannot exceed the maximum marks.")
        return cleaned


class HomeworkStatusForm(forms.ModelForm):
    class Meta:
        model = HomeworkStatus
        fields = ("title", "is_done")
        labels = {"is_done": "Homework completed"}


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
