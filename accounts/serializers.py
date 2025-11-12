"""
Django REST Framework serializers for all models.
"""
from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from accounts.models import (
    UserAccount, OTPRecord, Branch, AppFeature, AadhaarKYC, PANKYC,
    BusinessDetails, BankDetails, UserPlatformAccess, AppAccessControl,
    LoginActivity, AuditTrail, RegistrationProgress, SecuritySettings,
    UserRoleChoices
)
from accounts.utils.validators import (
    validate_pan, validate_aadhaar, validate_ifsc, validate_indian_mobile,
    validate_pincode, validate_email_format, validate_password_strength
)
from accounts.utils.encryption import encrypt_data, decrypt_data, mask_aadhaar, mask_account_number
from django.utils import timezone


# ===========================
# Nested Serializers
# ===========================

class BranchMinimalSerializer(serializers.ModelSerializer):
    """Minimal Branch serializer for nested use."""
    class Meta:
        model = Branch
        fields = ['branch_code', 'branch_name', 'city', 'state']
        read_only_fields = ['branch_code']


class AppFeatureMinimalSerializer(serializers.ModelSerializer):
    """Minimal AppFeature serializer for nested use."""
    class Meta:
        model = AppFeature
        fields = ['feature_code', 'feature_name', 'feature_category']
        read_only_fields = ['feature_code']


class UserAccountMinimalSerializer(serializers.ModelSerializer):
    """Minimal UserAccount serializer for nested use."""
    class Meta:
        model = UserAccount
        fields = ['user_code', 'email', 'first_name', 'last_name', 'user_role']
        read_only_fields = ['user_code']


# ===========================
# UserAccount Serializer
# ===========================

class UserAccountSerializer(serializers.ModelSerializer):
    """Complete UserAccount serializer with validation."""
    branch_code = BranchMinimalSerializer(read_only=True)
    branch_code_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = UserAccount
        fields = [
            'user_code', 'email', 'mobile', 'password', 'confirm_password',
            'user_role', 'branch_code', 'branch_code_id', 'first_name',
            'middle_name', 'last_name', 'gender', 'dob', 'is_mobile_verified',
            'is_email_verified', 'is_kyc_complete', 'kyc_verification_step',
            'is_aadhaar_verified', 'is_pan_verified', 'is_bank_verified',
            'is_active', 'is_staff', 'user_blocked', 'blocked_until',
            'address_line1', 'address_line2', 'address_line3', 'city', 'state',
            'country', 'pincode', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user_code', 'is_active', 'user_blocked', 'last_login', 'created_at',
            'updated_at', 'is_kyc_complete', 'kyc_verification_step',
            'is_aadhaar_verified', 'is_pan_verified', 'is_bank_verified'
        ]
    
    def validate_email(self, value):
        validate_email_format(value)
        return value
    
    def validate_mobile(self, value):
        validate_indian_mobile(value)
        return value
    
    def validate_pincode(self, value):
        if value:
            validate_pincode(value)
        return value
    
    def validate_password(self, value):
        if value:
            validate_password_strength(value)
        return value
    
    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError({'password': 'Passwords do not match.'})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        
        user = UserAccount(**validated_data)
        if password:
            user.password = make_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.password = make_password(password)
        
        instance.save()
        return instance


class UserAccountDetailSerializer(UserAccountSerializer):
    """Detailed UserAccount serializer including security and audit info."""
    class Meta(UserAccountSerializer.Meta):
        fields = UserAccountSerializer.Meta.fields + [
            'is_staff', 'is_superuser', 'email_otp_attempts', 'mobile_otp_attempts',
            'register_device_ip', 'password_changed_at', 'deleted_at'
        ]
        read_only_fields = UserAccountSerializer.Meta.read_only_fields + [
            'is_staff', 'is_superuser'
        ]


# ===========================
# OTPRecord Serializer
# ===========================

class OTPRecordSerializer(serializers.ModelSerializer):
    """OTPRecord serializer."""
    user_code = serializers.CharField(write_only=True)
    
    class Meta:
        model = OTPRecord
        fields = [
            'user_code', 'otp_type', 'otp_purpose', 'sent_to_email',
            'sent_to_mobile', 'is_used', 'verified_at', 'sent_at',
            'expires_at', 'attempt_count'
        ]
        read_only_fields = [
            'is_used', 'verified_at', 'sent_at', 'expires_at', 'attempt_count'
        ]


# ===========================
# Branch Serializer
# ===========================

