# Database Schema - CredBuzz Backend

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    CREDBUZZ BACKEND DATABASE SCHEMA                                      │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                         │
│  ┌─────────────────────────┐                                                                            │
│  │        User             │     (users_auth app)                                                       │
│  ├─────────────────────────┤                                                                            │
│  │ PK  id                  │                                                                            │
│  │     uuid                │                                                                            │
│  │     email (unique)      │                                                                            │
│  │     username (unique)   │                                                                            │
│  │     password            │                                                                            │
│  │     first_name          │                                                                            │
│  │     last_name           │                                                                            │
│  │     phone_number        │                                                                            │
│  │     profile_image       │                                                                            │
│  │     is_active           │                                                                            │
│  │     is_verified         │                                                                            │
│  │     last_login          │                                                                            │
│  │     created_at          │                                                                            │
│  │     updated_at          │                                                                            │
│  └──────────┬──────────────┘                                                                            │
│             │                                                                                           │
│             │ 1:N                                                                                       │
│             ▼                                                                                           │
│  ┌─────────────────────────┐      ┌─────────────────────────┐                                          │
│  │   PasswordResetToken    │      │      UserSession        │                                          │
│  ├─────────────────────────┤      ├─────────────────────────┤                                          │
│  │ PK  id                  │      │ PK  id                  │                                          │
│  │ FK  user_id             │      │ FK  user_id             │                                          │
│  │     token               │      │     session_token       │                                          │
│  │     expires_at          │      │     refresh_token       │                                          │
│  │     is_used             │      │     device_info         │                                          │
│  │     created_at          │      │     ip_address          │                                          │
│  └─────────────────────────┘      │     is_active           │                                          │
│                                   │     created_at          │                                          │
│                                   │     expires_at          │                                          │
│                                   └─────────────────────────┘                                          │
│                                                                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                         RBAC SYSTEM                                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                         │
│  ┌─────────────────────────┐                                                                            │
│  │       UserRole          │                                                                            │
│  ├─────────────────────────┤                                                                            │
│  │ PK  id                  │                                                                            │
│  │     uuid                │                                                                            │
│  │     name (unique)       │◄──────────────────────────────────────┐                                    │
│  │     code (unique)       │                                       │                                    │
│  │     level (1-5)         │                                       │                                    │
│  │     description         │                                       │                                    │
│  │     is_system_role      │                                       │                                    │
│  │     is_active           │                                       │                                    │
│  │ FK  created_by          │                                       │                                    │
│  │     created_at          │                                       │                                    │
│  │     updated_at          │                                       │                                    │
│  └──────────┬──────────────┘                                       │                                    │
│             │                                                       │                                    │
│             │                                                       │                                    │
│    ┌────────┴────────┬──────────────────┬──────────────────────────┤                                    │
│    │                 │                  │                          │                                    │
│    ▼                 ▼                  ▼                          │                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │                                    │
│  │RoleAppMapping│  │RoleFeature   │  │  UserRoleAssignment     │   │                                    │
│  │              │  │Mapping       │  │                         │   │                                    │
│  ├──────────────┤  ├──────────────┤  ├─────────────────────────┤   │                                    │
│  │ PK id        │  │ PK id        │  │ PK  id                  │   │                                    │
│  │    uuid      │  │    uuid      │  │     uuid                │   │                                    │
│  │ FK role_id   │  │ FK role_id   │  │ FK  user_id ────────────┼───┼──► User                           │
│  │ FK app_id    │  │ FK feature_id│  │ FK  role_id             │   │                                    │
│  │    can_view  │  │    can_view  │  │     is_primary          │   │                                    │
│  │    can_create│  │    can_create│  │     is_active           │   │                                    │
│  │    can_update│  │    can_update│  │     valid_from          │   │                                    │
│  │    can_delete│  │    can_delete│  │     valid_until         │   │                                    │
│  │    is_active │  │    is_active │  │ FK  assigned_by ────────┼───┼──► User                           │
│  │ FK assigned_by│ │ FK assigned_by│ │     created_at          │   │                                    │
│  │    created_at│  │    created_at│  │     updated_at          │   │                                    │
│  │    updated_at│  │    updated_at│  └─────────────────────────┘   │                                    │
│  └──────┬───────┘  └──────┬───────┘                                │                                    │
│         │                 │                                        │                                    │
│         │                 │                                        │                                    │
│         ▼                 │                                        │                                    │
│  ┌─────────────────────┐  │       ┌─────────────────────────┐      │                                    │
│  │        App          │  │       │     RoleHierarchy       │      │                                    │
│  ├─────────────────────┤  │       ├─────────────────────────┤      │                                    │
│  │ PK  id              │  │       │ PK  id                  │      │                                    │
│  │     uuid            │  │       │ FK  parent_role_id ─────┼──────┘                                    │
│  │     name (unique)   │  │       │ FK  child_role_id ──────┼──────► UserRole                          │
│  │     code (unique)   │  │       │     can_assign          │                                          │
│  │     description     │  │       │     can_revoke          │                                          │
│  │     icon            │  │       │     can_modify_perms    │                                          │
│  │     display_order   │  │       │     is_active           │                                          │
│  │     is_active       │  │       │ FK  created_by          │                                          │
│  │ FK  parent_app_id   │  │       │     created_at          │                                          │
│  │ FK  created_by      │  │       │     updated_at          │                                          │
│  │     created_at      │  │       └─────────────────────────┘                                          │
│  │     updated_at      │  │                                                                            │
│  └──────────┬──────────┘  │                                                                            │
│             │             │                                                                            │
│             │ 1:N         │                                                                            │
│             ▼             ▼                                                                            │
│  ┌─────────────────────────┐                                                                            │
│  │       Feature           │                                                                            │
│  ├─────────────────────────┤                                                                            │
│  │ PK  id                  │                                                                            │
│  │     uuid                │                                                                            │
│  │ FK  app_id              │                                                                            │
│  │     name                │                                                                            │
│  │     code                │                                                                            │
│  │     description         │                                                                            │
│  │     feature_type        │                                                                            │
│  │     display_order       │                                                                            │
│  │     is_active           │                                                                            │
│  │ FK  created_by          │                                                                            │
│  │     created_at          │                                                                            │
│  │     updated_at          │                                                                            │
│  └─────────────────────────┘                                                                            │
│                                                                                                         │
│  ┌─────────────────────────┐                                                                            │
│  │       AuditLog          │                                                                            │
│  ├─────────────────────────┤                                                                            │
│  │ PK  id                  │                                                                            │
│  │     uuid                │                                                                            │
│  │     action              │  (CREATE, UPDATE, DELETE, ASSIGN, REVOKE, etc.)                           │
│  │     entity_type         │  (USER_ROLE, APP, FEATURE, etc.)                                          │
│  │     entity_id           │                                                                            │
│  │     entity_uuid         │                                                                            │
│  │     description         │                                                                            │
│  │     old_values (JSON)   │                                                                            │
│  │     new_values (JSON)   │                                                                            │
│  │ FK  performed_by        │──────────────────────────────────────► User                               │
│  │     ip_address          │                                                                            │
│  │     user_agent          │                                                                            │
│  │     created_at          │                                                                            │
│  └─────────────────────────┘                                                                            │
│                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Tables Detail

