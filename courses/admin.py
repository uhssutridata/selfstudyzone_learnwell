from django.contrib import admin
from .models import Course, Enrollment, Lesson, LessonProgress

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "category", "level", "published", "learner_count")
    list_filter = ("published", "level", "category")
    search_fields = ("title", "description", "instructor__username")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline]

admin.site.register(Enrollment)
admin.site.register(LessonProgress)
