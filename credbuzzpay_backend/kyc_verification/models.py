"""
KYC Verification Models
========================
Comprehensive KYC/Onboarding models for user verification with:
- OTP verification for email/phone
- Identity proof (Aadhaar, PAN)
- Business details and address
- Verification images (selfie, office, address proof)
- Bank details
- Progress tracking
- Audit logging

Security Features:
- Encrypted sensitive data (Aadhaar, PAN numbers)
- Data masking for display
- Step-by-step validation
- Audit trail for all changes
"""

import uuid
import hashlib
import os
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
import base64


# =============================================================================
# ENCRYPTION UTILITIES
# =============================================================================

def get_encryption_key():
    """Get or generate encryption key for sensitive data."""
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    if not key:
        # Generate a key from SECRET_KEY if not configured
        secret = settings.SECRET_KEY.encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return key


def encrypt_value(value):
    """Encrypt sensitive value."""
    if not value:
        return value
    try:
        f = Fernet(get_encryption_key())
        return f.encrypt(value.encode()).decode()
    except Exception:
        return value


def decrypt_value(encrypted_value):
    """Decrypt sensitive value."""
    if not encrypted_value:
        return encrypted_value
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception:
        return encrypted_value


def mask_aadhaar(aadhaar_number):
    """Mask Aadhaar number: XXXX-XXXX-1234"""
    if not aadhaar_number or len(aadhaar_number) < 4:
        return "XXXX-XXXX-XXXX"
    return f"XXXX-XXXX-{aadhaar_number[-4:]}"


def mask_pan(pan_number):
    """Mask PAN number: ABCXX1234X"""
    if not pan_number or len(pan_number) < 10:
        return "XXXXXXXXXX"
    return f"{pan_number[:3]}XX{pan_number[5:9]}X"


def mask_account_number(account_number):
    """Mask bank account number: XXXXXX1234"""
    if not account_number or len(account_number) < 4:
        return "XXXXXXXXXX"
    return f"{'X' * (len(account_number) - 4)}{account_number[-4:]}"


# =============================================================================
# FILE UPLOAD PATHS
# =============================================================================

def aadhaar_front_path(instance, filename):
    """Generate secure path for Aadhaar front image."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"kyc/{instance.kyc_application.user.user_code}/aadhaar/front_{new_filename}"


def aadhaar_back_path(instance, filename):
    """Generate secure path for Aadhaar back image."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"kyc/{instance.kyc_application.user.user_code}/aadhaar/back_{new_filename}"


def pan_image_path(instance, filename):
    """Generate secure path for PAN image."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"kyc/{instance.kyc_application.user.user_code}/pan/{new_filename}"


def selfie_path(instance, filename):
    """Generate secure path for selfie image."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"kyc/{instance.kyc_application.user.user_code}/verification/selfie_{new_filename}"


def office_sitting_path(instance, filename):
    """Generate secure path for office sitting image."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"kyc/{instance.kyc_application.user.user_code}/verification/office_sitting_{new_filename}"


def office_door_path(instance, filename):
    """Generate secure path for office door image."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"kyc/{instance.kyc_application.user.user_code}/verification/office_door_{new_filename}"


def address_proof_path(instance, filename):
    """Generate secure path for address proof image."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"kyc/{instance.kyc_application.user.user_code}/verification/address_proof_{new_filename}"


def bank_document_path(instance, filename):
    """Generate secure path for bank document."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"kyc/{instance.kyc_application.user.user_code}/bank/{new_filename}"


# =============================================================================
# VALIDATORS
# =============================================================================

aadhaar_validator = RegexValidator(
    regex=r'^\d{12}$',
    message='Aadhaar number must be exactly 12 digits.'
)

pan_validator = RegexValidator(
    regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$',
    message='PAN must be in format: ABCDE1234F'
)

phone_validator = RegexValidator(
    regex=r'^\d{10}$',
    message='Phone number must be exactly 10 digits.'
)

pincode_validator = RegexValidator(
    regex=r'^\d{6}$',
    message='Pincode must be exactly 6 digits.'
)

ifsc_validator = RegexValidator(
    regex=r'^[A-Z]{4}0[A-Z0-9]{6}$',
    message='IFSC code must be in format: ABCD0XXXXXX'
)

account_number_validator = RegexValidator(
    regex=r'^\d{9,18}$',
    message='Account number must be between 9 and 18 digits.'
)


