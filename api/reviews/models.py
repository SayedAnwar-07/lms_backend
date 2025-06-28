from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from api.accounts.models import User
from api.core.models import Course


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=RATING_CHOICES
    )
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)  
    has_attended = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('course', 'user') 
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s review for {self.course.comment}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_course_rating()

    def update_course_rating(self):
        reviews = Review.objects.filter(course=self.course, is_approved=True)
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.course.rating = round(avg_rating, 1)
            self.course.reviews = reviews.count()
            self.course.save()


class ReviewResponse(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='response')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Instructor response to {self.review}"


class ReviewVote(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField() 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')  

    def __str__(self):
        return f"{self.user.username} voted on {self.review}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_review_vote_counts()

    def update_review_vote_counts(self):
        helpful_count = ReviewVote.objects.filter(review=self.review, is_helpful=True).count()
        not_helpful_count = ReviewVote.objects.filter(review=self.review, is_helpful=False).count()
        
        self.review.helpful_count = helpful_count
        self.review.not_helpful_count = not_helpful_count
        self.review.save()