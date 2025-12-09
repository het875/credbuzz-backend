"""
RBAC (Role-Based Access Control) System - Entity Relationship Design

================================================================================
HIERARCHICAL USER ROLES
================================================================================

1. DEVELOPER (Level 1 - Highest)
   - Full access to everything including code
   - Can manage all roles, apps, features
   - System-level access

2. SUPER ADMIN (Level 2)
   - Full access to all apps and features
   - Cannot access code/development side
   - Can manage admins, clients, end users
   - Can assign apps and features to roles

3. ADMIN (Level 3)
   - Limited app access (assigned by Super Admin)
   - Limited feature access (assigned by Super Admin)
   - Can manage clients and end users within their scope

4. CLIENT (Level 4)
   - Portal access only
   - Features assigned by Admin
   - Can manage end users within their scope

5. END USER (Level 5 - Lowest)
   - Limited access assigned by Client
   - No management capabilities

================================================================================
ENTITY RELATIONSHIP DIAGRAM
================================================================================

+------------------+       +------------------+       +------------------+
|    UserRole      |       |       App        |       |     Feature      |
+------------------+       +------------------+       +------------------+
| id (PK)          |       | id (PK)          |       | id (PK)          |
| name             |       | name             |       | name             |
| code             |       | code             |       | code             |
| level            |       | description      |       | description      |
| description      |       | icon             |       | app_id (FK)      |
| is_system_role   |       | is_active        |       | is_active        |
| is_active        |       | created_at       |       | created_at       |
| created_at       |       | updated_at       |       | updated_at       |
| updated_at       |       +------------------+       +------------------+
| created_by (FK)  |               |                         |
+------------------+               |                         |
        |                          |                         |
        |                          v                         v
        |               +----------------------+   +------------------------+
        |               |   RoleAppMapping     |   |  RoleFeatureMapping    |
        +-------------->+----------------------+   +------------------------+
                        | id (PK)              |   | id (PK)                |
                        | role_id (FK)         |   | role_id (FK)           |
                        | app_id (FK)          |   | feature_id (FK)        |
                        | can_create           |   | can_view               |
                        | can_read             |   | can_create             |
                        | can_update           |   | can_update             |
                        | can_delete           |   | can_delete             |
                        | assigned_by (FK)     |   | assigned_by (FK)       |
                        | created_at           |   | created_at             |
                        +----------------------+   +------------------------+

+------------------+
|      User        |  (from users_auth)
+------------------+
        |
        v
+------------------------+
|  UserRoleAssignment    |
+------------------------+
| id (PK)                |
| user_id (FK)           |
| role_id (FK)           |
| assigned_by (FK)       |
| is_primary             |
| is_active              |
| valid_from             |
| valid_until            |
| created_at             |
+------------------------+

================================================================================
PERMISSION INHERITANCE RULES
================================================================================

1. Higher level roles can manage lower level roles
2. Role level determines base permissions
3. Explicit app/feature mappings override defaults
4. Users can have multiple roles (primary + secondary)
5. Most permissive permission wins for same resource

================================================================================
ROLE LEVELS
================================================================================

DEVELOPER    = 1  (Highest - Full System Access)
SUPER_ADMIN  = 2  (Full App Access, No Code)
ADMIN        = 3  (Limited App Access)
CLIENT       = 4  (Portal Access)
END_USER     = 5  (Lowest - Basic Access)

================================================================================
"""
