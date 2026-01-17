"""
Views for users_auth app
All user authentication and management endpoints
"""
import logging
import random
import re

logger = logging.getLogger(__name__)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
from django.db.models import Q
from django.conf import settings

from .models import User, PasswordResetToken, UserSession, LoginAttempt
from django.utils import timezone
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserListSerializer,
    TokenRefreshSerializer,
    CreatePrivilegedUserSerializer,
    VerifyForgotPasswordOTPSerializer,
    ResetPasswordWithTokenSerializer,
    ProfileSendOTPSerializer,
    ProfileVerifyOTPSerializer,
    ProfileChangePasswordSerializer,
)
from .jwt_utils import JWTManager
from .authentication import JWTAuthentication, get_client_ip, get_user_agent


class RegisterView(APIView):
    """
    API endpoint for user registration.
    
    Step 1: User provides First Name, Middle Name, Last Name, Email, Mobile Number, Password.
    Step 2: After registration, OTPs are sent to email and phone for verification.
    Step 3: User must verify both OTPs before they can login.
    
    POST /api/auth-user/register/
    
    Request body:
    {
        "first_name": "John",
        "middle_name": "K",           # Optional
        "last_name": "Doe",
        "email": "john@example.com",
        "phone_number": "9876543210",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = []  # Using custom throttle below
    
    def get_throttles(self):
        """Apply registration rate throttle."""
        from .throttling import RegistrationRateThrottle
        return [RegistrationRateThrottle()]
    
    def post(self, request):
        """
        Register a new user or resend OTP to unverified user.
        
        Two-step process:
        1. User data is created/updated with is_email_verified=False
        2. OTP is generated, stored in User model, and sent via email
        
        If user exists but is not verified:
        - OTP is regenerated and resent (no error thrown)
        """
        from django.conf import settings
        from .email_service import send_otp_email
        import random
        
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Get OTP settings
            otp_length = getattr(settings, 'OTP_LENGTH', 6)
            otp_expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            
            # Generate and store email OTP in User model
            email_otp_code = ''.join([str(random.randint(0, 9)) for _ in range(otp_length)])
            user.email_otp = email_otp_code
            user.email_otp_created_at = timezone.now()
            user.email_otp_attempt_count = 0  # Reset attempt counter for new/resent OTP
            user.save(update_fields=['email_otp', 'email_otp_created_at', 'email_otp_attempt_count'])
            
            # Send OTP via email
            user_name = user.first_name or user.email.split('@')[0]
            email_sent = send_otp_email(
                email=user.email,
                otp_code=email_otp_code,
                user_name=user_name
            )
            
            response_data = {
                'success': True,
                'message': 'User registered successfully. Please verify your email with the OTP sent.',
                'data': {
                    'user': UserSerializer(user).data,
                    'verification_required': {
                        'email': True,
                    },
                    'email_sent': email_sent,
                    'expires_in_minutes': otp_expiry_minutes,
                }
            }
            
            # Include OTP in response only in DEBUG mode for testing
            if settings.DEBUG:
                response_data['data']['test_otp'] = email_otp_code
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        # return Response(
        #     {
        #         'success': False,
        #         'errors': serializer.errors
        #     },
        #     status=status.HTTP_400_BAD_REQUEST
        # )
        return Response({
            'success': False,
            'message': 'Registration failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint for user login with enhanced security.
    
    Features:
    - Dynamic login via single 'identifier' field (auto-detects email/username/user_code/phone)
    - Progressive lockout after failed attempts (2min, 5min, 10min, 30min, 60min, block)
    - Returns app_access and feature_access arrays
    - Session inactivity timeout (30 minutes like bank apps)
    - Rate limiting: 10 login attempts per minute per IP
    
    POST /api/auth-user/login/
    Request body: {"identifier": "email/username/user_code/phone", "password": "..."}
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Skip authentication for login endpoint
    throttle_classes = []  # Using custom throttle below
    
    def get_throttles(self):
        """Apply login rate throttle."""
        from .throttling import LoginRateThrottle
        return [LoginRateThrottle()]
    
    def _detect_identifier_type(self, identifier):
        """Auto-detect the type of identifier provided."""
        import re
        identifier = str(identifier).strip()
        
        # Check if it's an email (contains @)
        if '@' in identifier:
            return 'EMAIL', identifier.lower()
        
        # Check if it's a phone number (starts with + or is mostly digits)
        if identifier.startswith('+') or re.match(r'^[\d\s\-\(\)]+$', identifier):
            normalized = re.sub(r'[\s\-\(\)]', '', identifier)
            if len(normalized) >= 10:
                return 'PHONE', identifier
        
        # Check if it's a user_code (exactly 6 alphanumeric characters)
        if re.match(r'^[A-Za-z0-9]{6}$', identifier):
            return 'USER_CODE', identifier.upper()
        
        # Default to username
        return 'USERNAME', identifier
    
    def post(self, request):
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Get identifier from the single 'identifier' field
        identifier_input = request.data.get('identifier', '')
        identifier = None
        identifier_type = None
        
        if identifier_input:
            identifier_type, identifier = self._detect_identifier_type(identifier_input)
        
        # Check for lockout if we have an identifier
        login_attempt = None
        if identifier and identifier_type:
            login_attempt = LoginAttempt.get_or_create_for_identifier(
                identifier=identifier,
                identifier_type=identifier_type,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            is_locked, lockout_message = login_attempt.is_locked_out()
            if is_locked:
                return Response({
                    'success': False,
                    'message': lockout_message,
                    'errors': {
                        'non_field_errors': [lockout_message]
                    },
                    'data': {
                        'is_locked': True,
                        'lockout_stage': login_attempt.lockout_stage,
                        'is_blocked': login_attempt.is_blocked,
                    }
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Validate credentials
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Record failed attempt if we have an identifier
            if identifier and identifier_type and login_attempt:
                result = login_attempt.record_failed_attempt()
                
                # Check if user just got locked out
                is_locked, lockout_message = login_attempt.is_locked_out()
                if is_locked:
                    return Response({
                        'success': False,
                        'message': lockout_message,
                        'errors': serializer.errors,
                        'data': {
                            'is_locked': True,
                            'lockout_stage': result['lockout_stage'],
                            'is_blocked': result['is_blocked'],
                        }
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
                # Return with remaining attempts info
                remaining = result['remaining_attempts']
                return Response({
                    'success': False,
                    'message': f'Login failed. {remaining} attempt(s) remaining.',
                    'errors': serializer.errors,
                    'data': {
                        'remaining_attempts': remaining,
                        'lockout_stage': result['lockout_stage'],
                        'is_locked': False,
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            return Response({
                'success': False,
                'message': 'Login failed.',
                'errors': serializer.errors,
                'data': {
                    'remaining_attempts': 5,
                    'lockout_stage': 0,
                    'is_locked': False,
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = serializer.validated_data['user']
        
        # Record successful login
        if identifier and identifier_type and login_attempt:
            login_attempt.record_successful_login(user=user)
        
        # Update last login
        user.update_last_login()
        
        # Generate tokens (now includes permissions)
        tokens = JWTManager.generate_tokens(user)
        
        # Invalidate all previous active sessions (single session login)
        # This ensures user can only be logged in from one device at a time
        previous_sessions = UserSession.objects.filter(user=user, is_active=True)
        previous_sessions_count = previous_sessions.count()
        previous_sessions.update(is_active=False)
        
        # Create session with activity tracking
        session = UserSession.objects.create(
            user=user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Get app and feature access for response
        app_access, feature_access = JWTManager.get_user_permissions(user)
        
        # Check if user has any access (empty dashboard logic)
        has_access = bool(app_access) or bool(feature_access)
        access_message = None
        if not has_access:
            access_message = 'No applications or features have been assigned to your account. Please contact your administrator for access.'
        
        # Get KYC status
        kyc_status = None
        if hasattr(user, 'kyc_application'):
            kyc_app = user.kyc_application
            kyc_status = {
                'status': kyc_app.status,
                'application_id': kyc_app.application_id,
                'current_step': kyc_app.current_step,
                'mega_step': kyc_app.mega_step,
                'completion_percentage': kyc_app.completion_percentage,
            }
        else:
            kyc_status = {
                'status': 'NOT_STARTED',
                'application_id': None,
                'current_step': 0,
                'mega_step': None,
                'completion_percentage': 0,
            }
        
        return Response({
            'success': True,
            'message': 'Login successful.',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                },
                # Permission arrays for frontend
                'app_access': app_access,
                'feature_access': feature_access,
                # Access status for empty dashboard handling
                'access_status': {
                    'has_access': has_access,
                    'message': access_message,
                },
                # KYC status for redirect decision
                'kyc_status': kyc_status,
                # Session info
                'session': {
                    'session_id': session.token_id,
                    'expires_at': tokens['refresh_token_expiry'].isoformat(),
                    'inactivity_timeout_minutes': JWTManager.get_inactivity_timeout(),
                }
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    API endpoint for user logout
    POST /api/auth-user/logout/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Get token ID from auth payload
        token_payload = request.auth
        
        # Invalidate all active sessions for user (logout from all devices)
        logout_all = request.data.get('logout_all', False)
        
        if logout_all:
            UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
            message = 'Logged out from all devices successfully.'
        else:
            # Try to invalidate session for the provided refresh token (preferred)
            refresh_token = request.data.get('refresh_token')
            invalidated = False

            if refresh_token:
                payload = JWTManager.verify_token(refresh_token, token_type='refresh')
                if payload:
                    token_id = payload.get('jti')
                    try:
                        session = UserSession.objects.get(token_id=token_id, user=request.user, is_active=True)
                        session.invalidate()
                        invalidated = True
                    except UserSession.DoesNotExist:
                        invalidated = False

            # If no refresh token provided or not invalidated, try to use current token payload
            if not invalidated and token_payload:
                # If the current token is a refresh token, it will contain 'jti'
                token_type = token_payload.get('token_type')
                token_id = token_payload.get('jti')
                if token_type == 'refresh' and token_id:
                    try:
                        session = UserSession.objects.get(token_id=token_id, user=request.user, is_active=True)
                        session.invalidate()
                        invalidated = True
                    except UserSession.DoesNotExist:
                        invalidated = False

            # Respond based on whether we actually invalidated a session
            if invalidated:
                message = 'Logged out successfully.'
            else:
                # Idempotent: return success even if session was already invalid or token not provided
                message = 'Logged out successfully.'
        
        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    API endpoint for forgot password request
    Generates and sends a 6-digit OTP to email (and mobile if available)
    OTP is valid for 10 minutes
    
    POST /api/auth-user/forgot-password/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check if user exists
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Generate 6-digit OTP
                otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                
                # Store OTP with timestamp
                user.password_reset_otp = otp_code
                user.password_reset_otp_created_at = timezone.now()
                user.password_reset_otp_attempt_count = 0
                user.save(update_fields=['password_reset_otp', 'password_reset_otp_created_at', 'password_reset_otp_attempt_count'])
                
                # Send OTP to email
                try:
                    from .email_service import send_password_reset_otp_email
                    # Build a safe user_name fallback
                    user_name = getattr(user, 'full_name', '') or f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or getattr(user, 'username', user.email)
                    email_sent = send_password_reset_otp_email(
                        email=user.email,
                        otp_code=otp_code,
                        user_name=user_name
                    )
                    if not email_sent:
                        logger.warning(f"Password reset OTP email failed to send to {user.email}")
                except Exception as e:
                    logger.error(f"Error sending password reset OTP email: {str(e)}")
                
                # TODO: Send OTP to mobile if phone_number exists
                # if user.phone_number:
                #     send_sms_otp(user.phone_number, otp_code)
                
                response_data = {
                    'success': True,
                    'message': 'Password reset OTP has been sent to your email.',
                    'data': {
                        'email': user.email,
                        'expires_in_minutes': 10
                    }
                }
                
                # Include OTP in DEBUG mode for testing
                if settings.DEBUG:
                    response_data['data']['debug_otp'] = otp_code
                
                return Response(response_data, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # Return 404 if email doesn't exist
                return Response({
                    'success': False,
                    'message': 'Email not found. Please check your email address.',
                    'error': 'EMAIL_NOT_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'message': 'Invalid request.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """
    API endpoint for password reset with OTP
    POST /api/auth-user/reset-password/
    
    Request body:
    {
        "email": "user@example.com",
        "otp_code": "123456",
        "new_password": "NewSecurePass123",
        "confirm_password": "NewSecurePass123"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.user
            new_password = serializer.validated_data['new_password']
            
            with transaction.atomic():
                # Update password
                user.set_password(new_password)
                
                # Clear OTP after successful reset
                user.password_reset_otp = None
                user.password_reset_otp_created_at = None
                user.password_reset_otp_attempt_count = 0
                
                user.save()
                
                # Invalidate all existing sessions
                UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
            # Send password reset confirmation email
            try:
                from .email_service import send_password_reset_confirmation_email
                user_name = getattr(user, 'full_name', '') or f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or getattr(user, 'username', user.email)
                send_password_reset_confirmation_email(
                    email=user.email,
                    user_name=user_name
                )
            except Exception as e:
                logger.error(f"Error sending password reset confirmation email: {str(e)}")
            
            return Response({
                'success': True,
                'message': 'Password reset successful. Please login with your new password.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Password reset failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API endpoint for changing password (authenticated users)
    POST /api/auth-user/change-password/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            
            # Verify current password
            if not user.check_password(current_password):
                return Response({
                    'success': False,
                    'message': 'Current password is incorrect.',
                    'errors': {'current_password': ['Current password is incorrect.']}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Optionally invalidate other sessions
            logout_others = request.data.get('logout_others', False)
            if logout_others:
                UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
            return Response({
                'success': True,
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Password change failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# NEW PASSWORD RESET FLOW VIEWS
# =============================================================================

class VerifyForgotPasswordOTPView(APIView):
    """
    API endpoint to verify OTP during forgot password flow (FLOW A - Unauthenticated).
    After successful OTP verification, returns a short-lived reset_token.
    
    POST /api/auth-user/verify-forgot-password-otp/
    Body:
    {
        "email": "user@example.com",
        "otp_code": "123456"
    }
    
    Response:
    {
        "success": true,
        "message": "OTP verified successfully",
        "data": {
            "reset_token": "abc123...",
            "expires_in_minutes": 15
        }
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyForgotPasswordOTPSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.user
            
            # Generate reset_token (15 minutes validity)
            reset_token_obj = PasswordResetToken.create_token(user, expiry_hours=0.25)  # 15 minutes
            
            # Clear OTP after successful verification
            user.password_reset_otp = None
            user.password_reset_otp_created_at = None
            user.password_reset_otp_attempt_count = 0
            user.save(update_fields=['password_reset_otp', 'password_reset_otp_created_at', 'password_reset_otp_attempt_count'])
            
            return Response({
                'success': True,
                'message': 'OTP verified successfully. Use the reset_token to set your new password.',
                'data': {
                    'reset_token': reset_token_obj.token,
                    'expires_in_minutes': 15
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'OTP verification failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordWithTokenView(APIView):
    """
    API endpoint to reset password using reset_token (FLOW A - Unauthenticated).
    This endpoint does not require authentication, only a valid reset_token.
    
    POST /api/auth-user/reset-password-with-token/
    Body:
    {
        "reset_token": "abc123...",
        "new_password": "NewSecure@123",
        "confirm_password": "NewSecure@123"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordWithTokenSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.user
            token_obj = serializer.token_obj
            new_password = serializer.validated_data['new_password']
            
            with transaction.atomic():
                # Update password
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                token_obj.mark_as_used()
                
                # Invalidate all existing sessions for security
                UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
            # Send password reset confirmation email
            try:
                from .email_service import send_password_reset_confirmation_email
                user_name = user.full_name or user.email.split('@')[0]
                send_password_reset_confirmation_email(
                    email=user.email,
                    user_name=user_name
                )
            except Exception as e:
                logger.error(f"Error sending password reset confirmation email: {str(e)}")
            
            return Response({
                'success': True,
                'message': 'Password reset successful. Please login with your new password.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Password reset failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProfileSendOTPView(APIView):
    """
    API endpoint to send OTP for authenticated profile actions (FLOW B - Authenticated).
    Used for sensitive operations like password change from profile.
    
    POST /api/auth-user/profile/send-otp/
    Headers: Authorization: Bearer <access_token>
    Body:
    {
        "action_type": "PASSWORD_CHANGE"  // or "PROFILE_UPDATE"
    }
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ProfileSendOTPSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            action_type = serializer.validated_data.get('action_type', 'PASSWORD_CHANGE')
            
            # Generate 6-digit OTP
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store OTP with timestamp (shorter expiry for profile actions: 5 minutes)
            user.password_reset_otp = otp_code
            user.password_reset_otp_created_at = timezone.now()
            user.password_reset_otp_attempt_count = 0
            user.save(update_fields=['password_reset_otp', 'password_reset_otp_created_at', 'password_reset_otp_attempt_count'])
            
            # Send OTP to email
            try:
                from .email_service import send_password_reset_otp_email
                user_name = user.full_name or user.email.split('@')[0]
                email_sent = send_password_reset_otp_email(
                    email=user.email,
                    otp_code=otp_code,
                    user_name=user_name
                )
                if not email_sent:
                    logger.warning(f"Profile OTP email failed to send to {user.email}")
            except Exception as e:
                logger.error(f"Error sending profile OTP email: {str(e)}")
            
            response_data = {
                'success': True,
                'message': f'OTP has been sent to your email for {action_type.replace("_", " ").lower()}.',
                'data': {
                    'email': user.email,
                    'action_type': action_type,
                    'expires_in_minutes': 5
                }
            }
            
            # Include OTP in DEBUG mode for testing
            if settings.DEBUG:
                response_data['data']['debug_otp'] = otp_code
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Failed to send OTP.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProfileVerifyOTPView(APIView):
    """
    API endpoint to verify OTP for authenticated profile actions (FLOW B - Authenticated).
    
    POST /api/auth-user/profile/verify-otp/
    Headers: Authorization: Bearer <access_token>
    Body:
    {
        "otp_code": "123456",
        "action_type": "PASSWORD_CHANGE"
    }
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ProfileVerifyOTPSerializer(data=request.data, context={'user': request.user})
        
        if serializer.is_valid():
            # OTP is valid, user can proceed with the action
            # Note: We keep the OTP active for a short time so user can complete the action
            
            return Response({
                'success': True,
                'message': 'OTP verified successfully. You can now proceed with the action.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'OTP verification failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProfileChangePasswordView(APIView):
    """
    API endpoint to change password from profile after OTP verification (FLOW B - Authenticated).
    Requires prior OTP verification via ProfileVerifyOTPView.
    
    POST /api/auth-user/profile/change-password/
    Headers: Authorization: Bearer <access_token>
    Body:
    {
        "new_password": "NewSecure@123",
        "confirm_password": "NewSecure@123"
    }
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ProfileChangePasswordSerializer(data=request.data, context={'user': request.user})
        
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data['new_password']
            
            with transaction.atomic():
                # Update password
                user.set_password(new_password)
                
                # Clear OTP after successful password change
                user.password_reset_otp = None
                user.password_reset_otp_created_at = None
                user.password_reset_otp_attempt_count = 0
                
                user.save()
                
                # Optionally invalidate other sessions (keep current session)
                # UserSession.objects.filter(user=user, is_active=True).exclude(token_id=request.auth.get('jti')).update(is_active=False)
            
            # Send password change confirmation email
            try:
                from .email_service import send_password_reset_confirmation_email
                user_name = user.full_name or user.email.split('@')[0]
                send_password_reset_confirmation_email(
                    email=user.email,
                    user_name=user_name
                )
            except Exception as e:
                logger.error(f"Error sending password change confirmation email: {str(e)}")
            
            return Response({
                'success': True,
                'message': 'Password changed successfully from profile.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Password change failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# END OF NEW PASSWORD RESET FLOW
# =============================================================================


class RefreshTokenView(APIView):
    """
    API endpoint for refreshing access token
    POST /api/auth-user/refresh-token/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        
        if serializer.is_valid():
            refresh_token = serializer.validated_data['refresh_token']
            
            # Try to refresh access token
            result = JWTManager.refresh_access_token(refresh_token)
            
            if result:
                return Response({
                    'success': True,
                    'message': 'Token refreshed successfully.',
                    'data': {
                        'access_token': result['access_token']
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'message': 'Invalid or expired refresh token.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'message': 'Invalid request.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API endpoint for getting and updating current user profile
    GET /api/auth-user/profile/
    PUT /api/auth-user/profile/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile"""
        return Response({
            'success': True,
            'data': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Update current user profile"""
        serializer = UserUpdateSerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            user = serializer.update(request.user, serializer.validated_data)
            return Response({
                'success': True,
                'message': 'Profile updated successfully.',
                'data': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Profile update failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """Partial update current user profile"""
        return self.put(request)


class UserListView(APIView):
    """
    API endpoint for listing all users (admin only in production)
    GET /api/auth-user/users/
    
    Query params:
    - is_active: Filter by active status (true/false)
    - is_deleted: Filter by deleted status (true/false) - default is false
    - include_deleted: Include deleted users in results (true/false)
    - search: Search by email, username, first_name, last_name
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all users"""
        # Start with all users
        users = User.objects.all()
        
        # By default, exclude soft-deleted users unless include_deleted=true
        include_deleted = request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            users = users.filter(is_deleted=False)
        
        # Optional: filter by is_deleted specifically
        is_deleted = request.query_params.get('is_deleted')
        if is_deleted is not None:
            is_deleted = is_deleted.lower() == 'true'
            users = users.filter(is_deleted=is_deleted)
        
        # Optional: filter by is_active
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            users = users.filter(is_active=is_active)
        
        # Search by email or username
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            users = users.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(user_code__icontains=search)
            )
        
        return Response({
            'success': True,
            'data': UserListSerializer(users, many=True).data,
            'count': users.count()
        }, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    """
    API endpoint for getting, updating, and deleting a specific user
    GET /api/auth-user/users/<id>/
    PUT /api/auth-user/users/<id>/
    DELETE /api/auth-user/users/<id>/ - Soft delete (sets is_deleted=True)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_user(self, user_id):
        """Get user by ID (exclude soft deleted users)"""
        try:
            return User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            return None
    
    def get(self, request, user_id):
        """Get user details"""
        user = self.get_user(user_id)
        if not user:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    def put(self, request, user_id):
        """Update user"""
        user = self.get_user(user_id)
        if not user:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserUpdateSerializer(
            data=request.data,
            context={'user': user}
        )
        
        if serializer.is_valid():
            updated_user = serializer.update(user, serializer.validated_data)
            return Response({
                'success': True,
                'message': 'User updated successfully.',
                'data': UserSerializer(updated_user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'User update failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, user_id):
        """Partial update user"""
        return self.put(request, user_id)
    
    def delete(self, request, user_id):
        """
        Soft Delete user - Sets is_deleted=True and is_active=False
        User data remains in database but is marked as deleted
        """
        user = self.get_user(user_id)
        if not user:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response({
                'success': False,
                'message': 'You cannot delete your own account.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete - mark as deleted
        user.is_deleted = True
        user.is_active = False
        user.deleted_at = timezone.now()
        user.save()
        
        # Invalidate all sessions
        UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
        
        return Response({
            'success': True,
            'message': 'User soft deleted successfully.',
            'data': {
                'id': user.id,
                'email': user.email,
                'is_deleted': user.is_deleted,
                'deleted_at': user.deleted_at.isoformat() if user.deleted_at else None
            }
        }, status=status.HTTP_200_OK)


class UserHardDeleteView(APIView):
    """
    API endpoint for permanently deleting a user from database
    DELETE /api/auth-user/users/<id>/hard-delete/
    
    WARNING: This permanently removes the user and all related data.
    This action cannot be undone.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, user_id):
        """
        Hard Delete user - Permanently removes from database
        """
        try:
            # Include soft-deleted users for hard delete
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response({
                'success': False,
                'message': 'You cannot delete your own account.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store user info before deletion
        user_info = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'user_code': user.user_code
        }
        
        # Hard delete - permanently remove from database
        user.delete()
        
        return Response({
            'success': True,
            'message': 'User permanently deleted.',
            'data': user_info
        }, status=status.HTTP_200_OK)


class UserRestoreView(APIView):
    """
    API endpoint for restoring a soft-deleted user
    POST /api/auth-user/users/<id>/restore/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        """Restore a soft-deleted user"""
        try:
            user = User.objects.get(id=user_id, is_deleted=True)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Deleted user not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Restore user
        user.is_deleted = False
        user.is_active = True
        user.deleted_at = None
        user.save()
        
        return Response({
            'success': True,
            'message': 'User restored successfully.',
            'data': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class UserActivateView(APIView):
    """
    API endpoint for activating/deactivating a user
    POST /api/auth-user/users/<id>/activate/
    POST /api/auth-user/users/<id>/deactivate/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id, action):
        """Activate or deactivate user"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if action == 'activate':
            user.is_active = True
            user.save()
            message = 'User activated successfully.'
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            # Invalidate all sessions
            UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            message = 'User deactivated successfully.'
        else:
            return Response({
                'success': False,
                'message': 'Invalid action.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': message,
            'data': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


# =============================================================================
# OTP VERIFICATION ENDPOINTS FOR REGISTRATION
# =============================================================================

class VerifyRegistrationOTPView(APIView):
    """
    API endpoint for verifying email OTP during registration.
    
    Once email is verified, user can login.
    
    POST /api/auth-user/verify-registration-otp/
    
    Request body:
    {
        "email": "john@example.com",
        "otp_code": "123456"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Verify email OTP during registration.
        
        Logic:
        1. Find unverified user by email
        2. Validate OTP matches and is not expired (10 minutes)
        3. Mark user as is_email_verified=True
        4. Clear OTP after successful verification
        5. Return success response
        """
        email = request.data.get('email', '').lower()
        otp_code = request.data.get('otp_code', '').strip()
        
        # Validate required fields
        if not email or not otp_code:
            return Response({
                'success': False,
                'message': 'Email and OTP code are required.',
                'errors': {
                    'email': ['This field is required.'] if not email else [],
                    'otp_code': ['This field is required.'] if not otp_code else [],
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find unverified user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # If already verified, return error
        if user.is_email_verified:
            return Response({
                'success': False,
                'message': 'Email is already verified.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if OTP exists
        if not user.email_otp:
            return Response({
                'success': False,
                'message': 'No OTP found. Please request a new OTP.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check OTP expiry (default: 10 minutes)
        otp_expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        if user.email_otp_created_at:
            expiry_time = user.email_otp_created_at + timezone.timedelta(minutes=otp_expiry_minutes)
            if timezone.now() > expiry_time:
                return Response({
                    'success': False,
                    'message': f'OTP has expired. Please request a new OTP (valid for {otp_expiry_minutes} minutes).',
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Increment attempt counter to prevent brute force
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
        user.email_otp_attempt_count = (user.email_otp_attempt_count or 0) + 1
        
        # Check if max attempts exceeded
        if user.email_otp_attempt_count > max_attempts:
            user.save(update_fields=['email_otp_attempt_count'])
            return Response({
                'success': False,
                'message': f'Maximum OTP verification attempts ({max_attempts}) exceeded. Please request a new OTP.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Validate OTP code
        if user.email_otp != otp_code:
            user.save(update_fields=['email_otp_attempt_count'])
            remaining_attempts = max_attempts - user.email_otp_attempt_count
            return Response({
                'success': False,
                'message': f'Invalid OTP code. {remaining_attempts} attempts remaining.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # OTP is valid! Mark user as verified
        user.is_email_verified = True
        user.email_verified_at = timezone.now()
        user.is_verified = True  # Email verification is the only requirement now
        
        # Clear OTP after successful verification (security best practice)
        user.email_otp = None
        user.email_otp_created_at = None
        user.email_otp_attempt_count = 0
        
        user.save()
        
        return Response({
            'success': True,
            'message': 'Email verified successfully. You can now login.',
            'data': {
                'user': UserSerializer(user).data,
                'is_email_verified': user.is_email_verified,
                'verified_at': user.email_verified_at.isoformat() if user.email_verified_at else None,
            }
        }, status=status.HTTP_200_OK)


class ResendRegistrationOTPView(APIView):
    """
    API endpoint for resending email OTP during registration.
    
    If user exists but is NOT verified:
    - Regenerate OTP
    - Send OTP to email
    - Reset attempt counter
    
    POST /api/auth-user/resend-registration-otp/
    
    Request body:
    {
        "email": "john@example.com"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = []  # Can add throttle to prevent OTP spam
    
    def post(self, request):
        """
        Resend email OTP.
        
        Logic:
        1. Find user by email
        2. Check if already verified (if yes, return error)
        3. Generate new OTP and store in User model
        4. Send OTP via email
        5. Return success with OTP expiry time
        """
        import random
        from .email_service import send_otp_email
        
        email = request.data.get('email', '').lower()
        
        # Validate required fields
        if not email:
            return Response({
                'success': False,
                'message': 'Email is required.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already verified
        if user.is_email_verified:
            return Response({
                'success': False,
                'message': 'Email is already verified. You can login now.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get OTP settings
        otp_length = getattr(settings, 'OTP_LENGTH', 6)
        otp_expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        max_resend_attempts = getattr(settings, 'OTP_RESEND_MAX_ATTEMPTS', 5)
        
        # Track resend attempts (optional: add resend_count field to User if needed)
        # For now, we'll just generate and send
        
        # Generate new OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(otp_length)])
        
        # Update user with new OTP
        user.email_otp = otp_code
        user.email_otp_created_at = timezone.now()
        user.email_otp_attempt_count = 0  # Reset attempts on resend
        user.save(update_fields=['email_otp', 'email_otp_created_at', 'email_otp_attempt_count'])
        
        # Send OTP via email
        user_name = user.first_name or user.email.split('@')[0]
        email_sent = send_otp_email(
            email=user.email,
            otp_code=otp_code,
            user_name=user_name
        )
        
        response_data = {
            'success': True,
            'message': 'OTP has been resent to your email.',
            'data': {
                'email': user.email,
                'email_sent': email_sent,
                'expires_in_minutes': otp_expiry_minutes,
            }
        }
        
        # Include OTP in response only in DEBUG mode for testing
        if settings.DEBUG:
            response_data['data']['test_otp'] = otp_code
        
        return Response(response_data, status=status.HTTP_200_OK)


class ResendPasswordResetOTPView(APIView):
    """
    API endpoint for resending password reset OTP.
    
    POST /api/auth-user/resend-password-reset-otp/
    
    Request body:
    {
        "email": "user@example.com"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = []
    
    def post(self, request):
        """
        Resend password reset OTP.
        
        Logic:
        1. Find user by email
        2. Generate new OTP
        3. Store OTP with timestamp
        4. Send OTP via email (and mobile if available)
        5. Return success with OTP expiry time
        """
        from .email_service import send_password_reset_otp_email
        
        email = request.data.get('email', '').lower()
        
        # Validate required fields
        if not email:
            return Response({
                'success': False,
                'message': 'Email is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user by email
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Return success to prevent email enumeration
            return Response({
                'success': True,
                'message': 'If an account with this email exists, a new OTP has been sent.'
            }, status=status.HTTP_200_OK)
        
        # Generate new OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Update user with new OTP
        user.password_reset_otp = otp_code
        user.password_reset_otp_created_at = timezone.now()
        user.password_reset_otp_attempt_count = 0  # Reset attempts on resend
        user.save(update_fields=['password_reset_otp', 'password_reset_otp_created_at', 'password_reset_otp_attempt_count'])
        
        # Send OTP via email
        user_name = getattr(user, 'full_name', '') or f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or getattr(user, 'username', user.email)
        email_sent = send_password_reset_otp_email(
            email=user.email,
            otp_code=otp_code,
            user_name=user_name
        )
        
        # TODO: Send OTP to mobile if phone_number exists
        # if user.phone_number:
        #     send_sms_otp(user.phone_number, otp_code)
        
        response_data = {
            'success': True,
            'message': 'Password reset OTP has been resent to your email.',
            'data': {
                'email': user.email,
                'email_sent': email_sent,
                'expires_in_minutes': 10,
            }
        }
        
        # Include OTP in response only in DEBUG mode for testing
        if settings.DEBUG:
            response_data['data']['test_otp'] = otp_code
        
        return Response(response_data, status=status.HTTP_200_OK)


# =============================================================================
# USER ACTIVITY LOG ENDPOINTS
# =============================================================================

class UserActivityLogListView(APIView):
    """
    API endpoint to get user activity logs.
    
    SP/Developer can view all user logs.
    Admin can view logs for users below their level.
    Users can view their own logs.
    
    GET /api/auth-user/activity-logs/
    GET /api/auth-user/activity-logs/?user_id=123
    GET /api/auth-user/activity-logs/?activity_type=LOGIN
    GET /api/auth-user/activity-logs/?start_date=2024-01-01&end_date=2024-12-31
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import UserActivityLog
        from .serializers import UserActivityLogSerializer
        
        user_id = request.query_params.get('user_id')
        activity_type = request.query_params.get('activity_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        limit = int(request.query_params.get('limit', 100))
        
        # Determine what logs to show
        if user_id:
            # Check permissions to view other user's logs
            if request.user.user_role not in ['DEVELOPER', 'SUPER_ADMIN', 'ADMIN']:
                # Regular users can only view their own logs
                if str(request.user.id) != str(user_id):
                    return Response({
                        'success': False,
                        'message': 'You can only view your own activity logs.',
                    }, status=status.HTTP_403_FORBIDDEN)
            
            logs = UserActivityLog.objects.filter(user_id=user_id)
        elif request.user.user_role in ['DEVELOPER', 'SUPER_ADMIN']:
            # SP/Developer can view all logs
            logs = UserActivityLog.objects.all()
        else:
            # Others can only view their own logs
            logs = UserActivityLog.objects.filter(user=request.user)
        
        # Apply filters
        if activity_type:
            logs = logs.filter(activity_type=activity_type.upper())
        
        if start_date:
            logs = logs.filter(created_at__date__gte=start_date)
        
        if end_date:
            logs = logs.filter(created_at__date__lte=end_date)
        
        logs = logs.order_by('-created_at')[:limit]
        
        serializer = UserActivityLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'message': 'Activity logs retrieved successfully.',
            'data': {
                'logs': serializer.data,
                'count': len(serializer.data),
            }
        }, status=status.HTTP_200_OK)


class MyActivityLogView(APIView):
    """
    API endpoint to get current user's activity logs.
    
    GET /api/auth-user/my-activity/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import UserActivityLog
        from .serializers import UserActivityLogSerializer
        
        activity_type = request.query_params.get('activity_type')
        limit = int(request.query_params.get('limit', 50))
        
        logs = UserActivityLog.objects.filter(user=request.user)
        
        if activity_type:
            logs = logs.filter(activity_type=activity_type.upper())
        
        logs = logs.order_by('-created_at')[:limit]
        
        serializer = UserActivityLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'message': 'Your activity logs retrieved successfully.',
            'data': {
                'logs': serializer.data,
                'count': len(serializer.data),
            }
        }, status=status.HTTP_200_OK)


# =============================================================================
# USER PROFILE WITH KYC STATUS AND ACCESS
# =============================================================================

class UserProfileWithAccessView(APIView):
    """
    API endpoint to get comprehensive user profile with:
    - User details
    - KYC status
    - App/Feature access
    - Role information
    
    GET /api/auth-user/profile-full/
    
    Can also update profile:
    PATCH /api/auth-user/profile-full/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Build profile data
        profile_data = {
            'id': user.id,
            'user_code': user.user_code,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'middle_name': getattr(user, 'middle_name', None),
            'last_name': user.last_name,
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'user_role': user.user_role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'is_email_verified': getattr(user, 'is_email_verified', False),
            'is_phone_verified': getattr(user, 'is_phone_verified', False),
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        
        # Get KYC status
        kyc_status = None
        try:
            from kyc_verification.models import KYCApplication
            kyc_app = KYCApplication.objects.get(user=user, is_deleted=False)
            kyc_status = {
                'application_id': kyc_app.application_id,
                'status': kyc_app.status,
                'mega_step': kyc_app.mega_step,
                'current_step': kyc_app.current_step,
                'total_steps': kyc_app.total_steps,
                'completion_percentage': kyc_app.completion_percentage,
                'submitted_at': kyc_app.submitted_at.isoformat() if kyc_app.submitted_at else None,
                'reviewed_at': kyc_app.reviewed_at.isoformat() if kyc_app.reviewed_at else None,
                'approved_at': kyc_app.approved_at.isoformat() if kyc_app.approved_at else None,
                'is_email_verified': kyc_app.is_email_verified,
                'is_phone_verified': kyc_app.is_phone_verified,
                'review_remarks': kyc_app.review_remarks,
                'rejection_reason': kyc_app.rejection_reason,
            }
        except:
            kyc_status = {
                'status': 'NOT_STARTED',
                'message': 'KYC not yet initiated'
            }
        
        # Get app and feature access
        app_access = []
        feature_access = []
        
        try:
            from rbac.models import UserRoleAssignment, RoleAppMapping, RoleFeatureMapping
            
            # Get user's active role assignments
            role_assignments = UserRoleAssignment.objects.filter(
                user=user,
                is_active=True
            ).select_related('role')
            
            for assignment in role_assignments:
                role = assignment.role
                
                # Get app access
                app_mappings = RoleAppMapping.objects.filter(
                    role=role,
                    is_active=True
                ).select_related('app')
                
                for mapping in app_mappings:
                    app_data = {
                        'app_id': mapping.app.id,
                        'app_code': mapping.app.code,
                        'app_name': mapping.app.name,
                        'can_view': mapping.can_view,
                        'can_create': mapping.can_create,
                        'can_update': mapping.can_update,
                        'can_delete': mapping.can_delete,
                    }
                    if app_data not in app_access:
                        app_access.append(app_data)
                
                # Get feature access
                feature_mappings = RoleFeatureMapping.objects.filter(
                    role=role,
                    is_active=True
                ).select_related('feature', 'feature__app')
                
                for mapping in feature_mappings:
                    feature_data = {
                        'feature_id': mapping.feature.id,
                        'feature_code': mapping.feature.code,
                        'feature_name': mapping.feature.name,
                        'app_code': mapping.feature.app.code,
                        'can_execute': mapping.can_execute,
                        'can_view': mapping.can_view,
                        'can_edit': mapping.can_edit,
                    }
                    if feature_data not in feature_access:
                        feature_access.append(feature_data)
        except:
            pass
        
        # Add to profile
        profile_data['kyc_status'] = kyc_status
        profile_data['app_access'] = app_access
        profile_data['feature_access'] = feature_access
        
        return Response({
            'success': True,
            'message': 'Profile retrieved successfully.',
            'data': profile_data
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """Update user profile"""
        user = request.user
        
        # Fields that can be updated
        allowed_fields = ['first_name', 'middle_name', 'last_name', 'username']
        
        updated_fields = []
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
                updated_fields.append(field)
        
        if updated_fields:
            user.save(update_fields=updated_fields + ['updated_at'])
            
            # Log activity
            from .models import UserActivityLog
            UserActivityLog.log_activity(
                user=user,
                activity_type=UserActivityLog.ActivityType.PROFILE_UPDATE,
                action='Profile updated',
                description=f'Updated fields: {", ".join(updated_fields)}',
                entity_type='User',
                entity_id=user.id,
                request=request
            )
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully.',
            'data': {
                'updated_fields': updated_fields,
                'user': UserSerializer(user).data,
            }
        }, status=status.HTTP_200_OK)


class CreatePrivilegedUserView(APIView):
    """
    API endpoint for creating privileged users (Developer/Super Admin).
    
    This endpoint is INTENDED for SYSTEM SETUP and should be protected.
    It requires a 'secret_key' in the request body.
    
    POST /api/auth-user/system/create-privileged-user/
    
    Request Body:
    {
        "email": "dev@example.com",
        "username": "devuser",
        "first_name": "Dev",
        "last_name": "User",
        "password": "strongpassword",
        "confirm_password": "strongpassword",
        "role": "DEVELOPER" or "SUPER_ADMIN",
        "secret_key": "YOUR_SECRET_KEY"
    }
    """
    permission_classes = [AllowAny]
    throttle_classes = [] 
    
    def post(self, request):
        # Check for system setup secret key
        # In production, this should be validated against an environment variable
        # For this requirement, we will use a hardcoded check or env var
        import os
        creation_secret = os.getenv('PRIVILEGED_USER_CREATION_SECRET', 'credbuzz_setup_secret_2025')
        
        request_secret = request.data.get('secret_key')
        
        if request_secret != creation_secret:
            return Response({
                'success': False,
                'message': 'Unauthorized. Invalid secret key.'
            }, status=status.HTTP_403_FORBIDDEN)
            
        serializer = CreatePrivilegedUserSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'success': True,
                'message': f'{user.user_role} user created successfully.',
                'data': {
                    'user_code': user.user_code,
                    'email': user.email,
                    'username': user.username,
                    'role': user.user_role,
                    'created_at': user.created_at
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            'success': False,
            'message': 'User creation failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

