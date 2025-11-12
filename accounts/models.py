from django.db import models
from django.db.models import JSONField
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import json


# Choice Constants
class UserRoleChoices(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    ADMIN = 'admin', 'Admin'
    USER = 'user', 'User'


class GenderChoices(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'


class OTPTypeChoices(models.TextChoices):
    EMAIL = 'email', 'Email'
    MOBILE = 'mobile', 'Mobile'
    BOTH = 'both', 'Both Email and Mobile'
    AADHAAR = 'aadhaar', 'Aadhaar'
    BANK_PHONE = 'bank_phone', 'Bank Phone'
    BANK_EMAIL = 'bank_email', 'Bank Email'
    BUSINESS_PHONE = 'business_phone', 'Business Phone'
    BUSINESS_EMAIL = 'business_email', 'Business Email'


class OTPPurposeChoices(models.TextChoices):
    REGISTRATION = 'registration', 'Registration'
    LOGIN = 'login', 'Login'
    FORGOT_PASSWORD = 'forgot_password', 'Forgot Password'
    RESET_PASSWORD = 'reset_password', 'Reset Password'
    EMAIL_VERIFICATION = 'email_verification', 'Email Verification'
    MOBILE_VERIFICATION = 'mobile_verification', 'Mobile Verification'
    AADHAAR_VERIFICATION = 'aadhaar_verification', 'Aadhaar Verification'
    BANK_VERIFICATION = 'bank_verification', 'Bank Verification'
    BUSINESS_VERIFICATION = 'business_verification', 'Business Verification'


class PlatformChoices(models.TextChoices):
    WEB = 'web', 'Web'
    MOBILE_APP = 'mobile_app', 'Mobile App'
    ADMIN_PANEL = 'admin_panel', 'Admin Panel'
    API = 'api', 'API'
    POS_TERMINAL = 'pos_terminal', 'POS Terminal'


class AccessLevelChoices(models.TextChoices):
    FULL = 'full', 'Full Access'
    READ_ONLY = 'read_only', 'Read Only'
    RESTRICTED = 'restricted', 'Restricted'
    CREATE_ONLY = 'create_only', 'Create Only'
    UPDATE_ONLY = 'update_only', 'Update Only'


class LoginStatusChoices(models.TextChoices):
    SUCCESS = 'success', 'Success'
    FAILED_PASSWORD = 'failed_password', 'Failed - Wrong Password'
    FAILED_BLOCKED = 'failed_blocked', 'Failed - User Blocked'
    FAILED_INACTIVE = 'failed_inactive', 'Failed - User Inactive'
    FAILED_NOT_FOUND = 'failed_not_found', 'Failed - User Not Found'


class AuditActionChoices(models.TextChoices):
    CREATE = 'create', 'Create'
    UPDATE = 'update', 'Update'
    DELETE = 'delete', 'Delete'
    LOGIN = 'login', 'Login'
    LOGOUT = 'logout', 'Logout'
    OTP_REQUEST = 'otp_request', 'OTP Request'
    OTP_VERIFY = 'otp_verify', 'OTP Verify'
    KYC_SUBMIT = 'kyc_submit', 'KYC Submit'
    KYC_APPROVE = 'kyc_approve', 'KYC Approve'
    KYC_REJECT = 'kyc_reject', 'KYC Reject'
    PASSWORD_CHANGE = 'password_change', 'Password Change'
    ROLE_CHANGE = 'role_change', 'Role Change'
    ACCESS_GRANT = 'access_grant', 'Access Grant'
    ACCESS_REVOKE = 'access_revoke', 'Access Revoke'
    USER_BLOCK = 'user_block', 'User Block'
    USER_UNBLOCK = 'user_unblock', 'User Unblock'


class VerificationMethodChoices(models.TextChoices):
    MANUAL = 'manual', 'Manual'
    API_DIGILOCKER = 'api_digilocker', 'DigiLocker API'
    API_UIDAI = 'api_uidai', 'UIDAI API'
    API_NSDL = 'api_nsdl', 'NSDL API'
    API_KARZA = 'api_karza', 'Karza API'
    OFFLINE_XML = 'offline_xml', 'Offline XML'


class BusinessTypeChoices(models.TextChoices):
    SOLE_PROPRIETORSHIP = 'sole_proprietorship', 'Sole Proprietorship'
    PARTNERSHIP = 'partnership', 'Partnership'
    PRIVATE_LIMITED = 'private_limited', 'Private Limited'
    PUBLIC_LIMITED = 'public_limited', 'Public Limited'
    LLP = 'llp', 'Limited Liability Partnership'
    NGO = 'ngo', 'NGO'
    TRUST = 'trust', 'Trust'
    HUF = 'huf', 'Hindu Undivided Family'


class AccountTypeChoices(models.TextChoices):
    SAVINGS = 'savings', 'Savings'
    CURRENT = 'current', 'Current'
    FIXED_DEPOSIT = 'fixed_deposit', 'Fixed Deposit'
    RECURRING_DEPOSIT = 'recurring_deposit', 'Recurring Deposit'


class BankVerificationMethodChoices(models.TextChoices):
    PENNY_DROP = 'penny_drop', 'Penny Drop'
    MANUAL = 'manual', 'Manual'
    BANK_STATEMENT = 'bank_statement', 'Bank Statement'


class TwoFactorMethodChoices(models.TextChoices):
    SMS = 'sms', 'SMS'
    EMAIL = 'email', 'Email'
    AUTHENTICATOR = 'authenticator', 'Authenticator App'


# ===========================
# Table 1: UserAccount
# ===========================
class UserAccount(models.Model):
    """
    Custom user model for authentication and user management.
    Does not use Django's built-in User model.
    """
    id = models.BigAutoField(primary_key=True)
    user_code = models.CharField(max_length=6, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    mobile = models.CharField(max_length=15, db_index=True)
    password = models.CharField(max_length=128)
    user_role = models.CharField(max_length=20, choices=UserRoleChoices.choices, default=UserRoleChoices.USER)
    branch_code = models.ForeignKey('Branch', on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    
    # Personal Information
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GenderChoices.choices)
    dob = models.DateField()
    
    # Email and Mobile Verification
    is_mobile_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
    # KYC Verification Tracking
    is_kyc_complete = models.BooleanField(default=False)
    kyc_verification_step = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(4)]
    )
    is_aadhaar_verified = models.BooleanField(default=False)
    is_pan_verified = models.BooleanField(default=False)
    is_bank_verified = models.BooleanField(default=False)
    
    # Account Status
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    user_blocked = models.IntegerField(default=0)
    user_block_reason = models.TextField(blank=True, null=True)
    blocked_until = models.DateTimeField(blank=True, null=True)
    
    # OTP Attempt Tracking
    email_otp_attempts = models.IntegerField(default=0)
    mobile_otp_attempts = models.IntegerField(default=0)
    email_blocked_until = models.DateTimeField(blank=True, null=True)
    mobile_blocked_until = models.DateTimeField(blank=True, null=True)
    
    # Address Information
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    address_line3 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=6, blank=True)
    
    # Security & Audit
    register_device_ip = models.GenericIPAddressField()
    register_device_info = models.JSONField(default=dict)
    last_login = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    password_changed_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_last_field = models.CharField(max_length=100, blank=True, null=True)
    
    # Soft Delete
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='deleted_users'
    )
    
    # Registration Progress
    registration_step = models.IntegerField(default=0)
    registration_data = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['mobile']),
            models.Index(fields=['user_code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['user_role']),
        ]
        verbose_name = 'User Account'
        verbose_name_plural = 'User Accounts'
    
    def __str__(self):
        return f"{self.user_code} - {self.email}"


# ===========================
# Table 2: Branch
# ===========================
class Branch(models.Model):
    """Organization branch/location management"""
    id = models.BigAutoField(primary_key=True)
    branch_code = models.CharField(max_length=5, unique=True, db_index=True)
    branch_name = models.CharField(max_length=200)
    
    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    address_line3 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=6)
    
    # Contact
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    manager_name = models.CharField(max_length=100)
    manager_user_code = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branches'
    )
    
    # Hierarchy
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_branches'
    )
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name='created_branches')
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_branches'
    )
    
    class Meta:
        ordering = ['branch_name']
        indexes = [
            models.Index(fields=['branch_code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['referred_by']),
        ]
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
    
    def __str__(self):
        return f"{self.branch_code} - {self.branch_name}"


# ===========================
# Table 3: AppFeature
# ===========================
class AppFeature(models.Model):
    """Define system features/modules for access control"""
    id = models.BigAutoField(primary_key=True)
    feature_code = models.CharField(max_length=4, unique=True, db_index=True)
    feature_name = models.CharField(max_length=100)
    feature_description = models.TextField()
    
    # Hierarchy
    parent_feature = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_features'
    )
    
    feature_category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(UserAccount, on_delete=models.PROTECT, related_name='created_features')
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_features'
    )
    
    class Meta:
        ordering = ['feature_name']
        indexes = [
            models.Index(fields=['feature_code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['parent_feature']),
        ]
        verbose_name = 'App Feature'
        verbose_name_plural = 'App Features'
    
    def __str__(self):
        return f"{self.feature_code} - {self.feature_name}"


# ===========================
# Table 4: OTPRecord
# ===========================
class OTPRecord(models.Model):
    """Centralized OTP management for all verification types"""
    id = models.BigAutoField(primary_key=True)
    user_code = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='otp_records', db_index=True)
    otp_type = models.CharField(max_length=20, choices=OTPTypeChoices.choices, db_index=True)
    otp_purpose = models.CharField(max_length=30, choices=OTPPurposeChoices.choices, db_index=True)
    
    # OTP Codes
    otp_code = models.CharField(max_length=128)  # Hashed
    email_otp = models.CharField(max_length=128, blank=True, null=True)  # For 'both' type
    mobile_otp = models.CharField(max_length=128, blank=True, null=True)  # For 'both' type
    
    # Contact Info
    sent_to_email = models.EmailField(blank=True, null=True)
    sent_to_mobile = models.CharField(max_length=15, blank=True, null=True)
    
    # Status
    is_used = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Tracking
    attempt_count = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['otp_type']),
            models.Index(fields=['otp_purpose']),
            models.Index(fields=['is_used']),
            models.Index(fields=['expires_at']),
        ]
        verbose_name = 'OTP Record'
        verbose_name_plural = 'OTP Records'
    
    def __str__(self):
        return f"{self.user_code} - {self.otp_type} ({self.otp_purpose})"


