# API Documentation - CredbuzzPay ERP System

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All authenticated endpoints require JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Response Format

All API responses follow this format:

```json
{
  "success": true,
  "data": {},
  "message": "Success message",
  "errors": []
}
```

---

## Authentication APIs

### 1. Register - Initiate

**Endpoint:** `POST /auth/register/initiate`

**Description:** Initiate user registration with email, mobile, and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "mobile": "+919876543210",
  "password": "SecurePass@123"
}
```

**Response (201 Created):**
```json
{
  "user_code": "ABC123",
  "otp_sent_to_email": true,
  "otp_sent_to_mobile": true,
  "registration_step": 1,
  "message": "OTP sent to email and mobile. Please verify."
}
```

**Error Responses:**
- 400: Email/mobile already registered
- 500: Server error

---

### 2. Register - Verify OTP

**Endpoint:** `POST /auth/register/verify-otp`

**Description:** Verify email and mobile OTPs sent during registration.

**Request Body:**
```json
{
  "user_code": "ABC123",
  "email_otp": "123456",
  "mobile_otp": "654321"
}
```

**Response (200 OK):**
```json
{
  "verified": true,
  "user_code": "ABC123",
  "registration_step": 2,
  "message": "Email and mobile verified successfully."
}
```

**Error Responses:**
- 400: Invalid or expired OTP
- 404: User not found

---

### 3. Login

**Endpoint:** `POST /auth/login`

**Description:** Login with email/mobile and password.

**Request Body:**
```json
{
  "email_or_mobile": "user@example.com",
  "password": "SecurePass@123",
  "device_info": {
    "browser": "Chrome",
    "os": "Windows"
  }
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "user_code": "ABC123",
    "email": "user@example.com",
    "first_name": "John",
    "user_role": "user"
  },
  "requires_2fa": false
}
```

**Error Responses:**
- 401: Invalid credentials
- 403: Account blocked or inactive
- 404: User not found

---

### 4. Logout

**Endpoint:** `POST /auth/logout`

**Required:** Authentication

**Description:** Logout and invalidate session.

**Response (200 OK):**
```json
{
  "logged_out": true,
  "message": "Successfully logged out."
}
```

---

### 5. Forgot Password

**Endpoint:** `POST /auth/forgot-password`

**Description:** Request password reset OTP.

**Request Body:**
```json
{
  "email_or_mobile": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "otp_sent": true,
  "reset_token": "reset_token_xxx",
  "message": "OTP sent to your email and mobile."
}
```

---

### 6. Verify Reset OTP

**Endpoint:** `POST /auth/verify-reset-otp`

**Description:** Verify OTP for password reset.

**Request Body:**
```json
{
  "reset_token": "reset_token_xxx",
  "otp_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "verified": true,
  "password_reset_token": "new_reset_token_xxx"
}
```

---

### 7. Reset Password

**Endpoint:** `POST /auth/reset-password`

**Description:** Reset password with reset token.

**Request Body:**
```json
{
  "password_reset_token": "new_reset_token_xxx",
  "new_password": "NewSecurePass@456"
}
```

**Response (200 OK):**
```json
{
  "password_changed": true,
  "message": "Password reset successfully."
}
```

---

### 8. Change Password

**Endpoint:** `POST /auth/change-password`

**Required:** Authentication

**Description:** Change password for authenticated user.

**Request Body:**
```json
{
  "old_password": "SecurePass@123",
  "new_password": "NewSecurePass@456"
}
```

**Response (200 OK):**
```json
{
  "password_changed": true,
  "message": "Password changed successfully."
}
```

---

## KYC APIs

### 9. Submit Aadhaar

**Endpoint:** `POST /kyc/aadhaar/submit`

**Required:** Authentication

**Description:** Submit Aadhaar for verification.

**Request Body (multipart/form-data):**
```
user_code: ABC123
aadhaar_number: 123456789012
aadhaar_name: John Doe
aadhaar_dob: 1990-01-15
aadhaar_gender: male
aadhaar_address: 123 Main St, City, State 12345
aadhaar_front_image: [file]
aadhaar_back_image: [file]
```

**Response (201 Created):**
```json
{
  "id": "AADHAAR_001",
  "user_code": "ABC123",
  "aadhaar_name": "John Doe",
  "is_verified": false,
  "verification_method": "manual",
  "message": "Aadhaar submitted for verification."
}
```

---

### 10. Verify Aadhaar OTP

**Endpoint:** `POST /kyc/aadhaar/verify-otp`

**Required:** Authentication

**Description:** Verify Aadhaar with OTP (e-KYC).

**Request Body:**
```json
{
  "user_code": "ABC123",
  "otp_code": "123456",
  "request_id": "aadhaar_request_xxx"
}
```

**Response (200 OK):**
```json
{
  "verified": true,
  "aadhaar_data": {
    "name": "John Doe",
    "dob": "1990-01-15",
    "gender": "male"
  }
}
```

---

### 11. Submit PAN

**Endpoint:** `POST /kyc/pan/submit`

**Required:** Authentication

**Description:** Submit PAN for verification.

**Request Body (multipart/form-data):**
```
user_code: ABC123
pan_number: ABCDE1234F
pan_name: John Doe
pan_father_name: Doe Sr
pan_dob: 1990-01-15
pan_image: [file]
```

**Response (201 Created):**
```json
{
  "id": "PAN_001",
  "user_code": "ABC123",
  "pan_number": "ABCDE1234F",
  "is_verified": false,
  "message": "PAN submitted for verification."
}
```

---

### 12. Get KYC Status

**Endpoint:** `GET /kyc/status/{user_code}`

**Required:** Authentication

**Description:** Get complete KYC verification status.

**Response (200 OK):**
```json
{
  "user_code": "ABC123",
  "overall_status": "in_progress",
  "aadhaar_status": "verified",
  "pan_status": "pending",
  "business_status": "not_started",
  "bank_status": "not_started",
  "current_step": 2,
  "kyc_verification_step": 2
}
```

---

## User Management APIs

### 13. Get User Profile

**Endpoint:** `GET /users/{user_code}`

**Required:** Authentication

**Description:** Get user profile information.

**Response (200 OK):**
```json
{
  "user_code": "ABC123",
  "email": "user@example.com",
  "mobile": "+919876543210",
  "first_name": "John",
  "last_name": "Doe",
  "user_role": "user",
  "is_active": true,
  "is_kyc_complete": false,
  "kyc_verification_step": 2
}
```

---

### 14. Update User Profile

**Endpoint:** `PUT /users/{user_code}`

**Required:** Authentication

**Description:** Update user profile information.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "gender": "male",
  "dob": "1990-01-15",
  "address_line1": "123 Main St",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "pincode": "100001"
}
```

