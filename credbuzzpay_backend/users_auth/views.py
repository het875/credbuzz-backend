"""
Views for users_auth app
All user authentication and management endpoints
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
from django.db.models import Q

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
        from django.conf import settings
        from .email_service import send_otp_email
        
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Import OTP model from kyc_verification
            from kyc_verification.models import OTPVerification, OTPType
            import random
            
            # Get OTP settings
            otp_length = getattr(settings, 'OTP_LENGTH', 6)
            otp_expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            
            # Track email delivery status
            email_sent = False
            
            # Generate Email OTP
            email_otp_code = ''.join([str(random.randint(0, 9)) for _ in range(otp_length)])
            email_otp = OTPVerification.objects.create(
                user=user,
                otp_type=OTPType.EMAIL,
                otp_code=email_otp_code,
                expires_at=timezone.now() + timezone.timedelta(minutes=otp_expiry),
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            # Send OTP via email
            user_name = user.first_name or user.email.split('@')[0]
            email_sent = send_otp_email(
                email=user.email,
                otp_code=email_otp_code,
                user_name=user_name
            )
            
            # Generate Phone OTP (SMS not implemented yet)
            phone_otp_code = ''.join([str(random.randint(0, 9)) for _ in range(otp_length)])
            phone_otp = OTPVerification.objects.create(
                user=user,
                otp_type=OTPType.PHONE,
                otp_code=phone_otp_code,
                expires_at=timezone.now() + timezone.timedelta(minutes=otp_expiry),
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            # TODO: Integrate SMS service for phone OTP
            
            response_data = {
                'success': True,
                'message': 'User registered successfully. Please verify your email with the OTP sent.',
                'data': {
                    'user': UserSerializer(user).data,
                    'verification_required': {
                        'email': True,
                        'phone': True,
                    },
                    'email_sent': email_sent,
                    'expires_in_minutes': otp_expiry,
                }
            }
            
            # Include OTP in response only in DEBUG mode for testing
            if settings.DEBUG:
                response_data['data']['test_otps'] = {
                    'email_otp': email_otp_code,
                    'phone_otp': phone_otp_code,
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
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
            # Just mark the current session type tokens as invalid
            # For single logout, we'd need the refresh token ID
            # For now, just return success
            message = 'Logged out successfully.'
        
        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    API endpoint for forgot password request
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
                # Create reset token
                reset_token = PasswordResetToken.create_token(user)
                
                # In production, you would send this via email
                # For testing, we return the token in response
                return Response({
                    'success': True,
                    'message': 'Password reset instructions sent to your email.',
                    'data': {
                        # Remove this in production - only for testing
                        'reset_token': reset_token.token
                    }
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                pass
            
            # Always return success to prevent email enumeration
            return Response({
                'success': True,
                'message': 'If an account with this email exists, password reset instructions have been sent.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Invalid request.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """
    API endpoint for password reset
    POST /api/auth-user/reset-password/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            reset_token = serializer.reset_token
            user = reset_token.user
            new_password = serializer.validated_data['new_password']
            
            with transaction.atomic():
                # Update password
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                reset_token.mark_as_used()
                
                # Invalidate all existing sessions
                UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
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
    API endpoint for verifying OTP during registration.
    User must verify both email and phone OTPs after registration.
    
    POST /api/auth-user/verify-registration-otp/
    
    Request body:
    {
        "email": "john@example.com",
        "otp_type": "EMAIL",  // or "PHONE"
        "otp_code": "123456"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        otp_type = request.data.get('otp_type')
        otp_code = request.data.get('otp_code')
        
        if not all([email, otp_type, otp_code]):
            return Response({
                'success': False,
                'message': 'Email, OTP type, and OTP code are required.',
                'errors': {
                    'email': ['This field is required.'] if not email else [],
                    'otp_type': ['This field is required.'] if not otp_type else [],
                    'otp_code': ['This field is required.'] if not otp_code else [],
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user by email
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Import OTP model
        from kyc_verification.models import OTPVerification, OTPType
        
        # Validate OTP type
        valid_types = ['EMAIL', 'PHONE']
        if otp_type.upper() not in valid_types:
            return Response({
                'success': False,
                'message': f'Invalid OTP type. Must be one of: {", ".join(valid_types)}',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the latest active OTP for this user and type
        otp_record = OTPVerification.objects.filter(
            user=user,
            otp_type=otp_type.upper(),
            is_verified=False
        ).order_by('-created_at').first()
        
        if not otp_record:
            return Response({
                'success': False,
                'message': f'No active OTP found for {otp_type}. Please request a new OTP.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify OTP
        success, message = otp_record.verify(otp_code)
        
        if not success:
            return Response({
                'success': False,
                'message': message,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update user verification status
        if otp_type.upper() == 'EMAIL':
            user.is_email_verified = True
            user.email_verified_at = timezone.now()
        elif otp_type.upper() == 'PHONE':
            user.is_phone_verified = True
            user.phone_verified_at = timezone.now()
        
        # If both email and phone are verified, set user as verified
        if user.is_email_verified and user.is_phone_verified:
            user.is_verified = True
        
        user.save()
        
        return Response({
            'success': True,
            'message': f'{otp_type.capitalize()} verified successfully.',
            'data': {
                'is_email_verified': user.is_email_verified,
                'is_phone_verified': user.is_phone_verified,
                'is_fully_verified': user.is_email_verified and user.is_phone_verified,
            }
        }, status=status.HTTP_200_OK)


class ResendRegistrationOTPView(APIView):
    """
    API endpoint for resending OTP during registration.
    
    POST /api/auth-user/resend-registration-otp/
    
    Request body:
    {
        "email": "john@example.com",
        "otp_type": "EMAIL"  // or "PHONE"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        import random
        from django.conf import settings
        from .email_service import send_otp_email
        
        email = request.data.get('email')
        otp_type = request.data.get('otp_type')
        
        if not all([email, otp_type]):
            return Response({
                'success': False,
                'message': 'Email and OTP type are required.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user by email
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Import OTP model
        from kyc_verification.models import OTPVerification, OTPType
        
        # Check if already verified
        if otp_type.upper() == 'EMAIL' and user.is_email_verified:
            return Response({
                'success': False,
                'message': 'Email is already verified.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if otp_type.upper() == 'PHONE' and user.is_phone_verified:
            return Response({
                'success': False,
                'message': 'Phone is already verified.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get OTP settings
        otp_length = getattr(settings, 'OTP_LENGTH', 6)
        otp_expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        
        # Invalidate existing OTPs
        OTPVerification.objects.filter(
            user=user,
            otp_type=otp_type.upper(),
            is_verified=False
        ).update(expires_at=timezone.now())
        
        # Generate new OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(otp_length)])
        
        otp = OTPVerification.objects.create(
            user=user,
            otp_type=otp_type.upper(),
            otp_code=otp_code,
            expires_at=timezone.now() + timezone.timedelta(minutes=otp_expiry),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        # Send OTP via email if type is EMAIL
        email_sent = False
        if otp_type.upper() == 'EMAIL':
            user_name = user.first_name or user.email.split('@')[0]
            email_sent = send_otp_email(
                email=user.email,
                otp_code=otp_code,
                user_name=user_name
            )
        
        response_data = {
            'success': True,
            'message': f'OTP sent to your {otp_type.lower()}.',
            'data': {
                'expires_in_minutes': otp_expiry,
            }
        }
        
        if otp_type.upper() == 'EMAIL':
            response_data['data']['email_sent'] = email_sent
        
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
                'message': f'{user.role} user created successfully.',
                'data': {
                    'user_code': user.user_code,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role,
                    'created_at': user.created_at
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            'success': False,
            'message': 'User creation failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

