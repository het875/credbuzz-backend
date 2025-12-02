"""
Custom User Model for users_auth app
This model is completely custom without using Django's AbstractUser or AbstractBaseUser
"""
from django.db import models
import hashlib
import secrets
import string
import random
from datetime import datetime, timedelta
from django.utils import timezone


class UserCodeGenerator:
    """
    Utility class to generate unique user codes.
    Format: ABC001, XY1234, A0B221 (minimum 5 characters, alphanumeric)
    """
    
    @staticmethod
    def generate_code(length=6):
        """Generate a random alphanumeric code"""
        # Use uppercase letters and digits
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choices(characters, k=length))
    
    @classmethod
    def generate_unique_code(cls, model_class, field_name='user_code', length=6, max_attempts=100):
        """Generate a unique code that doesn't exist in the database"""
        for _ in range(max_attempts):
            code = cls.generate_code(length)
            # Check if code already exists
            if not model_class.objects.filter(**{field_name: code}).exists():
                return code
        # If we couldn't generate a unique code, try with longer length
        return cls.generate_unique_code(model_class, field_name, length + 1, max_attempts)


class RoleName:
    """Role name constants for direct role reference in User model"""
    DEVELOPER = 'DEVELOPER'
    SUPER_ADMIN = 'SUPER_ADMIN'
    ADMIN = 'ADMIN'
    CLIENT = 'CLIENT'
    END_USER = 'END_USER'
    
    CHOICES = [
        (DEVELOPER, 'Developer'),
        (SUPER_ADMIN, 'Super Admin'),
        (ADMIN, 'Admin'),
        (CLIENT, 'Client'),
        (END_USER, 'End User'),
    ]
    
    # Level mapping (lower = higher privilege)
    LEVELS = {
        DEVELOPER: 1,
        SUPER_ADMIN: 2,
        ADMIN: 3,
        CLIENT: 4,
        END_USER: 5,
    }
    
    @classmethod
    def get_level(cls, role_name):
        """Get hierarchy level for a role"""
        return cls.LEVELS.get(role_name, 999)


class User(models.Model):
    """
    Custom User model with all fields defined manually
    """
    id = models.AutoField(primary_key=True)
    
    # Unique user code (e.g., ABC001, XY1234) - minimum 5 characters
    user_code = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True,
        help_text="Unique user code (auto-generated if not provided)"
    )
    
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(unique=True, max_length=150)
    password_hash = models.CharField(max_length=256)  # Store hashed password
    salt = models.CharField(max_length=64)  # Salt for password hashing
    
    # User profile fields
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Direct role reference (for quick access, synced with UserRoleAssignment)
    user_role = models.CharField(
        max_length=20,
        choices=RoleName.CHOICES,
        default=RoleName.END_USER,
        help_text="Primary role of the user"
    )
    
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
        return f"{self.user_code} - {self.email}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate user_code if not provided"""
        if not self.user_code:
            self.user_code = UserCodeGenerator.generate_unique_code(User, 'user_code', length=6)
        super().save(*args, **kwargs)
    
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
    
    @property
    def role_level(self):
        """Get the hierarchy level of user's role"""
        return RoleName.get_level(self.user_role)
    
    @property
    def is_developer(self):
        """Check if user is a Developer"""
        return self.user_role == RoleName.DEVELOPER
    
    @property
    def is_super_admin(self):
        """Check if user is a Super Admin or higher"""
        return self.role_level <= RoleName.LEVELS[RoleName.SUPER_ADMIN]
    
    @property
    def is_admin(self):
        """Check if user is an Admin or higher"""
        return self.role_level <= RoleName.LEVELS[RoleName.ADMIN]
    
    @property
    def is_client(self):
        """Check if user is a Client or higher"""
        return self.role_level <= RoleName.LEVELS[RoleName.CLIENT]
    
    def can_manage_role(self, target_role):
        """Check if user can manage/assign a target role"""
        target_level = RoleName.get_level(target_role)
        return self.role_level < target_level
    
    def can_manage_user(self, target_user):
        """Check if user can manage another user based on role hierarchy"""
        return self.role_level < target_user.role_level


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
