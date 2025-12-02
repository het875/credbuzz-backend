"""
RBAC Serializers - Serializers for Role-Based Access Control System
"""

from rest_framework import serializers
from .models import (
    UserRole, App, Feature, RoleAppMapping, 
    RoleFeatureMapping, UserRoleAssignment, RoleHierarchy, AuditLog, RoleLevel
)


# =============================================================================
# UserRole Serializers
# =============================================================================

class UserRoleListSerializer(serializers.ModelSerializer):
    """Serializer for listing user roles"""
    level_display = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'uuid', 'name', 'code', 'level', 'level_display',
            'description', 'is_system_role', 'is_active', 'users_count',
            'created_at', 'updated_at'
        ]
    
    def get_level_display(self, obj):
        return RoleLevel.get_name(obj.level)
    
    def get_users_count(self, obj):
        return obj.user_assignments.filter(is_active=True).count()


class UserRoleDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed user role view"""
    level_display = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    apps = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'uuid', 'name', 'code', 'level', 'level_display',
            'description', 'is_system_role', 'is_active', 'users_count',
            'apps', 'features', 'created_at', 'updated_at', 'created_by_email'
        ]
    
    def get_level_display(self, obj):
        return RoleLevel.get_name(obj.level)
    
    def get_users_count(self, obj):
        return obj.user_assignments.filter(is_active=True).count()
    
    def get_apps(self, obj):
        mappings = obj.role_app_mappings.filter(is_active=True).select_related('app')
        return [{
            'id': m.app.id,
            'uuid': str(m.app.uuid),
            'name': m.app.name,
            'code': m.app.code,
            'can_view': m.can_view,
            'can_create': m.can_create,
            'can_update': m.can_update,
            'can_delete': m.can_delete,
        } for m in mappings]
    
    def get_features(self, obj):
        mappings = obj.role_feature_mappings.filter(is_active=True).select_related('feature', 'feature__app')
        return [{
            'id': m.feature.id,
            'uuid': str(m.feature.uuid),
            'name': m.feature.name,
            'code': m.feature.code,
            'app_name': m.feature.app.name,
            'can_view': m.can_view,
            'can_create': m.can_create,
            'can_update': m.can_update,
            'can_delete': m.can_delete,
        } for m in mappings]
    
    def get_created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else None


class UserRoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a user role"""
    
    class Meta:
        model = UserRole
        fields = ['name', 'code', 'level', 'description', 'is_system_role', 'is_active']
    
    def validate_code(self, value):
        """Ensure code is uppercase and contains only valid characters"""
        code = value.upper().replace(' ', '_')
        if not code.replace('_', '').isalnum():
            raise serializers.ValidationError("Code can only contain letters, numbers, and underscores")
        return code
    
    def validate_level(self, value):
        """Validate role level based on current user's role"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user:
            user_level = self._get_user_level(request.user)
            if user_level and value <= user_level:
                raise serializers.ValidationError(
                    "You cannot create a role with equal or higher privilege than your own"
                )
        return value
    
    def _get_user_level(self, user):
        """Get the highest privilege level of the user"""
        primary_assignment = user.role_assignments.filter(
            is_primary=True, is_active=True
        ).first()
        if primary_assignment:
            return primary_assignment.role.level
        return None
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a user role"""
    
    class Meta:
        model = UserRole
        fields = ['name', 'description', 'is_active']
    
    def validate(self, data):
        instance = self.instance
        if instance and instance.is_system_role:
            # System roles can only update name and description
            if 'is_active' in data and not data['is_active']:
                raise serializers.ValidationError({
                    'is_active': 'System roles cannot be deactivated'
                })
        return data


# =============================================================================
# App Serializers
# =============================================================================

class AppListSerializer(serializers.ModelSerializer):
    """Serializer for listing apps"""
    features_count = serializers.SerializerMethodField()
    parent_app_name = serializers.SerializerMethodField()
    
    class Meta:
        model = App
        fields = [
            'id', 'uuid', 'name', 'code', 'description', 'icon',
            'display_order', 'is_active', 'parent_app', 'parent_app_name',
            'features_count', 'created_at'
        ]
    
    def get_features_count(self, obj):
        return obj.features.filter(is_active=True).count()
    
    def get_parent_app_name(self, obj):
        return obj.parent_app.name if obj.parent_app else None


class AppDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed app view"""
    features = serializers.SerializerMethodField()
    child_apps = serializers.SerializerMethodField()
    parent_app_name = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()
    roles_with_access = serializers.SerializerMethodField()
    
    class Meta:
        model = App
        fields = [
            'id', 'uuid', 'name', 'code', 'description', 'icon',
            'display_order', 'is_active', 'parent_app', 'parent_app_name',
            'child_apps', 'features', 'roles_with_access',
            'created_at', 'updated_at', 'created_by_email'
        ]
    
    def get_features(self, obj):
        return FeatureListSerializer(obj.features.filter(is_active=True), many=True).data
    
    def get_child_apps(self, obj):
        return AppListSerializer(obj.child_apps.filter(is_active=True), many=True).data
    
    def get_parent_app_name(self, obj):
        return obj.parent_app.name if obj.parent_app else None
    
    def get_created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else None
    
    def get_roles_with_access(self, obj):
        mappings = obj.role_app_mappings.filter(is_active=True).select_related('role')
        return [{
            'role_id': m.role.id,
            'role_name': m.role.name,
            'role_code': m.role.code,
            'can_view': m.can_view,
            'can_create': m.can_create,
            'can_update': m.can_update,
            'can_delete': m.can_delete,
        } for m in mappings]


class AppCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an app"""
    
    class Meta:
        model = App
        fields = ['name', 'code', 'description', 'icon', 'display_order', 'parent_app', 'is_active']
    
    def validate_code(self, value):
        """Ensure code is uppercase and contains only valid characters"""
        code = value.upper().replace(' ', '_')
        if not code.replace('_', '').isalnum():
            raise serializers.ValidationError("Code can only contain letters, numbers, and underscores")
        return code
    
    def validate_parent_app(self, value):
        """Prevent circular references"""
        if value and self.instance and value.id == self.instance.id:
            raise serializers.ValidationError("An app cannot be its own parent")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class AppUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an app"""
    
    class Meta:
        model = App
        fields = ['name', 'description', 'icon', 'display_order', 'parent_app', 'is_active']
    
    def validate_parent_app(self, value):
        """Prevent circular references"""
        if value and self.instance and value.id == self.instance.id:
            raise serializers.ValidationError("An app cannot be its own parent")
        # Check for circular reference
        if value:
            current = value
            while current.parent_app:
                if current.parent_app.id == self.instance.id:
                    raise serializers.ValidationError("This would create a circular reference")
                current = current.parent_app
        return value


# =============================================================================
# Feature Serializers
# =============================================================================

class FeatureListSerializer(serializers.ModelSerializer):
    """Serializer for listing features"""
    app_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Feature
        fields = [
            'id', 'uuid', 'app', 'app_name', 'name', 'code',
            'description', 'feature_type', 'display_order', 'is_active', 'created_at'
        ]
    
    def get_app_name(self, obj):
        return obj.app.name


class FeatureDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed feature view"""
    app_name = serializers.SerializerMethodField()
    app_code = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()
    roles_with_access = serializers.SerializerMethodField()
    
    class Meta:
        model = Feature
        fields = [
            'id', 'uuid', 'app', 'app_name', 'app_code', 'name', 'code',
            'description', 'feature_type', 'display_order', 'is_active',
            'roles_with_access', 'created_at', 'updated_at', 'created_by_email'
        ]
    
    def get_app_name(self, obj):
        return obj.app.name
    
    def get_app_code(self, obj):
        return obj.app.code
    
    def get_created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else None
    
    def get_roles_with_access(self, obj):
        mappings = obj.role_feature_mappings.filter(is_active=True).select_related('role')
        return [{
            'role_id': m.role.id,
            'role_name': m.role.name,
            'role_code': m.role.code,
            'can_view': m.can_view,
            'can_create': m.can_create,
            'can_update': m.can_update,
            'can_delete': m.can_delete,
        } for m in mappings]


class FeatureCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a feature"""
    
    class Meta:
        model = Feature
        fields = ['app', 'name', 'code', 'description', 'feature_type', 'display_order', 'is_active']
    
    def validate_code(self, value):
        """Ensure code is uppercase and contains only valid characters"""
        code = value.upper().replace(' ', '_')
        if not code.replace('_', '').isalnum():
            raise serializers.ValidationError("Code can only contain letters, numbers, and underscores")
        return code
    
    def validate(self, data):
        """Ensure unique code within app"""
        app = data.get('app')
        code = data.get('code')
        if app and code:
            if Feature.objects.filter(app=app, code=code).exists():
                raise serializers.ValidationError({
                    'code': f"A feature with code '{code}' already exists in this app"
                })
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class FeatureUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a feature"""
    
    class Meta:
        model = Feature
        fields = ['name', 'description', 'feature_type', 'display_order', 'is_active']


# =============================================================================
# Role-App Mapping Serializers
# =============================================================================

