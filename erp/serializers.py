"""
ERP Serializers
Data serialization for API endpoints
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    UserAccount, Branch, AadhaarKYC, PanKYC, BusinessDetails, 
    BusinessImages, BankDetails, LoginActivity, AuditTrail,
    AppFeature, UserPlatformAccess, AppAccessControl
)
from .utils import (
    validate_password_strength, sanitize_mobile_number, sanitize_email,
    validate_aadhaar_number, validate_pan_number, validate_ifsc_code
)


class BranchSerializer(serializers.ModelSerializer):
    """Serializer for Branch model."""
    
    class Meta:
        model = Branch
        fields = ['id', 'branch_code', 'branch_name', 'address_line1', 'address_line2',
                 'city', 'state', 'country', 'pincode', 'phone', 'email', 
                 'manager_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = UserAccount
        fields = ['first_name', 'last_name', 'email', 'mobile', 'password', 
                 'confirm_password', 'branch']
        extra_kwargs = {
            'branch': {'required': True}
        }
    
    def validate_email(self, value):
        """Validate email format and uniqueness."""
        email = sanitize_email(value)
        if not email:
            raise serializers.ValidationError("Invalid email format")
        
        if UserAccount.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already registered")
        
        return email
    
    def validate_mobile(self, value):
        """Validate mobile number format and uniqueness."""
        mobile = sanitize_mobile_number(value)
        if not mobile:
            raise serializers.ValidationError("Invalid mobile number format")
        
        if UserAccount.objects.filter(mobile=mobile).exists():
            raise serializers.ValidationError("Mobile number already registered")
        
        return mobile
    
    def validate_password(self, value):
        """Validate password strength."""
        is_strong, errors = validate_password_strength(value)
        if not is_strong:
            raise serializers.ValidationError(errors)
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        # Check if branch exists and is active
        branch = attrs.get('branch')
        if branch and not branch.is_active:
            raise serializers.ValidationError("Selected branch is not active")
        
        return attrs
    
    def create(self, validated_data):
        """Create new user account."""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = UserAccount.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserAccountSerializer(serializers.ModelSerializer):
    """Serializer for UserAccount model."""
    
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserAccount
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'mobile',
                 'role', 'role_display', 'branch', 'branch_name', 'is_email_verified',
                 'is_mobile_verified', 'is_kyc_completed', 'is_business_verified',
                 'is_bank_verified', 'is_active', 'login_count', 'created_at']
        read_only_fields = ['id', 'role', 'is_email_verified', 'is_mobile_verified',
                          'is_kyc_completed', 'is_business_verified', 'is_bank_verified',
                          'is_active', 'login_count', 'created_at']


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for OTP request."""
    
    OTP_TYPE_CHOICES = [
        ('email', 'Email'),
        ('mobile', 'Mobile'),
        ('business_email', 'Business Email'),
        ('business_mobile', 'Business Mobile'),
        ('aadhaar', 'Aadhaar'),
    ]
    
    otp_type = serializers.ChoiceField(choices=OTP_TYPE_CHOICES)
    
    def validate_otp_type(self, value):
        """Validate OTP type based on context."""
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        
        if value in ['business_email', 'business_mobile'] and user:
            # Check if user has business details
            if not hasattr(user, 'business_details'):
                raise serializers.ValidationError(
                    "Business details required for business OTP"
                )
        
        return value


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification."""
    
    otp_type = serializers.ChoiceField(choices=OTPRequestSerializer.OTP_TYPE_CHOICES)
    otp = serializers.CharField(min_length=6, max_length=6)
    
    def validate_otp(self, value):
        """Validate OTP format."""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email_or_mobile = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate login credentials."""
        email_or_mobile = attrs.get('email_or_mobile')
        password = attrs.get('password')
        
        if not email_or_mobile or not password:
            raise serializers.ValidationError("Email/mobile and password are required")
        
        # Try to find user by email or mobile
        user = None
        if '@' in email_or_mobile:
            # Email login
            email = sanitize_email(email_or_mobile)
            if email:
                try:
                    user = UserAccount.objects.get(email=email)
                except UserAccount.DoesNotExist:
                    pass
        else:
            # Mobile login
            mobile = sanitize_mobile_number(email_or_mobile)
            if mobile:
                try:
                    user = UserAccount.objects.get(mobile=mobile)
                except UserAccount.DoesNotExist:
                    pass
        
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError(
                "Account is not active. Please verify your email and mobile."
            )
        
        # Check if user is login blocked
        if user.is_login_blocked():
            raise serializers.ValidationError(
                "Account temporarily blocked due to multiple failed attempts"
            )
        
        # Authenticate user
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")
        
        attrs['user'] = user
        return attrs


