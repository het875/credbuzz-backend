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
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag - True means user is deleted")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when user was soft deleted")
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
    last_activity = models.DateTimeField(auto_now_add=True)  # Track last activity for inactivity timeout
    
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
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def is_inactive_expired(self, inactivity_minutes=30):
        """Check if session has expired due to inactivity"""
        if not self.is_active:
            return True
        inactivity_threshold = self.last_activity + timedelta(minutes=inactivity_minutes)
        return timezone.now() > inactivity_threshold


class LoginAttempt(models.Model):
    """
    Model to track login attempts for security and rate limiting.
    
    Implements progressive lockout:
    - 5 failed attempts in first try
    - Then wait 2 minutes
    - Then wait 5 minutes
    - Then wait 10 minutes
    - Then wait 30 minutes
    - Then wait 60 minutes
    - Then account is blocked (needs admin intervention)
    """
    
    LOCKOUT_STAGES = [
        (0, 0),      # Initial: 5 attempts allowed
        (1, 2),      # Stage 1: 2 minutes lockout
        (2, 5),      # Stage 2: 5 minutes lockout
        (3, 10),     # Stage 3: 10 minutes lockout
        (4, 30),     # Stage 4: 30 minutes lockout
        (5, 60),     # Stage 5: 60 minutes lockout
        (6, -1),     # Stage 6: Blocked (requires manual unblock)
    ]
    
    MAX_ATTEMPTS_PER_STAGE = 5
    
    id = models.AutoField(primary_key=True)
    
    # Identifier for the login attempt (can be email, username, user_code, phone)
    identifier = models.CharField(max_length=255, db_index=True)
    identifier_type = models.CharField(
        max_length=20,
        choices=[
            ('EMAIL', 'Email'),
            ('USERNAME', 'Username'),
            ('USER_CODE', 'User Code'),
            ('PHONE', 'Phone Number'),
        ]
    )
    
    # User reference (null if user doesn't exist)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='login_attempts'
    )
    
    # Attempt tracking
    attempt_count = models.IntegerField(default=0)
    lockout_stage = models.IntegerField(default=0)
    
    # Status
    is_successful = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)  # Permanently blocked
    
    # Lockout timing
    lockout_until = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(auto_now=True)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_auth_login_attempt'
        ordering = ['-last_attempt_at']
        indexes = [
            models.Index(fields=['identifier', 'identifier_type']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"Login attempt for {self.identifier} ({self.attempt_count} attempts)"
    
    @classmethod
    def get_or_create_for_identifier(cls, identifier, identifier_type, ip_address=None, user_agent=None):
        """Get or create login attempt record for an identifier"""
        attempt, created = cls.objects.get_or_create(
            identifier=identifier.lower(),
            identifier_type=identifier_type,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent,
            }
        )
        if not created:
            attempt.ip_address = ip_address
            attempt.user_agent = user_agent
        return attempt
    
    def is_locked_out(self):
        """Check if the identifier is currently locked out"""
        if self.is_blocked:
            return True, "Account is blocked. Please contact support."
        
        if self.lockout_until and timezone.now() < self.lockout_until:
            remaining = self.lockout_until - timezone.now()
            minutes = int(remaining.total_seconds() / 60)
            seconds = int(remaining.total_seconds() % 60)
            if minutes > 0:
                return True, f"Too many failed attempts. Please try again in {minutes} minute(s)."
            else:
                return True, f"Too many failed attempts. Please try again in {seconds} second(s)."
        
        return False, None
    
    def get_remaining_attempts(self):
        """Get remaining attempts before next lockout"""
        return max(0, self.MAX_ATTEMPTS_PER_STAGE - self.attempt_count)
    
    def record_failed_attempt(self):
        """Record a failed login attempt and apply lockout if needed"""
        self.attempt_count += 1
        self.is_successful = False
        
        # Check if we've exceeded max attempts for current stage
        if self.attempt_count >= self.MAX_ATTEMPTS_PER_STAGE:
            self.lockout_stage += 1
            self.attempt_count = 0  # Reset attempt count for next stage
            
            # Get lockout duration for this stage
            lockout_minutes = None
            for stage, minutes in self.LOCKOUT_STAGES:
                if stage == self.lockout_stage:
                    lockout_minutes = minutes
                    break
            
            if lockout_minutes == -1:
                # Permanent block
                self.is_blocked = True
                self.lockout_until = None
            elif lockout_minutes is not None:
                self.lockout_until = timezone.now() + timedelta(minutes=lockout_minutes)
        
        self.save()
        
        return {
            'remaining_attempts': self.get_remaining_attempts(),
            'lockout_stage': self.lockout_stage,
            'is_blocked': self.is_blocked,
            'lockout_until': self.lockout_until,
        }
    
    def record_successful_login(self, user=None):
        """Record a successful login and reset attempt tracking"""
        self.attempt_count = 0
        self.lockout_stage = 0
        self.is_successful = True
        self.is_blocked = False
        self.lockout_until = None
        if user:
            self.user = user
        self.save()
    
    def reset_lockout(self):
        """Reset lockout (for admin intervention)"""
        self.attempt_count = 0
        self.lockout_stage = 0
        self.is_blocked = False
        self.lockout_until = None
        self.save()
    
    @classmethod
    def cleanup_old_records(cls, days=30):
        """Clean up old login attempt records"""
        threshold = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            last_attempt_at__lt=threshold,
            is_blocked=False
        ).delete()
