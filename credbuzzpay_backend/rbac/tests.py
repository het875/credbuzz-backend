"""
RBAC Tests - Unit tests for Role-Based Access Control System
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import json

from users_auth.models import User
from users_auth.jwt_utils import JWTManager
from .models import (
    UserRole, App, Feature, RoleAppMapping,
    RoleFeatureMapping, UserRoleAssignment, RoleHierarchy, AuditLog, RoleLevel
)


class RBACModelTests(TestCase):
    """Test cases for RBAC models"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.user.set_password('testpass123')
        self.user.save()
        
        # Create test roles
        self.developer_role = UserRole.objects.create(
            name='Test Developer',
            code='TEST_DEVELOPER',
            level=RoleLevel.DEVELOPER,
            description='Test developer role',
            is_system_role=True
        )
        
        self.admin_role = UserRole.objects.create(
            name='Test Admin',
            code='TEST_ADMIN',
            level=RoleLevel.ADMIN,
            description='Test admin role'
        )
        
        self.client_role = UserRole.objects.create(
            name='Test Client',
            code='TEST_CLIENT',
            level=RoleLevel.CLIENT,
            description='Test client role'
        )
        
        # Create test app
        self.test_app = App.objects.create(
            name='Test App',
            code='TEST_APP',
            description='Test application'
        )
        
        # Create test feature
        self.test_feature = Feature.objects.create(
            app=self.test_app,
            name='Test Feature',
            code='TEST_FEATURE',
            description='Test feature',
            feature_type='ACTION'
        )
    
    def test_user_role_creation(self):
        """Test UserRole model creation"""
        self.assertEqual(self.developer_role.name, 'Test Developer')
        self.assertEqual(self.developer_role.code, 'TEST_DEVELOPER')
        self.assertEqual(self.developer_role.level, RoleLevel.DEVELOPER)
        self.assertTrue(self.developer_role.is_system_role)
    
    def test_user_role_can_manage_role(self):
        """Test role hierarchy management check"""
        # Developer can manage admin
        self.assertTrue(self.developer_role.can_manage_role(self.admin_role))
        # Admin can manage client
        self.assertTrue(self.admin_role.can_manage_role(self.client_role))
        # Client cannot manage admin
        self.assertFalse(self.client_role.can_manage_role(self.admin_role))
    
    def test_app_creation(self):
        """Test App model creation"""
        self.assertEqual(self.test_app.name, 'Test App')
        self.assertEqual(self.test_app.code, 'TEST_APP')
        self.assertTrue(self.test_app.is_active)
    
    def test_feature_creation(self):
        """Test Feature model creation"""
        self.assertEqual(self.test_feature.name, 'Test Feature')
        self.assertEqual(self.test_feature.app, self.test_app)
        self.assertEqual(self.test_feature.feature_type, 'ACTION')
    
    def test_role_app_mapping(self):
        """Test RoleAppMapping model"""
        mapping = RoleAppMapping.objects.create(
            role=self.admin_role,
            app=self.test_app,
            can_view=True,
            can_create=True,
            can_update=True,
            can_delete=False
        )
        
        self.assertEqual(mapping.role, self.admin_role)
        self.assertEqual(mapping.app, self.test_app)
        self.assertTrue(mapping.can_view)
        self.assertFalse(mapping.can_delete)
    
    def test_role_feature_mapping(self):
        """Test RoleFeatureMapping model"""
        mapping = RoleFeatureMapping.objects.create(
            role=self.admin_role,
            feature=self.test_feature,
            can_view=True,
            can_create=False,
            can_update=False,
            can_delete=False
        )
        
        self.assertEqual(mapping.role, self.admin_role)
        self.assertEqual(mapping.feature, self.test_feature)
        self.assertTrue(mapping.can_view)
    
    def test_user_role_assignment(self):
        """Test UserRoleAssignment model"""
        assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.admin_role,
            is_primary=True
        )
        
        self.assertEqual(assignment.user, self.user)
        self.assertEqual(assignment.role, self.admin_role)
        self.assertTrue(assignment.is_primary)
        self.assertTrue(assignment.is_valid())
    
    def test_user_role_assignment_validity(self):
        """Test UserRoleAssignment validity check"""
        # Create an expired assignment
        expired_assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.client_role,
            is_primary=False,
            valid_until=timezone.now() - timedelta(days=1)
        )
        
        self.assertFalse(expired_assignment.is_valid())
        
        # Create a future assignment
        future_assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.developer_role,
            is_primary=False,
            valid_from=timezone.now() + timedelta(days=1)
        )
        
        self.assertFalse(future_assignment.is_valid())
    
    def test_role_hierarchy(self):
        """Test RoleHierarchy model"""
        hierarchy = RoleHierarchy.objects.create(
            parent_role=self.developer_role,
            child_role=self.admin_role,
            can_assign=True,
            can_revoke=True,
            can_modify_permissions=True
        )
        
        self.assertEqual(hierarchy.parent_role, self.developer_role)
        self.assertEqual(hierarchy.child_role, self.admin_role)
        self.assertTrue(hierarchy.can_assign)
    
    def test_audit_log(self):
        """Test AuditLog model"""
        log = AuditLog.objects.create(
            action='CREATE',
            entity_type='USER_ROLE',
            entity_id=self.admin_role.id,
            entity_uuid=self.admin_role.uuid,
            description='Created test admin role',
            performed_by=self.user
        )
        
        self.assertEqual(log.action, 'CREATE')
        self.assertEqual(log.entity_type, 'USER_ROLE')
        self.assertEqual(log.performed_by, self.user)


