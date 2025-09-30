"""
ERP Utilities
Email, SMS, OTP, Device Detection, and Security utilities for ERP system
"""
import secrets
import random
import string
import hashlib
import requests
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import get_user_model
from user_agents import parse
import json

logger = logging.getLogger(__name__)
User = get_user_model()


def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


def generate_unique_user_id():
    """Generate unique 5-character alphanumeric ID for users."""
    while True:
        user_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if not User.objects.filter(id=user_id).exists():
            return user_id


def send_email_otp(email, otp, purpose='verification'):
    """Send OTP via email."""
    try:
        subject_map = {
            'verification': 'Email Verification - CredBuzz',
            'login': 'Login OTP - CredBuzz',
            'password_reset': 'Password Reset OTP - CredBuzz',
            'business': 'Business Email Verification - CredBuzz',
            'aadhaar': 'Aadhaar Verification OTP - CredBuzz'
        }
        
        subject = subject_map.get(purpose, 'OTP Verification - CredBuzz')
        
        message = f"""
        Dear User,
        
        Your OTP for {purpose} is: {otp}
        
        This OTP is valid for {settings.OTP_EXPIRY_MINUTES} minutes.
        Please do not share this OTP with anyone.
        
        If you didn't request this OTP, please ignore this email.
        
        Best regards,
        CredBuzz Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"Email OTP sent successfully to {email} for {purpose}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email OTP to {email}: {str(e)}")
        return False


def send_sms_otp(mobile, otp, purpose='verification'):
    """Send OTP via Fast2SMS."""
    try:
        # Remove any country code and format mobile
        if mobile.startswith('+91'):
            mobile = mobile[3:]
        elif mobile.startswith('91') and len(mobile) == 12:
            mobile = mobile[2:]
        
        # Ensure mobile is 10 digits
        if len(mobile) != 10 or not mobile.isdigit():
            logger.error(f"Invalid mobile number format: {mobile}")
            return False
        
        purpose_map = {
            'verification': 'account verification',
            'login': 'login',
            'password_reset': 'password reset',
            'business': 'business verification',
            'aadhaar': 'Aadhaar verification'
        }
        
        purpose_text = purpose_map.get(purpose, 'verification')
        message = f"Your CredBuzz OTP for {purpose_text} is {otp}. Valid for {settings.OTP_EXPIRY_MINUTES} minutes. Do not share."
        
        # Fast2SMS API payload
        payload = {
            'authorization': settings.FAST2SMS_API_KEY,
            'route': settings.FAST2SMS_ROUTE,
            'numbers': mobile,
            'message': message,
            'flash': settings.FAST2SMS_FLASH
        }
        
        # Send SMS
        response = requests.post(settings.FAST2SMS_BASE_URL, data=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('return'):
                logger.info(f"SMS OTP sent successfully to {mobile} for {purpose}")
                return True
            else:
                logger.error(f"Fast2SMS API error: {result}")
                return False
        else:
            logger.error(f"Fast2SMS HTTP error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Network error sending SMS to {mobile}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send SMS OTP to {mobile}: {str(e)}")
        return False


def get_device_fingerprint(request):
    """Extract device information from request."""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    parsed_ua = parse(user_agent)
    
    # Get IP address considering proxies
    ip = get_client_ip(request)
    
    # Create device fingerprint
    device_info = {
        'browser': f"{parsed_ua.browser.family} {parsed_ua.browser.version_string}",
        'os': f"{parsed_ua.os.family} {parsed_ua.os.version_string}",
        'device': f"{parsed_ua.device.family} {parsed_ua.device.brand} {parsed_ua.device.model}",
        'is_mobile': parsed_ua.is_mobile,
        'is_tablet': parsed_ua.is_tablet,
        'is_desktop': not (parsed_ua.is_mobile or parsed_ua.is_tablet),
        'user_agent': user_agent,
        'ip_address': ip
    }
    
    # Generate device hash
    device_string = f"{device_info['browser']}_{device_info['os']}_{device_info['device']}_{ip}"
    device_hash = hashlib.sha256(device_string.encode()).hexdigest()[:16]
    
    return {
        'device_hash': device_hash,
        'device_info': device_info,
        'device_name': f"{parsed_ua.browser.family} on {parsed_ua.os.family}"
    }


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_suspicious_login(user, device_info, ip_address):
    """Check if login attempt is suspicious."""
    suspicious_reasons = []
    
    # Check for new device
    from .models import LoginActivity
    recent_logins = LoginActivity.objects.filter(
        user=user,
        status='success',
        login_timestamp__gte=timezone.now() - timedelta(days=30)
    ).values_list('device_info', flat=True)
    
    device_seen = False
    for login_device_info in recent_logins:
        if login_device_info and login_device_info.get('device_hash') == device_info['device_hash']:
            device_seen = True
            break
    
    if not device_seen:
        suspicious_reasons.append('new_device')
    
    # Check for unusual time (between 2 AM and 6 AM)
    current_hour = timezone.now().hour
    if 2 <= current_hour <= 6:
        suspicious_reasons.append('unusual_time')
    
    # Check for multiple failed attempts from same IP
    recent_failures = LoginActivity.objects.filter(
        ip_address=ip_address,
        status='failed',
        login_timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if recent_failures >= 3:
        suspicious_reasons.append('multiple_failures')
    
    # Check for rapid location change (if we had location data)
    # This would require IP geolocation service
    
    return len(suspicious_reasons) > 0, suspicious_reasons


def validate_password_strength(password):
    """Validate password strength."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(char.islower() for char in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one digit")
    
    if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def sanitize_mobile_number(mobile):
    """Sanitize and validate mobile number."""
    # Remove any spaces, dashes, or brackets
    mobile = ''.join(filter(str.isdigit, mobile))
    
    # Handle country code
    if mobile.startswith('91') and len(mobile) == 12:
        mobile = mobile[2:]
    elif mobile.startswith('+91'):
        mobile = mobile[3:]
    
    # Validate Indian mobile number format
    if len(mobile) == 10 and mobile[0] in '6789':
        return mobile
    
    return None


