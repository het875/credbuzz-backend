"""
KYC Verification Serializers
==============================
Serializers for KYC/Onboarding system with:
- Input validation
- Sensitive data masking
- Step-by-step progress tracking
- Admin review capabilities
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    OTPVerification, KYCApplication, IdentityProof, BusinessDetails,
    VerificationImages, BankDetails, KYCProgressTracker, KYCAuditLog,
    OTPType, KYCStatus, MegaStep, StepStatus, AccountType, AuditAction,
    mask_aadhaar, mask_pan, mask_account_number,
    aadhaar_validator, pan_validator, phone_validator, pincode_validator,
    ifsc_validator, account_number_validator
)


# =============================================================================
# OTP SERIALIZERS
# =============================================================================

class OTPSendSerializer(serializers.Serializer):
    """Serializer for sending OTP."""
    otp_type = serializers.ChoiceField(choices=OTPType.choices)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=10, required=False)
    
    def validate(self, data):
        otp_type = data.get('otp_type')
        
        if otp_type == OTPType.EMAIL and not data.get('email'):
            raise serializers.ValidationError({'email': 'Email is required for email OTP.'})
        
        if otp_type == OTPType.PHONE and not data.get('phone'):
            raise serializers.ValidationError({'phone': 'Phone is required for phone OTP.'})
        
        return data


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for verifying OTP."""
    otp_type = serializers.ChoiceField(choices=OTPType.choices)
    otp_code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('OTP must contain only digits.')
        return value


class OTPResponseSerializer(serializers.ModelSerializer):
    """Serializer for OTP response."""
    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    remaining_attempts = serializers.SerializerMethodField()
    
    class Meta:
        model = OTPVerification
        fields = ['id', 'otp_type', 'is_verified', 'is_valid', 'is_expired', 
                  'remaining_attempts', 'created_at', 'expires_at']
        read_only_fields = fields
    
    def get_remaining_attempts(self, obj):
        return max(0, obj.max_attempts - obj.attempts)


# =============================================================================
# KYC PROGRESS SERIALIZERS
# =============================================================================

class KYCProgressSerializer(serializers.ModelSerializer):
    """Serializer for KYC progress step."""
    
    class Meta:
        model = KYCProgressTracker
        fields = ['id', 'step_name', 'step_number', 'mega_step', 'status',
                  'started_at', 'completed_at', 'needs_correction', 'correction_remarks']
        read_only_fields = fields


class KYCProgressUpdateSerializer(serializers.Serializer):
    """Serializer for updating progress step."""
    step_number = serializers.IntegerField(min_value=1, max_value=8)
    status = serializers.ChoiceField(choices=StepStatus.choices)
    data_snapshot = serializers.JSONField(required=False)


# =============================================================================
# IDENTITY PROOF SERIALIZERS
# =============================================================================

class AadhaarDetailsSerializer(serializers.Serializer):
    """Serializer for Aadhaar details input."""
    aadhaar_number = serializers.CharField(max_length=12, min_length=12)
    aadhaar_name = serializers.CharField(max_length=100)
    aadhaar_dob = serializers.DateField()
    aadhaar_address = serializers.CharField(required=False, allow_blank=True)
    
    def validate_aadhaar_number(self, value):
        try:
            aadhaar_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value


class AadhaarUploadSerializer(serializers.Serializer):
    """Serializer for Aadhaar image upload."""
    aadhaar_front_image = serializers.ImageField()
    aadhaar_back_image = serializers.ImageField()
    
    def validate(self, data):
        max_size = 5 * 1024 * 1024  # 5MB
        
        for field in ['aadhaar_front_image', 'aadhaar_back_image']:
            file = data.get(field)
            if file and file.size > max_size:
                raise serializers.ValidationError({
                    field: f'File size must be under 5MB. Current: {file.size / (1024*1024):.2f}MB'
                })
        
        return data


class PANDetailsSerializer(serializers.Serializer):
    """Serializer for PAN details input."""
    pan_number = serializers.CharField(max_length=10, min_length=10)
    pan_name = serializers.CharField(max_length=100)
    pan_dob = serializers.DateField()
    pan_father_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_pan_number(self, value):
        value = value.upper()
        try:
            pan_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value


class PANUploadSerializer(serializers.Serializer):
    """Serializer for PAN image upload."""
    pan_image = serializers.ImageField()
    
    def validate_pan_image(self, value):
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size must be under 5MB. Current: {value.size / (1024*1024):.2f}MB'
            )
        return value


