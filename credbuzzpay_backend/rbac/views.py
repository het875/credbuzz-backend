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
