from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
import re
import secrets
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .forms import ExamResultForm, HomeworkEvaluationForm, HomeworkSubmissionForm, HomeworkStatusForm, LessonHomeworkForm, LessonQuizForm, ParentProfileForm, ParentRegistrationForm, RoleAuthenticationForm, StudentProfileForm, StudentRegistrationForm, StudentSearchForm, TeacherAssistedStudentForm, TeacherProfileForm, TeacherRegistrationForm
from .models import Course, Enrollment, HomePageFeedback, HomePageNotice, HomePagePerformanceHighlight, HomeworkSubmission, Lesson, LessonProgress, LessonQuizAttempt, ParentDetails, ParentWatchlist, StudyTime, StudentDetails, Subscription, TeacherDetails, TeacherStudentApproval, UserProfile


def _student_class_key(user):
    details = StudentDetails.objects.filter(profile__user=user).only("class_name").first()
    if not details or not details.class_name:
        return ""
    value = details.class_name.strip().lower().replace("_", " ")
    value = re.sub(r"^(class|grade|standard|std)\s*", "", value)
    value = re.sub(r"\s*(class|grade|standard|std)$", "", value)
    value = re.sub(r"^(\d+)(st|nd|rd|th)$", r"\1", value.strip())
    roman_levels = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10", "xi": "11", "xii": "12"}
    if value in roman_levels:
        return roman_levels[value]
    if value in {"pre primary", "nursery", "kindergarten", "kg", "lkg", "ukg"}:
        return "pre_primary"
    if value.isdigit() and 1 <= int(value) <= 12:
        return str(int(value))
    return ""


class RoleLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = RoleAuthenticationForm

    def get_initial(self):
        initial = super().get_initial()
        role = self.request.GET.get("role", "")
        if role in UserProfile.Role.values:
            initial["role"] = role
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")
        role = (form.data.get("role") if form and form.is_bound else "") or self.request.GET.get("role", "")
        context["selected_role"] = role if role in UserProfile.Role.values else ""
        context["role_label"] = UserProfile.Role(context["selected_role"]).label if context["selected_role"] else ""
        return context