class AadhaarUpdateSerializer(serializers.Serializer):
    """Serializer for Aadhaar update (details + optional images)."""
    aadhaar_number = serializers.CharField(max_length=12, min_length=12)
    aadhaar_name = serializers.CharField(max_length=100)
    aadhaar_dob = serializers.DateField()
    aadhaar_address = serializers.CharField(required=False, allow_blank=True)
    aadhaar_front_image = serializers.ImageField(required=False, allow_null=True)
    aadhaar_back_image = serializers.ImageField(required=False, allow_null=True)
    
    def validate_aadhaar_number(self, value):
        try:
            aadhaar_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value
    
    def validate(self, data):
        max_size = 5 * 1024 * 1024  # 5MB
        
        # Validate image sizes if provided
        for field in ['aadhaar_front_image', 'aadhaar_back_image']:
            file = data.get(field)
            if file and file.size > max_size:
                raise serializers.ValidationError({
                    field: f'File size must be under 5MB. Current: {file.size / (1024*1024):.2f}MB'
                })
        
        # If one image is provided, both should be provided
        has_front = data.get('aadhaar_front_image') is not None
        has_back = data.get('aadhaar_back_image') is not None
        
        if has_front != has_back:
            raise serializers.ValidationError({
                'aadhaar_images': 'Both front and back images must be provided together, or neither.'
            })
        
        return data


class PANUpdateSerializer(serializers.Serializer):
    """Serializer for PAN update (details + optional image)."""
    pan_number = serializers.CharField(max_length=10, min_length=10)
    pan_name = serializers.CharField(max_length=100)
    pan_dob = serializers.DateField()
    pan_father_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    pan_image = serializers.ImageField(required=False, allow_null=True)
    
    def validate_pan_number(self, value):
        value = value.upper()
        try:
            pan_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value
    
    def validate_pan_image(self, value):
        if value:
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    f'File size must be under 5MB. Current: {value.size / (1024*1024):.2f}MB'
                )
        return value


class IdentityProofSerializer(serializers.ModelSerializer):
    """Serializer for Identity Proof display."""
    aadhaar_masked = serializers.CharField(read_only=True)
    pan_masked = serializers.CharField(read_only=True)
    is_aadhaar_complete = serializers.BooleanField(read_only=True)
    is_pan_complete = serializers.BooleanField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    
    # Image URLs
    aadhaar_front_url = serializers.SerializerMethodField()
    aadhaar_back_url = serializers.SerializerMethodField()
    pan_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = IdentityProof
        fields = [
            'id', 'aadhaar_masked', 'aadhaar_name', 'aadhaar_dob', 'aadhaar_address',
            'aadhaar_front_url', 'aadhaar_back_url', 'aadhaar_verified', 'aadhaar_submitted_at',
            'pan_masked', 'pan_name', 'pan_dob', 'pan_father_name',
            'pan_image_url', 'pan_verified', 'pan_submitted_at',
            'is_aadhaar_complete', 'is_pan_complete', 'is_complete',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_aadhaar_front_url(self, obj):
        if obj.aadhaar_front_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhaar_front_image.url)
            return obj.aadhaar_front_image.url
        return None
    
    def get_aadhaar_back_url(self, obj):
        if obj.aadhaar_back_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhaar_back_image.url)
            return obj.aadhaar_back_image.url
        return None
    
    def get_pan_image_url(self, obj):
        if obj.pan_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pan_image.url)
            return obj.pan_image.url
        return None