### users_auth_user

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| uuid | UUID | UNIQUE | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| username | VARCHAR(150) | UNIQUE, NOT NULL | Username |
| password | VARCHAR(255) | NOT NULL | Hashed password |
| first_name | VARCHAR(100) | NULL | First name |
| last_name | VARCHAR(100) | NULL | Last name |
| phone_number | VARCHAR(20) | NULL | Phone number |
| profile_image | VARCHAR(255) | NULL | Profile image path |
| is_active | BOOLEAN | DEFAULT TRUE | Account active status |
| is_verified | BOOLEAN | DEFAULT FALSE | Email verified status |
| last_login | DATETIME | NULL | Last login timestamp |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Update timestamp |

### rbac_user_role

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| uuid | UUID | UNIQUE | Unique identifier |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Role name |
| code | VARCHAR(50) | UNIQUE, NOT NULL | Role code (e.g., DEVELOPER) |
| level | INTEGER | NOT NULL | Hierarchy level (1-5) |
| description | TEXT | NULL | Role description |
| is_system_role | BOOLEAN | DEFAULT FALSE | System role flag |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_by_id | INTEGER | FK → User | Creator |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Update timestamp |

### rbac_app

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| uuid | UUID | UNIQUE | Unique identifier |
| name | VARCHAR(100) | UNIQUE, NOT NULL | App name |
| code | VARCHAR(50) | UNIQUE, NOT NULL | App code |
| description | TEXT | NULL | App description |
| icon | VARCHAR(100) | NULL | Icon class/URL |
| display_order | INTEGER | DEFAULT 0 | Display order |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| parent_app_id | INTEGER | FK → App | Parent app |
| created_by_id | INTEGER | FK → User | Creator |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Update timestamp |