**Response (200 OK):**
```json
{
  "user_code": "ABC123",
  "updated_fields": ["first_name", "last_name", "address_line1"],
  "message": "Profile updated successfully."
}
```

---

### 15. Assign Role

**Endpoint:** `POST /users/{user_code}/assign-role`

**Required:** Super Admin Authentication

**Description:** Assign or change user role.

**Request Body:**
```json
{
  "role": "admin"
}
```

**Response (200 OK):**
```json
{
  "user_code": "ABC123",
  "role_assigned": "admin",
  "message": "Role assigned successfully."
}
```

---

### 16. Grant Platform Access

**Endpoint:** `POST /users/{user_code}/platform-access`

**Required:** Admin Authentication

**Description:** Grant user access to a platform.

**Request Body:**
```json
{
  "platform": "web",
  "is_allowed": true,
  "access_level": "full",
  "allowed_ip_ranges": ["192.168.1.0/24"]
}
```

**Response (201 Created):**
```json
{
  "id": "ACCESS_001",
  "platform": "web",
  "is_allowed": true,
  "access_level": "full"
}
```

---

### 17. Block User

**Endpoint:** `POST /users/{user_code}/block`

**Required:** Admin Authentication

**Description:** Temporarily block a user account.

**Request Body:**
```json
{
  "reason": "Suspicious activity detected",
  "block_duration_minutes": 60
}
```

