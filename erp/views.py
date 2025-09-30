"""
ERP Views
Authentication, Registration, KYC, Business Management API Views
"""
import logging
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth import login, logout
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination

from .models import (
    UserAccount, Branch, AadhaarKYC, PanKYC, BusinessDetails, 
    BusinessImages, BankDetails, LoginActivity, AuditTrail,
    AppFeature, UserPlatformAccess, AppAccessControl
)
from .serializers import (
    UserRegistrationSerializer, UserAccountSerializer, OTPRequestSerializer,
    OTPVerificationSerializer, LoginSerializer, AadhaarKYCSerializer,
    PanKYCSerializer, BusinessDetailsSerializer, BusinessImagesSerializer,
    BankDetailsSerializer, LoginActivitySerializer, AuditTrailSerializer,
    BranchSerializer, AppFeatureSerializer, UserPlatformAccessSerializer,
    AppAccessControlSerializer
)
from .utils import (
    generate_otp, send_email_otp, send_sms_otp, get_device_fingerprint,
    is_suspicious_login, log_security_event, create_audit_log,
    check_rate_limit, generate_unique_user_id
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================================================
# AUTHENTICATION & REGISTRATION VIEWS
# ============================================================================

class UserRegistrationView(APIView):
    """User registration with email and mobile verification."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Rate limiting
            ip_address = request.META.get('REMOTE_ADDR', '')
            is_allowed, error_msg = check_rate_limit(ip_address, 'registration', 5, 15)
            if not is_allowed:
                return Response(
                    {'error': error_msg}, 
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    # Generate unique user ID
                    serializer.validated_data['id'] = generate_unique_user_id()
                    
                    user = serializer.save()
                    
                    # Generate OTPs
                    email_otp = generate_otp()
                    mobile_otp = generate_otp()
                    
                    user.email_otp = email_otp
                    user.email_otp_created_at = timezone.now()
                    user.mobile_otp = mobile_otp
                    user.mobile_otp_created_at = timezone.now()
                    user.save()
                    
                    # Send OTPs
                    email_sent = send_email_otp(user.email, email_otp, 'verification')
                    sms_sent = send_sms_otp(user.mobile, mobile_otp, 'verification')
                    
                    # Log registration
                    create_audit_log(
                        user=user,
                        action='create',
                        resource_type='user_account',
                        resource_id=user.id,
                        description='User account created',
                        request=request
                    )
                    
                    response_data = {
                        'message': 'Registration successful. Please verify your email and mobile.',
                        'user_id': user.id,
                        'email_sent': email_sent,
                        'sms_sent': sms_sent
                    }
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response(
                {'error': 'Registration failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    """User login with device tracking."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Rate limiting
            ip_address = request.META.get('REMOTE_ADDR', '')
            is_allowed, error_msg = check_rate_limit(ip_address, 'login', 5, 15)
            if not is_allowed:
                return Response(
                    {'error': error_msg}, 
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                device_data = get_device_fingerprint(request)
                
                # Check for suspicious login
                is_suspicious, reasons = is_suspicious_login(
                    user, device_data['device_info'], ip_address
                )
                
                with transaction.atomic():
                    # Create login activity record
                    login_activity = LoginActivity.objects.create(
                        user=user,
                        email_or_mobile=request.data.get('email_or_mobile'),
                        ip_address=ip_address,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        device_info=device_data['device_info'],
                        status='success'
                    )
                    
                    # Update user login info
                    user.last_login_ip = ip_address
                    user.last_login_device = device_data['device_name']
                    user.reset_login_attempts()
                    user.save()
                    
                    # Generate tokens
                    refresh = RefreshToken.for_user(user)
                    
                    # Log security event if suspicious
                    if is_suspicious:
                        log_security_event(
                            user=user,
                            event_type='login',
                            description=f'Suspicious login detected: {", ".join(reasons)}',
                            request=request,
                            severity='warning'
                        )
                    
                    # Create audit log
                    create_audit_log(
                        user=user,
                        action='login',
                        resource_type='user_account',
                        resource_id=user.id,
                        description='User logged in successfully',
                        request=request
                    )
                    
                    response_data = {
                        'message': 'Login successful',
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                        'user': UserAccountSerializer(user).data,
                        'suspicious_login': is_suspicious,
                        'suspicious_reasons': reasons if is_suspicious else []
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
            
            # Handle login failure
            email_or_mobile = request.data.get('email_or_mobile', '')
            user = None
            
            # Try to find user for failed login tracking
            if '@' in email_or_mobile:
                try:
                    user = UserAccount.objects.get(email__iexact=email_or_mobile)
                except UserAccount.DoesNotExist:
                    pass
            else:
                try:
                    user = UserAccount.objects.get(mobile=email_or_mobile)
                except UserAccount.DoesNotExist:
                    pass
            
            # Log failed login attempt
            LoginActivity.objects.create(
                user=user,
                email_or_mobile=email_or_mobile,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                device_info=get_device_fingerprint(request)['device_info'],
                status='failed',
                failure_reason='Invalid credentials'
            )
            
            # Increment failed attempts for existing user
            if user:
                user.increment_login_attempts()
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response(
                {'error': 'Login failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    """User logout."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Find the latest login activity
            login_activity = LoginActivity.objects.filter(
                user=request.user,
                status='success',
                logout_timestamp__isnull=True
            ).order_by('-login_timestamp').first()
            
            if login_activity:
                login_activity.logout_timestamp = timezone.now()
                login_activity.session_duration = (
                    login_activity.logout_timestamp - login_activity.login_timestamp
                )
                login_activity.save()
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='logout',
                resource_type='user_account',
                resource_id=request.user.id,
                description='User logged out',
                request=request
            )
            
            return Response(
                {'message': 'Logout successful'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {'error': 'Logout failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# OTP VIEWS
# ============================================================================

class OTPRequestView(APIView):
    """Request OTP for various purposes."""
    permission_classes = [AllowAny]  # Some OTP requests don't need authentication
    
    def post(self, request):
        try:
            serializer = OTPRequestSerializer(
                data=request.data, 
                context={'request': request}
            )
            
            if serializer.is_valid():
                otp_type = serializer.validated_data['otp_type']
                
                # Rate limiting based on OTP type and user/IP
                identifier = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR', '')
                is_allowed, error_msg = check_rate_limit(identifier, f'otp_{otp_type}', 3, 5)
                if not is_allowed:
                    return Response(
                        {'error': error_msg}, 
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                
                with transaction.atomic():
                    if otp_type == 'email':
                        return self._handle_email_otp(request)
                    elif otp_type == 'mobile':
                        return self._handle_mobile_otp(request)
                    elif otp_type == 'business_email':
                        return self._handle_business_email_otp(request)
                    elif otp_type == 'business_mobile':
                        return self._handle_business_mobile_otp(request)
                    elif otp_type == 'aadhaar':
                        return self._handle_aadhaar_otp(request)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"OTP request error: {str(e)}")
            return Response(
                {'error': 'OTP request failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _handle_email_otp(self, request):
        """Handle email OTP request."""
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'User ID required for email OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = UserAccount.objects.get(id=user_id)
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user.is_otp_blocked('email'):
            return Response(
                {'error': 'Email OTP blocked due to multiple attempts'}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        otp = generate_otp()
        user.email_otp = otp
        user.email_otp_created_at = timezone.now()
        user.save()
        
        email_sent = send_email_otp(user.email, otp, 'verification')
        
        return Response({
            'message': 'Email OTP sent successfully' if email_sent else 'Failed to send email OTP',
            'sent': email_sent
        })
    
    def _handle_mobile_otp(self, request):
        """Handle mobile OTP request."""
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'User ID required for mobile OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = UserAccount.objects.get(id=user_id)
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user.is_otp_blocked('mobile'):
            return Response(
                {'error': 'Mobile OTP blocked due to multiple attempts'}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        otp = generate_otp()
        user.mobile_otp = otp
        user.mobile_otp_created_at = timezone.now()
        user.save()
        
        sms_sent = send_sms_otp(user.mobile, otp, 'verification')
        
        return Response({
            'message': 'Mobile OTP sent successfully' if sms_sent else 'Failed to send mobile OTP',
            'sent': sms_sent
        })
    
    def _handle_business_email_otp(self, request):
        """Handle business email OTP request."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            business = request.user.business_details
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        otp = generate_otp()
        business.business_email_otp = otp
        business.business_email_otp_created_at = timezone.now()
        business.save()
        
        email_sent = send_email_otp(business.business_email, otp, 'business')
        
        return Response({
            'message': 'Business email OTP sent successfully' if email_sent else 'Failed to send business email OTP',
            'sent': email_sent
        })
    
    def _handle_business_mobile_otp(self, request):
        """Handle business mobile OTP request."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            business = request.user.business_details
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        otp = generate_otp()
        business.business_phone_otp = otp
        business.business_phone_otp_created_at = timezone.now()
        business.save()
        
        sms_sent = send_sms_otp(business.business_phone, otp, 'business')
        
        return Response({
            'message': 'Business mobile OTP sent successfully' if sms_sent else 'Failed to send business mobile OTP',
            'sent': sms_sent
        })
    
    def _handle_aadhaar_otp(self, request):
        """Handle Aadhaar OTP request."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            aadhaar = request.user.aadhaar_kyc
        except AadhaarKYC.DoesNotExist:
            return Response(
                {'error': 'Aadhaar KYC details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # In real implementation, this would call UIDAI API
        otp = generate_otp()
        aadhaar.aadhaar_otp = otp
        aadhaar.aadhaar_otp_created_at = timezone.now()
        aadhaar.save()
        
        # For demo purposes, we'll use mobile OTP
        sms_sent = send_sms_otp(request.user.mobile, otp, 'aadhaar')
        
        return Response({
            'message': 'Aadhaar OTP sent successfully' if sms_sent else 'Failed to send Aadhaar OTP',
            'sent': sms_sent
        })


class OTPVerificationView(APIView):
    """Verify OTP for various purposes."""
    permission_classes = [AllowAny]  # Some OTP verifications don't need authentication
    
    def post(self, request):
        try:
            serializer = OTPVerificationSerializer(data=request.data)
            
            if serializer.is_valid():
                otp_type = serializer.validated_data['otp_type']
                otp = serializer.validated_data['otp']
                
                with transaction.atomic():
                    if otp_type == 'email':
                        return self._verify_email_otp(request, otp)
                    elif otp_type == 'mobile':
                        return self._verify_mobile_otp(request, otp)
                    elif otp_type == 'business_email':
                        return self._verify_business_email_otp(request, otp)
                    elif otp_type == 'business_mobile':
                        return self._verify_business_mobile_otp(request, otp)
                    elif otp_type == 'aadhaar':
                        return self._verify_aadhaar_otp(request, otp)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"OTP verification error: {str(e)}")
            return Response(
                {'error': 'OTP verification failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _verify_email_otp(self, request, otp):
        """Verify email OTP."""
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'User ID required for email OTP verification'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = UserAccount.objects.get(id=user_id)
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user.is_otp_blocked('email'):
            return Response(
                {'error': 'Email OTP verification blocked'}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        if not user.email_otp or not user.email_otp_created_at:
            return Response(
                {'error': 'No OTP found. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check OTP expiry
        expiry_time = user.email_otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return Response(
                {'error': 'OTP expired. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.email_otp != otp:
            user.increment_otp_attempts('email')
            return Response(
                {'error': 'Invalid OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP verified successfully
        user.is_email_verified = True
        user.reset_otp_attempts('email')
        
        # Check if both email and mobile are verified to activate account
        if user.is_mobile_verified:
            user.is_active = True
        
        user.save()
        
        # Create audit log
        create_audit_log(
            user=user,
            action='otp_verify',
            resource_type='user_account',
            resource_id=user.id,
            description='Email OTP verified successfully',
            request=request
        )
        
        return Response({
            'message': 'Email verified successfully',
            'account_activated': user.is_active
        })
    
    def _verify_mobile_otp(self, request, otp):
        """Verify mobile OTP."""
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'User ID required for mobile OTP verification'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = UserAccount.objects.get(id=user_id)
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user.is_otp_blocked('mobile'):
            return Response(
                {'error': 'Mobile OTP verification blocked'}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        if not user.mobile_otp or not user.mobile_otp_created_at:
            return Response(
                {'error': 'No OTP found. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check OTP expiry
        expiry_time = user.mobile_otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return Response(
                {'error': 'OTP expired. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.mobile_otp != otp:
            user.increment_otp_attempts('mobile')
            return Response(
                {'error': 'Invalid OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP verified successfully
        user.is_mobile_verified = True
        user.reset_otp_attempts('mobile')
        
        # Check if both email and mobile are verified to activate account
        if user.is_email_verified:
            user.is_active = True
        
        user.save()
        
        # Create audit log
        create_audit_log(
            user=user,
            action='otp_verify',
            resource_type='user_account',
            resource_id=user.id,
            description='Mobile OTP verified successfully',
            request=request
        )
        
        return Response({
            'message': 'Mobile verified successfully',
            'account_activated': user.is_active
        })
    
    def _verify_business_email_otp(self, request, otp):
        """Verify business email OTP."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            business = request.user.business_details
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not business.business_email_otp or not business.business_email_otp_created_at:
            return Response(
                {'error': 'No OTP found. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check OTP expiry
        expiry_time = business.business_email_otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return Response(
                {'error': 'OTP expired. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if business.business_email_otp != otp:
            business.business_email_otp_attempts += 1
            business.save()
            return Response(
                {'error': 'Invalid OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP verified successfully
        business.is_business_email_verified = True
        business.business_email_otp = None
        business.business_email_otp_created_at = None
        business.business_email_otp_attempts = 0
        business.save()
        
        return Response({'message': 'Business email verified successfully'})
    
    def _verify_business_mobile_otp(self, request, otp):
        """Verify business mobile OTP."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            business = request.user.business_details
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not business.business_phone_otp or not business.business_phone_otp_created_at:
            return Response(
                {'error': 'No OTP found. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check OTP expiry
        expiry_time = business.business_phone_otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return Response(
                {'error': 'OTP expired. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if business.business_phone_otp != otp:
            business.business_phone_otp_attempts += 1
            business.save()
            return Response(
                {'error': 'Invalid OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP verified successfully
        business.is_business_phone_verified = True
        business.business_phone_otp = None
        business.business_phone_otp_created_at = None
        business.business_phone_otp_attempts = 0
        business.save()
        
        return Response({'message': 'Business mobile verified successfully'})
    
    def _verify_aadhaar_otp(self, request, otp):
        """Verify Aadhaar OTP."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            aadhaar = request.user.aadhaar_kyc
        except AadhaarKYC.DoesNotExist:
            return Response(
                {'error': 'Aadhaar KYC details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not aadhaar.aadhaar_otp or not aadhaar.aadhaar_otp_created_at:
            return Response(
                {'error': 'No OTP found. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check OTP expiry
        expiry_time = aadhaar.aadhaar_otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return Response(
                {'error': 'OTP expired. Please request a new OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if aadhaar.aadhaar_otp != otp:
            aadhaar.aadhaar_otp_attempts += 1
            aadhaar.save()
            return Response(
                {'error': 'Invalid OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP verified successfully
        aadhaar.is_verified = True
        aadhaar.verified_at = timezone.now()
        aadhaar.aadhaar_otp = None
        aadhaar.aadhaar_otp_created_at = None
        aadhaar.aadhaar_otp_attempts = 0
        aadhaar.save()
        
        # Update user KYC status
        request.user.is_kyc_completed = True
        request.user.save()
        
        return Response({'message': 'Aadhaar verified successfully'})


# ============================================================================
# USER MANAGEMENT VIEWS
# ============================================================================

class UserProfileView(APIView):
    """Get and update user profile."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user profile."""
        serializer = UserAccountSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        """Update user profile."""
        serializer = UserAccountSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            old_values = UserAccountSerializer(request.user).data
            user = serializer.save()
            new_values = UserAccountSerializer(user).data
            
            # Create audit log
            create_audit_log(
                user=request.user,
                action='update',
                resource_type='user_account',
                resource_id=request.user.id,
                description='User profile updated',
                old_values=old_values,
                new_values=new_values,
                request=request
            )
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BranchListView(generics.ListAPIView):
    """List all active branches."""
    queryset = Branch.objects.filter(is_active=True)
    serializer_class = BranchSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination


# ============================================================================
# KYC MANAGEMENT VIEWS
# ============================================================================

class AadhaarKYCView(APIView):
    """Aadhaar KYC submission and management."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get Aadhaar KYC details."""
        try:
            aadhaar_kyc = request.user.aadhaar_kyc
            serializer = AadhaarKYCSerializer(aadhaar_kyc)
            return Response(serializer.data)
        except AadhaarKYC.DoesNotExist:
            return Response(
                {'error': 'Aadhaar KYC not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Submit Aadhaar KYC."""
        try:
            # Check if already exists
            if hasattr(request.user, 'aadhaar_kyc'):
                return Response(
                    {'error': 'Aadhaar KYC already submitted'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = AadhaarKYCSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    aadhaar_kyc = serializer.save(user=request.user)
                    
                    # Create audit log
                    create_audit_log(
                        user=request.user,
                        action='kyc_submit',
                        resource_type='aadhaar_kyc',
                        resource_id=aadhaar_kyc.id,
                        description='Aadhaar KYC submitted',
                        request=request
                    )
                    
                    return Response(
                        {
                            'message': 'Aadhaar KYC submitted successfully',
                            'data': AadhaarKYCSerializer(aadhaar_kyc).data
                        }, 
                        status=status.HTTP_201_CREATED
                    )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Aadhaar KYC submission error: {str(e)}")
            return Response(
                {'error': 'KYC submission failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        """Update Aadhaar KYC."""
        try:
            aadhaar_kyc = request.user.aadhaar_kyc
            
            if aadhaar_kyc.is_verified:
                return Response(
                    {'error': 'Cannot update verified KYC'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            old_values = AadhaarKYCSerializer(aadhaar_kyc).data
            serializer = AadhaarKYCSerializer(aadhaar_kyc, data=request.data, partial=True)
            
            if serializer.is_valid():
                aadhaar_kyc = serializer.save()
                new_values = AadhaarKYCSerializer(aadhaar_kyc).data
                
                # Create audit log
                create_audit_log(
                    user=request.user,
                    action='update',
                    resource_type='aadhaar_kyc',
                    resource_id=aadhaar_kyc.id,
                    description='Aadhaar KYC updated',
                    old_values=old_values,
                    new_values=new_values,
                    request=request
                )
                
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except AadhaarKYC.DoesNotExist:
            return Response(
                {'error': 'Aadhaar KYC not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PanKYCView(APIView):
    """PAN KYC submission and management."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get PAN KYC details."""
        try:
            pan_kyc = request.user.pan_kyc
            serializer = PanKYCSerializer(pan_kyc)
            return Response(serializer.data)
        except PanKYC.DoesNotExist:
            return Response(
                {'error': 'PAN KYC not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Submit PAN KYC."""
        try:
            # Check if already exists
            if hasattr(request.user, 'pan_kyc'):
                return Response(
                    {'error': 'PAN KYC already submitted'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = PanKYCSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    pan_kyc = serializer.save(user=request.user)
                    
                    # Create audit log
                    create_audit_log(
                        user=request.user,
                        action='kyc_submit',
                        resource_type='pan_kyc',
                        resource_id=pan_kyc.id,
                        description='PAN KYC submitted',
                        request=request
                    )
                    
                    return Response(
                        {
                            'message': 'PAN KYC submitted successfully',
                            'data': PanKYCSerializer(pan_kyc).data
                        }, 
                        status=status.HTTP_201_CREATED
                    )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"PAN KYC submission error: {str(e)}")
            return Response(
                {'error': 'KYC submission failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BusinessDetailsView(APIView):
    """Business details submission and management."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get business details."""
        try:
            business = request.user.business_details
            serializer = BusinessDetailsSerializer(business)
            return Response(serializer.data)
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Submit business details."""
        try:
            # Check if already exists
            if hasattr(request.user, 'business_details'):
                return Response(
                    {'error': 'Business details already submitted'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = BusinessDetailsSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    business = serializer.save(user=request.user)
                    
                    # Create audit log
                    create_audit_log(
                        user=request.user,
                        action='create',
                        resource_type='business_details',
                        resource_id=business.id,
                        description='Business details submitted',
                        request=request
                    )
                    
                    return Response(
                        {
                            'message': 'Business details submitted successfully',
                            'data': BusinessDetailsSerializer(business).data
                        }, 
                        status=status.HTTP_201_CREATED
                    )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Business details submission error: {str(e)}")
            return Response(
                {'error': 'Business details submission failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        """Update business details."""
        try:
            business = request.user.business_details
            
            if business.is_verified:
                return Response(
                    {'error': 'Cannot update verified business details'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            old_values = BusinessDetailsSerializer(business).data
            serializer = BusinessDetailsSerializer(business, data=request.data, partial=True)
            
            if serializer.is_valid():
                business = serializer.save()
                new_values = BusinessDetailsSerializer(business).data
                
                # Create audit log
                create_audit_log(
                    user=request.user,
                    action='update',
                    resource_type='business_details',
                    resource_id=business.id,
                    description='Business details updated',
                    old_values=old_values,
                    new_values=new_values,
                    request=request
                )
                
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class BusinessImagesView(APIView):
    """Business shop images management."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get business shop images."""
        try:
            business = request.user.business_details
            images = business.shop_images.all()
            serializer = BusinessImagesSerializer(images, many=True)
            return Response(serializer.data)
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Upload business shop image."""
        try:
            business = request.user.business_details
            
            # Check image limit (max 5 images)
            current_count = business.shop_images.count()
            if current_count >= 5:
                return Response(
                    {'error': 'Maximum 5 shop images allowed'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = BusinessImagesSerializer(data=request.data)
            if serializer.is_valid():
                image = serializer.save(business=business)
                
                # Create audit log
                create_audit_log(
                    user=request.user,
                    action='create',
                    resource_type='business_images',
                    resource_id=image.id,
                    description='Business shop image uploaded',
                    request=request
                )
                
                return Response(
                    {
                        'message': 'Shop image uploaded successfully',
                        'data': BusinessImagesSerializer(image).data
                    }, 
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, image_id):
        """Delete business shop image."""
        try:
            business = request.user.business_details
            image = business.shop_images.get(id=image_id)
            
            # Create audit log before deletion
            create_audit_log(
                user=request.user,
                action='delete',
                resource_type='business_images',
                resource_id=image.id,
                description='Business shop image deleted',
                request=request
            )
            
            image.delete()
            
            return Response(
                {'message': 'Shop image deleted successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except BusinessDetails.DoesNotExist:
            return Response(
                {'error': 'Business details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except BusinessImages.DoesNotExist:
            return Response(
                {'error': 'Shop image not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class BankDetailsView(APIView):
    """Bank details submission and management."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get bank details."""
        try:
            bank = request.user.bank_details
            serializer = BankDetailsSerializer(bank)
            return Response(serializer.data)
        except BankDetails.DoesNotExist:
            return Response(
                {'error': 'Bank details not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Submit bank details."""
        try:
            # Check if already exists
            if hasattr(request.user, 'bank_details'):
                return Response(
                    {'error': 'Bank details already submitted'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = BankDetailsSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    bank = serializer.save(user=request.user)
                    
                    # Create audit log
                    create_audit_log(
                        user=request.user,
                        action='create',
                        resource_type='bank_details',
                        resource_id=bank.id,
                        description='Bank details submitted',
                        request=request
                    )
                    
                    return Response(
                        {
                            'message': 'Bank details submitted successfully',
                            'data': BankDetailsSerializer(bank).data
                        }, 
                        status=status.HTTP_201_CREATED
                    )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Bank details submission error: {str(e)}")
            return Response(
                {'error': 'Bank details submission failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# ADMIN & REPORTING VIEWS
# ============================================================================

class LoginActivityListView(generics.ListAPIView):
    """List login activities."""
    serializer_class = LoginActivitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter based on user role and permissions."""
        user = self.request.user
        
        if user.role in ['master_superadmin', 'super_admin']:
            # Can see all login activities
            return LoginActivity.objects.all().order_by('-login_timestamp')
        elif user.role == 'admin':
            # Can see activities in their branch
            return LoginActivity.objects.filter(
                user__branch=user.branch
            ).order_by('-login_timestamp')
        else:
            # Regular users can only see their own activities
            return LoginActivity.objects.filter(
                user=user
            ).order_by('-login_timestamp')


class AuditTrailListView(generics.ListAPIView):
    """List audit trail entries."""
    serializer_class = AuditTrailSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter based on user role and permissions."""
        user = self.request.user
        
        if user.role in ['master_superadmin', 'super_admin']:
            # Can see all audit trails
            return AuditTrail.objects.all().order_by('-created_at')
        elif user.role == 'admin':
            # Can see audit trails in their branch
            return AuditTrail.objects.filter(
                user__branch=user.branch
            ).order_by('-created_at')
        else:
            # Regular users can only see their own audit trails
            return AuditTrail.objects.filter(
                user=user
            ).order_by('-created_at')


# ============================================================================
# DASHBOARD & ANALYTICS VIEWS
# ============================================================================

class DashboardStatsView(APIView):
    """Dashboard statistics for different user roles."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard statistics based on user role."""
        user = request.user
        
        if user.role in ['master_superadmin', 'super_admin']:
            return self._get_admin_stats()
        elif user.role == 'admin':
            return self._get_branch_admin_stats(user.branch)
        else:
            return self._get_user_stats(user)
    
    def _get_admin_stats(self):
        """Get statistics for super admin users."""
        total_users = UserAccount.objects.count()
        active_users = UserAccount.objects.filter(is_active=True).count()
        verified_users = UserAccount.objects.filter(
            is_email_verified=True, 
            is_mobile_verified=True
        ).count()
        kyc_completed = UserAccount.objects.filter(is_kyc_completed=True).count()
        
        # Recent activities
        recent_registrations = UserAccount.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        recent_logins = LoginActivity.objects.filter(
            login_timestamp__gte=timezone.now() - timedelta(days=1),
            status='success'
        ).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'kyc_completed': kyc_completed,
            'recent_registrations': recent_registrations,
            'recent_logins': recent_logins
        })
    
    def _get_branch_admin_stats(self, branch):
        """Get statistics for branch admin users."""
        total_users = UserAccount.objects.filter(branch=branch).count()
        active_users = UserAccount.objects.filter(branch=branch, is_active=True).count()
        verified_users = UserAccount.objects.filter(
            branch=branch,
            is_email_verified=True, 
            is_mobile_verified=True
        ).count()
        
        return Response({
            'branch_name': branch.branch_name,
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users
        })
    
    def _get_user_stats(self, user):
        """Get statistics for regular users."""
        login_count = user.login_count
        last_login = user.last_login
        
        # User's verification status
        verification_status = {
            'email_verified': user.is_email_verified,
            'mobile_verified': user.is_mobile_verified,
            'kyc_completed': user.is_kyc_completed,
            'business_verified': user.is_business_verified,
            'bank_verified': user.is_bank_verified
        }
        
        return Response({
            'login_count': login_count,
            'last_login': last_login,
            'verification_status': verification_status
        })


# ============================================================================
# HEALTH CHECK VIEW
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now(),
        'version': '1.0.0'
    })