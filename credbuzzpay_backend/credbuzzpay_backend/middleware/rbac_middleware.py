"""
RBAC Middleware for CredBuzz Backend

This middleware enforces Role-Based Access Control (RBAC) on all API endpoints.
It checks:
1. User authentication
2. User role level
3. App access permissions
4. Feature access permissions

Author: CredBuzz Team
Date: January 13, 2026
"""

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rbac.models import UserRoleAssignment, RoleAppMapping, RoleFeatureMapping

logger = logging.getLogger(__name__)


class RBACMiddleware(MiddlewareMixin):
    """
    Middleware to enforce RBAC on all API endpoints.
    
    How it works:
    1. Extracts app_code and feature_code from view attributes
    2. If codes are present, validates user has access
    3. DEVELOPER role bypasses all checks
    4. SUPER_ADMIN has all app access
    5. Other roles checked against RoleAppMapping and RoleFeatureMapping
    """
    
    # Endpoints that bypass RBAC (public endpoints)
    BYPASS_PATHS = [
        '/api/auth-user/register/',
        '/api/auth-user/login/',
        '/api/auth-user/forgot-password/',
        '/api/auth-user/verify-forgot-password-otp/',
        '/api/auth-user/reset-password-with-token/',
        '/api/auth-user/resend-otp/',
        '/api/health/',
        '/api/health/detailed/',
        '/admin/',
        '/swagger/',
        '/redoc/',
    ]
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process view before it's called.
        Check RBAC permissions based on view attributes.
        """
        
        # Skip RBAC for bypass paths
        if any(request.path.startswith(path) for path in self.BYPASS_PATHS):
            return None
        
        # Skip RBAC for non-API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Get the view class/function
        view_class = getattr(view_func, 'cls', None)
        
        if not view_class:
            # Function-based view, skip RBAC
            return None
        
        # Extract app_code and feature_code from view
        app_code = getattr(view_class, 'app_code', None)
        feature_code = getattr(view_class, 'feature_code', None)
        
        # If no app_code, skip RBAC (view doesn't require RBAC)
        if not app_code:
            return None
        
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required.',
                'error': 'AUTHENTICATION_REQUIRED'
            }, status=401)
        
        user = request.user
        
        # DEVELOPER role bypasses all RBAC checks
        user_roles = UserRoleAssignment.objects.filter(
            user=user,
            is_active=True
        ).values_list('role__role_level', flat=True)
        
        if 'DEVELOPER' in user_roles:
            logger.debug(f"RBAC: User {user.email} has DEVELOPER role, bypassing checks")
            return None
        
        # SUPER_ADMIN has access to all apps
        if 'SUPER_ADMIN' in user_roles:
            logger.debug(f"RBAC: User {user.email} has SUPER_ADMIN role")
            # Still need to check feature access if feature_code is present
            if feature_code:
                if not self._has_feature_access(user, feature_code):
                    return JsonResponse({
                        'success': False,
                        'message': f'Access denied. You do not have permission to access this feature.',
                        'error': 'FEATURE_ACCESS_DENIED',
                        'details': {
                            'feature_code': feature_code
                        }
                    }, status=403)
            return None
        
        # Check app access for other roles
        if not self._has_app_access(user, app_code):
            return JsonResponse({
                'success': False,
                'message': f'Access denied. You do not have permission to access this app.',
                'error': 'APP_ACCESS_DENIED',
                'details': {
                    'app_code': app_code
                }
            }, status=403)
        
        # Check feature access if feature_code is present
        if feature_code:
            if not self._has_feature_access(user, feature_code):
                return JsonResponse({
                    'success': False,
                    'message': f'Access denied. You do not have permission to access this feature.',
                    'error': 'FEATURE_ACCESS_DENIED',
                    'details': {
                        'feature_code': feature_code
                    }
                }, status=403)
        
        # All checks passed
        logger.debug(f"RBAC: User {user.email} has access to {app_code}/{feature_code}")
        return None
    
    def _has_app_access(self, user, app_code):
        """
        Check if user has access to the specified app.
        """
        try:
            # Get user's active role assignments
            user_role_ids = UserRoleAssignment.objects.filter(
                user=user,
                is_active=True
            ).values_list('role_id', flat=True)
            
            if not user_role_ids:
                logger.warning(f"RBAC: User {user.email} has no active roles")
                return False
            
            # Check if any of user's roles have access to this app
            has_access = RoleAppMapping.objects.filter(
                role_id__in=user_role_ids,
                app__app_code=app_code,
                app__is_active=True
            ).exists()
            
            return has_access
        except Exception as e:
            logger.error(f"RBAC: Error checking app access: {str(e)}")
            return False
    
    def _has_feature_access(self, user, feature_code):
        """
        Check if user has access to the specified feature.
        """
        try:
            # Get user's active role assignments
            user_role_ids = UserRoleAssignment.objects.filter(
                user=user,
                is_active=True
            ).values_list('role_id', flat=True)
            
            if not user_role_ids:
                logger.warning(f"RBAC: User {user.email} has no active roles")
                return False
            
            # Check if any of user's roles have access to this feature
            has_access = RoleFeatureMapping.objects.filter(
                role_id__in=user_role_ids,
                feature__feature_code=feature_code,
                feature__is_active=True
            ).exists()
            
            return has_access
        except Exception as e:
            logger.error(f"RBAC: Error checking feature access: {str(e)}")
            return False
