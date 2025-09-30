# ERP System API Documentation

## Overview

This is a comprehensive ERP (Enterprise Resource Planning) system built with Django REST Framework, featuring user authentication, KYC verification, business onboarding, role-based access control, and comprehensive security features.

## Base URL
```
http://localhost:8000/erp/
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## User Roles & Hierarchy

1. **User (Level 1)** - Basic user with limited access
2. **Admin (Level 2)** - Branch-level administrator
3. **Super Admin (Level 3)** - Multi-branch administrator
4. **Master Superadmin (Level 4)** - System-wide administrator

## API Endpoints

### Authentication Endpoints

#### 1. User Registration
**POST** `/auth/register/`

Register a new user account.

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "mobile": "9876543210",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "branch": 1
}
```

**Response (201):**
```json
{
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "mobile": "9876543210",
    "is_active": false,
    "is_email_verified": false,
    "is_mobile_verified": false,
    "role": "user",
    "message": "User registered successfully. Please verify your email and mobile."
}
```

#### 2. User Login
**POST** `/auth/login/`

Login with email/mobile and password.

**Request Body:**
```json
{
    "email_or_mobile": "john.doe@example.com",
    "password": "SecurePass123!",
    "device_info": {
        "device_type": "mobile",
        "device_name": "iPhone 12",
        "browser": "Safari",
        "os": "iOS 15.0",
        "location": "Mumbai, India"
    }
}
```

