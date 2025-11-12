"""
Authentication APIs for registration, login, and password management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from datetime import timedelta

from accounts.models import UserAccount, LoginActivity, SecuritySettings
from accounts.serializers import UserAccountSerializer, UserAccountDetailSerializer, LoginActivitySerializer
from accounts.utils.code_generator import generate_unique_user_code, generate_unique_id
from accounts.utils.security import (
    block_user, unblock_user, is_user_blocked, calculate_login_risk_score,
    get_device_info_from_user_agent
)
from accounts.services.otp_service import OTPService
from accounts.services.audit_service import log_user_action
from accounts.permissions import IsActiveUser, IsNotBlocked
from django.conf import settings


class AuthenticationViewSet(viewsets.ViewSet):
    """
    Authentication endpoints for registration, login, password management.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_initiate(self, request):
        """
        POST /api/v1/auth/register/initiate
        Initiate user registration with email, mobile, and password.
        """
        email = request.data.get('email')
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        
        # Validate input
        if not all([email, mobile, password]):
            return Response(
                {'error': 'Email, mobile, and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if UserAccount.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already registered.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if UserAccount.objects.filter(mobile=mobile).exists():
            return Response(
                {'error': 'Mobile number already registered.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            device_info = get_device_info_from_user_agent(
                request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Create user account
            user_code = generate_unique_user_code()
            user = UserAccount.objects.create(
                user_code=user_code,
                email=email,
                mobile=mobile,
                password=None,  # Will be set after OTP verification
                first_name='',
                last_name='',
                gender='other',
                dob=timezone.now().date(),
                register_device_ip=client_ip,
                register_device_info=device_info,
                registration_step=1,
                registration_data={'email': email, 'mobile': mobile, 'password': password}
            )
            
            # Generate OTPs
            otp_data = OTPService.generate_otp_record(
                user=user,
                otp_type='both',
                otp_purpose='registration',
                ip_address=client_ip,
                send_to_email=email,
                send_to_mobile=mobile
            )
            
            # Log audit
            log_user_action(
                action='registration',
                user_code=user,
                description=f'Registration initiated for {email}',
                ip_address=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'user_code': user_code,
                'otp_sent_to_email': True,
                'otp_sent_to_mobile': True,
                'registration_step': 1,
                'message': 'OTP sent to email and mobile. Please verify.'
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_verify_otp(self, request):
        """
        POST /api/v1/auth/register/verify-otp
        Verify email and mobile OTPs during registration.
        """
        user_code = request.data.get('user_code')
        email_otp = request.data.get('email_otp')
        mobile_otp = request.data.get('mobile_otp')
        
        if not all([user_code, email_otp, mobile_otp]):
            return Response(
                {'error': 'user_code, email_otp, and mobile_otp are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = UserAccount.objects.get(user_code=user_code)
            
            # Get latest OTP record
            otp_record = OTPService.get_latest_otp(user, 'registration')
            if not otp_record:
                return Response(
                    {'error': 'No OTP found. Please request a new OTP.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify email OTP
            email_valid, email_error = OTPService.verify_otp(otp_record, email_otp, 'email_otp')
            if not email_valid:
                return Response(
                    {'error': f'Email OTP verification failed: {email_error}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify mobile OTP
            mobile_valid, mobile_error = OTPService.verify_otp(otp_record, mobile_otp, 'mobile_otp')
            if not mobile_valid:
                return Response(
                    {'error': f'Mobile OTP verification failed: {mobile_error}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark OTP as used
            OTPService.mark_otp_as_used(otp_record)
            
            # Update user
            user.is_email_verified = True
            user.is_mobile_verified = True
            user.is_active = True
            user.registration_step = 2
            user.save()
            
            return Response({
                'verified': True,
                'user_code': user_code,
                'registration_step': 2,
                'message': 'Email and mobile verified successfully. Proceed to profile setup.'
            }, status=status.HTTP_200_OK)
        
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        POST /api/v1/auth/login
        Login with email/mobile and password.
        """
        email_or_mobile = request.data.get('email_or_mobile')
        password = request.data.get('password')
        
        if not all([email_or_mobile, password]):
            return Response(
                {'error': 'Email/mobile and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_info = get_device_info_from_user_agent(user_agent)
        
        try:
            # Find user by email or mobile
            user = None
            try:
                user = UserAccount.objects.get(email=email_or_mobile)
            except UserAccount.DoesNotExist:
                try:
                    user = UserAccount.objects.get(mobile=email_or_mobile)
                except UserAccount.DoesNotExist:
                    pass
            
            if not user:
                # Log failed attempt
                login_id = generate_unique_id(prefix='LOGIN_')
                LoginActivity.objects.create(
                    id=login_id,
                    login_identifier=email_or_mobile,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    device_info=device_info,
                    status='failed_not_found',
                    failure_reason='User not found'
                )
                return Response(
                    {'error': 'Invalid email/mobile or password.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if user is blocked
            is_blocked, reason, blocked_until = is_user_blocked(user)
            if is_blocked:
                login_id = generate_unique_id(prefix='LOGIN_')
                LoginActivity.objects.create(
                    id=login_id,
                    user_code=user,
                    login_identifier=email_or_mobile,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    device_info=device_info,
                    status='failed_blocked',
                    failure_reason=reason
                )
                return Response(
                    {'error': f'Account is blocked. {reason}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if user is active
            if not user.is_active:
                login_id = generate_unique_id(prefix='LOGIN_')
                LoginActivity.objects.create(
                    id=login_id,
                    user_code=user,
                    login_identifier=email_or_mobile,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    device_info=device_info,
                    status='failed_inactive',
                    failure_reason='User account is not active'
                )
                return Response(
                    {'error': 'User account is not active.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verify password
            if not check_password(password, user.password):
                login_id = generate_unique_id(prefix='LOGIN_')
                risk_score = calculate_login_risk_score(
                    client_ip, user, device_info,
                    user.login_activities.all()[:5]
                )
                
                LoginActivity.objects.create(
                    id=login_id,
                    user_code=user,
                    login_identifier=email_or_mobile,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    device_info=device_info,
                    status='failed_password',
                    failure_reason='Incorrect password',
                    risk_score=risk_score
                )
                
                return Response(
                    {'error': 'Invalid email/mobile or password.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Login successful
            user.last_login = timezone.now()
            user.last_login_ip = client_ip
            user.save()
            
            # Create tokens
            refresh = RefreshToken.for_user(user)
            
            # Create login activity
            login_id = generate_unique_id(prefix='LOGIN_')
            login_activity = LoginActivity.objects.create(
                id=login_id,
                user_code=user,
                login_identifier=email_or_mobile,
                ip_address=client_ip,
                user_agent=user_agent,
                device_info=device_info,
                status='success',
                session_token=str(refresh.access_token)
            )
            
            # Log audit
            log_user_action(
                action='login',
                user_code=user,
                description=f'User logged in from {client_ip}',
                ip_address=client_ip,
                user_agent=user_agent
            )
            
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': UserAccountSerializer(user).data,
                'requires_2fa': user.security_settings.two_factor_enabled if hasattr(user, 'security_settings') else False
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        POST /api/v1/auth/logout
        Logout and invalidate session.
        """
        try:
            client_ip = self._get_client_ip(request)
            user = request.user
            
            # Update last logout timestamp if there's a recent login activity
            login_activity = LoginActivity.objects.filter(
                user_code=user,
                status='success'
            ).latest('login_timestamp')
            
            if login_activity:
                login_activity.logout_timestamp = timezone.now()
                login_activity.session_duration = login_activity.logout_timestamp - login_activity.login_timestamp
                login_activity.save()
            
            # Log audit
            log_user_action(
                action='logout',
                user_code=user,
                description='User logged out',
                ip_address=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'logged_out': True,
                'message': 'Successfully logged out.'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '0.0.0.0'