def validate_file_size(file):
    """Validate file size is under 5MB."""
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise ValidationError(f'File size must be under 5MB. Current size: {file.size / (1024*1024):.2f}MB')


# =============================================================================
# CHOICE ENUMS
# =============================================================================

class OTPType(models.TextChoices):
    EMAIL = 'EMAIL', 'Email Verification'
    PHONE = 'PHONE', 'Phone Verification'
    LOGIN = 'LOGIN', 'Login Verification'
    PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'


class KYCStatus(models.TextChoices):
    NOT_STARTED = 'NOT_STARTED', 'Not Started'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    RESUBMIT = 'RESUBMIT', 'Resubmission Required'


class MegaStep(models.TextChoices):
    IDENTITY_PROOF = 'IDENTITY_PROOF', 'Identity Proof'
    SELFIE_AND_BUSINESS = 'SELFIE_AND_BUSINESS', 'Selfie & Business Address'
    COMPLETED = 'COMPLETED', 'All Steps Completed'


class StepStatus(models.TextChoices):
    NOT_STARTED = 'NOT_STARTED', 'Not Started'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    NEEDS_CORRECTION = 'NEEDS_CORRECTION', 'Needs Correction'


class AccountType(models.TextChoices):
    SAVINGS = 'SAVINGS', 'Savings Account'
    CURRENT = 'CURRENT', 'Current Account'


class AuditAction(models.TextChoices):
    KYC_STARTED = 'KYC_STARTED', 'KYC Started'
    STEP_COMPLETED = 'STEP_COMPLETED', 'Step Completed'
    KYC_SUBMITTED = 'KYC_SUBMITTED', 'KYC Submitted'
    STATUS_CHANGED = 'STATUS_CHANGED', 'Status Changed'
    DOCUMENT_UPLOADED = 'DOCUMENT_UPLOADED', 'Document Uploaded'
    DOCUMENT_UPDATED = 'DOCUMENT_UPDATED', 'Document Updated'
    ADMIN_REVIEW = 'ADMIN_REVIEW', 'Admin Review'
    ADMIN_APPROVED = 'ADMIN_APPROVED', 'Admin Approved'
    ADMIN_REJECTED = 'ADMIN_REJECTED', 'Admin Rejected'
    RESUBMIT_REQUESTED = 'RESUBMIT_REQUESTED', 'Resubmit Requested'


# =============================================================================
# OTP VERIFICATION MODEL
# =============================================================================

