"""
OTP Service for generating, sending, and verifying OTPs.
"""
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import OTPRecord, UserAccount
from accounts.utils.code_generator import generate_otp, generate_unique_id
from accounts.utils.encryption import hash_otp, verify_otp
from accounts.utils.security import increment_otp_attempts, reset_otp_attempts, is_email_otp_blocked, is_mobile_otp_blocked


class OTPService:
    """Service for OTP operations."""
    
    @staticmethod
    def generate_otp_record(user, otp_type, otp_purpose, ip_address, send_to_email=None, send_to_mobile=None):
        """
        Generate and store OTP record.
        
        Args:
            user: UserAccount object
            otp_type: Type of OTP (email, mobile, both, etc.)
            otp_purpose: Purpose of OTP (registration, login, etc.)
            ip_address: IP address of the request
            send_to_email: Email to send OTP to
            send_to_mobile: Mobile to send OTP to
        
        Returns:
            OTPRecord object with generated OTP(s)
        """
        # Get OTP validity in minutes
        validity_minutes = settings.OTP_VALIDITY.get(otp_purpose.split('_')[0], 10)
        expires_at = timezone.now() + timedelta(minutes=validity_minutes)
        
        otp_code = generate_otp()
        email_otp = None
        mobile_otp = None
        
        if otp_type in ['email', 'both']:
            email_otp = generate_otp()
        
        if otp_type in ['mobile', 'both', 'aadhaar']:
            mobile_otp = generate_otp()
        
        otp_id = generate_unique_id(prefix='OTP_')
        
        otp_record = OTPRecord.objects.create(
            id=otp_id,
            user_code=user,
            otp_type=otp_type,
            otp_purpose=otp_purpose,
            otp_code=hash_otp(otp_code),
            email_otp=hash_otp(email_otp) if email_otp else None,
            mobile_otp=hash_otp(mobile_otp) if mobile_otp else None,
            sent_to_email=send_to_email or user.email,
            sent_to_mobile=send_to_mobile or user.mobile,
            expires_at=expires_at,
            ip_address=ip_address,
        )
        
        # Return OTP for sending (not stored plain in DB)
        return {
            'otp_record_id': otp_id,
            'otp_code': otp_code,
            'email_otp': email_otp,
            'mobile_otp': mobile_otp,
            'expires_at': expires_at,
            'validity_minutes': validity_minutes,
        }
    
    @staticmethod
    def verify_otp(otp_record, provided_otp, otp_field='otp_code'):
        """
        Verify provided OTP against stored OTP.
        
        Args:
            otp_record: OTPRecord object
            provided_otp: OTP provided by user
            otp_field: Which OTP field to verify ('otp_code', 'email_otp', 'mobile_otp')
        
        Returns:
            Tuple (is_valid, error_message)
        """
        # Check if OTP is already used
        if otp_record.is_used:
            return False, "OTP has already been used."
        
        # Check if OTP has expired
        if otp_record.expires_at < timezone.now():
            return False, "OTP has expired."
        
        # Get the stored OTP hash
        if otp_field == 'email_otp':
            stored_otp_hash = otp_record.email_otp
        elif otp_field == 'mobile_otp':
            stored_otp_hash = otp_record.mobile_otp
        else:
            stored_otp_hash = otp_record.otp_code
        
        # Verify OTP
        if not verify_otp(provided_otp, stored_otp_hash):
            # Increment attempts
            otp_record.attempt_count += 1
            otp_record.save()
            
            max_attempts = settings.OTP_MAX_ATTEMPTS.get(
                'email' if otp_field == 'email_otp' else 'mobile',
                3
            )
            remaining_attempts = max_attempts - otp_record.attempt_count
            
            if remaining_attempts <= 0:
                otp_record.is_used = True
                otp_record.save()
                return False, f"Too many incorrect OTP attempts. OTP has been locked."
            
            return False, f"Incorrect OTP. {remaining_attempts} attempts remaining."
        
        return True, None
    
    @staticmethod
    def mark_otp_as_used(otp_record):
        """
        Mark OTP as used after successful verification.
        """
        otp_record.is_used = True
        otp_record.verified_at = timezone.now()
        otp_record.save()
    
    @staticmethod
    def get_latest_otp(user, otp_purpose):
        """
        Get the latest OTP record for a specific purpose.
        
        Args:
            user: UserAccount object
            otp_purpose: Purpose of OTP
        
        Returns:
            OTPRecord object or None
        """
        try:
            return OTPRecord.objects.filter(
                user_code=user,
                otp_purpose=otp_purpose,
                is_used=False
            ).latest('created_at')
        except OTPRecord.DoesNotExist:
            return None
    
    @staticmethod
    def cleanup_expired_otps():
        """
        Delete all expired OTPs (async task).
        """
        expired_count = OTPRecord.objects.filter(
            expires_at__lt=timezone.now(),
            is_used=False
        ).delete()[0]
        
        return f"Deleted {expired_count} expired OTPs"
    
    @staticmethod
    def check_otp_rate_limit(user, otp_type):
        """
        Check if user has hit rate limit for OTP requests.
        
        Args:
            user: UserAccount object
            otp_type: 'email' or 'mobile'
        
        Returns:
            Tuple (is_blocked, cooldown_seconds)
        """
        if otp_type == 'email':
            is_blocked, remaining = is_email_otp_blocked(user)
            return is_blocked, remaining
        elif otp_type == 'mobile':
            is_blocked, remaining = is_mobile_otp_blocked(user)
            return is_blocked, remaining
        
        return False, 0
