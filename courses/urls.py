from django.urls import path
from . import views

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course-list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("subscription/request-upgrade/", views.request_subscription_upgrade, name="request-subscription-upgrade"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile-edit"),
    path("parents/watchlist/", views.parent_watchlist, name="parent-watchlist"),
    path("teachers/students/", views.teacher_students, name="teacher-students"),
    path("teachers/students/<int:student_id>/", views.teacher_student_detail, name="teacher-student-detail"),
    path("activity/study-time/", views.track_study_time, name="track-study-time"),
    path("courses/<slug:slug>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("courses/<slug:slug>/enroll/", views.enroll, name="enroll"),
    path("courses/<slug:slug>/lessons/<int:lesson_id>/", views.lesson_detail, name="lesson-detail"),
    path("courses/<slug:slug>/lessons/<int:lesson_id>/complete/", views.complete_lesson, name="complete-lesson"),
    path("signup/", views.signup, name="signup"),
    path("signup/username-suggestion/", views.username_suggestion, name="username-suggestion"),
]
