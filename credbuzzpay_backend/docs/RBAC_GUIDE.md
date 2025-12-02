# RBAC (Role-Based Access Control) Guide

## Overview

The CredBuzz Backend implements a comprehensive multi-level Role-Based Access Control (RBAC) system that provides fine-grained access control for applications, features, and operations.

## Role Hierarchy

The system implements 5 hierarchical role levels:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ROLE HIERARCHY                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Level 1: Developer                                             │
│   ├── Full system access                                         │
│   ├── Can manage all roles, apps, features                       │
│   ├── Can assign any role to any user                            │
│   └── System configuration access                                │
│                                                                  │
│   Level 2: Super Admin                                           │
│   ├── Full application access                                    │
│   ├── Can manage roles (except Developer)                        │
│   ├── Can manage users and assignments                           │
│   └── Can view audit logs                                        │
│                                                                  │
│   Level 3: Admin                                                 │
│   ├── Limited app access (assigned apps only)                    │
│   ├── Can manage users within scope                              │
│   ├── Can assign lower roles (Client, End User)                  │
│   └── Limited configuration access                               │
│                                                                  │
│   Level 4: Client                                                │
│   ├── Portal apps and features access                            │
│   ├── Can manage own profile                                     │
│   ├── Can view assigned content                                  │
│   └── Can create End User accounts (if permitted)                │
│                                                                  │
│   Level 5: End User                                              │
│   ├── Minimal access                                             │
│   ├── Read-only on assigned features                             │
│   └── Can manage own profile only                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. User Roles

User roles define the hierarchy level and permissions set for a user.

```json
{
    "id": 1,
    "name": "Developer",
    "code": "DEVELOPER",
    "level": 1,
    "is_system_role": true,
    "description": "Full system access"
}
```

**Fields:**
- `name`: Display name of the role
- `code`: Unique identifier code (uppercase, underscores)
- `level`: Hierarchy level (1=highest, 5=lowest)
- `is_system_role`: If true, role cannot be deleted
- `is_active`: Whether role is active

### 2. Apps (Applications/Modules)

Apps represent different modules or sections of the system.

```json
{
    "id": 1,
    "name": "User Management",
    "code": "USER_MGMT",
    "description": "Manage users and profiles",
    "icon": "fa-users",
    "display_order": 1,
    "parent": null
}
```

**Features:**
- Apps can have parent-child relationships (nested modules)
- Apps can contain multiple features
- Each app can be assigned to multiple roles

### 3. Features

Features represent specific actions or sections within an app.

```json
{
    "id": 1,
    "app": 1,
    "name": "Create User",
    "code": "CREATE_USER",
    "feature_type": "ACTION",
    "description": "Create new user accounts"
}
```

**Feature Types:**
- `VIEW`: Read-only screen/page
- `ACTION`: Actionable operation (create, edit, delete)
- `REPORT`: Reporting feature
- `SETTING`: Configuration setting

### 4. Role-App Mappings

Define which apps a role can access and with what CRUD permissions.

```json
{
    "role": 3,
    "app": 1,
    "can_view": true,
    "can_create": true,
    "can_update": true,
    "can_delete": false
}
```

### 5. Role-Feature Mappings

Define which features a role can access and with what CRUD permissions.

```json
{
    "role": 3,
    "feature": 1,
    "can_view": true,
    "can_create": true,
    "can_update": false,
    "can_delete": false
}
```

### 6. User Role Assignments

Assign roles to users with optional time-based validity.

```json
{
    "user": 5,
    "role": 4,
    "is_primary": true,
    "valid_from": "2025-01-01T00:00:00Z",
    "valid_until": "2026-01-01T00:00:00Z"
}
```

## Permission Resolution

### How Permissions Are Determined

1. **Get User's Roles**: System fetches all active role assignments for the user
2. **Find Highest Role**: The role with the lowest `level` value (highest privilege) is used
3. **Check App Access**: Role-App mappings determine app-level permissions
4. **Check Feature Access**: Role-Feature mappings determine feature-level permissions

### Permission Inheritance

- **Developers (Level 1)**: Have implicit full access to everything
- **Super Admins (Level 2)**: Have full access to all apps and features
- **Lower Roles**: Only have access to explicitly assigned apps/features

### CRUD Permissions

Each mapping can have 4 permission flags:
- `can_view`: Can read/view the resource
- `can_create`: Can create new resources
- `can_update`: Can edit existing resources
- `can_delete`: Can delete resources

## API Usage Examples

### 1. Check User's Permissions

```http
GET /api/rbac/my-permissions/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "user": {
            "id": 5,
            "email": "admin@example.com"
        },
        "primary_role": {
            "id": 3,
            "name": "Admin",
            "level": 3
        },
        "all_roles": [
            {"id": 3, "name": "Admin", "level": 3}
        ],
        "apps": [
            {
                "app_id": 1,
                "app_code": "USER_MGMT",
                "app_name": "User Management",
                "can_view": true,
                "can_create": true,
                "can_update": true,
                "can_delete": false,
                "features": [
                    {
                        "feature_id": 1,
                        "feature_code": "CREATE_USER",
                        "can_view": true,
                        "can_create": true
                    }
                ]
            }
        ]
    }
}
```

