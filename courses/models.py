from django.conf import settings
from django.db import models
from django.urls import reverse

class HomePageSettings(models.Model):
    class Layout(models.TextChoices):
        SPLIT = "split", "Split hero (text beside illustration)"
        CENTERED = "centered", "Centered hero"
        ART_LEFT = "art_left", "Illustration on the left"
        TEXT_ONLY = "text_only", "Text only (hide illustration)"

    class SectionOrder(models.TextChoices):
        HERO_FIRST = "hero_first", "Welcome section before courses"
        COURSES_FIRST = "courses_first", "Courses before welcome section"

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    layout = models.CharField(max_length=16, choices=Layout.choices, default=Layout.SPLIT)
    section_order = models.CharField(max_length=16, choices=SectionOrder.choices, default=SectionOrder.HERO_FIRST)
    brand_name = models.CharField(max_length=80, default="learnwell")
    brand_tagline = models.CharField(max_length=100, default="selfstudyzone")
    footer_text = models.CharField(max_length=180, default="Make room for what’s next.")
    nav_explore = models.CharField(max_length=50, default="Explore")
    nav_learning = models.CharField(max_length=50, default="My learning")
    nav_teaching = models.CharField(max_length=50, default="Teaching")
    nav_parent = models.CharField(max_length=50, default="Parent space")
    nav_profile = models.CharField(max_length=50, default="Profile")
    nav_students = models.CharField(max_length=50, default="Students")
    nav_admin = models.CharField(max_length=50, default="Admin")
    nav_login = models.CharField(max_length=50, default="Log in")
    nav_signup = models.CharField(max_length=50, default="Get started")
    nav_logout = models.CharField(max_length=50, default="Log out")
    hero_eyebrow = models.CharField(max_length=100, default="YOUR NEXT CHAPTER STARTS HERE")
    hero_title = models.CharField(max_length=120, default="Learn something")
    hero_highlight = models.CharField(max_length=120, default="that moves you.")
    hero_description = models.CharField(max_length=300, default="Expert-led courses to help you build useful skills, one lesson at a time.")
    search_placeholder = models.CharField(max_length=120, default="What would you like to learn?")
    search_button = models.CharField(max_length=60, default="Find a course")
    illustration_text = models.CharField(max_length=100, default="MAKE IT HAPPEN")
    illustration_caption = models.CharField(max_length=120, default="Small steps. Big ideas.")
    library_eyebrow = models.CharField(max_length=100, default="THE COURSE LIBRARY")
    library_title = models.CharField(max_length=140, default="Find your kind of learning")
    lesson_label = models.CharField(max_length=40, default="lessons")
    previous_page_label = models.CharField(max_length=40, default="Previous")
    next_page_label = models.CharField(max_length=40, default="Next")
    empty_title = models.CharField(max_length=160, default="Your next favorite course is on its way.")
    empty_text = models.CharField(max_length=240, default="Try a different search, or check back soon.")

    class Meta:
        verbose_name = "Home page settings"
        verbose_name_plural = "Home page settings"

    def __str__(self):
        return "Home page settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        TEACHER = "teacher", "Teacher"
        PARENT = "parent", "Parent"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)
    avatar = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class StudentDetails(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="student_details")
    student_name = models.CharField(max_length=160, blank=True)
    father_name = models.CharField(max_length=160, blank=True)
    mother_name = models.CharField(max_length=160, blank=True)
    school_name = models.CharField(max_length=200, blank=True)
    class_name = models.CharField(max_length=40, blank=True)
    roll_number = models.CharField(max_length=40, blank=True)
    block = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return self.student_name

class TeacherDetails(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="teacher_details")
    subject = models.CharField(max_length=240, blank=True)
    school_name = models.CharField(max_length=200, blank=True)
    school_address = models.TextField(blank=True)
    is_private_tutor = models.BooleanField(default=False)
    mobile_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    block = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.profile.user.username} — {self.subject}"

class ParentDetails(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="parent_details")
    parent_name = models.CharField(max_length=160, blank=True)
    address = models.TextField(blank=True)
    mobile_number = models.CharField(max_length=30, blank=True)
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

class ParentWatchlist(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    parent = models.ForeignKey(ParentDetails, on_delete=models.CASCADE, related_name="watchlist")
    student = models.ForeignKey(StudentDetails, on_delete=models.CASCADE, related_name="parent_requests")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_parent_links")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["parent", "student"], name="unique_parent_student_watchlist")]
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.parent.parent_name} → {self.student.student_name} ({self.get_status_display()})"

class ExamResult(models.Model):
    student = models.ForeignKey(StudentDetails, on_delete=models.CASCADE, related_name="exam_results")
    exam_name = models.CharField(max_length=160)
    marks_obtained = models.DecimalField(max_digits=7, decimal_places=2)
    maximum_marks = models.DecimalField(max_digits=7, decimal_places=2)
    passed = models.BooleanField(default=False)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recorded_exam_results")
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.student.student_name}: {self.exam_name}"

class HomeworkStatus(models.Model):
    student = models.ForeignKey(StudentDetails, on_delete=models.CASCADE, related_name="homework_statuses")
    title = models.CharField(max_length=180)
    is_done = models.BooleanField(default=False)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recorded_homework_statuses")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title}: {self.student.student_name}"

class StudyTime(models.Model):
    student = models.OneToOneField(StudentDetails, on_delete=models.CASCADE, related_name="study_time")
    seconds = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_minutes(self):
        return self.seconds // 60

class Subscription(models.Model):
    class Plan(models.TextChoices):
        FREE = "free", "Free"
        PAID = "paid", "Paid"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING = "pending", "Upgrade requested"

    student = models.OneToOneField(StudentDetails, on_delete=models.CASCADE, related_name="subscription")
    plan = models.CharField(max_length=8, choices=Plan.choices, default=Plan.FREE)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    requested_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.student_name}: {self.get_plan_display()} ({self.get_status_display()})"

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