class AadhaarDetailsResponseSerializer(serializers.ModelSerializer):
    """Serializer for Aadhaar details with both masked and unmasked values."""
    aadhaar_number_masked = serializers.CharField(source='aadhaar_masked', read_only=True)
    aadhaar_number = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(source='is_aadhaar_complete', read_only=True)
    is_verified = serializers.BooleanField(source='aadhaar_verified', read_only=True)
    submitted_at = serializers.DateTimeField(source='aadhaar_submitted_at', read_only=True)
    
    class Meta:
        model = IdentityProof
        fields = [
            'aadhaar_number', 'aadhaar_number_masked', 'aadhaar_name', 
            'aadhaar_dob', 'aadhaar_address', 'is_complete', 'is_verified', 
            'submitted_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_aadhaar_number(self, obj):
        """Return unmasked Aadhaar number for verification."""
        return obj.aadhaar_number if obj.aadhaar_number else None


class AadhaarImagesResponseSerializer(serializers.ModelSerializer):
    """Serializer for Aadhaar images only."""
    aadhaar_front_url = serializers.SerializerMethodField()
    aadhaar_back_url = serializers.SerializerMethodField()
    has_images = serializers.SerializerMethodField()
    
    class Meta:
        model = IdentityProof
        fields = ['aadhaar_front_url', 'aadhaar_back_url', 'has_images', 'updated_at']
        read_only_fields = fields
    
    def get_aadhaar_front_url(self, obj):
        request = self.context.get('request')
        if obj.aadhaar_front_image:
            if request:
                return request.build_absolute_uri(obj.aadhaar_front_image.url)
            return obj.aadhaar_front_image.url
        return None
    
    def get_aadhaar_back_url(self, obj):
        request = self.context.get('request')
        if obj.aadhaar_back_image:
            if request:
                return request.build_absolute_uri(obj.aadhaar_back_image.url)
            return obj.aadhaar_back_image.url
        return None
    
    def get_has_images(self, obj):
        return bool(obj.aadhaar_front_image and obj.aadhaar_back_image)


class PANDetailsResponseSerializer(serializers.ModelSerializer):
    """Serializer for PAN details with both masked and unmasked values."""
    pan_number_masked = serializers.CharField(source='pan_masked', read_only=True)
    pan_number = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(source='is_pan_complete', read_only=True)
    is_verified = serializers.BooleanField(source='pan_verified', read_only=True)
    submitted_at = serializers.DateTimeField(source='pan_submitted_at', read_only=True)
    
    class Meta:
        model = IdentityProof
        fields = [
            'pan_number', 'pan_number_masked', 'pan_name', 'pan_dob', 
            'pan_father_name', 'is_complete', 'is_verified', 'submitted_at', 
            'updated_at'
        ]
        read_only_fields = fields
    
    def get_pan_number(self, obj):
        """Return unmasked PAN number for verification."""
        return obj.pan_number if obj.pan_number else None


class PANImageResponseSerializer(serializers.ModelSerializer):
    """Serializer for PAN image only."""
    pan_image_url = serializers.SerializerMethodField()
    has_image = serializers.SerializerMethodField()
    
    class Meta:
        model = IdentityProof
        fields = ['pan_image_url', 'has_image', 'updated_at']
        read_only_fields = fields
    
    def get_pan_image_url(self, obj):
        request = self.context.get('request')
        if obj.pan_image:
            if request:
                return request.build_absolute_uri(obj.pan_image.url)
            return obj.pan_image.url
        return None
    
    def get_has_image(self, obj):
        return bool(obj.pan_image)
    
    def get_aadhaar_front_url(self, obj):
        if obj.aadhaar_front_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhaar_front_image.url)
            return obj.aadhaar_front_image.url
        return None
    
    def get_aadhaar_back_url(self, obj):
        if obj.aadhaar_back_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhaar_back_image.url)
            return obj.aadhaar_back_image.url
        return None
    
    def get_pan_image_url(self, obj):
        if obj.pan_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pan_image.url)
            return obj.pan_image.url
        return None


# Admin serializer with unmasked data
class IdentityProofAdminSerializer(serializers.ModelSerializer):
    """Serializer for Identity Proof with full data for admin."""
    aadhaar_number = serializers.SerializerMethodField()
    pan_number = serializers.SerializerMethodField()
    aadhaar_front_url = serializers.SerializerMethodField()
    aadhaar_back_url = serializers.SerializerMethodField()
    pan_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = IdentityProof
        fields = [
            'id', 'aadhaar_number', 'aadhaar_name', 'aadhaar_dob', 'aadhaar_address',
            'aadhaar_front_url', 'aadhaar_back_url', 'aadhaar_verified', 'aadhaar_submitted_at',
            'pan_number', 'pan_name', 'pan_dob', 'pan_father_name',
            'pan_image_url', 'pan_verified', 'pan_submitted_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_aadhaar_number(self, obj):
        return obj.aadhaar_number  # Decrypted
    
    def get_pan_number(self, obj):
        return obj.pan_number  # Decrypted
    
    def get_aadhaar_front_url(self, obj):
        if obj.aadhaar_front_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhaar_front_image.url)
            return obj.aadhaar_front_image.url
        return None
    
    def get_aadhaar_back_url(self, obj):
        if obj.aadhaar_back_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhaar_back_image.url)
            return obj.aadhaar_back_image.url
        return None
    
    def get_pan_image_url(self, obj):
        if obj.pan_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pan_image.url)
            return obj.pan_image.url
        return None


