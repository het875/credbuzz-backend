"""
RBAC Views - API views for Role-Based Access Control System
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import (
    UserRole, App, Feature, RoleAppMapping, 
    RoleFeatureMapping, UserRoleAssignment, RoleHierarchy, AuditLog, RoleLevel
)
from .serializers import (
    UserRoleListSerializer, UserRoleDetailSerializer,
    UserRoleCreateSerializer, UserRoleUpdateSerializer,
    AppListSerializer, AppDetailSerializer,
    AppCreateSerializer, AppUpdateSerializer,
    FeatureListSerializer, FeatureDetailSerializer,
    FeatureCreateSerializer, FeatureUpdateSerializer,
    RoleAppMappingSerializer, RoleAppMappingCreateSerializer, RoleAppMappingUpdateSerializer,
    RoleFeatureMappingSerializer, RoleFeatureMappingCreateSerializer, RoleFeatureMappingUpdateSerializer,
    UserRoleAssignmentSerializer, UserRoleAssignmentCreateSerializer, UserRoleAssignmentUpdateSerializer,
    RoleHierarchySerializer, RoleHierarchyCreateSerializer,
    AuditLogSerializer,
    BulkRoleAppMappingSerializer, BulkRoleFeatureMappingSerializer, BulkUserRoleAssignmentSerializer
)
from .permissions import (
    IsDeveloper, IsSuperAdmin, IsAdmin,
    has_role_level, get_user_permissions, get_user_level
)
from users_auth.authentication import JWTAuthentication


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    """Standard success response"""
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status_code)


def error_response(message="Error", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """Standard error response"""
    return Response({
        'success': False,
        'message': message,
        'errors': errors
    }, status=status_code)


def log_audit(action, entity_type, entity_id, entity_uuid, description, user, request=None, old_values=None, new_values=None):
    """Create an audit log entry"""
    AuditLog.objects.create(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_uuid=entity_uuid,
        description=description,
        performed_by=user,
        old_values=old_values,
        new_values=new_values,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None
    )


# =============================================================================
# UserRole Views
# =============================================================================

class UserRoleListView(APIView):
    """List all user roles or create a new role"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all user roles"""
        roles = UserRole.objects.filter(is_active=True)
        
        # Filter by level if specified
        level = request.query_params.get('level')
        if level:
            roles = roles.filter(level=level)
        
        serializer = UserRoleListSerializer(roles, many=True)
        return success_response(serializer.data)
    
    def post(self, request):
        """Create a new user role"""
        # Check if user has permission to create roles
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to create roles",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserRoleCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            role = serializer.save()
            log_audit(
                'CREATE', 'USER_ROLE', role.id, role.uuid,
                f"Created role: {role.name}",
                request.user, request,
                new_values=serializer.data
            )
            return success_response(
                UserRoleDetailSerializer(role).data,
                "Role created successfully",
                status.HTTP_201_CREATED
            )
        return error_response("Validation failed", serializer.errors)