# ===========================
# Table 5: AadhaarKYC
# ===========================
class AadhaarKYC(models.Model):
    """Aadhaar card verification and storage"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='aadhaar_kyc', db_index=True)
    
    # Aadhaar Information
    aadhaar_number_encrypted = models.TextField()
    aadhaar_name = models.CharField(max_length=100)
    aadhaar_dob = models.DateField()
    aadhaar_gender = models.CharField(max_length=10)
    aadhaar_address = models.TextField()
    
    # Document Storage
    aadhaar_front_image = models.FileField(upload_to='kyc/aadhaar/front/', null=True, blank=True)
    aadhaar_back_image = models.FileField(upload_to='kyc/aadhaar/back/', null=True, blank=True)
    aadhaar_xml_file = models.FileField(upload_to='kyc/aadhaar/xml/', null=True, blank=True)
    
    # OTP Verification
    aadhaar_otp_request_id = models.CharField(max_length=50, blank=True, null=True)
    aadhaar_otp_attempts = models.IntegerField(default=0)
    aadhaar_blocked_until = models.DateTimeField(blank=True, null=True)
    
    # Verification Status
    verification_method = models.CharField(
        max_length=20,
        choices=VerificationMethodChoices.choices,
        default=VerificationMethodChoices.MANUAL
    )
    is_verified = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_aadhaar_records'
    )
    verification_remarks = models.TextField(blank=True, null=True)
    api_response = models.JSONField(blank=True, null=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['is_verified']),
        ]
        verbose_name = 'Aadhaar KYC'
        verbose_name_plural = 'Aadhaar KYCs'
    
    def __str__(self):
        return f"Aadhaar KYC - {self.user_code}"


# ===========================
# Table 6: PANKYC
# ===========================
class PANKYC(models.Model):
    """PAN card verification and storage"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='pan_kyc', db_index=True)
    
    # PAN Information
    pan_number = models.CharField(max_length=10)
    pan_name = models.CharField(max_length=100)
    pan_father_name = models.CharField(max_length=100)
    pan_dob = models.DateField()
    
    # Document Storage
    pan_image = models.FileField(upload_to='kyc/pan/')
    
    # Verification Status
    verification_method = models.CharField(
        max_length=20,
        choices=VerificationMethodChoices.choices,
        default=VerificationMethodChoices.MANUAL
    )
    is_verified = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_pan_records'
    )
    verification_remarks = models.TextField(blank=True, null=True)
    api_response = models.JSONField(blank=True, null=True)
    name_match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['pan_number']),
        ]
        verbose_name = 'PAN KYC'
        verbose_name_plural = 'PAN KYCs'
    
    def __str__(self):
        return f"PAN KYC - {self.user_code}"


