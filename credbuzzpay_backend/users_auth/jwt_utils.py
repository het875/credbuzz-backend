"""
JWT Utilities for users_auth app
Custom JWT token generation and validation
"""
import jwt
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone


class JWTManager:
    """
    Custom JWT Manager for token generation and validation
    """
    
    @staticmethod
    def get_secret_key():
        """Get JWT secret key from settings"""
        return getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
    
    @staticmethod
    def get_algorithm():
        """Get JWT algorithm from settings"""
        return getattr(settings, 'JWT_ALGORITHM', 'HS256')
    
    @staticmethod
    def get_access_token_expiry():
        """Get access token expiry in minutes"""
        return getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRY_MINUTES', 60)
    
    @staticmethod
    def get_refresh_token_expiry():
        """Get refresh token expiry in days"""
        return getattr(settings, 'JWT_REFRESH_TOKEN_EXPIRY_DAYS', 7)
    
    @staticmethod
    def get_inactivity_timeout():
        """Get session inactivity timeout in minutes (like bank apps)"""
        return getattr(settings, 'JWT_INACTIVITY_TIMEOUT_MINUTES', 30)
    
    @classmethod
    def get_user_permissions(cls, user):
        """
        Get user's app and feature permissions from RBAC.
        Returns list of app IDs and feature IDs the user has access to.
        """
        app_access = []
        feature_access = []
        
        try:
            from rbac.models import UserRoleAssignment, RoleAppMapping, RoleFeatureMapping
            
            # Get all active role assignments for user
            role_assignments = UserRoleAssignment.objects.filter(
                user=user,
                is_active=True
            ).select_related('role')
            
            role_ids = [ra.role_id for ra in role_assignments if ra.is_valid()]
            
            # Get app access for all user's roles
            app_mappings = RoleAppMapping.objects.filter(
                role_id__in=role_ids,
                is_active=True,
                can_view=True
            ).values_list('app_id', flat=True).distinct()
            app_access = list(app_mappings)
            
            # Get feature access for all user's roles
            feature_mappings = RoleFeatureMapping.objects.filter(
                role_id__in=role_ids,
                is_active=True,
                can_view=True
            ).values_list('feature_id', flat=True).distinct()
            feature_access = list(feature_mappings)
            
        except Exception:
            # If RBAC is not set up, return empty lists
            pass
        
        return app_access, feature_access
    
    @classmethod
    def generate_access_token(cls, user, include_permissions=True):
        """
        Generate JWT access token for user with complete user info.
        
        The token includes:
        - user_id, email, username, user_code, user_role
        - app_access: list of app IDs user can access
        - feature_access: list of feature IDs user can access
        - Session tracking for inactivity timeout
        
        Args:
            user: User model instance
            include_permissions: Whether to include RBAC permissions
            
        Returns:
            tuple: (token_string, token_id, expiry_datetime)
        """
        token_id = str(uuid.uuid4())
        expiry_minutes = cls.get_access_token_expiry()
        expiry_datetime = timezone.now() + timedelta(minutes=expiry_minutes)
        
        # Get permissions if requested
        app_access, feature_access = [], []
        if include_permissions:
            app_access, feature_access = cls.get_user_permissions(user)
        
        payload = {
            # User identification
            'user_id': user.id,
            'email': user.email,
            'username': user.username,
            'user_code': user.user_code,
            'user_role': user.user_role,
            'full_name': user.full_name,
            
            # RBAC permissions (for middleware/frontend use)
            'app_access': app_access,
            'feature_access': feature_access,
            
            # Token metadata
            'jti': token_id,  # JWT ID
            'token_type': 'access',
            'iat': timezone.now().timestamp(),  # Issued at
            'exp': expiry_datetime.timestamp(),  # Expiry
            
            # For inactivity tracking (frontend should refresh based on this)
            'inactivity_timeout_minutes': cls.get_inactivity_timeout(),
        }
        
        token = jwt.encode(
            payload,
            cls.get_secret_key(),
            algorithm=cls.get_algorithm()
        )
        
        return token, token_id, expiry_datetime
    
    @classmethod
    def generate_refresh_token(cls, user):
        """
        Generate JWT refresh token for user
        
        Args:
            user: User model instance
            
        Returns:
            tuple: (token_string, token_id, expiry_datetime)
        """
        token_id = str(uuid.uuid4())
        expiry_days = cls.get_refresh_token_expiry()
        expiry_datetime = timezone.now() + timedelta(days=expiry_days)
        
        payload = {
            'user_id': user.id,
            'jti': token_id,
            'token_type': 'refresh',
            'iat': timezone.now().timestamp(),
            'exp': expiry_datetime.timestamp(),
        }
        
        token = jwt.encode(
            payload,
            cls.get_secret_key(),
            algorithm=cls.get_algorithm()
        )
        
        return token, token_id, expiry_datetime
    
    @classmethod
    def generate_tokens(cls, user):
        """
        Generate both access and refresh tokens
        
        Args:
            user: User model instance
            
        Returns:
            dict: Dictionary containing access and refresh tokens with their expiry
        """
        access_token, access_token_id, access_expiry = cls.generate_access_token(user)
        refresh_token, refresh_token_id, refresh_expiry = cls.generate_refresh_token(user)
        
        return {
            'access_token': access_token,
            'access_token_id': access_token_id,
            'access_token_expiry': access_expiry,
            'refresh_token': refresh_token,
            'refresh_token_id': refresh_token_id,
            'refresh_token_expiry': refresh_expiry,
        }
    
    @classmethod
    def decode_token(cls, token):
        """
        Decode and validate JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Decoded payload if valid
            
        Raises:
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                cls.get_secret_key(),
                algorithms=[cls.get_algorithm()]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
    
    @classmethod
    def verify_token(cls, token, token_type='access'):
        """
        Verify token and return payload if valid
        
        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            dict: Token payload if valid, None otherwise
        """
        try:
            payload = cls.decode_token(token)
            
            if payload.get('token_type') != token_type:
                return None
            
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    @classmethod
    def get_user_id_from_token(cls, token):
        """
        Extract user ID from token
        
        Args:
            token: JWT token string
            
        Returns:
            int: User ID if token is valid, None otherwise
        """
        payload = cls.verify_token(token)
        if payload:
            return payload.get('user_id')
        return None
    
    @classmethod
    def refresh_access_token(cls, refresh_token):
        """
        Generate new access token using refresh token
        
        Args:
            refresh_token: JWT refresh token string
            
        Returns:
            dict: New access token info if refresh token is valid, None otherwise
        """
        from .models import User, UserSession
        
        payload = cls.verify_token(refresh_token, token_type='refresh')
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        token_id = payload.get('jti')
        
        # Verify session exists and is active
        try:
            session = UserSession.objects.get(token_id=token_id, is_active=True)
            if not session.is_valid():
                return None
            
            # Check for inactivity timeout (like bank apps)
            inactivity_timeout = cls.get_inactivity_timeout()
            if session.is_inactive_expired(inactivity_timeout):
                session.invalidate()
                return None
                
        except UserSession.DoesNotExist:
            return None
        
        # Get user
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return None
        
        # Update session activity
        session.update_activity()
        
        # Generate new access token with full permissions
        access_token, access_token_id, access_expiry = cls.generate_access_token(user, include_permissions=True)
        
        return {
            'access_token': access_token,
            'access_token_id': access_token_id,
            'access_token_expiry': access_expiry,
        }