class CourseListView(ListView):
    model = Course
    template_name = "courses/course_list.html"
    context_object_name = "courses"
    paginate_by = 9

    def get_queryset(self):
        qs = Course.objects.filter(published=True).select_related("instructor")
        if not self.request.user.is_authenticated or not UserProfile.objects.filter(user=self.request.user, role=UserProfile.Role.STUDENT).exists():
            return qs.none()
        class_key = _student_class_key(self.request.user)
        qs = qs.filter(class_name=class_key) if class_key else qs.none()
        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(subtitle__icontains=query) | Q(description__icontains=query) | Q(instructor__username__icontains=query))
        if category:
            qs = qs.filter(category__iexact=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["categories"] = self.get_queryset().values_list("category", flat=True).distinct()
        ctx["selected_category"] = self.request.GET.get("category", "")
        ctx["student_course_access"] = bool(
            self.request.user.is_authenticated
            and UserProfile.objects.filter(user=self.request.user, role=UserProfile.Role.STUDENT).exists()
            and _student_class_key(self.request.user)
        )
        ctx["home_notices"] = HomePageNotice.objects.filter(is_active=True)[:4]
        ctx["performance_highlights"] = HomePagePerformanceHighlight.objects.filter(is_published=True)
        published_feedback = HomePageFeedback.objects.filter(is_published=True)
        ctx["home_feedback_slots"] = [
            {
                "role": role,
                "role_label": label,
                "feedback": published_feedback.filter(role=role).first(),
            }
            for role, label in UserProfile.Role.choices
        ]
        return ctx

class CourseDetailView(DetailView):
    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        queryset = Course.objects.filter(published=True).select_related("instructor").prefetch_related("lessons")
        if not self.request.user.is_authenticated or not UserProfile.objects.filter(user=self.request.user, role=UserProfile.Role.STUDENT).exists():
            return queryset.none()
        class_key = _student_class_key(self.request.user)
        return queryset.filter(class_name=class_key) if class_key else queryset.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["enrollment"] = Enrollment.objects.filter(student=self.request.user, course=self.object).first() if self.request.user.is_authenticated else None
        return ctx

@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.role == UserProfile.Role.TEACHER:
        authorized_students = _teacher_student_queryset(request.user)
        pending_homework = HomeworkSubmission.objects.filter(student__in=authorized_students, evaluated_at__isnull=True).count()
        return render(request, "courses/dashboard.html", {"role": profile.role, "pending_homework": pending_homework})
    if profile.role == UserProfile.Role.PARENT:
        parent = ParentDetails.objects.filter(profile=profile).prefetch_related("children").first()
        watchlist = ParentWatchlist.objects.filter(parent=parent).select_related("student", "student__profile__user", "student__study_time").prefetch_related("student__exam_results", "student__homework_statuses") if parent else []
        return render(request, "courses/dashboard.html", {"role": profile.role, "cards": [], "parent_details": parent, "watchlist": watchlist})
    class_key = _student_class_key(request.user)
    if class_key:
        class_courses = Course.objects.filter(published=True, class_name=class_key)
        for course in class_courses:
            Enrollment.objects.get_or_create(student=request.user, course=course)
        enrollments = Enrollment.objects.filter(student=request.user, course__published=True, course__class_name=class_key).select_related("course", "course__instructor").prefetch_related("progress", "course__lessons")
    else:
        enrollments = Enrollment.objects.none()
    cards = []
    for enrollment in enrollments:
        course_lessons = list(enrollment.course.lessons.all())
        completed_ids = {progress.lesson_id for progress in enrollment.progress.all()}
        done = len(completed_ids)
        lessons = [{"lesson": lesson, "completed": lesson.id in completed_ids} for lesson in course_lessons]
        total = len(course_lessons)
        cards.append({"enrollment": enrollment, "lessons": lessons, "total": total, "done": done, "percent": round(done * 100 / total) if total else 0})
    student_details = StudentDetails.objects.filter(profile=profile).first()
    subscription = Subscription.objects.get_or_create(student=student_details)[0] if student_details else None
    return render(request, "courses/dashboard.html", {"role": profile.role, "cards": cards, "subscription": subscription, "student_class_label": dict(Course.CLASS_LEVELS).get(class_key, "Unassigned")})


@login_required
@require_POST
def request_subscription_upgrade(request):
    if not _has_role(request, UserProfile.Role.STUDENT):
        return HttpResponseForbidden("Student accounts only.")
    student = get_object_or_404(StudentDetails, profile__user=request.user)
    subscription, _ = Subscription.objects.get_or_create(student=student)
    if subscription.plan == Subscription.Plan.PAID and subscription.status == Subscription.Status.ACTIVE:
        messages.info(request, "Your paid subscription is already active.")
    elif subscription.status != Subscription.Status.PENDING:
        subscription.status = Subscription.Status.PENDING
        subscription.requested_at = timezone.now()
        subscription.save(update_fields=["status", "requested_at", "updated_at"])
        messages.success(request, "Your paid subscription request was sent. It will be activated after an administrator confirms payment.")
    else:
        messages.info(request, "Your paid subscription request is already awaiting review.")
    return redirect("dashboard")


@login_required
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    details = None
    watchlist = []
    if user_profile.role == UserProfile.Role.STUDENT:
        details = StudentDetails.objects.filter(profile=user_profile).first()
    elif user_profile.role == UserProfile.Role.TEACHER:
        details = TeacherDetails.objects.filter(profile=user_profile).first()
    elif user_profile.role == UserProfile.Role.PARENT:
        details = ParentDetails.objects.filter(profile=user_profile).first()
        if details:
            watchlist = ParentWatchlist.objects.filter(parent=details).select_related("student").order_by("-requested_at")
    return render(request, "courses/profile.html", {"profile": user_profile, "details": details, "watchlist": watchlist})


@login_required
def profile_edit(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    details_models = {
        UserProfile.Role.STUDENT: (StudentDetails, StudentProfileForm),
        UserProfile.Role.TEACHER: (TeacherDetails, TeacherProfileForm),
        UserProfile.Role.PARENT: (ParentDetails, ParentProfileForm),
    }
    model, form_class = details_models[user_profile.role]
    details, _ = model.objects.get_or_create(profile=user_profile)
    form = form_class(request.POST or None, request.FILES or None, instance=details)
    if request.method == "POST" and form.is_valid():
        updated = form.save()
        form.save_avatar(user_profile)
        request.user.email = form.cleaned_data.get("email", "").strip()
        user_fields = ["email"]
        if user_profile.role == UserProfile.Role.TEACHER:
            request.user.first_name = form.cleaned_data.get("full_name", "").strip()
            request.user.last_name = ""
            user_fields.extend(["first_name", "last_name"])
            if form.verification_details_changed():
                updated.is_verified = False
                updated.save(update_fields=["is_verified"])
        request.user.save(update_fields=user_fields)
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")
    return render(request, "courses/profile_edit.html", {"profile": user_profile, "details": details, "form": form})

@login_required
def enroll(request, slug):
    if request.method == "POST":
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if profile.role != UserProfile.Role.STUDENT:
            messages.error(request, "Only student accounts can enroll in courses.")
            return redirect("dashboard")
        course = get_object_or_404(Course, slug=slug, published=True)
        if course.class_name != _student_class_key(request.user):
            return HttpResponseForbidden("This course is for a different class.")
        Enrollment.objects.get_or_create(student=request.user, course=course)
        messages.success(request, f"You’re enrolled in {course.title}.")
        return redirect("dashboard")
    return redirect("course-detail", slug=slug)

@login_required
def lesson_detail(request, slug, lesson_id):
    enrollment = get_object_or_404(Enrollment, student=request.user, course__slug=slug, course__published=True, course__class_name=_student_class_key(request.user))
    lesson = get_object_or_404(Lesson, id=lesson_id, course=enrollment.course)
    completed = enrollment.progress.filter(lesson=lesson).exists()
    questions = list(lesson.questions.all())
    quiz_form = LessonQuizForm(request.POST if request.method == "POST" else None, questions=questions) if questions else None
    if request.method == "POST" and quiz_form and quiz_form.is_valid():
        answers = {str(question.pk): quiz_form.cleaned_data[f"question_{question.pk}"] for question in questions}
        score = sum(answers[str(question.pk)] == question.correct_option for question in questions)
        LessonQuizAttempt.objects.create(student=request.user, lesson=lesson, score=score, total_questions=len(questions), answers=answers)
        messages.success(request, f"Quiz submitted: {score} out of {len(questions)} correct.")
        return redirect("lesson-detail", slug=slug, lesson_id=lesson.id)
    latest_attempt = LessonQuizAttempt.objects.filter(student=request.user, lesson=lesson).first()
    quiz_results = []
    if latest_attempt:
        for question in questions:
            answer = latest_attempt.answers.get(str(question.pk), "")
            quiz_results.append({"question": question, "answer": answer, "correct": answer == question.correct_option})
    homework_form = LessonHomeworkForm()
    submissions = HomeworkSubmission.objects.filter(student__profile__user=request.user, lesson=lesson)
    return render(request, "courses/lesson_detail.html", {"course": enrollment.course, "lesson": lesson, "completed": completed, "quiz_form": quiz_form, "quiz_results": quiz_results, "latest_attempt": latest_attempt, "homework_form": homework_form, "homework_submissions": submissions})


@login_required
@require_POST
def submit_lesson_homework(request, slug, lesson_id):
    if not _has_role(request, UserProfile.Role.STUDENT):
        return HttpResponseForbidden("Student accounts only.")
    enrollment = get_object_or_404(Enrollment, student=request.user, course__slug=slug, course__published=True, course__class_name=_student_class_key(request.user))
    lesson = get_object_or_404(Lesson, id=lesson_id, course=enrollment.course)
    if not lesson.homework_description.strip():
        messages.error(request, "This lesson does not have homework assigned.")
        return redirect("lesson-detail", slug=slug, lesson_id=lesson_id)
    form = LessonHomeworkForm(request.POST, request.FILES)
    if form.is_valid():
        submission = form.save(commit=False)
        submission.student = get_object_or_404(StudentDetails, profile__user=request.user)
        submission.lesson = lesson
        submission.title = f"{lesson.title} — Homework"
        submission.save()
        messages.success(request, "Homework uploaded for review by your authorized teacher.")
    else:
        messages.error(request, "Please choose a homework file and try again.")
    return redirect("lesson-detail", slug=slug, lesson_id=lesson_id)

@login_required
def complete_lesson(request, slug, lesson_id):
    if request.method == "POST":
        enrollment = get_object_or_404(Enrollment, student=request.user, course__slug=slug, course__class_name=_student_class_key(request.user))
        lesson = get_object_or_404(Lesson, id=lesson_id, course=enrollment.course)
        LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        messages.success(request, "Lesson marked complete.")
        return redirect("lesson-detail", slug=slug, lesson_id=lesson_id)
    return redirect("dashboard")

def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    forms_by_role = {
        UserProfile.Role.STUDENT: StudentRegistrationForm,
        UserProfile.Role.TEACHER: TeacherRegistrationForm,
        UserProfile.Role.PARENT: ParentRegistrationForm,
    }
    role = request.POST.get("role") or request.GET.get("role", "")
    form_class = forms_by_role.get(role)
    form = form_class(request.POST or None) if form_class else None
    if request.method == "POST" and form and form.is_valid():
        user = form.save()
        login(request, user)
        if role == UserProfile.Role.PARENT and form.cleaned_data.get("parent_name"):
            return redirect("parent-watchlist")
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form, "selected_role": role, "role_label": UserProfile.Role(role).label if role in forms_by_role else ""})