# ===========================
# Table 7: BusinessDetails
# ===========================
class BusinessDetails(models.Model):
    """Business/shop information for merchant users"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='business_details', db_index=True)
    
    # Liveness Verification
    user_selfie = models.FileField(upload_to='business/selfies/')
    selfie_verified = models.BooleanField(default=False)
    
    # Business Information
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=50, choices=BusinessTypeChoices.choices)
    business_registration_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Business Address
    business_address_line1 = models.CharField(max_length=255)
    business_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    business_address_line3 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=6)
    
    # Business Contact with OTP
    business_phone = models.CharField(max_length=15)
    business_phone_otp_attempts = models.IntegerField(default=0)
    business_phone_blocked_until = models.DateTimeField(blank=True, null=True)
    is_business_phone_verified = models.BooleanField(default=False)
    
    business_email = models.EmailField()
    business_email_otp_attempts = models.IntegerField(default=0)
    business_email_blocked_until = models.DateTimeField(blank=True, null=True)
    is_business_email_verified = models.BooleanField(default=False)
    
    # Document Storage
    business_proof_image = models.FileField(upload_to='business/proofs/')
    
    # Verification
    is_verified = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_business_records'
    )
    verification_remarks = models.TextField(blank=True, null=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['is_verified']),
        ]
        verbose_name = 'Business Details'
        verbose_name_plural = 'Business Details'
    
    def __str__(self):
        return f"Business - {self.user_code} ({self.business_name})"


# ===========================
# Table 8: BankDetails
# ===========================
class BankDetails(models.Model):
    """Bank account verification for payment processing"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='bank_details', db_index=True)
    
    # Bank Account Information
    account_holder_name = models.CharField(max_length=100)
    account_number_encrypted = models.TextField()
    account_number_last4 = models.CharField(max_length=4)
    ifsc_code = models.CharField(max_length=11)
    account_type = models.CharField(max_length=20, choices=AccountTypeChoices.choices)
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100)
    branch_address = models.CharField(max_length=255, blank=True, null=True)
    
    # Document Storage
    bank_proof_image = models.FileField(upload_to='bank/proofs/')
    
    # Verification Methods
    verification_method = models.CharField(
        max_length=20,
        choices=BankVerificationMethodChoices.choices,
        default=BankVerificationMethodChoices.PENNY_DROP
    )
    penny_drop_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    penny_drop_reference = models.CharField(max_length=50, blank=True, null=True)
    
    # Verification Status
    is_verified = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_bank_records'
    )
    verification_remarks = models.TextField(blank=True, null=True)
    api_response = models.JSONField(blank=True, null=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['is_verified']),
        ]
        verbose_name = 'Bank Details'
        verbose_name_plural = 'Bank Details'
    
    def __str__(self):
        return f"Bank - {self.user_code} ({self.bank_name})"


