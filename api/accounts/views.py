from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UserRegistrationSerializer, VerifyOTPSerializer, ResendOTPSerializer, UserLoginSerializer, UserProfileSerializer,PasswordResetConfirmSerializer,PasswordResetRequestSerializer
from .models import User
import logging
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser

logger = logging.getLogger(__name__)

# register
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def registerView(request):
    if request.method == 'GET':
        response_data = {
            "fields": {
                "username": {"type": "string", "required": True},
                "email": {"type": "email", "required": True},
                "password": {"type": "string", "required": True, "write_only": True},
                "password2": {"type": "string", "required": True, "write_only": True},
                "role": {"type": "string", "required": True, "choices": ["admin", "teacher", "student"]},
                "mobile_no": {"type": "string", "required": False},
                "full_name": {"type": "string", "required": False},
                "avatar": {"type": "url", "required": False},  # Changed from file to url
            },
            "message": "Submit these fields to register a new account"
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        if User.objects.filter(email=request.data.get('email')).exists():
            return Response({
                "status": "error",
                "message": "A user with this email already exists."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # No need to convert to dict, MultiPartParser handles files properly
        data = request.data
        serializer = UserRegistrationSerializer(data=data)
        
        try:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                response_data = {
                    "status": "success",
                    "message": "User registered successfully. OTP sent to email.",
                    "data": {
                        "email": user.email,
                        "username": user.username,
                        "role": user.role,
                        "full_name": user.full_name,
                        "mobile_no": user.mobile_no,
                        "avatar": user.avatar  # Direct URL
                    }
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except ValidationError as e:
            return Response({
                "status": "error",
                "message": "Validation error",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# verify OTP
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def verifyOTPView(request):
    if request.method == 'GET':
        response_data = {
            "fields": {
                "email": {"type": "email", "required": True},
                "otp": {"type": "string", "required": True, "max_length": 6},
            },
            "message": "Submit your email and OTP to verify your account"
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = VerifyOTPSerializer(data=request.data)
        
        try:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                response_data = {
                    "status": "success",
                    "message": "Email verified successfully. Account activated.",
                    "data": {
                        "email": user.email,
                        "is_verified": user.is_verified
                    }
                }
                return Response(response_data, status=status.HTTP_200_OK)
                
        except ValidationError as e:
            return Response({
                "status": "error",
                "message": "OTP verification failed",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
# resend OTP
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def resendOTPView(request):
    if request.method == 'GET':
        response_data = {
            "fields": {
                "email": {"type": "email", "required": True},
            },
            "message": "Submit your email to resend the OTP"
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = ResendOTPSerializer(data=request.data)
        
        try:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                response_data = {
                    "status": "success",
                    "message": "OTP resent successfully. Please check your email.",
                    "data": {
                        "email": user.email
                    }
                }
                return Response(response_data, status=status.HTTP_200_OK)
                
        except ValidationError as e:
            return Response({
                "status": "error",
                "message": "Failed to resend OTP",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# login
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def loginView(request):
    """
    Handle user login and JWT token generation.
    
    GET: Returns login form fields information
    POST: Authenticates user and returns JWT tokens
    """
    if request.method == 'GET':
        response_data = {
            "fields": {
                "email": {"type": "email", "required": True},
                "password": {"type": "string", "required": True, "write_only": True},
            },
            "message": "Submit your credentials to login"
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        
        try:
            if serializer.is_valid(raise_exception=True):
                user = serializer.validated_data['user']
                tokens = serializer.get_tokens(user)
                
                response_data = {
                    "status": "success",
                    "message": "Login successful",
                    "data": {
                        "email": user.email,
                        "username": user.username,
                        "role": user.role,
                        "full_name": user.full_name,
                        "mobile_no": user.mobile_no,
                        "avatar": user.avatar,
                        "tokens": tokens
                    }
                }
                return Response(response_data, status=status.HTTP_200_OK)
                
        except ValidationError as e:
            return Response({
                "status": "error",
                "message": "Login failed",
                "errors": e.detail
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)            

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def profileView(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserProfileSerializer(user, context={'request': request}) 
        response_data = {
            "status": "success",
            "message": "User profile retrieved successfully",
            "data": serializer.data,
            "editable_fields": {
                "username": {"type": "string", "required": False},
                "email": {"type": "email", "required": False},
                "mobile_no": {"type": "string", "required": False},
                "full_name": {"type": "string", "required": False},
                "avatar": {"type": "url", "required": False},  # Changed from file to url
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = UserProfileSerializer(
            user, data=request.data, partial=True, context={'request': request} 
        )

        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response_data = {
                    "status": "success",
                    "message": "Profile updated successfully",
                    "data": serializer.data
                }
                return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                "status": "error",
                "message": "Validation error",
                "errors": e.detail if hasattr(e, 'detail') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "An error occurred while updating profile",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def passwordResetRequestView(request):
    if request.method == 'GET':
        response_data = {
            "fields": {
                "email": {"type": "email", "required": True},
            },
            "message": "Submit your email to receive a password reset OTP",
            "example_request": {
                "email": "user@example.com"
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        try:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                response_data = {
                    "status": "success",
                    "message": "Password reset OTP sent to your email.",
                    "data": {
                        "email": user.email,
                    }
                }
                return Response(response_data, status=status.HTTP_200_OK)
                
        except ValidationError as e:
            return Response({
                "status": "error",
                "message": "Password reset failed",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}")
            return Response({
                "status": "error",
                "message": "An error occurred. Please try again later."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
@csrf_exempt
@parser_classes([MultiPartParser, FormParser, JSONParser])
def passwordResetConfirmView(request):
    if request.method == 'GET':
        response_data = {
            "fields": {
                "email": {"type": "email", "required": True},
                "otp": {"type": "string", "required": True, "max_length": 6},
                "new_password": {"type": "string", "required": True},
                "confirm_password": {"type": "string", "required": True},
            },
            "message": "Submit your email, OTP, and new password to reset your password",
            "example_request": {
                "email": "user@example.com",
                "otp": "123456",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        logger.info(f"Password reset confirm request received for email: {request.data.get('email')}")
        
        try:
            serializer = PasswordResetConfirmSerializer(data=request.data)
            
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                logger.info(f"Password reset successful for {user.email}")
                
                response_data = {
                    "status": "success",
                    "message": "Password reset successfully. You can now login with your new password.",
                    "data": {
                        "email": user.email,
                    }
                }
                return Response(response_data, status=status.HTTP_200_OK)
                
        except ValidationError as e:
            logger.error(f"Password reset validation error: {str(e)}")
            return Response({
                "status": "error",
                "message": "Password reset failed",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.exception("Password reset confirm error")
            return Response({
                "status": "error",
                "message": "An unexpected error occurred. Please try again later."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)