from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'first_name', 
            'last_name', 
            'email', 
            'mobile', 
            'password', 
            'confirm_password'
        )

    def validate(self, attrs):
        """Validate password confirmation and password strength."""
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        
        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Password fields didn't match."}
            )
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        return attrs

    def create(self, validated_data):
        """Create a new user."""
        # Remove confirm_password before creating user
        validated_data.pop('confirm_password', None)
        
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login with email/mobile and password."""
    
    email_or_mobile = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Authenticate user with email or mobile."""
        email_or_mobile = attrs.get('email_or_mobile')
        password = attrs.get('password')

        if email_or_mobile and password:
            # Try to find user by email first, then by mobile
            user = None
            if '@' in email_or_mobile:
                # It's an email
                try:
                    user = User.objects.get(email=email_or_mobile, is_active=True)
                except User.DoesNotExist:
                    pass
            else:
                # It's a mobile number
                try:
                    user = User.objects.get(mobile=email_or_mobile, is_active=True)
                except User.DoesNotExist:
                    pass

            if user and user.check_password(password):
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )
        else:
            raise serializers.ValidationError(
                'Must include "email_or_mobile" and "password".'
            )


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request."""
    
    email_or_mobile = serializers.CharField()

    def validate_email_or_mobile(self, value):
        """Validate that user exists."""
        user = None
        if '@' in value:
            # It's an email
            try:
                user = User.objects.get(email=value, is_active=True)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this email does not exist.")
        else:
            # It's a mobile number
            try:
                user = User.objects.get(mobile=value, is_active=True)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this mobile number does not exist.")
        
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset with OTP."""
    
    email_or_mobile = serializers.CharField()
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate OTP and password confirmation."""
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')
        
        if new_password != confirm_new_password:
            raise serializers.ValidationError(
                {"confirm_new_password": "Password fields didn't match."}
            )
        
        # Validate password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password (for authenticated users)."""
    
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate old password and new password confirmation."""
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')
        
        if new_password != confirm_new_password:
            raise serializers.ValidationError(
                {"confirm_new_password": "Password fields didn't match."}
            )
        
        # Validate password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return attrs

    def validate_old_password(self, value):
        """Validate that old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile display."""
    
    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name', 
            'email',
            'mobile',
            'is_email_verified',
            'is_mobile_verified',
            'created_at',
            'updated_at'
        )
        read_only_fields = (
            'id',
            'email',
            'is_email_verified',
            'is_mobile_verified', 
            'created_at',
            'updated_at'
        )