@require_GET
def username_suggestion(request):
    parts = [request.GET.get(key, "").strip() for key in ("name", "block", "district")]
    if not parts[0]:
        return JsonResponse({"username": ""})
    base = slugify("-".join(part for part in parts if part))[:140].strip("-")
    if not base:
        return JsonResponse({"username": ""})
    candidate = base
    serial = 2
    while User.objects.filter(username__iexact=candidate).exists():
        suffix = f"-{serial}"
        candidate = f"{base[:150 - len(suffix)]}{suffix}"
        serial += 1
    return JsonResponse({"username": candidate})


def _has_role(request, role, verified_teacher=False):
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile or profile.role != role:
        return False
    if verified_teacher:
        return TeacherDetails.objects.filter(profile=profile, is_verified=True).exists()
    return True


def _teacher_student_queryset(user):
    return StudentDetails.objects.filter(
        Q(registered_by=user) | Q(teacher_approvals__teacher=user)
    ).distinct()


@login_required
def parent_watchlist(request):
    if not _has_role(request, UserProfile.Role.PARENT):
        return HttpResponseForbidden("This page is for parent accounts.")
    parent = get_object_or_404(ParentDetails, profile__user=request.user)
    search_form = StudentSearchForm(request.GET or None)
    results = StudentDetails.objects.none()
    if search_form.is_valid():
        query = search_form.cleaned_data["q"].strip()
        if len(query) >= 3 and parent.parent_name:
            results = StudentDetails.objects.filter(
                student_name__icontains=query,
            ).filter(
                Q(father_name__iexact=parent.parent_name) | Q(mother_name__iexact=parent.parent_name),
            ).select_related("profile__user").order_by("student_name")[:15]
    if request.method == "POST":
        student = get_object_or_404(StudentDetails, pk=request.POST.get("student_id"))
        request_obj, created = ParentWatchlist.objects.get_or_create(parent=parent, student=student)
        if request_obj.status == ParentWatchlist.Status.REJECTED:
            request_obj.status = ParentWatchlist.Status.PENDING
            request_obj.reviewed_by = None
            request_obj.reviewed_at = None
            request_obj.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        messages.success(request, "Student added to your request list. A school administrator must approve access before records are shown.")
        return redirect("dashboard")
    return render(request, "courses/parent_watchlist.html", {"parent": parent, "search_form": search_form, "results": results, "requested_ids": set(parent.watchlist.values_list("student_id", flat=True))})


