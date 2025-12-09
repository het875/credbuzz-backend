# API Documentation - CredBuzz Backend

## Overview

This document provides detailed API documentation for all endpoints in the CredBuzz Backend system.

---

## Base URL

```
Development: http://127.0.0.1:8000/api/
Production: https://api.credbuzz.com/api/
```

---

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## Response Format

All API responses follow this standard format:

### Success Response
```json
{
    "success": true,
    "message": "Success message",
    "data": { ... }
}
```

### Error Response
```json
{
    "success": false,
    "message": "Error message",
    "errors": { ... }
}
```

---

# Users Auth API (`/api/auth/`)

## 1. Register User

**POST** `/api/auth/register/`

Creates a new user account.

### Request Body
```json
{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
}
```

### Response (201 Created)
```json
{
    "success": true,
    "message": "User registered successfully",
    "data": {
        "id": 1,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe",
        "created_at": "2025-11-28T10:00:00Z"
    }
}
```

---

## 2. Login

**POST** `/api/auth/login/`

Authenticates user and returns JWT tokens with permissions.

### Dynamic Identifier Login

The login uses a **single `identifier` field** that auto-detects the type:
- **Email** - Contains `@` (e.g., `user@example.com`)
- **Phone** - Starts with `+` or is numeric (e.g., `+1234567890`)
- **User Code** - Exactly 6 alphanumeric characters (e.g., `ABC123`)
- **Username** - Default fallback for other formats

### Request Body
```json
{
    "identifier": "user@example.com",
    "password": "SecurePass123!"
}
```

### Login Examples

**Login with Email:**
```json
{
    "identifier": "user@example.com",
    "password": "SecurePass123!"
}
```

**Login with Username:**
```json
{
    "identifier": "johndoe",
    "password": "SecurePass123!"
}
```

**Login with User Code:**
```json
{
    "identifier": "ABC123",
    "password": "SecurePass123!"
}
```

**Login with Phone Number:**
```json
{
    "identifier": "+1234567890",
    "password": "SecurePass123!"
}
```

### Response (200 OK)
```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "user": {
            "id": 1,
            "email": "user@example.com",
            "username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "user_code": "ABC123",
            "user_role": "ADMIN"
        },
        "tokens": {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "access_token_expiry": "2025-11-28T11:00:00Z",
            "refresh_token_expiry": "2025-12-05T10:00:00Z"
        },
        "app_access": [1, 2, 5, 6],
        "feature_access": [1, 2, 3, 4, 5],
        "session": {
            "session_id": "abc123...",
            "expires_at": "2025-12-05T10:00:00Z",
            "inactivity_timeout_minutes": 30
        }
    }
}
```

### Security Features

#### Progressive Lockout

Failed login attempts trigger a progressive lockout system:

| Stage | Failed Attempts | Lockout Duration |
|-------|-----------------|------------------|
| 0 | 1-5 | No lockout |
| 1 | 6 | 2 minutes |
| 2 | 11 | 5 minutes |
| 3 | 16 | 10 minutes |
| 4 | 21 | 30 minutes |
| 5 | 26 | 60 minutes |
| 6 | 31+ | Permanently blocked |

#### Failed Login Response (401 Unauthorized)
```json
{
    "success": false,
    "message": "Invalid credentials",
    "data": {
        "remaining_attempts": 4,
        "lockout_stage": 0,
        "is_locked": false
    }
}
```

#### Locked Out Response (429 Too Many Requests)
```json
{
    "success": false,
    "message": "Account locked. Try again in 2 minutes",
    "data": {
        "is_locked": true,
        "lockout_remaining_seconds": 120,
        "lockout_stage": 1
    }
}
```

#### Blocked Account Response (403 Forbidden)
```json
{
    "success": false,
    "message": "Account is blocked due to too many failed attempts. Contact support.",
    "data": {
        "is_blocked": true
    }
}
```

### Session Inactivity Timeout

Sessions automatically expire after 30 minutes of inactivity (configurable via `JWT_INACTIVITY_TIMEOUT_MINUTES` setting). This works like bank app security - if you don't make any API requests for 30 minutes, your session expires.

### JWT Token Payload

The access token includes these claims for use in middleware:
```json
{
    "user_id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "user_code": "ABC123",
    "user_role": "ADMIN",
    "full_name": "John Doe",
    "app_access": [1, 2, 5, 6],
    "feature_access": [1, 2, 3, 4, 5],
    "token_type": "access",
    "inactivity_timeout_minutes": 30,
    "jti": "unique-token-id",
    "iat": 1732791600,
    "exp": 1732795200
}
```

---

## 3. Logout

**POST** `/api/auth/logout/`

🔒 **Requires Authentication**

Invalidates the current session.

### Request Headers
```
Authorization: Bearer <access_token>
```

### Request Body
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Response (200 OK)
```json
{
    "success": true,
    "message": "Logout successful"
}
```

---

## 4. Refresh Token

**POST** `/api/auth/refresh-token/`

Gets a new access token using refresh token.

