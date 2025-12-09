# KYC Verification API Documentation

## Overview

The KYC (Know Your Customer) Verification API provides a comprehensive, secure, and step-by-step user verification system for the CredBuzz platform. This module integrates with the custom `users_auth.User` model and RBAC system.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Security Features](#security-features)
3. [KYC Flow](#kyc-flow)
4. [API Endpoints](#api-endpoints)
   - [OTP Endpoints](#otp-endpoints)
   - [KYC Status Endpoints](#kyc-status-endpoints)
   - [Identity Proof Endpoints](#identity-proof-endpoints)
   - [Business Details Endpoints](#business-details-endpoints)
   - [Verification Images Endpoints](#verification-images-endpoints)
   - [Bank Details Endpoints](#bank-details-endpoints)
   - [Submission Endpoints](#submission-endpoints)
   - [Admin Endpoints](#admin-endpoints)
5. [Models](#models)
6. [Status Codes](#status-codes)
7. [Error Responses](#error-responses)

---

## Authentication

All endpoints require JWT authentication using the Bearer token scheme.

```
Authorization: Bearer <access_token>
```

Get the token from `/api/auth/login/`:

```json
POST /api/auth/login/
{
    "identifier": "user@example.com",
    "password": "password123"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "user": {...},
        "tokens": {
            "access_token": "eyJ...",
            "refresh_token": "eyJ..."
        }
    }
}
```

---

## Security Features

### Data Encryption
- **Aadhaar Number**: Encrypted using Fernet symmetric encryption
- **PAN Number**: Encrypted using Fernet symmetric encryption
- **Bank Account Number**: Encrypted using Fernet symmetric encryption

### Data Masking
- Aadhaar: `XXXX-XXXX-9012` (only last 4 digits visible)
- PAN: `ABCXX1234X` (middle characters masked)
- Account Number: `XXXXXXXX9012` (only last 4 digits visible)

### File Upload Security
- Maximum file size: 5MB
- Allowed formats: JPG, JPEG, PNG, PDF
- Files stored in secure `media/` directory

### Access Control
- Uses custom RBAC system
- Admin endpoints require `DEVELOPER`, `SUPER_ADMIN`, or `SUPPORT` roles
- User can only access their own KYC application

---

## KYC Flow

### Mega Steps
1. **IDENTITY_PROOF** - Aadhaar and PAN verification
2. **SELFIE_AND_BUSINESS** - Business details and verification images
3. **COMPLETED** - All steps completed, ready for review

### Progress Steps (8 Total)
| Step | Name | Mega Step |
|------|------|-----------|
| 1 | Aadhaar Details | IDENTITY_PROOF |
| 2 | Aadhaar Photos | IDENTITY_PROOF |
| 3 | PAN Details | IDENTITY_PROOF |
| 4 | PAN Photo | IDENTITY_PROOF |
| 5 | Business Details | SELFIE_AND_BUSINESS |
| 6 | Verification Images | SELFIE_AND_BUSINESS |
| 7 | Address Proof | SELFIE_AND_BUSINESS |
| 8 | Bank Details | SELFIE_AND_BUSINESS |

### Status Flow
```
NOT_STARTED → IN_PROGRESS → SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED
```

---

## API Endpoints

### Base URL
```
http://127.0.0.1:8000/api/kyc/
```

---

## OTP Endpoints

### Send OTP
```http
POST /api/kyc/send-otp/
```

**Request Body:**
```json
{
    "otp_type": "EMAIL"  // or "PHONE"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "OTP sent successfully to your email.",
    "otp_id": "uuid",
    "expires_in_minutes": 10,
    "otp_type": "EMAIL"
}
```

### Verify OTP
```http
POST /api/kyc/verify-otp/
```

**Request Body:**
```json
{
    "otp_code": "123456",
    "otp_type": "EMAIL"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "OTP verified successfully.",
    "otp_type": "EMAIL"
}
```

### Resend OTP
```http
POST /api/kyc/resend-otp/
```

**Request Body:**
```json
{
    "otp_type": "EMAIL"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "New OTP sent successfully.",
    "otp_id": "uuid",
    "expires_in_minutes": 10
}
```

---

## KYC Status Endpoints

### Get KYC Status
```http
GET /api/kyc/status/
```

**Response (200 OK) - No KYC:**
```json
{
    "success": true,
    "has_kyc": false,
    "message": "No KYC application found. Start KYC to begin."
}
```

**Response (200 OK) - With KYC:**
```json
{
    "success": true,
    "has_kyc": true,
    "kyc": {
        "id": "uuid",
        "application_id": "KYC20251205XXXXX",
        "user_email": "user@example.com",
        "status": "IN_PROGRESS",
        "mega_step": "IDENTITY_PROOF",
        "current_step": 1,
        "total_steps": 8,
        "completion_percentage": 12,
        "is_email_verified": true,
        "is_phone_verified": false,
        "identity_proof": {...},
        "business_details": {...},
        "verification_images": {...},
        "bank_details": {...},
        "progress_steps": [...]
    }
}
```

### Start KYC
```http
POST /api/kyc/start/
```

**Response (201 Created):**
```json
{
    "success": true,
    "message": "KYC application started successfully.",
    "kyc": {
        "id": "uuid",
        "application_id": "KYC20251205XXXXX",
        "status": "IN_PROGRESS",
        "mega_step": "IDENTITY_PROOF",
        "current_step": 1,
        "total_steps": 8,
        ...
    }
}
```

---

## Identity Proof Endpoints

### Submit Aadhaar Details
```http
POST /api/kyc/identity/aadhaar/
```

**Request Body:**
```json
{
    "aadhaar_number": "123456789012",
    "aadhaar_name": "John Doe",
    "aadhaar_dob": "1990-01-15",
    "aadhaar_address": "123 Main St, City, State 123456"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Aadhaar details saved successfully.",
    "aadhaar_masked": "XXXX-XXXX-9012"
}
```

### Upload Aadhaar Photos
```http
POST /api/kyc/identity/aadhaar/upload/
Content-Type: multipart/form-data
```

**Form Data:**
- `aadhaar_front`: File (JPG/PNG/PDF, max 5MB)
- `aadhaar_back`: File (JPG/PNG/PDF, max 5MB)

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Aadhaar photos uploaded successfully.",
    "aadhaar_front_url": "/media/kyc/.../front.jpg",
    "aadhaar_back_url": "/media/kyc/.../back.jpg"
}
```

### Submit PAN Details
```http
POST /api/kyc/identity/pan/
```

**Request Body:**
```json
{
    "pan_number": "ABCDE1234F",
    "pan_name": "John Doe",
    "pan_dob": "1990-01-15",
    "pan_father_name": "Father Name"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "PAN details saved successfully.",
    "pan_masked": "ABCXX1234X"
}
```

### Upload PAN Photo
```http
POST /api/kyc/identity/pan/upload/
Content-Type: multipart/form-data
```

**Form Data:**
- `pan_image`: File (JPG/PNG/PDF, max 5MB)

**Response (200 OK):**
```json
{
    "success": true,
    "message": "PAN photo uploaded successfully.",
    "pan_image_url": "/media/kyc/.../pan.jpg"
}
```

---

## Business Details Endpoints

### Submit/Update Business Details
```http
POST /api/kyc/business/
PUT /api/kyc/business/
```

**Request Body:**
```json
{
    "business_name": "Company Pvt Ltd",
    "business_type": "Private Limited",
    "business_phone": "9876543210",
    "business_email": "business@company.com",
    "address_line_1": "123 Business Park",
    "address_line_2": "Floor 5",
    "address_line_3": "",
    "landmark": "Near Metro Station",
    "city": "Mumbai",
    "district": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "country": "India"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Business details saved successfully.",
    "business": {
        "id": "uuid",
        "business_name": "Company Pvt Ltd",
        "full_address": "123 Business Park, Floor 5, Near Metro Station, Mumbai, Mumbai, Maharashtra, 400001, India",
        "is_complete": true,
        ...
    }
}
```

### Get Business Details
```http
GET /api/kyc/business/
```

---

## Verification Images Endpoints

### Upload Verification Images
```http
POST /api/kyc/verification-images/
PUT /api/kyc/verification-images/
Content-Type: multipart/form-data
```

**Form Data:**
- `selfie`: File (JPG/PNG, max 5MB)
- `office_sitting_photo`: File (JPG/PNG, max 5MB)
- `office_door_photo`: File (JPG/PNG, max 5MB)
- `address_proof`: File (JPG/PNG/PDF, max 5MB)
- `address_proof_type`: String (e.g., "UTILITY_BILL", "BANK_STATEMENT")

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Verification images uploaded successfully.",
    "images": {
        "selfie_url": "/media/kyc/.../selfie.jpg",
        "office_sitting_url": "/media/kyc/.../office_sitting.jpg",
        "office_door_url": "/media/kyc/.../office_door.jpg",
        "address_proof_url": "/media/kyc/.../address_proof.pdf",
        "is_complete": true
    }
}
```

---

## Bank Details Endpoints

### Submit/Update Bank Details
```http
POST /api/kyc/bank/
PUT /api/kyc/bank/
Content-Type: application/json (or multipart/form-data with document)
```

**Request Body:**
```json
{
    "account_holder_name": "John Doe",
    "account_number": "12345678901234",
    "confirm_account_number": "12345678901234",
    "ifsc_code": "SBIN0001234",
    "account_type": "SAVINGS",
    "bank_name": "State Bank of India",
    "branch_name": "Main Branch",
    "branch_address": "123 Bank Street"
}
```

**With Document (multipart/form-data):**
- `bank_document`: File (JPG/PNG/PDF, max 5MB) - Cancelled cheque or passbook

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Bank details saved successfully.",
    "bank": {
        "id": "uuid",
        "account_holder_name": "John Doe",
        "account_number_masked": "XXXXXXXXXX1234",
        "ifsc_code": "SBIN0001234",
        "account_type": "SAVINGS",
        "bank_name": "State Bank of India",
        "is_complete": false,
        "is_verified": false,
        ...
    }
}
```

### Get Bank Details
```http
GET /api/kyc/bank/
```

---

## Submission Endpoints

### Submit KYC for Review
```http
POST /api/kyc/submit/
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "KYC submitted for review successfully.",
    "application_id": "KYC20251205XXXXX",
    "status": "SUBMITTED",
    "submitted_at": "2025-12-05T14:30:00Z"
}
```

**Response (400 Bad Request) - Incomplete:**
```json
{
    "success": false,
    "message": "Please complete all required steps before submission.",
    "incomplete_steps": [
        "Aadhaar Photos",
        "Verification Images"
    ]
}
```

---

## Admin Endpoints

> **Note:** Admin endpoints require user roles: `DEVELOPER`, `SUPER_ADMIN`, or `SUPPORT`

### List All KYC Applications
```http
GET /api/kyc/admin/applications/
```

**Query Parameters:**
- `status`: Filter by status (NOT_STARTED, IN_PROGRESS, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED)
- `search`: Search by email, user_code, or application_id
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 20)

**Response (200 OK):**
```json
{
    "success": true,
    "count": 10,
    "status_summary": {
        "SUBMITTED": 5,
        "UNDER_REVIEW": 3,
        "APPROVED": 2
    },
    "applications": [
        {
            "id": "uuid",
            "application_id": "KYC20251205XXXXX",
            "user_email": "user@example.com",
            "user_code": "ABC123",
            "user_name": "John Doe",
            "status": "SUBMITTED",
            "mega_step": "COMPLETED",
            "completion_percentage": 100,
            "submitted_at": "2025-12-05T14:30:00Z",
            "created_at": "2025-12-05T14:00:00Z"
        }
    ]
}
```

### Get Application Detail
```http
GET /api/kyc/admin/applications/{application_id}/
```

**Response (200 OK):**
```json
{
    "success": true,
    "application": {
        "id": "uuid",
        "application_id": "KYC20251205XXXXX",
        "user": {
            "id": 1,
            "email": "user@example.com",
            "user_code": "ABC123",
            "full_name": "John Doe"
        },
        "status": "SUBMITTED",
        "identity_proof": {...},
        "business_details": {...},
        "verification_images": {...},
        "bank_details": {...},
        "progress_steps": [...],
        "audit_logs": [...]
    }
}
```

### Start Review
```http
POST /api/kyc/admin/applications/{application_id}/review/
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Review started for KYC20251205XXXXX.",
    "status": "UNDER_REVIEW",
    "reviewed_at": "2025-12-05T15:00:00Z"
}
```

### Approve Application
```http
POST /api/kyc/admin/applications/{application_id}/approve/
```

**Request Body (optional):**
```json
{
    "remarks": "All documents verified successfully."
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "KYC application KYC20251205XXXXX approved successfully.",
    "status": "APPROVED",
    "approved_at": "2025-12-05T15:30:00Z"
}
```

### Reject Application
```http
POST /api/kyc/admin/applications/{application_id}/reject/
```

**Request Body:**
```json
{
    "rejection_reason": "Aadhaar image is blurry. Please upload a clearer image.",
    "remarks": "Additional notes for internal reference"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "KYC application KYC20251205XXXXX rejected.",
    "status": "REJECTED",
    "rejection_reason": "Aadhaar image is blurry..."
}
```

---

## Models

### KYC Status Enum
| Value | Description |
|-------|-------------|
| NOT_STARTED | KYC not yet initiated |
| IN_PROGRESS | KYC in progress |
| SUBMITTED | Submitted for review |
| UNDER_REVIEW | Currently being reviewed |
| APPROVED | KYC approved |
| REJECTED | KYC rejected |
| RESUBMIT_REQUESTED | Corrections needed |

### Account Type Enum
| Value | Description |
|-------|-------------|
| SAVINGS | Savings Account |
| CURRENT | Current Account |

### OTP Type Enum
| Value | Description |
|-------|-------------|
| EMAIL | Email OTP |
| PHONE | Phone/SMS OTP |

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid data |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 415 | Unsupported Media Type |
| 500 | Internal Server Error |

---

## Error Responses

### Validation Error
```json
{
    "success": false,
    "message": "Validation error",
    "errors": {
        "aadhaar_number": ["Aadhaar number must be exactly 12 digits."],
        "pan_number": ["Invalid PAN format."]
    }
}
```

### Authentication Error
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Permission Error
```json
{
    "success": false,
    "message": "You do not have permission to perform this action."
}
```

---

## Testing

### Test Accounts
| Role | Email | Password | User Code |
|------|-------|----------|-----------|
| Developer | dev@credbuzz.com | Developer@123 | CGX0R0 |
| Super Admin | superadmin@credbuzz.com | SuperAdmin@123 | VYO541 |

### PowerShell Examples

**Login and Get Token:**
```powershell
$body = @{identifier="dev@credbuzz.com"; password="Developer@123"} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method POST -Body $body -ContentType "application/json"
$token = $response.data.tokens.access_token
$headers = @{Authorization = "Bearer $token"}
```

**Start KYC:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/kyc/start/" -Method POST -Headers $headers
```

**Submit Aadhaar:**
```powershell
$body = @{
    aadhaar_number="123456789012"
    aadhaar_name="Test User"
    aadhaar_dob="1990-01-15"
    aadhaar_address="123 Test Street"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/kyc/identity/aadhaar/" -Method POST -Headers $headers -Body $body -ContentType "application/json"
```

---

## Integration with RBAC

The KYC module integrates with the RBAC system for permission management:

### Admin Roles
- `SUPER_ADMIN`: Full access to all KYC operations
- `DEVELOPER`: Full access for development and testing
- `SUPPORT`: Can view and review KYC applications

### User Roles
- `END_USER`: Can only manage their own KYC application
- `MERCHANT`: Can manage their own KYC application
- `AGENT`: Can manage their own KYC application

---

## Audit Logging

All KYC actions are logged with:
- Action type (CREATE, UPDATE, SUBMIT, APPROVE, REJECT, etc.)
- Performer details (user ID, email)
- Timestamp
- IP address
- Old/new status
- Data changes
- Remarks

---

## File Structure

```
kyc_verification/
├── __init__.py
├── admin.py           # Django admin configuration
├── apps.py            # App configuration
├── models.py          # Database models (8 models)
├── permissions.py     # Custom permission classes
├── serializers.py     # API serializers
├── tests.py           # Unit tests (38 tests)
├── urls.py            # URL routing
├── views.py           # API views
└── migrations/
    ├── __init__.py
    └── 0001_initial.py
```

---

## Summary

- **Total Tests**: 38 (all passing)
- **Total Models**: 8
- **Total Endpoints**: 18
- **Security**: Fernet encryption, data masking, file size limits
- **Integration**: Custom User model, RBAC system
- **Authentication**: JWT Bearer tokens

---

*Last Updated: December 5, 2025*
*Version: 1.0.0*
