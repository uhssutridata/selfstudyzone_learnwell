from django.urls import path
from . import views

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course-list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("courses/<slug:slug>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("courses/<slug:slug>/enroll/", views.enroll, name="enroll"),
    path("courses/<slug:slug>/lessons/<int:lesson_id>/", views.lesson_detail, name="lesson-detail"),
    path("courses/<slug:slug>/lessons/<int:lesson_id>/complete/", views.complete_lesson, name="complete-lesson"),
    path("signup/", views.signup, name="signup"),
    path("signup/username-suggestion/", views.username_suggestion, name="username-suggestion"),
]
