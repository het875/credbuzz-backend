"""
Custom authentication for users_auth app
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User, UserSession
from .jwt_utils import JWTManager
import jwt


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT Authentication class with inactivity timeout check.
    
    Features:
    - Validates JWT access tokens
    - Checks session inactivity (30 minutes like bank apps)
    - Updates last activity on each request
    - Returns user info from token for middleware use
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, auth_info) or None.
        
        The auth_info (request.auth) contains the full token payload including:
        - user_id, email, username, user_code, user_role
        - app_access, feature_access (RBAC permissions)
        """
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        try:
            # Extract token from header
            auth_parts = auth_header.split()
            
            if len(auth_parts) != 2:
                raise AuthenticationFailed('Invalid authorization header format.')
            
            if auth_parts[0].lower() != 'bearer':
                raise AuthenticationFailed('Invalid token prefix. Use "Bearer".')
            
            token = auth_parts[1]
            
            # Decode and validate token
            try:
                payload = JWTManager.decode_token(token)
            except jwt.ExpiredSignatureError:
                raise AuthenticationFailed('Token has expired.')
            except jwt.InvalidTokenError as e:
                raise AuthenticationFailed(f'Invalid token: {str(e)}')
            
            # Verify token type
            if payload.get('token_type') != 'access':
                raise AuthenticationFailed('Invalid token type.')
            
            # Get user
            user_id = payload.get('user_id')
            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                raise AuthenticationFailed('User not found or inactive.')
            
            # Check session inactivity timeout (like bank apps)
            # This requires finding the session from a refresh token
            # For access tokens, we check the inactivity from user's sessions
            self._check_session_inactivity(user)
            
            return (user, payload)
            
        except AuthenticationFailed:
            raise
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def _check_session_inactivity(self, user):
        """
        Check if user has any active session that's not expired due to inactivity.
        Also updates the last activity timestamp.
        """
        inactivity_timeout = JWTManager.get_inactivity_timeout()
        
        # Get user's active sessions
        active_sessions = UserSession.objects.filter(
            user=user,
            is_active=True
        )
        
        if not active_sessions.exists():
            # No active session means token might be from before we added this check
            # Allow it but log warning
            return
        
        # Check if all sessions have expired due to inactivity
        all_inactive = True
        for session in active_sessions:
            if not session.is_inactive_expired(inactivity_timeout):
                all_inactive = False
                # Update activity for the valid session
                session.update_activity()
                break
        
        if all_inactive:
            # Invalidate all sessions
            active_sessions.update(is_active=False)
            raise AuthenticationFailed(
                'Session expired due to inactivity. Please login again.'
            )
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return 'Bearer'


def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Get user agent from request
    """
    return request.META.get('HTTP_USER_AGENT', '')