class RBACAPITests(APITestCase):
    """Test cases for RBAC API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user with developer role
        self.admin_user = User.objects.create(
            username='adminuser',
            email='admin@example.com',
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.set_password('adminpass123')
        self.admin_user.save()
        
        # Create regular user
        self.regular_user = User.objects.create(
            username='regularuser',
            email='regular@example.com',
            first_name='Regular',
            last_name='User'
        )
        self.regular_user.set_password('regularpass123')
        self.regular_user.save()
        
        # Create roles
        self.developer_role = UserRole.objects.create(
            name='Developer',
            code='DEVELOPER',
            level=RoleLevel.DEVELOPER,
            is_system_role=True
        )
        
        self.super_admin_role = UserRole.objects.create(
            name='Super Admin',
            code='SUPER_ADMIN',
            level=RoleLevel.SUPER_ADMIN,
            is_system_role=True
        )
        
        self.admin_role = UserRole.objects.create(
            name='Admin',
            code='ADMIN',
            level=RoleLevel.ADMIN,
            is_system_role=True
        )
        
        self.client_role = UserRole.objects.create(
            name='Client',
            code='CLIENT',
            level=RoleLevel.CLIENT,
            is_system_role=True
        )
        
        self.end_user_role = UserRole.objects.create(
            name='End User',
            code='END_USER',
            level=RoleLevel.END_USER,
            is_system_role=True
        )
        
        # Assign developer role to admin user
        UserRoleAssignment.objects.create(
            user=self.admin_user,
            role=self.developer_role,
            is_primary=True
        )
        
        # Assign end user role to regular user
        UserRoleAssignment.objects.create(
            user=self.regular_user,
            role=self.end_user_role,
            is_primary=True
        )
        
        # Create test app and feature
        self.test_app = App.objects.create(
            name='User Management',
            code='USER_MGMT',
            description='User management application'
        )
        
        self.test_feature = Feature.objects.create(
            app=self.test_app,
            name='Create User',
            code='CREATE_USER',
            feature_type='ACTION'
        )
        
        # Get tokens
        tokens = JWTManager.generate_tokens(self.admin_user)
        self.admin_token = tokens['access_token']
        
        tokens = JWTManager.generate_tokens(self.regular_user)
        self.regular_token = tokens['access_token']
    
    def get_auth_header(self, token):
        """Get authorization header"""
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}
    
    # =========================================================================
    # UserRole Tests
    # =========================================================================
    
    def test_list_roles(self):
        """Test listing all user roles"""
        response = self.client.get(
            '/api/rbac/roles/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertGreaterEqual(len(response.json()['data']), 5)
    
    def test_list_roles_unauthenticated(self):
        """Test listing roles without authentication"""
        response = self.client.get('/api/rbac/roles/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_role(self):
        """Test creating a new user role"""
        data = {
            'name': 'Custom Role',
            'code': 'CUSTOM_ROLE',
            'level': RoleLevel.CLIENT,
            'description': 'A custom test role'
        }
        
        response = self.client.post(
            '/api/rbac/roles/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['name'], 'Custom Role')
    
    def test_create_role_forbidden_for_regular_user(self):
        """Test that regular users cannot create roles"""
        data = {
            'name': 'Hacker Role',
            'code': 'HACKER',
            'level': RoleLevel.DEVELOPER
        }
        
        response = self.client.post(
            '/api/rbac/roles/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.regular_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_role_detail(self):
        """Test getting role details"""
        response = self.client.get(
            f'/api/rbac/roles/{self.admin_role.id}/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['name'], 'Admin')
    
    def test_update_role(self):
        """Test updating a role"""
        # Create a non-system role
        test_role = UserRole.objects.create(
            name='Test Role',
            code='TEST_ROLE',
            level=RoleLevel.CLIENT,
            is_system_role=False
        )
        
        data = {
            'name': 'Updated Test Role',
            'description': 'Updated description'
        }
        
        response = self.client.put(
            f'/api/rbac/roles/{test_role.id}/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['name'], 'Updated Test Role')
    
    def test_delete_system_role_forbidden(self):
        """Test that system roles cannot be deleted"""
        response = self.client.delete(
            f'/api/rbac/roles/{self.admin_role.id}/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # =========================================================================
    # App Tests
    # =========================================================================
    
    def test_list_apps(self):
        """Test listing all apps"""
        response = self.client.get(
            '/api/rbac/apps/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
    
    def test_create_app(self):
        """Test creating a new app"""
        data = {
            'name': 'Reports',
            'code': 'REPORTS',
            'description': 'Reports application'
        }
        
        response = self.client.post(
            '/api/rbac/apps/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data']['name'], 'Reports')
    
    def test_create_app_forbidden_for_non_developer(self):
        """Test that only developers can create apps"""
        # Assign super admin role to admin user
        UserRoleAssignment.objects.filter(user=self.admin_user).delete()
        UserRoleAssignment.objects.create(
            user=self.admin_user,
            role=self.super_admin_role,
            is_primary=True
        )
        
        data = {
            'name': 'Test App',
            'code': 'TEST_APP2',
            'description': 'Test'
        }
        
        response = self.client.post(
            '/api/rbac/apps/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Restore developer role
        UserRoleAssignment.objects.filter(user=self.admin_user).delete()
        UserRoleAssignment.objects.create(
            user=self.admin_user,
            role=self.developer_role,
            is_primary=True
        )
    
    def test_get_app_detail(self):
        """Test getting app details"""
        response = self.client.get(
            f'/api/rbac/apps/{self.test_app.id}/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['name'], 'User Management')
    
    # =========================================================================
    # Feature Tests
    # =========================================================================
    
    def test_list_features(self):
        """Test listing all features"""
        response = self.client.get(
            '/api/rbac/features/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
    
    def test_list_features_by_app(self):
        """Test listing features filtered by app"""
        response = self.client.get(
            f'/api/rbac/features/?app_id={self.test_app.id}',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All returned features should belong to the test app
        for feature in response.json()['data']:
            self.assertEqual(feature['app'], self.test_app.id)
    
    def test_create_feature(self):
        """Test creating a new feature"""
        data = {
            'app': self.test_app.id,
            'name': 'Delete User',
            'code': 'DELETE_USER',
            'feature_type': 'ACTION'
        }
        
        response = self.client.post(
            '/api/rbac/features/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data']['name'], 'Delete User')
    
    # =========================================================================
    # Role-App Mapping Tests
    # =========================================================================
    
    def test_create_role_app_mapping(self):
        """Test assigning an app to a role"""
        data = {
            'role': self.admin_role.id,
            'app': self.test_app.id,
            'can_view': True,
            'can_create': True,
            'can_update': True,
            'can_delete': False
        }
        
        response = self.client.post(
            '/api/rbac/role-app-mappings/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()['data']['can_view'])
        self.assertFalse(response.json()['data']['can_delete'])
    
    def test_list_role_app_mappings(self):
        """Test listing role-app mappings"""
        # Create a mapping first
        RoleAppMapping.objects.create(
            role=self.admin_role,
            app=self.test_app,
            can_view=True
        )
        
        response = self.client.get(
            '/api/rbac/role-app-mappings/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
    
    # =========================================================================
    # Role-Feature Mapping Tests
    # =========================================================================
    
    def test_create_role_feature_mapping(self):
        """Test assigning a feature to a role"""
        data = {
            'role': self.admin_role.id,
            'feature': self.test_feature.id,
            'can_view': True,
            'can_create': False,
            'can_update': False,
            'can_delete': False
        }
        
        response = self.client.post(
            '/api/rbac/role-feature-mappings/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()['data']['can_view'])
    
    # =========================================================================
    # User Role Assignment Tests
    # =========================================================================
    
    def test_assign_role_to_user(self):
        """Test assigning a role to a user"""
        # Create a new user
        new_user = User.objects.create(
            username='newuser',
            email='new@example.com'
        )
        new_user.set_password('newpass123')
        new_user.save()
        
        data = {
            'user': new_user.id,
            'role': self.client_role.id,
            'is_primary': True
        }
        
        response = self.client.post(
            '/api/rbac/user-role-assignments/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()['data']['is_primary'])
    
    def test_cannot_assign_higher_privilege_role(self):
        """Test that users cannot assign roles with higher or equal privilege"""
        # Create super admin user
        super_admin_user = User.objects.create(
            username='superadmin',
            email='super@example.com'
        )
        super_admin_user.set_password('superpass123')
        super_admin_user.save()
        
        UserRoleAssignment.objects.create(
            user=super_admin_user,
            role=self.super_admin_role,
            is_primary=True
        )
        
        tokens = JWTManager.generate_tokens(super_admin_user)
        super_admin_token = tokens['access_token']
        
        # Super admin trying to assign developer role
        data = {
            'user': self.regular_user.id,
            'role': self.developer_role.id,
            'is_primary': False
        }
        
        response = self.client.post(
            '/api/rbac/user-role-assignments/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(super_admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_user_role_assignments(self):
        """Test listing user role assignments"""
        response = self.client.get(
            '/api/rbac/user-role-assignments/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
    
    # =========================================================================
    # Permission Check Tests
    # =========================================================================
    
    def test_my_permissions(self):
        """Test getting current user's permissions"""
        response = self.client.get(
            '/api/rbac/my-permissions/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertIn('roles', response.json()['data'])
        self.assertIn('apps', response.json()['data'])
        self.assertIn('features', response.json()['data'])
    
    def test_check_permission(self):
        """Test checking specific permission"""
        # Assign app permission to admin role
        RoleAppMapping.objects.create(
            role=self.admin_role,
            app=self.test_app,
            can_view=True,
            can_create=True
        )
        
        # Assign admin role to a user
        test_user = User.objects.create(
            username='permtest',
            email='permtest@example.com'
        )
        test_user.set_password('permtest123')
        test_user.save()
        
        UserRoleAssignment.objects.create(
            user=test_user,
            role=self.admin_role,
            is_primary=True
        )
        
        tokens = JWTManager.generate_tokens(test_user)
        test_token = tokens['access_token']
        
        response = self.client.get(
            f'/api/rbac/check-permission/?app_code=USER_MGMT&permission=view',
            **self.get_auth_header(test_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['data']['has_permission'])
    
    # =========================================================================
    # Bulk Operation Tests
    # =========================================================================
    
    def test_bulk_assign_apps(self):
        """Test bulk assigning apps to a role"""
        # Create additional apps
        app2 = App.objects.create(name='App 2', code='APP_2')
        app3 = App.objects.create(name='App 3', code='APP_3')
        
        data = {
            'role_id': self.admin_role.id,
            'app_ids': [self.test_app.id, app2.id, app3.id],
            'can_view': True,
            'can_create': False,
            'can_update': False,
            'can_delete': False
        }
        
        response = self.client.post(
            '/api/rbac/role-app-mappings/bulk/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['count'], 3)
    
    def test_bulk_assign_features(self):
        """Test bulk assigning features to a role"""
        # Create additional features
        feature2 = Feature.objects.create(
            app=self.test_app,
            name='Feature 2',
            code='FEATURE_2'
        )
        feature3 = Feature.objects.create(
            app=self.test_app,
            name='Feature 3',
            code='FEATURE_3'
        )
        
        data = {
            'role_id': self.admin_role.id,
            'feature_ids': [self.test_feature.id, feature2.id, feature3.id],
            'can_view': True,
            'can_create': True,
            'can_update': False,
            'can_delete': False
        }
        
        response = self.client.post(
            '/api/rbac/role-feature-mappings/bulk/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['count'], 3)
    
    def test_bulk_assign_users_to_role(self):
        """Test bulk assigning a role to multiple users"""
        # Create additional users
        user2 = User.objects.create(username='user2', email='user2@example.com')
        user3 = User.objects.create(username='user3', email='user3@example.com')
        
        data = {
            'user_ids': [user2.id, user3.id],
            'role_id': self.client_role.id,
            'is_primary': False
        }
        
        response = self.client.post(
            '/api/rbac/user-role-assignments/bulk/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['count'], 2)
    
    # =========================================================================
    # Audit Log Tests
    # =========================================================================
    
    def test_audit_log_created_on_role_creation(self):
        """Test that audit log is created when a role is created"""
        initial_log_count = AuditLog.objects.count()
        
        data = {
            'name': 'Audit Test Role',
            'code': 'AUDIT_TEST',
            'level': RoleLevel.CLIENT
        }
        
        self.client.post(
            '/api/rbac/roles/',
            data=json.dumps(data),
            content_type='application/json',
            **self.get_auth_header(self.admin_token)
        )
        
        # Check that an audit log was created
        self.assertEqual(AuditLog.objects.count(), initial_log_count + 1)
        
        log = AuditLog.objects.latest('created_at')
        self.assertEqual(log.action, 'CREATE')
        self.assertEqual(log.entity_type, 'USER_ROLE')
    
    def test_list_audit_logs(self):
        """Test listing audit logs"""
        response = self.client.get(
            '/api/rbac/audit-logs/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
    
    def test_audit_logs_forbidden_for_non_super_admin(self):
        """Test that only super admins can view audit logs"""
        # Assign admin role (not super admin or developer)
        UserRoleAssignment.objects.filter(user=self.admin_user).delete()
        UserRoleAssignment.objects.create(
            user=self.admin_user,
            role=self.admin_role,
            is_primary=True
        )
        
        response = self.client.get(
            '/api/rbac/audit-logs/',
            **self.get_auth_header(self.admin_token)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Restore developer role
        UserRoleAssignment.objects.filter(user=self.admin_user).delete()
        UserRoleAssignment.objects.create(
            user=self.admin_user,
            role=self.developer_role,
            is_primary=True
        )


class RBACPermissionHelperTests(TestCase):
    """Test cases for permission helper functions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('testpass123')
        self.user.save()
        
        self.developer_role = UserRole.objects.create(
            name='Developer',
            code='DEVELOPER',
            level=RoleLevel.DEVELOPER
        )
        
        self.admin_role = UserRole.objects.create(
            name='Admin',
            code='ADMIN',
            level=RoleLevel.ADMIN
        )
        
        self.test_app = App.objects.create(
            name='Test App',
            code='TEST_APP'
        )
        
        self.test_feature = Feature.objects.create(
            app=self.test_app,
            name='Test Feature',
            code='TEST_FEATURE'
        )
    
    def test_get_user_level_with_role(self):
        """Test getting user level when user has a role"""
        from .permissions import get_user_level
        
        UserRoleAssignment.objects.create(
            user=self.user,
            role=self.admin_role,
            is_primary=True
        )
        
        level = get_user_level(self.user)
        self.assertEqual(level, RoleLevel.ADMIN)
    
    def test_get_user_level_without_role(self):
        """Test getting user level when user has no role"""
        from .permissions import get_user_level
        
        level = get_user_level(self.user)
        self.assertIsNone(level)
    
    def test_has_role_level(self):
        """Test has_role_level function"""
        from .permissions import has_role_level
        
        UserRoleAssignment.objects.create(
            user=self.user,
            role=self.admin_role,
            is_primary=True
        )
        
        # Admin should have admin level
        self.assertTrue(has_role_level(self.user, RoleLevel.ADMIN))
        # Admin should have client level (lower privilege)
        self.assertTrue(has_role_level(self.user, RoleLevel.CLIENT))
        # Admin should NOT have super admin level (higher privilege)
        self.assertFalse(has_role_level(self.user, RoleLevel.SUPER_ADMIN))
    
    def test_has_app_permission(self):
        """Test has_app_permission function"""
        from .permissions import has_app_permission
        
        UserRoleAssignment.objects.create(
            user=self.user,
            role=self.admin_role,
            is_primary=True
        )
        
        RoleAppMapping.objects.create(
            role=self.admin_role,
            app=self.test_app,
            can_view=True,
            can_create=True,
            can_update=False,
            can_delete=False
        )
        
        self.assertTrue(has_app_permission(self.user, 'TEST_APP', 'view'))
        self.assertTrue(has_app_permission(self.user, 'TEST_APP', 'create'))
        self.assertFalse(has_app_permission(self.user, 'TEST_APP', 'update'))
        self.assertFalse(has_app_permission(self.user, 'TEST_APP', 'delete'))
    
    def test_has_feature_permission(self):
        """Test has_feature_permission function"""
        from .permissions import has_feature_permission
        
        UserRoleAssignment.objects.create(
            user=self.user,
            role=self.admin_role,
            is_primary=True
        )
        
        RoleFeatureMapping.objects.create(
            role=self.admin_role,
            feature=self.test_feature,
            can_view=True,
            can_create=False,
            can_update=False,
            can_delete=False
        )
        
        self.assertTrue(has_feature_permission(self.user, 'TEST_APP', 'TEST_FEATURE', 'view'))
        self.assertFalse(has_feature_permission(self.user, 'TEST_APP', 'TEST_FEATURE', 'create'))
    
    def test_developer_has_full_access(self):
        """Test that developer has full access to all apps and features"""
        from .permissions import has_app_permission, has_feature_permission
        
        UserRoleAssignment.objects.create(
            user=self.user,
            role=self.developer_role,
            is_primary=True
        )
        
        # Developer should have all permissions even without explicit mappings
        self.assertTrue(has_app_permission(self.user, 'TEST_APP', 'view'))
        self.assertTrue(has_app_permission(self.user, 'TEST_APP', 'create'))
        self.assertTrue(has_app_permission(self.user, 'TEST_APP', 'update'))
        self.assertTrue(has_app_permission(self.user, 'TEST_APP', 'delete'))
        
        self.assertTrue(has_feature_permission(self.user, 'TEST_APP', 'TEST_FEATURE', 'view'))
        self.assertTrue(has_feature_permission(self.user, 'TEST_APP', 'TEST_FEATURE', 'delete'))
    
    def test_get_user_permissions(self):
        """Test get_user_permissions function"""
        from .permissions import get_user_permissions
        
        UserRoleAssignment.objects.create(
            user=self.user,
            role=self.admin_role,
            is_primary=True
        )
        
        RoleAppMapping.objects.create(
            role=self.admin_role,
            app=self.test_app,
            can_view=True,
            can_create=True
        )
        
        permissions = get_user_permissions(self.user)
        
        self.assertIn('roles', permissions)
        self.assertIn('apps', permissions)
        self.assertIn('features', permissions)
        self.assertEqual(permissions['user_id'], self.user.id)
        
        # Check that admin role is in permissions
        role_names = [r['name'] for r in permissions['roles']]
        self.assertIn('Admin', role_names)

