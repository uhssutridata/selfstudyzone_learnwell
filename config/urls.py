from django.contrib import admin
from django.urls import include, path
from courses.views import RoleLoginView

urlpatterns = [path("admin/", admin.site.urls), path("accounts/login/", RoleLoginView.as_view(), name="login"), path("accounts/", include("django.contrib.auth.urls")), path("", include("courses.urls"))]
