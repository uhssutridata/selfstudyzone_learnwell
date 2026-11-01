from django.contrib import admin
from .models import Course, Enrollment, Lesson, LessonProgress, ParentChild, ParentDetails, StudentDetails, TeacherDetails, UserProfile

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
admin.site.register(UserProfile)
admin.site.register(StudentDetails)
admin.site.register(TeacherDetails)

class ParentChildInline(admin.TabularInline):
    model = ParentChild
    extra = 0

@admin.register(ParentDetails)
class ParentDetailsAdmin(admin.ModelAdmin):
    list_display = ("parent_name", "mobile_number", "profile")
    search_fields = ("parent_name", "mobile_number", "profile__user__username")
    inlines = [ParentChildInline]