@login_required
def teacher_students(request):
    if not _has_role(request, UserProfile.Role.TEACHER):
        return HttpResponseForbidden("Teacher student search is available after an administrator verifies your teacher account.")
    if not _has_role(request, UserProfile.Role.TEACHER, verified_teacher=True):
        return render(request, "courses/teacher_students.html", {"teacher_verified": False}, status=403)
    teacher = get_object_or_404(TeacherDetails, profile__user=request.user, is_verified=True)
    student_form = TeacherAssistedStudentForm(request.POST or None)
    if request.method == "POST" and student_form.is_valid():
        student_name = student_form.cleaned_data["student_name"].strip()
        username_base = slugify("-".join((student_name, student_form.cleaned_data["block"], student_form.cleaned_data["district"])))[:150].strip("-") or "student"
        username = username_base
        serial = 2
        while User.objects.filter(username__iexact=username).exists():
            suffix = f"-{serial}"
            username = f"{username_base[:150 - len(suffix)]}{suffix}"
            serial += 1
        password = secrets.token_urlsafe(18)
        with transaction.atomic():
            student_user = User.objects.create_user(username=username, password=password, first_name=student_name)
            student_profile = UserProfile.objects.create(user=student_user, role=UserProfile.Role.STUDENT)
            student_details = student_form.save(commit=False)
            student_details.profile = student_profile
            student_details.registered_by = request.user
            student_details.save()
        request.session["teacher_student_credentials"] = {"name": student_name, "username": username, "password": password}
        messages.success(request, f"{student_name} was registered successfully. Share the login details below with the student.")
        return redirect("teacher-students")
    form = StudentSearchForm(request.GET if "q" in request.GET else None)
    students = _teacher_student_queryset(request.user).select_related("profile__user").prefetch_related("homework_submissions").order_by("student_name")
    if form.is_bound:
        if form.is_valid():
            query = form.cleaned_data["q"].strip()
            students = students.filter(student_name__icontains=query) if len(query) >= 3 else students.none()
        else:
            students = students.none()
    credentials = request.session.pop("teacher_student_credentials", None)
    return render(request, "courses/teacher_students.html", {"form": form, "students": students, "student_form": student_form, "new_student_credentials": credentials, "teacher_verified": True})


