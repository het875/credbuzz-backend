# CredbuzzPay ERP System - Django Backend

A comprehensive Django-based ERP system focused on user authentication, verification, and access management. This system handles all user-related operations including registration, KYC verification, OTP management, and role-based access control.

## Project Overview

The CredbuzzPay ERP backend is built with Django 5.2 and Django REST Framework, providing a complete solution for:
- Multi-step user registration with OTP verification
- Role-based access control (Super Admin, Admin, User)
- Complete KYC verification workflow (Aadhaar, PAN, Bank, Business)
- OTP-based verification for email and mobile
- Comprehensive audit trails
- Device and IP tracking
- Session management with JWT tokens

## Technology Stack

- **Backend Framework**: Django 5.2.6
- **REST API**: Django REST Framework 3.16.1
- **Database**: PostgreSQL 14+ (or SQLite for development)
- **Authentication**: JWT (djangorestframework-simplejwt 5.5.1)
- **Task Queue**: Celery 5.4.0 with Redis
- **Caching**: Redis 5.0.0
- **Encryption**: cryptography 42.0.0
- **API Documentation**: drf-yasg 1.21.8
- **Phone Validation**: django-phonenumber-field 8.0.0

## Project Structure

```
accounts/
├── models.py              # 14 custom database models
├── serializers.py         # DRF serializers for all models
├── views.py               # API viewsets and endpoints
├── urls.py                # URL routing configuration
├── admin.py               # Django admin customization
├── apps.py                # App configuration
├── signals.py             # Django signals for auto-operations
├── permissions.py         # Custom DRF permissions
├── utils/
│   ├── code_generator.py  # User/Branch/Feature code generation
│   ├── validators.py      # PAN, Aadhaar, IFSC, mobile validation
│   ├── encryption.py      # AES encryption for sensitive data
│   └── security.py        # OTP blocking, risk scoring, IP management
├── services/
│   ├── otp_service.py     # OTP generation, verification, cleanup
│   ├── audit_service.py   # Audit trail logging
│   └── notification_service.py  # Email/SMS notifications
├── middleware/
│   ├── audit_middleware.py    # Auto-logging of all API requests
│   └── authentication.py      # Custom JWT authentication
├── tasks.py               # Celery async tasks
└── tests/
    ├── test_models.py
    ├── test_apis.py
    └── test_services.py
```

## Database Schema (14 Tables)

### Core User Management
1. **UserAccount** - Custom user model with verification flags, OTP tracking, KYC status
2. **Branch** - Organization branch/location management
3. **AppFeature** - System features/modules for access control
4. **RegistrationProgress** - Multi-step registration workflow tracking

### OTP & Security
5. **OTPRecord** - Centralized OTP management (email, mobile, Aadhaar, bank verification)
6. **SecuritySettings** - User security configurations (2FA, IP whitelist, etc.)
7. **LoginActivity** - Login attempts and session tracking
8. **AuditTrail** - Comprehensive audit log of all operations

### KYC Verification
9. **AadhaarKYC** - Aadhaar verification with encrypted storage
10. **PANKYC** - PAN verification
11. **BusinessDetails** - Business/merchant information
12. **BankDetails** - Bank account details with encryption

### Access Control
13. **UserPlatformAccess** - Platform-level access control
14. **AppAccessControl** - Feature-level access control

## Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (or SQLite for development)
- Redis 7+
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/het875/credbuzz-backend.git
cd credbuzz-backend
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv credbuzz_backend_venv
credbuzz_backend_venv\Scripts\activate

# macOS/Linux
python3 -m venv credbuzz_backend_venv
source credbuzz_backend_venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-django-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=credbuzz_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Encryption
ENCRYPTION_KEY=your-encryption-key-change-in-production

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SMS Configuration (Twilio/AWS SNS)
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

### Step 5: Configure Django Settings

Update `credbuzzpay_backend/settings.py`:

```python
# Database
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DATABASE_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DATABASE_USER', ''),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', ''),
        'PORT': os.getenv('DATABASE_PORT', ''),
    }
}

# Redis
CACHES['default']['LOCATION'] = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
```

