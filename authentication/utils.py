"""
Utility functions for authentication app.
"""
import random
import string
import requests
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def generate_otp(length=6):
    """Generate a random OTP of specified length."""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(user, otp_type='email_verification', subject=None):
    """
    Send OTP email to user and save OTP to database.
    
    Args:
        user: User instance
        otp_type: Type of OTP ('email_verification', 'password_reset', 'login_verification')
        subject: Custom email subject
    
    Returns:
        tuple: (success: bool, otp: str, message: str)
    """
    try:
        # Generate OTP and save to user
        otp = user.generate_otp('email')
        
        # Determine email subject and content based on OTP type
        if otp_type == 'email_verification':
            email_subject = subject or 'Verify Your Email - CredBuzz'
            email_body = f"""
Dear {user.get_full_name() or user.email},

Welcome to CredBuzz! Please verify your email address using the OTP below:

OTP: {otp}

This OTP will expire in 10 minutes for security reasons.

If you didn't request this verification, please ignore this email.

Best regards,
CredBuzz Team
            """
            
        elif otp_type == 'password_reset':
            email_subject = subject or 'Password Reset OTP - CredBuzz'
            email_body = f"""
Dear {user.get_full_name() or user.email},

You requested to reset your password. Please use the OTP below to proceed:

OTP: {otp}

This OTP will expire in 10 minutes for security reasons.

If you didn't request a password reset, please ignore this email and your password will remain unchanged.

Best regards,
CredBuzz Team
            """
            
        elif otp_type == 'login_verification':
            email_subject = subject or 'Login Verification OTP - CredBuzz'
            email_body = f"""
Dear {user.get_full_name() or user.email},

Someone is trying to log in to your CredBuzz account. Please use the OTP below to verify:

OTP: {otp}

This OTP will expire in 10 minutes for security reasons.

If this wasn't you, please secure your account immediately.

Best regards,
CredBuzz Team
            """
        else:
            email_subject = subject or 'OTP Verification - CredBuzz'
            email_body = f"""
Dear {user.get_full_name() or user.email},

Your OTP for verification is: {otp}

This OTP will expire in 10 minutes.

Best regards,
CredBuzz Team
            """

        # Send email
        success = send_mail(
            subject=email_subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        if success:
            return True, otp, 'OTP sent successfully'
        else:
            return False, None, 'Failed to send email'
            
    except Exception as e:
        return False, None, f'Error sending email: {str(e)}'


def send_welcome_email(user):
    """Send welcome email after successful registration."""
    try:
        subject = 'Welcome to CredBuzz!'
        message = f"""
Dear {user.get_full_name() or user.email},

Welcome to CredBuzz! Your account has been successfully created.

Your User ID: {user.id}
Email: {user.email}

Please verify your email address to activate all features of your account.

Best regards,
CredBuzz Team
        """
        
        success = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return success
        
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False


def send_password_changed_notification(user):
    """Send notification email when password is changed."""
    try:
        subject = 'Password Changed Successfully - CredBuzz'
        message = f"""
Dear {user.get_full_name() or user.email},

This email confirms that your CredBuzz account password has been successfully changed.

If you did not make this change, please contact our support team immediately.

Changed at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Best regards,
CredBuzz Team
        """
        
        success = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return success
        
    except Exception as e:
        print(f"Error sending password change notification: {str(e)}")
        return False


def is_otp_expired(otp_updated_at, expire_minutes=10):
    """Check if OTP is expired."""
    if not otp_updated_at:
        return True
    
    now = timezone.now()
    return (now - otp_updated_at).total_seconds() > expire_minutes * 60


def send_sms_otp(user, mobile_number, otp_type='mobile_verification'):
    """
    Send OTP via Fast2SMS API.
    
    Args:
        user: User instance
        mobile_number: Mobile number to send SMS to
        otp_type: Type of OTP ('mobile_verification', 'password_reset', 'login_verification')
    
    Returns:
        tuple: (success: bool, otp: str, message: str)
    """
    try:
        # Generate OTP and save to user
        otp = user.generate_otp('mobile')
        
        # Determine message based on OTP type
        if otp_type == 'mobile_verification':
            message = f"Your CredBuzz mobile verification OTP is {otp}. Valid for 10 minutes. Do not share with anyone."
        elif otp_type == 'password_reset':
            message = f"Your CredBuzz password reset OTP is {otp}. Valid for 10 minutes. Do not share with anyone."
        elif otp_type == 'login_verification':
            message = f"Your CredBuzz login verification OTP is {otp}. Valid for 10 minutes. Do not share with anyone."
        else:
            message = f"Your CredBuzz OTP is {otp}. Valid for 10 minutes. Do not share with anyone."
        
        # Prepare Fast2SMS API request
        url = settings.FAST2SMS_BASE_URL
        headers = {
            'authorization': settings.FAST2SMS_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'route': settings.FAST2SMS_ROUTE,
            'message': message,
            'flash': settings.FAST2SMS_FLASH,
            'numbers': mobile_number.replace('+', '').replace(' ', '')  # Clean mobile number
        }
        
        # Send SMS via Fast2SMS API
        response = requests.get(url, headers=headers, params=payload, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('return'):  # Fast2SMS returns True for success
                return True, otp, 'SMS sent successfully'
            else:
                error_message = response_data.get('message', 'Failed to send SMS')
                return False, None, f'SMS API error: {error_message}'
        else:
            return False, None, f'SMS API error: HTTP {response.status_code}'
            
    except requests.exceptions.RequestException as e:
        return False, None, f'Network error sending SMS: {str(e)}'
    except Exception as e:
        return False, None, f'Error sending SMS: {str(e)}'


def send_bulk_sms(mobile_numbers, message):
    """
    Send bulk SMS to multiple numbers.
    
    Args:
        mobile_numbers: List of mobile numbers
        message: Message to send
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        if not mobile_numbers:
            return False, 'No mobile numbers provided'
        
        # Clean and format mobile numbers
        clean_numbers = []
        for number in mobile_numbers:
            clean_number = str(number).replace('+', '').replace(' ', '')
            if len(clean_number) >= 10:
                clean_numbers.append(clean_number)
        
        if not clean_numbers:
            return False, 'No valid mobile numbers found'
        
        # Prepare Fast2SMS API request
        url = settings.FAST2SMS_BASE_URL
        headers = {
            'authorization': settings.FAST2SMS_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'route': 'q',  # Quick route for bulk SMS
            'message': message,
            'flash': '0',  # Normal SMS for bulk
            'numbers': ','.join(clean_numbers)
        }
        
        # Send bulk SMS
        response = requests.get(url, headers=headers, params=payload, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('return'):
                return True, f'Bulk SMS sent to {len(clean_numbers)} numbers'
            else:
                error_message = response_data.get('message', 'Failed to send bulk SMS')
                return False, f'Bulk SMS API error: {error_message}'
        else:
            return False, f'Bulk SMS API error: HTTP {response.status_code}'
            
    except Exception as e:
        return False, f'Error sending bulk SMS: {str(e)}'


def validate_mobile_number(mobile_number):
    """
    Validate mobile number format for SMS sending.
    
    Args:
        mobile_number: Mobile number to validate
    
    Returns:
        tuple: (is_valid: bool, cleaned_number: str, message: str)
    """
    if not mobile_number:
        return False, None, 'Mobile number is required'
    
    # Clean the number
    clean_number = str(mobile_number).replace('+', '').replace(' ', '').replace('-', '')
    
    # Check if it's all digits
    if not clean_number.isdigit():
        return False, None, 'Mobile number should contain only digits'
    
    # Check length (10 digits for Indian numbers)
    if len(clean_number) < 10:
        return False, None, 'Mobile number should be at least 10 digits'
    
    if len(clean_number) > 15:
        return False, None, 'Mobile number should not exceed 15 digits'
    
    # For Indian numbers, add country code if not present
    if len(clean_number) == 10 and clean_number[0] in '6789':
        clean_number = '91' + clean_number
    
    return True, clean_number, 'Valid mobile number'