@login_required
def teacher_student_detail(request, student_id):
    if not _has_role(request, UserProfile.Role.TEACHER, verified_teacher=True):
        return HttpResponseForbidden("Teacher student records require a verified teacher account.")
    teacher = get_object_or_404(TeacherDetails, profile__user=request.user, is_verified=True)
    permitted_students = _teacher_student_queryset(request.user).select_related("profile__user")
    student = get_object_or_404(permitted_students, pk=student_id)
    submissions = HomeworkSubmission.objects.filter(student=student).select_related("evaluated_by")
    if request.method == "POST":
        submission_id = request.POST.get("submission_id")
        submission = get_object_or_404(submissions, pk=submission_id) if submission_id else None
        if submission is None:
            return HttpResponseForbidden("Select a submitted homework to evaluate.")
        evaluation_form = HomeworkEvaluationForm(request.POST, instance=submission)
        if evaluation_form.is_valid():
            evaluated = evaluation_form.save(commit=False)
            evaluated.evaluated_by = request.user
            evaluated.evaluated_at = timezone.now()
            evaluated.save(update_fields=["teacher_feedback", "evaluated_by", "evaluated_at"])
            messages.success(request, "Homework feedback saved.")
            return redirect("teacher-student-detail", student_id=student.id)
    else:
        evaluation_form = HomeworkEvaluationForm()
    return render(request, "courses/teacher_student_detail.html", {"student": student, "submissions": submissions, "evaluation_form": evaluation_form})


@login_required
def student_homework(request):
    if not _has_role(request, UserProfile.Role.STUDENT):
        return HttpResponseForbidden("Student accounts only.")
    student = get_object_or_404(StudentDetails, profile__user=request.user)
    form = HomeworkSubmissionForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        submission = form.save(commit=False)
        submission.student = student
        submission.save()
        messages.success(request, "Your homework was uploaded for teacher review.")
        return redirect("student-homework")
    submissions = HomeworkSubmission.objects.filter(student=student).select_related("evaluated_by")
    return render(request, "courses/student_homework.html", {"form": form, "submissions": submissions})


@login_required
@require_POST
def track_study_time(request):
    if not _has_role(request, UserProfile.Role.STUDENT):
        return JsonResponse({"error": "Student accounts only."}, status=403)
    try:
        seconds = int(request.POST.get("seconds", "0"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid duration."}, status=400)
    if seconds < 1 or seconds > 300:
        return JsonResponse({"error": "Duration must be between 1 and 300 seconds."}, status=400)
    student = get_object_or_404(StudentDetails, profile__user=request.user)
    StudyTime.objects.get_or_create(student=student)
    StudyTime.objects.filter(student=student).update(seconds=F("seconds") + seconds, updated_at=timezone.now())
    return JsonResponse({"saved": seconds})
