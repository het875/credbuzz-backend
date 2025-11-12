"""
Security utilities for blocking logic, risk scoring, IP management, etc.
"""
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from accounts.models import UserAccount, SecuritySettings, LoginActivity
import ipaddress


def is_user_blocked(user_code):
    """
    Check if a user is currently blocked.
    
    Args:
        user_code: UserAccount object or user code string
    
    Returns:
        Tuple (is_blocked, reason, blocked_until)
    """
    if isinstance(user_code, str):
        try:
            user = UserAccount.objects.get(user_code=user_code)
        except UserAccount.DoesNotExist:
            return False, None, None
    else:
        user = user_code
    
    if user.blocked_until and user.blocked_until > timezone.now():
        return True, user.user_block_reason, user.blocked_until
    elif user.blocked_until and user.blocked_until <= timezone.now():
        # Block time expired, unblock user
        user.user_blocked = 0
        user.user_block_reason = None
        user.blocked_until = None
        user.save()
        return False, None, None
    
    return False, None, None


def block_user(user, reason, duration_minutes=60):
    """
    Block a user temporarily.
    
    Args:
        user: UserAccount object
        reason: Reason for blocking
        duration_minutes: How long to block (in minutes)
    """
    user.user_blocked += 1
    user.user_block_reason = reason
    user.blocked_until = timezone.now() + timedelta(minutes=duration_minutes)
    user.save()


def unblock_user(user):
    """
    Unblock a user.
    
    Args:
        user: UserAccount object
    """
    user.user_blocked = 0
    user.user_block_reason = None
    user.blocked_until = None
    user.save()


def is_email_otp_blocked(user):
    """
    Check if email OTP is blocked due to max attempts.
    
    Args:
        user: UserAccount object
    
    Returns:
        Tuple (is_blocked, time_remaining_seconds)
    """
    if user.email_blocked_until and user.email_blocked_until > timezone.now():
        remaining = (user.email_blocked_until - timezone.now()).total_seconds()
        return True, int(remaining)
    elif user.email_blocked_until and user.email_blocked_until <= timezone.now():
        user.email_otp_attempts = 0
        user.email_blocked_until = None
        user.save()
        return False, 0
    
    return False, 0


def is_mobile_otp_blocked(user):
    """
    Check if mobile OTP is blocked due to max attempts.
    
    Args:
        user: UserAccount object
    
    Returns:
        Tuple (is_blocked, time_remaining_seconds)
    """
    if user.mobile_blocked_until and user.mobile_blocked_until > timezone.now():
        remaining = (user.mobile_blocked_until - timezone.now()).total_seconds()
        return True, int(remaining)
    elif user.mobile_blocked_until and user.mobile_blocked_until <= timezone.now():
        user.mobile_otp_attempts = 0
        user.mobile_blocked_until = None
        user.save()
        return False, 0
    
    return False, 0


def increment_otp_attempts(user, otp_type):
    """
    Increment OTP attempts and block if max attempts exceeded.
    
    Args:
        user: UserAccount object
        otp_type: 'email' or 'mobile'
    
    Returns:
        Tuple (is_blocked, remaining_attempts)
    """
    max_attempts = settings.OTP_MAX_ATTEMPTS.get(otp_type, 3)
    cooldown = settings.OTP_COOLDOWN.get('registration', 60)
    
    if otp_type == 'email':
        user.email_otp_attempts += 1
        if user.email_otp_attempts >= max_attempts:
            user.email_blocked_until = timezone.now() + timedelta(seconds=cooldown)
            user.save()
            return True, 0
        user.save()
        return False, max_attempts - user.email_otp_attempts
    
    elif otp_type == 'mobile':
        user.mobile_otp_attempts += 1
        if user.mobile_otp_attempts >= max_attempts:
            user.mobile_blocked_until = timezone.now() + timedelta(seconds=cooldown)
            user.save()
            return True, 0
        user.save()
        return False, max_attempts - user.mobile_otp_attempts
    
    return False, 0