# =============================================================================
# BUSINESS DETAILS SERIALIZERS
# =============================================================================

class BusinessDetailsSerializer(serializers.ModelSerializer):
    """Serializer for Business Details."""
    full_address = serializers.CharField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = BusinessDetails
        fields = [
            'id', 'business_name', 'business_type', 'business_phone', 'business_email',
            'address_line_1', 'address_line_2', 'address_line_3', 'landmark',
            'city', 'district', 'state', 'pincode', 'country',
            'full_address', 'is_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'full_address', 'is_complete', 'created_at', 'updated_at']
    
    def validate_business_phone(self, value):
        if value:
            try:
                phone_validator(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e.message))
        return value
    
    def validate_pincode(self, value):
        if value:
            try:
                pincode_validator(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e.message))
        return value


class BusinessDetailsInputSerializer(serializers.Serializer):
    """Serializer for Business Details input."""
    business_name = serializers.CharField(max_length=200)
    business_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    business_phone = serializers.CharField(max_length=10)
    business_email = serializers.EmailField(required=False, allow_blank=True)
    address_line_1 = serializers.CharField(max_length=255)
    address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line_3 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    landmark = serializers.CharField(max_length=200, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    district = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100)
    pincode = serializers.CharField(max_length=6, min_length=6)
    country = serializers.CharField(max_length=100, default='India')
    
    def validate_business_phone(self, value):
        try:
            phone_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value
    
    def validate_pincode(self, value):
        try:
            pincode_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value


# =============================================================================
# VERIFICATION IMAGES SERIALIZERS
# =============================================================================

class SelfieUploadSerializer(serializers.Serializer):
    """Serializer for selfie upload."""
    selfie_image = serializers.ImageField()
    
    def validate_selfie_image(self, value):
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size must be under 5MB. Current: {value.size / (1024*1024):.2f}MB'
            )
        return value


class OfficePhotosUploadSerializer(serializers.Serializer):
    """Serializer for office photos upload."""
    office_sitting_image = serializers.ImageField()
    office_door_image = serializers.ImageField()
    
    def validate(self, data):
        max_size = 5 * 1024 * 1024  # 5MB
        
        for field in ['office_sitting_image', 'office_door_image']:
            file = data.get(field)
            if file and file.size > max_size:
                raise serializers.ValidationError({
                    field: f'File size must be under 5MB. Current: {file.size / (1024*1024):.2f}MB'
                })
        
        return data


class AddressProofUploadSerializer(serializers.Serializer):
    """Serializer for address proof upload."""
    address_proof_image = serializers.ImageField()
    address_proof_type = serializers.CharField(max_length=50)
    
    def validate_address_proof_image(self, value):
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size must be under 5MB. Current: {value.size / (1024*1024):.2f}MB'
            )
        return value


class VerificationImagesSerializer(serializers.ModelSerializer):
    """Serializer for Verification Images display."""
    is_selfie_complete = serializers.BooleanField(read_only=True)
    is_office_complete = serializers.BooleanField(read_only=True)
    is_address_proof_complete = serializers.BooleanField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    
    # Image URLs
    selfie_url = serializers.SerializerMethodField()
    office_sitting_url = serializers.SerializerMethodField()
    office_door_url = serializers.SerializerMethodField()
    address_proof_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VerificationImages
        fields = [
            'id', 'selfie_url', 'selfie_submitted_at', 'selfie_verified',
            'office_sitting_url', 'office_door_url', 'office_photos_submitted_at', 'office_photos_verified',
            'address_proof_url', 'address_proof_type', 'address_proof_submitted_at', 'address_proof_verified',
            'is_selfie_complete', 'is_office_complete', 'is_address_proof_complete', 'is_complete',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_selfie_url(self, obj):
        if obj.selfie_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.selfie_image.url)
            return obj.selfie_image.url
        return None
    
    def get_office_sitting_url(self, obj):
        if obj.office_sitting_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.office_sitting_image.url)
            return obj.office_sitting_image.url
        return None
    
    def get_office_door_url(self, obj):
        if obj.office_door_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.office_door_image.url)
            return obj.office_door_image.url
        return None
    
    def get_address_proof_url(self, obj):
        if obj.address_proof_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.address_proof_image.url)
            return obj.address_proof_image.url
        return None


# =============================================================================
# BANK DETAILS SERIALIZERS
# =============================================================================

