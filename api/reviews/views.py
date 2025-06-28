from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from api.core.models import Course
from .models import Review, ReviewResponse
from .serializers import (
    ReviewSerializer,
    CreateReviewSerializer,
    ReviewResponseSerializer,
    ReviewVoteSerializer,
    CreateReviewVoteSerializer
)


@swagger_auto_schema(method='get', responses={200: ReviewSerializer(many=True)})
@api_view(['GET'])
def list_reviews(request, course_id):
    """
    List all approved reviews for a specific course
    """
    reviews = Review.objects.filter(course_id=course_id, is_approved=True).order_by('-created_at')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    request_body=CreateReviewSerializer,
    responses={201: ReviewSerializer, 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, course_id):
    """
    Create a new review for a course (student only)
    """
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role != 'student':
        return Response(
            {'error': 'Only students can create reviews'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    data = request.data.copy()
    data['course'] = course_id
    serializer = CreateReviewSerializer(data=data, context={'request': request})
    
    if serializer.is_valid():
        review = serializer.save(user=request.user)
        response_serializer = ReviewSerializer(review)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='get', responses={200: ReviewSerializer})
@api_view(['GET'])
def review_detail(request, review_id):
    """
    Get details of a specific review
    """
    try:
        review = Review.objects.get(pk=review_id, is_approved=True)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ReviewSerializer(review)
    return Response(serializer.data)


@swagger_auto_schema(
    method='patch',
    request_body=CreateReviewSerializer,
    responses={200: ReviewSerializer, 400: 'Bad Request', 403: 'Forbidden'}
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_review(request, review_id):
    """
    Update a review (only by the review creator)
    """
    try:
        review = Review.objects.get(pk=review_id)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

    if review.user != request.user:
        return Response(
            {'error': 'You can only update your own reviews'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = CreateReviewSerializer(review, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(ReviewSerializer(review).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    responses={204: 'No Content', 403: 'Forbidden', 404: 'Not Found'}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, review_id):
    """
    Delete a review (only by the review creator)
    """
    try:
        review = Review.objects.get(pk=review_id)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

    if review.user != request.user:
        return Response(
            {'error': 'You can only delete your own reviews'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    review.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='post',
    request_body=ReviewResponseSerializer,
    responses={201: ReviewResponseSerializer, 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review_response(request, review_id):
    """
    Create a response to a review (instructor only)
    """
    try:
        review = Review.objects.get(pk=review_id)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role != 'teacher' or request.user != review.course.instructor:
        return Response(
            {'error': 'Only the course instructor can respond to reviews'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    data = request.data.copy()
    data['review'] = review_id
    serializer = ReviewResponseSerializer(data=data, context={'request': request})
    
    if serializer.is_valid():
        # Check if response already exists
        if ReviewResponse.objects.filter(review=review).exists():
            return Response(
                {'error': 'Response already exists for this review'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        response = serializer.save(instructor=request.user)
        return Response(ReviewResponseSerializer(response).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=CreateReviewVoteSerializer,
    responses={201: ReviewVoteSerializer, 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_review(request, review_id):
    """
    Vote on whether a review is helpful or not (student only)
    """
    try:
        review = Review.objects.get(pk=review_id, is_approved=True)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role != 'student':
        return Response(
            {'error': 'Only students can vote on reviews'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    data = request.data.copy()
    data['review'] = review_id
    serializer = CreateReviewVoteSerializer(data=data, context={'request': request})
    
    if serializer.is_valid():
        vote = serializer.save(user=request.user)
        return Response(ReviewVoteSerializer(vote).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='get', responses={200: ReviewResponseSerializer})
@api_view(['GET'])
def get_review_response(request, review_id):
    """
    Get the instructor's response to a review
    """
    try:
        response = ReviewResponse.objects.get(review_id=review_id)
    except ReviewResponse.DoesNotExist:
        return Response({'error': 'Response not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ReviewResponseSerializer(response)
    return Response(serializer.data)