# Testing Guide - CredbuzzPay ERP System

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Setup](#setup)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [API Tests](#api-tests)
6. [Performance Tests](#performance-tests)
7. [Security Tests](#security-tests)
8. [Coverage Report](#coverage-report)
9. [CI/CD Integration](#cicd-integration)

---

## Testing Overview

### Testing Strategy

- **Unit Tests**: Test individual functions and methods in isolation
- **Integration Tests**: Test interactions between multiple components
- **API Tests**: Test REST endpoints end-to-end
- **Performance Tests**: Test system under load
- **Security Tests**: Test authentication, authorization, and data security

### Testing Framework

- **unittest**: Django's built-in testing framework
- **pytest**: Python testing framework with fixtures and plugins
- **pytest-django**: Django plugin for pytest
- **factory-boy**: Test fixture library
- **faker**: Fake data generation
- **responses**: Mock HTTP requests
- **locust**: Load testing

### Test Structure

```
accounts/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_views.py
│   ├── test_utils.py
│   ├── test_services.py
│   ├── test_permissions.py
│   ├── test_middleware.py
│   ├── test_validators.py
│   ├── test_encryption.py
│   ├── test_security.py
│   ├── fixtures.py
│   └── factories.py
```

---

## Setup

### Install Testing Dependencies

```bash
pip install pytest pytest-django pytest-cov pytest-xdist \
            factory-boy faker responses locust django-test-plus
```

### Configuration Files

#### pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = credbuzzpay_backend.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=accounts --cov-report=html --cov-report=term-missing
testpaths = accounts/tests
```

#### conftest.py

```python
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'credbuzzpay_backend.settings')
django.setup()

import pytest
from django.test import Client
from rest_framework.test import APIClient
from accounts.tests.factories import UserAccountFactory


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.fixture
def client():
    """Return Django test client."""
    return Client()


@pytest.fixture
def authenticated_client(db):
    """Return authenticated API client."""
    user = UserAccountFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(db):
    """Return admin API client."""
    admin = UserAccountFactory(user_role='admin')
    client = APIClient()
    client.force_authenticate(user=admin)
    return client
```

---

## Unit Tests

### Test Models

Create `accounts/tests/test_models.py`:

```python
import pytest
from django.contrib.auth import get_user_model
from accounts.models import (
    UserAccount, OTPRecord, AadhaarKYC, PANKYC, 
    LoginActivity, AuditTrail
)
from accounts.tests.factories import (
    UserAccountFactory, OTPRecordFactory, 
    AadhaarKYCFactory, PANKYCFactory
)
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class TestUserAccountModel:
    """Test UserAccount model."""
    
    @pytest.mark.django_db
    def test_create_user_account(self):
        """Test creating a user account."""
        user = UserAccountFactory(
            email="test@example.com",
            mobile="+919876543210"
        )
        assert user.email == "test@example.com"
        assert user.mobile == "+919876543210"
        assert user.is_active is False
        assert user.user_code is not None
    
    @pytest.mark.django_db
    def test_user_code_uniqueness(self):
        """Test user code is unique."""
        user1 = UserAccountFactory()
        user2 = UserAccountFactory()
        assert user1.user_code != user2.user_code
    
    @pytest.mark.django_db
    def test_email_verification_flag(self):
        """Test email verification flag."""
        user = UserAccountFactory(is_email_verified=False)
        assert user.is_email_verified is False
        
        user.is_email_verified = True
        user.email_verified_at = timezone.now()
        user.save()
        assert user.is_email_verified is True
    
    @pytest.mark.django_db
    def test_mobile_verification_flag(self):
        """Test mobile verification flag."""
        user = UserAccountFactory(is_mobile_verified=False)
        assert user.is_mobile_verified is False
    
    @pytest.mark.django_db
    def test_user_blocking(self):
        """Test user blocking mechanism."""
        user = UserAccountFactory()
        user.is_blocked = True
        user.blocked_until = timezone.now() + timedelta(hours=1)
        user.save()
        
        assert user.is_blocked is True
        assert user.blocked_until > timezone.now()


class TestOTPRecordModel:
    """Test OTPRecord model."""
    
    @pytest.mark.django_db
    def test_create_otp_record(self):
        """Test creating OTP record."""
        otp = OTPRecordFactory(otp_purpose='email_verification')
        assert otp.otp_purpose == 'email_verification'
        assert otp.is_used is False
    
    @pytest.mark.django_db
    def test_otp_expiry(self):
        """Test OTP expiry."""
        otp = OTPRecordFactory(expires_at=timezone.now() - timedelta(minutes=5))
        assert otp.expires_at < timezone.now()
    
    @pytest.mark.django_db
    def test_otp_attempt_tracking(self):
        """Test OTP attempt tracking."""
        otp = OTPRecordFactory()
        assert otp.otp_attempts == 0
        
        otp.otp_attempts = 1
        otp.save()
        assert otp.otp_attempts == 1


class TestAadhaarKYCModel:
    """Test Aadhaar KYC model."""
    
    @pytest.mark.django_db
    def test_create_aadhaar_kyc(self):
        """Test creating Aadhaar KYC record."""
        kyc = AadhaarKYCFactory()
        assert kyc.user_account is not None
        assert kyc.is_verified is False
    
    @pytest.mark.django_db
    def test_aadhaar_verification_method(self):
        """Test Aadhaar verification method options."""
        kyc = AadhaarKYCFactory(verification_method='manual')
        assert kyc.verification_method in ['manual', 'otp', 'api']
```

### Test Serializers

Create `accounts/tests/test_serializers.py`:

```python
import pytest
from accounts.serializers import (
    UserAccountSerializer, OTPRecordSerializer,
    AadhaarKYCSerializer
)
from accounts.tests.factories import UserAccountFactory


class TestUserAccountSerializer:
    """Test UserAccount serializer."""
    
    def test_serialize_user_account(self):
        """Test serializing user account."""
        user = UserAccountFactory()
        serializer = UserAccountSerializer(user)
        
        assert serializer.data['email'] == user.email
        assert serializer.data['mobile'] == user.mobile
        assert serializer.data['user_code'] == user.user_code
    
    def test_password_validation(self):
        """Test password validation."""
        data = {
            'email': 'test@example.com',
            'mobile': '+919876543210',
            'password': 'weak',  # Too weak
            'password_confirm': 'weak'
        }
        serializer = UserAccountSerializer(data=data)
        assert serializer.is_valid() is False
    
    def test_email_validation(self):
        """Test email validation."""
        data = {
            'email': 'invalid-email',
            'mobile': '+919876543210',
            'password': 'SecurePass@123',
            'password_confirm': 'SecurePass@123'
        }
        serializer = UserAccountSerializer(data=data)
        assert serializer.is_valid() is False
    
    def test_mobile_validation(self):
        """Test mobile validation."""
        data = {
            'email': 'test@example.com',
            'mobile': '12345',  # Invalid format
            'password': 'SecurePass@123',
            'password_confirm': 'SecurePass@123'
        }
        serializer = UserAccountSerializer(data=data)
        assert serializer.is_valid() is False


class TestAadhaarKYCSerializer:
    """Test Aadhaar KYC serializer."""
    
    def test_aadhaar_number_validation(self):
        """Test Aadhaar number validation."""
        data = {
            'aadhaar_number': '123',  # Invalid length
            'aadhaar_name': 'John Doe'
        }
        serializer = AadhaarKYCSerializer(data=data)
        assert serializer.is_valid() is False
```

---

## Integration Tests

### Test Views

Create `accounts/tests/test_views.py`:

```python
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from accounts.tests.factories import UserAccountFactory, OTPRecordFactory
from accounts.models import UserAccount


class TestAuthenticationViews:
    """Test authentication views."""
    
    @pytest.mark.django_db
    def test_register_initiate(self, api_client):
        """Test user registration initiation."""
        data = {
            'email': 'newuser@example.com',
            'mobile': '+919876543210',
            'password': 'SecurePass@123'
        }
        response = api_client.post(
            reverse('auth-register-initiate'),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user_code' in response.data
    
    @pytest.mark.django_db
    def test_register_duplicate_email(self, api_client):
        """Test registration with duplicate email."""
        UserAccountFactory(email='test@example.com')
        
        data = {
            'email': 'test@example.com',
            'mobile': '+919876543211',
            'password': 'SecurePass@123'
        }
        response = api_client.post(
            reverse('auth-register-initiate'),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.django_db
    def test_register_verify_otp(self, api_client):
        """Test OTP verification during registration."""
        user = UserAccountFactory()
        otp = OTPRecordFactory(
            user_account=user,
            otp_purpose='email_verification'
        )
        
        data = {
            'user_code': user.user_code,
            'email_otp': '123456',
            'mobile_otp': '654321'
        }
        response = api_client.post(
            reverse('auth-register-verify-otp'),
            data,
            format='json'
        )
        # Expected to fail with invalid OTP
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED
        ]
    
    @pytest.mark.django_db
    def test_login_success(self, api_client):
        """Test successful login."""
        user = UserAccountFactory(
            email='test@example.com',
            is_active=True,
            is_email_verified=True,
            is_mobile_verified=True
        )
        user.set_password('SecurePass@123')
        user.save()
        
        data = {
            'email_or_mobile': 'test@example.com',
            'password': 'SecurePass@123'
        }
        response = api_client.post(
            reverse('auth-login'),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
    
    @pytest.mark.django_db
    def test_login_invalid_password(self, api_client):
        """Test login with invalid password."""
        user = UserAccountFactory(email='test@example.com')
        user.set_password('SecurePass@123')
        user.save()
        
        data = {
            'email_or_mobile': 'test@example.com',
            'password': 'WrongPassword@123'
        }
        response = api_client.post(
            reverse('auth-login'),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.django_db
    def test_logout(self, api_client):
        """Test logout."""
        user = UserAccountFactory(is_active=True)
        api_client.force_authenticate(user=user)
        
        response = api_client.post(reverse('auth-logout'))
        assert response.status_code == status.HTTP_200_OK
```

---

## API Tests

### Test Authentication Flow

Create `accounts/tests/test_authentication_flow.py`:

```python
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse


class TestCompleteAuthenticationFlow:
    """Test complete authentication flow."""
    
    @pytest.mark.django_db
    def test_registration_to_login_flow(self):
        """Test complete registration and login flow."""
        client = APIClient()
        
        # Step 1: Register
        register_data = {
            'email': 'newuser@example.com',
            'mobile': '+919876543210',
            'password': 'SecurePass@123'
        }
        register_response = client.post(
            reverse('auth-register-initiate'),
            register_data,
            format='json'
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        user_code = register_response.data['user_code']
        
        # Step 2: Verify OTP (in real scenario)
        # Step 3: Login
        login_data = {
            'email_or_mobile': 'newuser@example.com',
            'password': 'SecurePass@123'
        }
        # Would succeed after email/mobile verification
        # login_response = client.post(
        #     reverse('auth-login'),
        #     login_data,
        #     format='json'
        # )
```

---

## Performance Tests

### Load Testing with Locust

Create `accounts/tests/load_test.py`:

```python
from locust import HttpUser, task, between


class AuthenticationUser(HttpUser):
    """Load test authentication endpoints."""
    
    wait_time = between(1, 3)
    
    @task
    def login(self):
        """Test login endpoint under load."""
        self.client.post('/api/v1/auth/login', {
            'email_or_mobile': 'test@example.com',
            'password': 'SecurePass@123'
        })
    
    @task
    def register(self):
        """Test registration endpoint under load."""
        self.client.post('/api/v1/auth/register/initiate', {
            'email': 'test@example.com',
            'mobile': '+919876543210',
            'password': 'SecurePass@123'
        })
```

Run load test:

```bash
locust -f accounts/tests/load_test.py --host=http://localhost:8000
```

---

## Security Tests

### Test Authorization

Create `accounts/tests/test_security.py`:

```python
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from accounts.tests.factories import UserAccountFactory


class TestSecurity:
    """Test security features."""
    
    @pytest.mark.django_db
    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints."""
        client = APIClient()
        response = client.get('/api/v1/users/ABC123')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.django_db
    def test_admin_only_access(self):
        """Test admin-only endpoint access."""
        user = UserAccountFactory(user_role='user')
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.post('/api/v1/users/ABC123/assign-role', {
            'role': 'admin'
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.django_db
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        client = APIClient()
        response = client.get(
            "/api/v1/users/?search='; DROP TABLE users;--"
        )
        # Should not execute SQL
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]
    
    @pytest.mark.django_db
    def test_rate_limiting_login(self):
        """Test rate limiting on login attempts."""
        client = APIClient()
        
        for _ in range(11):  # Attempt login 11 times
            response = client.post('/api/v1/auth/login', {
                'email_or_mobile': 'test@example.com',
                'password': 'wrong'
            })
        
        # Should be rate limited
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
```

---

## Coverage Report

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=accounts --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

### Expected Coverage Targets

- **Overall**: 80%+
- **Models**: 90%+
- **Serializers**: 85%+
- **Views**: 80%+
- **Utils**: 90%+

---

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run migrations
        run: python manage.py migrate
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
      
      - name: Run tests with coverage
        run: pytest --cov=accounts --cov-report=xml
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest accounts/tests/test_models.py
```

### Run Specific Test Class

```bash
pytest accounts/tests/test_models.py::TestUserAccountModel
```

### Run Specific Test

```bash
pytest accounts/tests/test_models.py::TestUserAccountModel::test_create_user_account
```

### Run with Verbose Output

```bash
pytest -v
```

### Run in Parallel

```bash
pytest -n auto
```

### Run with Specific Marker

```bash
pytest -m django_db
```

---

## Test Factories

Create `accounts/tests/factories.py`:

```python
import factory
from django.utils import timezone
from accounts.models import UserAccount, OTPRecord, AadhaarKYC, PANKYC


class UserAccountFactory(factory.django.DjangoModelFactory):
    """Factory for UserAccount model."""
    
    class Meta:
        model = UserAccount
    
    email = factory.Faker('email')
    mobile = factory.Faker('msisdn')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.django.Password('SecurePass@123')
    user_role = 'user'
    is_active = False


class OTPRecordFactory(factory.django.DjangoModelFactory):
    """Factory for OTPRecord model."""
    
    class Meta:
        model = OTPRecord
    
    user_account = factory.SubFactory(UserAccountFactory)
    otp_purpose = 'email_verification'
    otp_type = 'email'
    expires_at = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(minutes=10)
    )


class AadhaarKYCFactory(factory.django.DjangoModelFactory):
    """Factory for AadhaarKYC model."""
    
    class Meta:
        model = AadhaarKYC
    
    user_account = factory.SubFactory(UserAccountFactory)
    aadhaar_number = '123456789012'
    aadhaar_name = factory.Faker('name')
    verification_method = 'manual'
```

---

**Last Updated:** November 2025
**Version:** 1.0.0