class BranchSerializer(serializers.ModelSerializer):
    """Branch serializer."""
    manager_user_code = UserAccountMinimalSerializer(read_only=True)
    manager_user_code_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    referred_by = BranchMinimalSerializer(read_only=True)
    referred_by_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Branch
        fields = [
            'branch_code', 'branch_name', 'address_line1', 'address_line2',
            'address_line3', 'city', 'state', 'country', 'pincode', 'phone',
            'email', 'manager_name', 'manager_user_code', 'manager_user_code_id',
            'referred_by', 'referred_by_code', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['branch_code', 'created_at', 'updated_at']
    
    def validate_pincode(self, value):
        validate_pincode(value)
        return value


# ===========================
# AppFeature Serializer
# ===========================

class AppFeatureSerializer(serializers.ModelSerializer):
    """AppFeature serializer."""
    parent_feature = AppFeatureMinimalSerializer(read_only=True)
    parent_feature_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = AppFeature
        fields = [
            'feature_code', 'feature_name', 'feature_description',
            'parent_feature', 'parent_feature_code', 'feature_category',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['feature_code', 'created_at', 'updated_at']


# ===========================
# KYC Serializers
# ===========================

class AadhaarKYCSerializer(serializers.ModelSerializer):
    """AadhaarKYC serializer with encryption."""
    user_code = serializers.CharField(read_only=True)
    aadhaar_number = serializers.CharField(write_only=True, required=False)
    aadhaar_number_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AadhaarKYC
        fields = [
            'id', 'user_code', 'aadhaar_number', 'aadhaar_number_display',
            'aadhaar_name', 'aadhaar_dob', 'aadhaar_gender', 'aadhaar_address',
            'aadhaar_front_image', 'aadhaar_back_image', 'aadhaar_xml_file',
            'verification_method', 'is_verified', 'verified_at', 'verified_by',
            'verification_remarks', 'created_at', 'updated_at', 'submitted_at'
        ]
        read_only_fields = [
            'id', 'user_code', 'is_verified', 'verified_at', 'verified_by',
            'created_at', 'updated_at', 'submitted_at'
        ]
    
    def validate_aadhaar_number(self, value):
        if value:
            validate_aadhaar(value)
        return value
    
    def get_aadhaar_number_display(self, obj):
        """Return masked Aadhaar for display."""
        if obj.aadhaar_number_encrypted:
            return mask_aadhaar(obj.aadhaar_number_encrypted)
        return None
    
    def create(self, validated_data):
        aadhaar_number = validated_data.pop('aadhaar_number', None)
        if aadhaar_number:
            validated_data['aadhaar_number_encrypted'] = encrypt_data(aadhaar_number)
        return super().create(validated_data)


class PANKYCSerializer(serializers.ModelSerializer):
    """PANKYC serializer."""
    user_code = serializers.CharField(read_only=True)
    
    class Meta:
        model = PANKYC
        fields = [
            'id', 'user_code', 'pan_number', 'pan_name', 'pan_father_name',
            'pan_dob', 'pan_image', 'verification_method', 'is_verified',
            'verified_at', 'verified_by', 'verification_remarks',
            'name_match_score', 'created_at', 'updated_at', 'submitted_at'
        ]
        read_only_fields = [
            'id', 'user_code', 'is_verified', 'verified_at', 'verified_by',
            'name_match_score', 'created_at', 'updated_at', 'submitted_at'
        ]
    
    def validate_pan_number(self, value):
        validate_pan(value)
        return value


class BusinessDetailsSerializer(serializers.ModelSerializer):
    """BusinessDetails serializer."""
    user_code = serializers.CharField(read_only=True)
    
    class Meta:
        model = BusinessDetails
        fields = [
            'id', 'user_code', 'user_selfie', 'selfie_verified', 'business_name',
            'business_type', 'business_registration_number', 'business_address_line1',
            'business_address_line2', 'business_address_line3', 'city', 'state',
            'country', 'pincode', 'business_phone', 'is_business_phone_verified',
            'business_email', 'is_business_email_verified', 'business_proof_image',
            'is_verified', 'verified_at', 'verified_by', 'verification_remarks',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_code', 'selfie_verified', 'is_business_phone_verified',
            'is_business_email_verified', 'is_verified', 'verified_at',
            'verified_by', 'created_at', 'updated_at'
        ]
    
    def validate_business_phone(self, value):
        validate_indian_mobile(value)
        return value
    
    def validate_pincode(self, value):
        validate_pincode(value)
        return value


class BankDetailsSerializer(serializers.ModelSerializer):
    """BankDetails serializer with encryption."""
    user_code = serializers.CharField(read_only=True)
    account_number = serializers.CharField(write_only=True, required=False)
    account_number_display = serializers.SerializerMethodField()
    
    class Meta:
        model = BankDetails
        fields = [
            'id', 'user_code', 'account_holder_name', 'account_number',
            'account_number_display', 'account_number_last4', 'ifsc_code',
            'account_type', 'bank_name', 'branch_name', 'branch_address',
            'bank_proof_image', 'verification_method', 'penny_drop_amount',
            'is_verified', 'verified_at', 'verified_by', 'verification_remarks',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_code', 'account_number_last4', 'is_verified',
            'verified_at', 'verified_by', 'created_at', 'updated_at'
        ]
    
    def validate_ifsc_code(self, value):
        validate_ifsc(value)
        return value
    
    def get_account_number_display(self, obj):
        """Return masked account number for display."""
        if obj.account_number_encrypted:
            return mask_account_number(obj.account_number_encrypted)
        return None
    
    def create(self, validated_data):
        account_number = validated_data.pop('account_number', None)
        if account_number:
            validated_data['account_number_encrypted'] = encrypt_data(account_number)
            validated_data['account_number_last4'] = account_number[-4:]
        return super().create(validated_data)


# ===========================
# Access Control Serializers
# ===========================

class UserPlatformAccessSerializer(serializers.ModelSerializer):
    """UserPlatformAccess serializer."""
    user_code = UserAccountMinimalSerializer(read_only=True)
    
    class Meta:
        model = UserPlatformAccess
        fields = [
            'id', 'user_code', 'platform', 'is_allowed', 'access_level',
            'allowed_ip_ranges', 'granted_by', 'granted_at', 'revoked_at',
            'revocation_reason'
        ]
        read_only_fields = ['id', 'granted_at', 'revoked_at']


class AppAccessControlSerializer(serializers.ModelSerializer):
    """AppAccessControl serializer."""
    user_code = UserAccountMinimalSerializer(read_only=True)
    feature = AppFeatureMinimalSerializer(read_only=True)
    
    class Meta:
        model = AppAccessControl
        fields = [
            'id', 'user_code', 'feature', 'is_allowed', 'access_level',
            'granted_by', 'granted_at', 'expires_at', 'revoked_at',
            'revoked_by'
        ]
        read_only_fields = ['id', 'granted_at', 'revoked_at']


# ===========================
# LoginActivity Serializer
# ===========================

class LoginActivitySerializer(serializers.ModelSerializer):
    """LoginActivity serializer."""
    user_code = UserAccountMinimalSerializer(read_only=True)
    
    class Meta:
        model = LoginActivity
        fields = [
            'id', 'user_code', 'login_identifier', 'ip_address', 'device_info',
            'location_info', 'status', 'failure_reason', 'login_timestamp',
            'logout_timestamp', 'session_duration', 'is_suspicious', 'risk_score'
        ]
        read_only_fields = [
            'id', 'login_timestamp', 'logout_timestamp', 'session_duration',
            'is_suspicious', 'risk_score'
        ]


# ===========================
# AuditTrail Serializer
# ===========================

class AuditTrailSerializer(serializers.ModelSerializer):
    """AuditTrail serializer."""
    user_code = UserAccountMinimalSerializer(read_only=True)
    
    class Meta:
        model = AuditTrail
        fields = [
            'id', 'user_code', 'action', 'resource_type', 'resource_id',
            'resource_identifier', 'description', 'old_values', 'new_values',
            'changed_fields', 'ip_address', 'user_agent', 'request_method',
            'request_path', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at'
        ]


# ===========================
# RegistrationProgress Serializer
# ===========================

class RegistrationProgressSerializer(serializers.ModelSerializer):
    """RegistrationProgress serializer."""
    user_code = UserAccountMinimalSerializer(read_only=True)
    
    class Meta:
        model = RegistrationProgress
        fields = [
            'id', 'user_code', 'current_step', 'steps_completed', 'step_data',
            'last_completed_step', 'abandoned', 'abandoned_at', 'started_at',
            'completed_at', 'last_active_at'
        ]
        read_only_fields = [
            'id', 'abandoned_at', 'completed_at', 'last_active_at'
        ]


# ===========================
# SecuritySettings Serializer
# ===========================

class SecuritySettingsSerializer(serializers.ModelSerializer):
    """SecuritySettings serializer."""
    user_code = UserAccountMinimalSerializer(read_only=True)
    
    class Meta:
        model = SecuritySettings
        fields = [
            'id', 'user_code', 'two_factor_enabled', 'two_factor_method',
            'login_notification_enabled', 'suspicious_activity_alert',
            'allowed_ip_whitelist', 'password_expiry_days', 'last_password_change',
            'failed_login_attempts', 'account_locked_until', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'failed_login_attempts', 'account_locked_until',
            'created_at', 'updated_at'
        ]