def reset_otp_attempts(user, otp_type):
    """
    Reset OTP attempts after successful verification.
    
    Args:
        user: UserAccount object
        otp_type: 'email' or 'mobile'
    """
    if otp_type == 'email':
        user.email_otp_attempts = 0
        user.email_blocked_until = None
    elif otp_type == 'mobile':
        user.mobile_otp_attempts = 0
        user.mobile_blocked_until = None
    
    user.save()


def calculate_login_risk_score(ip_address, user, device_info, previous_logins=None):
    """
    Calculate risk score for a login attempt.
    
    Args:
        ip_address: IP address of login attempt
        user: UserAccount object
        device_info: Device information dict
        previous_logins: QuerySet of previous login activities
    
    Returns:
        Risk score (0-100)
    """
    risk_score = 0
    
    # Risk: New IP address (high risk)
    if previous_logins and previous_logins.count() > 0:
        recent_ips = set(previous_logins.values_list('ip_address', flat=True)[:5])
        if ip_address not in recent_ips:
            risk_score += 20
    
    # Risk: Impossible travel (high risk)
    if previous_logins and previous_logins.count() > 0:
        last_login = previous_logins.first()
        if last_login.location_info and 'city' in last_login.location_info:
            # This would require actual location data from IP geolocation API
            pass
    
    # Risk: Unusual device (medium risk)
    if previous_logins and previous_logins.count() > 0:
        recent_devices = set()
        for login in previous_logins[:5]:
            if login.device_info and 'user_agent' in login.device_info:
                recent_devices.add(login.device_info['user_agent'])
        
        if device_info.get('user_agent') not in recent_devices:
            risk_score += 15
    
    # Risk: Login outside business hours (low risk)
    current_hour = timezone.now().hour
    if current_hour < 6 or current_hour > 22:
        risk_score += 5
    
    # Risk: User is marked as suspicious
    if user.is_blocked > 0:
        risk_score += 10
    
    return min(risk_score, 100)


def is_ip_whitelisted(ip_address, user):
    """
    Check if IP address is in user's whitelist.
    
    Args:
        ip_address: IP address to check
        user: UserAccount object
    
    Returns:
        True if whitelisted or whitelist is empty, False otherwise
    """
    try:
        security_settings = user.security_settings
        if security_settings.allowed_ip_whitelist:
            for allowed_ip in security_settings.allowed_ip_whitelist:
                try:
                    if ipaddress.ip_address(ip_address) in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                except ValueError:
                    continue
            return False
    except SecuritySettings.DoesNotExist:
        return True
    
    return True


def get_device_info_from_user_agent(user_agent):
    """
    Parse user agent to extract device information.
    
    Args:
        user_agent: HTTP User-Agent header
    
    Returns:
        Dictionary with browser, os, device_type
    """
    info = {
        'user_agent': user_agent,
        'browser': 'Unknown',
        'os': 'Unknown',
        'device_type': 'Unknown'
    }
    
    user_agent_lower = user_agent.lower()
    
    # Detect OS
    if 'windows' in user_agent_lower:
        info['os'] = 'Windows'
    elif 'macintosh' in user_agent_lower or 'mac os' in user_agent_lower:
        info['os'] = 'macOS'
    elif 'linux' in user_agent_lower:
        info['os'] = 'Linux'
    elif 'iphone' in user_agent_lower:
        info['os'] = 'iOS'
    elif 'android' in user_agent_lower:
        info['os'] = 'Android'
    
    # Detect Browser
    if 'chrome' in user_agent_lower:
        info['browser'] = 'Chrome'
    elif 'safari' in user_agent_lower:
        info['browser'] = 'Safari'
    elif 'firefox' in user_agent_lower:
        info['browser'] = 'Firefox'
    elif 'edge' in user_agent_lower:
        info['browser'] = 'Edge'
    
    # Detect Device Type
    if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
        info['device_type'] = 'Mobile'
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
        info['device_type'] = 'Tablet'
    else:
        info['device_type'] = 'Desktop'
    
    return info


def flag_suspicious_activity(user, reason, login_activity=None):
    """
    Flag a login or activity as suspicious.
    
    Args:
        user: UserAccount object
        reason: Reason for flagging
        login_activity: LoginActivity object (optional)
    """
    if login_activity:
        login_activity.is_suspicious = True
        login_activity.save()
