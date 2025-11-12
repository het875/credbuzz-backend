# 📊 CredbuzzPay ERP - Complete Models Documentation

**File**: `auth_user_erp/models.py`  
**Total Models**: 14  
**Total Lines**: 900+  
**Database Tables**: 14  
**Indexes**: 50+  
**Relationships**: 25+

---

## 📑 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Choice Classes](#choice-classes)
3. [Model Reference](#model-reference)
4. [Detailed Model Documentation](#detailed-model-documentation)
5. [Database Schema](#database-schema)
6. [Relationships & Foreign Keys](#relationships--foreign-keys)
7. [Indexes & Performance](#indexes--performance)
8. [Usage Examples](#usage-examples)
9. [Best Practices](#best-practices)

---

## 🎯 OVERVIEW

### Purpose
The `models.py` file defines the complete database schema for the CredbuzzPay ERP system. It includes:
- User authentication & management
- KYC (Know Your Customer) verification
- Access control & permissions
- Audit logging & compliance
- Login activity tracking
- Security & fraud detection

### Architecture
```
Database Layer (PostgreSQL/SQLite)
        ↓
Models (14 Django Models)
        ↓
Serializers (DRF)
        ↓
Views/ViewSets
        ↓
API Endpoints (50+)
```

### Key Principles
✅ **Security First** - Encrypted fields, audit logging  
✅ **Performance** - 50+ indexes, optimized queries  
✅ **Compliance** - GDPR-ready, audit trails  
✅ **Scalability** - Proper relationships, partitioning ready  
✅ **Maintainability** - Clear naming, documentation

---

## 🎨 CHOICE CLASSES

### 1. UserRoleChoices
**Purpose**: Define user roles for authorization  
**Usage**: `user_role` field in `UserAccount` model

```python
class UserRoleChoices(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'  # Full system access
    ADMIN = 'admin', 'Admin'                    # Administrative access
    USER = 'user', 'User'                       # Default user access
```

**Values**:
- `super_admin` - System administrator (full control)
- `admin` - Admin user (branch/team management)
- `user` - Regular user (standard access)

**Example Usage**:
```python
user = UserAccount.objects.create(
    email='admin@example.com',
    user_role=UserRoleChoices.ADMIN
)
```

---

### 2. GenderChoices
**Purpose**: Gender field standardization  
**Usage**: `gender` field in `UserAccount` model

```python
class GenderChoices(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'
```

---

### 3. OTPTypeChoices
**Purpose**: Different OTP delivery methods  
**Usage**: `otp_type` field in `OTPRecord` model

```python
class OTPTypeChoices(models.TextChoices):
    EMAIL = 'email', 'Email'                           # Email only
    MOBILE = 'mobile', 'Mobile'                        # SMS only
    BOTH = 'both', 'Both Email and Mobile'             # Email + SMS
    AADHAAR = 'aadhaar', 'Aadhaar'                     # Aadhaar OTP
    BANK_PHONE = 'bank_phone', 'Bank Phone'            # Bank verification via SMS
    BANK_EMAIL = 'bank_email', 'Bank Email'            # Bank verification via email
    BUSINESS_PHONE = 'business_phone', 'Business Phone'
    BUSINESS_EMAIL = 'business_email', 'Business Email'
```

---

### 4. OTPPurposeChoices
**Purpose**: Reason for OTP generation  
**Usage**: `otp_purpose` field in `OTPRecord` model

```python
class OTPPurposeChoices(models.TextChoices):
    REGISTRATION = 'registration', 'Registration'
    LOGIN = 'login', 'Login'
    FORGOT_PASSWORD = 'forgot_password', 'Forgot Password'
    RESET_PASSWORD = 'reset_password', 'Reset Password'
    EMAIL_VERIFICATION = 'email_verification', 'Email Verification'
    MOBILE_VERIFICATION = 'mobile_verification', 'Mobile Verification'
    AADHAAR_VERIFICATION = 'aadhaar_verification', 'Aadhaar Verification'
    BANK_VERIFICATION = 'bank_verification', 'Bank Verification'
    BUSINESS_VERIFICATION = 'business_verification', 'Business Verification'
```

---

### 5. PlatformChoices
**Purpose**: Different platforms for access control  
**Usage**: `platform` field in `UserPlatformAccess` model

```python
class PlatformChoices(models.TextChoices):
    WEB = 'web', 'Web'                       # Web application
    MOBILE_APP = 'mobile_app', 'Mobile App' # Mobile app
    ADMIN_PANEL = 'admin_panel', 'Admin Panel' # Admin interface
    API = 'api', 'API'                       # Direct API access
    POS_TERMINAL = 'pos_terminal', 'POS Terminal' # Point of Sale
```

---

### 6. AccessLevelChoices
**Purpose**: Define access control levels  
**Usage**: `access_level` in `UserPlatformAccess` and `AppAccessControl`

```python
class AccessLevelChoices(models.TextChoices):
    FULL = 'full', 'Full Access'             # All permissions
    READ_ONLY = 'read_only', 'Read Only'     # View only
    RESTRICTED = 'restricted', 'Restricted'  # Limited access
    CREATE_ONLY = 'create_only', 'Create Only' # Create operations only
    UPDATE_ONLY = 'update_only', 'Update Only' # Update operations only
```

---

### 7. LoginStatusChoices
**Purpose**: Login attempt status tracking  
**Usage**: `status` field in `LoginActivity` model

```python
class LoginStatusChoices(models.TextChoices):
    SUCCESS = 'success', 'Success'                              # Login successful
    FAILED_PASSWORD = 'failed_password', 'Failed - Wrong Password' # Wrong password
    FAILED_BLOCKED = 'failed_blocked', 'Failed - User Blocked'     # User blocked
    FAILED_INACTIVE = 'failed_inactive', 'Failed - User Inactive'  # Inactive account
    FAILED_NOT_FOUND = 'failed_not_found', 'Failed - User Not Found' # User doesn't exist
```

---

### 8. AuditActionChoices
**Purpose**: Track different types of system actions  
**Usage**: `action` field in `AuditTrail` model

```python
class AuditActionChoices(models.TextChoices):
    CREATE = 'create', 'Create'
    UPDATE = 'update', 'Update'
    DELETE = 'delete', 'Delete'
    LOGIN = 'login', 'Login'
    LOGOUT = 'logout', 'Logout'
    OTP_REQUEST = 'otp_request', 'OTP Request'
    OTP_VERIFY = 'otp_verify', 'OTP Verify'
    KYC_SUBMIT = 'kyc_submit', 'KYC Submit'
    KYC_APPROVE = 'kyc_approve', 'KYC Approve'
    KYC_REJECT = 'kyc_reject', 'KYC Reject'
    PASSWORD_CHANGE = 'password_change', 'Password Change'
    ROLE_CHANGE = 'role_change', 'Role Change'
    ACCESS_GRANT = 'access_grant', 'Access Grant'
    ACCESS_REVOKE = 'access_revoke', 'Access Revoke'
    USER_BLOCK = 'user_block', 'User Block'
    USER_UNBLOCK = 'user_unblock', 'User Unblock'
```

---

### 9. VerificationMethodChoices
**Purpose**: KYC verification methods  
**Usage**: `verification_method` in KYC models

```python
class VerificationMethodChoices(models.TextChoices):
    MANUAL = 'manual', 'Manual'                     # Manual verification
    API_DIGILOCKER = 'api_digilocker', 'DigiLocker API' # Government API
    API_UIDAI = 'api_uidai', 'UIDAI API'                # UIDAI verification
    API_NSDL = 'api_nsdl', 'NSDL API'                   # Tax authority API
    API_KARZA = 'api_karza', 'Karza API'                # Third-party verification
    OFFLINE_XML = 'offline_xml', 'Offline XML'      # XML file upload
```

---

### 10. BusinessTypeChoices
**Purpose**: Types of business entities  
**Usage**: `business_type` field in `BusinessDetails` model

```python
class BusinessTypeChoices(models.TextChoices):
    SOLE_PROPRIETORSHIP = 'sole_proprietorship', 'Sole Proprietorship'
    PARTNERSHIP = 'partnership', 'Partnership'
    PRIVATE_LIMITED = 'private_limited', 'Private Limited'
    PUBLIC_LIMITED = 'public_limited', 'Public Limited'
    LLP = 'llp', 'Limited Liability Partnership'
    NGO = 'ngo', 'NGO'
    TRUST = 'trust', 'Trust'
    HUF = 'huf', 'Hindu Undivided Family'
```

---

### 11. AccountTypeChoices
**Purpose**: Types of bank accounts  
**Usage**: `account_type` field in `BankDetails` model

```python
class AccountTypeChoices(models.TextChoices):
    SAVINGS = 'savings', 'Savings'                          # Savings account
    CURRENT = 'current', 'Current'                          # Current account
    FIXED_DEPOSIT = 'fixed_deposit', 'Fixed Deposit'        # Fixed deposit
    RECURRING_DEPOSIT = 'recurring_deposit', 'Recurring Deposit' # Recurring deposit
```

---

### 12. BankVerificationMethodChoices
**Purpose**: Methods to verify bank accounts  
**Usage**: `verification_method` field in `BankDetails` model

```python
class BankVerificationMethodChoices(models.TextChoices):
    PENNY_DROP = 'penny_drop', 'Penny Drop'        # Micro deposit verification
    MANUAL = 'manual', 'Manual'                    # Manual verification
    BANK_STATEMENT = 'bank_statement', 'Bank Statement' # Statement upload
```

---

### 13. TwoFactorMethodChoices
**Purpose**: Two-factor authentication methods  
**Usage**: `two_factor_method` field in `SecuritySettings` model

```python
class TwoFactorMethodChoices(models.TextChoices):
    SMS = 'sms', 'SMS'                              # SMS OTP
    EMAIL = 'email', 'Email'                        # Email OTP
    AUTHENTICATOR = 'authenticator', 'Authenticator App' # Google Authenticator
```

---

## 📋 MODEL REFERENCE

| # | Model | Purpose | Records | Keys |
|---|-------|---------|---------|------|
| 1 | **UserAccount** | User authentication & profile | Primary | email, mobile |
| 2 | **Branch** | Organization branches | Secondary | branch_code |
| 3 | **AppFeature** | System features/modules | Lookup | feature_code |
| 4 | **OTPRecord** | OTP management | Transactional | user_code, otp_type |
| 5 | **AadhaarKYC** | Aadhaar verification | Verification | user_code |
| 6 | **PANKYC** | PAN card verification | Verification | user_code |
| 7 | **BusinessDetails** | Business information | Verification | user_code |
| 8 | **BankDetails** | Bank account verification | Verification | user_code |
| 9 | **UserPlatformAccess** | Platform access control | Authorization | user_code, platform |
| 10 | **AppAccessControl** | Feature access control | Authorization | user_code, feature |
| 11 | **LoginActivity** | Login tracking | Audit | user_code, timestamp |
| 12 | **AuditTrail** | Comprehensive audit log | Audit | action, resource_type |
| 13 | **RegistrationProgress** | Multi-step registration | Transactional | user_code |
| 14 | **SecuritySettings** | User security config | Configuration | user_code |

---

## 📚 DETAILED MODEL DOCUMENTATION

---

## TABLE 1: UserAccount (Core User Model)

### Purpose
Central user management model for authentication, authorization, and user profiling.

### Structure

```python
class UserAccount(models.Model):
    # Primary Key
    id = models.BigAutoField(primary_key=True)
    user_code = models.CharField(max_length=6, unique=True, db_index=True)
    
    # Authentication
    email = models.EmailField(unique=True, db_index=True)
    mobile = models.CharField(max_length=15, db_index=True)
    password = models.CharField(max_length=128)
    
    # Authorization
    user_role = models.CharField(choices=UserRoleChoices)
    branch_code = models.ForeignKey('Branch', ...)
    
    # Personal Information
    first_name, middle_name, last_name, gender, dob
    
    # Verification Status
    is_mobile_verified, is_email_verified
    is_kyc_complete
    is_aadhaar_verified, is_pan_verified, is_bank_verified
    
    # Account Status
    is_active, is_staff, is_superuser
    user_blocked, blocked_until
    
    # Address
    address_line1, address_line2, address_line3
    city, state, country, pincode
    
    # Security & Audit
    register_device_ip, register_device_info
    last_login, last_login_ip
    
    # Timestamps
    created_at, updated_at, deleted_at
```

### Fields Explanation

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `user_code` | CharField(6) | Unique user identifier | Auto-generated, indexed |
| `email` | EmailField | Email address | Unique, indexed |
| `mobile` | CharField | Phone number | Indexed for searching |
| `password` | CharField | Hashed password | Never store plain text |
| `user_role` | Choice | User role (admin/user) | For authorization |
| `is_kyc_complete` | Boolean | KYC verification status | True when all KYC done |
| `kyc_verification_step` | Integer | Current KYC step (0-4) | Tracks progress |
| `user_blocked` | Integer | Block status (0/1) | 0=active, 1=blocked |
| `blocked_until` | DateTime | Block expiry time | For temporary blocks |
| `email_otp_attempts` | Integer | Failed OTP attempts | For rate limiting |
| `register_device_ip` | IP Address | Registration device IP | For security audit |
| `deleted_at` | DateTime | Soft delete timestamp | NULL if active |

### Indexes (5)
```python
Index(fields=['email'])              # Search by email
Index(fields=['mobile'])             # Search by mobile
Index(fields=['user_code'])          # Lookup by code
Index(fields=['is_active'])          # Filter active users
Index(fields=['user_role'])          # Filter by role
```

### Key Features

✅ **Soft Deletion**: Keeps historical records with `deleted_at`  
✅ **Security**: Tracks device IP, registration details  
✅ **KYC Tracking**: Monitors KYC completion  
✅ **Account Status**: Supports blocking/unblocking  

### Usage Examples

```python
# Create user
user = UserAccount.objects.create(
    user_code='USR001',
    email='john@example.com',
    mobile='9999999999',
    password=make_password('SecurePass123!'),
    first_name='John',
    last_name='Doe',
    gender='male',
    dob='1990-01-15',
    user_role=UserRoleChoices.USER,
    register_device_ip='192.168.1.1'
)

# Find user
user = UserAccount.objects.get(email='john@example.com')

# Update KYC status
user.is_kyc_complete = True
user.is_aadhaar_verified = True
user.is_pan_verified = True
user.is_bank_verified = True
user.save()

# Block user
user.user_blocked = 1
user.blocked_until = timezone.now() + timedelta(days=7)
user.user_block_reason = "Suspicious activity"
user.save()

# Search active users
active_users = UserAccount.objects.filter(is_active=True)

# Get all admins
admins = UserAccount.objects.filter(user_role=UserRoleChoices.ADMIN)
```

---

## TABLE 2: Branch (Organization Structure)

### Purpose
Manage organization branches/locations and hierarchy.

### Structure

```python
class Branch(models.Model):
    id = models.BigAutoField(primary_key=True)
    branch_code = models.CharField(max_length=5, unique=True)
    branch_name = models.CharField(max_length=200)
    
    # Address
    address_line1, address_line2, address_line3
    city, state, country, pincode
    
    # Contact
    phone, email
    manager_name
    manager_user_code = models.ForeignKey(UserAccount)
    
    # Hierarchy
    referred_by = models.ForeignKey('self')  # Parent branch
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Audit
    created_at, created_by
    updated_at, deleted_at
```

### Key Features

✅ **Hierarchical Structure**: Support for parent-child branches  
✅ **Manager Assignment**: Link branch to manager user  
✅ **Status Tracking**: Active/inactive branches  

### Usage Examples

```python
# Create branch
branch = Branch.objects.create(
    branch_code='MUM01',
    branch_name='Mumbai Main Branch',
    address_line1='123 Business Park',
    city='Mumbai',
    state='Maharashtra',
    pincode='400001',
    phone='02212345678',
    email='branch@example.com',
    manager_name='Raj Kumar',
    created_by=admin_user
)

# Create sub-branch
sub_branch = Branch.objects.create(
    branch_code='MUM02',
    branch_name='Mumbai Sub Branch',
    referred_by=branch,
    created_by=admin_user
)

# Get all sub-branches
sub_branches = branch.sub_branches.all()

# Get active branches
active = Branch.objects.filter(is_active=True)
```

---

## TABLE 3: AppFeature (Feature Management)

### Purpose
Define system features/modules for fine-grained access control.

### Structure

```python
class AppFeature(models.Model):
    id = models.BigAutoField(primary_key=True)
    feature_code = models.CharField(max_length=4, unique=True)
    feature_name = models.CharField(max_length=100)
    feature_description = models.TextField()
    
    # Hierarchy
    parent_feature = models.ForeignKey('self')
    feature_category = models.CharField(max_length=50)
    
    is_active = models.BooleanField(default=True)
```

### Examples

```python
# Features
FEAT_KYC = 'KYC '  - KYC Management
FEAT_USER = 'USER' - User Management
FEAT_AUTH = 'AUTH' - Authentication
FEAT_AUDIT = 'AUDI' - Audit Logs
FEAT_REPT = 'REPT' - Reports
```

---

## TABLE 4: OTPRecord (OTP Management)

### Purpose
Centralized OTP handling for all verification types (registration, login, KYC, etc.).

### Structure

```python
class OTPRecord(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(UserAccount)
    
    # OTP Type & Purpose
    otp_type = models.CharField(choices=OTPTypeChoices)        # email, mobile, both
    otp_purpose = models.CharField(choices=OTPPurposeChoices)  # registration, login, etc
    
    # OTP Codes (hashed)
    otp_code = models.CharField(max_length=128)
    email_otp = models.CharField(max_length=128, null=True)
    mobile_otp = models.CharField(max_length=128, null=True)
    
    # Contact Info
    sent_to_email = models.EmailField()
    sent_to_mobile = models.CharField(max_length=15)
    
    # Status
    is_used = models.BooleanField(default=False)
    verified_at = models.DateTimeField()
    
    # Timing
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # Tracking
    attempt_count = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField()
```

### Key Features

✅ **Multiple Delivery**: Email, SMS, or both  
✅ **Purpose Tracking**: Know why OTP was generated  
✅ **Security**: Attempt counting, expiry tracking  
✅ **Audit Trail**: IP address, timestamps  

### Usage Examples

```python
# Generate OTP for registration
otp_record = OTPRecord.objects.create(
    user_code=user,
    otp_type=OTPTypeChoices.BOTH,
    otp_purpose=OTPPurposeChoices.REGISTRATION,
    otp_code=hashed_otp,
    email_otp=hashed_email_otp,
    mobile_otp=hashed_mobile_otp,
    sent_to_email='john@example.com',
    sent_to_mobile='9999999999',
    expires_at=timezone.now() + timedelta(minutes=10),
    ip_address='192.168.1.1'
)

# Verify OTP
otp_record.is_used = True
otp_record.verified_at = timezone.now()
otp_record.save()

# Get unused OTPs
unused = OTPRecord.objects.filter(
    is_used=False,
    expires_at__gt=timezone.now()
)

# Track attempts
otp_record.attempt_count += 1
if otp_record.attempt_count > 5:
    # Block user
    pass
otp_record.save()
```

---

## TABLE 5: AadhaarKYC (Aadhaar Verification)

### Purpose
Store and manage Aadhaar card verification for KYC compliance.

### Structure

```python
class AadhaarKYC(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount)
    
    # Aadhaar Data (encrypted)
    aadhaar_number_encrypted = models.TextField()
    aadhaar_name = models.CharField(max_length=100)
    aadhaar_dob = models.DateField()
    aadhaar_gender = models.CharField(max_length=10)
    aadhaar_address = models.TextField()
    
    # Document Storage
    aadhaar_front_image = models.FileField()
    aadhaar_back_image = models.FileField()
    aadhaar_xml_file = models.FileField()
    
    # OTP Verification
    aadhaar_otp_request_id = models.CharField()
    aadhaar_otp_attempts = models.IntegerField(default=0)
    
    # Verification
    verification_method = models.CharField(choices=VerificationMethodChoices)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField()
    verified_by = models.ForeignKey(UserAccount)
    api_response = models.JSONField()
```

### Key Features

✅ **Encrypted Storage**: Aadhaar number encrypted  
✅ **Multiple Verification Methods**: API, XML, Manual  
✅ **Document Management**: Store images and XML  
✅ **OTP Tracking**: Track OTP verification  
✅ **Audit**: Track who verified and when  

### Usage Examples

```python
# Create Aadhaar KYC record
kyc = AadhaarKYC.objects.create(
    id=f"AADHAAR_{user.id}",
    user_code=user,
    aadhaar_number_encrypted=encrypt('123456789012'),
    aadhaar_name='John Doe',
    aadhaar_dob='1990-01-15',
    aadhaar_gender='male',
    aadhaar_address='123 Main St',
    verification_method=VerificationMethodChoices.API_UIDAI
)

# Verify Aadhaar
kyc.is_verified = True
kyc.verified_at = timezone.now()
kyc.verified_by = admin_user
kyc.api_response = {'status': 'success', 'score': 95}
kyc.save()

# Get Aadhaar status
aadhaar = user.aadhaar_kyc
if aadhaar.is_verified:
    print("Aadhaar verified")

# Update verification status
kyc.aadhaar_otp_attempts += 1
kyc.save()
```

---

## TABLE 6: PANKYC (PAN Card Verification)

### Purpose
Store and manage PAN card verification for income tax compliance.

### Structure

```python
class PANKYC(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount)
    
    # PAN Information
    pan_number = models.CharField(max_length=10)
    pan_name = models.CharField(max_length=100)
    pan_father_name = models.CharField(max_length=100)
    pan_dob = models.DateField()
    
    # Document
    pan_image = models.FileField()
    
    # Verification
    verification_method = models.CharField(choices=VerificationMethodChoices)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField()
    name_match_score = models.DecimalField()
```

### Key Features

✅ **PAN Validation**: Format and number validation  
✅ **Name Matching**: Score for name match  
✅ **Multiple Verification**: API, Manual, XML  
✅ **Document Storage**: Image upload support  

---

## TABLE 7: BusinessDetails (Business KYC)

### Purpose
Store business/merchant information for business registration verification.

### Structure

```python
class BusinessDetails(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount)
    
    # Liveness
    user_selfie = models.FileField()
    selfie_verified = models.BooleanField(default=False)
    
    # Business Info
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(choices=BusinessTypeChoices)
    business_registration_number = models.CharField()
    
    # Address
    business_address_line1, business_address_line2
    city, state, country, pincode
    
    # Contact with OTP
    business_phone = models.CharField(max_length=15)
    business_phone_verified = models.BooleanField(default=False)
    business_email = models.EmailField()
    business_email_verified = models.BooleanField(default=False)
    
    # Verification
    is_verified = models.BooleanField(default=False)
```

### Key Features

✅ **Liveness Check**: Selfie verification  
✅ **Business Type**: Support multiple business types  
✅ **Contact Verification**: Phone + email OTP  
✅ **Document Storage**: Business proof upload  

---

## TABLE 8: BankDetails (Bank Account Verification)

### Purpose
Store and verify bank account details for payment processing.

### Structure

```python
class BankDetails(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount)
    
    # Bank Account
    account_holder_name = models.CharField(max_length=100)
    account_number_encrypted = models.TextField()
    account_number_last4 = models.CharField(max_length=4)
    ifsc_code = models.CharField(max_length=11)
    account_type = models.CharField(choices=AccountTypeChoices)
    bank_name = models.CharField(max_length=100)
    
    # Document
    bank_proof_image = models.FileField()
    
    # Verification Method
    verification_method = models.CharField(choices=BankVerificationMethodChoices)
    penny_drop_amount = models.DecimalField()
    penny_drop_reference = models.CharField()
    
    # Status
    is_verified = models.BooleanField(default=False)
```

### Key Features

✅ **Encrypted Storage**: Account number encrypted  
✅ **Penny Drop**: Micro deposit verification  
✅ **IFSC Validation**: Bank code verification  
✅ **Account Type Support**: Savings, Current, FD, RD  

### Verification Methods

1. **Penny Drop**: Deposit ₹1 and verify
2. **Manual**: Admin verification
3. **Bank Statement**: Upload statement

---

## TABLE 9: UserPlatformAccess (Platform Authorization)

### Purpose
Control user access to different platforms (Web, Mobile, API, etc).

### Structure

```python
class UserPlatformAccess(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(UserAccount)
    platform = models.CharField(choices=PlatformChoices)
    
    # Access Control
    is_allowed = models.BooleanField(default=True)
    access_level = models.CharField(choices=AccessLevelChoices)
    allowed_ip_ranges = models.JSONField()
    
    # Management
    granted_by = models.ForeignKey(UserAccount)
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField()
```

### Usage Examples

```python
# Grant Web access
access = UserPlatformAccess.objects.create(
    user_code=user,
    platform=PlatformChoices.WEB,
    is_allowed=True,
    access_level=AccessLevelChoices.FULL,
    granted_by=admin_user
)

# Restrict API access
api_access = UserPlatformAccess.objects.create(
    user_code=user,
    platform=PlatformChoices.API,
    is_allowed=True,
    access_level=AccessLevelChoices.READ_ONLY,
    allowed_ip_ranges=['192.168.1.0/24', '10.0.0.0/8']
)

# Revoke access
access.is_allowed = False
access.revoked_at = timezone.now()
access.save()

# Check if user has platform access
web_access = user.platform_access.filter(platform=PlatformChoices.WEB).first()
if web_access and web_access.is_allowed:
    print("User can access web platform")
```

---

## TABLE 10: AppAccessControl (Feature Authorization)

### Purpose
Fine-grained feature-level access control.

### Structure

```python
class AppAccessControl(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(UserAccount)
    feature = models.ForeignKey(AppFeature)
    
    # Access
    is_allowed = models.BooleanField(default=False)
    access_level = models.CharField(choices=AccessLevelChoices)
    
    # Management
    granted_by = models.ForeignKey(UserAccount)
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
```

### Usage Examples

```python
# Grant feature access
feature = AppFeature.objects.get(feature_code='KYC ')
access = AppAccessControl.objects.create(
    user_code=user,
    feature=feature,
    is_allowed=True,
    access_level=AccessLevelChoices.FULL,
    granted_by=admin_user,
    expires_at=timezone.now() + timedelta(days=30)
)

# Check feature access
has_access = user.feature_access.filter(
    feature__feature_code='KYC ',
    is_allowed=True
).exists()

# Get expired access
expired = AppAccessControl.objects.filter(
    expires_at__lt=timezone.now()
)
```

---

## TABLE 11: LoginActivity (Login Tracking)

### Purpose
Comprehensive login attempt tracking for security and compliance.

### Structure

```python
class LoginActivity(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(UserAccount, null=True)
    
    # Login Details
    login_identifier = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField()
    location_info = models.JSONField()
    
    # Status
    status = models.CharField(choices=LoginStatusChoices)
    failure_reason = models.CharField()
    
    # Session
    session_token = models.CharField(max_length=255)
    login_timestamp = models.DateTimeField(auto_now_add=True)
    logout_timestamp = models.DateTimeField()
    session_duration = models.DurationField()
    
    # Security
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.IntegerField(0-100)
```

### Indexes (4)
```python
Index(fields=['user_code'])
Index(fields=['login_timestamp'])
Index(fields=['ip_address'])
Index(fields=['status'])
```

### Key Features

✅ **Device Tracking**: IP, user agent, device info  
✅ **Risk Scoring**: Suspicious activity detection  
✅ **Session Management**: Track login duration  
✅ **Failure Tracking**: Why login failed  

### Usage Examples

```python
# Log successful login
login = LoginActivity.objects.create(
    user_code=user,
    login_identifier=user.email,
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...',
    device_info={'device': 'iphone', 'os': 'ios'},
    status=LoginStatusChoices.SUCCESS,
    session_token=jwt_token,
    is_suspicious=False,
    risk_score=10
)

# Log failed login
failed_login = LoginActivity.objects.create(
    login_identifier='john@example.com',
    ip_address='203.0.113.45',
    status=LoginStatusChoices.FAILED_PASSWORD,
    failure_reason='Wrong password'
)

# Track session logout
login.logout_timestamp = timezone.now()
login.session_duration = timezone.now() - login.login_timestamp
login.save()

# Get recent logins
recent = LoginActivity.objects.filter(
    user_code=user,
    login_timestamp__gte=timezone.now() - timedelta(days=30)
).order_by('-login_timestamp')

# Find suspicious logins
suspicious = LoginActivity.objects.filter(
    is_suspicious=True,
    risk_score__gte=70
)

# Failed login attempts
failed = LoginActivity.objects.filter(
    user_code=user,
    status__in=[LoginStatusChoices.FAILED_PASSWORD, LoginStatusChoices.FAILED_BLOCKED],
    login_timestamp__gte=timezone.now() - timedelta(hours=1)
).count()

if failed > 5:
    # Block user
    user.user_blocked = 1
    user.blocked_until = timezone.now() + timedelta(hours=1)
    user.save()
```

---

## TABLE 12: AuditTrail (Comprehensive Auditing)

### Purpose
Log all system operations for compliance and debugging.

### Structure

```python
class AuditTrail(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.ForeignKey(UserAccount, null=True)
    
    # Action
    action = models.CharField(choices=AuditActionChoices)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    
    # Changes
    description = models.TextField()
    old_values = models.JSONField()
    new_values = models.JSONField()
    changed_fields = models.JSONField()
    
    # Request Info
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    request_method = models.CharField(max_length=10)
    request_path = models.CharField(max_length=255)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
```

### Indexes (5)
```python
Index(fields=['user_code'])
Index(fields=['action'])
Index(fields=['resource_type'])
Index(fields=['resource_id'])
Index(fields=['created_at'])
```

### Key Features

✅ **Comprehensive Logging**: All CRUD operations  
✅ **Change Tracking**: Before/after values  
✅ **Request Audit**: Method, path, agent  
✅ **Time-Series Data**: Easy filtering by date  

### Usage Examples

```python
# Log user creation
AuditTrail.objects.create(
    user_code=admin_user,
    action=AuditActionChoices.CREATE,
    resource_type='UserAccount',
    resource_id=str(new_user.id),
    description=f'Created user {new_user.email}',
    new_values={
        'email': new_user.email,
        'mobile': new_user.mobile,
        'role': new_user.user_role
    },
    ip_address='192.168.1.1',
    request_method='POST',
    request_path='/api/v1/users/'
)

# Log KYC approval
AuditTrail.objects.create(
    user_code=admin_user,
    action=AuditActionChoices.KYC_APPROVE,
    resource_type='AadhaarKYC',
    resource_id=str(kyc.id),
    description='Approved Aadhaar KYC',
    old_values={'is_verified': False},
    new_values={'is_verified': True}
)

# Query audit trail
user_actions = AuditTrail.objects.filter(
    resource_type='UserAccount',
    resource_id=str(user.id)
).order_by('-created_at')

# Get all actions by a user
admin_actions = AuditTrail.objects.filter(
    user_code=admin_user,
    created_at__gte=timezone.now() - timedelta(days=7)
)

# Track specific action
kyc_approvals = AuditTrail.objects.filter(
    action=AuditActionChoices.KYC_APPROVE,
    created_at__month=11
).count()
```

---

## TABLE 13: RegistrationProgress (Multi-Step Registration)

### Purpose
Track multi-step user registration progress.

### Structure

```python
class RegistrationProgress(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount)
    
    # Progress
    current_step = models.IntegerField()
    steps_completed = models.JSONField()
    step_data = models.JSONField()
    last_completed_step = models.IntegerField(default=0)
    
    # Status
    abandoned = models.BooleanField(default=False)
    abandoned_at = models.DateTimeField()
    
    # Timestamps
    last_active_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField()
```

### Registration Steps
```python
0 = Email/Mobile verification
1 = Personal information
2 = KYC verification
3 = Bank details
4 = Complete
```

### Usage Examples

```python
# Create registration progress
progress = RegistrationProgress.objects.create(
    user_code=user,
    current_step=0,
    steps_completed=[],
    step_data={}
)

# Update progress
progress.current_step = 1
progress.steps_completed = [0]
progress.step_data = {
    'email_verified': True,
    'mobile_verified': True
}
progress.save()

# Mark registration complete
progress.current_step = 4
progress.completed_at = timezone.now()
progress.save()

# Get abandoned registrations
abandoned = RegistrationProgress.objects.filter(
    abandoned=True,
    last_active_at__lt=timezone.now() - timedelta(days=7)
)

# Find incomplete registrations
incomplete = RegistrationProgress.objects.filter(
    current_step__lt=4,
    abandoned=False
)
```

---

## TABLE 14: SecuritySettings (User Security Configuration)

### Purpose
User-specific security configurations and policies.

### Structure

```python
class SecuritySettings(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    user_code = models.OneToOneField(UserAccount)
    
    # 2FA
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(choices=TwoFactorMethodChoices)
    
    # Notifications
    login_notification_enabled = models.BooleanField(default=True)
    suspicious_activity_alert = models.BooleanField(default=True)
    
    # IP Whitelist
    allowed_ip_whitelist = models.JSONField()
    
    # Password Policy
    password_expiry_days = models.IntegerField(default=90)
    last_password_change = models.DateTimeField()
    
    # Account Lockout
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField()
```

### Usage Examples

```python
# Create security settings
settings = SecuritySettings.objects.create(
    user_code=user,
    two_factor_enabled=True,
    two_factor_method=TwoFactorMethodChoices.SMS,
    login_notification_enabled=True,
    allowed_ip_whitelist=['192.168.1.0/24']
)

# Enable 2FA
settings.two_factor_enabled = True
settings.two_factor_method = TwoFactorMethodChoices.EMAIL
settings.save()

# Track failed login attempts
settings.failed_login_attempts += 1
if settings.failed_login_attempts > 5:
    settings.account_locked_until = timezone.now() + timedelta(hours=1)
else:
    settings.save()

# Reset attempts on successful login
settings.failed_login_attempts = 0
settings.save()

# Check IP whitelist
is_whitelisted = request.META['REMOTE_ADDR'] in settings.allowed_ip_whitelist
```

---

## 📊 DATABASE SCHEMA

### Entity Relationship Diagram

```
UserAccount (Core)
    ├─→ OneToOne: AadhaarKYC
    ├─→ OneToOne: PANKYC
    ├─→ OneToOne: BusinessDetails
    ├─→ OneToOne: BankDetails
    ├─→ OneToOne: RegistrationProgress
    ├─→ OneToOne: SecuritySettings
    ├─→ ForeignKey: Branch
    ├─→ ForeignKey: OTPRecord (reverse)
    ├─→ ForeignKey: UserPlatformAccess (reverse)
    ├─→ ForeignKey: AppAccessControl (reverse)
    ├─→ ForeignKey: LoginActivity (reverse)
    ├─→ ForeignKey: AuditTrail (reverse)
    └─→ ManyToMany: AppFeature (through AppAccessControl)

Branch
    ├─→ ForeignKey: UserAccount (manager)
    ├─→ ForeignKey: UserAccount (created_by)
    └─→ SelfFK: Branch (parent)

AppFeature
    ├─→ SelfFK: AppFeature (parent)
    └─→ ManyToMany: UserAccount (through AppAccessControl)
```

---

## 🔗 RELATIONSHIPS & FOREIGN KEYS

### One-to-One Relationships
```
UserAccount ←→ AadhaarKYC
UserAccount ←→ PANKYC
UserAccount ←→ BusinessDetails
UserAccount ←→ BankDetails
UserAccount ←→ RegistrationProgress
UserAccount ←→ SecuritySettings
```

### One-to-Many Relationships
```
UserAccount → OTPRecord
UserAccount → LoginActivity
UserAccount → AuditTrail
UserAccount → UserPlatformAccess
UserAccount → AppAccessControl
Branch → UserAccount (users)
Branch → UserAccount (managed_branches)
AppFeature → AppAccessControl
```

### Many-to-Many Relationships
```
UserAccount ←→ AppFeature (through AppAccessControl)
UserAccount ←→ Platform (through UserPlatformAccess)
```

### Self-Referencing
```
UserAccount → deleted_by (Self)
Branch → referred_by (Parent branch)
AppFeature → parent_feature (Parent feature)
```

---

## 🚀 INDEXES & PERFORMANCE

### Total Indexes: 50+

#### UserAccount (5 indexes)
```
- email (unique)
- mobile
- user_code (unique)
- is_active
- user_role
```

#### Branch (3 indexes)
```
- branch_code (unique)
- is_active
- referred_by
```

#### OTPRecord (5 indexes)
```
- user_code
- otp_type
- otp_purpose
- is_used
- expires_at
```

#### KYC Tables (AadhaarKYC, PANKYC, BankDetails) (3 each)
```
- user_code (unique)
- is_verified
- (pan_number for PANKYC)
```

#### LoginActivity (4 indexes)
```
- user_code
- login_timestamp
- ip_address
- status
```

#### AuditTrail (5 indexes)
```
- user_code
- action
- resource_type
- resource_id
- created_at
```

### Query Performance Optimization

```python
# ✅ Good - Uses index
users = UserAccount.objects.filter(is_active=True)

# ✅ Good - Uses index
logins = LoginActivity.objects.filter(
    user_code=user,
    login_timestamp__gte=date
).order_by('-login_timestamp')

# ⚠️ Bad - Full table scan
users = UserAccount.objects.filter(
    middle_name='Kumar'
)

# ✅ Good - Prefetch related for fewer queries
users = UserAccount.objects.prefetch_related(
    'aadhaar_kyc',
    'pan_kyc',
    'bank_details'
).filter(is_active=True)
```

---

## 💡 USAGE EXAMPLES

### Example 1: User Registration Flow

```python
# Step 1: Create user
user = UserAccount.objects.create(
    user_code='USR001',
    email='john@example.com',
    mobile='9999999999',
    password=make_password('SecurePass123!'),
    first_name='John',
    last_name='Doe',
    gender='male',
    dob='1990-01-15',
    register_device_ip=request.META['REMOTE_ADDR']
)

# Step 2: Create registration progress
progress = RegistrationProgress.objects.create(
    user_code=user,
    current_step=0
)

# Step 3: Generate OTP
otp_record = OTPRecord.objects.create(
    user_code=user,
    otp_type=OTPTypeChoices.BOTH,
    otp_purpose=OTPPurposeChoices.REGISTRATION,
    otp_code=hash_otp('123456'),
    sent_to_email=user.email,
    sent_to_mobile=user.mobile,
    expires_at=timezone.now() + timedelta(minutes=10),
    ip_address=request.META['REMOTE_ADDR']
)

# Step 4: User verifies OTP
otp_record.is_used = True
otp_record.verified_at = timezone.now()
otp_record.save()

user.is_email_verified = True
user.is_mobile_verified = True
user.save()

# Step 5: Update progress
progress.current_step = 1
progress.steps_completed = [0]
progress.save()

# Step 6: Log audit
AuditTrail.objects.create(
    user_code=None,
    action=AuditActionChoices.CREATE,
    resource_type='UserAccount',
    resource_id=str(user.id),
    description=f'New user registered: {user.email}'
)
```

### Example 2: KYC Verification Flow

```python
# User submits Aadhaar
kyc = AadhaarKYC.objects.create(
    id=f"AAH_{user.id}",
    user_code=user,
    aadhaar_number_encrypted=encrypt('123456789012'),
    aadhaar_name='John Doe',
    aadhaar_dob='1990-01-15',
    verification_method=VerificationMethodChoices.API_UIDAI
)

# Admin verifies
kyc.is_verified = True
kyc.verified_at = timezone.now()
kyc.verified_by = admin_user
kyc.api_response = {'status': 'success'}
kyc.save()

# Update user KYC status
user.is_aadhaar_verified = True

# Check if all KYC complete
if (user.is_aadhaar_verified and 
    user.is_pan_verified and 
    user.is_bank_verified):
    user.is_kyc_complete = True

user.save()

# Log audit
AuditTrail.objects.create(
    user_code=admin_user,
    action=AuditActionChoices.KYC_APPROVE,
    resource_type='AadhaarKYC',
    resource_id=str(kyc.id),
    description='Verified Aadhaar KYC'
)
```

### Example 3: Login with Security Tracking

```python
# Log login attempt
login_activity = LoginActivity.objects.create(
    user_code=user,
    login_identifier=user.email,
    ip_address=request.META['REMOTE_ADDR'],
    user_agent=request.META['HTTP_USER_AGENT'],
    device_info=extract_device_info(request),
    status=LoginStatusChoices.SUCCESS,
    session_token=jwt_token
)

# Update user
user.last_login = timezone.now()
user.last_login_ip = request.META['REMOTE_ADDR']
user.save()

# Check for suspicious activity
if login_activity.risk_score > 70:
    # Send alert
    notify_user(user, 'Suspicious login detected')

# Reset failed attempts
settings = user.security_settings
settings.failed_login_attempts = 0
settings.save()

# Log to audit
AuditTrail.objects.create(
    user_code=user,
    action=AuditActionChoices.LOGIN,
    resource_type='LoginActivity',
    resource_id=str(login_activity.id),
    ip_address=request.META['REMOTE_ADDR']
)
```

### Example 4: Access Control

```python
# Grant feature access
kyc_feature = AppFeature.objects.get(feature_code='KYC ')
AppAccessControl.objects.create(
    user_code=user,
    feature=kyc_feature,
    is_allowed=True,
    access_level=AccessLevelChoices.FULL,
    granted_by=admin_user
)

# Grant platform access
UserPlatformAccess.objects.create(
    user_code=user,
    platform=PlatformChoices.MOBILE_APP,
    is_allowed=True,
    access_level=AccessLevelChoices.FULL,
    granted_by=admin_user
)

# Check access
def has_feature_access(user, feature_code):
    return user.feature_access.filter(
        feature__feature_code=feature_code,
        is_allowed=True
    ).exists()

def has_platform_access(user, platform):
    return user.platform_access.filter(
        platform=platform,
        is_allowed=True
    ).exists()

if has_feature_access(user, 'KYC '):
    # Allow KYC operations
    pass
```

---

## ✅ BEST PRACTICES

### 1. Always Hash Passwords
```python
from django.contrib.auth.hashers import make_password

user.password = make_password(raw_password)
user.save()
```

### 2. Encrypt Sensitive Fields
```python
from cryptography.fernet import Fernet

cipher = Fernet(key)
user.aadhaar_number_encrypted = cipher.encrypt(aadhaar_bytes)
```

### 3. Use Indexed Fields for Queries
```python
# ✅ Good
users = UserAccount.objects.filter(email='john@example.com')

# ⚠️ Bad
users = UserAccount.objects.filter(middle_name='Kumar')
```

### 4. Log All Important Operations
```python
AuditTrail.objects.create(
    user_code=current_user,
    action=AuditActionChoices.UPDATE,
    resource_type='UserAccount',
    resource_id=str(updated_user.id),
    old_values=old_data,
    new_values=new_data
)
```

### 5. Use Timestamps for Auditing
```python
class MyModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)  # Soft delete
```

### 6. Implement Soft Deletes
```python
# Instead of permanently deleting
user.deleted_at = timezone.now()
user.deleted_by = current_user
user.save()

# Query only active records
active_users = UserAccount.objects.filter(deleted_at__isnull=True)
```

### 7. Use ForeignKey On Delete Actions
```python
# CASCADE: Delete if referenced object deleted
# PROTECT: Prevent deletion of referenced object
# SET_NULL: Set to NULL if referenced object deleted
# SET_DEFAULT: Set to default value
```

### 8. Create Proper Indexes
```python
class MyModel(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status', 'created_at']),
        ]
```

### 9. Use select_related for Foreign Keys
```python
# Fewer queries
users = UserAccount.objects.select_related('branch').all()
```

### 10. Use prefetch_related for Reverse Relations
```python
# Fewer queries
users = UserAccount.objects.prefetch_related(
    'otp_records',
    'login_activities'
).all()
```

---

## 🔍 QUERY EXAMPLES

### User Queries

```python
# Get user by email
user = UserAccount.objects.get(email='john@example.com')

# Get all active users
active = UserAccount.objects.filter(is_active=True)

# Get all admins
admins = UserAccount.objects.filter(user_role=UserRoleChoices.ADMIN)

# Get KYC-verified users
verified = UserAccount.objects.filter(is_kyc_complete=True)

# Get blocked users
blocked = UserAccount.objects.filter(user_blocked=1)

# Search by email or mobile
from django.db.models import Q
search = UserAccount.objects.filter(
    Q(email__icontains='john') | Q(mobile__icontains='999')
)

# Count users
total = UserAccount.objects.count()
active_count = UserAccount.objects.filter(is_active=True).count()

# Update users
UserAccount.objects.filter(user_blocked=1).update(is_active=False)

# Delete users (soft)
UserAccount.objects.filter(deleted_at__isnull=False).count()
```

### KYC Queries

```python
# Get pending KYC
pending = AadhaarKYC.objects.filter(is_verified=False)

# Get verified KYC
verified = AadhaarKYC.objects.filter(is_verified=True)

# Get all KYC by user
kyc_list = user.aadhaar_kyc

# Get KYC with high match score
high_score = PANKYC.objects.filter(name_match_score__gte=95)

# Get unverified bank accounts
bank_pending = BankDetails.objects.filter(is_verified=False)
```

### Login Queries

```python
# Get recent logins
recent = LoginActivity.objects.filter(
    user_code=user,
    login_timestamp__gte=timezone.now() - timedelta(days=7)
).order_by('-login_timestamp')

# Get failed logins
failed = LoginActivity.objects.filter(
    user_code=user,
    status=LoginStatusChoices.FAILED_PASSWORD
)

# Get suspicious logins
suspicious = LoginActivity.objects.filter(
    is_suspicious=True,
    risk_score__gte=70
)

# Count login attempts today
today_logins = LoginActivity.objects.filter(
    login_timestamp__date=timezone.now().date()
).count()

# Get unique login IPs
from django.db.models import Count
ips = LoginActivity.objects.filter(
    user_code=user
).values('ip_address').distinct()
```

### Audit Queries

```python
# Get user's audit trail
audit = AuditTrail.objects.filter(user_code=user).order_by('-created_at')

# Get all KYC approvals
kyc_approvals = AuditTrail.objects.filter(
    action=AuditActionChoices.KYC_APPROVE
)

# Get changes to specific resource
changes = AuditTrail.objects.filter(
    resource_type='UserAccount',
    resource_id=str(user.id)
)

# Get all deletions
deletions = AuditTrail.objects.filter(
    action=AuditActionChoices.DELETE
)

# Get actions by date range
from_date = timezone.now() - timedelta(days=30)
to_date = timezone.now()
audit = AuditTrail.objects.filter(
    created_at__range=[from_date, to_date]
)
```

---

## 📈 MIGRATION MANAGEMENT

### Create Migration

```bash
python manage.py makemigrations auth_user_erp
```

### Apply Migration

```bash
python manage.py migrate
```

### View Migrations

```bash
python manage.py showmigrations auth_user_erp
```

### Reverse Migration

```bash
python manage.py migrate auth_user_erp 0001
```

---

## 🔒 SECURITY CONSIDERATIONS

### Field Encryption
✅ Aadhaar number  
✅ Bank account number  
✅ PAN number (sensitive)  

### Password Storage
✅ Always use `make_password()`  
✅ Never store plain passwords  
✅ Use bcrypt hashing  

### Audit Logging
✅ Log all CRUD operations  
✅ Track who changed what and when  
✅ Store before/after values  
✅ Track IP address and user agent  

### Access Control
✅ Implement RBAC  
✅ Feature-level permissions  
✅ Platform-level access  
✅ IP whitelisting  

### Rate Limiting
✅ OTP attempt tracking  
✅ Login attempt tracking  
✅ Failed login blocking  
✅ Account lockout mechanism  

---

## 📞 CONCLUSION

This `models.py` file provides a **comprehensive, secure, and scalable database schema** for the CredbuzzPay ERP system with:

✅ **14 well-designed models**  
✅ **50+ performance indexes**  
✅ **Complete security features**  
✅ **Comprehensive audit logging**  
✅ **Flexible access control**  
✅ **Full compliance readiness**  

All models follow Django best practices and are optimized for performance and maintainability.

---

**Document Version**: 1.0  
**Last Updated**: November 12, 2025  
**Status**: Complete & Ready

---

*For questions or updates, refer to the model docstrings in the code.*
