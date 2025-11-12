"""
Custom DRF permissions for role-based access control.
"""
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from accounts.models import UserRoleChoices, AppAccessControl, UserPlatformAccess


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission to check if user is a super admin.
    """
    message = 'Only Super Admin users can perform this action.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'user_role'):
            return False
        return request.user.user_role == UserRoleChoices.SUPER_ADMIN


class IsAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin or super admin.
    """
    message = 'Only Admin users can perform this action.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'user_role'):
            return False
        return request.user.user_role in [UserRoleChoices.ADMIN, UserRoleChoices.SUPER_ADMIN]


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is the owner of the object or an admin.
    """
    message = 'You can only access your own account.'
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access any object
        if hasattr(request.user, 'user_role') and request.user.user_role in [UserRoleChoices.ADMIN, UserRoleChoices.SUPER_ADMIN]:
            return True
        
        # Users can only access their own account
        if hasattr(obj, 'user_code'):
            return obj.user_code == request.user
        
        return False


class HasPlatformAccess(permissions.BasePermission):
    """
    Permission to check if user has access to the requested platform.
    """
    message = 'You do not have access to this platform.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'id'):
            return False
        
        # Get the platform from the request
        platform = request.query_params.get('platform') or view.kwargs.get('platform')
        if not platform:
            return True  # If no platform specified, allow access
        
        # Check if user has platform access
        try:
            platform_access = UserPlatformAccess.objects.get(
                user_code=request.user,
                platform=platform
            )
            return platform_access.is_allowed
        except UserPlatformAccess.DoesNotExist:
            return False


class HasFeatureAccess(permissions.BasePermission):
    """
    Permission to check if user has access to a specific feature.
    """
    message = 'You do not have access to this feature.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'id'):
            return False
        
        # Get the feature from the request
        feature_code = request.query_params.get('feature_code') or view.kwargs.get('feature_code')
        if not feature_code:
            return True  # If no feature specified, allow access
        
        # Check if user has feature access
        try:
            feature_access = AppAccessControl.objects.select_related('feature').get(
                user_code=request.user,
                feature__feature_code=feature_code
            )
            return feature_access.is_allowed
        except AppAccessControl.DoesNotExist:
            return False


class IsActiveUser(permissions.BasePermission):
    """
    Permission to check if user account is active.
    """
    message = 'Your account is not active.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_active'):
            return False
        return request.user.is_active


class IsEmailVerified(permissions.BasePermission):
    """
    Permission to check if user's email is verified.
    """
    message = 'Your email is not verified.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_email_verified'):
            return False
        return request.user.is_email_verified


class IsMobileVerified(permissions.BasePermission):
    """
    Permission to check if user's mobile is verified.
    """
    message = 'Your mobile number is not verified.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_mobile_verified'):
            return False
        return request.user.is_mobile_verified


class IsKYCComplete(permissions.BasePermission):
    """
    Permission to check if user's KYC is complete.
    """
    message = 'Your KYC verification is not complete.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_kyc_complete'):
            return False
        return request.user.is_kyc_complete


class IsNotBlocked(permissions.BasePermission):
    """
    Permission to check if user account is not blocked.
    """
    message = 'Your account has been blocked.'
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_active'):
            return False
        
        # Check if user is blocked
        if hasattr(request.user, 'blocked_until') and request.user.blocked_until:
            from django.utils import timezone
            if request.user.blocked_until > timezone.now():
                return False
        
        return True