class RoleAppMappingSerializer(serializers.ModelSerializer):
    """Serializer for role-app mappings"""
    role_name = serializers.SerializerMethodField()
    app_name = serializers.SerializerMethodField()
    assigned_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = RoleAppMapping
        fields = [
            'id', 'uuid', 'role', 'role_name', 'app', 'app_name',
            'can_view', 'can_create', 'can_update', 'can_delete',
            'is_active', 'assigned_by_email', 'created_at', 'updated_at'
        ]
    
    def get_role_name(self, obj):
        return obj.role.name
    
    def get_app_name(self, obj):
        return obj.app.name
    
    def get_assigned_by_email(self, obj):
        return obj.assigned_by.email if obj.assigned_by else None


class RoleAppMappingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating role-app mappings"""
    
    class Meta:
        model = RoleAppMapping
        fields = ['role', 'app', 'can_view', 'can_create', 'can_update', 'can_delete', 'is_active']
    
    def validate(self, data):
        """Check for duplicate mappings"""
        role = data.get('role')
        app = data.get('app')
        if role and app:
            if RoleAppMapping.objects.filter(role=role, app=app).exists():
                raise serializers.ValidationError({
                    'non_field_errors': f"A mapping already exists for role '{role.name}' and app '{app.name}'"
                })
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['assigned_by'] = request.user
        return super().create(validated_data)


class RoleAppMappingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating role-app mappings"""
    
    class Meta:
        model = RoleAppMapping
        fields = ['can_view', 'can_create', 'can_update', 'can_delete', 'is_active']


# =============================================================================
# Role-Feature Mapping Serializers
# =============================================================================

class RoleFeatureMappingSerializer(serializers.ModelSerializer):
    """Serializer for role-feature mappings"""
    role_name = serializers.SerializerMethodField()
    feature_name = serializers.SerializerMethodField()
    app_name = serializers.SerializerMethodField()
    assigned_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = RoleFeatureMapping
        fields = [
            'id', 'uuid', 'role', 'role_name', 'feature', 'feature_name', 'app_name',
            'can_view', 'can_create', 'can_update', 'can_delete',
            'is_active', 'assigned_by_email', 'created_at', 'updated_at'
        ]
    
    def get_role_name(self, obj):
        return obj.role.name
    
    def get_feature_name(self, obj):
        return obj.feature.name
    
    def get_app_name(self, obj):
        return obj.feature.app.name
    
    def get_assigned_by_email(self, obj):
        return obj.assigned_by.email if obj.assigned_by else None


class RoleFeatureMappingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating role-feature mappings"""
    
    class Meta:
        model = RoleFeatureMapping
        fields = ['role', 'feature', 'can_view', 'can_create', 'can_update', 'can_delete', 'is_active']
    
    def validate(self, data):
        """Check for duplicate mappings"""
        role = data.get('role')
        feature = data.get('feature')
        if role and feature:
            if RoleFeatureMapping.objects.filter(role=role, feature=feature).exists():
                raise serializers.ValidationError({
                    'non_field_errors': f"A mapping already exists for role '{role.name}' and feature '{feature.name}'"
                })
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['assigned_by'] = request.user
        return super().create(validated_data)


class RoleFeatureMappingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating role-feature mappings"""
    
    class Meta:
        model = RoleFeatureMapping
        fields = ['can_view', 'can_create', 'can_update', 'can_delete', 'is_active']


# =============================================================================
# User Role Assignment Serializers
# =============================================================================

class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for user role assignments"""
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    role_level = serializers.SerializerMethodField()
    assigned_by_email = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRoleAssignment
        fields = [
            'id', 'uuid', 'user', 'user_email', 'user_name',
            'role', 'role_name', 'role_level',
            'is_primary', 'is_active', 'is_valid',
            'valid_from', 'valid_until',
            'assigned_by_email', 'created_at', 'updated_at'
        ]
    
    def get_user_email(self, obj):
        return obj.user.email
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    
    def get_role_name(self, obj):
        return obj.role.name
    
    def get_role_level(self, obj):
        return obj.role.level
    
    def get_assigned_by_email(self, obj):
        return obj.assigned_by.email if obj.assigned_by else None
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class UserRoleAssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user role assignments"""
    
    class Meta:
        model = UserRoleAssignment
        fields = ['user', 'role', 'is_primary', 'is_active', 'valid_from', 'valid_until']
    
    def validate(self, data):
        """Validate the assignment"""
        user = data.get('user')
        role = data.get('role')
        
        # Check if assignment already exists
        if user and role:
            existing = UserRoleAssignment.objects.filter(user=user, role=role).first()
            if existing:
                raise serializers.ValidationError({
                    'non_field_errors': f"User '{user.email}' already has the role '{role.name}'"
                })
        
        # Validate valid_until is after valid_from
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')
        if valid_from and valid_until and valid_until <= valid_from:
            raise serializers.ValidationError({
                'valid_until': 'Must be after valid_from'
            })
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['assigned_by'] = request.user
        return super().create(validated_data)


class UserRoleAssignmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user role assignments"""
    
    class Meta:
        model = UserRoleAssignment
        fields = ['is_primary', 'is_active', 'valid_from', 'valid_until']
    
    def validate(self, data):
        """Validate the update"""
        valid_from = data.get('valid_from', self.instance.valid_from)
        valid_until = data.get('valid_until', self.instance.valid_until)
        if valid_from and valid_until and valid_until <= valid_from:
            raise serializers.ValidationError({
                'valid_until': 'Must be after valid_from'
            })
        return data


# =============================================================================
# Role Hierarchy Serializers
# =============================================================================

class RoleHierarchySerializer(serializers.ModelSerializer):
    """Serializer for role hierarchy"""
    parent_role_name = serializers.SerializerMethodField()
    child_role_name = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = RoleHierarchy
        fields = [
            'id', 'parent_role', 'parent_role_name', 'child_role', 'child_role_name',
            'can_assign', 'can_revoke', 'can_modify_permissions', 'is_active',
            'created_by_email', 'created_at', 'updated_at'
        ]
    
    def get_parent_role_name(self, obj):
        return obj.parent_role.name
    
    def get_child_role_name(self, obj):
        return obj.child_role.name
    
    def get_created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else None


class RoleHierarchyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating role hierarchy"""
    
    class Meta:
        model = RoleHierarchy
        fields = ['parent_role', 'child_role', 'can_assign', 'can_revoke', 'can_modify_permissions', 'is_active']
    
    def validate(self, data):
        """Validate the hierarchy"""
        parent_role = data.get('parent_role')
        child_role = data.get('child_role')
        
        if parent_role and child_role:
            # Cannot be same role
            if parent_role.id == child_role.id:
                raise serializers.ValidationError({
                    'non_field_errors': 'Parent and child roles cannot be the same'
                })
            
            # Parent must have higher privilege (lower level number)
            if parent_role.level >= child_role.level:
                raise serializers.ValidationError({
                    'non_field_errors': 'Parent role must have higher privilege than child role'
                })
            
            # Check for existing hierarchy
            if RoleHierarchy.objects.filter(parent_role=parent_role, child_role=child_role).exists():
                raise serializers.ValidationError({
                    'non_field_errors': 'This hierarchy relationship already exists'
                })
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


# =============================================================================
# Audit Log Serializers
# =============================================================================

class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    performed_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'uuid', 'action', 'entity_type', 'entity_id', 'entity_uuid',
            'description', 'old_values', 'new_values',
            'performed_by', 'performed_by_email', 'ip_address', 'user_agent',
            'created_at'
        ]
    
    def get_performed_by_email(self, obj):
        return obj.performed_by.email if obj.performed_by else None


# =============================================================================
# Bulk Operation Serializers
# =============================================================================

class BulkRoleAppMappingSerializer(serializers.Serializer):
    """Serializer for bulk assigning apps to a role"""
    role_id = serializers.IntegerField()
    app_ids = serializers.ListField(child=serializers.IntegerField())
    can_view = serializers.BooleanField(default=True)
    can_create = serializers.BooleanField(default=False)
    can_update = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)


class BulkRoleFeatureMappingSerializer(serializers.Serializer):
    """Serializer for bulk assigning features to a role"""
    role_id = serializers.IntegerField()
    feature_ids = serializers.ListField(child=serializers.IntegerField())
    can_view = serializers.BooleanField(default=True)
    can_create = serializers.BooleanField(default=False)
    can_update = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)


class BulkUserRoleAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk assigning roles to users"""
    user_ids = serializers.ListField(child=serializers.IntegerField())
    role_id = serializers.IntegerField()
    is_primary = serializers.BooleanField(default=False)


# =============================================================================
# Permission Check Serializers
# =============================================================================

class PermissionCheckSerializer(serializers.Serializer):
    """Serializer for checking user permissions"""
    user_id = serializers.IntegerField(required=False)
    app_code = serializers.CharField(required=False)
    feature_code = serializers.CharField(required=False)
    permission = serializers.ChoiceField(
        choices=['view', 'create', 'update', 'delete'],
        required=True
    )


class UserPermissionsSerializer(serializers.Serializer):
    """Serializer for getting all permissions of a user"""
    user_id = serializers.IntegerField()
    roles = serializers.ListField(child=serializers.DictField())
    apps = serializers.ListField(child=serializers.DictField())
    features = serializers.ListField(child=serializers.DictField())
