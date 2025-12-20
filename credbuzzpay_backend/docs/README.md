# CredBuzz Backend - Project Documentation

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Apps Structure](#apps-structure)
4. [Installation](#installation)
5. [API Reference](#api-reference)
6. [Authentication](#authentication)
7. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)

---

## 🚀 Project Overview

**CredBuzz Backend** is a Django REST Framework-based backend system that provides:

- **User Authentication System** - Custom user management with JWT authentication
- **Role-Based Access Control (RBAC)** - Multi-level permission system for enterprise applications

### Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 5.2.8 |
| API | Django REST Framework 3.16.1 |
| Authentication | Custom JWT (PyJWT 2.10.1) |
| Database | SQLite (Development) / PostgreSQL (Production) |
| Python | 3.12.6 |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CredBuzz Backend                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐          ┌─────────────────────────────┐  │
│  │   users_auth    │◄────────►│           rbac              │  │
│  │                 │          │                             │  │
│  │  • User Model   │          │  • UserRole                 │  │
│  │  • JWT Auth     │          │  • App                      │  │
│  │  • Registration │          │  • Feature                  │  │
│  │  • Login/Logout │          │  • RoleAppMapping           │  │
│  │  • Password     │          │  • RoleFeatureMapping       │  │
│  │    Reset        │          │  • UserRoleAssignment       │  │
│  │  • Sessions     │          │  • RoleHierarchy            │  │
│  │                 │          │  • AuditLog                 │  │
│  └─────────────────┘          └─────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### App Dependencies

```
rbac ──depends on──► users_auth
  │
  ├── Uses User model for role assignments
  ├── Uses JWTAuthentication for API security
  └── Tracks user actions in audit logs
```

---

## 📁 Apps Structure

### 1. `users_auth` - User Authentication App

Handles all user-related operations without using Django's AbstractUser.

**Models:**
- `User` - Custom user model with email, username, password
- `PasswordResetToken` - Password reset token management
- `UserSession` - User session tracking

**Features:**
- ✅ User Registration
- ✅ User Login with JWT tokens
- ✅ User Logout
- ✅ Password Reset (Forgot Password)
- ✅ User CRUD operations
- ✅ Token refresh mechanism

### 2. `rbac` - Role-Based Access Control App

Implements a hierarchical 5-level permission system.

**Models:**
- `UserRole` - Role definitions with hierarchy levels
- `App` - Application/module definitions
- `Feature` - Features within apps
- `RoleAppMapping` - Role to app permissions
- `RoleFeatureMapping` - Role to feature permissions
- `UserRoleAssignment` - User to role assignments
- `RoleHierarchy` - Custom role delegation
- `AuditLog` - Change tracking

**Role Hierarchy:**
```
Level 1: Developer      → Full system access (code, deploy, all features)
Level 2: Super Admin    → Full admin access (no code access)
Level 3: Admin          → Limited app/feature access (assigned by Super Admin)
Level 4: Client         → Portal access (assigned by Admin)
Level 5: End User       → Basic access (assigned by Client)
```

---

## 🔧 Installation

### Prerequisites
- Python 3.12+
- pip
- virtualenv (recommended)

### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/het875/credbuzz-backend.git
cd credbuzz-backend/credbuzzpay_backend

# 2. Create virtual environment
python -m venv ../credbuzz_backend_venv

# 3. Activate virtual environment
# Windows:
..\credbuzz_backend_venv\Scripts\activate
# Linux/Mac:
source ../credbuzz_backend_venv/bin/activate

# 4. Install dependencies
pip install django djangorestframework pyjwt python-dotenv pillow django-cors-headers

# 5. Run migrations
python manage.py migrate

# 6. Initialize default roles
python manage.py init_roles

# 7. Run development server
python manage.py runserver
```

---

## 📚 API Reference

### Base URL
```
http://127.0.0.1:8000/api/
```

### Authentication Endpoints (`/api/auth-user/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register/` | Register new user |
| POST | `/login/` | User login |
| POST | `/logout/` | User logout |
| POST | `/refresh-token/` | Refresh JWT token |
| POST | `/forgot-password/` | Request password reset |
| POST | `/reset-password/` | Reset password with token |
| GET | `/users/` | List all users |
| GET | `/users/<id>/` | Get user details |
| PUT | `/users/<id>/` | Update user |
| DELETE | `/users/<id>/` | Delete user |
| GET | `/me/` | Get current user profile |
| PUT | `/me/` | Update current user profile |

### RBAC Endpoints (`/api/rbac/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Roles** |||
| GET | `/roles/` | List all roles |
| POST | `/roles/` | Create new role |
| GET | `/roles/<id>/` | Get role details |
| PUT | `/roles/<id>/` | Update role |
| DELETE | `/roles/<id>/` | Delete role |
| **Apps** |||
| GET | `/apps/` | List all apps |
| POST | `/apps/` | Create new app |
| GET | `/apps/<id>/` | Get app details |
| PUT | `/apps/<id>/` | Update app |
| DELETE | `/apps/<id>/` | Delete app |
| **Features** |||
| GET | `/features/` | List all features |
| POST | `/features/` | Create new feature |
| GET | `/features/<id>/` | Get feature details |
| PUT | `/features/<id>/` | Update feature |
| DELETE | `/features/<id>/` | Delete feature |
| **Mappings** |||
| GET | `/role-app-mappings/` | List role-app mappings |
| POST | `/role-app-mappings/` | Assign app to role |
| POST | `/role-app-mappings/bulk/` | Bulk assign apps |
| GET | `/role-feature-mappings/` | List role-feature mappings |
| POST | `/role-feature-mappings/` | Assign feature to role |
| POST | `/role-feature-mappings/bulk/` | Bulk assign features |
| **Assignments** |||
| GET | `/user-role-assignments/` | List user assignments |
| POST | `/user-role-assignments/` | Assign role to user |
| POST | `/user-role-assignments/bulk/` | Bulk assign role to users |
| **Permissions** |||
| GET | `/check-permission/` | Check specific permission |
| GET | `/my-permissions/` | Get current user permissions |
| **Audit** |||
| GET | `/audit-logs/` | List audit logs |

---

## 🔐 Authentication

### JWT Token Structure

The system uses custom JWT tokens with the following claims:

```json
{
  "user_id": 1,
  "email": "user@example.com",
  "token_type": "access",
  "jti": "unique-token-id",
  "exp": 1732867200,
  "iat": 1732863600
}
```

### Token Expiry
- **Access Token**: 60 minutes
- **Refresh Token**: 7 days

### Usage

Include the JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## 🛡️ Role-Based Access Control (RBAC)

### How It Works

1. **Users** are assigned **Roles**
2. **Roles** have **Apps** and **Features** mapped to them
3. Each mapping includes CRUD permissions (can_view, can_create, can_update, can_delete)
4. Higher-level roles can manage lower-level roles

### Permission Hierarchy

```
Developer (Level 1)
    │
    ├── Can do everything
    ├── Create/manage all roles, apps, features
    └── Access audit logs
    
Super Admin (Level 2)
    │
    ├── Manage Admin, Client, End User roles
    ├── Create/manage apps and features
    └── View audit logs
    
Admin (Level 3)
    │
    ├── Manage Client and End User roles
    ├── Access assigned apps/features only
    └── View own audit logs
    
Client (Level 4)
    │
    ├── Manage End User roles (limited)
    ├── Access portal apps/features
    └── View own data
    
End User (Level 5)
    │
    └── Access assigned features only
```

### Example: Checking Permission

```python
from rbac.permissions import has_app_permission, has_feature_permission

# Check if user has view permission on USER_MGMT app
if has_app_permission(user, 'USER_MGMT', 'view'):
    # User can view the app
    pass

# Check if user has create permission on CREATE_USER feature
if has_feature_permission(user, 'USER_MGMT', 'CREATE_USER', 'create'):
    # User can create users
    pass
```

---

## 📊 Database Schema

See [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for detailed ERD and table structures.

---

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run users_auth tests
python manage.py test users_auth

# Run rbac tests
python manage.py test rbac

# Run with verbosity
python manage.py test --verbosity=2
```

### Test Coverage
- **users_auth**: 24 tests
- **rbac**: 45 tests
- **Total**: 69 tests ✅

---

## 📝 License

This project is proprietary software owned by CredBuzz.

---

## 👥 Contributors

- Development Team @ CredBuzz

---

*Last Updated: November 28, 2025*
