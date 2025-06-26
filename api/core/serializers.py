from rest_framework import serializers
from ast import literal_eval  
from .models import (
    Category, Course, Lesson, Material, Enrollment, QuestionAnswer, CurriculumSection
)
from api.accounts.models import User

class CategorySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='title')

    class Meta:
        model = Category
        fields = ['id', 'name', 'title', 'is_active', 'created_at', 'updated_at']
        extra_kwargs = {
            'title': {'write_only': True} 
        }

class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'avatar', 'mobile_no']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'video', 'course',
            'section', 'duration', 'is_preview', 'is_active',
            'created_at', 'updated_at', 'sequence_number'
        ]


class CurriculumSectionSerializer(serializers.ModelSerializer):
    lectures = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = CurriculumSection
        fields = ['id', 'course', 'title', 'lectures']


class CourseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True) 
    instructor = InstructorSerializer(read_only=True)
    curriculum = CurriculumSectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'banner', 'price',
            'discount_price', 'duration', 'rating', 'reviews',
            'students', 'start_date', 'is_featured', 'level',
            'category', 'category_id', 'instructor', 'what_you_will_learn',
            'requirements', 'curriculum',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'banner': {'required': True},
            'price': {'min_value': 0},
            'discount_price': {'min_value': 0},
        }

    def validate_what_you_will_learn(self, value):
        if isinstance(value, str):
            try:
                value = literal_eval(value)  
            except (ValueError, SyntaxError):
                raise serializers.ValidationError("Must be a valid Python list representation")
        
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of strings")
        
        return [str(item).strip() for item in value if str(item).strip()]

    def validate_requirements(self, value):
        if isinstance(value, str):
            try:
                value = literal_eval(value)
            except (ValueError, SyntaxError):
                raise serializers.ValidationError("Must be a valid Python list representation")
        
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of strings")
        
        return [str(item).strip() for item in value if str(item).strip()]


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    completed_lessons = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Lesson.objects.all(), 
        required=False
    )

    class Meta:
        model = Enrollment
        fields = '__all__'


class PaymentSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    payment_intent_id = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    


class QuestionAnswerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    lesson = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = QuestionAnswer
        fields = '__all__'
