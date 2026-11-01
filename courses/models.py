from django.conf import settings
from django.db import models
from django.urls import reverse

class UserProfile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        TEACHER = "teacher", "Teacher"
        PARENT = "parent", "Parent"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class StudentDetails(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="student_details")
    student_name = models.CharField(max_length=160)
    father_name = models.CharField(max_length=160)
    mother_name = models.CharField(max_length=160)
    school_name = models.CharField(max_length=200)
    class_name = models.CharField(max_length=40)
    roll_number = models.CharField(max_length=40)
    block = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    state = models.CharField(max_length=120)

    def __str__(self):
        return self.student_name

class TeacherDetails(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="teacher_details")
    subject = models.CharField(max_length=160)
    school_name = models.CharField(max_length=200, blank=True)
    school_address = models.TextField(blank=True)
    is_private_tutor = models.BooleanField(default=False)
    mobile_number = models.CharField(max_length=30)
    email = models.EmailField()
    block = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"{self.profile.user.username} — {self.subject}"

class ParentDetails(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="parent_details")
    parent_name = models.CharField(max_length=160)
    address = models.TextField()
    mobile_number = models.CharField(max_length=30)
    block = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return self.parent_name

class ParentChild(models.Model):
    parent = models.ForeignKey(ParentDetails, on_delete=models.CASCADE, related_name="children")
    name = models.CharField(max_length=160)
    class_name = models.CharField(max_length=40)

    def __str__(self):
        return f"{self.name} — {self.class_name}"

class Course(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    subtitle = models.CharField(max_length=240, blank=True)
    description = models.TextField()
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    category = models.CharField(max_length=80, default="General")
    level = models.CharField(max_length=20, choices=[("Beginner", "Beginner"), ("Intermediate", "Intermediate"), ("Advanced", "Advanced")], default="Beginner")
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("course-detail", kwargs={"slug": self.slug})

    @property
    def learner_count(self):
        return self.enrollments.count()

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=180)
    content = models.TextField(help_text="Lesson notes. You can include links to video or resources.")
    position = models.PositiveIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["position", "id"]
        unique_together = ["course", "position"]

    def __str__(self):
        return f"{self.course.title}: {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="unique_student_course")]

    def __str__(self):
        return f"{self.student} → {self.course}"

class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="completions")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["enrollment", "lesson"], name="unique_lesson_completion")]
