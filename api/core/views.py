from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef
from django.core.cache import cache
from .permissions import IsStudentUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import authentication_classes
from .models import Category, Course, Lesson, Material, Enrollment, QuestionAnswer, CurriculumSection, LessonCompletion
LessonCompletion
from .serializers import (
    CategorySerializer,
    CourseSerializer,
    LessonSerializer,
    EnrollmentSerializer,
    QuestionAnswerSerializer,
    CurriculumSectionSerializer,
    PaymentSerializer
)
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
import stripe
import logging
logger = logging.getLogger(__name__)


class MyPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = "limit"
    max_page_size = 100
    page_query_param = 'page'
    last_page_strings = ('last',)

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
        })

# Public GET endpoint for categories
@swagger_auto_schema(method='get', auto_schema=None)
@api_view(["GET"])
@permission_classes([AllowAny])
def category_list(request):
    categories = Category.objects.all()
    paginator = MyPagination()
    result_page = paginator.paginate_queryset(categories, request)
    serializer = CategorySerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

# Protected POST endpoint for category creation (admin only)
@swagger_auto_schema(method='post', request_body=CategorySerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def category_create(request):
    if request.user.role != "admin":
        return Response(
            {"detail": "Only admin can create categories."}, 
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([AllowAny])
def course_list(request):
    try:
        queryset = Course.objects.select_related('category').all()
        
        category = request.query_params.get('category')
        if category and category != 'all':
            queryset = queryset.filter(category_id=category)
        
        level = request.query_params.get('level')
        if level and level != 'all':
            queryset = queryset.filter(level=level)
        
        is_featured = request.query_params.get('is_featured')
        if is_featured:
            if is_featured.lower() == 'true':
                queryset = queryset.filter(is_featured=True)
            elif is_featured.lower() == 'false':
                queryset = queryset.filter(is_featured=False)
            
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # Ordering and pagination
        queryset = queryset.order_by('-created_at')
        paginator = MyPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = CourseSerializer(
            result_page, 
            many=True,
            context={'request': request}
        )
        
        return paginator.get_paginated_response(serializer.data)
    
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(method="post", request_body=CourseSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_course(request):
    if request.user.role != "teacher":
        return Response(
            {"detail": "Only teachers can create courses."}, 
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = CourseSerializer(data=request.data)
    if serializer.is_valid():
        print("Serializer errors:", serializer.errors)
        # Validate category exists
        try:
            Category.objects.get(pk=request.data.get('category_id'))  
        except Category.DoesNotExist:
            return Response(
                {"category_id": "Invalid category ID"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer.save(instructor=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method="get", responses={200: CourseSerializer})
@api_view(["GET"])
@permission_classes([AllowAny]) 
def public_course_detail(request, pk):
    """Public endpoint to retrieve course details (no authentication required)"""
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response({"detail": "Course not found"}, status=404)

    serializer = CourseSerializer(course)
    return Response(serializer.data)

@swagger_auto_schema(method="put", request_body=CourseSerializer, responses={200: CourseSerializer})
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_course(request, pk):
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response({"detail": "Course not found"}, status=404)

    if request.user.role != "teacher":
        return Response(
            {"detail": "Only teachers can update courses"},
            status=403,
        )
    data = request.data.copy()
    if 'banner' not in data and hasattr(course, 'banner'):
        data['banner'] = course.banner
    elif hasattr(data['banner'], 'read'):
        pass

    serializer = CourseSerializer(course, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_course(request, pk):
    """Delete a course (only allowed for course instructor)"""
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response({"detail": "Course not found"}, status=404)

    if request.user.role != "teacher" or request.user != course.instructor:
        return Response(
            {"detail": "Only the course owner (teacher) can delete this course."},
            status=403,
        )

    course.delete()
    return Response({"detail": "Course deleted"}, status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method="post", request_body=LessonSerializer)
@swagger_auto_schema(method="patch", request_body=LessonSerializer)
@api_view(["GET", "POST", "PATCH", "DELETE"])
def lesson_list_create(request, pk=None):
    if request.method == "GET":
        lessons = Lesson.objects.all()
        paginator = MyPagination()
        result_page = paginator.paginate_queryset(lessons, request)
        serializer = LessonSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    # For POST, PATCH, DELETE → Require authentication + teacher role
    if not request.user.is_authenticated or request.user.role != "teacher":
        raise PermissionDenied("Only authenticated teachers can perform this action.")
    
    
    if request.method == "POST":
        serializer = LessonSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == "PATCH":
        try:
            lesson = Lesson.objects.get(pk=pk)
        except Lesson.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = LessonSerializer(lesson, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == "DELETE":
        try:
            lesson = Lesson.objects.get(pk=pk)
        except Lesson.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



@swagger_auto_schema(method="post", request_body=QuestionAnswerSerializer)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def question_list_create(request):
    if request.method == "GET":
        questions = QuestionAnswer.objects.all()
        paginator = MyPagination()
        result_page = paginator.paginate_queryset(questions, request)
        serializer = QuestionAnswerSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    elif request.method == "POST":
        serializer = QuestionAnswerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return Response(
            {
                "status": "error",
                "message": "Only teachers can access this dashboard.",
                "data": None
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    teacher = request.user
    
    try:
        courses = Course.objects.filter(instructor=teacher)
        course_serializer = CourseSerializer(courses, many=True)

        total_courses = courses.count()
        total_students = sum(course.students for course in courses)  
        total_featured_courses = courses.filter(is_featured=True).count() 
        
        response_data = {
            "status": "success",
            "message": "Teacher dashboard data retrieved successfully",
            "data": {
                'teacher': {
                    'id': teacher.id,
                    'name': teacher.full_name,
                    'email': teacher.email,
                    "avatar": teacher.avatar,
                    'mobile_no': teacher.mobile_no,
                    'join_date': teacher.date_joined.strftime("%Y-%m-%d")
                },
                'stats': {
                    'total_courses': total_courses,
                    'total_students': total_students,
                    'total_featured_courses': total_featured_courses,
                },
                'courses': course_serializer.data,
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": str(e),
                "data": None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_enrollments(request):
    enrollments = Enrollment.objects.filter(user=request.user)
    paginator = MyPagination()
    result_page = paginator.paginate_queryset(enrollments, request)
    serializer = EnrollmentSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@swagger_auto_schema(method="post", request_body=EnrollmentSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStudentUser])
def enroll_in_course(request):
    data = request.data.copy()
    data['user'] = request.user.id  
    serializer = EnrollmentSerializer(data=data)

    if serializer.is_valid():
        course_id = serializer.validated_data['course'].id
        if Enrollment.objects.filter(user=request.user, course_id=course_id).exists():
            return Response({"detail": "You are already enrolled in this course."}, status=400)

        serializer.save(user=request.user)
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)

# Section Views
@api_view(['GET', 'POST'])
def section_list_create(request):
    if request.method == 'GET':
        sections = CurriculumSection.objects.all()
        serializer = CurriculumSectionSerializer(sections, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.is_authenticated or request.user.role != 'teacher':
            return Response(
                {"error": "Only authenticated teachers can create sections"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = CurriculumSectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH', 'DELETE'])
def section_detail_update_delete(request, pk):
    try:
        section = CurriculumSection.objects.get(pk=pk)
    except CurriculumSection.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CurriculumSectionSerializer(section)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        if not request.user.is_authenticated or request.user.role != 'teacher':
            return Response(
                {"error": "Only authenticated teachers can update sections"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CurriculumSectionSerializer(section, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not request.user.is_authenticated or request.user.role != 'teacher':
            return Response(
                {"error": "Only authenticated teachers can delete sections"},
                status=status.HTTP_403_FORBIDDEN
            )
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Lesson Detail View
@api_view(['GET', 'PATCH', 'DELETE'])
def lesson_detail_update_delete(request, pk):
    try:
        lesson = Lesson.objects.get(pk=pk)
    except Lesson.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'GET':
        serializer = LessonSerializer(lesson)  
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        if not request.user.is_authenticated or request.user.role != 'teacher':
            return Response(
                {"error": "Only authenticated teachers can update lessons"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = LessonSerializer(lesson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not request.user.is_authenticated or request.user.role != 'teacher':
            return Response(
                {"error": "Only authenticated teachers can delete lessons"},
                status=status.HTTP_403_FORBIDDEN
            )
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY 

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_payment_details(request, course_id):
    try:
        logger.info(f"Starting payment process for course {course_id} by user {request.user.id}")
        
        course = Course.objects.get(id=course_id)
        user = request.user
        
        logger.info(f"Course found: {course.title}")
        
        if Enrollment.objects.filter(user=user, course=course).exists():
            logger.info("User already enrolled")
            return Response({
                "already_enrolled": True,
                "message": "You are already enrolled in this course",
                **CourseSerializer(course).data
            }, status=200)

        amount = int((course.discount_price or course.price) * 100)
        logger.info(f"Calculated amount: {amount} cents")
        
        if amount <= 0:
            logger.error("Invalid amount calculated")
            raise ValueError("Invalid payment amount")

        logger.info("Creating Stripe PaymentIntent...")
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            metadata={
                "course_id": course.id,
                "user_id": user.id,
                "user_email": user.email,
            },
            receipt_email=user.email,
            description=f"Payment for {course.title}",
        )
        logger.info(f"Stripe PaymentIntent created: {intent.id}")

        return Response({
            "already_enrolled": False,
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "currency": intent.currency,
            "amount": amount,
            **CourseSerializer(course).data
        })

    except Course.DoesNotExist:
        logger.error(f"Course not found: {course_id}")
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in get_payment_details: {str(e)}", exc_info=True)
        return Response({"error": "Payment processing failed"}, status=500)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_payment(request):
    serializer = PaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=400)
    
    data = serializer.validated_data
    user = request.user
    
    try:
        intent = stripe.PaymentIntent.retrieve(data['payment_intent_id'])
        
        if intent.status != 'succeeded':
            return Response({
                "error": f"Payment not completed. Status: {intent.status}"
            }, status=400)
        if (str(intent.metadata.get('course_id')) != str(data['course_id']) or 
            str(intent.metadata.get('user_id')) != str(user.id)):
            return Response({"error": "Payment validation failed"}, status=400)

        # Create enrollment
        course = Course.objects.get(id=data['course_id'])
        price_paid = intent.amount / 100
        
        enrollment, created = Enrollment.objects.get_or_create(
            user=user,
            course=course,
            defaults={'is_active': True, 'price': price_paid}
        )
        
        if not created:
            return Response({"message": "Already enrolled"}, status=200)

        return Response({
            "message": "Enrollment successful",
            "enrollment_id": enrollment.id,
            "amount_paid": price_paid
        }, status=201)

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except stripe.error.StripeError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error in process_payment: {str(e)}")
        return Response({"error": "Payment processing failed"}, status=500)
    
class PaymentHistoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_enrollments(request):
    enrollments = Enrollment.objects.filter(
        user=request.user, 
        is_active=True
    ).select_related('course')
    serializer = EnrollmentSerializer(enrollments, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_enrollment(request, course_id):
    is_enrolled = Enrollment.objects.filter(
        user=request.user,
        course_id=course_id,
        is_active=True
    ).exists()
    return Response({"is_enrolled": is_enrolled})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStudentUser])
def mark_lesson_completed(request, enrollment_id, lesson_id):
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
        lesson = Lesson.objects.get(id=lesson_id, course=enrollment.course)
    except (Enrollment.DoesNotExist, Lesson.DoesNotExist):
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    print(f"Before: progress={enrollment.progress}, completed_lessons={enrollment.completed_lessons.count()}")

    enrollment.completed_lessons.add(lesson)
    LessonCompletion.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    enrollment.update_progress()
    enrollment.refresh_from_db()  #

    print(f"After: progress={enrollment.progress}, completed_lessons={enrollment.completed_lessons.count()}")

    return Response({
        "detail": "Lesson marked as completed",
        "progress": enrollment.progress,
        "is_completed": True,
        "lesson_id": lesson_id,
        "is_course_completed": enrollment.is_completed,
        "completed_lessons": [l.id for l in enrollment.completed_lessons.all()]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStudentUser])
def mark_lesson_incomplete(request, enrollment_id, lesson_id):
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
        lesson = Lesson.objects.get(id=lesson_id, course=enrollment.course)
    except (Enrollment.DoesNotExist, Lesson.DoesNotExist):
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if not enrollment.completed_lessons.filter(id=lesson_id).exists():
        return Response({
            "detail": "Lesson not marked as completed",
            "progress": enrollment.progress,
            "is_completed": False,
            "lesson_id": lesson_id
        }, status=status.HTTP_200_OK)

    enrollment.completed_lessons.remove(lesson)
    enrollment.update_progress()
    LessonCompletion.objects.filter(enrollment=enrollment, lesson=lesson).delete()

    return Response({
        "detail": "Lesson marked as incomplete",
        "progress": enrollment.progress,
        "is_completed": False,
        "lesson_id": lesson_id,
        "is_course_completed": enrollment.is_completed,
        "completed_lessons": [l.id for l in enrollment.completed_lessons.all()]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def get_course_progress(request, course_id):
    try:
        enrollment = Enrollment.objects.get(user=request.user, course_id=course_id)
        total_lessons = Lesson.objects.filter(course_id=course_id).count()
        completed_lessons = enrollment.completed_lessons.count()
        
        # Get detailed progress
        lessons = Lesson.objects.filter(course_id=course_id).annotate(
            is_completed=Exists(
                enrollment.completed_lessons.filter(pk=OuterRef('pk'))
            )
        ).order_by('sequence_number')
        
        lesson_serializer = LessonSerializer(lessons, many=True)
        
        return Response({
            'course_id': course_id,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': enrollment.progress,
            'is_course_completed': enrollment.is_completed,
            'lessons': lesson_serializer.data
        })
    except Enrollment.DoesNotExist:
        return Response({"detail": "Not enrolled in this course"}, status=status.HTTP_404_NOT_FOUND)