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
    
    @classmethod
    def generate_access_token(cls, user):
        """
        Generate JWT access token for user
        
        Args:
            user: User model instance
            
        Returns:
            tuple: (token_string, token_id, expiry_datetime)
        """
        token_id = str(uuid.uuid4())
        expiry_minutes = cls.get_access_token_expiry()
        expiry_datetime = timezone.now() + timedelta(minutes=expiry_minutes)
        
        payload = {
            'user_id': user.id,
            'email': user.email,
            'username': user.username,
            'jti': token_id,  # JWT ID
            'token_type': 'access',
            'iat': timezone.now().timestamp(),  # Issued at
            'exp': expiry_datetime.timestamp(),  # Expiry
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
        except UserSession.DoesNotExist:
            return None
        
        # Get user
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return None
        
        # Generate new access token
        access_token, access_token_id, access_expiry = cls.generate_access_token(user)
        
        return {
            'access_token': access_token,
            'access_token_id': access_token_id,
            'access_token_expiry': access_expiry,
        }
