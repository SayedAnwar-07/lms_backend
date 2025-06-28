from rest_framework import serializers
from api.accounts.models import User
from api.core.models import Course
from .models import Review, ReviewResponse, ReviewVote


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar']


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'banner']


class ReviewVoteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ReviewVote
        fields = ['id', 'user', 'is_helpful', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    votes = ReviewVoteSerializer(many=True, read_only=True)
    helpful_count = serializers.IntegerField(read_only=True)
    not_helpful_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'course', 'user', 'rating',  'comment', 
            'is_approved', 'has_attended', 'created_at', 'updated_at',
            'helpful_count', 'not_helpful_count', 'votes'
        ]
        read_only_fields = [
            'id', 'user', 'course', 'created_at', 'updated_at', 
            'helpful_count', 'not_helpful_count', 'votes'
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['course', 'rating','comment', 'has_attended']
        
    def validate(self, data):
        user = self.context['request'].user
        course = data['course']
        
        if not course.enrollment_set.filter(user=user, is_active=True).exists():
            raise serializers.ValidationError("You must be enrolled in the course to leave a review")
            
        if Review.objects.filter(course=course, user=user).exists():
            raise serializers.ValidationError("You have already reviewed this course")
            
        return data


class ReviewResponseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    
    class Meta:
        model = ReviewResponse
        fields = ['id', 'review', 'instructor', 'response_text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'instructor', 'created_at', 'updated_at']


class CreateReviewVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewVote
        fields = ['review', 'is_helpful']
        
    def validate(self, data):
        user = self.context['request'].user
        review = data['review']
        
        # Check if user already voted on this review
        if ReviewVote.objects.filter(review=review, user=user).exists():
            raise serializers.ValidationError("You have already voted on this review")
            
        return data