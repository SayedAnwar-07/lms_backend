from django.urls import path
from .views import (
    list_reviews,
    create_review,
    review_detail,
    update_review,
    delete_review,
    create_review_response,
    vote_review,
    get_review_response
)

urlpatterns = [
    # Course reviews
    path('courses/<int:course_id>/reviews/', list_reviews, name='list-reviews'),
    path('courses/<int:course_id>/reviews/create/', create_review, name='create-review'),
    
    # Single review operations
    path('reviews/<int:review_id>/', review_detail, name='review-detail'),
    path('reviews/<int:review_id>/update/', update_review, name='update-review'),
    path('reviews/<int:review_id>/delete/', delete_review, name='delete-review'),
    path('reviews/<int:review_id>/response/', create_review_response, name='create-response'),
    path('reviews/<int:review_id>/response/view/', get_review_response, name='get-response'),
    path('reviews/<int:review_id>/vote/', vote_review, name='vote-review'),
]