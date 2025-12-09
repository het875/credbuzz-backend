"""
Custom Throttling Classes for CredBuzz API
============================================
Rate limiting for sensitive operations like login, OTP, and password reset.
"""

from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """
    Rate limit for login attempts.
    Uses IP address as the identifier for anonymous users.
    """
    scope = 'login'
    
    def get_cache_key(self, request, view):
        # Use IP address for login attempts
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class OTPRateThrottle(SimpleRateThrottle):
    """
    Rate limit for OTP requests.
    Uses phone/email + IP combination to prevent abuse.
    """
    scope = 'otp'
    
    def get_cache_key(self, request, view):
        # Combine IP with phone/email for OTP rate limiting
        ident = self.get_ident(request)
        
        # Try to get phone or email from request
        phone = request.data.get('phone_number', '')
        email = request.data.get('email', '')
        identifier = phone or email or ''
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"{ident}_{identifier}"
        }


class SensitiveOperationThrottle(SimpleRateThrottle):
    """
    Rate limit for sensitive operations like password change, 
    bank details update, etc.
    """
    scope = 'sensitive'
    
    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
            
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class RegistrationRateThrottle(SimpleRateThrottle):
    """
    Rate limit for registration attempts.
    Prevents mass account creation.
    """
    rate = '5/hour'  # 5 registration attempts per hour per IP
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"registration_{ident}"


class PasswordResetThrottle(SimpleRateThrottle):
    """
    Rate limit for password reset requests.
    Prevents email/SMS bombing.
    """
    rate = '3/hour'  # 3 password reset requests per hour
    
    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        email = request.data.get('email', '')
        return f"password_reset_{ident}_{email}"


class KYCUploadThrottle(SimpleRateThrottle):
    """
    Rate limit for KYC document uploads.
    Prevents storage abuse.
    """
    rate = '20/hour'  # 20 uploads per hour per user
    
    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
            
        return f"kyc_upload_{ident}"