**Response (200 OK):**
```json
{
  "user_code": "ABC123",
  "blocked": true,
  "blocked_until": "2024-11-07T10:00:00Z",
  "reason": "Suspicious activity detected"
}
```

---

## Branch Management APIs

### 18. Create Branch

**Endpoint:** `POST /branches/`

**Required:** Admin Authentication

**Description:** Create a new branch.

**Request Body:**
```json
{
  "branch_name": "Downtown Branch",
  "address_line1": "123 Main St",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "pincode": "100001",
  "phone": "+12125551234",
  "email": "downtown@credbuzz.com",
  "manager_name": "Jane Smith",
  "manager_user_code": "USER001"
}
```

**Response (201 Created):**
```json
{
  "branch_code": "BR001",
  "branch_name": "Downtown Branch",
  "created": true
}
```

---

### 19. List Branches

**Endpoint:** `GET /branches/?is_active=true&search=downtown&limit=20&offset=0`

**Description:** List all branches with pagination.

**Response (200 OK):**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/branches/?offset=20",
  "previous": null,
  "results": [
    {
      "branch_code": "BR001",
      "branch_name": "Downtown Branch",
      "city": "New York",
      "state": "NY",
      "is_active": true
    }
  ]
}
```

---

## Audit & Reporting APIs

### 20. Get User Audit Trail

**Endpoint:** `GET /audit/user/{user_code}/?action=login&from_date=2024-11-01&to_date=2024-11-07&limit=50`

**Required:** Admin Authentication

**Description:** Get user's audit trail.

**Response (200 OK):**
```json
{
  "count": 15,
  "results": [
    {
      "id": "AUDIT_001",
      "action": "login",
      "resource_type": "LoginActivity",
      "description": "User logged in from 192.168.1.1",
      "created_at": "2024-11-07T09:30:00Z"
    }
  ]
}
```

---

### 21. Get Login Activity Report

**Endpoint:** `GET /reports/login-activity/?user_code=ABC123&from_date=2024-11-01&to_date=2024-11-07&status=success`

**Required:** Admin Authentication

**Description:** Generate login activity report.

**Response (200 OK):**
```json
{
  "login_activities": [
    {
      "login_identifier": "user@example.com",
      "status": "success",
      "ip_address": "192.168.1.1",
      "login_timestamp": "2024-11-07T09:30:00Z",
      "risk_score": 5
    }
  ],
  "suspicious_count": 0
}
```

---

### 22. Get KYC Status Report

**Endpoint:** `GET /reports/kyc-status/?branch_code=BR001&verification_step=2`

**Required:** Admin Authentication

**Description:** Generate KYC verification statistics report.

**Response (200 OK):**
```json
{
  "kyc_stats": {
    "pending": 45,
    "in_progress": 23,
    "completed": 132,
    "rejected": 5
  },
  "completion_rate": 73.5
}
```

---

## Error Codes & Messages

### Common Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "message": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "success": false,
  "message": "You do not have permission to access this resource"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "message": "Resource not found"
}
```

**429 Too Many Requests:**
```json
{
  "success": false,
  "message": "Too many requests. Please try again later."
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "An error occurred. Please try again later."
}
```

---

## Rate Limiting

- **General API**: 1000 requests per hour per IP
- **Login**: 10 attempts per minute per IP
- **OTP**: 3 attempts per 5 minutes per user per type

---

## Pagination

List endpoints support pagination:

```
?limit=20&offset=0
```

Response includes:
```json
{
  "count": 150,
  "next": "url_to_next_page",
  "previous": "url_to_previous_page",
  "results": []
}
```

---

## Filtering & Searching

Filter by fields:
```
GET /users/?user_role=admin&is_active=true
```

Search in multiple fields:
```
GET /users/search?q=john
```

---

## Sorting

Sort by field (prefix with `-` for descending):
```
GET /audit/?ordering=-created_at
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

## Webhooks (Future)

Support for real-time notifications via webhooks:

```json
{
  "event": "kyc.verified",
  "timestamp": "2024-11-07T09:30:00Z",
  "data": {
    "user_code": "ABC123",
    "kyc_type": "aadhaar"
  }
}
```

---

**Last Updated:** November 2025
**Version:** 1.0.0
