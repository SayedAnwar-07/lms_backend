from django.urls import path
from .views import (
    registerView,
    verifyOTPView,
    resendOTPView,
    loginView,
    profileView,
    passwordResetRequestView,
    passwordResetConfirmView,
)

urlpatterns = [
    path('users/register/', registerView, name='register'),
    
    path('users/verify-otp/', verifyOTPView, name='verify-otp'),
    path('users/resend-otp/', resendOTPView, name='resend-otp'),
    
    path('users/login/', loginView, name='login'),
    
    path('users/profile/', profileView, name='profile'),
    
    path('users/password-reset/', passwordResetRequestView, name='password-reset'),
    path('users/password-reset-confirm/', passwordResetConfirmView, name='password-reset-confirm'),

]