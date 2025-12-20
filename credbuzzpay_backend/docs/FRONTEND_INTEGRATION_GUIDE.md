# CredBuzz Complete System Integration Guide

## For Frontend Developers

This guide covers the complete flow from registration to full system access including authentication, KYC, role management, and app/feature access control.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CREDBUZZ SYSTEM FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. REGISTRATION        2. LOGIN              3. KYC (If Required)          │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐               │
│  │ Register    │──────▶│ Login       │──────▶│ KYC Steps   │               │
│  │ Verify OTP  │       │ Get Token   │       │ 1-8 Steps   │               │
│  └─────────────┘       └─────────────┘       └─────────────┘               │
│                              │                      │                       │
│                              ▼                      ▼                       │
│                        ┌─────────────────────────────────────┐             │
│                        │      JWT TOKEN CONTAINS:            │             │
│                        │  - user_id                          │             │
│                        │  - user_role                        │             │
│                        │  - app_access: [1, 2, 3, ...]       │             │
│                        │  - feature_access: [1, 2, 3, ...]   │             │
│                        └─────────────────────────────────────┘             │
│                                       │                                     │
│                                       ▼                                     │
│  4. ACCESS APPS BASED ON TOKEN PERMISSIONS                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Bill Pay │  │ KYC      │  │ RBAC     │  │ Reports  │                   │
│  │ (App 1)  │  │ (App 2)  │  │ (App 3)  │  │ (App 4)  │                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. USER ROLES

| Role | Level | KYC Required | Access |
|------|-------|--------------|--------|
| **SUPER_ADMIN** | 1 | ❌ No | Full system access |
| **DEVELOPER** | 1 | ❌ No | Full system access |
| **ADMIN** | 2 | ❌ No | Admin panel + assigned apps |
| **CLIENT** | 3 | ✅ Yes | Only assigned apps after KYC |
| **GUEST** | 4 | - | Very limited |

> **Note:** SUPER_ADMIN and DEVELOPER users bypass KYC and have full access.

---

## 2. AUTHENTICATION APIs

### Base URL: `/api/auth-user/`

### 2.1 Register User
```http
POST /api/auth-user/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "phone_number": "9876543210",
    "password": "SecurePass@123",
    "confirm_password": "SecurePass@123",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Registration successful. Please verify OTP.",
    "data": {
        "user_id": 1,
        "email": "user@example.com",
        "requires_otp_verification": true
    }
}
```

### 2.2 Verify Registration OTP
```http
POST /api/auth-user/verify-registration-otp/
{
    "email": "user@example.com",
    "otp": "123456"
}
```

### 2.3 Login
```http
POST /api/auth-user/login/
{
    "identifier": "user@example.com",
    "password": "SecurePass@123"
}
```

**Response (Contains Access Info):**
```json
{
    "success": true,
    "message": "Login successful.",
    "data": {
        "user": {
            "id": 1,
            "email": "user@example.com",
            "user_code": "USR20251210ABC",
            "user_role": "CLIENT"
        },
        "tokens": {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "expires_in": 3600
        },
        "kyc_status": {
            "status": "NOT_STARTED",
            "completion_percentage": 0,
            "current_step": 1,
            "requires_kyc": true
        },
        "app_access": [1, 2, 3],
        "feature_access": [1, 2, 3, 4, 5]
    }
}
```

### 2.4 Get Profile with Full Access
```http
GET /api/auth-user/profile-full/
Authorization: Bearer {access_token}
```

Returns user profile with complete app/feature access list.

### 2.5 Refresh Token
```http
POST /api/auth-user/refresh-token/
{
    "refresh_token": "eyJ..."
}
```

### 2.6 Logout
```http
POST /api/auth-user/logout/
Authorization: Bearer {access_token}
```

---

## 3. KYC APIs (8 Steps)

### Base URL: `/api/kyc/`

### 3.1 KYC Flow Overview
```
Step 1: Start KYC
Step 2: Aadhaar Details + Upload
Step 3: PAN Details + Upload
Step 4: Business Details
Step 5: Selfie Upload
Step 6: Office Photos Upload
Step 7: Address Proof Upload
Step 8: Bank Details + Submit
```