class OTPVerification(models.Model):
    """
    OTP verification for email and phone.
    Used during registration and login verification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users_auth.User',
        on_delete=models.CASCADE,
        related_name='otp_verifications'
    )
    otp_type = models.CharField(
        max_length=20,
        choices=OTPType.choices,
        default=OTPType.EMAIL
    )
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'kyc_otp_verification'
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'otp_type', '-created_at']),
            models.Index(fields=['otp_code', 'expires_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_type}"
    
    @property
    def is_expired(self):
        """Check if OTP has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if OTP is still valid (not expired, not used, attempts remaining)."""
        return not self.is_expired and not self.is_verified and self.attempts < self.max_attempts
    
    def verify(self, code):
        """Verify OTP code."""
        self.attempts += 1
        self.save(update_fields=['attempts'])
        
        if not self.is_valid:
            return False, 'OTP expired or max attempts exceeded'
        
        if self.otp_code != code:
            return False, 'Invalid OTP code'
        
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])
        return True, 'OTP verified successfully'


# =============================================================================
# KYC APPLICATION MODEL (Master Record)
# =============================================================================

class KYCApplication(models.Model):
    """
    Master KYC application record.
    Tracks overall KYC status and progress.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'users_auth.User',
        on_delete=models.CASCADE,
        related_name='kyc_application'
    )
    application_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=KYCStatus.choices,
        default=KYCStatus.NOT_STARTED
    )
    mega_step = models.CharField(
        max_length=30,
        choices=MegaStep.choices,
        default=MegaStep.IDENTITY_PROOF
    )
    current_step = models.PositiveSmallIntegerField(default=1)
    total_steps = models.PositiveSmallIntegerField(default=8)
    completion_percentage = models.PositiveSmallIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Review information
    reviewed_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_kyc_applications'
    )
    review_remarks = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Verification flags
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'kyc_application'
        verbose_name = 'KYC Application'
        verbose_name_plural = 'KYC Applications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['application_id']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"KYC-{self.application_id} ({self.user.email}) - {self.status}"
    
    def save(self, *args, **kwargs):
        # Generate application ID if not exists
        if not self.application_id:
            self.application_id = self._generate_application_id()
        
        # Update completion percentage
        self._update_completion()
        
        super().save(*args, **kwargs)
    
    def _generate_application_id(self):
        """Generate unique application ID: KYC-YYYYMMDD-XXXXXX"""
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = uuid.uuid4().hex[:6].upper()
        return f"KYC{date_part}{random_part}"
    
    def _update_completion(self):
        """Calculate and update completion percentage."""
        completed_steps = 0
        
        # Check each component
        if hasattr(self, 'identity_proof'):
            if self.identity_proof.aadhaar_verified:
                completed_steps += 2  # Aadhaar details + photos
            if self.identity_proof.pan_verified:
                completed_steps += 2  # PAN details + photo
        
        if hasattr(self, 'business_details') and self.business_details.is_complete:
            completed_steps += 1
        
        if hasattr(self, 'verification_images') and self.verification_images.is_complete:
            completed_steps += 2
        
        if hasattr(self, 'bank_details') and self.bank_details.is_verified:
            completed_steps += 1
        
        self.completion_percentage = int((completed_steps / self.total_steps) * 100)
    
    def submit(self):
        """Submit KYC for review."""
        if self.completion_percentage < 100:
            raise ValidationError('All steps must be completed before submission.')
        
        self.status = KYCStatus.SUBMITTED
        self.submitted_at = timezone.now()
        self.save(update_fields=['status', 'submitted_at', 'updated_at'])
    
    def start_review(self, admin_user):
        """Start admin review of KYC application."""
        self.status = KYCStatus.UNDER_REVIEW
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
    
    def approve(self, admin_user, remarks=''):
        """Approve KYC application."""
        self.status = KYCStatus.APPROVED
        self.reviewed_by = admin_user
        self.review_remarks = remarks
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'review_remarks', 'approved_at', 'updated_at'])
    
    def reject(self, admin_user, reason):
        """Reject KYC application."""
        self.status = KYCStatus.REJECTED
        self.reviewed_by = admin_user
        self.rejection_reason = reason
        self.save(update_fields=['status', 'reviewed_by', 'rejection_reason', 'updated_at'])
    
    def request_resubmit(self, admin_user, reason):
        """Request user to resubmit with corrections."""
        self.status = KYCStatus.RESUBMIT
        self.reviewed_by = admin_user
        self.review_remarks = reason
        self.save(update_fields=['status', 'reviewed_by', 'review_remarks', 'updated_at'])


# =============================================================================
# IDENTITY PROOF MODEL (Aadhaar & PAN)
# =============================================================================

