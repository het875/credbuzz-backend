import random
import string
import hashlib
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager for User model."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(email, password, **extra_fields)


def generate_unique_user_id():
    """Generate a unique 5-character alphanumeric ID like A0031, XY12Z."""
    characters = string.ascii_uppercase + string.digits
    while True:
        user_id = ''.join(random.choices(characters, k=5))
        # Skip the database check during migrations
        try:
            if not User.objects.filter(id=user_id).exists():
                return user_id
        except:
            # During migration, just return a random ID
            return user_id


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with 5-character alphanumeric ID and authentication fields."""
    
    # Phone number regex validator
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    # Primary key - 5 character alphanumeric ID
    id = models.CharField(
        max_length=5,
        primary_key=True,
        default=generate_unique_user_id,
        editable=False,
        help_text="Unique 5-character alphanumeric ID like A0031, XY12Z"
    )
    
    # User information
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # Authentication fields
    email = models.EmailField(unique=True, db_index=True)
    mobile = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        blank=True,
        null=True,
        db_index=True
    )
    
    # OTP fields for verification
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    email_otp_updated_at = models.DateTimeField(blank=True, null=True)
    mobile_otp = models.CharField(max_length=6, blank=True, null=True)
    mobile_otp_updated_at = models.DateTimeField(blank=True, null=True)
    
    # Email verification
    is_email_verified = models.BooleanField(default=False)
    is_mobile_verified = models.BooleanField(default=False)
    
    # Login tracking fields
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_device = models.CharField(max_length=255, blank=True, null=True)
    last_login_location = models.CharField(max_length=255, blank=True, null=True)
    login_count = models.PositiveIntegerField(default=0)
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete fields
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='deleted_users'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.id} - {self.email}"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    def soft_delete(self, deleted_by=None):
        """Soft delete the user."""
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.is_active = False
        self.save()
    
    def restore(self):
        """Restore a soft-deleted user."""
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True
        self.save()
    
    def generate_otp(self, otp_type='email'):
        """Generate a 6-digit OTP for email or mobile verification."""
        otp = ''.join(random.choices(string.digits, k=6))
        
        if otp_type == 'email':
            self.email_otp = otp
            self.email_otp_updated_at = timezone.now()
        elif otp_type == 'mobile':
            self.mobile_otp = otp
            self.mobile_otp_updated_at = timezone.now()
        
        self.save()
        return otp
    
    def verify_otp(self, otp, otp_type='email', expire_minutes=10):
        """Verify OTP and check if it's still valid."""
        now = timezone.now()
        
        if otp_type == 'email':
            if not self.email_otp or not self.email_otp_updated_at:
                return False
            if self.email_otp != otp:
                return False
            if (now - self.email_otp_updated_at).total_seconds() > expire_minutes * 60:
                return False
            # Clear OTP after successful verification
            self.email_otp = None
            self.email_otp_updated_at = None
            self.is_email_verified = True
            self.save()
            return True
        
        elif otp_type == 'mobile':
            if not self.mobile_otp or not self.mobile_otp_updated_at:
                return False
            if self.mobile_otp != otp:
                return False
            if (now - self.mobile_otp_updated_at).total_seconds() > expire_minutes * 60:
                return False
            # Clear OTP after successful verification
            self.mobile_otp = None
            self.mobile_otp_updated_at = None
            self.is_mobile_verified = True
            self.save()
            return True
        
        return False


class LoginHistory(models.Model):
    """Track all login attempts and sessions."""
    
    LOGIN_STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
    ]
    
    LOGIN_TYPE_CHOICES = [
        ('web', 'Web Browser'),
        ('mobile', 'Mobile App'),
        ('api', 'API'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    device_name = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)  # mobile, desktop, tablet
    browser_name = models.CharField(max_length=100, blank=True, null=True)
    os_name = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    login_method = models.CharField(max_length=20, default='email')  # email, mobile
    login_type = models.CharField(max_length=10, choices=LOGIN_TYPE_CHOICES, default='web')
    status = models.CharField(max_length=10, choices=LOGIN_STATUS_CHOICES)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    session_duration = models.DurationField(blank=True, null=True)
    logout_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_history'
        verbose_name = 'Login History'
        verbose_name_plural = 'Login Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.status} at {self.created_at}"


class UserToken(models.Model):
    """Store JWT tokens with device and session information."""
    
    TOKEN_TYPE_CHOICES = [
        ('refresh', 'Refresh Token'),
        ('access', 'Access Token'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens')
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)  # SHA-256 hash of token
    token_type = models.CharField(max_length=10, choices=TOKEN_TYPE_CHOICES, default='refresh')
    device_id = models.CharField(max_length=64, blank=True, null=True)  # Unique device identifier
    device_name = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)
    browser_name = models.CharField(max_length=100, blank=True, null=True)
    os_name = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'user_tokens'
        verbose_name = 'User Token'
        verbose_name_plural = 'User Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['token_hash']),
            models.Index(fields=['device_id', 'user']),
            models.Index(fields=['is_active', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.token_type} ({self.device_name})"
    
    @classmethod
    def create_token_hash(cls, token):
        """Create SHA-256 hash of token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def revoke(self):
        """Revoke the token."""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save()
    
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at


class DeviceFingerprint(models.Model):
    """Store unique device fingerprints for security."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_fingerprints')
    device_id = models.CharField(max_length=64, unique=True, db_index=True)
    fingerprint_hash = models.CharField(max_length=64, db_index=True)  # Hash of device characteristics
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=50)  # mobile, desktop, tablet
    browser_name = models.CharField(max_length=100, blank=True, null=True)
    browser_version = models.CharField(max_length=50, blank=True, null=True)
    os_name = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)
    screen_resolution = models.CharField(max_length=20, blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    language = models.CharField(max_length=10, blank=True, null=True)
    is_trusted = models.BooleanField(default=False)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    login_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'device_fingerprints'
        verbose_name = 'Device Fingerprint'
        verbose_name_plural = 'Device Fingerprints'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['user', '-last_seen']),
            models.Index(fields=['device_id']),
            models.Index(fields=['fingerprint_hash']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name}"
    
    def mark_as_seen(self):
        """Update last seen timestamp and increment login count."""
        self.last_seen = timezone.now()
        self.login_count += 1
        self.save()


class SecurityLog(models.Model):
    """Log security-related events."""
    
    EVENT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('password_change', 'Password Changed'),
        ('email_verified', 'Email Verified'),
        ('mobile_verified', 'Mobile Verified'),
        ('token_revoked', 'Token Revoked'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('account_locked', 'Account Locked'),
        ('device_added', 'New Device Added'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs', blank=True, null=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    device_id = models.CharField(max_length=64, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)  # Additional event data
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'security_logs'
        verbose_name = 'Security Log'
        verbose_name_plural = 'Security Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user.email if self.user else 'Anonymous'} at {self.created_at}"