### rbac_feature

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| uuid | UUID | UNIQUE | Unique identifier |
| app_id | INTEGER | FK → App, NOT NULL | Parent app |
| name | VARCHAR(100) | NOT NULL | Feature name |
| code | VARCHAR(100) | NOT NULL | Feature code |
| description | TEXT | NULL | Feature description |
| feature_type | VARCHAR(20) | NOT NULL | Type (ACTION, VIEW, REPORT, SETTING) |
| display_order | INTEGER | DEFAULT 0 | Display order |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_by_id | INTEGER | FK → User | Creator |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Update timestamp |

**Unique Constraint:** (app_id, code)

### rbac_role_app_mapping

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| uuid | UUID | UNIQUE | Unique identifier |
| role_id | INTEGER | FK → UserRole, NOT NULL | Role |
| app_id | INTEGER | FK → App, NOT NULL | App |
| can_view | BOOLEAN | DEFAULT TRUE | View permission |
| can_create | BOOLEAN | DEFAULT FALSE | Create permission |
| can_update | BOOLEAN | DEFAULT FALSE | Update permission |
| can_delete | BOOLEAN | DEFAULT FALSE | Delete permission |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| assigned_by_id | INTEGER | FK → User | Assigner |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Update timestamp |

**Unique Constraint:** (role_id, app_id)

### rbac_role_feature_mapping

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| uuid | UUID | UNIQUE | Unique identifier |
| role_id | INTEGER | FK → UserRole, NOT NULL | Role |
| feature_id | INTEGER | FK → Feature, NOT NULL | Feature |
| can_view | BOOLEAN | DEFAULT TRUE | View permission |
| can_create | BOOLEAN | DEFAULT FALSE | Create permission |
| can_update | BOOLEAN | DEFAULT FALSE | Update permission |
| can_delete | BOOLEAN | DEFAULT FALSE | Delete permission |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| assigned_by_id | INTEGER | FK → User | Assigner |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Update timestamp |

**Unique Constraint:** (role_id, feature_id)

### rbac_user_role_assignment

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| uuid | UUID | UNIQUE | Unique identifier |
| user_id | INTEGER | FK → User, NOT NULL | User |
| role_id | INTEGER | FK → UserRole, NOT NULL | Role |
| is_primary | BOOLEAN | DEFAULT FALSE | Primary role flag |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| valid_from | DATETIME | DEFAULT NOW | Validity start |
| valid_until | DATETIME | NULL | Validity end |
| assigned_by_id | INTEGER | FK → User | Assigner |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Update timestamp |

### rbac_role_hierarchy

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| parent_role_id | INTEGER | FK → UserRole, NOT NULL | Parent role |
| child_role_id | INTEGER | FK → UserRole, NOT NULL | Child role |
| can_assign | BOOLEAN | DEFAULT TRUE | Can assign child role |
| can_revoke | BOOLEAN | DEFAULT TRUE | Can revoke child role |
| can_modify_permissions | BOOLEAN | DEFAULT FALSE | Can modify permissions |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_by_id | INTEGER | FK → User | Creator |
| created_at | DATETIME | AUTO | Creation timestamp |
| updated_at | DATETIME | AUTO | Update timestamp |

**Unique Constraint:** (parent_role_id, child_role_id)

### rbac_audit_log

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Primary key |
| uuid | UUID | UNIQUE | Unique identifier |
| action | VARCHAR(20) | NOT NULL | Action type |
| entity_type | VARCHAR(50) | NOT NULL | Entity type |
| entity_id | INTEGER | NOT NULL | Entity ID |
| entity_uuid | UUID | NULL | Entity UUID |
| description | TEXT | NOT NULL | Change description |
| old_values | JSON | NULL | Previous values |
| new_values | JSON | NULL | New values |
| performed_by_id | INTEGER | FK → User | Performer |
| ip_address | VARCHAR(45) | NULL | IP address |
| user_agent | TEXT | NULL | User agent |
| created_at | DATETIME | AUTO | Creation timestamp |

---

## Role Levels

| Level | Role | Description |
|-------|------|-------------|
| 1 | Developer | Full system access |
| 2 | Super Admin | Full admin access |
| 3 | Admin | Limited app/feature access |
| 4 | Client | Portal access |
| 5 | End User | Basic access |

---

*Last Updated: November 28, 2025*