### 3.2 Check KYC Status
```http
GET /api/kyc/status/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "status": "IN_PROGRESS",
        "mega_step": "IDENTITY_PROOF",
        "current_step": 3,
        "total_steps": 8,
        "completion_percentage": 25,
        "can_submit": false
    }
}
```

### 3.3 Start KYC
```http
POST /api/kyc/start/
Authorization: Bearer {access_token}
```

### 3.4 Submit Aadhaar
```http
POST /api/kyc/identity/aadhaar/
{
    "aadhaar_number": "123456789012",
    "full_name": "John Doe",
    "date_of_birth": "1990-01-15",
    "gender": "MALE",
    "address": "123 Main Street, Mumbai"
}
```

### 3.5 Upload Aadhaar Images
```http
POST /api/kyc/identity/aadhaar/upload/
Content-Type: multipart/form-data

aadhaar_front: [file]
aadhaar_back: [file]
```

### 3.6 Submit PAN
```http
POST /api/kyc/identity/pan/
{
    "pan_number": "ABCDE1234F",
    "name_on_pan": "JOHN DOE"
}
```

### 3.7 Submit Business Details
```http
POST /api/kyc/business/
{
    "business_name": "John's Electronics",
    "business_type": "RETAIL",
    "gst_number": "22AAAAA0000A1Z5",
    "business_address": "456 Shop Street, Mumbai"
}
```

### 3.8 Upload Verification Images
```http
POST /api/kyc/verification/selfie/
POST /api/kyc/verification/office/
POST /api/kyc/verification/address-proof/
```

### 3.9 Submit Bank Details
```http
POST /api/kyc/bank/
{
    "account_holder_name": "John Doe",
    "account_number": "123456789012",
    "ifsc_code": "SBIN0001234",
    "bank_name": "State Bank of India"
}
```

### 3.10 Submit KYC for Review
```http
POST /api/kyc/submit/
Authorization: Bearer {access_token}
```

---

## 4. RBAC APIs (Role-Based Access Control)

### Base URL: `/api/rbac/`

### 4.1 Get All Roles
```http
GET /api/rbac/roles/
Authorization: Bearer {access_token}
```

### 4.2 Get All Apps
```http
GET /api/rbac/apps/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "success": true,
    "data": [
        {"id": 1, "name": "Bill Pay", "code": "BILL_PAY", "is_active": true},
        {"id": 2, "name": "KYC", "code": "KYC", "is_active": true},
        {"id": 3, "name": "RBAC Admin", "code": "RBAC", "is_active": true},
        {"id": 4, "name": "Reports", "code": "REPORTS", "is_active": true}
    ]
}
```

### 4.3 Get All Features
```http
GET /api/rbac/features/
Authorization: Bearer {access_token}
```

### 4.4 Get Features by App
```http
GET /api/rbac/features/?app_id=1
```

### 4.5 Get All Apps and Features (Combined)
```http
GET /api/rbac/all-access-items/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "apps": [
            {
                "id": 1,
                "name": "Bill Pay",
                "code": "BILL_PAY",
                "features": [
                    {"id": 1, "name": "View Bills", "code": "VIEW_BILLS"},
                    {"id": 2, "name": "Pay Bills", "code": "PAY_BILLS"},
                    {"id": 3, "name": "Manage Bank Accounts", "code": "MANAGE_BANK"}
                ]
            }
        ]
    }
}
```

### 4.6 Get My Permissions
```http
GET /api/rbac/my-permissions/
Authorization: Bearer {access_token}
```

Returns all apps and features you have access to.

### 4.7 Check Specific Permission
```http
POST /api/rbac/check-permission/
{
    "app_code": "BILL_PAY",
    "feature_code": "PAY_BILLS"
}
```

---

## 5. USER ACCESS MANAGEMENT (Admin/SuperAdmin Only)

### 5.1 Get User's Access Overview
```http
GET /api/rbac/users/{user_id}/access/
Authorization: Bearer {access_token}
```

