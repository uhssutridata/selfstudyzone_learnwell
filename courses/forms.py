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
    student_name = forms.CharField(max_length=160, label="Student name", required=False)
    father_name = forms.CharField(max_length=160, label="Father’s name", required=False)
    mother_name = forms.CharField(max_length=160, label="Mother’s name", required=False)
    school_name = forms.CharField(max_length=200, label="School name", required=False)
    class_name = forms.CharField(max_length=40, label="Class", required=False)
    roll_number = forms.CharField(max_length=40, label="Roll number", required=False)
    block = forms.CharField(max_length=120, required=False)
    district = forms.CharField(max_length=120, required=False)
    state = forms.CharField(max_length=120, required=False)

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
    full_name = forms.CharField(max_length=160, label="Your name", required=False)
    block = forms.CharField(max_length=120, required=False, label="Block (optional)")
    district = forms.CharField(max_length=120, required=False, label="District (optional)")
    state = forms.CharField(max_length=120, required=False, label="State (optional)")
    subjects = forms.MultipleChoiceField(
        choices=TEACHING_SUBJECTS,
        widget=CheckboxSelectMultiple,
        label="Select the subjects you teach",
        required=False,
    )
    other_subject = forms.CharField(max_length=160, required=False, label="Other subject (if applicable)")
    is_private_tutor = forms.BooleanField(required=False, label="I am a private tutor")
    school_name = forms.CharField(max_length=200, required=False, label="School name where you teach")
    school_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False, label="School address")
    mobile_number = forms.CharField(max_length=30, label="Mobile number", required=False)
    email = forms.EmailField(label="Email address", required=False)

    class Meta(RegistrationForm.Meta):
        fields = ("full_name", "username", "subjects", "other_subject", "is_private_tutor", "school_name", "school_address", "mobile_number", "email", "block", "district", "state")

    def clean(self):
        return super().clean()

    def clean_mobile_number(self):
        value = self.cleaned_data.get("mobile_number", "").strip()
        if not value:
            return value
        if not re.fullmatch(r"[+()\-\d\s]{7,20}", value):
            raise forms.ValidationError("Enter a valid mobile number.")
        return value

    def clean(self):
        return super().clean()

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
    parent_name = forms.CharField(max_length=160, label="Your name", required=False)
    block = forms.CharField(max_length=120, required=False, label="Block (optional)")
    district = forms.CharField(max_length=120, required=False, label="District (optional)")
    state = forms.CharField(max_length=120, required=False, label="State (optional)")
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="Your address", required=False)
    mobile_number = forms.CharField(max_length=30, label="Mobile number", required=False)

    class Meta(RegistrationForm.Meta):
        fields = ("parent_name", "username", "address", "mobile_number", "block", "district", "state")

    def clean_mobile_number(self):
        value = self.cleaned_data.get("mobile_number", "").strip()
        if not value:
            return value
        if not re.fullmatch(r"[+()\-\d\s]{7,20}", value):
            raise forms.ValidationError("Enter a valid mobile number.")
        return value

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = self.save_profile(user, UserProfile.Role.PARENT)
            parent = ParentDetails.objects.create(profile=profile, parent_name=self.cleaned_data["parent_name"], address=self.cleaned_data["address"], mobile_number=self.cleaned_data["mobile_number"], block=self.cleaned_data["block"], district=self.cleaned_data["district"], state=self.cleaned_data["state"])
        return user


class ProfileAvatarMixin:
    def save_avatar(self, profile):
        if self.cleaned_data.get("avatar"):
            profile.avatar = self.cleaned_data["avatar"]
            profile.save(update_fields=["avatar"])


class StudentProfileForm(ProfileAvatarMixin, forms.ModelForm):
    avatar = forms.ImageField(required=False, label="Profile photo")
    class Meta:
        model = StudentDetails
        fields = ("student_name", "father_name", "mother_name", "school_name", "class_name", "roll_number", "block", "district", "state")


class TeacherProfileForm(ProfileAvatarMixin, forms.ModelForm):
    avatar = forms.ImageField(required=False, label="Profile photo")
    full_name = forms.CharField(max_length=160, required=False, label="Your name")
    subjects = forms.MultipleChoiceField(choices=TEACHING_SUBJECTS, widget=CheckboxSelectMultiple, required=False, label="Subjects you teach")
    other_subject = forms.CharField(max_length=160, required=False, label="Other subject")

    class Meta:
        model = TeacherDetails
        fields = ("school_name", "school_address", "is_private_tutor", "mobile_number", "email", "block", "district", "state")

    def verification_details_changed(self):
        return any(name in self.changed_data for name in ("school_name", "school_address", "is_private_tutor", "mobile_number", "email", "block", "district", "state"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.profile_id:
            self.fields["full_name"].initial = self.instance.profile.user.first_name
        if self.instance and self.instance.subject:
            current = {label: key for key, label in TEACHING_SUBJECTS}
            self.fields["subjects"].initial = [current[s.strip()] for s in self.instance.subject.split(",") if s.strip() in current]
            known = {label for _, label in TEACHING_SUBJECTS}
            self.fields["other_subject"].initial = ", ".join(s.strip() for s in self.instance.subject.split(",") if s.strip() not in known)

    def save(self, commit=True):
        instance = super().save(commit=False)
        labels = dict(TEACHING_SUBJECTS)
        selected = self.cleaned_data.get("subjects", [])
        subjects = [labels[item] for item in selected if item != "other"]
        if "other" in selected and self.cleaned_data.get("other_subject", "").strip():
            subjects.append(self.cleaned_data["other_subject"].strip())
        instance.subject = ", ".join(subjects)
        if commit:
            instance.save()
        return instance


class ParentProfileForm(ProfileAvatarMixin, forms.ModelForm):
    avatar = forms.ImageField(required=False, label="Profile photo")
    class Meta:
        model = ParentDetails
        fields = ("parent_name", "address", "mobile_number", "block", "district", "state")


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