class BankDetailsInputSerializer(serializers.Serializer):
    """Serializer for Bank Details input."""
    account_holder_name = serializers.CharField(max_length=200)
    account_number = serializers.CharField(max_length=18, min_length=9)
    confirm_account_number = serializers.CharField(max_length=18, min_length=9)
    ifsc_code = serializers.CharField(max_length=11, min_length=11)
    account_type = serializers.ChoiceField(choices=AccountType.choices)
    bank_name = serializers.CharField(max_length=200)
    branch_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    branch_address = serializers.CharField(required=False, allow_blank=True)
    bank_document = serializers.ImageField(required=False, allow_null=True)
    
    def validate_account_number(self, value):
        try:
            account_number_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value
    
    def validate_confirm_account_number(self, value):
        try:
            account_number_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value
    
    def validate_ifsc_code(self, value):
        value = value.upper()
        try:
            ifsc_validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
        return value
    
    def validate_bank_document(self, value):
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size must be under 5MB. Current: {value.size / (1024*1024):.2f}MB'
            )
        return value
    
    def validate(self, data):
        if data['account_number'] != data['confirm_account_number']:
            raise serializers.ValidationError({
                'confirm_account_number': 'Account numbers do not match.'
            })
        return data


class BankDetailsSerializer(serializers.ModelSerializer):
    """Serializer for Bank Details display."""
    account_number_masked = serializers.CharField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    bank_document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BankDetails
        fields = [
            'id', 'account_holder_name', 'account_number_masked', 'ifsc_code',
            'account_type', 'bank_name', 'branch_name', 'branch_address',
            'bank_document_url', 'is_verified', 'verified_at',
            'is_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_bank_document_url(self, obj):
        if obj.bank_document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.bank_document.url)
            return obj.bank_document.url
        return None

