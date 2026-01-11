"""
Serializers for users_auth app
"""
from rest_framework import serializers
from .models import User, PasswordResetToken, RoleName
import re
from django.utils import timezone
from django.conf import settings


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    Collects: First Name, Middle Name, Last Name, Email, Mobile Number, Password, Confirm Password
    After registration, OTP verification is required for both email and phone.
    """
    first_name = serializers.CharField(max_length=100, required=True)
    middle_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=True)
    email = serializers.EmailField(max_length=255)
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    
    # Username is auto-generated from email if not provided
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    def validate_email(self, value):
        """
        Validate email uniqueness considering verification status.
        
        If email exists and is verified → Error (user already registered)
        If email exists but NOT verified → Allow (resend OTP scenario)
        If email doesn't exist → Allow (new registration)
        """
        value = value.lower()
        # Check if email exists AND is verified
        existing_user = User.objects.filter(email=value).first()
        if existing_user and existing_user.is_email_verified:
            raise serializers.ValidationError("A user with this email already exists and is verified.")
        return value
    
    def validate_phone_number(self, value):
        """
        Validate phone number considering verification status.
        
        If phone exists and is verified → Error (user already registered)
        If phone exists but NOT verified → Allow (resend OTP scenario)
        If phone doesn't exist → Allow (new registration)
        """
        # Remove any spaces, dashes or parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        
        # Check if phone number is valid (10 digits)
        if not re.match(r'^\d{10}$', cleaned):
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        
        # Check if phone number exists AND is verified
        existing_user = User.objects.filter(phone_number=cleaned).first()
        if existing_user and existing_user.is_phone_verified:
            raise serializers.ValidationError("A user with this phone number already exists and is verified.")
        
        return cleaned
    
    def validate_username(self, value):
        """Validate username is unique and follows pattern"""
        if not value:
            return value  # Will be auto-generated
            
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, and underscores."
            )
        return value
    
    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        
        return value
    
    def validate(self, data):
        """Validate password confirmation and auto-generate username"""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        
        # Auto-generate username from email if not provided
        if not data.get('username'):
            email = data.get('email', '')
            base_username = email.split('@')[0].lower()
            # Clean username to only allow valid characters
            base_username = re.sub(r'[^a-zA-Z0-9_]', '_', base_username)
            
            # Ensure unique username
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            data['username'] = username
        
        return data
    
    def create(self, validated_data):
        """
        Create new user or update unverified existing user.
        
        Handles two scenarios:
        1. Email exists but unverified → Update user details (resend OTP)
        2. Phone exists but unverified → Update user details (resend OTP)
        3. Neither exists → Create new user
        
        Returns:
            User: Created/updated user object (not verified until OTP confirmation)
        """
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        email = validated_data.get('email')
        phone_number = validated_data.get('phone_number')
        
        # Check if unverified user already exists with this email
        existing_user_by_email = User.objects.filter(email=email, is_email_verified=False).first()
        
        # Check if unverified user already exists with this phone
        existing_user_by_phone = User.objects.filter(phone_number=phone_number, is_phone_verified=False).first()
        
        # If both exist and they're the same user, use that user
        # If they're different users, this shouldn't happen if validation worked correctly
        existing_user = existing_user_by_email or existing_user_by_phone
        
        if existing_user:
            # Resend OTP scenario: Update unverified user with new password and details
            existing_user.first_name = validated_data.get('first_name', existing_user.first_name)
            existing_user.middle_name = validated_data.get('middle_name', existing_user.middle_name)
            existing_user.last_name = validated_data.get('last_name', existing_user.last_name)
            existing_user.email = email  # Update email
            existing_user.phone_number = phone_number  # Update phone
            existing_user.username = validated_data.get('username', existing_user.username)
            existing_user.set_password(password)
            existing_user.user_role = 'END_USER'
            existing_user.is_verified = False  # Still needs verification
            existing_user.is_email_verified = False
            existing_user.is_phone_verified = False  # Reset phone verification too
            existing_user.email_otp_attempt_count = 0  # Reset email OTP attempts on resend
            existing_user.save()
            return existing_user
        
        # New registration: Create new user
        user = User(**validated_data)
        user.set_password(password)
        user.is_verified = False  # User needs to verify email via OTP
        user.is_email_verified = False
        user.is_phone_verified = False
        user.user_role = 'END_USER'  # Default role for new registrations
        user.save()
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Supports dynamic login via a single 'identifier' field.
    The identifier can be: email, username, user_code, or phone_number.
    System auto-detects the type.
    """
    identifier = serializers.CharField(
        help_text="Login identifier: email, username, user_code, or phone_number"
    )
    password = serializers.CharField(write_only=True)
    
    def _detect_identifier_type(self, identifier):
        """
        Auto-detect the type of identifier provided.
        Returns: (identifier_type, normalized_identifier)
        """
        identifier = identifier.strip()
        
        # Check if it's an email (contains @)
        if '@' in identifier:
            return 'EMAIL', identifier.lower()
        
        # Check if it's a phone number (starts with + or contains only digits and common phone chars)
        if identifier.startswith('+') or re.match(r'^[\d\s\-\(\)]+$', identifier):
            # Normalize phone number - remove spaces, dashes, parentheses
            normalized = re.sub(r'[\s\-\(\)]', '', identifier)
            if len(normalized) >= 10:  # Valid phone number length
                return 'PHONE', identifier
        
        # Check if it's a user_code (exactly 6 alphanumeric characters, uppercase)
        if re.match(r'^[A-Za-z0-9]{6}$', identifier):
            return 'USER_CODE', identifier.upper()
        
        # Default to username
        return 'USERNAME', identifier
    
    def validate(self, data):
        """Validate login credentials with auto-detection"""
        identifier_input = data.get('identifier')
        password = data.get('password')
        
        if not identifier_input:
            raise serializers.ValidationError({
                'identifier': "Please provide your email, username, user_code, or phone_number."
            })
        
        # Auto-detect identifier type
        identifier_type, identifier = self._detect_identifier_type(identifier_input)
        
        # Store identifier info for lockout tracking in view
        data['identifier'] = identifier
        data['identifier_type'] = identifier_type
        
        # Try to find user by the detected identifier type
        user = None
        try:
            if identifier_type == 'EMAIL':
                user = User.objects.get(email=identifier)
            elif identifier_type == 'USERNAME':
                user = User.objects.get(username=identifier)
            elif identifier_type == 'USER_CODE':
                user = User.objects.get(user_code=identifier)
            elif identifier_type == 'PHONE':
                # Try exact match first, then try normalized
                try:
                    user = User.objects.get(phone_number=identifier)
                except User.DoesNotExist:
                    # Try with just the digits
                    normalized = re.sub(r'[\s\-\(\)]', '', identifier)
                    user = User.objects.get(phone_number__endswith=normalized[-10:])
        except User.DoesNotExist:
            # If not found with detected type, try all types as fallback
            user = self._find_user_fallback(identifier_input)
        
        if not user:
            raise serializers.ValidationError({
                'non_field_errors': ["Invalid credentials."]
            })
        
        if user.is_deleted:
            raise serializers.ValidationError({
                'non_field_errors': ["User account has been deleted."]
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': ["User account is deactivated."]
            })
        
        if not user.check_password(password):
            raise serializers.ValidationError({
                'non_field_errors': ["Invalid credentials."],
                '_auth_failed': True  # Flag for lockout tracking
            })
        
        # Check if user has verified email and phone (for END_USER role)
        # DEVELOPER and SUPER_ADMIN don't need OTP verification
        if user.user_role == 'END_USER':
            # Check if mobile verification is required (can be bypassed via settings)
            require_phone_verification = settings.REQUIRE_MOBILE_VERIFICATION
            
            # Build verification requirements
            verification_needed = []
            if not user.is_email_verified:
                verification_needed.append('email')
            if not user.is_phone_verified and require_phone_verification:
                verification_needed.append('phone')
            
            # Only raise error if there are verification requirements
            if verification_needed:
                raise serializers.ValidationError({
                    'non_field_errors': [f"Please verify your {' and '.join(verification_needed)} before logging in."],
                    '_verification_required': True,
                    '_verification_needed': verification_needed,
                })
        
        data['user'] = user
        return data
    
    def _find_user_fallback(self, identifier):
        """
        Fallback: Try to find user by checking all identifier types.
        This handles edge cases where detection might be wrong.
        """
        identifier_lower = identifier.lower().strip()
        identifier_upper = identifier.upper().strip()
        
        # Try email
        user = User.objects.filter(email=identifier_lower).first()
        if user:
            return user
        
        # Try username
        user = User.objects.filter(username=identifier.strip()).first()
        if user:
            return user
        
        # Try user_code
        user = User.objects.filter(user_code=identifier_upper).first()
        if user:
            return user
        
        # Try phone_number
        user = User.objects.filter(phone_number=identifier.strip()).first()
        if user:
            return user
        
        return None


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Serializer for forgot password request
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists"""
        try:
            user = User.objects.get(email=value.lower(), is_active=True)
            self.user = user
        except User.DoesNotExist:
            # Don't reveal if email exists or not
            pass
        return value.lower()


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for password reset with OTP
    """
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    
    def validate(self, data):
        """Validate OTP and user"""
        from django.utils import timezone
        from datetime import timedelta
        from django.conf import settings
        
        email = data.get('email', '').lower()
        otp_code = data.get('otp_code', '').strip()
        
        # Find user
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'No account found with this email.'
            })
        
        # Check if OTP exists
        if not user.password_reset_otp:
            raise serializers.ValidationError({
                'otp_code': 'No password reset OTP found. Please request a new one.'
            })
        
        # Check OTP expiry (10 minutes)
        otp_expiry_minutes = 10
        if user.password_reset_otp_created_at:
            expiry_time = user.password_reset_otp_created_at + timedelta(minutes=otp_expiry_minutes)
            if timezone.now() > expiry_time:
                raise serializers.ValidationError({
                    'otp_code': 'OTP has expired. Please request a new one.'
                })
        
        # Increment attempt counter
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
        user.password_reset_otp_attempt_count = (user.password_reset_otp_attempt_count or 0) + 1
        
        # Check max attempts
        if user.password_reset_otp_attempt_count > max_attempts:
            user.password_reset_otp = None
            user.password_reset_otp_created_at = None
            user.save(update_fields=['password_reset_otp', 'password_reset_otp_created_at', 'password_reset_otp_attempt_count'])
            raise serializers.ValidationError({
                'otp_code': 'Too many failed attempts. Please request a new OTP.'
            })
        
        # Validate OTP
        if user.password_reset_otp != otp_code:
            user.save(update_fields=['password_reset_otp_attempt_count'])
            raise serializers.ValidationError({
                'otp_code': 'Invalid OTP code. Please try again.'
            })
        
        # Password confirmation check
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        # Store user for later use
        self.user = user
        return data
    
    def validate_new_password(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        
        return value
    


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password (when user is logged in)
    """
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    
    def validate_new_password(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        
        return value
    
    def validate(self, data):
        """Validate password confirmation"""
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return data


class UserSerializer(serializers.Serializer):
    """
    Serializer for user details (read-only)
    """
    id = serializers.IntegerField(read_only=True)
    user_code = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    middle_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    user_role = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_email_verified = serializers.BooleanField(read_only=True)
    is_phone_verified = serializers.BooleanField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class UserUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating user details
    """
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    middle_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    username = serializers.CharField(max_length=150, required=False)
    
    def validate_username(self, value):
        """Validate username is unique (excluding current user)"""
        user = self.context.get('user')
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, and underscores."
            )
        return value
    
    def update(self, instance, validated_data):
        """Update user instance"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserListSerializer(serializers.Serializer):
    """
    Serializer for user list with minimal data
    """
    id = serializers.IntegerField(read_only=True)
    user_code = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    user_role = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for token refresh
    """
    refresh_token = serializers.CharField()


