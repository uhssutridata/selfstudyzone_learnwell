from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView
from .forms import RoleAuthenticationForm, SignUpForm
from .models import Course, Enrollment, Lesson, LessonProgress, UserProfile


class RoleLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = RoleAuthenticationForm

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
        return render(request, "courses/dashboard.html", {"role": profile.role, "cards": []})
    enrollments = Enrollment.objects.filter(student=request.user).select_related("course", "course__instructor").prefetch_related("progress", "course__lessons")
    cards = []
    for enrollment in enrollments:
        total = enrollment.course.lessons.count()
        done = enrollment.progress.count()
        cards.append({"enrollment": enrollment, "total": total, "done": done, "percent": round(done * 100 / total) if total else 0})
    return render(request, "courses/dashboard.html", {"role": profile.role, "cards": cards})

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
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})
