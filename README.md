# CredBuzz ERP Backend System

A comprehensive Enterprise Resource Planning (ERP) system built with Django REST Framework, featuring user authentication, KYC verification, business onboarding, role-based access control, and advanced security features.

## 🚀 Features

### Core Features
- **Multi-layered User Authentication** with JWT tokens
- **Role-based Access Control** (4-tier hierarchy: User → Admin → Super Admin → Master Superadmin)
- **KYC Verification System** (Aadhaar, PAN, Bank Details)
- **Business Onboarding** with document verification
- **Real-time OTP Verification** (Email SMTP + SMS via Fast2SMS)
- **Device Tracking & Fingerprinting** with security analysis
- **Platform Access Control** (Web/Mobile/Both restrictions)
- **Comprehensive Audit Trail** with security logging

### Security Features
- **Advanced Encryption** for sensitive data (Aadhaar, Bank accounts)
- **Rate Limiting** for APIs and login attempts
- **Account Lockout** after failed login attempts
- **Suspicious Activity Detection** with automated blocking
- **Session Management** with JWT token storage
- **CORS Security** with configurable headers
- **SQL Injection Protection** with parameterized queries

### Enterprise Features
- **Branch Management** with hierarchical structure
- **Admin Dashboard** with comprehensive analytics
- **User Management** with role-based permissions
- **Document Management** with secure file storage
- **Login History** with device and location tracking
- **Comprehensive Logging** with file rotation
- **API Rate Limiting** with user-based quotas

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [System Architecture](#-system-architecture)
- [API Documentation](#-api-documentation)
- [Authentication Flow](#-authentication-flow)
- [Role Hierarchy](#-role-hierarchy)
- [Security Features](#-security-features)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip
- Virtual environment
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd credbuzz-backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   
   Create `.env` file in the project root:
   ```env
   SECRET_KEY=your-super-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Database
   DATABASE_URL=sqlite:///db.sqlite3
   
   # Email Configuration (Gmail)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   
   # SMS Configuration
   FAST2SMS_API_KEY=your-fast2sms-api-key
   
   # Security
   ENCRYPTION_KEY=generate-with-cryptography-fernet
   JWT_SECRET_KEY=your-jwt-secret-key
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   ```

6. **Create initial data**
   ```bash
   python manage.py shell
   ```
   
   In Django shell, create branches and features:
   ```python
   from erp.models import Branch, AppFeature
   
   # Create branches
   Branch.objects.create(
       branch_code='MUM001',
       branch_name='Mumbai Central Branch',
       address_line1='123 Business District',
       city='Mumbai',
       state='Maharashtra',
       pincode='400001',
       phone='9876543210',
       email='mumbai@credbuzz.com'
   )
   
   # Create app features
   AppFeature.objects.create(
       feature_code='USER_MANAGEMENT',
       feature_name='User Management',
       description='Manage users and roles'
   )
   
   exit()
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

   Access the application at `http://localhost:8000`

## 🏗️ System Architecture

### Backend Structure
```
credbuzz-backend/
├── credbuzzpay_backend/          # Main Django project
│   ├── settings.py               # Django settings with security configs
│   ├── urls.py                   # Main URL configuration
│   └── wsgi.py                   # WSGI configuration
├── erp/                          # Main ERP application
│   ├── models.py                 # Data models (13+ models)
│   ├── views.py                  # API views (15+ endpoints)
│   ├── serializers.py            # DRF serializers
│   ├── utils.py                  # Utility functions
│   ├── middleware.py             # Custom middleware (6 classes)
│   ├── admin.py                  # Django admin configuration
│   ├── urls.py                   # ERP URL patterns
│   └── tests.py                  # Comprehensive test suite
├── media/                        # User uploaded files
├── logs/                         # Application logs
├── requirements.txt              # Python dependencies
├── API_DOCUMENTATION.md          # Complete API documentation
└── DEPLOYMENT.md                 # Deployment guide
```

### Database Schema
- **UserAccount** - Extended user model with role hierarchy
- **Branch** - Branch management with hierarchical structure
- **AadhaarKYC** - Aadhaar verification with encryption
- **PanKYC** - PAN card verification
- **BankDetails** - Bank account details with encryption
- **BusinessDetails** - Business information with verification
- **LoginActivity** - Device tracking and login history
- **AuditTrail** - Comprehensive activity logging
- **AppFeature** - Feature management
- **UserPlatformAccess** - Platform access control

## 📚 API Documentation

### Base URL
```
http://localhost:8000/erp/
```

### Key Endpoints

#### Authentication
- `POST /auth/register/` - User registration
- `POST /auth/login/` - User login with device tracking
- `POST /auth/logout/` - Secure logout
- `POST /auth/change-password/` - Password change

#### OTP Management
- `POST /otp/request/` - Request OTP (Email/SMS)
- `POST /otp/verify/` - Verify OTP

#### KYC Verification
- `POST /kyc/aadhaar/` - Submit Aadhaar KYC
- `POST /kyc/pan/` - Submit PAN KYC
- `POST /kyc/bank/` - Submit bank details

#### Business Management
- `POST /business/details/` - Submit business details
- `GET /business/details/` - Get business information

#### Dashboard & Analytics
- `GET /dashboard/stats/` - Dashboard statistics (role-based)

#### Admin Management (Admin+ roles)
- `GET /admin/users/` - User management
- `POST /admin/users/create/` - Create new users
- `GET /admin/kyc/pending/` - Pending KYC verifications
- `PUT /admin/kyc/{id}/verify/` - Approve/reject KYC

For complete API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🔐 Authentication Flow

### Registration Process
1. User provides basic details + branch selection
2. System sends email OTP for verification
3. System sends SMS OTP for mobile verification
4. Both verifications required for account activation
5. User can then access protected endpoints

### Login Process
1. User provides email/mobile + password
2. System validates credentials and checks account status
3. Device fingerprinting and location tracking
4. JWT tokens generated (access + refresh)
5. Login activity logged with device information

### Security Checks
- Account lockout after 3 failed attempts
- Suspicious device detection
- Rate limiting on login attempts
- Session management with JWT storage

## 👥 Role Hierarchy

### 1. User (Level 1)
- Basic dashboard access
- Personal KYC management
- Business details submission
- Profile management

### 2. Admin (Level 2)
- Branch-level user management
- KYC verification for branch users
- Branch-specific reporting
- User creation within branch

### 3. Super Admin (Level 3)
- Multi-branch user management
- System-wide KYC management
- Advanced reporting and analytics
- Admin user creation

### 4. Master Superadmin (Level 4)
- Complete system access
- Super admin creation
- System configuration
- Security management
- Audit trail access

## 🛡️ Security Features

### Data Protection
- **Sensitive Data Encryption**: Aadhaar numbers and bank account numbers encrypted using Fernet
- **Password Security**: Strong password requirements with complexity validation
- **JWT Token Management**: Secure token generation with configurable expiry
- **File Upload Security**: File type validation and secure storage

### Access Control
- **Role-based Access Control**: 4-tier role hierarchy with granular permissions
- **Platform Restrictions**: Users can be restricted to web/mobile/both platforms
- **API Rate Limiting**: Different limits for different endpoints and user roles
- **Session Management**: Secure session handling with Redis backend

### Security Monitoring
- **Login Attempt Tracking**: Failed login attempts tracked and blocked
- **Device Fingerprinting**: Comprehensive device information collection
- **Suspicious Activity Detection**: Automated detection and blocking
- **Comprehensive Audit Trail**: All user actions logged with context

### Middleware Stack
1. **SecurityLoggingMiddleware** - Logs all security-related events
2. **RoleBasedAccessMiddleware** - Enforces role-based access control
3. **PlatformAccessMiddleware** - Restricts access based on platform
4. **APIRateLimitMiddleware** - Implements rate limiting
5. **JWTAuthMiddleware** - Handles JWT token validation
6. **CORSSecurityMiddleware** - Manages CORS and security headers

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific test categories
python manage.py test erp.tests.ModelTestCase
python manage.py test erp.tests.AuthenticationAPITestCase
python manage.py test erp.tests.SecurityTestCase
```

### Test Coverage
- **Model Tests**: All 13+ models with relationships
- **API Tests**: All 15+ endpoints with authentication
- **Security Tests**: Login blocking, audit trails, encryption
- **Utility Tests**: OTP generation, password validation, mobile sanitization
- **Integration Tests**: Complete user flows from registration to verification

### Test Categories
- Authentication and authorization
- KYC submission and verification
- Business onboarding process
- Security features and middleware
- Role-based access control
- OTP generation and verification

## 🚀 Deployment

### Development Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Production Deployment
For detailed production deployment instructions including:
- Server setup (Ubuntu/CentOS)
- Database configuration (PostgreSQL)
- Web server setup (Nginx)
- SSL certificate setup
- Docker deployment
- Security hardening
- Monitoring and logging

See [DEPLOYMENT.md](DEPLOYMENT.md)

### Docker Deployment
```bash
# Build and start services
docker-compose up --build -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## 📊 Key Features Deep Dive

### Device Fingerprinting
- **User Agent Analysis**: Detailed browser and OS information
- **IP Geolocation**: Country and city detection
- **Security Risk Assessment**: Suspicious device detection
- **Device History**: Track user's devices over time

### KYC Management
- **Multi-document Support**: Aadhaar, PAN, Bank statements
- **Encrypted Storage**: Sensitive information encrypted at rest
- **Verification Workflow**: Admin approval process with remarks
- **Document Validation**: File type and size validation

### Business Onboarding
- **Complete Business Profile**: Name, address, contact details
- **Document Requirements**: Business registration, selfie verification
- **Approval Workflow**: Multi-level approval process
- **Integration Ready**: API endpoints for frontend integration

### Advanced Security
- **Rate Limiting**: Configurable limits per endpoint and user role
- **Session Security**: Secure session management with Redis
- **Audit Logging**: Comprehensive activity tracking
- **Encryption**: Sensitive data encrypted using industry standards

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Install pre-commit hooks
4. Make changes with tests
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Create Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use meaningful commit messages
- Add docstrings for new functions and classes

### Testing Requirements
- All new features must have corresponding tests
- Maintain test coverage above 85%
- Test security features thoroughly
- Include both unit and integration tests

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ User authentication and authorization
- ✅ KYC verification system
- ✅ Business onboarding
- ✅ Security features and middleware
- ✅ Admin management interface

### Phase 2 (Upcoming)
- [ ] Payment integration
- [ ] Document management system
- [ ] Advanced reporting and analytics
- [ ] Mobile app API enhancements
- [ ] Notification system improvements

### Phase 3 (Future)
- [ ] Machine learning for fraud detection
- [ ] Advanced document OCR
- [ ] Integration with external services
- [ ] Multi-language support
- [ ] Advanced workflow management

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Deployment Guide](DEPLOYMENT.md) - Production deployment instructions

### Getting Help
- Create an issue for bugs or feature requests
- Check existing issues before creating new ones
- Provide detailed information including logs and environment details
- Follow the issue template for faster resolution

### Contact
- **Email**: support@credbuzz.com
- **GitHub Issues**: For bugs and feature requests
- **Documentation**: Check README and documentation files first

## 🙏 Acknowledgments

- Django REST Framework for the excellent API framework
- Fast2SMS for SMS services
- Cryptography library for encryption support
- All contributors and beta testers

---

**Note**: This is an enterprise-grade system with comprehensive security features. Please ensure proper environment configuration and security measures when deploying to production.