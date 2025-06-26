from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Course, Lesson, Material,
    Enrollment, QuestionAnswer, CurriculumSection
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'active_status', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title',)
    ordering = ('-created_at',)
    list_per_page = 20
    
    def active_status(self, obj):
        return "Active" if obj.is_active else "Inactive"
    active_status.short_description = 'Status'
    active_status.admin_order_field = 'is_active'


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'duration', 'is_preview', 'is_active')
    ordering = ('sequence_number',)


class CurriculumSectionInline(admin.StackedInline):
    model = CurriculumSection
    extra = 1
    show_change_link = True
    inlines = [LessonInline]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'category_link', 'instructor_link',
        'level', 'price_display', 'featured_status', 'created_date'
    )
    list_filter = ('level', 'is_featured', 'category')
    search_fields = ('title', 'description', 'instructor__email', 'category__title')
    ordering = ('-created_at',)
    inlines = [CurriculumSectionInline]
    list_per_page = 20
    readonly_fields = ('banner_preview',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'banner', 'banner_preview')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price'),
        }),
        ('Details', {
            'fields': ('duration', 'level', 'category', 'instructor', 'is_featured'),
        }),
        ('Content', {
            'fields': ('what_you_will_learn', 'requirements'),
        }),
    )

    def category_link(self, obj):
        return format_html('<a href="/admin/courses/category/{}/">{}</a>', 
                         obj.category.id, obj.category.title)
    category_link.short_description = 'Category'
    
    def instructor_link(self, obj):
        return format_html('<a href="/admin/accounts/user/{}/">{}</a>', 
                         obj.instructor.id, obj.instructor.full_name)
    instructor_link.short_description = 'Instructor'
    
    def price_display(self, obj):
        if obj.discount_price:
            return format_html('<span style="text-decoration: line-through;">${}</span> ${}', 
                             obj.price, obj.discount_price)
        return f"${obj.price}"
    price_display.short_description = 'Price'
    
    def featured_status(self, obj):
        return "⭐" if obj.is_featured else ""
    featured_status.short_description = 'Featured'
    
    def created_date(self, obj):
        return obj.created_at.date()
    created_date.short_description = 'Created'
    created_date.admin_order_field = 'created_at'
    
    def banner_preview(self, obj):
        if obj.banner:
            return format_html('<img src="{}" style="max-height: 200px;"/>', obj.banner.url)
        return "No banner"
    banner_preview.short_description = 'Banner Preview'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'course_link', 'section_link', 
        'duration', 'preview_status', 'active_status'
    )
    list_filter = ('is_active', 'is_preview', 'course')
    search_fields = ('title', 'course__title', 'section__title')
    ordering = ('course', 'sequence_number')
    list_per_page = 30
    list_select_related = ('course', 'section')
    
    def course_link(self, obj):
        return format_html('<a href="/admin/courses/course/{}/">{}</a>', 
                          obj.course.id, obj.course.title)
    course_link.short_description = 'Course'
    
    def section_link(self, obj):
        if obj.section:
            return format_html('<a href="/admin/courses/curriculumsection/{}/">{}</a>', 
                             obj.section.id, obj.section.title)
        return "-"
    section_link.short_description = 'Section'
    
    def preview_status(self, obj):
        return "Preview" if obj.is_preview else ""
    preview_status.short_description = 'Preview'
    
    def active_status(self, obj):
        return "Active" if obj.is_active else "Inactive"
    active_status.short_description = 'Status'


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'file_type', 'course_link', 
        'active_status', 'created_date'
    )
    list_filter = ('is_active', 'file_type', 'course')
    search_fields = ('title', 'description', 'course__title')
    ordering = ('-created_at',)
    list_per_page = 30
    
    def course_link(self, obj):
        return format_html('<a href="/admin/courses/course/{}/">{}</a>', 
                          obj.course.id, obj.course.title)
    course_link.short_description = 'Course'
    
    def active_status(self, obj):
        return "Active" if obj.is_active else "Inactive"
    active_status.short_description = 'Status'
    
    def created_date(self, obj):
        return obj.created_at.date()
    created_date.short_description = 'Created'
    created_date.admin_order_field = 'created_at'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student_link', 'course_link','price', 'progress_bar', 
        'completion_status', 'created_date',
    )
    list_filter = (
        'id','is_active', 'is_completed', 'is_certificate_ready',
        'payment_status'
    )
    search_fields = ('user__username', 'course__title')
    ordering = ('-created_at',)
    list_per_page = 30
    list_select_related = ('user', 'course')
    
    def student_link(self, obj):
        return format_html('<a href="/admin/accounts/user/{}/">{}</a>', 
                         obj.user.id, obj.user.full_name)
    student_link.short_description = 'Student'
    
    def course_link(self, obj):
        return format_html('<a href="/admin/courses/course/{}/">{}</a>', 
                          obj.course.id, obj.course.title)
    course_link.short_description = 'Course'
    
    def progress_bar(self, obj):
        return format_html(
            '<div style="width:100px;background:#ddd;">'
            '<div style="width:{}%;background:#4CAF50;height:20px;"></div>'
            '</div>{}%', 
            obj.progress, obj.progress
        )
    progress_bar.short_description = 'Progress'
    
    def completion_status(self, obj):
        if obj.is_completed:
            return format_html('<span style="color:green;">✓ Completed</span>')
        return format_html('<span style="color:orange;">In Progress</span>')
    completion_status.short_description = 'Status'
    
    def payment_status(self, obj):
        if obj.payment_status == 'succeeded':
            return format_html('<span style="color:green;">✓ Paid</span>')
        return format_html('<span style="color:red;">{}</span>', 
                         obj.payment_status or 'Unpaid')
    payment_status.short_description = 'Payment'
    
    def created_date(self, obj):
        return obj.created_at.date()
    created_date.short_description = 'Enrolled'
    created_date.admin_order_field = 'created_at'


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'truncated_description', 'student_link', 
        'lesson_link', 'active_status', 'created_date'
    )
    list_filter = ('is_active', 'lesson__course')
    search_fields = ('user__username', 'lesson__title', 'description')
    ordering = ('-created_at',)
    list_per_page = 30
    
    def truncated_description(self, obj):
        return (obj.description[:50] + '...') if len(obj.description) > 50 else obj.description
    truncated_description.short_description = 'Question'
    
    def student_link(self, obj):
        return format_html('<a href="/admin/accounts/user/{}/">{}</a>', 
                         obj.user.id, obj.user.full_name)
    student_link.short_description = 'Student'
    
    def lesson_link(self, obj):
        return format_html('<a href="/admin/courses/lesson/{}/">{}</a>', 
                          obj.lesson.id, obj.lesson.title)
    lesson_link.short_description = 'Lesson'
    
    def active_status(self, obj):
        return "Active" if obj.is_active else "Inactive"
    active_status.short_description = 'Status'
    
    def created_date(self, obj):
        return obj.created_at.date()
    created_date.short_description = 'Asked'
    created_date.admin_order_field = 'created_at'


@admin.register(CurriculumSection)
class CurriculumSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_link', 'lesson_count')
    search_fields = ('title', 'course__title')
    list_per_page = 30
    inlines = [LessonInline]
    
    def course_link(self, obj):
        return format_html('<a href="/admin/courses/course/{}/">{}</a>', 
                          obj.course.id, obj.course.title)
    course_link.short_description = 'Course'
    
    def lesson_count(self, obj):
        return obj.lectures.count()
    lesson_count.short_description = 'Lessons'