### Step 6: Run Migrations

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

### Step 7: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 8: Run Development Server

```bash
python manage.py runserver
```

Server runs at: `http://localhost:8000`

API Documentation: `http://localhost:8000/api/docs/`

### Step 9: Run Celery (For Async Tasks)

```bash
# In a separate terminal
celery -A credbuzzpay_backend worker -l info
celery -A credbuzzpay_backend beat -l info
```

## API Endpoints

### Authentication (11 endpoints)
- `POST /api/v1/auth/register/initiate` - Start registration
- `POST /api/v1/auth/register/verify-otp` - Verify registration OTPs
- `POST /api/v1/auth/register/basic-info` - Submit basic information
- `POST /api/v1/auth/register/resend-otp` - Resend OTP
- `POST /api/v1/auth/login` - Login with email/mobile
- `POST /api/v1/auth/login/verify-2fa` - Verify 2FA
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/forgot-password` - Forgot password
- `POST /api/v1/auth/verify-reset-otp` - Verify password reset OTP
- `POST /api/v1/auth/reset-password` - Reset password
- `POST /api/v1/auth/change-password` - Change password

### KYC Verification (11 endpoints)
- `POST /api/v1/kyc/aadhaar/submit` - Submit Aadhaar
- `POST /api/v1/kyc/aadhaar/verify-otp` - Verify Aadhaar OTP
- `POST /api/v1/kyc/aadhaar/upload-offline` - Upload offline Aadhaar
- `POST /api/v1/kyc/pan/submit` - Submit PAN
- `GET /api/v1/kyc/pan/verify-status/{user_code}` - Check PAN status
- `POST /api/v1/kyc/business/submit` - Submit business details
- `POST /api/v1/kyc/business/verify-contact` - Verify business contact
- `POST /api/v1/kyc/bank/submit` - Submit bank details
- `POST /api/v1/kyc/bank/verify-penny-drop` - Verify penny drop
- `GET /api/v1/kyc/status/{user_code}` - Get KYC status
- `GET /api/v1/kyc/resume/{user_code}` - Resume KYC

### User Management (9 endpoints)
- `GET /api/v1/users/{user_code}` - Get user profile
- `PUT /api/v1/users/{user_code}` - Update profile
- `GET /api/v1/users/search` - Search users
- `POST /api/v1/users/{user_code}/assign-role` - Assign role
- `POST /api/v1/users/{user_code}/platform-access` - Grant platform access
- `POST /api/v1/users/{user_code}/feature-access` - Grant feature access
- `GET /api/v1/users/{user_code}/permissions` - Get user permissions
- `POST /api/v1/users/{user_code}/block` - Block user
- `POST /api/v1/users/{user_code}/unblock` - Unblock user

### Branch Management (5 endpoints)
- `POST /api/v1/branches/` - Create branch
- `GET /api/v1/branches/` - List branches
- `GET /api/v1/branches/{branch_code}` - Get branch
- `PUT /api/v1/branches/{branch_code}` - Update branch
- `DELETE /api/v1/branches/{branch_code}` - Delete branch

### Feature Management (3 endpoints)
- `POST /api/v1/features/` - Create feature
- `GET /api/v1/features/` - List features
- `PUT /api/v1/features/{feature_code}` - Update feature

### Audit & Reporting (5 endpoints)
- `GET /api/v1/audit/user/{user_code}` - User audit log
- `GET /api/v1/audit/system` - System audit log
- `GET /api/v1/reports/login-activity` - Login activity report
- `GET /api/v1/reports/kyc-status` - KYC status report
- `GET /api/v1/reports/registration-funnel` - Registration funnel

### Security (2 endpoints)
- `POST /api/v1/security/settings/{user_code}` - Update security settings
- `GET /api/v1/security/suspicious-activity/{user_code}` - Get suspicious activity

## Usage Examples

### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "mobile": "+919876543210",
    "password": "SecurePass@123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_mobile": "user@example.com",
    "password": "SecurePass@123",
    "device_info": {"browser": "Chrome", "os": "Windows"}
  }'
```

### Submit Aadhaar KYC