class IdentityProof(models.Model):
    """
    Identity proof documents: Aadhaar and PAN.
    Sensitive data is encrypted at rest.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_application = models.OneToOneField(
        KYCApplication,
        on_delete=models.CASCADE,
        related_name='identity_proof'
    )
    
    # Aadhaar Details (encrypted)
    aadhaar_number_encrypted = models.CharField(max_length=255, blank=True)
    aadhaar_name = models.CharField(max_length=100, blank=True)
    aadhaar_dob = models.DateField(null=True, blank=True)
    aadhaar_address = models.TextField(blank=True)
    aadhaar_front_image = models.ImageField(
        upload_to=aadhaar_front_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf']),
            validate_file_size
        ],
        null=True,
        blank=True
    )
    aadhaar_back_image = models.ImageField(
        upload_to=aadhaar_back_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf']),
            validate_file_size
        ],
        null=True,
        blank=True
    )
    aadhaar_verified = models.BooleanField(default=False)
    aadhaar_submitted_at = models.DateTimeField(null=True, blank=True)
    
    # PAN Details (encrypted)
    pan_number_encrypted = models.CharField(max_length=255, blank=True)
    pan_name = models.CharField(max_length=100, blank=True)
    pan_dob = models.DateField(null=True, blank=True)
    pan_father_name = models.CharField(max_length=100, blank=True)
    pan_image = models.ImageField(
        upload_to=pan_image_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf']),
            validate_file_size
        ],
        null=True,
        blank=True
    )
    pan_verified = models.BooleanField(default=False)
    pan_submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kyc_identity_proof'
        verbose_name = 'Identity Proof'
        verbose_name_plural = 'Identity Proofs'
    
    def __str__(self):
        return f"Identity Proof for {self.kyc_application.application_id}"
    
    # Aadhaar number property with encryption
    @property
    def aadhaar_number(self):
        """Get decrypted Aadhaar number."""
        return decrypt_value(self.aadhaar_number_encrypted)
    
    @aadhaar_number.setter
    def aadhaar_number(self, value):
        """Set encrypted Aadhaar number."""
        if value:
            # Validate Aadhaar format
            aadhaar_validator(value)
            self.aadhaar_number_encrypted = encrypt_value(value)
    
    @property
    def aadhaar_masked(self):
        """Get masked Aadhaar number for display."""
        return mask_aadhaar(self.aadhaar_number)
    
    # PAN number property with encryption
    @property
    def pan_number(self):
        """Get decrypted PAN number."""
        return decrypt_value(self.pan_number_encrypted)
    
    @pan_number.setter
    def pan_number(self, value):
        """Set encrypted PAN number."""
        if value:
            # Validate PAN format
            value = value.upper()
            pan_validator(value)
            self.pan_number_encrypted = encrypt_value(value)
    
    @property
    def pan_masked(self):
        """Get masked PAN number for display."""
        return mask_pan(self.pan_number)
    
    @property
    def is_aadhaar_complete(self):
        """Check if Aadhaar details are complete."""
        return all([
            self.aadhaar_number_encrypted,
            self.aadhaar_name,
            self.aadhaar_dob,
            self.aadhaar_front_image,
            self.aadhaar_back_image
        ])
    
    @property
    def is_pan_complete(self):
        """Check if PAN details are complete."""
        return all([
            self.pan_number_encrypted,
            self.pan_name,
            self.pan_dob,
            self.pan_image
        ])
    
    @property
    def is_complete(self):
        """Check if all identity proofs are complete."""
        return self.is_aadhaar_complete and self.is_pan_complete


# =============================================================================
# BUSINESS DETAILS MODEL
# =============================================================================

class BusinessDetails(models.Model):
    """
    Business information and address details.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_application = models.OneToOneField(
        KYCApplication,
        on_delete=models.CASCADE,
        related_name='business_details'
    )
    
    # Business Information
    business_name = models.CharField(max_length=200, blank=True)
    business_type = models.CharField(max_length=100, blank=True)
    business_phone = models.CharField(
        max_length=10,
        validators=[phone_validator],
        blank=True
    )
    business_email = models.EmailField(blank=True)
    
    # Business Address
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    address_line_3 = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(
        max_length=6,
        validators=[pincode_validator],
        blank=True
    )
    country = models.CharField(max_length=100, default='India')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kyc_business_details'
        verbose_name = 'Business Details'
        verbose_name_plural = 'Business Details'
    
    def __str__(self):
        return f"Business: {self.business_name or 'N/A'} - {self.kyc_application.application_id}"
    
    @property
    def full_address(self):
        """Get formatted full address."""
        parts = [
            self.address_line_1,
            self.address_line_2,
            self.address_line_3,
            self.landmark,
            self.city,
            self.district,
            self.state,
            self.pincode,
            self.country
        ]
        return ', '.join(filter(None, parts))
    
    @property
    def is_complete(self):
        """Check if business details are complete."""
        return all([
            self.business_name,
            self.business_phone,
            self.address_line_1,
            self.city,
            self.state,
            self.pincode
        ])


# =============================================================================
# VERIFICATION IMAGES MODEL
# =============================================================================

