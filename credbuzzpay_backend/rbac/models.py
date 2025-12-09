"""
RBAC Models - Role-Based Access Control System

This module contains all the models required for managing:
- User Roles (Developer, Super Admin, Admin, Client, End User)
- Applications (Apps in the system)
- Features (Features within apps)
- Role-App Mappings (Which roles have access to which apps)
- Role-Feature Mappings (Which roles have access to which features)
- User-Role Assignments (Which users have which roles)
"""

from django.db import models
from django.utils import timezone
import uuid


class RoleLevel:
    """Role hierarchy levels - lower number = higher privilege"""
    DEVELOPER = 1
    SUPER_ADMIN = 2
    ADMIN = 3
    CLIENT = 4
    END_USER = 5
    
    CHOICES = [
        (DEVELOPER, 'Developer'),
        (SUPER_ADMIN, 'Super Admin'),
        (ADMIN, 'Admin'),
        (CLIENT, 'Client'),
        (END_USER, 'End User'),
    ]
    
    @classmethod
    def get_name(cls, level):
        """Get role name by level"""
        for choice in cls.CHOICES:
            if choice[0] == level:
                return choice[1]
        return None


class UserRole(models.Model):
    """
    Model for storing user roles.
    
    Roles have a hierarchical level where:
    - Level 1 (Developer) has full system access
    - Level 2 (Super Admin) has full app access but no code access
    - Level 3 (Admin) has limited app access assigned by Super Admin
    - Level 4 (Client) has portal access assigned by Admin
    - Level 5 (End User) has basic access assigned by Client
    """
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for the role (e.g., 'DEVELOPER', 'SUPER_ADMIN')")
    level = models.IntegerField(choices=RoleLevel.CHOICES, default=RoleLevel.END_USER)
    description = models.TextField(blank=True, null=True)
    is_system_role = models.BooleanField(default=False, help_text="System roles cannot be deleted")
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_roles'
    )
    
    class Meta:
        db_table = 'rbac_user_role'
        ordering = ['level', 'name']
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
    
    def __str__(self):
        return f"{self.name} (Level {self.level})"
    
    def can_manage_role(self, other_role):
        """Check if this role can manage another role (based on level)"""
        return self.level < other_role.level
    
    def get_accessible_apps(self):
        """Get all apps accessible by this role"""
        return App.objects.filter(
            role_app_mappings__role=self,
            role_app_mappings__is_active=True,
            is_active=True
        ).distinct()
    
    def get_accessible_features(self):
        """Get all features accessible by this role"""
        return Feature.objects.filter(
            role_feature_mappings__role=self,
            role_feature_mappings__is_active=True,
            is_active=True
        ).distinct()


class App(models.Model):
    """
    Model for storing applications/modules in the system.
    
    Apps represent major functional areas of the system.
    Each app can have multiple features.
    """
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for the app (e.g., 'USER_MGMT', 'REPORTS')")
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True, help_text="Icon class or URL")
    display_order = models.IntegerField(default=0, help_text="Order in which app appears in menus")
    is_active = models.BooleanField(default=True)
    
    # Parent app for nested structure
    parent_app = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_apps'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_apps'
    )
    
    class Meta:
        db_table = 'rbac_app'
        ordering = ['display_order', 'name']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
    
    def __str__(self):
        return self.name
    
    def get_features(self):
        """Get all features of this app"""
        return self.features.filter(is_active=True)
    
    def get_child_apps(self):
        """Get all child apps"""
        return self.child_apps.filter(is_active=True)


class Feature(models.Model):
    """
    Model for storing features within applications.
    
    Features represent specific functionalities within an app.
    Example: "Create User", "View Reports", "Delete Transaction"
    """
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    app = models.ForeignKey(
        App,
        on_delete=models.CASCADE,
        related_name='features'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, help_text="Unique code within the app (e.g., 'CREATE_USER', 'VIEW_REPORT')")
    description = models.TextField(blank=True, null=True)
    feature_type = models.CharField(
        max_length=20,
        choices=[
            ('ACTION', 'Action'),      # e.g., Create, Update, Delete
            ('VIEW', 'View'),          # e.g., View page, Read data
            ('REPORT', 'Report'),      # e.g., Generate report
            ('SETTING', 'Setting'),    # e.g., Configure settings
            ('OTHER', 'Other'),
        ],
        default='ACTION'
    )
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_features'
    )
    
    class Meta:
        db_table = 'rbac_feature'
        ordering = ['app', 'display_order', 'name']
        unique_together = ['app', 'code']
        verbose_name = 'Feature'
        verbose_name_plural = 'Features'
    
    def __str__(self):
        return f"{self.app.name} - {self.name}"