### 5.2 Assign Access to User
```http
POST /api/rbac/users/{user_id}/assign-access/
{
    "role_id": 3,
    "app_ids": [1, 2, 3],
    "feature_ids": [1, 2, 3, 4, 5]
}
```

### 5.3 Revoke Access from User
```http
POST /api/rbac/users/{user_id}/revoke-access/
{
    "app_ids": [2],
    "feature_ids": [4, 5]
}
```

### 5.4 Assign Role to User
```http
POST /api/rbac/user-role-assignments/
{
    "user": 5,
    "role": 3,
    "assigned_by": 1,
    "is_active": true
}
```

---

## 6. FRONTEND IMPLEMENTATION GUIDE

### 6.1 Login Flow
```javascript
// 1. Login and store tokens
const loginResponse = await fetch('/api/auth-user/login/', {
    method: 'POST',
    body: JSON.stringify({ identifier: email, password })
});
const { data } = await loginResponse.json();

// Store tokens
localStorage.setItem('access_token', data.tokens.access_token);
localStorage.setItem('refresh_token', data.tokens.refresh_token);

// Store access info for navigation
localStorage.setItem('app_access', JSON.stringify(data.app_access));
localStorage.setItem('feature_access', JSON.stringify(data.feature_access));
localStorage.setItem('user_role', data.user.user_role);
localStorage.setItem('kyc_status', JSON.stringify(data.kyc_status));
```

### 6.2 KYC Redirect Logic
```javascript
function checkKYCRedirect(kycStatus, userRole) {
    // Skip KYC for Admin/SuperAdmin/Developer
    const skipKYCRoles = ['SUPER_ADMIN', 'DEVELOPER', 'ADMIN'];
    if (skipKYCRoles.includes(userRole)) {
        return '/dashboard'; // Go to main app
    }
    
    // Check KYC status
    if (kycStatus.status === 'APPROVED') {
        return '/dashboard';
    }
    
    if (kycStatus.status === 'NOT_STARTED') {
        return '/kyc/start';
    }
    
    if (kycStatus.status === 'IN_PROGRESS') {
        return `/kyc/step/${kycStatus.current_step}`;
    }
    
    if (kycStatus.status === 'SUBMITTED') {
        return '/kyc/pending-review';
    }
    
    if (kycStatus.status === 'REJECTED') {
        return '/kyc/resubmit';
    }
}
```

### 6.3 Access Control Hook
```javascript
// React Hook for access control
function useHasAccess(appCode, featureCode = null) {
    const appAccess = JSON.parse(localStorage.getItem('app_access') || '[]');
    const featureAccess = JSON.parse(localStorage.getItem('feature_access') || '[]');
    
    // For SuperAdmin/Developer - full access
    const userRole = localStorage.getItem('user_role');
    if (['SUPER_ADMIN', 'DEVELOPER'].includes(userRole)) {
        return true;
    }
    
    // Check app access (you'll need app ID mapping)
    const appIdMap = { BILL_PAY: 1, KYC: 2, RBAC: 3, REPORTS: 4 };
    const hasApp = appAccess.includes(appIdMap[appCode]);
    
    if (!featureCode) return hasApp;
    
    // Check feature access
    const featureIdMap = { VIEW_BILLS: 1, PAY_BILLS: 2, ... };
    return hasApp && featureAccess.includes(featureIdMap[featureCode]);
}

// Usage in component
function BillPayPage() {
    const hasAccess = useHasAccess('BILL_PAY');
    if (!hasAccess) return <AccessDenied />;
    return <BillPayContent />;
}
```

### 6.4 Navigation Menu Based on Access
```javascript
function buildNavMenu(appAccess, userRole) {
    const fullAccessRoles = ['SUPER_ADMIN', 'DEVELOPER'];
    
    const allMenuItems = [
        { id: 1, name: 'Bill Pay', path: '/bills', icon: 'receipt' },
        { id: 2, name: 'KYC Management', path: '/kyc', icon: 'id-card' },
        { id: 3, name: 'User Management', path: '/users', icon: 'users' },
        { id: 4, name: 'Role Management', path: '/rbac', icon: 'shield' },
        { id: 5, name: 'Reports', path: '/reports', icon: 'chart' },
    ];
    
    if (fullAccessRoles.includes(userRole)) {
        return allMenuItems; // Show all for SuperAdmin/Developer
    }
    
    return allMenuItems.filter(item => appAccess.includes(item.id));
}
```