class UserActivityLogSerializer(serializers.Serializer):
    """
    Serializer for user activity logs
    """
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_code = serializers.CharField(source='user.user_code', read_only=True)
    activity_type = serializers.CharField(read_only=True)
    action = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    entity_type = serializers.CharField(read_only=True)
    entity_id = serializers.CharField(read_only=True)
    metadata = serializers.JSONField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    request_method = serializers.CharField(read_only=True)
    request_path = serializers.CharField(read_only=True)
    is_success = serializers.BooleanField(read_only=True)
    error_message = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class UserProfileWithAccessSerializer(serializers.Serializer):
    """
    Serializer for user profile with KYC status and access information.
    """
    # User Info
    id = serializers.IntegerField(read_only=True)
    user_code = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    middle_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    user_role = serializers.CharField(read_only=True)
    
    # Verification status
    is_active = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_email_verified = serializers.BooleanField(read_only=True)
    is_phone_verified = serializers.BooleanField(read_only=True)
    
    # Timestamps
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    
    # These will be added dynamically in the view
    kyc_status = serializers.DictField(read_only=True, required=False)
    app_access = serializers.ListField(read_only=True, required=False)
    feature_access = serializers.ListField(read_only=True, required=False)


class CreatePrivilegedUserSerializer(serializers.Serializer):
    """
    Serializer for creating privileged users (Developer/Super Admin).
    Requires a secret key for authorization.
    """
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=[
        (RoleName.DEVELOPER, 'Developer'),
        (RoleName.SUPER_ADMIN, 'Super Admin')
    ])
    secret_key = serializers.CharField(write_only=True)

    def validate_role(self, value):
        if value not in [RoleName.DEVELOPER, RoleName.SUPER_ADMIN]:
            raise serializers.ValidationError("Only Developer and Super Admin roles can be created via this endpoint.")
        return value

    def validate_password(self, value):
        # Basic complexity check
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain both letters and numbers.")
        return value

    def validate(self, data):
        # 1. Validate Password Confirmation
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        # 2. Check for unique email
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "User with this email already exists."})

        # 3. Check for unique username
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "User with this username already exists."})

        return data

    def create(self, validated_data):
        # Remove auxiliary fields
        validated_data.pop('confirm_password')
        secret_key = validated_data.pop('secret_key')
        
        # Role is already validated and in data
        
        # Create user
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            user_role=validated_data['role'],  # Maps to user_role field in model
            is_active=True,
            is_verified=True, # Auto-verify privileged users
            is_phone_verified=True,  # Maps to is_phone_verified
            is_email_verified=True,  # Maps to is_email_verified
            email_verified_at=timezone.now(),
            phone_verified_at=timezone.now()
        )
        
        # Generate Salt and Hash Password
        salt = User.generate_salt()
        hashed_password = User.hash_password(validated_data['password'], salt)
        
        user.password_salt = salt
        user.password_hash = hashed_password
        
        # Save user (User Code will be auto-generated in save method)
        user.save()
        
        return user
