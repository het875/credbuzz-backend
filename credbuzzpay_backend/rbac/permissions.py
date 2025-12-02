"""
RBAC Permissions - Custom permission classes for role-based access control
"""

from rest_framework.permissions import BasePermission
from django.utils import timezone
from .models import UserRole, UserRoleAssignment, RoleAppMapping, RoleFeatureMapping, RoleLevel


class IsAuthenticated(BasePermission):
    """Check if user is authenticated"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsDeveloper(BasePermission):
    """Check if user has Developer role"""
    message = "Only developers can perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_role_level(request.user, RoleLevel.DEVELOPER)


class IsSuperAdmin(BasePermission):
    """Check if user has Super Admin or higher role"""
    message = "Only super admins or higher can perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_role_level(request.user, RoleLevel.SUPER_ADMIN)


class IsAdmin(BasePermission):
    """Check if user has Admin or higher role"""
    message = "Only admins or higher can perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_role_level(request.user, RoleLevel.ADMIN)


class IsClient(BasePermission):
    """Check if user has Client or higher role"""
    message = "Only clients or higher can perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_role_level(request.user, RoleLevel.CLIENT)


class HasAppAccess(BasePermission):
    """Check if user has access to a specific app"""
    message = "You do not have access to this application."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get app code from view or request
        app_code = getattr(view, 'app_code', None) or request.query_params.get('app_code')
        if not app_code:
            return True  # No specific app required
        
        # Get required permission based on request method
        permission = self._get_permission_for_method(request.method)
        
        return has_app_permission(request.user, app_code, permission)
    
    def _get_permission_for_method(self, method):
        """Map HTTP method to permission type"""
        method_permissions = {
            'GET': 'view',
            'HEAD': 'view',
            'OPTIONS': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        return method_permissions.get(method, 'view')


class HasFeatureAccess(BasePermission):
    """Check if user has access to a specific feature"""
    message = "You do not have access to this feature."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get feature code from view or request
        feature_code = getattr(view, 'feature_code', None) or request.query_params.get('feature_code')
        app_code = getattr(view, 'app_code', None) or request.query_params.get('app_code')
        
        if not feature_code:
            return True  # No specific feature required
        
        # Get required permission based on request method
        permission = self._get_permission_for_method(request.method)
        
        return has_feature_permission(request.user, app_code, feature_code, permission)
    
    def _get_permission_for_method(self, method):
        """Map HTTP method to permission type"""
        method_permissions = {
            'GET': 'view',
            'HEAD': 'view',
            'OPTIONS': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        return method_permissions.get(method, 'view')


class CanManageRole(BasePermission):
    """Check if user can manage a specific role"""
    message = "You cannot manage this role."
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get user's highest privilege level
        user_level = get_user_level(request.user)
        if user_level is None:
            return False
        
        # Developer has full access
        if user_level == RoleLevel.DEVELOPER:
            return True
        
        # Can only manage roles with lower privilege (higher level number)
        if isinstance(obj, UserRole):
            return user_level < obj.level
        
        return False


class CanAssignRole(BasePermission):
    """Check if user can assign a specific role to users"""
    message = "You cannot assign this role."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get role_id from request data
        role_id = request.data.get('role')
        if not role_id:
            return True  # No specific role to check
        
        try:
            role = UserRole.objects.get(id=role_id)
        except UserRole.DoesNotExist:
            return False
        
        return can_assign_role(request.user, role)


# =============================================================================
# Helper Functions
# =============================================================================

def get_user_roles(user):
    """Get all active roles for a user"""
    from django.db import models as django_models
    now = timezone.now()
    assignments = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True,
        valid_from__lte=now
    ).filter(
        django_models.Q(valid_until__isnull=True) | django_models.Q(valid_until__gte=now)
    ).select_related('role')
    
    return [a.role for a in assignments if a.is_valid()]


def get_user_level(user):
    """Get the highest privilege level (lowest number) of a user"""
    from django.db import models as django_models
    now = timezone.now()
    
    assignment = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True,
        role__is_active=True,
        valid_from__lte=now
    ).filter(
        django_models.Q(valid_until__isnull=True) | django_models.Q(valid_until__gte=now)
    ).select_related('role').order_by('role__level').first()
    
    return assignment.role.level if assignment else None


def has_role_level(user, required_level):
    """Check if user has a role with required level or higher (lower number)"""
    user_level = get_user_level(user)
    if user_level is None:
        return False
    return user_level <= required_level


def has_any_role(user, role_codes):
    """Check if user has any of the specified roles"""
    from django.db import models as django_models
    now = timezone.now()
    
    return UserRoleAssignment.objects.filter(
        user=user,
        is_active=True,
        role__is_active=True,
        role__code__in=role_codes,
        valid_from__lte=now
    ).filter(
        django_models.Q(valid_until__isnull=True) | django_models.Q(valid_until__gte=now)
    ).exists()


def has_app_permission(user, app_code, permission='view'):
    """Check if user has specific permission for an app"""
    from django.db import models as django_models
    now = timezone.now()
    
    # Get user's active roles
    role_ids = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True,
        role__is_active=True,
        valid_from__lte=now
    ).filter(
        django_models.Q(valid_until__isnull=True) | django_models.Q(valid_until__gte=now)
    ).values_list('role_id', flat=True)
    
    if not role_ids:
        return False
    
    # Check if user is developer (full access)
    if UserRole.objects.filter(id__in=role_ids, level=RoleLevel.DEVELOPER).exists():
        return True
    
    # Check app permissions
    permission_field = f'can_{permission}'
    return RoleAppMapping.objects.filter(
        role_id__in=role_ids,
        app__code=app_code,
        app__is_active=True,
        is_active=True,
        **{permission_field: True}
    ).exists()


def has_feature_permission(user, app_code, feature_code, permission='view'):
    """Check if user has specific permission for a feature"""
    from django.db import models as django_models
    now = timezone.now()
    
    # Get user's active roles
    role_ids = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True,
        role__is_active=True,
        valid_from__lte=now
    ).filter(
        django_models.Q(valid_until__isnull=True) | django_models.Q(valid_until__gte=now)
    ).values_list('role_id', flat=True)
    
    if not role_ids:
        return False
    
    # Check if user is developer (full access)
    if UserRole.objects.filter(id__in=role_ids, level=RoleLevel.DEVELOPER).exists():
        return True
    
    # Build feature filter
    feature_filter = {'feature__code': feature_code, 'feature__is_active': True}
    if app_code:
        feature_filter['feature__app__code'] = app_code
    
    # Check feature permissions
    permission_field = f'can_{permission}'
    return RoleFeatureMapping.objects.filter(
        role_id__in=role_ids,
        is_active=True,
        **feature_filter,
        **{permission_field: True}
    ).exists()


def can_assign_role(assigner, role_to_assign):
    """Check if a user can assign a specific role"""
    assigner_level = get_user_level(assigner)
    if assigner_level is None:
        return False
    
    # Developer can assign any role
    if assigner_level == RoleLevel.DEVELOPER:
        return True
    
    # Can only assign roles with lower privilege (higher level number)
    return assigner_level < role_to_assign.level


def get_user_permissions(user):
    """Get all permissions for a user"""
    from django.db import models as django_models
    now = timezone.now()
    
    # Get user's active roles
    assignments = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True,
        role__is_active=True,
        valid_from__lte=now
    ).filter(
        django_models.Q(valid_until__isnull=True) | django_models.Q(valid_until__gte=now)
    ).select_related('role')
    
    roles = []
    for a in assignments:
        if a.is_valid():
            roles.append({
                'id': a.role.id,
                'name': a.role.name,
                'code': a.role.code,
                'level': a.role.level,
                'is_primary': a.is_primary
            })
    
    role_ids = [r['id'] for r in roles]
    
    # Check if developer (full access)
    is_developer = any(r['level'] == RoleLevel.DEVELOPER for r in roles)
    
    # Get app permissions
    apps = []
    if is_developer:
        from .models import App
        for app in App.objects.filter(is_active=True):
            apps.append({
                'id': app.id,
                'name': app.name,
                'code': app.code,
                'can_view': True,
                'can_create': True,
                'can_update': True,
                'can_delete': True
            })
    else:
        app_mappings = RoleAppMapping.objects.filter(
            role_id__in=role_ids,
            app__is_active=True,
            is_active=True
        ).select_related('app')
        
        # Aggregate permissions (most permissive wins)
        app_perms = {}
        for m in app_mappings:
            if m.app.code not in app_perms:
                app_perms[m.app.code] = {
                    'id': m.app.id,
                    'name': m.app.name,
                    'code': m.app.code,
                    'can_view': False,
                    'can_create': False,
                    'can_update': False,
                    'can_delete': False
                }
            app_perms[m.app.code]['can_view'] |= m.can_view
            app_perms[m.app.code]['can_create'] |= m.can_create
            app_perms[m.app.code]['can_update'] |= m.can_update
            app_perms[m.app.code]['can_delete'] |= m.can_delete
        
        apps = list(app_perms.values())
    
    # Get feature permissions
    features = []
    if is_developer:
        from .models import Feature
        for feature in Feature.objects.filter(is_active=True).select_related('app'):
            features.append({
                'id': feature.id,
                'name': feature.name,
                'code': feature.code,
                'app_code': feature.app.code,
                'can_view': True,
                'can_create': True,
                'can_update': True,
                'can_delete': True
            })
    else:
        feature_mappings = RoleFeatureMapping.objects.filter(
            role_id__in=role_ids,
            feature__is_active=True,
            is_active=True
        ).select_related('feature', 'feature__app')
        
        # Aggregate permissions (most permissive wins)
        feature_perms = {}
        for m in feature_mappings:
            key = f"{m.feature.app.code}.{m.feature.code}"
            if key not in feature_perms:
                feature_perms[key] = {
                    'id': m.feature.id,
                    'name': m.feature.name,
                    'code': m.feature.code,
                    'app_code': m.feature.app.code,
                    'can_view': False,
                    'can_create': False,
                    'can_update': False,
                    'can_delete': False
                }
            feature_perms[key]['can_view'] |= m.can_view
            feature_perms[key]['can_create'] |= m.can_create
            feature_perms[key]['can_update'] |= m.can_update
            feature_perms[key]['can_delete'] |= m.can_delete
        
        features = list(feature_perms.values())
    
    return {
        'user_id': user.id,
        'roles': roles,
        'apps': apps,
        'features': features,
        'is_developer': is_developer
    }