### 2. Check Specific Permission

```http
GET /api/rbac/check-permission/?app_code=USER_MGMT&permission=create
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "has_permission": true,
        "app_code": "USER_MGMT",
        "feature_code": null,
        "permission": "create",
        "user_role_level": 3
    }
}
```

### 3. Assign Role to User

```http
POST /api/rbac/user-role-assignments/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "user": 10,
    "role": 4,
    "is_primary": true
}
```

### 4. Grant App Access to Role

```http
POST /api/rbac/role-app-mappings/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "role": 4,
    "app": 1,
    "can_view": true,
    "can_create": false,
    "can_update": false,
    "can_delete": false
}
```

## Frontend Integration

### Checking Permissions in Frontend

```javascript
// Fetch user permissions on login
const response = await fetch('/api/rbac/my-permissions/', {
    headers: { 'Authorization': `Bearer ${accessToken}` }
});
const permissions = await response.json();

// Store in state/context
setUserPermissions(permissions.data);

// Check permission before rendering
function canAccessApp(appCode) {
    return permissions.data.apps.some(app => 
        app.app_code === appCode && app.can_view
    );
}

function canPerformAction(appCode, featureCode, action) {
    const app = permissions.data.apps.find(a => a.app_code === appCode);
    if (!app) return false;
    
    const feature = app.features.find(f => f.feature_code === featureCode);
    if (!feature) return false;
    
    return feature[`can_${action}`];
}

// Usage in component
{canAccessApp('USER_MGMT') && <UserManagementModule />}

{canPerformAction('USER_MGMT', 'CREATE_USER', 'create') && 
    <button>Create User</button>
}
```

### Navigation Menu Example

```javascript
function buildNavMenu(permissions) {
    const menu = [];
    
    permissions.data.apps.forEach(app => {
        if (app.can_view) {
            menu.push({
                name: app.app_name,
                icon: app.icon || 'fa-folder',
                features: app.features
                    .filter(f => f.can_view)
                    .map(f => ({
                        name: f.feature_name,
                        code: f.feature_code
                    }))
            });
        }
    });
    
    return menu;
}
```

## Backend Integration

### Using Permission Decorators

```python
from rbac.permissions import IsDeveloper, IsSuperAdmin, IsAdmin, has_app_permission

class UserViewSet(viewsets.ModelViewSet):
    # Only developers and super admins can access
    permission_classes = [IsSuperAdmin]
    
    def get_permissions(self):
        if self.action == 'destroy':
            return [IsDeveloper()]
        return super().get_permissions()
```

### Custom Permission Check

```python
from rbac.permissions import has_app_permission, has_feature_permission

def my_view(request):
    # Check app-level permission
    if not has_app_permission(request.user, 'USER_MGMT', 'create'):
        return Response({'error': 'Permission denied'}, status=403)
    
    # Check feature-level permission
    if not has_feature_permission(request.user, 'USER_MGMT', 'CREATE_USER', 'create'):
        return Response({'error': 'Permission denied'}, status=403)
    
    # Proceed with operation
    ...
```

## Audit Logging

All RBAC operations are automatically logged:

```json
{
    "id": 1,
    "user": 1,
    "action": "CREATE",
    "entity_type": "USER_ROLE_ASSIGNMENT",
    "entity_id": 5,
    "old_values": null,
    "new_values": {"user": 10, "role": 4},
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "timestamp": "2025-11-28T10:00:00Z"
}
```

**Action Types:**
- `CREATE`: New entity created
- `UPDATE`: Entity modified
- `DELETE`: Entity removed
- `ASSIGN`: Permission/role assigned
- `REVOKE`: Permission/role revoked

## Best Practices

1. **Use System Roles**: Don't delete or modify the 5 default system roles
2. **Principle of Least Privilege**: Assign the minimum required permissions
3. **Use Feature-Level Permissions**: For fine-grained control, use feature mappings
4. **Time-Based Assignments**: Use `valid_from` and `valid_until` for temporary access
5. **Audit Regularly**: Review audit logs for suspicious activities
6. **Test Permissions**: Always test permission checks before deployment

## Default Roles Reference

| Role | Code | Level | Description |
|------|------|-------|-------------|
| Developer | DEVELOPER | 1 | Full system access, can manage everything |
| Super Admin | SUPER_ADMIN | 2 | Full app access, manages roles and users |
| Admin | ADMIN | 3 | Limited app access, manages assigned areas |
| Client | CLIENT | 4 | Portal access, manages own resources |
| End User | END_USER | 5 | Minimal read-only access |

## Troubleshooting

### User Can't Access Expected Features

1. Check user has a role assignment: `GET /api/rbac/user-role-assignments/?user_id=X`
2. Check role has app access: `GET /api/rbac/role-app-mappings/?role_id=Y`
3. Check role has feature access: `GET /api/rbac/role-feature-mappings/?role_id=Y`
4. Verify assignment validity dates are current

### Permission Denied Errors

1. Ensure access token is valid and not expired
2. Check user's primary role level
3. Verify the specific CRUD permission (view/create/update/delete) is granted
4. For bulk operations, ensure user has permission on all target entities