class AadhaarKYCSerializer(serializers.ModelSerializer):
    """Serializer for Aadhaar KYC."""
    
    aadhaar_number = serializers.CharField(write_only=True, max_length=12)
    masked_aadhaar = serializers.CharField(source='get_masked_aadhaar', read_only=True)
    
    class Meta:
        model = AadhaarKYC
        fields = ['id', 'aadhaar_number', 'masked_aadhaar', 'aadhaar_name', 
                 'aadhaar_front_image', 'aadhaar_back_image', 'is_verified',
                 'verified_at', 'verification_remarks', 'created_at']
        read_only_fields = ['id', 'is_verified', 'verified_at', 'verification_remarks', 'created_at']
    
    def validate_aadhaar_number(self, value):
        """Validate Aadhaar number format."""
        is_valid, error_msg = validate_aadhaar_number(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value
    
    def validate_aadhaar_front_image(self, value):
        """Validate Aadhaar front image."""
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("Image size should not exceed 5MB")
        return value
    
    def validate_aadhaar_back_image(self, value):
        """Validate Aadhaar back image."""
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("Image size should not exceed 5MB")
        return value
    
    def create(self, validated_data):
        """Create Aadhaar KYC record."""
        aadhaar_number = validated_data.pop('aadhaar_number')
        aadhaar_kyc = AadhaarKYC.objects.create(**validated_data)
        aadhaar_kyc.set_aadhaar_number(aadhaar_number)
        aadhaar_kyc.save()
        return aadhaar_kyc


class PanKYCSerializer(serializers.ModelSerializer):
    """Serializer for PAN KYC."""
    
    class Meta:
        model = PanKYC
        fields = ['id', 'pan_number', 'pan_name', 'date_of_birth', 'pan_image',
                 'is_verified', 'verified_at', 'verification_remarks', 'created_at']
        read_only_fields = ['id', 'is_verified', 'verified_at', 'verification_remarks', 'created_at']
    
    def validate_pan_number(self, value):
        """Validate PAN number format."""
        is_valid, error_msg = validate_pan_number(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value.upper()
    
    def validate_pan_image(self, value):
        """Validate PAN image."""
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("Image size should not exceed 5MB")
        return value


class BusinessDetailsSerializer(serializers.ModelSerializer):
    """Serializer for Business Details."""
    
    class Meta:
        model = BusinessDetails
        fields = ['id', 'user_selfie', 'business_name', 'business_address_line1',
                 'business_address_line2', 'city', 'state', 'country', 'pincode',
                 'business_phone', 'business_email', 'is_business_phone_verified',
                 'is_business_email_verified', 'is_verified', 'verified_at',
                 'verification_remarks', 'created_at']
        read_only_fields = ['id', 'is_business_phone_verified', 'is_business_email_verified',
                          'is_verified', 'verified_at', 'verification_remarks', 'created_at']
    
    def validate_business_phone(self, value):
        """Validate business phone number."""
        mobile = sanitize_mobile_number(value)
        if not mobile:
            raise serializers.ValidationError("Invalid mobile number format")
        return mobile
    
    def validate_business_email(self, value):
        """Validate business email."""
        email = sanitize_email(value)
        if not email:
            raise serializers.ValidationError("Invalid email format")
        return email
    
    def validate_user_selfie(self, value):
        """Validate user selfie."""
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("Image size should not exceed 5MB")
        return value


class BusinessImagesSerializer(serializers.ModelSerializer):
    """Serializer for Business Images."""
    
    class Meta:
        model = BusinessImages
        fields = ['id', 'image', 'image_description', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    
    def validate_image(self, value):
        """Validate shop image."""
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("Image size should not exceed 5MB")
        return value


class BankDetailsSerializer(serializers.ModelSerializer):
    """Serializer for Bank Details."""
    
    account_number = serializers.CharField(write_only=True, max_length=20)
    masked_account_number = serializers.CharField(source='get_masked_account_number', read_only=True)
    
    class Meta:
        model = BankDetails
        fields = ['id', 'account_holder_name', 'account_number', 'masked_account_number',
                 'ifsc_code', 'account_type', 'bank_name', 'branch_name',
                 'bank_proof_image', 'is_verified', 'verified_at',
                 'verification_remarks', 'created_at']
        read_only_fields = ['id', 'is_verified', 'verified_at', 'verification_remarks', 'created_at']
    
    def validate_ifsc_code(self, value):
        """Validate IFSC code."""
        is_valid, error_msg = validate_ifsc_code(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value.upper()
    
    def validate_bank_proof_image(self, value):
        """Validate bank proof image."""
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("Image size should not exceed 5MB")
        return value
    
    def create(self, validated_data):
        """Create Bank Details record."""
        account_number = validated_data.pop('account_number')
        bank_details = BankDetails.objects.create(**validated_data)
        bank_details.set_account_number(account_number)
        bank_details.save()
        return bank_details


class LoginActivitySerializer(serializers.ModelSerializer):
    """Serializer for Login Activity."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = LoginActivity
        fields = ['id', 'user', 'user_name', 'email_or_mobile', 'ip_address',
                 'user_agent', 'device_info', 'status', 'failure_reason',
                 'login_timestamp', 'logout_timestamp', 'session_duration']
        read_only_fields = ['id', 'login_timestamp', 'logout_timestamp', 'session_duration']


class AuditTrailSerializer(serializers.ModelSerializer):
    """Serializer for Audit Trail."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AuditTrail
        fields = ['id', 'user', 'user_name', 'action', 'resource_type', 'resource_id',
                 'description', 'old_values', 'new_values', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['id', 'created_at']


class AppFeatureSerializer(serializers.ModelSerializer):
    """Serializer for App Feature."""
    
    class Meta:
        model = AppFeature
        fields = ['id', 'feature_code', 'feature_name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserPlatformAccessSerializer(serializers.ModelSerializer):
    """Serializer for User Platform Access."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    granted_by_name = serializers.CharField(source='granted_by.get_full_name', read_only=True)
    
    class Meta:
        model = UserPlatformAccess
        fields = ['id', 'user', 'user_name', 'platform', 'is_allowed', 
                 'granted_by', 'granted_by_name', 'granted_at', 'revoked_at']
        read_only_fields = ['id', 'granted_at', 'revoked_at']


class AppAccessControlSerializer(serializers.ModelSerializer):
    """Serializer for App Access Control."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    feature_name = serializers.CharField(source='feature.feature_name', read_only=True)
    granted_by_name = serializers.CharField(source='granted_by.get_full_name', read_only=True)
    
    class Meta:
        model = AppAccessControl
        fields = ['id', 'user', 'user_name', 'feature', 'feature_name', 
                 'is_allowed', 'granted_by', 'granted_by_name', 'granted_at']
        read_only_fields = ['id', 'granted_at']