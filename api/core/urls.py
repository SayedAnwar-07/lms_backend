from django.urls import path
from .views import (
    category_list,
    category_create,
    course_list,
    create_course,
    public_course_detail,
    update_course,
    delete_course,
    lesson_list_create,
    lesson_detail_update_delete,
    teacher_dashboard,
    section_list_create,
    section_detail_update_delete,
    get_payment_details,
    process_payment,
    user_enrollments,
    check_enrollment,
    mark_lesson_completed,
    mark_lesson_incomplete,
    get_course_progress,
)

urlpatterns = [
    # Category endpoints
    path("categories/", category_list, name="category-list"),
    path("categories/create/", category_create, name="category-create"),
    
    # Course endpoints
   path("courses/", course_list, name="course-list"),
    path("courses/create/", create_course, name="create-course"),
    path("courses/<int:pk>/", public_course_detail, name="course-public-detail"),
    path("courses/<int:pk>/update/", update_course, name="course-update"),
    path("courses/<int:pk>/delete/", delete_course, name="course-delete"),
    
    
    path("teacher-dashboard/", teacher_dashboard, name="teacher-dashboard"),
    
    # Section endpoints
    path("sections/", section_list_create, name="section-list-create"),
    path("sections/<int:pk>/", section_detail_update_delete, name="section-detail"),
    
    # Lesson endpoints
    path("lessons/", lesson_list_create, name="lesson-list-create"),
    path("lessons/<int:pk>/", lesson_detail_update_delete, name="lesson-detail"),
    
    # payments
    path('payment/<int:course_id>/', get_payment_details, name='payment-details'),
    path('payment/process/', process_payment, name='process-payment'),
    
    # enrolled
    path('enrollments/', user_enrollments, name='user-enrollments'),
    path('enrollments/check/<int:course_id>/', check_enrollment, name='check-enrollment'),
    
    # Add these to your urls.py
    path('enrollments/<int:enrollment_id>/lessons/<int:lesson_id>/complete/', mark_lesson_completed, name='mark-lesson-completed'),
    path('enrollments/<int:enrollment_id>/lessons/<int:lesson_id>/incomplete/', mark_lesson_incomplete, name='mark-lesson-incomplete'),
    path('courses/<int:course_id>/progress/', get_course_progress, name='course-progress'),
]