# ===========================
# Table 9: UserPlatformAccess
# ===========================
class UserPlatformAccess(models.Model):
    """Control user access to different platforms"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='platform_access', db_index=True)
    platform = models.CharField(max_length=20, choices=PlatformChoices.choices, db_index=True)
    
    # Access Control
    is_allowed = models.BooleanField(default=True)
    access_level = models.CharField(max_length=20, choices=AccessLevelChoices.choices)
    allowed_ip_ranges = models.JSONField(blank=True, null=True)
    
    # Access Management
    granted_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_platform_access'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    revoked_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_platform_access'
    )
    revocation_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('user_code', 'platform')
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['platform']),
            models.Index(fields=['is_allowed']),
        ]
        verbose_name = 'User Platform Access'
        verbose_name_plural = 'User Platform Access'
    
    def __str__(self):
        return f"{self.user_code} - {self.platform}"


# ===========================
# Table 10: AppAccessControl
# ===========================
class AppAccessControl(models.Model):
    """Feature-level access control for users"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='feature_access', db_index=True)
    feature = models.ForeignKey(AppFeature, on_delete=models.CASCADE, related_name='user_access', db_index=True)
    
    # Access Control
    is_allowed = models.BooleanField(default=False)
    access_level = models.CharField(max_length=20, choices=AccessLevelChoices.choices)
    
    # Access Management
    granted_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_feature_access'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    revoked_at = models.DateTimeField(blank=True, null=True)
    revoked_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_feature_access'
    )
    
    class Meta:
        unique_together = ('user_code', 'feature')
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['feature']),
            models.Index(fields=['is_allowed']),
        ]
        verbose_name = 'App Access Control'
        verbose_name_plural = 'App Access Controls'
    
    def __str__(self):
        return f"{self.user_code} - {self.feature.feature_code}"