class RoleAppMapping(models.Model):
    """
    Model for mapping roles to applications.
    
    Defines which roles have access to which applications
    and what level of access (CRUD permissions).
    """
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    role = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name='role_app_mappings'
    )
    app = models.ForeignKey(
        App,
        on_delete=models.CASCADE,
        related_name='role_app_mappings'
    )
    
    # CRUD Permissions
    can_view = models.BooleanField(default=True)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_role_app_mappings'
    )
    
    class Meta:
        db_table = 'rbac_role_app_mapping'
        unique_together = ['role', 'app']
        verbose_name = 'Role-App Mapping'
        verbose_name_plural = 'Role-App Mappings'
    
    def __str__(self):
        return f"{self.role.name} -> {self.app.name}"


class RoleFeatureMapping(models.Model):
    """
    Model for mapping roles to features.
    
    Defines which roles have access to which features
    and what level of access (CRUD permissions).
    """
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    role = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name='role_feature_mappings'
    )
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='role_feature_mappings'
    )
    
    # CRUD Permissions
    can_view = models.BooleanField(default=True)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_role_feature_mappings'
    )
    
    class Meta:
        db_table = 'rbac_role_feature_mapping'
        unique_together = ['role', 'feature']
        verbose_name = 'Role-Feature Mapping'
        verbose_name_plural = 'Role-Feature Mappings'
    
    def __str__(self):
        return f"{self.role.name} -> {self.feature.name}"


class UserRoleAssignment(models.Model):
    """
    Model for assigning roles to users.
    
    A user can have multiple roles, but only one primary role.
    Roles can have validity periods (temporary assignments).
    """
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        'users_auth.User',
        on_delete=models.CASCADE,
        related_name='role_assignments'
    )
    role = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    
    is_primary = models.BooleanField(default=False, help_text="Is this the user's primary role?")
    is_active = models.BooleanField(default=True)
    
    # Validity period for temporary role assignments
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True, help_text="Leave empty for permanent assignment")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_user_roles'
    )
    
    class Meta:
        db_table = 'rbac_user_role_assignment'
        ordering = ['-is_primary', 'role__level']
        verbose_name = 'User Role Assignment'
        verbose_name_plural = 'User Role Assignments'
    
    def __str__(self):
        primary_indicator = " (Primary)" if self.is_primary else ""
        return f"{self.user.email} - {self.role.name}{primary_indicator}"
    
    def is_valid(self):
        """Check if the role assignment is currently valid"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if now < self.valid_from:
            return False
        return True
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one primary role per user"""
        if self.is_primary:
            # Set all other roles for this user as non-primary
            UserRoleAssignment.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class RoleHierarchy(models.Model):
    """
    Model for defining custom role hierarchy/delegation.
    
    This allows defining which roles can manage which other roles
    beyond the default level-based hierarchy.
    """
    
    id = models.AutoField(primary_key=True)
    parent_role = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name='child_role_relations'
    )
    child_role = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name='parent_role_relations'
    )
    
    # What the parent role can do to users with child role
    can_assign = models.BooleanField(default=True, help_text="Can assign this role to users")
    can_revoke = models.BooleanField(default=True, help_text="Can revoke this role from users")
    can_modify_permissions = models.BooleanField(default=False, help_text="Can modify permissions of this role")
    
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_role_hierarchies'
    )
    
    class Meta:
        db_table = 'rbac_role_hierarchy'
        unique_together = ['parent_role', 'child_role']
        verbose_name = 'Role Hierarchy'
        verbose_name_plural = 'Role Hierarchies'
    
    def __str__(self):
        return f"{self.parent_role.name} -> {self.child_role.name}"


class AuditLog(models.Model):
    """
    Model for storing RBAC-related audit logs.
    
    Tracks all changes to roles, permissions, and assignments.
    """
    
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('ASSIGN', 'Assign'),
        ('REVOKE', 'Revoke'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ACCESS', 'Access'),
        ('DENY', 'Deny'),
    ]
    
    ENTITY_TYPES = [
        ('USER_ROLE', 'User Role'),
        ('APP', 'Application'),
        ('FEATURE', 'Feature'),
        ('ROLE_APP_MAPPING', 'Role-App Mapping'),
        ('ROLE_FEATURE_MAPPING', 'Role-Feature Mapping'),
        ('USER_ROLE_ASSIGNMENT', 'User Role Assignment'),
        ('ROLE_HIERARCHY', 'Role Hierarchy'),
    ]
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPES)
    entity_id = models.IntegerField()
    entity_uuid = models.UUIDField(null=True, blank=True)
    
    description = models.TextField()
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    # Who performed the action
    performed_by = models.ForeignKey(
        'users_auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rbac_audit_logs'
    )
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rbac_audit_log'
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.action} - {self.entity_type} ({self.entity_id})"
