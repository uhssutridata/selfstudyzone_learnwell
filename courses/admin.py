from django.contrib import admin, messages
from django.utils import timezone
from .models import Course, Enrollment, ExamResult, HomePageFeedback, HomePageNotice, HomePagePerformanceHighlight, HomePageSettings, HomeworkStatus, Lesson, LessonProgress, ParentChild, ParentDetails, ParentWatchlist, StudentDetails, StudyTime, Subscription, TeacherDetails, UserProfile


@admin.register(HomePageSettings)
class HomePageSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Layout", {"fields": ("layout", "section_order")}),
        ("Branding", {"fields": ("brand_name", "brand_tagline", "footer_text")}),
        ("Navigation labels", {"fields": ("nav_explore", "nav_learning", "nav_teaching", "nav_parent", "nav_profile", "nav_students", "nav_admin", "nav_login", "nav_signup", "nav_logout")}),
        ("Welcome section", {"fields": ("hero_eyebrow", "hero_title", "hero_highlight", "hero_description", "search_placeholder", "search_button")}),
        ("Illustration", {"fields": ("illustration_text", "illustration_caption")}),
        ("Course library", {"fields": ("library_eyebrow", "library_title", "lesson_label", "previous_page_label", "next_page_label", "empty_title", "empty_text")}),
        ("Notices section", {"fields": ("notice_eyebrow", "notice_title", "notice_empty_text")}),
        ("Performance section", {"fields": ("performance_eyebrow", "performance_title", "performance_empty_text")}),
        ("Feedback section", {"fields": ("feedback_eyebrow", "feedback_title", "feedback_empty_text")}),
    )
    readonly_fields = ()

    def has_add_permission(self, request):
        return not HomePageSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HomePageNotice)
class HomePageNoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "published_at")
    list_filter = ("is_active", "published_at")
    search_fields = ("title", "message")
    list_editable = ("is_active",)


@admin.register(HomePagePerformanceHighlight)
class HomePagePerformanceHighlightAdmin(admin.ModelAdmin):
    list_display = ("title", "student_display_name", "metric_value", "is_published", "published_at")
    list_filter = ("is_published", "published_at")
    search_fields = ("title", "student_display_name", "description")
    list_editable = ("is_published",)
    fieldsets = (
        ("Highlight", {"fields": ("title", "description", "student_display_name", "class_label")}),
        ("Result shown on homepage", {"fields": ("metric_label", "metric_value", "is_published")}),
    )


@admin.register(HomePageFeedback)
class HomePageFeedbackAdmin(admin.ModelAdmin):
    list_display = ("display_name", "role", "is_published", "created_at")
    list_filter = ("role", "is_published", "created_at")
    search_fields = ("display_name", "quote")
    list_editable = ("is_published",)
    fieldsets = (
        ("Feedback shown on the homepage", {"fields": ("quote", "display_name", "role", "profile_picture", "is_published")}),
    )

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
@admin.register(StudentDetails)
class StudentDetailsAdmin(admin.ModelAdmin):
    list_display = ("student_name", "school_name", "class_name", "registered_by")
    list_filter = ("school_name", "class_name")
    search_fields = ("student_name", "father_name", "mother_name", "school_name", "registered_by__username")

@admin.register(TeacherDetails)
class TeacherDetailsAdmin(admin.ModelAdmin):
    list_display = ("profile", "subject", "school_name", "is_private_tutor", "is_verified")
    list_filter = ("is_verified", "is_private_tutor")
    actions = ("verify_teachers",)

    @admin.action(description="Verify selected teacher accounts")
    def verify_teachers(self, request, queryset):
        queryset.update(is_verified=True)

class ParentChildInline(admin.TabularInline):
    model = ParentChild
    extra = 0

@admin.register(ParentDetails)
class ParentDetailsAdmin(admin.ModelAdmin):
    list_display = ("parent_name", "mobile_number", "profile")
    search_fields = ("parent_name", "mobile_number", "profile__user__username")
    inlines = [ParentChildInline]

@admin.action(description="Approve selected parent watchlist requests")
def approve_parent_requests(modeladmin, request, queryset):
    queryset.update(status=ParentWatchlist.Status.APPROVED, reviewed_at=timezone.now(), reviewed_by=request.user)
    modeladmin.message_user(request, "Selected parent access requests approved.", messages.SUCCESS)

@admin.action(description="Reject selected parent watchlist requests")
def reject_parent_requests(modeladmin, request, queryset):
    queryset.update(status=ParentWatchlist.Status.REJECTED, reviewed_at=timezone.now(), reviewed_by=request.user)
    modeladmin.message_user(request, "Selected parent access requests rejected.", messages.SUCCESS)

@admin.register(ParentWatchlist)
class ParentWatchlistAdmin(admin.ModelAdmin):
    list_display = ("parent", "student", "status", "requested_at", "reviewed_by", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("parent__parent_name", "parent__profile__user__username", "student__student_name", "student__school_name")
    actions = (approve_parent_requests, reject_parent_requests)

admin.site.register(ExamResult)
admin.site.register(HomeworkStatus)
admin.site.register(StudyTime)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("student", "plan", "status", "requested_at", "activated_at", "updated_at")
    list_filter = ("plan", "status")
    search_fields = ("student__student_name", "student__profile__user__username", "student__school_name")
    actions = ("activate_paid_subscriptions", "return_to_free_plan")

    @admin.action(description="Confirm payment and activate paid subscription")
    def activate_paid_subscriptions(self, request, queryset):
        queryset.update(plan=Subscription.Plan.PAID, status=Subscription.Status.ACTIVE, activated_at=timezone.now())

    @admin.action(description="Return selected students to the free plan")
    def return_to_free_plan(self, request, queryset):
        queryset.update(plan=Subscription.Plan.FREE, status=Subscription.Status.ACTIVE, activated_at=None)
