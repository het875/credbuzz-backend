"""
Core Django Models for ERP Credit Card Bill Payment System
Includes: User Management, KYC, Business, Bank, Role-based Access, Security
"""
import uuid
import hashlib
import secrets
from datetime import timedelta, datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from django.conf import settings
import os


def get_encryption_key():
    """Get or create encryption key for sensitive data."""
    key_file = os.path.join(settings.BASE_DIR, '.encryption_key')
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key


def encrypt_sensitive_data(data):
    """Encrypt sensitive data like Aadhaar, Bank Account."""
    if not data:
        return None
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode()).decode()


def decrypt_sensitive_data(encrypted_data):
    """Decrypt sensitive data."""
    if not encrypted_data:
        return None
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_data.encode()).decode()


def generate_short_id():
    """Generate short unique ID for primary keys."""
    return secrets.token_urlsafe(8)


class Branch(models.Model):
    """Branch management for user assignment."""
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    branch_code = models.CharField(max_length=20, unique=True)
    branch_name = models.CharField(max_length=100)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    manager_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete fields
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey('UserAccount', on_delete=models.SET_NULL, blank=True, null=True, related_name='deleted_branches')

    class Meta:
        db_table = 'branches'
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
        ordering = ['branch_code']

    def __str__(self):
        return f"{self.branch_code} - {self.branch_name}"

    def soft_delete(self, deleted_by=None):
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.is_active = False
        self.save()


class AppFeature(models.Model):
    """Defines features/modules available in the system."""
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    feature_code = models.CharField(max_length=50, unique=True)
    feature_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_features'
        verbose_name = 'App Feature'
        verbose_name_plural = 'App Features'

    def __str__(self):
        return f"{self.feature_code} - {self.feature_name}"


class UserAccountManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, email, mobile, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        if not mobile:
            raise ValueError('Mobile is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, mobile, password=None, **extra_fields):
        extra_fields.setdefault('role', 'master_superadmin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        extra_fields.setdefault('is_mobile_verified', True)
        
        return self.create_user(email, mobile, password, **extra_fields)


class UserAccount(AbstractBaseUser, PermissionsMixin):
    """Enhanced User model with role hierarchy and security features."""
    
    ROLE_CHOICES = [
        ('master_superadmin', 'Master Super Admin'),
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        
        ('user', 'User'),
    ]
    
    ROLE_HIERARCHY = {
        'master_superadmin': 4,
        'super_admin': 3,
        'admin': 2,
        'user': 1
    }
    
    # Validators
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number format: '+999999999'. Up to 15 digits."
    )
    
    # Primary key
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    
    # Personal Details
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    
    email = models.EmailField(unique=True, db_index=True)
    mobile = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        unique=True, 
        db_index=True
    )
    
    # Role and Branch Assignment
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='users')
    
    # Verification Status
    is_email_verified = models.BooleanField(default=False)
    is_mobile_verified = models.BooleanField(default=False)
    is_kyc_completed = models.BooleanField(default=False)
    is_business_verified = models.BooleanField(default=False)
    is_bank_verified = models.BooleanField(default=False)
    
    # OTP Fields with Retry Tracking
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    email_otp_created_at = models.DateTimeField(blank=True, null=True)
    email_otp_attempts = models.PositiveIntegerField(default=0)
    email_blocked_until = models.DateTimeField(blank=True, null=True)
    
    mobile_otp = models.CharField(max_length=6, blank=True, null=True)
    mobile_otp_created_at = models.DateTimeField(blank=True, null=True)
    mobile_otp_attempts = models.PositiveIntegerField(default=0)
    mobile_blocked_until = models.DateTimeField(blank=True, null=True)
    
    # Login Security
    login_attempts = models.PositiveIntegerField(default=0)
    login_blocked_until = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_device = models.CharField(max_length=255, blank=True, null=True)
    login_count = models.PositiveIntegerField(default=0)
    
    # Django required fields
    is_active = models.BooleanField(default=False)  # Activated after email/mobile verification
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Override groups and user_permissions to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="erp_user_set",
        related_query_name="erp_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="erp_user_set",
        related_query_name="erp_user",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='deleted_users')
    
    objects = UserAccountManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['mobile', 'first_name', 'last_name']

    class Meta:
        db_table = 'user_accounts'
        verbose_name = 'User Account'
        verbose_name_plural = 'User Accounts'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['mobile']),
            models.Index(fields=['role', 'branch']),
            models.Index(fields=['is_active', 'role']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def get_role_level(self):
        return self.ROLE_HIERARCHY.get(self.role, 0)

    def can_create_role(self, target_role):
        """Check if user can create accounts with target role."""
        user_level = self.get_role_level()
        target_level = self.ROLE_HIERARCHY.get(target_role, 0)
        
        if self.role == 'master_superadmin':
            return target_role in ['super_admin']
        elif self.role == 'super_admin':
            return target_role in ['admin', 'user']
        elif self.role == 'admin':
            return target_role in ['user']
        
        return False

    def is_login_blocked(self):
        """Check if user is blocked from login attempts."""
        if self.login_blocked_until and timezone.now() < self.login_blocked_until:
            return True
        return False

    def is_otp_blocked(self, otp_type='email'):
        """Check if user is blocked from OTP attempts."""
        if otp_type == 'email':
            return self.email_blocked_until and timezone.now() < self.email_blocked_until
        elif otp_type == 'mobile':
            return self.mobile_blocked_until and timezone.now() < self.mobile_blocked_until
        return False

    def increment_login_attempts(self):
        """Increment login attempts and block if needed."""
        self.login_attempts += 1
        if self.login_attempts >= 3:
            self.login_blocked_until = timezone.now() + timedelta(minutes=15)
        self.save()

    def reset_login_attempts(self):
        """Reset login attempts after successful login."""
        self.login_attempts = 0
        self.login_blocked_until = None
        self.login_count += 1
        self.save()

    def increment_otp_attempts(self, otp_type='email'):
        """Increment OTP attempts and block if needed."""
        if otp_type == 'email':
            self.email_otp_attempts += 1
            if self.email_otp_attempts >= 3:
                self.email_blocked_until = timezone.now() + timedelta(minutes=15)
        elif otp_type == 'mobile':
            self.mobile_otp_attempts += 1
            if self.mobile_otp_attempts >= 3:
                self.mobile_blocked_until = timezone.now() + timedelta(minutes=15)
        self.save()

    def reset_otp_attempts(self, otp_type='email'):
        """Reset OTP attempts after successful verification."""
        if otp_type == 'email':
            self.email_otp_attempts = 0
            self.email_blocked_until = None
            self.email_otp = None
            self.email_otp_created_at = None
        elif otp_type == 'mobile':
            self.mobile_otp_attempts = 0
            self.mobile_blocked_until = None
            self.mobile_otp = None
            self.mobile_otp_created_at = None
        self.save()

    def soft_delete(self, deleted_by=None):
        """Soft delete user."""
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.is_active = False
        self.save()


class AadhaarKYC(models.Model):
    """Aadhaar KYC verification details."""
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='aadhaar_kyc')
    
    # Encrypted Aadhaar number
    aadhaar_number_encrypted = models.TextField()  # Encrypted 12-digit number
    aadhaar_name = models.CharField(max_length=100)  # Name as per Aadhaar
    
    # Document images
    aadhaar_front_image = models.ImageField(upload_to='kyc/aadhaar/front/')
    aadhaar_back_image = models.ImageField(upload_to='kyc/aadhaar/back/')
    
    # OTP Verification
    aadhaar_otp = models.CharField(max_length=6, blank=True, null=True)
    aadhaar_otp_created_at = models.DateTimeField(blank=True, null=True)
    aadhaar_otp_attempts = models.PositiveIntegerField(default=0)
    aadhaar_blocked_until = models.DateTimeField(blank=True, null=True)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_remarks = models.TextField(blank=True, null=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'aadhaar_kyc'
        verbose_name = 'Aadhaar KYC'
        verbose_name_plural = 'Aadhaar KYCs'

    def set_aadhaar_number(self, aadhaar_number):
        """Encrypt and store Aadhaar number."""
        self.aadhaar_number_encrypted = encrypt_sensitive_data(aadhaar_number)

    def get_aadhaar_number(self):
        """Decrypt and return Aadhaar number."""
        return decrypt_sensitive_data(self.aadhaar_number_encrypted)

    def get_masked_aadhaar(self):
        """Return masked Aadhaar number."""
        aadhaar = self.get_aadhaar_number()
        if aadhaar and len(aadhaar) == 12:
            return f"XXXX-XXXX-{aadhaar[-4:]}"
        return "XXXX-XXXX-XXXX"

    def __str__(self):
        return f"Aadhaar KYC - {self.user.get_full_name()}"


class PanKYC(models.Model):
    """PAN Card KYC verification details."""
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='pan_kyc')
    
    # PAN details
    pan_number = models.CharField(max_length=10, validators=[
        RegexValidator(regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message='Invalid PAN format')
    ])
    pan_name = models.CharField(max_length=100)  # Name as per PAN
    date_of_birth = models.DateField()
    
    # Document image
    pan_image = models.ImageField(upload_to='kyc/pan/')
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_remarks = models.TextField(blank=True, null=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pan_kyc'
        verbose_name = 'PAN KYC'
        verbose_name_plural = 'PAN KYCs'

    def __str__(self):
        return f"PAN KYC - {self.user.get_full_name()}"


class BusinessDetails(models.Model):
    """Business/Shop details for users."""
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='business_details')
    
    # User selfie for liveness check
    user_selfie = models.ImageField(upload_to='business/selfies/')
    
    # Business details
    business_name = models.CharField(max_length=200)
    business_address_line1 = models.CharField(max_length=255)
    business_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=10)
    
    # Business contact with OTP verification
    business_phone = models.CharField(validators=[UserAccount.phone_regex], max_length=17)
    business_phone_otp = models.CharField(max_length=6, blank=True, null=True)
    business_phone_otp_created_at = models.DateTimeField(blank=True, null=True)
    business_phone_otp_attempts = models.PositiveIntegerField(default=0)
    business_phone_blocked_until = models.DateTimeField(blank=True, null=True)
    is_business_phone_verified = models.BooleanField(default=False)
    
    business_email = models.EmailField()
    business_email_otp = models.CharField(max_length=6, blank=True, null=True)
    business_email_otp_created_at = models.DateTimeField(blank=True, null=True)
    business_email_otp_attempts = models.PositiveIntegerField(default=0)
    business_email_blocked_until = models.DateTimeField(blank=True, null=True)
    is_business_email_verified = models.BooleanField(default=False)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_remarks = models.TextField(blank=True, null=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_details'
        verbose_name = 'Business Details'
        verbose_name_plural = 'Business Details'

    def __str__(self):
        return f"{self.business_name} - {self.user.get_full_name()}"


class BusinessImages(models.Model):
    """Shop images for business verification (up to 5 images)."""
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    business = models.ForeignKey(BusinessDetails, on_delete=models.CASCADE, related_name='shop_images')
    image = models.ImageField(upload_to='business/shop_images/')
    image_description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'business_images'
        verbose_name = 'Business Image'
        verbose_name_plural = 'Business Images'

    def __str__(self):
        return f"Shop Image - {self.business.business_name}"


class BankDetails(models.Model):
    """Bank account details for payments."""
    
    ACCOUNT_TYPE_CHOICES = [
        ('savings', 'Savings'),
        ('current', 'Current'),
    ]
    
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='bank_details')
    
    # Bank account details
    account_holder_name = models.CharField(max_length=100)
    account_number_encrypted = models.TextField()  # Encrypted account number
    ifsc_code = models.CharField(max_length=11, validators=[
        RegexValidator(regex=r'^[A-Z]{4}0[A-Z0-9]{6}$', message='Invalid IFSC format')
    ])
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100)
    
    # Bank proof document
    bank_proof_image = models.ImageField(upload_to='bank/proofs/')
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_remarks = models.TextField(blank=True, null=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_details'
        verbose_name = 'Bank Details'
        verbose_name_plural = 'Bank Details'

    def set_account_number(self, account_number):
        """Encrypt and store account number."""
        self.account_number_encrypted = encrypt_sensitive_data(account_number)

    def get_account_number(self):
        """Decrypt and return account number."""
        return decrypt_sensitive_data(self.account_number_encrypted)

    def get_masked_account_number(self):
        """Return masked account number."""
        account_number = self.get_account_number()
        if account_number and len(account_number) > 4:
            return f"XXXXX{account_number[-4:]}"
        return "XXXXXXXXXX"

    def __str__(self):
        return f"Bank - {self.user.get_full_name()}"


class UserPlatformAccess(models.Model):
    """Platform access control for users."""
    
    PLATFORM_CHOICES = [
        ('web', 'Web'),
        ('mobile_app', 'Mobile App'),
        ('admin_panel', 'Admin Panel'),
        ('api', 'API'),
    ]
    
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='platform_access')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    is_allowed = models.BooleanField(default=True)
    granted_by = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, related_name='granted_platform_access')
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'user_platform_access'
        verbose_name = 'User Platform Access'
        verbose_name_plural = 'User Platform Access'
        unique_together = ['user', 'platform']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.platform}"


