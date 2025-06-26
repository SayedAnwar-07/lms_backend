from django.db import models
from api.accounts.models import User


class Category(models.Model):
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Course(models.Model):
    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    banner = models.URLField()
    price = models.FloatField()
    discount_price = models.FloatField(null=True, blank=True)
    duration = models.CharField(max_length=100) 
    rating = models.FloatField(default=0.0)
    reviews = models.PositiveIntegerField(default=0)
    students = models.PositiveIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Beginner')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    what_you_will_learn = models.JSONField(default=list) 
    requirements = models.JSONField(default=list)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CurriculumSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="curriculum")
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    section = models.ForeignKey(CurriculumSection, on_delete=models.CASCADE, related_name='lectures', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    duration = models.CharField(max_length=20, default="00:00") 
    is_preview = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sequence_number = models.PositiveIntegerField(default=0) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sequence_number']  
        unique_together = ['course', 'sequence_number']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.sequence_number or self.sequence_number == 0:
            last_lesson = Lesson.objects.filter(course=self.course).order_by('-sequence_number').first()
            self.sequence_number = last_lesson.sequence_number + 1 if last_lesson else 1
        super().save(*args, **kwargs)


class Material(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    file_type = models.CharField(max_length=100)
    file = models.FileField(upload_to='materials/')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    price = models.FloatField()
    progress = models.IntegerField(default=0) 
    completed_lessons = models.ManyToManyField(Lesson, blank=True) 
    is_completed = models.BooleanField(default=False)
    payment_currency = models.CharField(max_length=3, default='USD')
    payment_status = models.CharField(max_length=20, blank=True)
    payment_receipt_url = models.URLField(blank=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    total_mark = models.FloatField(default=0)
    is_certificate_ready = models.BooleanField(default=False)

    def update_progress(self):
        total_lessons = Lesson.objects.filter(course=self.course, is_active=True).count()
        completed_count = self.completed_lessons.filter(is_active=True).count()
        self.progress = int((completed_count / total_lessons) * 100) if total_lessons else 0
        self.is_completed = self.progress == 100
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    
class LessonCompletion(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_completions')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=True)

    class Meta:
        unique_together = ('enrollment', 'lesson') 

    def __str__(self):
        return f"{self.enrollment.user.username} completed {self.lesson.title}"


class QuestionAnswer(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}-->{self.lesson}-->{self.description}"
