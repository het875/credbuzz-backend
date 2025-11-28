"""
Custom User Model for users_auth app
This model is completely custom without using Django's AbstractUser or AbstractBaseUser
"""
from django.db import models
import hashlib
import secrets
from datetime import datetime, timedelta
from django.utils import timezone


class User(models.Model):
    """
    Custom User model with all fields defined manually
    """
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(unique=True, max_length=150)
    password_hash = models.CharField(max_length=256)  # Store hashed password
    salt = models.CharField(max_length=64)  # Salt for password hashing
    
    # User profile fields
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'users_auth_user'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    @staticmethod
    def generate_salt():
        """Generate a random salt for password hashing"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password, salt):
        """Hash password with salt using SHA-256"""
        salted_password = f"{password}{salt}"
        return hashlib.sha256(salted_password.encode()).hexdigest()
    
    def set_password(self, raw_password):
        """Set password with salt and hash"""
        self.salt = self.generate_salt()
        self.password_hash = self.hash_password(raw_password, self.salt)
    
    def check_password(self, raw_password):
        """Verify password against stored hash"""
        return self.password_hash == self.hash_password(raw_password, self.salt)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
    
    @property
    def full_name(self):
        """Return full name of user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username
    
    @property
    def is_authenticated(self):
        """
        Always return True for authenticated users.
        This is required by DRF's IsAuthenticated permission class.
        """
        return True
    
    @property
    def is_anonymous(self):
        """
        Always return False. This is required by Django's authentication system.
        """
        return False


class PasswordResetToken(models.Model):
    """
    Model to store password reset tokens
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=256, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users_auth_password_reset_token'
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    @staticmethod
    def generate_token():
        """Generate a unique reset token"""
        return secrets.token_urlsafe(64)
    
    @classmethod
    def create_token(cls, user, expiry_hours=24):
        """Create a new password reset token for user"""
        # Invalidate any existing unused tokens for this user
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        token = cls.generate_token()
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and self.expires_at > timezone.now()
    
    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save(update_fields=['is_used'])


class UserSession(models.Model):
    """
    Model to track user sessions and JWT tokens
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token_id = models.CharField(max_length=256, unique=True)  # JWT token ID (jti)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'users_auth_user_session'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session for {self.user.email}"
    
    def invalidate(self):
        """Invalidate this session"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def is_valid(self):
        """Check if session is still valid"""
        return self.is_active and self.expires_at > timezone.now()