**Response (200):**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "user",
        "is_active": true
    },
    "message": "Login successful"
}
```

#### 3. Token Refresh
**POST** `/auth/token/refresh/`

Refresh access token using refresh token.

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 4. Change Password
**POST** `/auth/change-password/`

Change user password (requires authentication).

**Request Body:**
```json
{
    "current_password": "CurrentPass123!",
    "new_password": "NewSecurePass123!",
    "confirm_password": "NewSecurePass123!"
}
```

#### 5. Logout
**POST** `/auth/logout/`

Logout user and blacklist token.

**Request Body:**
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### OTP (One-Time Password) Endpoints

#### 1. Request OTP
**POST** `/otp/request/`

Request OTP for email or mobile verification.

**Request Body:**
```json
{
    "otp_type": "email",  // "email" or "mobile"
    "user_id": 1
}
```

**Response (200):**
```json
{
    "message": "OTP sent successfully to email",
    "otp_type": "email"
}
```

#### 2. Verify OTP
**POST** `/otp/verify/`

Verify OTP for email or mobile.

**Request Body:**
```json
{
    "otp_type": "email",  // "email" or "mobile"
    "otp": "123456",
    "user_id": 1
}
```

**Response (200):**
```json
{
    "message": "Email verified successfully",
    "is_verified": true
}
```

### KYC (Know Your Customer) Endpoints

#### 1. Aadhaar KYC
**POST** `/kyc/aadhaar/`

Submit Aadhaar KYC documents (requires authentication).

**Request Body (multipart/form-data):**
```
aadhaar_number: 123456789012
aadhaar_name: John Doe
aadhaar_front_image: [file]
aadhaar_back_image: [file]
```

**Response (201):**
```json
{
    "id": 1,
    "aadhaar_name": "John Doe",
    "masked_aadhaar": "XXXX-XXXX-9012",
    "verification_status": "pending",
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. PAN KYC
**POST** `/kyc/pan/`

Submit PAN KYC documents (requires authentication).

**Request Body (multipart/form-data):**
```
pan_number: ABCDE1234F
pan_name: John Doe
date_of_birth: 1990-01-15
pan_image: [file]
```

#### 3. Bank Details
**POST** `/kyc/bank/`

Submit bank account details (requires authentication).

**Request Body (multipart/form-data):**
```
account_holder_name: John Doe
account_number: 1234567890123456
ifsc_code: HDFC0001234
account_type: savings
bank_name: HDFC Bank
branch_name: Mumbai Branch
bank_proof_image: [file]
```

### Business Management Endpoints

#### 1. Business Details
**POST** `/business/details/`

Submit business details (requires authentication).

**Request Body (multipart/form-data):**
```
user_selfie: [file]
business_name: John's Enterprise
business_address_line1: 123 Business Street
city: Mumbai
state: Maharashtra
pincode: 400001
business_phone: 9876543210
business_email: business@example.com
```

#### 2. Get Business Details
**GET** `/business/details/`

Get user's business details (requires authentication).

**Response (200):**
```json
{
    "id": 1,
    "business_name": "John's Enterprise",
    "business_phone": "9876543210",
    "business_email": "business@example.com",
    "verification_status": "pending",
    "created_at": "2024-01-15T10:30:00Z"
}
```

### Dashboard Endpoints

#### 1. Dashboard Statistics
**GET** `/dashboard/stats/`

Get dashboard statistics (role-based access).

**Admin Response (200):**
```json
{
    "total_users": 150,
    "active_users": 120,
    "verified_users": 100,
    "pending_kyc": 25,
    "approved_kyc": 75,
    "rejected_kyc": 5,
    "total_businesses": 50,
    "pending_businesses": 10,
    "approved_businesses": 40,
    "recent_registrations": 5
}
```

**User Response (200):**
```json
{
    "login_count": 15,
    "verification_status": {
        "email": true,
        "mobile": true,
        "aadhaar": "approved",
        "pan": "pending",
        "bank": "rejected",
        "business": "pending"
    },
    "last_login": "2024-01-15T10:30:00Z",
    "account_created": "2024-01-01T12:00:00Z"
}
```

### Admin Management Endpoints (Admin+ roles only)

#### 1. User Management
**GET** `/admin/users/`

Get list of users with filters.

**Query Parameters:**
- `role`: Filter by role
- `status`: Filter by status (active/inactive)
- `branch`: Filter by branch
- `search`: Search by name/email/mobile

#### 2. KYC Management
**GET** `/admin/kyc/pending/`

Get pending KYC verifications.

**PUT** `/admin/kyc/{kyc_id}/verify/`

Approve or reject KYC verification.

**Request Body:**
```json
{
    "action": "approve",  // "approve" or "reject"
    "remarks": "All documents verified successfully"
}
```

#### 3. User Creation (Admin only)
**POST** `/admin/users/create/`

Create new user account.

**Request Body:**
```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "mobile": "9876543211",
    "role": "user",
    "branch": 1,
    "is_active": true
}
```

### Security & Audit Endpoints

#### 1. Login History
**GET** `/security/login-history/`

Get user's login history (requires authentication).

**Response (200):**
```json
{
    "login_activities": [
        {
            "id": 1,
            "login_time": "2024-01-15T10:30:00Z",
            "ip_address": "192.168.1.1",
            "device_info": "iPhone 12 - Safari",
            "location": "Mumbai, India",
            "status": "success"
        }
    ]
}
```

#### 2. Audit Trail (Admin only)
**GET** `/admin/audit/`

Get system audit trail.

**Query Parameters:**
- `user_id`: Filter by user
- `action`: Filter by action type
- `date_from`: Start date
- `date_to`: End date

## Error Responses

### 400 Bad Request
```json
{
    "error": "Validation failed",
    "details": {
        "email": ["This field is required."],
        "password": ["Password must be at least 8 characters."]
    }
}
```

### 401 Unauthorized
```json
{
    "error": "Authentication required",
    "message": "Please provide a valid token"
}
```

### 403 Forbidden
```json
{
    "error": "Permission denied",
    "message": "You don't have permission to access this resource"
}
```

### 404 Not Found
```json
{
    "error": "Resource not found",
    "message": "The requested resource does not exist"
}
```

### 429 Too Many Requests
```json
{
    "error": "Rate limit exceeded",
    "message": "Too many requests. Please try again later."
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error",
    "message": "An unexpected error occurred. Please contact support."
}
```

## Security Features

### 1. Rate Limiting
- Login attempts: 5 per minute
- OTP requests: 3 per 5 minutes
- API calls: 100 per minute for authenticated users

### 2. Account Lockout
- Account locked after 3 failed login attempts
- Automatic unlock after 15 minutes
- Admin can manually unlock accounts

### 3. Device Tracking
- Device fingerprinting for security
- Suspicious device alerts
- Login history with device details

### 4. Data Encryption
- Sensitive data (Aadhaar, Bank accounts) encrypted at rest
- HTTPS required for all API calls
- JWT tokens with short expiry times

### 5. Audit Trail
- All user actions logged
- Admin actions tracked
- Security events monitored

## Platform Access Control

Users can be restricted to specific platforms:
- **web**: Web application only
- **mobile**: Mobile application only
- **both**: Both web and mobile access

Access restrictions are enforced at the middleware level.

## File Upload Guidelines

### Supported Formats
- Images: JPEG, PNG, PDF
- Maximum size: 5MB per file

### Required Documents
- **Aadhaar**: Front and back images
- **PAN**: Clear image of PAN card
- **Bank**: Bank statement or passbook
- **Business**: Business registration documents
- **Selfie**: Clear user selfie for verification

## Testing

Run the test suite:
```bash
python manage.py test erp.tests
```

Test categories:
- Model tests
- API endpoint tests
- Authentication tests
- Security tests
- Utility function tests

## Environment Variables

Required environment variables:
```
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=sqlite:///db.sqlite3

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SMS Configuration
FAST2SMS_API_KEY=your-fast2sms-api-key

# Security
ENCRYPTION_KEY=your-fernet-encryption-key
JWT_SECRET_KEY=your-jwt-secret-key
```

## Support

For API support and issues, please contact the development team or check the system logs for detailed error information.