### Request Body
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Response (200 OK)
```json
{
    "success": true,
    "message": "Token refreshed successfully",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access_token_expiry": "2025-11-28T12:00:00Z"
    }
}
```

---

## 5. Forgot Password

**POST** `/api/auth/forgot-password/`

Sends password reset token to user's email.

### Request Body
```json
{
    "email": "user@example.com"
}
```

### Response (200 OK)
```json
{
    "success": true,
    "message": "Password reset token sent to email",
    "data": {
        "token": "abc123def456..."
    }
}
```

---

## 6. Reset Password

**POST** `/api/auth/reset-password/`

Resets password using the reset token.

### Request Body
```json
{
    "token": "abc123def456...",
    "new_password": "NewSecurePass123!",
    "confirm_password": "NewSecurePass123!"
}
```

### Response (200 OK)
```json
{
    "success": true,
    "message": "Password reset successful"
}
```

---

## 7. List Users

**GET** `/api/auth/users/`

🔒 **Requires Authentication**

Returns list of all users.

### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number |
| limit | int | Items per page |

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": [
        {
            "id": 1,
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": true,
            "created_at": "2025-11-28T10:00:00Z"
        }
    ]
}
```

---

## 8. Get User Details

**GET** `/api/auth/users/{id}/`

🔒 **Requires Authentication**

Returns details of a specific user.

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": {
        "id": 1,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
        "is_active": true,
        "is_verified": true,
        "created_at": "2025-11-28T10:00:00Z",
        "updated_at": "2025-11-28T10:00:00Z"
    }
}
```

---

## 9. Update User

**PUT** `/api/auth/users/{id}/`

🔒 **Requires Authentication**

Updates user information.

### Request Body
```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "+9876543210"
}
```

### Response (200 OK)
```json
{
    "success": true,
    "message": "User updated successfully",
    "data": {
        "id": 1,
        "email": "user@example.com",
        "username": "johndoe",
        "first_name": "Jane",
        "last_name": "Smith",
        "phone_number": "+9876543210"
    }
}
```

---

## 10. Delete User

**DELETE** `/api/auth/users/{id}/`

🔒 **Requires Authentication**

Deletes a user account.

### Response (200 OK)
```json
{
    "success": true,
    "message": "User deleted successfully"
}
```

---

## 11. Get Current User Profile

**GET** `/api/auth/me/`

🔒 **Requires Authentication**

Returns the authenticated user's profile.

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": {
        "id": 1,
        "email": "user@example.com",
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890"
    }
}
```

---

# RBAC API (`/api/rbac/`)

## Roles

### 1. List Roles

**GET** `/api/rbac/roles/`

🔒 **Requires Authentication**

Returns list of all user roles.

### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| level | int | Filter by hierarchy level (1-5) |

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": [
        {
            "id": 1,
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Developer",
            "code": "DEVELOPER",
            "level": 1,
            "level_display": "Developer",
            "description": "Full system access",
            "is_system_role": true,
            "is_active": true,
            "users_count": 2,
            "created_at": "2025-11-28T10:00:00Z"
        }
    ]
}
```

---

### 2. Create Role

**POST** `/api/rbac/roles/`

🔒 **Requires Authentication** (Super Admin or above)

Creates a new user role.

### Request Body
```json
{
    "name": "Custom Manager",
    "code": "CUSTOM_MANAGER",
    "level": 3,
    "description": "Custom manager role",
    "is_system_role": false
}
```

### Response (201 Created)
```json
{
    "success": true,
    "message": "Role created successfully",
    "data": {
        "id": 6,
        "uuid": "...",
        "name": "Custom Manager",
        "code": "CUSTOM_MANAGER",
        "level": 3,
        "level_display": "Admin",
        "description": "Custom manager role",
        "is_system_role": false,
        "is_active": true
    }
}
```

---

### 3. Get Role Details

**GET** `/api/rbac/roles/{id}/`

🔒 **Requires Authentication**

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": {
        "id": 1,
        "uuid": "...",
        "name": "Developer",
        "code": "DEVELOPER",
        "level": 1,
        "level_display": "Developer",
        "description": "Full system access",
        "is_system_role": true,
        "is_active": true,
        "users_count": 2,
        "apps": [
            {
                "id": 1,
                "name": "User Management",
                "code": "USER_MGMT",
                "can_view": true,
                "can_create": true,
                "can_update": true,
                "can_delete": true
            }
        ],
        "features": [
            {
                "id": 1,
                "name": "Create User",
                "code": "CREATE_USER",
                "app_name": "User Management",
                "can_view": true,
                "can_create": true,
                "can_update": true,
                "can_delete": true
            }
        ]
    }
}
```

---

## Apps

### 4. List Apps

**GET** `/api/rbac/apps/`

🔒 **Requires Authentication**

### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| parent_id | int | Filter by parent app ID |
| root_only | bool | Get only root apps (no parent) |

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": [
        {
            "id": 1,
            "uuid": "...",
            "name": "User Management",
            "code": "USER_MGMT",
            "description": "User management module",
            "icon": "fa-users",
            "display_order": 1,
            "is_active": true,
            "parent_app": null,
            "features_count": 5,
            "created_at": "2025-11-28T10:00:00Z"
        }
    ]
}
```

