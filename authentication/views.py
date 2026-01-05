from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import User, LoginHistory, UserToken, DeviceFingerprint, SecurityLog
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer, 
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer
)
from .utils import send_otp_email, send_welcome_email, send_password_changed_notification, send_sms_otp, validate_mobile_number
from .device_utils import (
    get_client_ip, create_device_fingerprint, log_login_attempt, 
    store_user_token, cleanup_expired_tokens, is_suspicious_login,
    generate_device_id
)

User = get_user_model()


def get_tokens_for_user(user, request):
    """Generate JWT tokens for user and store them in database."""
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    # Calculate expiry times
    refresh_expires_at = timezone.now() + timedelta(days=7)  # From settings.SIMPLE_JWT
    access_expires_at = timezone.now() + timedelta(hours=1)  # From settings.SIMPLE_JWT
    
    # Store refresh token in database
    store_user_token(user, str(refresh), 'refresh', request, refresh_expires_at)
    
    # Store access token in database (optional, as it's short-lived)
    store_user_token(user, str(access_token), 'access', request, access_expires_at)
    
    # Clean up expired tokens
    cleanup_expired_tokens(user)
    
    return {
        'refresh': str(refresh),
        'access': str(access_token),
    }


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """User registration endpoint."""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Get client information
        ip_address = get_client_ip(request)
        
        # Generate JWT tokens and store in database
        tokens = get_tokens_for_user(user, request)
        
        # Create device fingerprint
        device_fingerprint = create_device_fingerprint(user, request)
        
        # Update user login information
        user.last_login_ip = ip_address
        user.last_login_device = device_fingerprint.device_name
        user.login_count += 1
        user.save()
        
        # Log registration as successful login
        log_login_attempt(user, request, 'success', 'email')
        
        # Log security event
        SecurityLog.objects.create(
            user=user,
            event_type='login_success',
            description='User registered and logged in',
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_id=device_fingerprint.device_id
        )
        
        # Send welcome email
        send_welcome_email(user)
        
        # Send email OTP for verification
        email_success, email_otp, email_message = send_otp_email(user, 'email_verification')
        
        # Send mobile OTP if mobile number is provided AND mobile verification is required
        mobile_otp_sent = False
        mobile_message = ''
        mobile_otp = None
        
        from django.conf import settings
        require_mobile = getattr(settings, 'REQUIRE_MOBILE_VERIFICATION', False)
        
        if user.mobile and require_mobile:
            is_valid, clean_mobile, validation_message = validate_mobile_number(user.mobile)
            if is_valid:
                mobile_success, mobile_otp, mobile_message = send_sms_otp(user, clean_mobile, 'mobile_verification')
                mobile_otp_sent = mobile_success
            else:
                mobile_message = validation_message
        elif user.mobile and not require_mobile:
            # Mobile verification is disabled, auto-verify mobile
            user.is_mobile_verified = True
            user.save()
            mobile_message = 'Mobile verification disabled - automatically verified'
        
        response_data = {
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'user': UserProfileSerializer(user).data,
                'tokens': tokens,
                'device': {
                    'device_id': device_fingerprint.device_id,
                    'device_name': device_fingerprint.device_name,
                    'device_type': device_fingerprint.device_type,
                    'is_new_device': True
                },
                'email_otp_sent': email_success,
                'email_message': email_message,
                'mobile_otp_sent': mobile_otp_sent,
                'mobile_message': mobile_message
            }
        }
        
        # For development, include OTPs in response
        if email_success and email_otp:
            response_data['data']['email_otp'] = email_otp
        if mobile_otp_sent and mobile_otp:
            response_data['data']['mobile_otp'] = mobile_otp
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response({
        'status': 'error',
        'message': 'Registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """User login endpoint."""
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Get client information
        ip_address = get_client_ip(request)
        
        # Check for suspicious activity
        is_suspicious, suspicious_reason = is_suspicious_login(user, request)
        
        if is_suspicious:
            # Log suspicious attempt
            log_login_attempt(user, request, 'blocked', 'email', suspicious_reason)
            
            SecurityLog.objects.create(
                user=user,
                event_type='suspicious_activity',
                description=f'Suspicious login attempt: {suspicious_reason}',
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                device_id=generate_device_id(request)
            )
            
            return Response({
                'status': 'error',
                'message': 'Login blocked due to suspicious activity. Please verify your identity.',
                'requires_verification': True
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT tokens and store in database
        tokens = get_tokens_for_user(user, request)
        
        # Create or update device fingerprint
        device_fingerprint = create_device_fingerprint(user, request)
        is_new_device = device_fingerprint.login_count == 1
        
        # Update user login information
        user.last_login_ip = ip_address
        user.last_login_device = device_fingerprint.device_name
        user.login_count += 1
        user.save()
        
        # Determine login method
        login_method = 'email' if '@' in serializer.validated_data.get('email_or_mobile', '') else 'mobile'
        
        # Log successful login
        log_login_attempt(user, request, 'success', login_method)
        
        # Log security event
        SecurityLog.objects.create(
            user=user,
            event_type='login_success',
            description=f'Successful login via {login_method}',
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_id=device_fingerprint.device_id
        )
        
        # Clean up old tokens
        cleanup_expired_tokens(user)
        
        response_data = {
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'user': UserProfileSerializer(user).data,
                'tokens': tokens,
                'device': {
                    'device_id': device_fingerprint.device_id,
                    'device_name': device_fingerprint.device_name,
                    'device_type': device_fingerprint.device_type,
                    'is_new_device': is_new_device,
                    'is_trusted': device_fingerprint.is_trusted
                },
                'login_count': user.login_count,
                'last_login_ip': user.last_login_ip
            }
        }
        
        # If new device, suggest email/mobile verification
        if is_new_device:
            response_data['data']['verification_suggested'] = True
            response_data['message'] = 'Login successful from new device. Please verify your email/mobile for enhanced security.'
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    # Log failed login attempt
    email_or_mobile = request.data.get('email_or_mobile', '')
    if email_or_mobile:
        try:
            if '@' in email_or_mobile:
                user = User.objects.get(email=email_or_mobile, is_active=True)
            else:
                user = User.objects.get(mobile=email_or_mobile, is_active=True)
            
            log_login_attempt(user, request, 'failed', 'email' if '@' in email_or_mobile else 'mobile', 'Invalid credentials')
        except User.DoesNotExist:
            # Don't log for non-existent users to avoid creating attack vectors
            pass
    
    return Response({
        'status': 'error',
        'message': 'Login failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    """Forgot password endpoint - sends OTP."""
    serializer = ForgotPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        email_or_mobile = serializer.validated_data['email_or_mobile']
        
        # Find user
        user = None
        otp_type = 'email'
        if '@' in email_or_mobile:
            user = User.objects.get(email=email_or_mobile, is_active=True)
            otp_type = 'email'
        else:
            user = User.objects.get(mobile=email_or_mobile, is_active=True)
            otp_type = 'mobile'
        
        # Send OTP based on type
        if otp_type == 'email':
            email_success, otp, email_message = send_otp_email(user, 'password_reset')
            
            response_data = {
                'status': 'success',
                'message': f'OTP sent to your {otp_type}',
                'data': {
                    'otp_sent': email_success,
                    'message': email_message,
                    'otp_type': otp_type,
                    'expires_in': '10 minutes'
                }
            }
            
            # For development, include OTP in response
            if email_success and otp:
                response_data['data']['otp'] = otp
                
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            # For mobile, generate OTP (SMS not implemented yet)
            otp = user.generate_otp(otp_type)
            return Response({
                'status': 'success',
                'message': f'OTP sent to your {otp_type}',
                'data': {
                    'otp': otp,  # In production, send via SMS
                    'otp_type': otp_type,
                    'expires_in': '10 minutes'
                }
            }, status=status.HTTP_200_OK)
    
    return Response({
        'status': 'error',
        'message': 'Request failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """Reset password endpoint using OTP."""
    serializer = ResetPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        email_or_mobile = serializer.validated_data['email_or_mobile']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        # Find user
        user = None
        otp_type = 'email'
        if '@' in email_or_mobile:
            user = User.objects.get(email=email_or_mobile, is_active=True)
            otp_type = 'email'
        else:
            user = User.objects.get(mobile=email_or_mobile, is_active=True)
            otp_type = 'mobile'
        
        # Verify OTP
        if user.verify_otp(otp, otp_type):
            # Reset password
            user.set_password(new_password)
            user.save()
            
            # Send password change notification
            if otp_type == 'email':
                send_password_changed_notification(user)
            
            return Response({
                'status': 'success',
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': 'Invalid or expired OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'status': 'error',
        'message': 'Password reset failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Change password endpoint for authenticated users."""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = request.user
        new_password = serializer.validated_data['new_password']
        
        user.set_password(new_password)
        user.save()
        
        # Send password change notification
        send_password_changed_notification(user)
        
        return Response({
            'status': 'success',
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'status': 'error',
        'message': 'Password change failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """Get user profile."""
    serializer = UserProfileSerializer(request.user)
    return Response({
        'status': 'success',
        'data': {
            'user': serializer.data
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_email(request):
    """Verify email with OTP."""
    otp = request.data.get('otp')
    
    if not otp:
        return Response({
            'status': 'error',
            'message': 'OTP is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    if user.verify_otp(otp, 'email'):
        return Response({
            'status': 'success',
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'status': 'error',
            'message': 'Invalid or expired OTP'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_mobile(request):
    """Verify mobile with OTP."""
    from django.conf import settings
    require_mobile = getattr(settings, 'REQUIRE_MOBILE_VERIFICATION', False)
    
    # If mobile verification is disabled, auto-verify
    if not require_mobile:
        user = request.user
        user.is_mobile_verified = True
        user.save()
        return Response({
            'status': 'success',
            'message': 'Mobile verification is disabled - automatically verified'
        }, status=status.HTTP_200_OK)
    
    otp = request.data.get('otp')
    
    if not otp:
        return Response({
            'status': 'error',
            'message': 'OTP is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    if user.verify_otp(otp, 'mobile'):
        return Response({
            'status': 'success',
            'message': 'Mobile verified successfully'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'status': 'error',
            'message': 'Invalid or expired OTP'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resend_otp(request):
    """Resend OTP for email or mobile verification."""
    otp_type = request.data.get('type', 'email')  # 'email' or 'mobile'
    
    if otp_type not in ['email', 'mobile']:
        return Response({
            'status': 'error',
            'message': 'Invalid OTP type. Use "email" or "mobile"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    if otp_type == 'email':
        # Send email OTP
        email_success, otp, email_message = send_otp_email(user, 'email_verification')
        
        response_data = {
            'status': 'success',
            'message': f'OTP sent to your {otp_type}',
            'data': {
                'otp_sent': email_success,
                'message': email_message,
                'expires_in': '10 minutes'
            }
        }
        
        # For development, include OTP in response
        if email_success and otp:
            response_data['data']['otp'] = otp
            
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        # Check if mobile verification is required
        from django.conf import settings
        require_mobile = getattr(settings, 'REQUIRE_MOBILE_VERIFICATION', False)
        
        if not require_mobile:
            # Mobile verification is disabled, auto-verify
            user.is_mobile_verified = True
            user.save()
            return Response({
                'status': 'success',
                'message': 'Mobile verification is disabled - automatically verified',
                'data': {
                    'otp_sent': False,
                    'message': 'Mobile verification bypassed'
                }
            }, status=status.HTTP_200_OK)
        
        # Send mobile OTP
        if not user.mobile:
            return Response({
                'status': 'error',
                'message': 'Mobile number not registered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate mobile number
        is_valid, clean_mobile, validation_message = validate_mobile_number(user.mobile)
        if not is_valid:
            return Response({
                'status': 'error',
                'message': f'Invalid mobile number: {validation_message}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send SMS OTP
        sms_success, otp, sms_message = send_sms_otp(user, clean_mobile, 'mobile_verification')
        
        response_data = {
            'status': 'success',
            'message': f'OTP sent to your {otp_type}',
            'data': {
                'otp_sent': sms_success,
                'message': sms_message,
                'expires_in': '10 minutes'
            }
        }
        
        # For development, include OTP in response
        if sms_success and otp:
            response_data['data']['otp'] = otp
            
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def login_history(request):
    """Get user's login history."""
    user = request.user
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    history = LoginHistory.objects.filter(user=user).order_by('-created_at')[offset:offset + page_size]
    total_count = LoginHistory.objects.filter(user=user).count()
    
    history_data = []
    for entry in history:
        history_data.append({
            'id': entry.id,
            'ip_address': entry.ip_address,
            'device_name': entry.device_name,
            'device_type': entry.device_type,
            'browser_name': entry.browser_name,
            'os_name': entry.os_name,
            'location': entry.location,
            'login_method': entry.login_method,
            'login_type': entry.login_type,
            'status': entry.status,
            'failure_reason': entry.failure_reason,
            'created_at': entry.created_at,
            'logout_time': entry.logout_time,
            'session_duration': str(entry.session_duration) if entry.session_duration else None
        })
    
    return Response({
        'status': 'success',
        'data': {
            'login_history': history_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def active_devices(request):
    """Get user's active devices."""
    user = request.user
    
    # Get devices active in last 30 days
    devices = DeviceFingerprint.objects.filter(
        user=user,
        last_seen__gte=timezone.now() - timedelta(days=30)
    ).order_by('-last_seen')
    
    devices_data = []
    for device in devices:
        # Get active tokens for this device
        active_tokens = UserToken.objects.filter(
            user=user,
            device_id=device.device_id,
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        
        devices_data.append({
            'device_id': device.device_id,
            'device_name': device.device_name,
            'device_type': device.device_type,
            'browser_name': device.browser_name,
            'browser_version': device.browser_version,
            'os_name': device.os_name,
            'os_version': device.os_version,
            'is_trusted': device.is_trusted,
            'first_seen': device.first_seen,
            'last_seen': device.last_seen,
            'login_count': device.login_count,
            'active_tokens': active_tokens,
            'is_current_device': device.device_id == generate_device_id(request)
        })
    
    return Response({
        'status': 'success',
        'data': {
            'active_devices': devices_data,
            'total_devices': len(devices_data)
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def revoke_device(request):
    """Revoke all tokens for a specific device."""
    device_id = request.data.get('device_id')
    
    if not device_id:
        return Response({
            'status': 'error',
            'message': 'Device ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    # Check if device belongs to user
    try:
        device = DeviceFingerprint.objects.get(user=user, device_id=device_id)
    except DeviceFingerprint.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Revoke all tokens for this device
    from .device_utils import revoke_device_tokens
    revoked_count = revoke_device_tokens(user, device_id)
    
    # Log security event
    SecurityLog.objects.create(
        user=user,
        event_type='token_revoked',
        description=f'Revoked {revoked_count} tokens for device: {device.device_name}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        device_id=device_id
    )
    
    return Response({
        'status': 'success',
        'message': f'Revoked {revoked_count} tokens for device: {device.device_name}',
        'data': {
            'device_name': device.device_name,
            'revoked_tokens': revoked_count
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trust_device(request):
    """Mark a device as trusted."""
    device_id = request.data.get('device_id')
    is_trusted = request.data.get('is_trusted', True)
    
    if not device_id:
        return Response({
            'status': 'error',
            'message': 'Device ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    try:
        device = DeviceFingerprint.objects.get(user=user, device_id=device_id)
        device.is_trusted = is_trusted
        device.save()
        
        # Log security event
        SecurityLog.objects.create(
            user=user,
            event_type='device_added' if is_trusted else 'suspicious_activity',
            description=f'Device {"trusted" if is_trusted else "untrusted"}: {device.device_name}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_id=device_id
        )
        
        return Response({
            'status': 'success',
            'message': f'Device {"trusted" if is_trusted else "untrusted"} successfully',
            'data': {
                'device_name': device.device_name,
                'is_trusted': device.is_trusted
            }
        }, status=status.HTTP_200_OK)
        
    except DeviceFingerprint.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def security_logs(request):
    """Get user's security logs."""
    user = request.user
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    logs = SecurityLog.objects.filter(user=user).order_by('-created_at')[offset:offset + page_size]
    total_count = SecurityLog.objects.filter(user=user).count()
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'event_type': log.event_type,
            'description': log.description,
            'ip_address': log.ip_address,
            'device_id': log.device_id,
            'metadata': log.metadata,
            'created_at': log.created_at
        })
    
    return Response({
        'status': 'success',
        'data': {
            'security_logs': logs_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        }
    }, status=status.HTTP_200_OK)
