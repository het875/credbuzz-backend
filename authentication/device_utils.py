"""
Device detection and fingerprinting utilities.
"""
import hashlib
import json
from user_agents import parse
from django.utils import timezone
from .models import DeviceFingerprint, LoginHistory, UserToken


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_user_agent(user_agent_string):
    """Parse user agent string to extract device information."""
    if not user_agent_string:
        return {
            'browser': 'Unknown',
            'browser_version': 'Unknown',
            'os': 'Unknown',
            'os_version': 'Unknown',
            'device': 'Unknown',
            'device_type': 'Unknown'
        }
    
    user_agent = parse(user_agent_string)
    
    return {
        'browser': user_agent.browser.family,
        'browser_version': user_agent.browser.version_string,
        'os': user_agent.os.family,
        'os_version': user_agent.os.version_string,
        'device': user_agent.device.family,
        'device_type': get_device_type(user_agent)
    }


def get_device_type(user_agent):
    """Determine device type from user agent."""
    if user_agent.is_mobile:
        return 'mobile'
    elif user_agent.is_tablet:
        return 'tablet'
    elif user_agent.is_pc:
        return 'desktop'
    else:
        return 'unknown'


def generate_device_id(request):
    """Generate unique device ID based on request characteristics."""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
    
    # Create device fingerprint
    fingerprint_data = f"{user_agent}|{accept_language}|{accept_encoding}"
    device_id = hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    return device_id


def create_device_fingerprint(user, request, device_info=None):
    """Create or update device fingerprint."""
    device_id = generate_device_id(request)
    user_agent_info = parse_user_agent(request.META.get('HTTP_USER_AGENT', ''))
    
    # Additional device info from frontend (if provided)
    if device_info:
        screen_resolution = device_info.get('screen_resolution')
        timezone_str = device_info.get('timezone')
        language = device_info.get('language')
    else:
        screen_resolution = None
        timezone_str = None
        language = request.META.get('HTTP_ACCEPT_LANGUAGE', '').split(',')[0] if request.META.get('HTTP_ACCEPT_LANGUAGE') else None
    
    # Create fingerprint hash
    fingerprint_data = {
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'browser': user_agent_info['browser'],
        'os': user_agent_info['os'],
        'device': user_agent_info['device'],
        'screen_resolution': screen_resolution,
        'timezone': timezone_str,
        'language': language
    }
    fingerprint_hash = hashlib.sha256(json.dumps(fingerprint_data, sort_keys=True).encode()).hexdigest()
    
    # Create device name
    device_name = f"{user_agent_info['browser']} on {user_agent_info['os']}"
    if user_agent_info['device'] and user_agent_info['device'] != 'Other':
        device_name = f"{user_agent_info['device']} - {device_name}"
    
    # Get or create device fingerprint
    fingerprint, created = DeviceFingerprint.objects.get_or_create(
        user=user,
        device_id=device_id,
        defaults={
            'fingerprint_hash': fingerprint_hash,
            'device_name': device_name,
            'device_type': user_agent_info['device_type'],
            'browser_name': user_agent_info['browser'],
            'browser_version': user_agent_info['browser_version'],
            'os_name': user_agent_info['os'],
            'os_version': user_agent_info['os_version'],
            'screen_resolution': screen_resolution,
            'timezone': timezone_str,
            'language': language
        }
    )
    
    if not created:
        # Update existing fingerprint
        fingerprint.fingerprint_hash = fingerprint_hash
        fingerprint.device_name = device_name
        fingerprint.device_type = user_agent_info['device_type']
        fingerprint.browser_name = user_agent_info['browser']
        fingerprint.browser_version = user_agent_info['browser_version']
        fingerprint.os_name = user_agent_info['os']
        fingerprint.os_version = user_agent_info['os_version']
        fingerprint.screen_resolution = screen_resolution
        fingerprint.timezone = timezone_str
        fingerprint.language = language
        fingerprint.mark_as_seen()
    else:
        fingerprint.mark_as_seen()
    
    return fingerprint


def log_login_attempt(user, request, status, login_method='email', failure_reason=None):
    """Log login attempt in login history."""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    user_agent_info = parse_user_agent(user_agent)
    
    # Create device name
    device_name = f"{user_agent_info['browser']} on {user_agent_info['os']}"
    if user_agent_info['device'] and user_agent_info['device'] != 'Other':
        device_name = f"{user_agent_info['device']} - {device_name}"
    
    # Determine login type
    login_type = 'web'  # Default
    if 'mobile' in user_agent.lower() or user_agent_info['device_type'] == 'mobile':
        login_type = 'mobile'
    elif 'api' in request.path.lower():
        login_type = 'api'
    
    login_history = LoginHistory.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        device_name=device_name,
        device_type=user_agent_info['device_type'],
        browser_name=user_agent_info['browser'],
        os_name=user_agent_info['os'],
        login_method=login_method,
        login_type=login_type,
        status=status,
        failure_reason=failure_reason
    )
    
    return login_history


def store_user_token(user, token, token_type, request, expires_at):
    """Store JWT token with device information."""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    user_agent_info = parse_user_agent(user_agent)
    device_id = generate_device_id(request)
    
    # Create device name
    device_name = f"{user_agent_info['browser']} on {user_agent_info['os']}"
    if user_agent_info['device'] and user_agent_info['device'] != 'Other':
        device_name = f"{user_agent_info['device']} - {device_name}"
    
    # Create token hash
    token_hash = UserToken.create_token_hash(token)
    
    # Store token
    user_token = UserToken.objects.create(
        user=user,
        token_hash=token_hash,
        token_type=token_type,
        device_id=device_id,
        device_name=device_name,
        device_type=user_agent_info['device_type'],
        browser_name=user_agent_info['browser'],
        os_name=user_agent_info['os'],
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at
    )
    
    return user_token


def cleanup_expired_tokens(user=None):
    """Clean up expired tokens."""
    query = UserToken.objects.filter(
        expires_at__lt=timezone.now(),
        is_active=True
    )
    
    if user:
        query = query.filter(user=user)
    
    expired_count = query.count()
    query.update(is_active=False, revoked_at=timezone.now())
    
    return expired_count


def get_active_devices(user):
    """Get list of active devices for a user."""
    return DeviceFingerprint.objects.filter(
        user=user,
        last_seen__gte=timezone.now() - timezone.timedelta(days=30)
    ).order_by('-last_seen')


def revoke_device_tokens(user, device_id):
    """Revoke all tokens for a specific device."""
    tokens = UserToken.objects.filter(
        user=user,
        device_id=device_id,
        is_active=True
    )
    
    revoked_count = tokens.count()
    tokens.update(is_active=False, revoked_at=timezone.now())
    
    return revoked_count


def is_suspicious_login(user, request):
    """Check if login attempt is suspicious."""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Check recent failed attempts from this IP
    recent_failures = LoginHistory.objects.filter(
        ip_address=ip_address,
        status='failed',
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    ).count()
    
    if recent_failures >= 5:
        return True, f"Multiple failed attempts from IP {ip_address}"
    
    # Check if user has logged in from this device before
    device_id = generate_device_id(request)
    known_device = DeviceFingerprint.objects.filter(
        user=user,
        device_id=device_id
    ).exists()
    
    if not known_device:
        # New device - check if location is very different
        # This is a simplified check - in production, you'd use geolocation
        recent_logins = LoginHistory.objects.filter(
            user=user,
            status='success',
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).exclude(ip_address=ip_address)[:5]
        
        if recent_logins.count() > 0:
            return True, "Login from new device"
    
    return False, "Normal login"