# ===========================
# Table 11: LoginActivity
# ===========================
class LoginActivity(models.Model):
    """Track all login attempts and sessions"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='login_activities',
        db_index=True
    )
    
    # Login Attempt Details
    login_identifier = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField()
    device_info = models.JSONField()
    location_info = models.JSONField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=30, choices=LoginStatusChoices.choices, db_index=True)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    
    # Session Information
    session_token = models.CharField(max_length=255, blank=True, null=True)
    login_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    logout_timestamp = models.DateTimeField(blank=True, null=True)
    session_duration = models.DurationField(blank=True, null=True)
    
    # Security
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    class Meta:
        ordering = ['-login_timestamp']
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['login_timestamp']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'Login Activity'
        verbose_name_plural = 'Login Activities'
    
    def __str__(self):
        return f"Login - {self.login_identifier} ({self.status})"


# ===========================
# Table 12: AuditTrail
# ===========================
class AuditTrail(models.Model):
    """Comprehensive audit log for all system operations"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_trails',
        db_index=True
    )
    
    # Action Details
    action = models.CharField(max_length=30, choices=AuditActionChoices.choices, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)
    resource_id = models.CharField(max_length=50, blank=True, null=True)
    resource_identifier = models.CharField(max_length=100, blank=True, null=True)
    
    # Description and Changes
    description = models.TextField()
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    changed_fields = models.JSONField(blank=True, null=True)
    
    # Request Information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    request_method = models.CharField(max_length=10, blank=True, null=True)
    request_path = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['action']),
            models.Index(fields=['resource_type']),
            models.Index(fields=['resource_id']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trails'
    
    def __str__(self):
        return f"{self.action} - {self.resource_type} ({self.resource_id})"


# ===========================
# Table 13: RegistrationProgress
# ===========================
class RegistrationProgress(models.Model):
    """Track multi-step registration progress"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='registration_progress', db_index=True)
    
    # Progress Tracking
    current_step = models.IntegerField()
    steps_completed = models.JSONField(default=list)
    step_data = models.JSONField(default=dict)
    last_completed_step = models.IntegerField(default=0)
    
    # Status
    abandoned = models.BooleanField(default=False)
    abandoned_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    last_active_at = models.DateTimeField(auto_now=True, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-last_active_at']
        indexes = [
            models.Index(fields=['user_code']),
            models.Index(fields=['current_step']),
            models.Index(fields=['last_active_at']),
        ]
        verbose_name = 'Registration Progress'
        verbose_name_plural = 'Registration Progress'
    
    def __str__(self):
        return f"Registration - {self.user_code} (Step {self.current_step})"


# ===========================
# Table 14: SecuritySettings
# ===========================
class SecuritySettings(models.Model):
    """User-specific security configurations"""
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='security_settings', db_index=True)
    
    # Two-Factor Authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(
        max_length=20,
        choices=TwoFactorMethodChoices.choices,
        blank=True,
        null=True
    )
    
    # Notifications
    login_notification_enabled = models.BooleanField(default=True)
    suspicious_activity_alert = models.BooleanField(default=True)
    
    # IP Whitelist
    allowed_ip_whitelist = models.JSONField(blank=True, null=True)
    
    # Password Policy
    password_expiry_days = models.IntegerField(default=90)
    last_password_change = models.DateTimeField(blank=True, null=True)
    
    # Account Lockout
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user_code']),
        ]
        verbose_name = 'Security Settings'
        verbose_name_plural = 'Security Settings'
    
    def __str__(self):
        return f"Security Settings - {self.user_code}"
