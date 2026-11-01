from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.db.models import F, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .forms import ExamResultForm, HomeworkStatusForm, ParentProfileForm, ParentRegistrationForm, RoleAuthenticationForm, StudentProfileForm, StudentRegistrationForm, StudentSearchForm, TeacherProfileForm, TeacherRegistrationForm
from .models import Course, Enrollment, HomePageFeedback, HomePageNotice, HomePagePerformanceHighlight, Lesson, LessonProgress, ParentDetails, ParentWatchlist, StudyTime, StudentDetails, Subscription, TeacherDetails, UserProfile


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
        ctx["categories"] = Course.objects.filter(published=True).values_list("category", flat=True).distinct()
        ctx["selected_category"] = self.request.GET.get("category", "")
        ctx["home_notices"] = HomePageNotice.objects.filter(is_active=True)[:4]
        ctx["performance_highlights"] = HomePagePerformanceHighlight.objects.filter(is_published=True)[:3]
        ctx["home_feedback"] = HomePageFeedback.objects.filter(is_published=True)[:6]
        return ctx

class CourseDetailView(DetailView):
    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Course.objects.filter(published=True).select_related("instructor").prefetch_related("lessons")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["enrollment"] = Enrollment.objects.filter(student=self.request.user, course=self.object).first() if self.request.user.is_authenticated else None
        return ctx

@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.role == UserProfile.Role.TEACHER:
        courses = Course.objects.filter(instructor=request.user).prefetch_related("lessons")
        return render(request, "courses/dashboard.html", {"role": profile.role, "teacher_courses": courses})
    if profile.role == UserProfile.Role.PARENT:
        parent = ParentDetails.objects.filter(profile=profile).prefetch_related("children").first()
        watchlist = ParentWatchlist.objects.filter(parent=parent).select_related("student", "student__profile__user", "student__study_time").prefetch_related("student__exam_results", "student__homework_statuses") if parent else []
        return render(request, "courses/dashboard.html", {"role": profile.role, "cards": [], "parent_details": parent, "watchlist": watchlist})
    enrollments = Enrollment.objects.filter(student=request.user).select_related("course", "course__instructor").prefetch_related("progress", "course__lessons")
    cards = []
    for enrollment in enrollments:
        total = enrollment.course.lessons.count()
        done = enrollment.progress.count()
        cards.append({"enrollment": enrollment, "total": total, "done": done, "percent": round(done * 100 / total) if total else 0})
    student_details = StudentDetails.objects.filter(profile=profile).first()
    subscription = Subscription.objects.get_or_create(student=student_details)[0] if student_details else None
    return render(request, "courses/dashboard.html", {"role": profile.role, "cards": cards, "subscription": subscription})


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
        if user_profile.role == UserProfile.Role.TEACHER:
            request.user.first_name = form.cleaned_data.get("full_name", "").strip()
            request.user.save(update_fields=["first_name"])
            if form.verification_details_changed():
                updated.is_verified = False
                updated.save(update_fields=["is_verified"])
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
        Enrollment.objects.get_or_create(student=request.user, course=course)
        messages.success(request, f"You’re enrolled in {course.title}.")
        return redirect("dashboard")
    return redirect("course-detail", slug=slug)

@login_required
def lesson_detail(request, slug, lesson_id):
    enrollment = get_object_or_404(Enrollment, student=request.user, course__slug=slug, course__published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=enrollment.course)
    completed = enrollment.progress.filter(lesson=lesson).exists()
    return render(request, "courses/lesson_detail.html", {"course": enrollment.course, "lesson": lesson, "completed": completed})

@login_required
def complete_lesson(request, slug, lesson_id):
    if request.method == "POST":
        enrollment = get_object_or_404(Enrollment, student=request.user, course__slug=slug)
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
    if not _has_role(request, UserProfile.Role.TEACHER, verified_teacher=True):
        return HttpResponseForbidden("Teacher student search is available after an administrator verifies your teacher account.")
    teacher = get_object_or_404(TeacherDetails, profile__user=request.user, is_verified=True)
    form = StudentSearchForm(request.GET or None)
    students = StudentDetails.objects.none()
    if form.is_valid():
        query = form.cleaned_data["q"].strip()
        if len(query) >= 3:
            students = StudentDetails.objects.filter(student_name__icontains=query)
            if not teacher.is_private_tutor and not request.user.is_staff:
                students = students.filter(school_name__iexact=teacher.school_name)
            students = students.select_related("profile__user").order_by("student_name")[:30]
    return render(request, "courses/teacher_students.html", {"form": form, "students": students})


@login_required
def teacher_student_detail(request, student_id):
    if not _has_role(request, UserProfile.Role.TEACHER, verified_teacher=True):
        return HttpResponseForbidden("Teacher student records require a verified teacher account.")
    teacher = get_object_or_404(TeacherDetails, profile__user=request.user, is_verified=True)
    permitted_students = StudentDetails.objects.select_related("profile__user")
    if not teacher.is_private_tutor and not request.user.is_staff:
        permitted_students = permitted_students.filter(school_name__iexact=teacher.school_name)
    student = get_object_or_404(permitted_students, pk=student_id)
    exam_form = ExamResultForm(request.POST if request.method == "POST" and request.POST.get("record_type") == "exam" else None)
    homework_form = HomeworkStatusForm(request.POST if request.method == "POST" and request.POST.get("record_type") == "homework" else None)
    if request.method == "POST" and request.POST.get("record_type") == "exam" and exam_form.is_valid():
        exam = exam_form.save(commit=False)
        exam.student = student
        exam.recorded_by = request.user
        exam.save()
        messages.success(request, "Exam result saved.")
        return redirect("teacher-student-detail", student_id=student.id)
    if request.method == "POST" and request.POST.get("record_type") == "homework" and homework_form.is_valid():
        homework = homework_form.save(commit=False)
        homework.student = student
        homework.recorded_by = request.user
        homework.save()
        messages.success(request, "Homework status saved.")
        return redirect("teacher-student-detail", student_id=student.id)
    return render(request, "courses/teacher_student_detail.html", {"student": student, "exam_form": exam_form, "homework_form": homework_form})


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
