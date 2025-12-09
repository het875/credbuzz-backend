# CredBuzz Backend - Complete API Documentation

## Overview

This document provides comprehensive documentation for all API endpoints in the CredBuzz Backend system.

**Base URL:** `http://127.0.0.1:8000/api`

**Authentication:** Most endpoints require JWT Bearer token authentication.

---

## Table of Contents

1. [User Registration & Authentication Flow](#1-user-registration--authentication-flow)
2. [Authentication APIs](#2-authentication-apis)
3. [OTP Verification APIs](#3-otp-verification-apis)
4. [User Profile APIs](#4-user-profile-apis)
5. [User Activity Log APIs](#5-user-activity-log-apis)
6. [KYC Verification APIs](#6-kyc-verification-apis)
7. [RBAC (Role-Based Access Control) APIs](#7-rbac-apis)
8. [Access Management APIs](#8-access-management-apis)
9. [Bill Pay APIs](#9-bill-pay-apis)

---

## Security Features (NEW)

### Rate Limiting
| Endpoint Type | Rate Limit |
|---------------|------------|
| Login | 10 requests/minute |
| Registration | 5 requests/hour |
| OTP | 5 requests/minute |
| KYC Uploads | 20 requests/hour |
| General APIs | 1000 requests/hour |

### Single Session Login
- When a user logs in on a new device, all previous sessions are invalidated
- Old sessions will receive 401 Unauthorized with message "Session has been invalidated"
- User must login again on old device

### Security Headers
- X-Frame-Options: DENY (prevents clickjacking)
- Content-Type-Nosniff: True (prevents MIME type sniffing)
- HTTPS enforced in production
- HSTS enabled with 1 year max-age

---

## 1. User Registration & Authentication Flow

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        USER REGISTRATION & KYC FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: Create Account                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /api/auth/register/                                             │   │
│  │ Body: first_name, middle_name, last_name, email, phone_number,       │   │
│  │       password, confirm_password                                     │   │
│  │ Response: User created + OTPs sent to email & phone                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  STEP 2: Verify OTPs                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /api/auth/verify-registration-otp/                              │   │
│  │ Body: email, otp_type (EMAIL/PHONE), otp_code                        │   │
│  │ (Repeat for both EMAIL and PHONE)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  STEP 3: Login                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /api/auth/login/                                                │   │
│  │ Body: identifier (email/username/phone/user_code), password          │   │
│  │ Response: access_token, refresh_token, app_access, feature_access    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  STEP 4: KYC Process (After Login)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4.1 Start KYC: POST /api/kyc/start/                                  │   │
│  │ 4.2 Aadhaar: POST /api/kyc/identity/aadhaar/                         │   │
│  │ 4.3 Aadhaar Upload: POST /api/kyc/identity/aadhaar/upload/           │   │
│  │ 4.4 PAN: POST /api/kyc/identity/pan/                                 │   │
│  │ 4.5 PAN Upload: POST /api/kyc/identity/pan/upload/                   │   │
│  │ 4.6 Business Details: POST /api/kyc/business/                        │   │
│  │ 4.7 Verification Images: POST /api/kyc/verification/selfie/          │   │
│  │ 4.8 Bank Details: POST /api/kyc/bank/                                │   │
│  │ 4.9 Submit: POST /api/kyc/submit/                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  STEP 5: Admin Review                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Admin reviews and approves/rejects via:                              │   │
│  │ POST /api/kyc/admin/applications/<id>/review/                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Authentication APIs

### 2.1 Register User

**Endpoint:** `POST /api/auth/register/`  
**Auth Required:** No

**Request Body:**
```json
{
    "first_name": "John",
    "middle_name": "K",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone_number": "9876543210",
    "password": "SecurePass@123",
    "confirm_password": "SecurePass@123"
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "message": "User registered successfully. Please verify your email and phone number with OTP.",
    "data": {
        "user": {
            "id": 1,
            "user_code": "ABC123",
            "email": "john@example.com",
            "username": "john",
            "first_name": "John",
            "middle_name": "K",
            "last_name": "Doe",
            "phone_number": "9876543210",
            "user_role": "END_USER",
            "is_verified": false,
            "is_email_verified": false,
            "is_phone_verified": false
        },
        "verification_required": {
            "email": true,
            "phone": true
        },
        "test_otps": {
            "email_otp": "123456",
            "phone_otp": "654321"
        }
    }
}
```

### 2.2 Login

**Endpoint:** `POST /api/auth/login/`  
**Auth Required:** No

**Request Body:**
```json
{
    "identifier": "john@example.com",
    "password": "SecurePass@123"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Login successful.",
    "data": {
        "user": {
            "id": 1,
            "user_code": "ABC123",
            "email": "john@example.com",
            "full_name": "John K Doe",
            "user_role": "END_USER"
        },
        "tokens": {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
        },
        "app_access": ["USER_MGMT", "REPORTS"],
        "feature_access": ["VIEW_PROFILE", "UPDATE_PROFILE"],
        "session": {
            "session_id": "...",
            "expires_at": "2024-12-06T10:00:00Z",
            "inactivity_timeout_minutes": 30
        }
    }
}
```

### 2.3 Logout

**Endpoint:** `POST /api/auth/logout/`  
**Auth Required:** Yes

**Request Body (Optional):**
```json
{
    "logout_all": true
}
```

### 2.4 Refresh Token

**Endpoint:** `POST /api/auth/refresh-token/`  
**Auth Required:** No

**Request Body:**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 2.5 Change Password

**Endpoint:** `POST /api/auth/change-password/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "current_password": "OldPass@123",
    "new_password": "NewPass@123",
    "confirm_password": "NewPass@123"
}
```

### 2.6 Forgot Password

**Endpoint:** `POST /api/auth/forgot-password/`  
**Auth Required:** No

**Request Body:**
```json
{
    "email": "john@example.com"
}
```

### 2.7 Reset Password

**Endpoint:** `POST /api/auth/reset-password/`  
**Auth Required:** No

**Request Body:**
```json
{
    "token": "reset_token_here",
    "new_password": "NewPass@123",
    "confirm_password": "NewPass@123"
}
```

---

## 3. OTP Verification APIs

### 3.1 Verify Registration OTP

**Endpoint:** `POST /api/auth/verify-registration-otp/`  
**Auth Required:** No

**Request Body:**
```json
{
    "email": "john@example.com",
    "otp_type": "EMAIL",
    "otp_code": "123456"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Email verified successfully.",
    "data": {
        "is_email_verified": true,
        "is_phone_verified": false,
        "is_fully_verified": false
    }
}
```

### 3.2 Resend Registration OTP

**Endpoint:** `POST /api/auth/resend-registration-otp/`  
**Auth Required:** No

**Request Body:**
```json
{
    "email": "john@example.com",
    "otp_type": "PHONE"
}
```

---

## 4. User Profile APIs

### 4.1 Get Basic Profile

**Endpoint:** `GET /api/auth/profile/`  
**Auth Required:** Yes

### 4.2 Update Basic Profile

**Endpoint:** `PATCH /api/auth/profile/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "first_name": "Johnny",
    "last_name": "Doe",
    "username": "johnnydoe"
}
```

### 4.3 Get Full Profile with KYC Status & Access

**Endpoint:** `GET /api/auth/profile-full/`  
**Auth Required:** Yes

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Profile retrieved successfully.",
    "data": {
        "id": 1,
        "user_code": "ABC123",
        "email": "john@example.com",
        "username": "john",
        "first_name": "John",
        "middle_name": "K",
        "last_name": "Doe",
        "full_name": "John K Doe",
        "phone_number": "9876543210",
        "user_role": "END_USER",
        "is_active": true,
        "is_verified": true,
        "is_email_verified": true,
        "is_phone_verified": true,
        "kyc_status": {
            "application_id": "KYC20241205ABC123",
            "status": "APPROVED",
            "mega_step": "COMPLETED",
            "current_step": 8,
            "total_steps": 8,
            "completion_percentage": 100,
            "submitted_at": "2024-12-05T10:00:00Z",
            "approved_at": "2024-12-05T12:00:00Z"
        },
        "app_access": [
            {
                "app_id": 1,
                "app_code": "USER_MGMT",
                "app_name": "User Management",
                "can_view": true,
                "can_create": false,
                "can_update": false,
                "can_delete": false
            }
        ],
        "feature_access": [
            {
                "feature_id": 1,
                "feature_code": "VIEW_PROFILE",
                "feature_name": "View Profile",
                "app_code": "USER_MGMT",
                "can_execute": true,
                "can_view": true,
                "can_edit": false
            }
        ]
    }
}
```

### 4.4 User List (Admin)

**Endpoint:** `GET /api/auth/users/`  
**Auth Required:** Yes (Admin+)

**Query Parameters:**
- `role` - Filter by role
- `is_active` - Filter by active status
- `search` - Search by email/username

### 4.5 Get User Detail

**Endpoint:** `GET /api/auth/users/<user_id>/`  
**Auth Required:** Yes (Admin+)

### 4.6 Update User

**Endpoint:** `PATCH /api/auth/users/<user_id>/`  
**Auth Required:** Yes (Admin+)

### 4.7 Soft Delete User

**Endpoint:** `DELETE /api/auth/users/<user_id>/`  
**Auth Required:** Yes (Admin+)

### 4.8 Hard Delete User

**Endpoint:** `DELETE /api/auth/users/<user_id>/hard-delete/`  
**Auth Required:** Yes (Super Admin+)

### 4.9 Restore User

**Endpoint:** `POST /api/auth/users/<user_id>/restore/`  
**Auth Required:** Yes (Admin+)

### 4.10 Activate/Deactivate User

**Endpoint:** `POST /api/auth/users/<user_id>/activate/`  
**Endpoint:** `POST /api/auth/users/<user_id>/deactivate/`  
**Auth Required:** Yes (Admin+)

---

## 5. User Activity Log APIs

### 5.1 Get Activity Logs

**Endpoint:** `GET /api/auth/activity-logs/`  
**Auth Required:** Yes (Admin+ for all logs, users can view own)

**Query Parameters:**
- `user_id` - Filter by user
- `activity_type` - Filter by activity type (LOGIN, LOGOUT, KYC_SUBMIT, etc.)
- `start_date` - Filter by start date (YYYY-MM-DD)
- `end_date` - Filter by end date
- `limit` - Limit results (default: 100)

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Activity logs retrieved successfully.",
    "data": {
        "logs": [
            {
                "id": 1,
                "user_id": 1,
                "user_email": "john@example.com",
                "user_code": "ABC123",
                "activity_type": "LOGIN",
                "action": "User logged in",
                "description": "",
                "entity_type": "",
                "entity_id": "",
                "ip_address": "127.0.0.1",
                "request_method": "POST",
                "request_path": "/api/auth/login/",
                "is_success": true,
                "created_at": "2024-12-05T10:00:00Z"
            }
        ],
        "count": 1
    }
}
```

### 5.2 Get My Activity

**Endpoint:** `GET /api/auth/my-activity/`  
**Auth Required:** Yes

**Query Parameters:**
- `activity_type` - Filter by activity type
- `limit` - Limit results (default: 50)

---

## 6. KYC Verification APIs

### 6.1 Get KYC Status

**Endpoint:** `GET /api/kyc/status/`  
**Auth Required:** Yes

### 6.2 Start KYC

**Endpoint:** `POST /api/kyc/start/`  
**Auth Required:** Yes

### 6.3 Get KYC Detail

**Endpoint:** `GET /api/kyc/detail/`  
**Auth Required:** Yes

### 6.4 Submit Aadhaar Details

**Endpoint:** `POST /api/kyc/identity/aadhaar/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "aadhaar_number": "123456789012",
    "aadhaar_name": "John Doe",
    "aadhaar_dob": "1990-01-15",
    "aadhaar_address": "123 Main Street, City, State - 123456"
}
```

### 6.5 Upload Aadhaar Images

**Endpoint:** `POST /api/kyc/identity/aadhaar/upload/`  
**Auth Required:** Yes  
**Content-Type:** multipart/form-data

**Form Data:**
- `aadhaar_front_image` - Aadhaar front image (JPG/PNG/PDF, max 5MB)
- `aadhaar_back_image` - Aadhaar back image (JPG/PNG/PDF, max 5MB)

### 6.6 Submit PAN Details

**Endpoint:** `POST /api/kyc/identity/pan/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "pan_number": "ABCDE1234F",
    "pan_name": "John Doe",
    "pan_dob": "1990-01-15"
}
```

### 6.7 Upload PAN Image

**Endpoint:** `POST /api/kyc/identity/pan/upload/`  
**Auth Required:** Yes  
**Content-Type:** multipart/form-data

**Form Data:**
- `pan_image` - PAN card image (JPG/PNG/PDF, max 5MB)

### 6.8 Submit Business Details

**Endpoint:** `POST /api/kyc/business/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "business_name": "ABC Enterprises",
    "business_phone": "9876543210",
    "business_email": "contact@abc.com",
    "address_line_1": "123 Business Park",
    "address_line_2": "Building A",
    "address_line_3": "Floor 5",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001"
}
```

### 6.9 Upload Verification Images

#### Selfie
**Endpoint:** `POST /api/kyc/verification/selfie/`  
**Form Data:** `selfie` - Selfie image (max 5MB)

#### Office Photos
**Endpoint:** `POST /api/kyc/verification/office/`  
**Form Data:**
- `office_sitting` - Photo of sitting at office
- `office_door` - Photo at office door

#### Address Proof
**Endpoint:** `POST /api/kyc/verification/address-proof/`  
**Form Data:** `address_proof` - Address proof document

### 6.10 Submit Bank Details

**Endpoint:** `POST /api/kyc/bank/`  
**Auth Required:** Yes

**Request Body (JSON or multipart):**
```json
{
    "account_holder_name": "John Doe",
    "account_number": "1234567890123456",
    "confirm_account_number": "1234567890123456",
    "ifsc_code": "SBIN0001234",
    "bank_name": "State Bank of India",
    "branch_name": "Main Branch",
    "branch_address": "123 Bank Street, City",
    "account_type": "SAVINGS"
}
```

### 6.11 Submit KYC for Review

**Endpoint:** `POST /api/kyc/submit/`  
**Auth Required:** Yes

### 6.12 Admin: List Applications

**Endpoint:** `GET /api/kyc/admin/applications/`  
**Auth Required:** Yes (Admin+)

**Query Parameters:**
- `status` - Filter by status (NOT_STARTED, IN_PROGRESS, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED)
- `search` - Search by application ID or user email

### 6.13 Admin: Get Application Detail

**Endpoint:** `GET /api/kyc/admin/applications/<application_id>/`  
**Auth Required:** Yes (Admin+)

### 6.14 Admin: Start Review

**Endpoint:** `POST /api/kyc/admin/applications/<application_id>/start-review/`  
**Auth Required:** Yes (Admin+)

### 6.15 Admin: Review (Approve/Reject/Request Resubmit)

**Endpoint:** `POST /api/kyc/admin/applications/<application_id>/review/`  
**Auth Required:** Yes (Admin+)

**Request Body:**
```json
{
    "action": "APPROVE",
    "remarks": "All documents verified successfully"
}
```

Or for rejection:
```json
{
    "action": "REJECT",
    "remarks": "Invalid PAN card image"
}
```

Or for resubmission:
```json
{
    "action": "RESUBMIT",
    "remarks": "Please upload clear Aadhaar back image"
}
```

---

## 7. RBAC APIs

### 7.1 List Roles

**Endpoint:** `GET /api/rbac/roles/`  
**Auth Required:** Yes

### 7.2 Get Role Detail

**Endpoint:** `GET /api/rbac/roles/<id>/`  
**Auth Required:** Yes

### 7.3 Create Role

**Endpoint:** `POST /api/rbac/roles/`  
**Auth Required:** Yes (Super Admin+)

### 7.4 List Apps

**Endpoint:** `GET /api/rbac/apps/`  
**Auth Required:** Yes

### 7.5 Create App

**Endpoint:** `POST /api/rbac/apps/`  
**Auth Required:** Yes (Super Admin+)

**Request Body:**
```json
{
    "name": "User Management",
    "code": "USER_MGMT",
    "description": "User management module"
}
```

### 7.6 List Features

**Endpoint:** `GET /api/rbac/features/`  
**Auth Required:** Yes

### 7.7 Create Feature

**Endpoint:** `POST /api/rbac/features/`  
**Auth Required:** Yes (Super Admin+)

**Request Body:**
```json
{
    "app_id": 1,
    "name": "Create User",
    "code": "CREATE_USER",
    "feature_type": "ACTION"
}
```

### 7.8 Role-App Mappings

**Endpoint:** `GET /api/rbac/role-app-mappings/`  
**Endpoint:** `POST /api/rbac/role-app-mappings/`  
**Endpoint:** `POST /api/rbac/role-app-mappings/bulk/`

### 7.9 Role-Feature Mappings

**Endpoint:** `GET /api/rbac/role-feature-mappings/`  
**Endpoint:** `POST /api/rbac/role-feature-mappings/`  
**Endpoint:** `POST /api/rbac/role-feature-mappings/bulk/`

### 7.10 User Role Assignments

**Endpoint:** `GET /api/rbac/user-role-assignments/`  
**Endpoint:** `POST /api/rbac/user-role-assignments/`  
**Endpoint:** `POST /api/rbac/user-role-assignments/bulk/`

### 7.11 Check Permission

**Endpoint:** `POST /api/rbac/check-permission/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "app_code": "USER_MGMT",
    "feature_code": "CREATE_USER",
    "permission": "can_execute"
}
```

### 7.12 Get My Permissions

**Endpoint:** `GET /api/rbac/my-permissions/`  
**Auth Required:** Yes

### 7.13 Audit Logs

**Endpoint:** `GET /api/rbac/audit-logs/`  
**Auth Required:** Yes (Admin+)

---

## 8. Access Management APIs

### 8.1 Get All Apps and Features (for SP/Developer)

**Endpoint:** `GET /api/rbac/all-access-items/`  
**Auth Required:** Yes (Admin+)

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Success",
    "data": {
        "apps": [
            {
                "app_id": 1,
                "app_code": "USER_MGMT",
                "app_name": "User Management",
                "app_description": "...",
                "features": [
                    {
                        "feature_id": 1,
                        "feature_code": "CREATE_USER",
                        "feature_name": "Create User",
                        "feature_type": "ACTION"
                    }
                ]
            }
        ],
        "roles": [
            {
                "role_id": 1,
                "role_code": "DEVELOPER",
                "role_name": "Developer",
                "role_level": 1,
                "is_system_role": true
            }
        ],
        "total_apps": 5,
        "total_features": 25,
        "total_roles": 5
    }
}
```

### 8.2 Get User Access Overview

**Endpoint:** `GET /api/rbac/users/<user_id>/access/`  
**Auth Required:** Yes (Admin+)

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Success",
    "data": {
        "user": {
            "id": 5,
            "user_code": "XYZ789",
            "email": "client@example.com",
            "full_name": "Client User",
            "user_role": "CLIENT",
            "is_verified": true
        },
        "roles": [
            {
                "role_id": 4,
                "role_code": "CLIENT",
                "role_name": "Client",
                "role_level": 4,
                "assigned_at": "2024-12-05T10:00:00Z"
            }
        ],
        "apps": [
            {
                "app_id": 1,
                "app_code": "USER_MGMT",
                "app_name": "User Management",
                "can_view": true,
                "can_create": false,
                "assigned_via_role": "Client"
            }
        ],
        "features": [...],
        "kyc_status": {
            "application_id": "KYC...",
            "status": "APPROVED"
        }
    }
}
```

### 8.3 Assign Access to User

**Endpoint:** `POST /api/rbac/users/<user_id>/assign-access/`  
**Auth Required:** Yes (Admin+)

**Request Body:**
```json
{
    "role_code": "ADMIN",
    "app_codes": ["USER_MGMT", "REPORTS"],
    "feature_codes": ["CREATE_USER", "VIEW_REPORT"]
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Access assigned successfully",
    "data": {
        "user_id": 5,
        "role_assigned": "Admin",
        "apps_assigned": ["User Management", "Reports"],
        "features_assigned": ["Create User", "View Report"]
    }
}
```

### 8.4 Revoke Access from User

**Endpoint:** `POST /api/rbac/users/<user_id>/revoke-access/`  
**Auth Required:** Yes (Admin+)

**Request Body:**
```json
{
    "role_code": "ADMIN",
    "revoke_all": false
}
```

Or revoke specific items:
```json
{
    "app_codes": ["REPORTS"],
    "feature_codes": ["CREATE_USER"]
}
```

Or revoke all:
```json
{
    "revoke_all": true
}
```

---

## Role Hierarchy

| Level | Role | Description | Can Manage |
|-------|------|-------------|------------|
| 1 | DEVELOPER | Full system access | All roles below |
| 2 | SUPER_ADMIN | Full app access | ADMIN, CLIENT, END_USER |
| 3 | ADMIN | Limited app access | CLIENT, END_USER |
| 4 | CLIENT | Portal access | END_USER |
| 5 | END_USER | Basic access | None |

---

## Error Response Format

All error responses follow this format:

```json
{
    "success": false,
    "message": "Error description",
    "errors": {
        "field_name": ["Error message 1", "Error message 2"]
    }
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Success |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Permission denied |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limited/locked out |
| 500 | Internal Server Error |

---

## Testing Checklist

### Registration Flow
1. ✅ Register new user with all required fields
2. ✅ Verify email OTP
3. ✅ Verify phone OTP
4. ✅ Login after verification

### KYC Flow
1. ✅ Start KYC process
2. ✅ Submit Aadhaar details
3. ✅ Upload Aadhaar images
4. ✅ Submit PAN details
5. ✅ Upload PAN image
6. ✅ Submit business details
7. ✅ Upload verification images (selfie, office, address proof)
8. ✅ Submit bank details
9. ✅ Submit KYC for review
10. ✅ Admin approves/rejects

### Access Management Flow
1. ✅ View all apps and features
2. ✅ Assign role to user
3. ✅ Assign specific apps/features
4. ✅ Revoke access
5. ✅ View user access overview

---

## Quick Start Examples

### Register and Login (PowerShell)

```powershell
# 1. Register
$body = @{
    first_name = "John"
    last_name = "Doe"
    email = "john@example.com"
    phone_number = "9876543210"
    password = "Test@1234"
    confirm_password = "Test@1234"
} | ConvertTo-Json

$register = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/register/" -Method POST -Body $body -ContentType "application/json"

# 2. Verify Email OTP
$verifyEmail = @{
    email = "john@example.com"
    otp_type = "EMAIL"
    otp_code = $register.data.test_otps.email_otp
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/verify-registration-otp/" -Method POST -Body $verifyEmail -ContentType "application/json"

# 3. Verify Phone OTP
$verifyPhone = @{
    email = "john@example.com"
    otp_type = "PHONE"
    otp_code = $register.data.test_otps.phone_otp
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/verify-registration-otp/" -Method POST -Body $verifyPhone -ContentType "application/json"

# 4. Login
$login = @{
    identifier = "john@example.com"
    password = "Test@1234"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method POST -Body $login -ContentType "application/json"

# Save token
$token = $loginResponse.data.tokens.access_token
$headers = @{ Authorization = "Bearer $token" }

# 5. Get Profile
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/profile-full/" -Method GET -Headers $headers
```

---

## 9. Bill Pay APIs

The Bill Pay module provides APIs for paying utility bills, recharges, and other payments.

### 9.1 List Bill Categories

**Endpoint:** `GET /api/bills/categories/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "Bill categories retrieved successfully.",
    "data": {
        "categories": [
            {"id": 1, "name": "Electricity", "code": "ELECTRICITY", "billers_count": 5},
            {"id": 2, "name": "Gas", "code": "GAS", "billers_count": 3}
        ]
    }
}
```

### 9.2 List Billers

**Endpoint:** `GET /api/bills/billers/`  
**Auth Required:** Yes

**Query Parameters:** `category_id`, `category_code`, `search`, `featured`

### 9.3 Get Biller Details

**Endpoint:** `GET /api/bills/billers/<biller_id>/`  
**Auth Required:** Yes

### 9.4 Fetch Bill

**Endpoint:** `POST /api/bills/fetch/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "biller_id": 1,
    "consumer_number": "1234567890"
}
```

### 9.5 Pay Bill

**Endpoint:** `POST /api/bills/pay/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "biller_id": 1,
    "consumer_number": "1234567890",
    "amount": 1500.00,
    "payment_method": "WALLET"
}
```

**Payment Methods:** `WALLET`, `UPI`, `CARD`, `NETBANKING`

### 9.6 Payment History

**Endpoint:** `GET /api/bills/history/`  
**Auth Required:** Yes

**Query Parameters:** `status`, `category_id`, `biller_id`, `start_date`, `end_date`, `page`, `page_size`

### 9.7 Payment Details

**Endpoint:** `GET /api/bills/payments/<transaction_id>/`  
**Auth Required:** Yes

### 9.8 Saved Billers

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bills/saved/` | GET | List saved billers |
| `/api/bills/saved/` | POST | Save a biller |
| `/api/bills/saved/<id>/` | GET | Get saved biller details |
| `/api/bills/saved/<id>/` | PUT | Update saved biller |
| `/api/bills/saved/<id>/` | DELETE | Remove saved biller |

### 9.9 Quick Access

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bills/featured/` | GET | Get featured billers |
| `/api/bills/recent/` | GET | Get recent payments |

**For complete Bill Pay documentation, see:** [BILL_PAY_API_DOCUMENTATION.md](BILL_PAY_API_DOCUMENTATION.md)

---

*Last Updated: December 8, 2025*