class VerificationImages(models.Model):
    """
    Verification images: selfie, office photos, address proof.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_application = models.OneToOneField(
        KYCApplication,
        on_delete=models.CASCADE,
        related_name='verification_images'
    )
    
    # Selfie
    selfie_image = models.ImageField(
        upload_to=selfie_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size
        ],
        null=True,
        blank=True
    )
    selfie_submitted_at = models.DateTimeField(null=True, blank=True)
    selfie_verified = models.BooleanField(default=False)
    
    # Office Photos
    office_sitting_image = models.ImageField(
        upload_to=office_sitting_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size
        ],
        null=True,
        blank=True,
        help_text='Photo of you sitting inside your office/workplace'
    )
    office_door_image = models.ImageField(
        upload_to=office_door_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size
        ],
        null=True,
        blank=True,
        help_text='Photo of office entrance/door with name board'
    )
    office_photos_submitted_at = models.DateTimeField(null=True, blank=True)
    office_photos_verified = models.BooleanField(default=False)
    
    # Address Proof
    address_proof_image = models.ImageField(
        upload_to=address_proof_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf']),
            validate_file_size
        ],
        null=True,
        blank=True,
        help_text='Utility bill, rental agreement, or other address proof'
    )
    address_proof_type = models.CharField(max_length=50, blank=True)
    address_proof_submitted_at = models.DateTimeField(null=True, blank=True)
    address_proof_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kyc_verification_images'
        verbose_name = 'Verification Images'
        verbose_name_plural = 'Verification Images'
    
    def __str__(self):
        return f"Verification Images for {self.kyc_application.application_id}"
    
    @property
    def is_selfie_complete(self):
        """Check if selfie is uploaded."""
        return bool(self.selfie_image)
    
    @property
    def is_office_complete(self):
        """Check if office photos are uploaded."""
        return bool(self.office_sitting_image and self.office_door_image)
    
    @property
    def is_address_proof_complete(self):
        """Check if address proof is uploaded."""
        return bool(self.address_proof_image)
    
    @property
    def is_complete(self):
        """Check if all verification images are uploaded."""
        return self.is_selfie_complete and self.is_office_complete and self.is_address_proof_complete


# =============================================================================
# BANK DETAILS MODEL
# =============================================================================

class BankDetails(models.Model):
    """
    Bank account details for payment processing.
    Account number is encrypted at rest.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_application = models.OneToOneField(
        KYCApplication,
        on_delete=models.CASCADE,
        related_name='bank_details'
    )
    
    # Account Information
    account_holder_name = models.CharField(max_length=200, blank=True)
    account_number_encrypted = models.CharField(max_length=255, blank=True)
    confirm_account_number_encrypted = models.CharField(max_length=255, blank=True)
    ifsc_code = models.CharField(
        max_length=11,
        validators=[ifsc_validator],
        blank=True
    )
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.SAVINGS
    )
    
    # Bank Information
    bank_name = models.CharField(max_length=200, blank=True)
    branch_name = models.CharField(max_length=200, blank=True)
    branch_address = models.TextField(blank=True)
    
    # Bank Document (Cancelled cheque/passbook)
    bank_document = models.ImageField(
        upload_to=bank_document_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf']),
            validate_file_size
        ],
        null=True,
        blank=True,
        help_text='Cancelled cheque or passbook front page'
    )
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kyc_bank_details'
        verbose_name = 'Bank Details'
        verbose_name_plural = 'Bank Details'
    
    def __str__(self):
        return f"Bank: {self.bank_name or 'N/A'} - {self.kyc_application.application_id}"
    
    # Account number property with encryption
    @property
    def account_number(self):
        """Get decrypted account number."""
        return decrypt_value(self.account_number_encrypted)
    
    @account_number.setter
    def account_number(self, value):
        """Set encrypted account number."""
        if value:
            account_number_validator(value)
            self.account_number_encrypted = encrypt_value(value)
    
    @property
    def account_number_masked(self):
        """Get masked account number for display."""
        return mask_account_number(self.account_number)
    
    def set_confirm_account_number(self, value):
        """Set confirm account number."""
        if value:
            self.confirm_account_number_encrypted = encrypt_value(value)
    
    def validate_account_numbers_match(self):
        """Validate that account numbers match."""
        if self.account_number_encrypted and self.confirm_account_number_encrypted:
            acc1 = decrypt_value(self.account_number_encrypted)
            acc2 = decrypt_value(self.confirm_account_number_encrypted)
            if acc1 != acc2:
                raise ValidationError('Account numbers do not match.')
        return True
    
    @property
    def is_complete(self):
        """Check if bank details are complete."""
        return all([
            self.account_holder_name,
            self.account_number_encrypted,
            self.ifsc_code,
            self.bank_name,
            self.bank_document
        ])


# =============================================================================
# KYC PROGRESS TRACKER MODEL
# =============================================================================

