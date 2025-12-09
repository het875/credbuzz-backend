"""
RBAC Admin - Admin configuration for RBAC models
"""

from django.contrib import admin
from .models import (
    UserRole, App, Feature, RoleAppMapping,
    RoleFeatureMapping, UserRoleAssignment, RoleHierarchy, AuditLog
)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'level', 'is_system_role', 'is_active', 'created_at']
    list_filter = ['level', 'is_system_role', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['level', 'name']
    readonly_fields = ['uuid', 'created_at', 'updated_at']


@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent_app', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent_app']
    search_fields = ['name', 'code', 'description']
    ordering = ['display_order', 'name']
    readonly_fields = ['uuid', 'created_at', 'updated_at']


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'app', 'feature_type', 'is_active', 'created_at']
    list_filter = ['app', 'feature_type', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['app', 'display_order', 'name']
    readonly_fields = ['uuid', 'created_at', 'updated_at']


@admin.register(RoleAppMapping)
class RoleAppMappingAdmin(admin.ModelAdmin):
    list_display = ['role', 'app', 'can_view', 'can_create', 'can_update', 'can_delete', 'is_active']
    list_filter = ['role', 'app', 'is_active', 'can_view', 'can_create', 'can_update', 'can_delete']
    search_fields = ['role__name', 'app__name']
    readonly_fields = ['uuid', 'created_at', 'updated_at']


@admin.register(RoleFeatureMapping)
class RoleFeatureMappingAdmin(admin.ModelAdmin):
    list_display = ['role', 'feature', 'can_view', 'can_create', 'can_update', 'can_delete', 'is_active']
    list_filter = ['role', 'feature__app', 'is_active']
    search_fields = ['role__name', 'feature__name']
    readonly_fields = ['uuid', 'created_at', 'updated_at']


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_primary', 'is_active', 'valid_from', 'valid_until']
    list_filter = ['role', 'is_primary', 'is_active']
    search_fields = ['user__email', 'user__username', 'role__name']
    readonly_fields = ['uuid', 'created_at', 'updated_at']


@admin.register(RoleHierarchy)
class RoleHierarchyAdmin(admin.ModelAdmin):
    list_display = ['parent_role', 'child_role', 'can_assign', 'can_revoke', 'can_modify_permissions', 'is_active']
    list_filter = ['is_active', 'can_assign', 'can_revoke', 'can_modify_permissions']
    search_fields = ['parent_role__name', 'child_role__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'entity_type', 'entity_id', 'performed_by', 'created_at']
    list_filter = ['action', 'entity_type', 'created_at']
    search_fields = ['description', 'performed_by__email']
    readonly_fields = ['uuid', 'created_at', 'action', 'entity_type', 'entity_id', 'entity_uuid',
                       'description', 'old_values', 'new_values', 'performed_by', 'ip_address', 'user_agent']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