class UserRoleDetailView(APIView):
    """Get, update, or delete a specific user role"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get a specific role"""
        role = get_object_or_404(UserRole, pk=pk)
        serializer = UserRoleDetailSerializer(role)
        return success_response(serializer.data)
    
    def put(self, request, pk):
        """Update a role"""
        role = get_object_or_404(UserRole, pk=pk)
        
        # Check permission
        user_level = get_user_level(request.user)
        if user_level is None or user_level >= role.level:
            return error_response(
                "You don't have permission to update this role",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        old_values = UserRoleDetailSerializer(role).data
        serializer = UserRoleUpdateSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            role = serializer.save()
            log_audit(
                'UPDATE', 'USER_ROLE', role.id, role.uuid,
                f"Updated role: {role.name}",
                request.user, request,
                old_values=old_values,
                new_values=UserRoleDetailSerializer(role).data
            )
            return success_response(
                UserRoleDetailSerializer(role).data,
                "Role updated successfully"
            )
        return error_response("Validation failed", serializer.errors)
    
    def delete(self, request, pk):
        """Delete (deactivate) a role"""
        role = get_object_or_404(UserRole, pk=pk)
        
        # Check if system role
        if role.is_system_role:
            return error_response(
                "System roles cannot be deleted",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check permission
        user_level = get_user_level(request.user)
        if user_level is None or user_level >= role.level:
            return error_response(
                "You don't have permission to delete this role",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        role.is_active = False
        role.save()
        
        log_audit(
            'DELETE', 'USER_ROLE', role.id, role.uuid,
            f"Deleted role: {role.name}",
            request.user, request
        )
        
        return success_response(message="Role deleted successfully")


# =============================================================================
# App Views
# =============================================================================

class AppListView(APIView):
    """List all apps or create a new app"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all apps"""
        apps = App.objects.filter(is_active=True)
        
        # Filter by parent if specified
        parent_id = request.query_params.get('parent_id')
        if parent_id:
            apps = apps.filter(parent_app_id=parent_id)
        elif request.query_params.get('root_only') == 'true':
            apps = apps.filter(parent_app__isnull=True)
        
        serializer = AppListSerializer(apps, many=True)
        return success_response(serializer.data)
    
    def post(self, request):
        """Create a new app"""
        # Check if user has permission
        if not has_role_level(request.user, RoleLevel.DEVELOPER):
            return error_response(
                "Only developers can create apps",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AppCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            app = serializer.save()
            log_audit(
                'CREATE', 'APP', app.id, app.uuid,
                f"Created app: {app.name}",
                request.user, request,
                new_values=serializer.data
            )
            return success_response(
                AppDetailSerializer(app).data,
                "App created successfully",
                status.HTTP_201_CREATED
            )
        return error_response("Validation failed", serializer.errors)


class AppDetailView(APIView):
    """Get, update, or delete a specific app"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get a specific app"""
        app = get_object_or_404(App, pk=pk)
        serializer = AppDetailSerializer(app)
        return success_response(serializer.data)
    
    def put(self, request, pk):
        """Update an app"""
        if not has_role_level(request.user, RoleLevel.DEVELOPER):
            return error_response(
                "Only developers can update apps",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        app = get_object_or_404(App, pk=pk)
        old_values = AppDetailSerializer(app).data
        serializer = AppUpdateSerializer(app, data=request.data, partial=True)
        if serializer.is_valid():
            app = serializer.save()
            log_audit(
                'UPDATE', 'APP', app.id, app.uuid,
                f"Updated app: {app.name}",
                request.user, request,
                old_values=old_values,
                new_values=AppDetailSerializer(app).data
            )
            return success_response(
                AppDetailSerializer(app).data,
                "App updated successfully"
            )
        return error_response("Validation failed", serializer.errors)
    
    def delete(self, request, pk):
        """Delete (deactivate) an app"""
        if not has_role_level(request.user, RoleLevel.DEVELOPER):
            return error_response(
                "Only developers can delete apps",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        app = get_object_or_404(App, pk=pk)
        app.is_active = False
        app.save()
        
        log_audit(
            'DELETE', 'APP', app.id, app.uuid,
            f"Deleted app: {app.name}",
            request.user, request
        )
        
        return success_response(message="App deleted successfully")


# =============================================================================
# Feature Views
# =============================================================================

class FeatureListView(APIView):
    """List all features or create a new feature"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all features"""
        features = Feature.objects.filter(is_active=True)
        
        # Filter by app if specified
        app_id = request.query_params.get('app_id')
        if app_id:
            features = features.filter(app_id=app_id)
        
        app_code = request.query_params.get('app_code')
        if app_code:
            features = features.filter(app__code=app_code)
        
        serializer = FeatureListSerializer(features, many=True)
        return success_response(serializer.data)
    
    def post(self, request):
        """Create a new feature"""
        if not has_role_level(request.user, RoleLevel.DEVELOPER):
            return error_response(
                "Only developers can create features",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = FeatureCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            feature = serializer.save()
            log_audit(
                'CREATE', 'FEATURE', feature.id, feature.uuid,
                f"Created feature: {feature.name} in app {feature.app.name}",
                request.user, request,
                new_values=serializer.data
            )
            return success_response(
                FeatureDetailSerializer(feature).data,
                "Feature created successfully",
                status.HTTP_201_CREATED
            )
        return error_response("Validation failed", serializer.errors)


class FeatureDetailView(APIView):
    """Get, update, or delete a specific feature"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get a specific feature"""
        feature = get_object_or_404(Feature, pk=pk)
        serializer = FeatureDetailSerializer(feature)
        return success_response(serializer.data)
    
    def put(self, request, pk):
        """Update a feature"""
        if not has_role_level(request.user, RoleLevel.DEVELOPER):
            return error_response(
                "Only developers can update features",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        feature = get_object_or_404(Feature, pk=pk)
        old_values = FeatureDetailSerializer(feature).data
        serializer = FeatureUpdateSerializer(feature, data=request.data, partial=True)
        if serializer.is_valid():
            feature = serializer.save()
            log_audit(
                'UPDATE', 'FEATURE', feature.id, feature.uuid,
                f"Updated feature: {feature.name}",
                request.user, request,
                old_values=old_values,
                new_values=FeatureDetailSerializer(feature).data
            )
            return success_response(
                FeatureDetailSerializer(feature).data,
                "Feature updated successfully"
            )
        return error_response("Validation failed", serializer.errors)
    
    def delete(self, request, pk):
        """Delete (deactivate) a feature"""
        if not has_role_level(request.user, RoleLevel.DEVELOPER):
            return error_response(
                "Only developers can delete features",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        feature = get_object_or_404(Feature, pk=pk)
        feature.is_active = False
        feature.save()
        
        log_audit(
            'DELETE', 'FEATURE', feature.id, feature.uuid,
            f"Deleted feature: {feature.name}",
            request.user, request
        )
        
        return success_response(message="Feature deleted successfully")


# =============================================================================
# Role-App Mapping Views
# =============================================================================

class RoleAppMappingListView(APIView):
    """List all role-app mappings or create a new mapping"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all role-app mappings"""
        mappings = RoleAppMapping.objects.filter(is_active=True)
        
        # Filter by role if specified
        role_id = request.query_params.get('role_id')
        if role_id:
            mappings = mappings.filter(role_id=role_id)
        
        # Filter by app if specified
        app_id = request.query_params.get('app_id')
        if app_id:
            mappings = mappings.filter(app_id=app_id)
        
        serializer = RoleAppMappingSerializer(mappings, many=True)
        return success_response(serializer.data)
    
    def post(self, request):
        """Create a new role-app mapping"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to assign apps to roles",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RoleAppMappingCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            mapping = serializer.save()
            log_audit(
                'ASSIGN', 'ROLE_APP_MAPPING', mapping.id, mapping.uuid,
                f"Assigned app {mapping.app.name} to role {mapping.role.name}",
                request.user, request,
                new_values=RoleAppMappingSerializer(mapping).data
            )
            return success_response(
                RoleAppMappingSerializer(mapping).data,
                "App assigned to role successfully",
                status.HTTP_201_CREATED
            )
        return error_response("Validation failed", serializer.errors)


class RoleAppMappingDetailView(APIView):
    """Get, update, or delete a specific role-app mapping"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get a specific mapping"""
        mapping = get_object_or_404(RoleAppMapping, pk=pk)
        serializer = RoleAppMappingSerializer(mapping)
        return success_response(serializer.data)
    
    def put(self, request, pk):
        """Update a mapping"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to update role-app mappings",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        mapping = get_object_or_404(RoleAppMapping, pk=pk)
        old_values = RoleAppMappingSerializer(mapping).data
        serializer = RoleAppMappingUpdateSerializer(mapping, data=request.data, partial=True)
        if serializer.is_valid():
            mapping = serializer.save()
            log_audit(
                'UPDATE', 'ROLE_APP_MAPPING', mapping.id, mapping.uuid,
                f"Updated mapping: {mapping.role.name} -> {mapping.app.name}",
                request.user, request,
                old_values=old_values,
                new_values=RoleAppMappingSerializer(mapping).data
            )
            return success_response(
                RoleAppMappingSerializer(mapping).data,
                "Mapping updated successfully"
            )
        return error_response("Validation failed", serializer.errors)
    
    def delete(self, request, pk):
        """Delete (revoke) a mapping"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to revoke role-app mappings",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        mapping = get_object_or_404(RoleAppMapping, pk=pk)
        mapping.is_active = False
        mapping.save()
        
        log_audit(
            'REVOKE', 'ROLE_APP_MAPPING', mapping.id, mapping.uuid,
            f"Revoked app {mapping.app.name} from role {mapping.role.name}",
            request.user, request
        )
        
        return success_response(message="App access revoked from role successfully")


# =============================================================================
# Role-Feature Mapping Views
# =============================================================================

class RoleFeatureMappingListView(APIView):
    """List all role-feature mappings or create a new mapping"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all role-feature mappings"""
        mappings = RoleFeatureMapping.objects.filter(is_active=True)
        
        # Filter by role if specified
        role_id = request.query_params.get('role_id')
        if role_id:
            mappings = mappings.filter(role_id=role_id)
        
        # Filter by feature if specified
        feature_id = request.query_params.get('feature_id')
        if feature_id:
            mappings = mappings.filter(feature_id=feature_id)
        
        # Filter by app if specified
        app_id = request.query_params.get('app_id')
        if app_id:
            mappings = mappings.filter(feature__app_id=app_id)
        
        serializer = RoleFeatureMappingSerializer(mappings, many=True)
        return success_response(serializer.data)
    
    def post(self, request):
        """Create a new role-feature mapping"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to assign features to roles",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RoleFeatureMappingCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            mapping = serializer.save()
            log_audit(
                'ASSIGN', 'ROLE_FEATURE_MAPPING', mapping.id, mapping.uuid,
                f"Assigned feature {mapping.feature.name} to role {mapping.role.name}",
                request.user, request,
                new_values=RoleFeatureMappingSerializer(mapping).data
            )
            return success_response(
                RoleFeatureMappingSerializer(mapping).data,
                "Feature assigned to role successfully",
                status.HTTP_201_CREATED
            )
        return error_response("Validation failed", serializer.errors)


class RoleFeatureMappingDetailView(APIView):
    """Get, update, or delete a specific role-feature mapping"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get a specific mapping"""
        mapping = get_object_or_404(RoleFeatureMapping, pk=pk)
        serializer = RoleFeatureMappingSerializer(mapping)
        return success_response(serializer.data)
    
    def put(self, request, pk):
        """Update a mapping"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to update role-feature mappings",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        mapping = get_object_or_404(RoleFeatureMapping, pk=pk)
        old_values = RoleFeatureMappingSerializer(mapping).data
        serializer = RoleFeatureMappingUpdateSerializer(mapping, data=request.data, partial=True)
        if serializer.is_valid():
            mapping = serializer.save()
            log_audit(
                'UPDATE', 'ROLE_FEATURE_MAPPING', mapping.id, mapping.uuid,
                f"Updated mapping: {mapping.role.name} -> {mapping.feature.name}",
                request.user, request,
                old_values=old_values,
                new_values=RoleFeatureMappingSerializer(mapping).data
            )
            return success_response(
                RoleFeatureMappingSerializer(mapping).data,
                "Mapping updated successfully"
            )
        return error_response("Validation failed", serializer.errors)
    
    def delete(self, request, pk):
        """Delete (revoke) a mapping"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to revoke role-feature mappings",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        mapping = get_object_or_404(RoleFeatureMapping, pk=pk)
        mapping.is_active = False
        mapping.save()
        
        log_audit(
            'REVOKE', 'ROLE_FEATURE_MAPPING', mapping.id, mapping.uuid,
            f"Revoked feature {mapping.feature.name} from role {mapping.role.name}",
            request.user, request
        )
        
        return success_response(message="Feature access revoked from role successfully")


# =============================================================================
# User Role Assignment Views
# =============================================================================

class UserRoleAssignmentListView(APIView):
    """List all user role assignments or create a new assignment"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all user role assignments"""
        assignments = UserRoleAssignment.objects.filter(is_active=True)
        
        # Filter by user if specified
        user_id = request.query_params.get('user_id')
        if user_id:
            assignments = assignments.filter(user_id=user_id)
        
        # Filter by role if specified
        role_id = request.query_params.get('role_id')
        if role_id:
            assignments = assignments.filter(role_id=role_id)
        
        serializer = UserRoleAssignmentSerializer(assignments, many=True)
        return success_response(serializer.data)
    
    def post(self, request):
        """Assign a role to a user"""
        # Check permission to assign roles
        if not has_role_level(request.user, RoleLevel.ADMIN):
            return error_response(
                "You don't have permission to assign roles",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Validate that user can assign this specific role
        role_id = request.data.get('role')
        if role_id:
            try:
                role = UserRole.objects.get(id=role_id)
                user_level = get_user_level(request.user)
                if user_level is None or user_level >= role.level:
                    return error_response(
                        "You cannot assign a role with equal or higher privilege than your own",
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            except UserRole.DoesNotExist:
                return error_response("Role not found")
        
        serializer = UserRoleAssignmentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            assignment = serializer.save()
            log_audit(
                'ASSIGN', 'USER_ROLE_ASSIGNMENT', assignment.id, assignment.uuid,
                f"Assigned role {assignment.role.name} to user {assignment.user.email}",
                request.user, request,
                new_values=UserRoleAssignmentSerializer(assignment).data
            )
            return success_response(
                UserRoleAssignmentSerializer(assignment).data,
                "Role assigned to user successfully",
                status.HTTP_201_CREATED
            )
        return error_response("Validation failed", serializer.errors)


class UserRoleAssignmentDetailView(APIView):
    """Get, update, or delete a specific user role assignment"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get a specific assignment"""
        assignment = get_object_or_404(UserRoleAssignment, pk=pk)
        serializer = UserRoleAssignmentSerializer(assignment)
        return success_response(serializer.data)
    
    def put(self, request, pk):
        """Update an assignment"""
        if not has_role_level(request.user, RoleLevel.ADMIN):
            return error_response(
                "You don't have permission to update role assignments",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        assignment = get_object_or_404(UserRoleAssignment, pk=pk)
        
        # Check if user can manage this role
        user_level = get_user_level(request.user)
        if user_level is None or user_level >= assignment.role.level:
            return error_response(
                "You cannot modify assignments for roles with equal or higher privilege",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        old_values = UserRoleAssignmentSerializer(assignment).data
        serializer = UserRoleAssignmentUpdateSerializer(assignment, data=request.data, partial=True)
        if serializer.is_valid():
            assignment = serializer.save()
            log_audit(
                'UPDATE', 'USER_ROLE_ASSIGNMENT', assignment.id, assignment.uuid,
                f"Updated assignment: {assignment.user.email} - {assignment.role.name}",
                request.user, request,
                old_values=old_values,
                new_values=UserRoleAssignmentSerializer(assignment).data
            )
            return success_response(
                UserRoleAssignmentSerializer(assignment).data,
                "Assignment updated successfully"
            )
        return error_response("Validation failed", serializer.errors)
    
    def delete(self, request, pk):
        """Revoke a role assignment"""
        if not has_role_level(request.user, RoleLevel.ADMIN):
            return error_response(
                "You don't have permission to revoke role assignments",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        assignment = get_object_or_404(UserRoleAssignment, pk=pk)
        
        # Check if user can manage this role
        user_level = get_user_level(request.user)
        if user_level is None or user_level >= assignment.role.level:
            return error_response(
                "You cannot revoke assignments for roles with equal or higher privilege",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        assignment.is_active = False
        assignment.save()
        
        log_audit(
            'REVOKE', 'USER_ROLE_ASSIGNMENT', assignment.id, assignment.uuid,
            f"Revoked role {assignment.role.name} from user {assignment.user.email}",
            request.user, request
        )
        
        return success_response(message="Role revoked from user successfully")


# =============================================================================
# Bulk Operation Views
# =============================================================================

class BulkRoleAppMappingView(APIView):
    """Bulk assign apps to a role"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Bulk assign apps to a role"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to perform bulk operations",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BulkRoleAppMappingSerializer(data=request.data)
        if serializer.is_valid():
            role_id = serializer.validated_data['role_id']
            app_ids = serializer.validated_data['app_ids']
            
            try:
                role = UserRole.objects.get(id=role_id)
            except UserRole.DoesNotExist:
                return error_response("Role not found")
            
            created = []
            with transaction.atomic():
                for app_id in app_ids:
                    try:
                        app = App.objects.get(id=app_id)
                        mapping, is_new = RoleAppMapping.objects.get_or_create(
                            role=role,
                            app=app,
                            defaults={
                                'can_view': serializer.validated_data['can_view'],
                                'can_create': serializer.validated_data['can_create'],
                                'can_update': serializer.validated_data['can_update'],
                                'can_delete': serializer.validated_data['can_delete'],
                                'assigned_by': request.user
                            }
                        )
                        if is_new:
                            created.append(mapping.id)
                    except App.DoesNotExist:
                        continue
            
            return success_response(
                {'created_mappings': created, 'count': len(created)},
                f"Successfully assigned {len(created)} apps to role"
            )
        return error_response("Validation failed", serializer.errors)


class BulkRoleFeatureMappingView(APIView):
    """Bulk assign features to a role"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Bulk assign features to a role"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to perform bulk operations",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BulkRoleFeatureMappingSerializer(data=request.data)
        if serializer.is_valid():
            role_id = serializer.validated_data['role_id']
            feature_ids = serializer.validated_data['feature_ids']
            
            try:
                role = UserRole.objects.get(id=role_id)
            except UserRole.DoesNotExist:
                return error_response("Role not found")
            
            created = []
            with transaction.atomic():
                for feature_id in feature_ids:
                    try:
                        feature = Feature.objects.get(id=feature_id)
                        mapping, is_new = RoleFeatureMapping.objects.get_or_create(
                            role=role,
                            feature=feature,
                            defaults={
                                'can_view': serializer.validated_data['can_view'],
                                'can_create': serializer.validated_data['can_create'],
                                'can_update': serializer.validated_data['can_update'],
                                'can_delete': serializer.validated_data['can_delete'],
                                'assigned_by': request.user
                            }
                        )
                        if is_new:
                            created.append(mapping.id)
                    except Feature.DoesNotExist:
                        continue
            
            return success_response(
                {'created_mappings': created, 'count': len(created)},
                f"Successfully assigned {len(created)} features to role"
            )
        return error_response("Validation failed", serializer.errors)


class BulkUserRoleAssignmentView(APIView):
    """Bulk assign a role to multiple users"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Bulk assign a role to multiple users"""
        if not has_role_level(request.user, RoleLevel.ADMIN):
            return error_response(
                "You don't have permission to perform bulk operations",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BulkUserRoleAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            user_ids = serializer.validated_data['user_ids']
            role_id = serializer.validated_data['role_id']
            is_primary = serializer.validated_data['is_primary']
            
            try:
                role = UserRole.objects.get(id=role_id)
            except UserRole.DoesNotExist:
                return error_response("Role not found")
            
            # Check if user can assign this role
            user_level = get_user_level(request.user)
            if user_level is None or user_level >= role.level:
                return error_response(
                    "You cannot assign a role with equal or higher privilege",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            from users_auth.models import User
            created = []
            with transaction.atomic():
                for user_id in user_ids:
                    try:
                        user = User.objects.get(id=user_id)
                        assignment, is_new = UserRoleAssignment.objects.get_or_create(
                            user=user,
                            role=role,
                            defaults={
                                'is_primary': is_primary,
                                'assigned_by': request.user
                            }
                        )
                        if is_new:
                            created.append(assignment.id)
                    except User.DoesNotExist:
                        continue
            
            return success_response(
                {'created_assignments': created, 'count': len(created)},
                f"Successfully assigned role to {len(created)} users"
            )
        return error_response("Validation failed", serializer.errors)


# =============================================================================
# Permission Check Views
# =============================================================================

class CheckPermissionView(APIView):
    """Check if current user has a specific permission"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Check permission"""
        app_code = request.query_params.get('app_code')
        feature_code = request.query_params.get('feature_code')
        permission = request.query_params.get('permission', 'view')
        
        from .permissions import has_app_permission, has_feature_permission
        
        if feature_code:
            has_permission = has_feature_permission(request.user, app_code, feature_code, permission)
        elif app_code:
            has_permission = has_app_permission(request.user, app_code, permission)
        else:
            has_permission = False
        
        return success_response({
            'has_permission': has_permission,
            'app_code': app_code,
            'feature_code': feature_code,
            'permission': permission
        })


class MyPermissionsView(APIView):
    """Get all permissions of the current user"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's permissions"""
        permissions = get_user_permissions(request.user)
        return success_response(permissions)


# =============================================================================
# Audit Log Views
# =============================================================================

class AuditLogListView(APIView):
    """List audit logs"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of audit logs"""
        if not has_role_level(request.user, RoleLevel.SUPER_ADMIN):
            return error_response(
                "You don't have permission to view audit logs",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        logs = AuditLog.objects.all()
        
        # Filter by action
        action = request.query_params.get('action')
        if action:
            logs = logs.filter(action=action)
        
        # Filter by entity type
        entity_type = request.query_params.get('entity_type')
        if entity_type:
            logs = logs.filter(entity_type=entity_type)
        
        # Filter by user
        user_id = request.query_params.get('user_id')
        if user_id:
            logs = logs.filter(performed_by_id=user_id)
        
        # Limit results
        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]
        
        serializer = AuditLogSerializer(logs, many=True)
        return success_response(serializer.data)


# =============================================================================
# Initialize Default Roles View
# =============================================================================

class InitializeDefaultRolesView(APIView):
    """Initialize default system roles"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create default system roles if they don't exist"""
        if not has_role_level(request.user, RoleLevel.DEVELOPER):
            return error_response(
                "Only developers can initialize default roles",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        default_roles = [
            {
                'name': 'Developer',
                'code': 'DEVELOPER',
                'level': RoleLevel.DEVELOPER,
                'description': 'Full system access including code and development',
                'is_system_role': True
            },
            {
                'name': 'Super Admin',
                'code': 'SUPER_ADMIN',
                'level': RoleLevel.SUPER_ADMIN,
                'description': 'Full access to all apps and features, no code access',
                'is_system_role': True
            },
            {
                'name': 'Admin',
                'code': 'ADMIN',
                'level': RoleLevel.ADMIN,
                'description': 'Limited app access assigned by Super Admin',
                'is_system_role': True
            },
            {
                'name': 'Client',
                'code': 'CLIENT',
                'level': RoleLevel.CLIENT,
                'description': 'Portal access with features assigned by Admin',
                'is_system_role': True
            },
            {
                'name': 'End User',
                'code': 'END_USER',
                'level': RoleLevel.END_USER,
                'description': 'Basic access with limited features',
                'is_system_role': True
            },
        ]
        
        created_roles = []
        for role_data in default_roles:
            role, created = UserRole.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    **role_data,
                    'created_by': request.user
                }
            )
            if created:
                created_roles.append(role.name)
        
        return success_response(
            {'created_roles': created_roles},
            f"Initialized {len(created_roles)} default roles" if created_roles else "All default roles already exist"
        )


# =============================================================================
# Access Management Views (For SP/Developer to assign access to Admin/Client)
# =============================================================================

class UserAccessOverviewView(APIView):
    """
    Get complete access overview for a user.
    Includes: apps, features, role assignments.
    
    GET /api/rbac/users/<user_id>/access/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        """Get complete access overview for a user"""
        from users_auth.models import User
        
        # Only SP/Developer/Admin can view user access
        if not has_role_level(request.user, RoleLevel.ADMIN):
            return error_response(
                "You don't have permission to view user access",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            return error_response(
                "User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's role assignments
        role_assignments = UserRoleAssignment.objects.filter(
            user=user,
            is_active=True
        ).select_related('role')
        
        # Get all accessible apps and features based on roles
        accessible_apps = []
        accessible_features = []
        
        for assignment in role_assignments:
            role = assignment.role
            
            # Get role's app mappings
            app_mappings = RoleAppMapping.objects.filter(
                role=role,
                is_active=True
            ).select_related('app')
            
            for mapping in app_mappings:
                app_data = {
                    'app_id': mapping.app.id,
                    'app_code': mapping.app.code,
                    'app_name': mapping.app.name,
                    'can_view': mapping.can_view,
                    'can_create': mapping.can_create,
                    'can_update': mapping.can_update,
                    'can_delete': mapping.can_delete,
                    'assigned_via_role': role.name,
                }
                if app_data not in accessible_apps:
                    accessible_apps.append(app_data)
            
            # Get role's feature mappings
            feature_mappings = RoleFeatureMapping.objects.filter(
                role=role,
                is_active=True
            ).select_related('feature', 'feature__app')
            
            for mapping in feature_mappings:
                feature_data = {
                    'feature_id': mapping.feature.id,
                    'feature_code': mapping.feature.code,
                    'feature_name': mapping.feature.name,
                    'app_code': mapping.feature.app.code,
                    'app_name': mapping.feature.app.name,
                    'can_execute': mapping.can_execute,
                    'can_view': mapping.can_view,
                    'can_edit': mapping.can_edit,
                    'assigned_via_role': role.name,
                }
                if feature_data not in accessible_features:
                    accessible_features.append(feature_data)
        
        # Get KYC status if exists
        kyc_status = None
        try:
            from kyc_verification.models import KYCApplication
            kyc_app = KYCApplication.objects.get(user=user, is_deleted=False)
            kyc_status = {
                'application_id': kyc_app.application_id,
                'status': kyc_app.status,
                'completion_percentage': kyc_app.completion_percentage,
                'submitted_at': kyc_app.submitted_at.isoformat() if kyc_app.submitted_at else None,
                'approved_at': kyc_app.approved_at.isoformat() if kyc_app.approved_at else None,
            }
        except:
            pass
        
        return success_response({
            'user': {
                'id': user.id,
                'user_code': user.user_code,
                'email': user.email,
                'full_name': user.full_name,
                'user_role': user.user_role,
                'is_verified': user.is_verified,
                'is_email_verified': getattr(user, 'is_email_verified', False),
                'is_phone_verified': getattr(user, 'is_phone_verified', False),
            },
            'roles': [{
                'role_id': a.role.id,
                'role_code': a.role.code,
                'role_name': a.role.name,
                'role_level': a.role.level,
                'assigned_at': a.assigned_at.isoformat() if a.assigned_at else None,
            } for a in role_assignments],
            'apps': accessible_apps,
            'features': accessible_features,
            'kyc_status': kyc_status,
        })


class AssignAccessToUserView(APIView):
    """
    Assign app/feature access to a user by role.
    SP can assign to Admin/Client, Admin can assign to Client.
    
    POST /api/rbac/users/<user_id>/assign-access/
    
    Request body:
    {
        "role_code": "ADMIN",  // Role to assign
        "app_codes": ["USER_MGMT", "REPORTS"],  // Optional: specific apps
        "feature_codes": ["CREATE_USER", "VIEW_REPORT"],  // Optional: specific features
    }
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        """Assign access to a user"""
        from users_auth.models import User
        
        # Only SP/Developer/Admin can assign access
        if not has_role_level(request.user, RoleLevel.ADMIN):
            return error_response(
                "You don't have permission to assign access",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        try:
            target_user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            return error_response(
                "User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        role_code = request.data.get('role_code')
        app_codes = request.data.get('app_codes', [])
        feature_codes = request.data.get('feature_codes', [])
        
        if not role_code:
            return error_response(
                "Role code is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the role
        try:
            role = UserRole.objects.get(code=role_code, is_active=True)
        except UserRole.DoesNotExist:
            return error_response(
                f"Role '{role_code}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if requesting user can assign this role (hierarchy check)
        user_level = get_user_level(request.user)
        if user_level >= role.level:
            return error_response(
                f"You cannot assign a role equal to or higher than your own",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            # Create or update role assignment
            assignment, created = UserRoleAssignment.objects.update_or_create(
                user=target_user,
                role=role,
                defaults={
                    'is_active': True,
                    'assigned_by': request.user,
                }
            )
            
            # Update user's primary role if it's higher
            if role.level < get_user_level(target_user):
                target_user.user_role = role.code
                target_user.save(update_fields=['user_role'])
            
            # If specific apps are provided, create app mappings
            apps_assigned = []
            if app_codes:
                for app_code in app_codes:
                    try:
                        app = App.objects.get(code=app_code, is_active=True)
                        mapping, _ = RoleAppMapping.objects.update_or_create(
                            role=role,
                            app=app,
                            defaults={
                                'is_active': True,
                                'can_view': True,
                                'can_create': True,
                                'can_update': True,
                                'can_delete': True,
                                'assigned_by': request.user,
                            }
                        )
                        apps_assigned.append(app.name)
                    except App.DoesNotExist:
                        pass
            
            # If specific features are provided, create feature mappings
            features_assigned = []
            if feature_codes:
                for feature_code in feature_codes:
                    try:
                        feature = Feature.objects.get(code=feature_code, is_active=True)
                        mapping, _ = RoleFeatureMapping.objects.update_or_create(
                            role=role,
                            feature=feature,
                            defaults={
                                'is_active': True,
                                'can_execute': True,
                                'can_view': True,
                                'can_edit': True,
                                'assigned_by': request.user,
                            }
                        )
                        features_assigned.append(feature.name)
                    except Feature.DoesNotExist:
                        pass
            
            # Log audit
            log_audit(
                action='ASSIGN_ACCESS',
                entity_type='USER',
                entity_id=target_user.id,
                entity_uuid=None,
                description=f"Assigned {role.name} role to user {target_user.email}",
                user=request.user,
                request=request,
                new_values={
                    'role': role.code,
                    'apps': apps_assigned,
                    'features': features_assigned,
                }
            )
        
        return success_response({
            'user_id': target_user.id,
            'role_assigned': role.name,
            'apps_assigned': apps_assigned,
            'features_assigned': features_assigned,
        }, "Access assigned successfully")


class RevokeAccessFromUserView(APIView):
    """
    Revoke app/feature access from a user.
    
    POST /api/rbac/users/<user_id>/revoke-access/
    
    Request body:
    {
        "role_code": "ADMIN",  // Optional: revoke specific role
        "app_codes": ["USER_MGMT"],  // Optional: revoke specific apps
        "feature_codes": ["CREATE_USER"],  // Optional: revoke specific features
        "revoke_all": false  // Optional: revoke all access
    }
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        """Revoke access from a user"""
        from users_auth.models import User
        
        # Only SP/Developer/Admin can revoke access
        if not has_role_level(request.user, RoleLevel.ADMIN):
            return error_response(
                "You don't have permission to revoke access",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        try:
            target_user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            return error_response(
                "User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        role_code = request.data.get('role_code')
        app_codes = request.data.get('app_codes', [])
        feature_codes = request.data.get('feature_codes', [])
        revoke_all = request.data.get('revoke_all', False)
        
        revoked_items = {
            'roles': [],
            'apps': [],
            'features': [],
        }
        
        with transaction.atomic():
            if revoke_all:
                # Revoke all role assignments
                assignments = UserRoleAssignment.objects.filter(
                    user=target_user,
                    is_active=True
                )
                for assignment in assignments:
                    revoked_items['roles'].append(assignment.role.name)
                assignments.update(is_active=False)
                
                # Reset user to END_USER
                target_user.user_role = 'END_USER'
                target_user.save(update_fields=['user_role'])
            
            elif role_code:
                # Revoke specific role
                try:
                    role = UserRole.objects.get(code=role_code)
                    assignment = UserRoleAssignment.objects.filter(
                        user=target_user,
                        role=role,
                        is_active=True
                    ).first()
                    if assignment:
                        assignment.is_active = False
                        assignment.save()
                        revoked_items['roles'].append(role.name)
                        
                        # Recalculate user's primary role
                        remaining = UserRoleAssignment.objects.filter(
                            user=target_user,
                            is_active=True
                        ).select_related('role').order_by('role__level').first()
                        
                        if remaining:
                            target_user.user_role = remaining.role.code
                        else:
                            target_user.user_role = 'END_USER'
                        target_user.save(update_fields=['user_role'])
                except UserRole.DoesNotExist:
                    pass
            
            # Revoke specific apps (from role mappings)
            if app_codes:
                for app_code in app_codes:
                    try:
                        app = App.objects.get(code=app_code)
                        # Find user's roles and remove app access
                        user_roles = UserRoleAssignment.objects.filter(
                            user=target_user,
                            is_active=True
                        ).values_list('role_id', flat=True)
                        
                        mappings = RoleAppMapping.objects.filter(
                            role_id__in=user_roles,
                            app=app,
                            is_active=True
                        )
                        for mapping in mappings:
                            revoked_items['apps'].append(app.name)
                        mappings.update(is_active=False)
                    except App.DoesNotExist:
                        pass
            
            # Revoke specific features
            if feature_codes:
                for feature_code in feature_codes:
                    try:
                        feature = Feature.objects.get(code=feature_code)
                        user_roles = UserRoleAssignment.objects.filter(
                            user=target_user,
                            is_active=True
                        ).values_list('role_id', flat=True)
                        
                        mappings = RoleFeatureMapping.objects.filter(
                            role_id__in=user_roles,
                            feature=feature,
                            is_active=True
                        )
                        for mapping in mappings:
                            revoked_items['features'].append(feature.name)
                        mappings.update(is_active=False)
                    except Feature.DoesNotExist:
                        pass
            
            # Log audit
            log_audit(
                action='REVOKE_ACCESS',
                entity_type='USER',
                entity_id=target_user.id,
                entity_uuid=None,
                description=f"Revoked access from user {target_user.email}",
                user=request.user,
                request=request,
                old_values=revoked_items,
            )
        
        return success_response({
            'user_id': target_user.id,
            'revoked': revoked_items,
        }, "Access revoked successfully")


class AllAppsAndFeaturesView(APIView):
    """
    Get all apps and features available in the system.
    Used by SP/Developer to see what can be assigned.
    
    GET /api/rbac/all-access-items/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all apps and features"""
        # Only SP/Developer/Admin can view all access items
        if not has_role_level(request.user, RoleLevel.ADMIN):
            return error_response(
                "You don't have permission to view access items",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        apps = App.objects.filter(is_active=True).prefetch_related('features')
        
        result = []
        for app in apps:
            features = app.features.filter(is_active=True)
            result.append({
                'app_id': app.id,
                'app_code': app.code,
                'app_name': app.name,
                'app_description': app.description,
                'app_icon': app.icon,
                'features': [{
                    'feature_id': f.id,
                    'feature_code': f.code,
                    'feature_name': f.name,
                    'feature_description': f.description,
                    'feature_type': f.feature_type,
                } for f in features]
            })
        
        # Get all roles
        roles = UserRole.objects.filter(is_active=True).order_by('level')
        roles_data = [{
            'role_id': r.id,
            'role_code': r.code,
            'role_name': r.name,
            'role_level': r.level,
            'is_system_role': r.is_system_role,
        } for r in roles]
        
        return success_response({
            'apps': result,
            'roles': roles_data,
            'total_apps': len(result),
            'total_features': sum(len(app['features']) for app in result),
            'total_roles': len(roles_data),
        })