class BankDetailsResponseSerializer(serializers.ModelSerializer):
    """Serializer for bank details with both masked and unmasked values."""
    account_number_masked = serializers.CharField(read_only=True)
    account_number = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = BankDetails
        fields = [
            'account_holder_name', 'account_number', 'account_number_masked',
            'ifsc_code', 'account_type', 'bank_name', 'branch_name',
            'branch_address', 'is_complete', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_account_number(self, obj):
        """Return unmasked account number for verification."""
        return obj.account_number if obj.account_number else None


class BankDocumentResponseSerializer(serializers.ModelSerializer):
    """Serializer for bank document image only."""
    bank_document_url = serializers.SerializerMethodField()
    has_document = serializers.SerializerMethodField()
    
    class Meta:
        model = BankDetails
        fields = ['bank_document_url', 'has_document', 'updated_at']
        read_only_fields = fields
    
    def get_bank_document_url(self, obj):
        request = self.context.get('request')
        if obj.bank_document:
            if request:
                return request.build_absolute_uri(obj.bank_document.url)
            return obj.bank_document.url
        return None
    
    def get_has_document(self, obj):
        return bool(obj.bank_document)


class BankDetailsAdminSerializer(serializers.ModelSerializer):
    """Serializer for Bank Details with full data for admin."""
    account_number = serializers.SerializerMethodField()
    bank_document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BankDetails
        fields = [
            'id', 'account_holder_name', 'account_number', 'ifsc_code',
            'account_type', 'bank_name', 'branch_name', 'branch_address',
            'bank_document_url', 'is_verified', 'verified_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_account_number(self, obj):
        return obj.account_number  # Decrypted
    
    def get_bank_document_url(self, obj):
        if obj.bank_document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.bank_document.url)
            return obj.bank_document.url
        return None


# =============================================================================
# STEP-WISE GET API SERIALIZERS
# =============================================================================

class AadhaarDetailsResponseSerializer(serializers.ModelSerializer):
    """Serializer for Aadhaar details with both masked and unmasked values."""
    aadhaar_number_masked = serializers.CharField(source='aadhaar_masked', read_only=True)
    aadhaar_number = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(source='is_aadhaar_complete', read_only=True)
    is_verified = serializers.BooleanField(source='aadhaar_verified', read_only=True)
    submitted_at = serializers.DateTimeField(source='aadhaar_submitted_at', read_only=True)
    
    class Meta:
        model = IdentityProof
        fields = [
            'aadhaar_number', 'aadhaar_number_masked', 'aadhaar_name', 
            'aadhaar_dob', 'aadhaar_address', 'is_complete', 'is_verified', 
            'submitted_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_aadhaar_number(self, obj):
        """Return unmasked Aadhaar number for verification."""
        return obj.aadhaar_number if obj.aadhaar_number else None


class AadhaarImagesResponseSerializer(serializers.ModelSerializer):
    """Serializer for Aadhaar images only."""
    aadhaar_front_url = serializers.SerializerMethodField()
    aadhaar_back_url = serializers.SerializerMethodField()
    has_images = serializers.SerializerMethodField()
    
    class Meta:
        model = IdentityProof
        fields = ['aadhaar_front_url', 'aadhaar_back_url', 'has_images', 'updated_at']
        read_only_fields = fields
    
    def get_aadhaar_front_url(self, obj):
        request = self.context.get('request')
        if obj.aadhaar_front_image:
            if request:
                return request.build_absolute_uri(obj.aadhaar_front_image.url)
            return obj.aadhaar_front_image.url
        return None
    
    def get_aadhaar_back_url(self, obj):
        request = self.context.get('request')
        if obj.aadhaar_back_image:
            if request:
                return request.build_absolute_uri(obj.aadhaar_back_image.url)
            return obj.aadhaar_back_image.url
        return None
    
    def get_has_images(self, obj):
        return bool(obj.aadhaar_front_image and obj.aadhaar_back_image)


class PANDetailsResponseSerializer(serializers.ModelSerializer):
    """Serializer for PAN details with both masked and unmasked values."""
    pan_number_masked = serializers.CharField(source='pan_masked', read_only=True)
    pan_number = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(source='is_pan_complete', read_only=True)
    is_verified = serializers.BooleanField(source='pan_verified', read_only=True)
    submitted_at = serializers.DateTimeField(source='pan_submitted_at', read_only=True)
    
    class Meta:
        model = IdentityProof
        fields = [
            'pan_number', 'pan_number_masked', 'pan_name', 'pan_dob', 
            'pan_father_name', 'is_complete', 'is_verified', 'submitted_at', 
            'updated_at'
        ]
        read_only_fields = fields
    
    def get_pan_number(self, obj):
        """Return unmasked PAN number for verification."""
        return obj.pan_number if obj.pan_number else None


class PANImageResponseSerializer(serializers.ModelSerializer):
    """Serializer for PAN image only."""
    pan_image_url = serializers.SerializerMethodField()
    has_image = serializers.SerializerMethodField()
    
    class Meta:
        model = IdentityProof
        fields = ['pan_image_url', 'has_image', 'updated_at']
        read_only_fields = fields
    
    def get_pan_image_url(self, obj):
        request = self.context.get('request')
        if obj.pan_image:
            if request:
                return request.build_absolute_uri(obj.pan_image.url)
            return obj.pan_image.url
        return None
    
    def get_has_image(self, obj):
        return bool(obj.pan_image)


class SelfieImageResponseSerializer(serializers.ModelSerializer):
    """Serializer for selfie image only."""
    selfie_url = serializers.SerializerMethodField()
    has_image = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(source='is_selfie_complete', read_only=True)
    is_verified = serializers.BooleanField(source='selfie_verified', read_only=True)
    
    class Meta:
        model = VerificationImages
        fields = ['selfie_url', 'has_image', 'is_complete', 'is_verified', 'selfie_submitted_at', 'updated_at']
        read_only_fields = fields
    
    def get_selfie_url(self, obj):
        request = self.context.get('request')
        if obj.selfie_image:
            if request:
                return request.build_absolute_uri(obj.selfie_image.url)
            return obj.selfie_image.url
        return None
    
    def get_has_image(self, obj):
        return bool(obj.selfie_image)


class OfficeImagesResponseSerializer(serializers.ModelSerializer):
    """Serializer for office images only."""
    office_sitting_url = serializers.SerializerMethodField()
    office_door_url = serializers.SerializerMethodField()
    has_images = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(source='is_office_complete', read_only=True)
    is_verified = serializers.BooleanField(source='office_photos_verified', read_only=True)
    
    class Meta:
        model = VerificationImages
        fields = ['office_sitting_url', 'office_door_url', 'has_images', 'is_complete', 'is_verified', 'office_photos_submitted_at', 'updated_at']
        read_only_fields = fields
    
    def get_office_sitting_url(self, obj):
        request = self.context.get('request')
        if obj.office_sitting_image:
            if request:
                return request.build_absolute_uri(obj.office_sitting_image.url)
            return obj.office_sitting_image.url
        return None
    
    def get_office_door_url(self, obj):
        request = self.context.get('request')
        if obj.office_door_image:
            if request:
                return request.build_absolute_uri(obj.office_door_image.url)
            return obj.office_door_image.url
        return None
    
    def get_has_images(self, obj):
        return bool(obj.office_sitting_image and obj.office_door_image)


class AddressProofImageResponseSerializer(serializers.ModelSerializer):
    """Serializer for address proof image only."""
    address_proof_url = serializers.SerializerMethodField()
    has_image = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(source='is_address_proof_complete', read_only=True)
    is_verified = serializers.BooleanField(source='address_proof_verified', read_only=True)
    
    class Meta:
        model = VerificationImages
        fields = ['address_proof_url', 'address_proof_type', 'has_image', 'is_complete', 'is_verified', 'address_proof_submitted_at', 'updated_at']
        read_only_fields = fields
    
    def get_address_proof_url(self, obj):
        request = self.context.get('request')
        if obj.address_proof_image:
            if request:
                return request.build_absolute_uri(obj.address_proof_image.url)
            return obj.address_proof_image.url
        return None
    
    def get_has_image(self, obj):
        return bool(obj.address_proof_image)


class BankDetailsResponseSerializer(serializers.ModelSerializer):
    """Serializer for bank details with both masked and unmasked values."""
    account_number_masked = serializers.CharField(read_only=True)
    account_number = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = BankDetails
        fields = [
            'account_holder_name', 'account_number', 'account_number_masked',
            'ifsc_code', 'account_type', 'bank_name', 'branch_name',
            'branch_address', 'is_complete', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_account_number(self, obj):
        """Return unmasked account number for verification."""
        return obj.account_number if obj.account_number else None


class BankDocumentResponseSerializer(serializers.ModelSerializer):
    """Serializer for bank document image only."""
    bank_document_url = serializers.SerializerMethodField()
    has_document = serializers.SerializerMethodField()
    
    class Meta:
        model = BankDetails
        fields = ['bank_document_url', 'has_document', 'updated_at']
        read_only_fields = fields
    
    def get_bank_document_url(self, obj):
        request = self.context.get('request')
        if obj.bank_document:
            if request:
                return request.build_absolute_uri(obj.bank_document.url)
            return obj.bank_document.url
        return None
    
    def get_has_document(self, obj):
        return bool(obj.bank_document)


# =============================================================================
# KYC AUDIT LOG SERIALIZER
# =============================================================================

class KYCAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for KYC Audit Log."""
    performed_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = KYCAuditLog
        fields = [
            'id', 'action', 'performed_by', 'performed_by_email',
            'old_status', 'new_status', 'remarks', 'data_changed',
            'ip_address', 'created_at'
        ]
        read_only_fields = fields
    
    def get_performed_by_email(self, obj):
        if obj.performed_by:
            return obj.performed_by.email
        return None


# =============================================================================
# KYC APPLICATION SERIALIZERS
# =============================================================================

class KYCApplicationStatusSerializer(serializers.ModelSerializer):
    """Serializer for KYC Application status overview."""
    user_email = serializers.SerializerMethodField()
    progress_steps = KYCProgressSerializer(many=True, read_only=True)
    
    class Meta:
        model = KYCApplication
        fields = [
            'id', 'application_id', 'user_email', 'status', 'mega_step',
            'current_step', 'total_steps', 'completion_percentage',
            'is_email_verified', 'is_phone_verified',
            'submitted_at', 'reviewed_at', 'approved_at',
            'rejection_reason', 'review_remarks',
            'progress_steps', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_user_email(self, obj):
        return obj.user.email


class KYCApplicationDetailSerializer(serializers.ModelSerializer):
    """Serializer for KYC Application full details."""
    user_email = serializers.SerializerMethodField()
    identity_proof = IdentityProofSerializer(read_only=True)
    business_details = BusinessDetailsSerializer(read_only=True)
    verification_images = VerificationImagesSerializer(read_only=True)
    bank_details = BankDetailsSerializer(read_only=True)
    progress_steps = KYCProgressSerializer(many=True, read_only=True)
    
    class Meta:
        model = KYCApplication
        fields = [
            'id', 'application_id', 'user_email', 'status', 'mega_step',
            'current_step', 'total_steps', 'completion_percentage',
            'is_email_verified', 'is_phone_verified',
            'email_verified_at', 'phone_verified_at',
            'submitted_at', 'reviewed_at', 'approved_at',
            'rejection_reason', 'review_remarks',
            'identity_proof', 'business_details', 'verification_images', 'bank_details',
            'progress_steps', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_user_email(self, obj):
        return obj.user.email


class KYCApplicationAdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for KYC Application with full data for admin."""
    user_email = serializers.SerializerMethodField()
    user_code = serializers.SerializerMethodField()
    identity_proof = IdentityProofAdminSerializer(read_only=True)
    business_details = BusinessDetailsSerializer(read_only=True)
    verification_images = VerificationImagesSerializer(read_only=True)
    bank_details = BankDetailsAdminSerializer(read_only=True)
    progress_steps = KYCProgressSerializer(many=True, read_only=True)
    audit_logs = KYCAuditLogSerializer(many=True, read_only=True)
    reviewed_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = KYCApplication
        fields = [
            'id', 'application_id', 'user_email', 'user_code', 'status', 'mega_step',
            'current_step', 'total_steps', 'completion_percentage',
            'is_email_verified', 'is_phone_verified',
            'email_verified_at', 'phone_verified_at',
            'submitted_at', 'reviewed_at', 'approved_at',
            'reviewed_by', 'reviewed_by_email',
            'rejection_reason', 'review_remarks',
            'identity_proof', 'business_details', 'verification_images', 'bank_details',
            'progress_steps', 'audit_logs', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_user_email(self, obj):
        return obj.user.email
    
    def get_user_code(self, obj):
        return obj.user.user_code
    
    def get_reviewed_by_email(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.email
        return None


# =============================================================================
# ADMIN ACTION SERIALIZERS
# =============================================================================

class KYCReviewActionSerializer(serializers.Serializer):
    """Serializer for admin review actions."""
    action = serializers.ChoiceField(choices=['approve', 'reject', 'resubmit'])
    remarks = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate(self, data):
        action = data.get('action')
        remarks = data.get('remarks', '')
        
        if action in ['reject', 'resubmit'] and not remarks:
            raise serializers.ValidationError({
                'remarks': f'Remarks are required when action is {action}.'
            })
        
        return data


class KYCAdminListSerializer(serializers.ModelSerializer):
    """Serializer for KYC Applications list in admin panel."""
    user_email = serializers.SerializerMethodField()
    user_code = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = KYCApplication
        fields = [
            'id', 'application_id', 'user_email', 'user_code', 'user_name',
            'status', 'mega_step', 'completion_percentage',
            'submitted_at', 'created_at'
        ]
        read_only_fields = fields
    
    def get_user_email(self, obj):
        return obj.user.email
    
    def get_user_code(self, obj):
        return obj.user.user_code
    
    def get_user_name(self, obj):
        return obj.user.full_name


# =============================================================================
# KYC START SERIALIZER
# =============================================================================

class KYCStartSerializer(serializers.Serializer):
    """Serializer for starting KYC process."""
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Check if user already has KYC application
        if hasattr(user, 'kyc_application'):
            kyc_app = user.kyc_application
            if kyc_app.status == KYCStatus.NOT_STARTED:
                kyc_app.status = KYCStatus.IN_PROGRESS
                kyc_app.save(update_fields=['status', 'updated_at'])
            return kyc_app
        
        # Create new KYC application
        kyc_app = KYCApplication.objects.create(
            user=user,
            status=KYCStatus.IN_PROGRESS
        )
        return kyc_app


# =============================================================================
# KYC SUBMIT SERIALIZER
# =============================================================================

class KYCSubmitSerializer(serializers.Serializer):
    """Serializer for submitting KYC for review."""
    
    def validate(self, data):
        user = self.context['request'].user
        
        if not hasattr(user, 'kyc_application'):
            raise serializers.ValidationError('No KYC application found.')
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            raise serializers.ValidationError(
                f'Cannot submit KYC with status: {kyc_app.status}'
            )
        
        if kyc_app.completion_percentage < 100:
            raise serializers.ValidationError(
                f'All steps must be completed. Current progress: {kyc_app.completion_percentage}%'
            )
        
        return data
    
    def save(self):
        user = self.context['request'].user
        kyc_app = user.kyc_application
        
        old_status = kyc_app.status
        kyc_app.submit()
        
        # Log the action
        request = self.context['request']
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.KYC_SUBMITTED,
            performed_by=user,
            old_status=old_status,
            new_status=KYCStatus.SUBMITTED,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return kyc_app
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
