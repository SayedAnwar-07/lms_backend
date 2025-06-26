from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.conf import settings
import logging


from .models import User

logger = logging.getLogger(__name__)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    avatar = serializers.URLField(required=False, allow_null=True)  # Changed from ImageField to URLField

    class Meta:
        model = User
        fields = ('avatar','username','full_name', 'email', 'password', 'password2', 'role', 'mobile_no')
        extra_kwargs = {
            'role': {'required': True},
            'full_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        avatar = validated_data.pop('avatar', None)
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Handle avatar upload
        if avatar:
            user.avatar = avatar
            user.save()
            
        user.generate_otp()
        self._send_otp_email(user)
        return user

    def _send_otp_email(self, user):
        """Sends an HTML email with embedded CSS containing the OTP."""
        try:
            subject = f"{settings.SITE_NAME} - Email Verification Code"
            from_email = f"{settings.SITE_NAME} <{settings.DEFAULT_FROM_EMAIL}>"
            to_email = [user.email]

            context = {
                'site_name': settings.SITE_NAME,
                'user_email': user.email,
                'otp': user.otp,
                'expiry_minutes': settings.OTP_EXPIRY_MINUTES,
            }

            try:
                html_content = render_to_string("emails/otp_email.html", context)
            except TemplateDoesNotExist:
                logger.error(f"OTP email template not found at emails/otp_email.html")
                raise ValueError("Email template not found")

            text_content = f"""
    Hello {user.email},

    Thank you for registering with {settings.SITE_NAME}!

    Your verification code is: {user.otp}

    This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.

    If you didn't request this code, please ignore this email.

    Regards,
    The {settings.SITE_NAME} Team
            """

            email = EmailMultiAlternatives(subject, text_content.strip(), from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"OTP email sent to {user.email}")

        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
            raise

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=6, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        if user.is_verified:
            raise serializers.ValidationError("User is already verified.")

        if not user.otp or user.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")

        # Check if OTP is expired
        if user.otp_created_at and (timezone.now() - user.otp_created_at) > timedelta(minutes=settings.OTP_EXPIRY_MINUTES):
            raise serializers.ValidationError("OTP has expired.")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.is_verified = True
        user.otp = None
        user.otp_created_at = None
        user.save()
        return user


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        if user.is_verified:
            raise serializers.ValidationError("User is already verified.")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.generate_otp()
        self._send_otp_email(user)
        return user

    def _send_otp_email(self, user):
        """Reuses the same OTP email sending logic from UserRegistrationSerializer"""
        UserRegistrationSerializer()._send_otp_email(user)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("No account found with this email address.")

            user = authenticate(request=self.context.get('request'), 
                            username=email, 
                            password=password)
            
            if not user:
                raise serializers.ValidationError("Invalid password.")
            
            if not user.is_verified:
                raise serializers.ValidationError("Account not verified. Please verify your email first.")

            attrs['user'] = user
        else:
            raise serializers.ValidationError("Both email and password are required.")

        return attrs

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        
class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    avatar = serializers.URLField(required=False) 

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'mobile_no',
            'role',
            'is_verified',
            'full_name',
            'avatar',
            'avatar_url'
        ]
        extra_kwargs = {
            'role': {'read_only': True},
            'is_verified': {'read_only': True},
        }

    def get_avatar_url(self, obj):
            return obj.avatar
    
    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar', None)
        if avatar is not None:
            instance.avatar = avatar
        return super().update(instance, validated_data)

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.generate_otp() 
        self._send_reset_email(user)
        return user

    def _send_reset_email(self, user):
        """Sends a password reset email with OTP"""
        try:
            subject = f"{settings.SITE_NAME} - Password Reset Request"
            from_email = f"{settings.SITE_NAME} <{settings.DEFAULT_FROM_EMAIL}>"
            to_email = [user.email]

            context = {
                'site_name': settings.SITE_NAME,
                'user_email': user.email,
                'otp': user.otp,
                'expiry_minutes': settings.OTP_EXPIRY_MINUTES,
            }

            try:
                html_content = render_to_string("emails/password_reset_email.html", context)
            except TemplateDoesNotExist:
                logger.error(f"Password reset email template not found at emails/password_reset_email.html")
                html_content = None

            text_content = f"""
Hello {user.email},

You requested a password reset for your {settings.SITE_NAME} account.

Your password reset code is: {user.otp}

This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.

If you didn't request this password reset, please ignore this email.

Regards,
The {settings.SITE_NAME} Team
            """

            email = EmailMultiAlternatives(subject, text_content.strip(), from_email, to_email)
            if html_content:
                email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"Password reset email sent to {user.email}")

        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            raise


class PasswordResetConfirmSerializer(serializers.Serializer):
    
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=6, required=True)
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        required=True
    )
    confirm_password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        required=True
    )

    def validate(self, attrs):
        print("Received data:", attrs)  # Debug what's coming in
        email = attrs.get('email')
        otp = attrs.get('otp')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        print(f"Validating: {email}, OTP: {otp}")  # Debug

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        if not user.otp or user.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")

        if user.otp_created_at and (timezone.now() - user.otp_created_at) > timedelta(minutes=settings.OTP_EXPIRY_MINUTES):
            raise serializers.ValidationError("OTP has expired.")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.otp = None
        user.otp_created_at = None
        user.save()
        return user