```bash
curl -X POST http://localhost:8000/api/v1/kyc/aadhaar/submit \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: multipart/form-data" \
  -F "user_code=ABC123" \
  -F "aadhaar_number=123456789012" \
  -F "aadhaar_name=John Doe" \
  -F "aadhaar_dob=1990-01-15" \
  -F "aadhaar_front_image=@front.jpg" \
  -F "aadhaar_back_image=@back.jpg"
```

## Security Features

✅ **Password Security**
- Bcrypt hashing with Django's `make_password()`
- Strong password validation (min 8 chars, uppercase, lowercase, digit, special char)
- Password change tracking

✅ **OTP Security**
- Hashed OTP storage
- Rate limiting and cooldown periods
- Max attempt blocking
- Configurable validity periods

✅ **Data Encryption**
- AES encryption for Aadhaar numbers
- AES encryption for bank account numbers
- Selective decryption for display

✅ **Authentication**
- JWT tokens with short expiry (15 mins access, 7 days refresh)
- Token refresh mechanism
- Session tracking

✅ **Authorization**
- Role-based access control (RBAC)
- Feature-level access control
- Platform-level access control
- Custom DRF permissions

✅ **Audit & Logging**
- Complete audit trail of all operations
- Login activity tracking
- Device and IP logging
- Risk scoring

✅ **Input Validation**
- PAN format validation
- Aadhaar checksum validation (Verhoeff algorithm)
- IFSC code validation
- Indian mobile number validation
- Pincode validation

## Configuration

### OTP Settings

```python
OTP_VALIDITY = {
    'registration': 10,      # minutes
    'login': 5,              # minutes
    'password_reset': 15,    # minutes
    'kyc': 10,               # minutes
}

OTP_MAX_ATTEMPTS = {
    'email': 3,
    'mobile': 5,
}

OTP_COOLDOWN = {
    'registration': 60,      # seconds
    'login': 30,             # seconds
    'password_reset': 120,   # seconds
}
```

### Security Settings

```python
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 3600  # 1 hour
PASSWORD_RESET_TIMEOUT = 3600    # 1 hour
```

## Admin Interface

Access Django admin at: `http://localhost:8000/admin/`

Features:
- View and manage all user accounts
- Monitor KYC verification status
- View login activities and audit trails
- Manage branches and features
- Control user permissions
- Block/unblock users

## Testing

### Run Unit Tests

```bash
python manage.py test accounts
```

### Run with Coverage

```bash
coverage run --source='accounts' manage.py test accounts
coverage report
coverage html
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in settings
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching
- [ ] Configure email backend (SendGrid, AWS SES, etc.)
- [ ] Configure SMS backend (Twilio, AWS SNS, etc.)
- [ ] Enable HTTPS/SSL
- [ ] Configure allowed hosts
- [ ] Set up environment variables
- [ ] Run migrations
- [ ] Collect static files
- [ ] Configure Celery with production broker
- [ ] Set up monitoring and logging

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

CMD ["gunicorn", "credbuzzpay_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: credbuzz_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/credbuzz_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A credbuzzpay_backend worker -l info
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/credbuzz_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'accounts'`
- Solution: Ensure 'accounts' is in `INSTALLED_APPS`

**Issue**: Database migrations not applying
- Solution: Run `python manage.py makemigrations accounts && python manage.py migrate`

**Issue**: OTP not sending
- Solution: Configure email backend and SMS provider credentials

**Issue**: Celery tasks not executing
- Solution: Ensure Redis is running and Celery worker is started

## Documentation

- **API Documentation**: `http://localhost:8000/api/docs/` (Swagger UI)
- **ReDoc Documentation**: `http://localhost:8000/api/redoc/` (ReDoc)
- **Django Admin**: `http://localhost:8000/admin/`

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For support and issues:
- Email: support@credbuzz.com
- GitHub Issues: [Create an issue](https://github.com/het875/credbuzz-backend/issues)

## Author

**CredbuzzPay Development Team**
- GitHub: [@het875](https://github.com/het875)

---

**Last Updated**: November 2025
**Version**: 1.0.0
**Status**: Active Development
