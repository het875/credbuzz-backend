# Architecture & Design Guide - CredbuzzPay ERP System

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Design](#database-design)
3. [API Architecture](#api-architecture)
4. [Authentication & Authorization](#authentication--authorization)
5. [Encryption & Security](#encryption--security)
6. [Error Handling](#error-handling)
7. [Performance Optimization](#performance-optimization)
8. [Scalability](#scalability)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Applications                      │
│              (Web, Mobile, Admin Dashboard)                  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Gateway / Nginx                          │
│        (Load Balancer, SSL Termination, Rate Limiting)       │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    ┌───────┐   ┌───────┐   ┌───────┐
    │Django│   │Django│   │Django│
    │App-1 │   │App-2 │   │App-N │
    │(8001)│   │(8002)│   │(800N)│
    └───┬──┘   └───┬──┘   └───┬──┘
        │          │          │
        └──────────┼──────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    ┌────────┐ ┌─────────┐ ┌──────────┐
    │Database│ │  Cache  │ │Task Queue│
    │(Postgres)│(Redis)  │ │ (Celery) │
    └────────┘ └─────────┘ └──────────┘
```

### Application Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Views/Viewsets                          │
│              (HTTP Request Handlers)                         │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Serializers                             │
│        (Request/Response Data Transformation)               │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Services Layer                          │
│       (OTPService, AuditService, KYCService, etc.)          │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Utilities Layer                         │
│    (Validators, Encryption, CodeGenerator, Security)        │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                       Models Layer                           │
│              (Database ORM Objects)                          │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack by Layer

| Layer | Technology |
|-------|-----------|
| Frontend | React/Vue.js, React Native |
| API Gateway | Nginx, AWS ALB |
| Application | Django 5.2, DRF 3.16, Python 3.12 |
| Database | PostgreSQL 15, Redis 7 |
| Task Queue | Celery 5.4 with Redis Broker |
| Caching | Redis, Django Cache Framework |
| Search | Elasticsearch (future) |
| Monitoring | Sentry, Prometheus, ELK Stack |
| CDN | CloudFront / Cloudflare |

---

## Database Design

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    UserAccount (Users)                       │
│                                                               │
│ - user_code (PK)          - email_verified_at               │
│ - email                   - mobile_verified_at              │
│ - mobile                  - kyc_verification_step           │
│ - password_hash           - is_kyc_complete                 │
│ - first_name              - is_blocked                      │
│ - last_name               - blocked_until                   │
│ - gender                  - created_at                      │
│ - dob                     - updated_at                      │
│ - user_role               - updated_by_user_id              │
└────────┬────────────────────────────────────────────────────┘
         │
    ┌────┴─────────────────────┬──────────────────┬──────────────┐
    ▼                           ▼                  ▼              ▼
┌─────────────────┐    ┌──────────────────┐  ┌─────────────┐  ┌──────────────────┐
│  SecuritySettings│    │RegistrationProgress│ │OTPRecord  │  │ LoginActivity   │
│                 │    │                  │  │           │  │                │
│ - user_code (FK)│    │ - user_code (FK) │  │ - id (PK) │  │ - id (PK)       │
│ - 2fa_enabled   │    │ - step_1_completed│  │ - user... │  │ - login_id      │
│ - 2fa_method    │    │ - step_2_completed│  │ - otp_type│  │ - status        │
│ - ip_whitelist  │    │ - step_3_completed│  │ - expires │  │ - ip_address    │
└─────────────────┘    └──────────────────┘  │ - is_used │  │ - device_info   │
                                              │ - attempts│  │ - risk_score    │
                                              └─────────────┘  └──────────────────┘

┌─────────────────┐    ┌──────────────────┐  ┌─────────────┐
│ AadhaarKYC      │    │   PANKYC         │  │BankDetails  │
│                 │    │                  │  │             │
│ - user_account..│    │ - user_account.. │  │ - user_acc..│
│ - aadhaar_number│    │ - pan_number     │  │ - bank_name │
│ - encrypted_data│    │ - is_verified    │  │ - encrypted │
└─────────────────┘    └──────────────────┘  └─────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│ UserPlatformAccess   │  │ AppAccessControl     │
│                      │  │                      │
│ - user_code (FK)     │  │ - user_code (FK)     │
│ - platform           │  │ - app_feature (FK)   │
│ - is_allowed         │  │ - access_level       │
└──────────────────────┘  └──────────────────────┘

┌──────────────────────┐
│    AuditTrail        │
│                      │
│ - id (PK)           │
│ - user_code (FK)     │
│ - action             │
│ - resource_type      │
│ - old_values         │
│ - new_values         │
│ - timestamp          │
└──────────────────────┘
```

### Database Optimization

#### Indexes

```python
class UserAccount(models.Model):
    # Single Column Indexes
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['mobile']),
            models.Index(fields=['user_code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['user_role']),
            models.Index(fields=['created_at']),
            
            # Composite Indexes for common queries
            models.Index(fields=['user_role', 'is_active']),
            models.Index(fields=['is_kyc_complete', 'created_at']),
            models.Index(fields=['email', 'is_active']),
        ]
```

#### Query Optimization

```python
# SELECT_RELATED for Foreign Keys
UserAccount.objects.select_related('branch', 'created_by_user')

# PREFETCH_RELATED for Many-to-Many
UserAccount.objects.prefetch_related('app_access_control', 'platform_access')

# Only select needed fields
UserAccount.objects.values_list('user_code', 'email', 'mobile')

# Avoid N+1 queries
users = UserAccount.objects.select_related(
    'branch',
    'created_by_user'
).prefetch_related(
    'app_access_control__app_feature',
    'platform_access',
    'audit_trail'
)
```

---

## API Architecture

### RESTful API Design Principles

#### Resource-Oriented URLs

```
Authentication:
POST   /api/v1/auth/register/initiate
POST   /api/v1/auth/register/verify-otp
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password

Users:
GET    /api/v1/users/
GET    /api/v1/users/{user_code}
PUT    /api/v1/users/{user_code}
POST   /api/v1/users/{user_code}/assign-role
POST   /api/v1/users/{user_code}/block

KYC:
POST   /api/v1/kyc/aadhaar/submit
POST   /api/v1/kyc/aadhaar/verify-otp
GET    /api/v1/kyc/status/{user_code}

Reports:
GET    /api/v1/reports/kyc-status/
GET    /api/v1/reports/login-activity/
GET    /api/v1/reports/user-audit-trail/
```

#### HTTP Status Codes

```
200 OK                   - Request succeeded
201 Created              - Resource created successfully
204 No Content           - Resource deleted successfully
400 Bad Request          - Invalid input
401 Unauthorized         - Authentication required
403 Forbidden            - Insufficient permissions
404 Not Found            - Resource not found
409 Conflict             - Resource already exists
429 Too Many Requests    - Rate limit exceeded
500 Server Error         - Internal server error
503 Service Unavailable  - Server temporarily unavailable
```

#### Response Format

```json
{
  "success": true,
  "data": {
    "user_code": "ABC123",
    "email": "user@example.com"
  },
  "message": "Operation successful",
  "errors": []
}
```

### API Versioning

```
/api/v1/    - Version 1 (Current)
/api/v2/    - Version 2 (Future)

# Backward compatibility maintained
# Deprecation warnings for v1 in v2
```

---

## Authentication & Authorization

### JWT Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Frontend)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ POST /auth/login
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 Django Authentication                        │
│          (Verify email/mobile & password)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Generate Tokens
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                JWT Token Generation                          │
│  Access Token:  15 minutes validity                         │
│  Refresh Token: 7 days validity                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Return tokens
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Client Stores Tokens Securely                     │
│  - LocalStorage (XSS vulnerable - be careful)               │
│  - IndexedDB                                                 │
│  - SessionStorage                                            │
│  - Secure Cookie (HttpOnly, Secure flags)                   │
└─────────────────────────────────────────────────────────────┘
                     │
                     │ Subsequent Requests
                     │ Authorization: Bearer <access_token>
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Middleware Validates JWT Token                     │
│          (Extract user from token claims)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼ (Expired)      ▼ (Valid)
┌──────────────┐      ┌────────────────┐
│ Request      │      │Grant Access    │
│ /auth/       │      │(Execute View)  │
│refresh/      │      └────────────────┘
│with refresh  │
│token         │
└──────────────┘
```

### Role-Based Access Control

```
Super Admin
    ├── Assign roles to users
    ├── Block/unblock users
    ├── View all audit trails
    ├── Generate reports
    └── Configure features

Admin
    ├── Manage users (within branch)
    ├── View audit trails
    ├── Generate branch reports
    ├── Grant feature access
    └── Verify KYC documents

User
    ├── View own profile
    ├── Submit KYC documents
    ├── View own audit trail
    └── Change own password
```

### Permission Hierarchy

```python
class IsSuperAdmin(permissions.BasePermission):
    """Only super admins can access."""
    def has_permission(self, request, view):
        return request.user.user_role == 'super_admin'

class HasFeatureAccess(permissions.BasePermission):
    """User has access to specific feature."""
    def has_permission(self, request, view):
        feature_code = view.kwargs.get('feature_code')
        return AppAccessControl.objects.filter(
            user_code=request.user.user_code,
            app_feature__feature_code=feature_code
        ).exists()
```

---

## Encryption & Security

### Data Protection

#### Sensitive Fields Encrypted

```
1. Aadhaar Number
   - Algorithm: Fernet (AES)
   - Key: Derived from ENCRYPTION_KEY
   - Stored as: Base64-encoded ciphertext

2. Bank Account Number
   - Algorithm: Fernet (AES)
   - Masked display: XXXXXXXX1234

3. OTP Codes
   - Algorithm: PBKDF2 (Django's make_password)
   - Verified using check_password()
```

#### Encryption Implementation

```python
from cryptography.fernet import Fernet
import hashlib
import base64

def get_cipher():
    """Derive cipher from encryption key."""
    key = settings.ENCRYPTION_KEY
    # Derive 32-byte key from ENCRYPTION_KEY
    derived_key = hashlib.sha256(key.encode()).digest()
    cipher_key = base64.urlsafe_b64encode(derived_key)
    return Fernet(cipher_key)

def encrypt_data(plaintext):
    """Encrypt sensitive data."""
    cipher = get_cipher()
    return cipher.encrypt(plaintext.encode()).decode()

def decrypt_data(ciphertext):
    """Decrypt sensitive data."""
    cipher = get_cipher()
    return cipher.decrypt(ciphertext.encode()).decode()

# Usage
encrypted_aadhaar = encrypt_data('123456789012')
decrypted_aadhaar = decrypt_data(encrypted_aadhaar)
```

### Authentication Security

#### Password Hashing

```python
from django.contrib.auth.hashers import make_password, check_password

# Hashing during registration
user.password = make_password(raw_password)
user.save()

# Verifying during login
check_password(raw_password, user.password)
```

#### OTP Security

```python
# Generate OTP
otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

# Hash OTP for storage
hashed_otp = make_password(otp_code)
OTPRecord.objects.create(
    user_account=user,
    email_otp=hashed_otp,  # Stored hashed
    expires_at=timezone.now() + timedelta(minutes=10)
)

# Verify OTP on submission
otp_record = OTPRecord.objects.get(user_code=user_code)
if check_password(submitted_otp, otp_record.email_otp):
    # Valid
    pass
```

### Security Headers

```nginx
# Nginx configuration
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

---

## Error Handling

### Exception Hierarchy

```python
# Custom Exceptions
class BaseAPIException(Exception):
    """Base exception for all API errors."""
    status_code = 500
    message = "An error occurred"

class ValidationException(BaseAPIException):
    """Invalid input data."""
    status_code = 400

class AuthenticationException(BaseAPIException):
    """Authentication failed."""
    status_code = 401

class PermissionException(BaseAPIException):
    """Permission denied."""
    status_code = 403

class ResourceNotFoundException(BaseAPIException):
    """Resource not found."""
    status_code = 404

class RateLimitException(BaseAPIException):
    """Rate limit exceeded."""
    status_code = 429
```

### Error Response Format

```json
{
  "success": false,
  "message": "Validation error",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format",
      "code": "INVALID_EMAIL"
    }
  ],
  "timestamp": "2024-11-07T09:30:00Z",
  "request_id": "req_123456"
}
```

---

## Performance Optimization

### Caching Strategy

```python
# Cache frequently accessed data
from django.core.cache import cache

# Cache user data
cache_key = f'user:{user_code}'
user_data = cache.get(cache_key)
if not user_data:
    user_data = UserAccount.objects.get(user_code=user_code)
    cache.set(cache_key, user_data, 3600)  # 1 hour TTL

# Cache feature access
cache_key = f'features:{user_code}'
features = cache.get(cache_key)
if not features:
    features = AppAccessControl.objects.filter(
        user_code=user_code
    ).values_list('app_feature__feature_code')
    cache.set(cache_key, features, 3600)
```

### Database Query Optimization

```python
# 1. Use select_related for ForeignKey
users = UserAccount.objects.select_related(
    'branch',
    'created_by_user'
)

# 2. Use prefetch_related for ManyToMany
users = UserAccount.objects.prefetch_related(
    'app_access_control',
    'platform_access'
)

# 3. Only select needed fields
users = UserAccount.objects.values_list(
    'user_code', 'email', 'mobile'
)

# 4. Use pagination
from django.core.paginator import Paginator
paginator = Paginator(users, 50)
page = paginator.get_page(1)
```

### API Response Optimization

```python
# 1. Field filtering
?fields=user_code,email,mobile

# 2. Sparse fieldsets
?include=user,branch&fields[user]=email,mobile

# 3. Limit nested relationships depth
?depth=1

# 4. Compression (Gzip)
# Configured in Nginx/Web server
```

---

## Scalability

### Horizontal Scaling

```
Load Balancer
    │
    ├─→ App Instance 1
    ├─→ App Instance 2
    └─→ App Instance N

Database
    ├─ Primary (Write)
    ├─ Replica 1 (Read)
    └─ Replica N (Read)

Cache
    └─ Distributed Redis Cluster

Task Queue
    ├─ Celery Worker 1
    ├─ Celery Worker 2
    └─ Celery Worker N
```

### Caching Layers

```
L1: Application Cache (Redis)
    ├ User sessions
    ├ Feature access
    └ OTP records

L2: CDN Cache (CloudFront)
    ├ Static files
    ├ API responses
    └ Images

L3: Database Cache
    ├ Query results
    └ Frequently accessed records
```

### Database Sharding (Future)

```
User Accounts
├─ Shard 1: user_code A-M
├─ Shard 2: user_code N-Z
└─ Shard 3: user_code 0-9

Audit Trail (by date)
├─ 2024-11: partition_1
├─ 2024-12: partition_2
└─ 2025-01: partition_3
```

### Monitoring & Alerting

```
Application Metrics:
├─ Request Rate
├─ Response Time
├─ Error Rate
└─ Concurrent Users

Infrastructure Metrics:
├─ CPU Usage
├─ Memory Usage
├─ Disk I/O
└─ Network Bandwidth

Alerts:
├─ Error rate > 1%
├─ Response time > 2s
├─ CPU > 80%
└─ Memory > 85%
```

---

**Last Updated:** November 2025
**Version:** 1.0.0
