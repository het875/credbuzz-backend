"""
RBAC URLs - URL routing for Role-Based Access Control System
"""

from django.urls import path
from . import views

app_name = 'rbac'

urlpatterns = [
    # User Roles
    path('roles/', views.UserRoleListView.as_view(), name='role-list'),
    path('roles/<int:pk>/', views.UserRoleDetailView.as_view(), name='role-detail'),
    path('roles/initialize/', views.InitializeDefaultRolesView.as_view(), name='role-initialize'),
    
    # Apps
    path('apps/', views.AppListView.as_view(), name='app-list'),
    path('apps/<int:pk>/', views.AppDetailView.as_view(), name='app-detail'),
    
    # Features
    path('features/', views.FeatureListView.as_view(), name='feature-list'),
    path('features/<int:pk>/', views.FeatureDetailView.as_view(), name='feature-detail'),
    
    # Role-App Mappings
    path('role-app-mappings/', views.RoleAppMappingListView.as_view(), name='role-app-mapping-list'),
    path('role-app-mappings/<int:pk>/', views.RoleAppMappingDetailView.as_view(), name='role-app-mapping-detail'),
    path('role-app-mappings/bulk/', views.BulkRoleAppMappingView.as_view(), name='role-app-mapping-bulk'),
    
    # Role-Feature Mappings
    path('role-feature-mappings/', views.RoleFeatureMappingListView.as_view(), name='role-feature-mapping-list'),
    path('role-feature-mappings/<int:pk>/', views.RoleFeatureMappingDetailView.as_view(), name='role-feature-mapping-detail'),
    path('role-feature-mappings/bulk/', views.BulkRoleFeatureMappingView.as_view(), name='role-feature-mapping-bulk'),
    
    # User Role Assignments
    path('user-role-assignments/', views.UserRoleAssignmentListView.as_view(), name='user-role-assignment-list'),
    path('user-role-assignments/<int:pk>/', views.UserRoleAssignmentDetailView.as_view(), name='user-role-assignment-detail'),
    path('user-role-assignments/bulk/', views.BulkUserRoleAssignmentView.as_view(), name='user-role-assignment-bulk'),
    
    # Access Management for SP/Developer (to assign/revoke access to Admin/Client)
    path('users/<int:user_id>/access/', views.UserAccessOverviewView.as_view(), name='user-access-overview'),
    path('users/<int:user_id>/assign-access/', views.AssignAccessToUserView.as_view(), name='assign-access'),
    path('users/<int:user_id>/revoke-access/', views.RevokeAccessFromUserView.as_view(), name='revoke-access'),
    path('all-access-items/', views.AllAppsAndFeaturesView.as_view(), name='all-access-items'),
    
    # Permission Checks
    path('check-permission/', views.CheckPermissionView.as_view(), name='check-permission'),
    path('my-permissions/', views.MyPermissionsView.as_view(), name='my-permissions'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
]
