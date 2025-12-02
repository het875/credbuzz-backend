"""
Serializers for users_auth app
"""
from rest_framework import serializers
from .models import User, PasswordResetToken
import re


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration
    """
    email = serializers.EmailField(max_length=255)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Validate email is unique"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate_username(self, value):
        """Validate username is unique and follows pattern"""
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
        """Validate password confirmation"""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return data
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Validate login credentials"""
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        if not email and not username:
            raise serializers.ValidationError(
                "Either email or username is required."
            )
        
        # Try to find user by email or username
        user = None
        if email:
            try:
                user = User.objects.get(email=email.lower())
            except User.DoesNotExist:
                pass
        
        if not user and username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is deactivated.")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials.")
        
        data['user'] = user
        return data


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
    Serializer for password reset
    """
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    
    def validate_token(self, value):
        """Validate reset token"""
        try:
            reset_token = PasswordResetToken.objects.get(token=value)
            if not reset_token.is_valid():
                raise serializers.ValidationError("Reset token has expired or already used.")
            self.reset_token = reset_token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token.")
        return value
    
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
    last_name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    user_role = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class UserUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating user details
    """
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
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
    created_at = serializers.DateTimeField(read_only=True)


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for token refresh
    """
    refresh_token = serializers.CharField()