---

### 5. Create App

**POST** `/api/rbac/apps/`

🔒 **Requires Authentication** (Developer only)

### Request Body
```json
{
    "name": "Reports",
    "code": "REPORTS",
    "description": "Reporting module",
    "icon": "fa-chart-bar",
    "display_order": 5
}
```

---

## Features

### 6. List Features

**GET** `/api/rbac/features/`

🔒 **Requires Authentication**

### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| app_id | int | Filter by app ID |
| app_code | string | Filter by app code |

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": [
        {
            "id": 1,
            "uuid": "...",
            "app": 1,
            "app_name": "User Management",
            "name": "Create User",
            "code": "CREATE_USER",
            "description": "Create new users",
            "feature_type": "ACTION",
            "display_order": 1,
            "is_active": true
        }
    ]
}
```

---

### 7. Create Feature

**POST** `/api/rbac/features/`

🔒 **Requires Authentication** (Developer only)

### Request Body
```json
{
    "app": 1,
    "name": "Delete User",
    "code": "DELETE_USER",
    "description": "Delete users",
    "feature_type": "ACTION",
    "display_order": 4
}
```

---

## Role Mappings

### 8. Assign App to Role

**POST** `/api/rbac/role-app-mappings/`

🔒 **Requires Authentication** (Super Admin or above)

### Request Body
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

---

### 9. Bulk Assign Apps to Role

**POST** `/api/rbac/role-app-mappings/bulk/`

🔒 **Requires Authentication** (Super Admin or above)

### Request Body
```json
{
    "role_id": 3,
    "app_ids": [1, 2, 3],
    "can_view": true,
    "can_create": false,
    "can_update": false,
    "can_delete": false
}
```

---

### 10. Assign Feature to Role

**POST** `/api/rbac/role-feature-mappings/`

🔒 **Requires Authentication** (Super Admin or above)

### Request Body
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

---

## User Role Assignments

### 11. Assign Role to User

**POST** `/api/rbac/user-role-assignments/`

🔒 **Requires Authentication** (Admin or above)

### Request Body
```json
{
    "user": 5,
    "role": 4,
    "is_primary": true,
    "valid_from": "2025-11-28T00:00:00Z",
    "valid_until": "2026-11-28T00:00:00Z"
}
```

---

### 12. Bulk Assign Role to Users

**POST** `/api/rbac/user-role-assignments/bulk/`

🔒 **Requires Authentication** (Admin or above)

### Request Body
```json
{
    "user_ids": [5, 6, 7],
    "role_id": 4,
    "is_primary": false
}
```

---

## Permissions

### 13. Check Permission

**GET** `/api/rbac/check-permission/`

🔒 **Requires Authentication**

### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| app_code | string | App code to check |
| feature_code | string | Feature code to check |
| permission | string | Permission type (view, create, update, delete) |

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": {
        "has_permission": true,
        "app_code": "USER_MGMT",
        "feature_code": "CREATE_USER",
        "permission": "create"
    }
}
```

---

### 14. Get My Permissions

**GET** `/api/rbac/my-permissions/`

🔒 **Requires Authentication**

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": {
        "user_id": 1,
        "is_developer": false,
        "roles": [
            {
                "id": 3,
                "name": "Admin",
                "code": "ADMIN",
                "level": 3,
                "is_primary": true
            }
        ],
        "apps": [
            {
                "id": 1,
                "name": "User Management",
                "code": "USER_MGMT",
                "can_view": true,
                "can_create": true,
                "can_update": true,
                "can_delete": false
            }
        ],
        "features": [
            {
                "id": 1,
                "name": "Create User",
                "code": "CREATE_USER",
                "app_code": "USER_MGMT",
                "can_view": true,
                "can_create": true,
                "can_update": false,
                "can_delete": false
            }
        ]
    }
}
```

---

## Audit Logs

### 15. List Audit Logs

**GET** `/api/rbac/audit-logs/`

🔒 **Requires Authentication** (Super Admin or above)

### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| action | string | Filter by action (CREATE, UPDATE, DELETE, etc.) |
| entity_type | string | Filter by entity type |
| user_id | int | Filter by performer |
| limit | int | Max results (default: 100) |

### Response (200 OK)
```json
{
    "success": true,
    "message": "Success",
    "data": [
        {
            "id": 1,
            "uuid": "...",
            "action": "CREATE",
            "entity_type": "USER_ROLE",
            "entity_id": 6,
            "description": "Created role: Custom Manager",
            "old_values": null,
            "new_values": { "name": "Custom Manager", ... },
            "performed_by": 1,
            "performed_by_email": "admin@example.com",
            "ip_address": "127.0.0.1",
            "created_at": "2025-11-28T10:30:00Z"
        }
    ]
}
```

---

## Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Validation error |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 500 | Internal Server Error |

---

*Last Updated: November 28, 2025*