### 6.5 API Request Interceptor
```javascript
// Axios interceptor for token management
axios.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401 errors - refresh token or redirect to login
axios.interceptors.response.use(
    response => response,
    async error => {
        if (error.response?.status === 401) {
            const refreshToken = localStorage.getItem('refresh_token');
            try {
                const res = await axios.post('/api/auth-user/refresh-token/', {
                    refresh_token: refreshToken
                });
                localStorage.setItem('access_token', res.data.data.access_token);
                return axios(error.config); // Retry
            } catch {
                localStorage.clear();
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);
```

---

## 7. USER MANAGEMENT APIs

### Base URL: `/api/auth-user/users/`

### 7.1 List All Users (Admin Only)
```http
GET /api/auth-user/users/
GET /api/auth-user/users/?role=CLIENT&is_active=true
```

### 7.2 Get User Details
```http
GET /api/auth-user/users/{user_id}/
```

### 7.3 Update User
```http
PUT /api/auth-user/users/{user_id}/
{
    "first_name": "Updated",
    "last_name": "Name",
    "is_active": true
}
```

### 7.4 Activate/Deactivate User
```http
PUT /api/auth-user/users/{user_id}/activate/
PUT /api/auth-user/users/{user_id}/deactivate/
```

---

## 8. KYC ADMIN REVIEW APIs (Admin Only)

### 8.1 List KYC Applications
```http
GET /api/kyc/admin/applications/
GET /api/kyc/admin/applications/?status=SUBMITTED
```

### 8.2 Review KYC Application
```http
POST /api/kyc/admin/applications/{application_id}/review/
{
    "action": "APPROVE",
    "remarks": "All documents verified"
}
```

Actions: `APPROVE`, `REJECT`, `REQUEST_RESUBMIT`

---

## Quick Reference: All Endpoints

### Authentication (`/api/auth-user/`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /register/ | Register new user |
| POST | /verify-registration-otp/ | Verify registration OTP |
| POST | /login/ | Login & get tokens |
| POST | /logout/ | Logout current session |
| POST | /refresh-token/ | Refresh access token |
| GET | /profile/ | Get user profile |
| GET | /profile-full/ | Profile with access info |
| POST | /change-password/ | Change password |
| POST | /forgot-password/ | Request password reset |
| GET | /users/ | List users (Admin) |
| GET | /users/{id}/ | User details |

### KYC (`/api/kyc/`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /status/ | KYC status |
| POST | /start/ | Start KYC |
| POST | /identity/aadhaar/ | Submit Aadhaar |
| POST | /identity/aadhaar/upload/ | Upload Aadhaar images |
| POST | /identity/pan/ | Submit PAN |
| POST | /business/ | Business details |
| POST | /verification/selfie/ | Upload selfie |
| POST | /bank/ | Bank details |
| POST | /submit/ | Submit for review |

### RBAC (`/api/rbac/`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /roles/ | List all roles |
| GET | /apps/ | List all apps |
| GET | /features/ | List all features |
| GET | /all-access-items/ | Apps with features |
| GET | /my-permissions/ | Current user's access |
| POST | /check-permission/ | Check specific access |
| GET | /users/{id}/access/ | User's access overview |
| POST | /users/{id}/assign-access/ | Assign access to user |
| POST | /users/{id}/revoke-access/ | Revoke access |
| POST | /user-role-assignments/ | Assign role to user |

### Bill Pay (`/api/bills/`)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /categories/ | Bill categories |
| GET | /billers/ | List billers |
| POST | /fetch/ | Fetch bill |
| POST | /pay/ | Pay bill |
| GET | /bank-accounts/ | User bank accounts |
| GET | /cards/ | User cards |
| POST | /mpin/setup/ | Setup MPIN |
| POST | /transfer/ | Money transfer |
