# CredBuzz User Creation Guide

This guide explains how to create users with different roles in the CredBuzz system.

---

## Table of Contents

1. [User Role Hierarchy](#user-role-hierarchy)
2. [User Fields Overview](#user-fields-overview)
3. [Creating a Developer](#creating-a-developer)
4. [Creating a Super Admin](#creating-a-super-admin)
5. [Creating an Admin](#creating-an-admin)
6. [Creating a Client](#creating-a-client)
7. [Creating an End User](#creating-an-end-user)
8. [User Code System](#user-code-system)
9. [Quick Reference](#quick-reference)

---

## User Role Hierarchy

CredBuzz uses a hierarchical role system where higher-level roles can create and manage lower-level roles:

```
Level 1: DEVELOPER         (System developer - highest privileges)
    │
    └── Level 2: SUPER_ADMIN   (Created by Developer)
            │
            └── Level 3: ADMIN         (Role assigned by Super Admin)
                    │
                    └── Level 4: CLIENT        (Role assigned by Admin+)
                            │
                            └── Level 5: END_USER      (Default role)
```

### Role Capabilities

| Role | Can Create/Manage | Special Privileges |
|------|-------------------|-------------------|
| DEVELOPER | Super Admin | Full system access, database access |
| SUPER_ADMIN | Admin, Client, End User | Full app access, role management |
| ADMIN | Client, End User | App management, limited role assignment |
| CLIENT | End User | Client-specific features |
| END_USER | None | Basic user access |

---

## User Fields Overview

Every user in the system has these key fields:

| Field | Description | Auto-Generated? |
|-------|-------------|-----------------|
| `email` | Unique email address | No |
| `username` | Unique username | No |
| `user_code` | 6-character unique identifier (e.g., ABC123) | Yes |
| `user_role` | Role in the system | Yes (defaults to END_USER) |
| `is_verified` | Email verification status | Depends on creation method |

---

## Creating a Developer

**Method:** Management Command (CLI only)

**Prerequisites:** 
- Access to server terminal
- Django management command access

### Interactive Mode

```bash
# Activate virtual environment first
cd /path/to/credbuzzpay_backend
source ../credbuzz_backend_venv/bin/activate  # Linux/Mac
# OR
..\credbuzz_backend_venv\Scripts\Activate.ps1  # Windows PowerShell

# Run the command
python manage.py create_developer
```

The command will interactively prompt for:
- Email address
- Username
- Password (with confirmation)
- First name
- Last name

### Non-Interactive Mode (Scripted)

```bash
python manage.py create_developer \
    --email=dev@credbuzz.com \
    --username=developer \
    --password=SecurePass@123 \
    --first-name=System \
    --last-name=Developer \
    --noinput
```

### Example Output

```
============================================================
   CREDBUZZ - DEVELOPER USER CREATION
============================================================

⚠️  WARNING: Developer is the highest privilege role!
A Developer can:
  - Access all system configurations
  - Create Super Admin users
  - Access database directly
  - Manage all system components

--- Developer Details ---
Developer Email: dev@credbuzz.com
Developer Username: developer
...

============================================================
   ✅ DEVELOPER USER CREATED SUCCESSFULLY!
============================================================

   User Code:  CGX0R0
   Email:      dev@credbuzz.com
   Username:   developer
   Role:       Developer
```

---

## Creating a Super Admin

**Method:** Management Command (CLI only)

**Prerequisites:** 
- Valid Developer credentials
- Access to server terminal

### Interactive Mode

```bash
python manage.py create_superadmin
```

The command will prompt for:
1. **Developer Authorization**
   - Developer email
   - Developer password

2. **Super Admin Details**
   - Email address
   - Username
   - Password (with confirmation)
   - First name
   - Last name

### Non-Interactive Mode (Scripted)

```bash
python manage.py create_superadmin \
    --dev-email=dev@credbuzz.com \
    --dev-password=Developer@123 \
    --email=superadmin@credbuzz.com \
    --username=superadmin \
    --password=SuperAdmin@123 \
    --first-name=Super \
    --last-name=Admin \
    --noinput
```

### Example Output

```
============================================================
   CREDBUZZ - SUPER ADMIN USER CREATION
============================================================

🔐 Developer authorization required to create Super Admin.

--- Developer Authorization ---
Developer Email: dev@credbuzz.com
Developer Password: ********
✓ Authorized as: System Developer

--- Super Admin Details ---
...

============================================================
   ✅ SUPER ADMIN USER CREATED SUCCESSFULLY!
============================================================

   User Code:  VYO541
   Email:      superadmin@credbuzz.com
   Username:   superadmin
   Role:       Super Admin
```

---

## Creating an Admin

**Method:** API (Two-step process)

**Prerequisites:** 
- Super Admin authentication token

### Step 1: User Registration

The user registers normally via the API:

```http
POST /api/users/register/
Content-Type: application/json

{
    "email": "admin@company.com",
    "username": "admin_user",
    "password": "SecurePass@123",
    "confirm_password": "SecurePass@123",
    "first_name": "John",
    "last_name": "Smith"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "User registered successfully",
    "data": {
        "user": {
            "id": 3,
            "email": "admin@company.com",
            "username": "admin_user",
            "user_code": "XK9M2P",
            "user_role": "END_USER"
        }
    }
}
```

### Step 2: Assign Admin Role (Super Admin Required)

Super Admin assigns the ADMIN role:

```http
POST /api/rbac/role-assignments/
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
    "user": 3,
    "role": 3,  // ADMIN role ID
    "is_primary": true
}
```

**Response:**
```json
{
    "id": 1,
    "user": 3,
    "role": 3,
    "is_primary": true,
    "assigned_by": 2,
    "assigned_at": "2025-01-20T10:30:00Z"
}
```

### Step 3: Update User Role Field (Optional but Recommended)

```http
PATCH /api/users/3/
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
    "user_role": "ADMIN"
}
```

---

## Creating a Client

**Method:** API (Two-step process)

**Prerequisites:** 
- Admin or Super Admin authentication token

### Step 1: User Registration

Same as Admin creation - user registers via API.

### Step 2: Assign Client Role (Admin+ Required)

Admin or Super Admin assigns the CLIENT role:

```http
POST /api/rbac/role-assignments/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
    "user": 4,
    "role": 4,  // CLIENT role ID
    "is_primary": true
}
```

### Step 3: Update User Role Field

```http
PATCH /api/users/4/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
    "user_role": "CLIENT"
}
```

---

## Creating an End User

**Method:** API (Self-registration)

**Prerequisites:** None

End Users are created through the normal registration process:

```http
POST /api/users/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "username": "enduser",
    "password": "UserPass@123",
    "confirm_password": "UserPass@123",
    "first_name": "Jane",
    "last_name": "Doe"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "User registered successfully",
    "data": {
        "user": {
            "id": 5,
            "email": "user@example.com",
            "username": "enduser",
            "user_code": "M3N7K2",
            "user_role": "END_USER"
        }
    }
}
```

The user is automatically assigned:
- `user_role`: END_USER (default)
- `user_code`: Auto-generated 6-character code
- `is_verified`: false (requires email verification)

---

## User Code System

### Format
- 6 characters alphanumeric (uppercase)
- Examples: `CGX0R0`, `VYO541`, `M3N7K2`

### Auto-Generation
User codes are automatically generated when:
- A user is created via management command
- A user registers via API
- A user is created programmatically without providing a user_code

### Custom User Code
You can also specify a custom user code (minimum 5 characters):

```python
user = User(
    email="test@example.com",
    username="testuser",
    user_code="CUST001"  # Custom code
)
user.save()
```

### Uniqueness
- Each user_code is unique across the system
- The system verifies uniqueness before saving
- Collision handling: regenerates if duplicate detected

---

## Quick Reference

### Management Commands Summary

| Command | Creates | Authorization Required |
|---------|---------|----------------------|
| `create_developer` | Developer user | Server access only |
| `create_superadmin` | Super Admin user | Developer credentials |

### API Endpoints Summary

| Action | Endpoint | Method | Auth Required |
|--------|----------|--------|---------------|
| Register (any user) | `/api/users/register/` | POST | None |
| Get user details | `/api/users/{id}/` | GET | Token |
| Update user role | `/api/users/{id}/` | PATCH | Admin+ Token |
| Assign RBAC role | `/api/rbac/role-assignments/` | POST | Admin+ Token |

### Role IDs (Default)

| Role | ID | Code |
|------|-----|------|
| Developer | 1 | DEVELOPER |
| Super Admin | 2 | SUPER_ADMIN |
| Admin | 3 | ADMIN |
| Client | 4 | CLIENT |
| End User | 5 | END_USER |

### Test Accounts (Development)

| Role | Email | Username | Password | User Code |
|------|-------|----------|----------|-----------|
| Developer | dev@credbuzz.com | developer | Developer@123 | CGX0R0 |
| Super Admin | superadmin@credbuzz.com | superadmin | SuperAdmin@123 | VYO541 |

---

## Troubleshooting

### "Super Admin role not found"
Run `python manage.py init_roles` to initialize all RBAC roles.

### "Developer not found" when creating Super Admin
Ensure a Developer user exists. Create one using `python manage.py create_developer`.

### "Invalid developer credentials"
Check the Developer email and password are correct.

### User code collision
The system automatically handles this by regenerating codes. If persistent issues occur, check the database for duplicate entries.

---

## Security Best Practices

1. **Never share Developer credentials** - Only trusted system administrators should have Developer access.

2. **Use strong passwords** - All management commands enforce:
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one digit

3. **Limit Super Admin creation** - Only create Super Admins when absolutely necessary.

4. **Audit user creation** - Check `UserRoleAssignment.assigned_by` to track who created which users.

5. **Rotate Developer accounts** - Periodically update Developer credentials for security.
