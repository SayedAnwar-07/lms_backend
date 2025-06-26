from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string

USER_ROLES = (
    ("admin", "Admin"),
    ("teacher", "Teacher"),
    ("student", "Student"),
)

class User(AbstractUser):
    role = models.CharField(max_length=10, choices=USER_ROLES, default="student")
    full_name = models.CharField(max_length=100, blank=True)  
    avatar = models.URLField(default='https://www.iconpacks.net/icons/2/free-user-icon-3296-thumb.png')
    email = models.EmailField(unique=True)
    mobile_no = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    # Add these lines
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] 

    def generate_otp(self):
        """Generate a 6-digit OTP"""
        self.otp = ''.join(random.choices(string.digits, k=6))
        self.save()
        return self.otp

    def __str__(self):
        return f"{self.username} ({self.role})"