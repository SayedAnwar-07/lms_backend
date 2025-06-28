from django.contrib import admin
from .models import Review, ReviewResponse, ReviewVote


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id','course', 'user', 'rating', 'is_approved', 'has_attended', 'created_at')
    list_filter = ('is_approved', 'has_attended', 'rating', 'course')
    search_fields = ('comment', 'user__username', 'course__title')
    list_editable = ('is_approved',)  
    raw_id_fields = ('course', 'user')  
    date_hierarchy = 'created_at'
    actions = ['approve_reviews', 'disapprove_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = "Disapprove selected reviews"


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ('review', 'instructor', 'created_at', 'updated_at')
    search_fields = ('response_text', 'review__id', 'instructor__username')
    raw_id_fields = ('review', 'instructor')
    date_hierarchy = 'created_at'


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'is_helpful', 'created_at')
    list_filter = ('is_helpful',)
    search_fields = ('review__id', 'user__username')
    raw_id_fields = ('review', 'user')
    date_hierarchy = 'created_at'