def sanitize_email(email):
    """Sanitize and validate email."""
    if not email:
        return None
    
    email = email.strip().lower()
    
    # Basic email validation
    if '@' in email and '.' in email.split('@')[1]:
        return email
    
    return None


def log_security_event(user, event_type, description, request=None, severity='info'):
    """Log security events."""
    from .models import AuditTrail
    
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditTrail.objects.create(
        user=user,
        action=event_type,
        resource_type='security',
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        new_values={'severity': severity}
    )
    
    # Also log to Django logger
    logger.info(f"Security Event - User: {user}, Type: {event_type}, Description: {description}")


def create_audit_log(user, action, resource_type, resource_id=None, description='', 
                    old_values=None, new_values=None, request=None):
    """Create audit trail entry."""
    from .models import AuditTrail
    
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditTrail.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        old_values=old_values or {},
        new_values=new_values or {},
        ip_address=ip_address,
        user_agent=user_agent
    )


def check_rate_limit(identifier, limit_type='login', max_attempts=5, time_window=15):
    """
    Check if rate limit is exceeded.
    identifier: IP address or user ID
    limit_type: Type of rate limit (login, otp_email, otp_sms)
    max_attempts: Maximum attempts allowed
    time_window: Time window in minutes
    """
    from django.core.cache import cache
    
    key = f"rate_limit_{limit_type}_{identifier}"
    attempts = cache.get(key, 0)
    
    if attempts >= max_attempts:
        return False, f"Rate limit exceeded. Try again after {time_window} minutes."
    
    # Increment attempt count
    cache.set(key, attempts + 1, timeout=time_window * 60)
    return True, None


def validate_aadhaar_number(aadhaar):
    """Validate Aadhaar number format."""
    # Remove spaces and hyphens
    aadhaar = ''.join(filter(str.isdigit, aadhaar))
    
    if len(aadhaar) != 12:
        return False, "Aadhaar number must be 12 digits"
    
    # Verhoeff algorithm validation for Aadhaar
    # This is a simplified version - real implementation would use full Verhoeff algorithm
    if aadhaar.startswith('0000') or aadhaar.startswith('1111'):
        return False, "Invalid Aadhaar number format"
    
    return True, None


def validate_pan_number(pan):
    """Validate PAN number format."""
    if not pan or len(pan) != 10:
        return False, "PAN number must be 10 characters"
    
    pan = pan.upper()
    
    # PAN format: AAAAA9999A
    if not (pan[:5].isalpha() and pan[5:9].isdigit() and pan[9].isalpha()):
        return False, "Invalid PAN format. Should be like AAAAA9999A"
    
    return True, None


def validate_ifsc_code(ifsc):
    """Validate IFSC code format."""
    if not ifsc or len(ifsc) != 11:
        return False, "IFSC code must be 11 characters"
    
    ifsc = ifsc.upper()
    
    # IFSC format: AAAA0999999
    if not (ifsc[:4].isalpha() and ifsc[4] == '0' and ifsc[5:].isalnum()):
        return False, "Invalid IFSC format. Should be like ABCD0123456"
    
    return True, None


def mask_sensitive_data(data_type, value):
    """Mask sensitive data for display."""
    if not value:
        return "****"
    
    if data_type == 'aadhaar':
        if len(value) >= 4:
            return f"XXXX-XXXX-{value[-4:]}"
        return "XXXX-XXXX-XXXX"
    
    elif data_type == 'account_number':
        if len(value) >= 4:
            return f"XXXXX{value[-4:]}"
        return "XXXXXXXXXX"
    
    elif data_type == 'email':
        if '@' in value:
            username, domain = value.split('@', 1)
            if len(username) > 2:
                return f"{username[:2]}***@{domain}"
        return "****@****.com"
    
    elif data_type == 'mobile':
        if len(value) >= 4:
            return f"XXXXXX{value[-4:]}"
        return "XXXXXXXXXX"
    
    return "****"