class AppAccessControl(models.Model):
    """Feature access control for users."""
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='feature_access')
    feature = models.ForeignKey(AppFeature, on_delete=models.CASCADE)
    is_allowed = models.BooleanField(default=False)
    granted_by = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, related_name='granted_feature_access')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_access_control'
        verbose_name = 'App Access Control'
        verbose_name_plural = 'App Access Control'
        unique_together = ['user', 'feature']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.feature.feature_name}"


class LoginActivity(models.Model):
    """Track all login activities and attempts."""
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
    ]
    
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='login_activities', null=True, blank=True)
    email_or_mobile = models.CharField(max_length=255)  # Store attempted login credential
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    device_info = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    login_timestamp = models.DateTimeField(auto_now_add=True)
    logout_timestamp = models.DateTimeField(blank=True, null=True)
    session_duration = models.DurationField(blank=True, null=True)

    class Meta:
        db_table = 'login_activities'
        verbose_name = 'Login Activity'
        verbose_name_plural = 'Login Activities'
        ordering = ['-login_timestamp']
        indexes = [
            models.Index(fields=['user', '-login_timestamp']),
            models.Index(fields=['ip_address', '-login_timestamp']),
            models.Index(fields=['status', '-login_timestamp']),
        ]

    def __str__(self):
        return f"{self.email_or_mobile} - {self.status} at {self.login_timestamp}"


class AuditTrail(models.Model):
    """Comprehensive audit trail for all system activities."""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('otp_request', 'OTP Request'),
        ('otp_verify', 'OTP Verify'),
        ('kyc_submit', 'KYC Submit'),
        ('kyc_verify', 'KYC Verify'),
        ('password_change', 'Password Change'),
        ('role_change', 'Role Change'),
        ('access_grant', 'Access Grant'),
        ('access_revoke', 'Access Revoke'),
    ]
    
    id = models.CharField(max_length=16, primary_key=True, default=generate_short_id)
    user = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_trails')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)  # Model name
    resource_id = models.CharField(max_length=16, blank=True, null=True)  # Object ID
    description = models.TextField()
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_trails'
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trails'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        return f"{self.action} - {self.resource_type} by {self.user}"