class KYCProgressTracker(models.Model):
    """
    Tracks step-by-step KYC progress.
    Stores data snapshot at each step for audit purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_application = models.ForeignKey(
        KYCApplication,
        on_delete=models.CASCADE,
        related_name='progress_steps'
    )
    
    # Step Information
    step_name = models.CharField(max_length=50)
    step_number = models.PositiveSmallIntegerField()
    mega_step = models.CharField(
        max_length=30,
        choices=MegaStep.choices
    )
    status = models.CharField(
        max_length=20,
        choices=StepStatus.choices,
        default=StepStatus.NOT_STARTED
    )
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Data snapshot (JSON) for audit
    data_snapshot = models.JSONField(default=dict, blank=True)
    
    # Correction info
    needs_correction = models.BooleanField(default=False)
    correction_remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'kyc_progress_tracker'
        verbose_name = 'KYC Progress Step'
        verbose_name_plural = 'KYC Progress Steps'
        ordering = ['step_number']
        unique_together = ['kyc_application', 'step_number']
    
    def __str__(self):
        return f"Step {self.step_number}: {self.step_name} - {self.status}"
    
    def start(self):
        """Mark step as started."""
        self.status = StepStatus.IN_PROGRESS
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def complete(self, data_snapshot=None):
        """Mark step as completed."""
        self.status = StepStatus.COMPLETED
        self.completed_at = timezone.now()
        if data_snapshot:
            self.data_snapshot = data_snapshot
        self.save(update_fields=['status', 'completed_at', 'data_snapshot'])
    
    def mark_needs_correction(self, remarks):
        """Mark step as needing correction."""
        self.status = StepStatus.NEEDS_CORRECTION
        self.needs_correction = True
        self.correction_remarks = remarks
        self.save(update_fields=['status', 'needs_correction', 'correction_remarks'])


# =============================================================================
# KYC AUDIT LOG MODEL
# =============================================================================

class KYCAuditLog(models.Model):
    """
    Audit log for all KYC-related actions.
    Provides complete audit trail for compliance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_application = models.ForeignKey(
        KYCApplication,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    # Action Information
    action = models.CharField(
        max_length=30,
        choices=AuditAction.choices
    )
    performed_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='kyc_audit_actions'
    )
    
    # Status Change
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    
    # Details
    remarks = models.TextField(blank=True)
    data_changed = models.JSONField(default=dict, blank=True)
    
    # Request Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'kyc_audit_log'
        verbose_name = 'KYC Audit Log'
        verbose_name_plural = 'KYC Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['kyc_application', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['performed_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.kyc_application.application_id} at {self.created_at}"
    
    @classmethod
    def log_action(cls, kyc_application, action, performed_by, old_status='', 
                   new_status='', remarks='', data_changed=None, ip_address=None, 
                   user_agent=''):
        """Create an audit log entry."""
        return cls.objects.create(
            kyc_application=kyc_application,
            action=action,
            performed_by=performed_by,
            old_status=old_status,
            new_status=new_status,
            remarks=remarks,
            data_changed=data_changed or {},
            ip_address=ip_address,
            user_agent=user_agent
        )


# =============================================================================
# SIGNALS FOR AUTOMATIC ACTIONS
# =============================================================================

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=KYCApplication)
def create_related_models(sender, instance, created, **kwargs):
    """Create related models when KYCApplication is created."""
    if created:
        # Create IdentityProof
        IdentityProof.objects.create(kyc_application=instance)
        
        # Create BusinessDetails
        BusinessDetails.objects.create(kyc_application=instance)
        
        # Create VerificationImages
        VerificationImages.objects.create(kyc_application=instance)
        
        # Create BankDetails
        BankDetails.objects.create(kyc_application=instance)
        
        # Create Progress Tracker for each step
        steps = [
            (1, 'Aadhaar Details', MegaStep.IDENTITY_PROOF),
            (2, 'Aadhaar Photos', MegaStep.IDENTITY_PROOF),
            (3, 'PAN Details', MegaStep.IDENTITY_PROOF),
            (4, 'PAN Photo', MegaStep.IDENTITY_PROOF),
            (5, 'Business Details', MegaStep.SELFIE_AND_BUSINESS),
            (6, 'Verification Images', MegaStep.SELFIE_AND_BUSINESS),
            (7, 'Address Proof', MegaStep.SELFIE_AND_BUSINESS),
            (8, 'Bank Details', MegaStep.SELFIE_AND_BUSINESS),
        ]
        
        for step_number, step_name, mega_step in steps:
            KYCProgressTracker.objects.create(
                kyc_application=instance,
                step_name=step_name,
                step_number=step_number,
                mega_step=mega_step
            )
        
        # Log KYC started
        KYCAuditLog.log_action(
            kyc_application=instance,
            action=AuditAction.KYC_STARTED,
            performed_by=instance.user,
            new_status=KYCStatus.NOT_STARTED
        )
