"""
ERP Tests
Comprehensive test suite for ERP system
"""
import json
import tempfile
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    Branch, UserAccount, AadhaarKYC, PanKYC, BusinessDetails,
    BankDetails, LoginActivity, AuditTrail, AppFeature
)
from .utils import generate_otp, validate_password_strength, sanitize_mobile_number

User = get_user_model()


class ModelTestCase(TestCase):
    """Test ERP models."""
    
    def setUp(self):
        """Set up test data."""
        self.branch = Branch.objects.create(
            branch_code='TEST001',
            branch_name='Test Branch',
            address_line1='Test Address',
            city='Test City',
            state='Test State',
            pincode='123456',
            phone='9876543210',
            email='test@test.com'
        )
        
        self.user = UserAccount.objects.create_user(
            email='test@example.com',
            mobile='9876543210',
            first_name='Test',
            last_name='User',
            password='TestPass123!',
            branch=self.branch
        )
    
    def test_branch_creation(self):
        """Test branch model creation."""
        self.assertEqual(self.branch.branch_code, 'TEST001')
        self.assertEqual(self.branch.branch_name, 'Test Branch')
        self.assertTrue(self.branch.is_active)
        self.assertIsNotNone(self.branch.id)
    
    def test_user_creation(self):
        """Test user account creation."""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.mobile, '9876543210')
        self.assertEqual(self.user.get_full_name(), 'Test User')
        self.assertEqual(self.user.role, 'user')
        self.assertFalse(self.user.is_active)  # Not active until verified
        self.assertIsNotNone(self.user.id)
    
    def test_user_role_hierarchy(self):
        """Test user role hierarchy."""
        master_admin = UserAccount.objects.create_user(
            email='master@example.com',
            mobile='9876543211',
            first_name='Master',
            last_name='Admin',
            password='TestPass123!',
            role='master_superadmin',
            branch=self.branch
        )
        
        self.assertEqual(master_admin.get_role_level(), 4)
        self.assertEqual(self.user.get_role_level(), 1)
        self.assertTrue(master_admin.can_create_role('super_admin'))
        self.assertFalse(self.user.can_create_role('admin'))
    
    def test_aadhaar_kyc_creation(self):
        """Test Aadhaar KYC model."""
        # Create test image
        test_image = SimpleUploadedFile(
            "test.jpg", 
            b"fake image content", 
            content_type="image/jpeg"
        )
        
        aadhaar = AadhaarKYC.objects.create(
            user=self.user,
            aadhaar_name='Test User',
            aadhaar_front_image=test_image,
            aadhaar_back_image=test_image
        )
        
        aadhaar.set_aadhaar_number('123456789012')
        aadhaar.save()
        
        self.assertEqual(aadhaar.get_aadhaar_number(), '123456789012')
        self.assertEqual(aadhaar.get_masked_aadhaar(), 'XXXX-XXXX-9012')
    
    def test_bank_details_encryption(self):
        """Test bank details account number encryption."""
        test_image = SimpleUploadedFile(
            "bank.jpg", 
            b"fake bank document", 
            content_type="image/jpeg"
        )
        
        bank = BankDetails.objects.create(
            user=self.user,
            account_holder_name='Test User',
            ifsc_code='TEST0123456',
            account_type='savings',
            bank_name='Test Bank',
            branch_name='Test Branch',
            bank_proof_image=test_image
        )
        
        bank.set_account_number('1234567890123456')
        bank.save()
        
        self.assertEqual(bank.get_account_number(), '1234567890123456')
        self.assertEqual(bank.get_masked_account_number(), 'XXXXX3456')


class UtilsTestCase(TestCase):
    """Test utility functions."""
    
    def test_generate_otp(self):
        """Test OTP generation."""
        otp = generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())
    
    def test_password_validation(self):
        """Test password strength validation."""
        # Strong password
        is_strong, errors = validate_password_strength('StrongPass123!')
        self.assertTrue(is_strong)
        self.assertEqual(len(errors), 0)
        
        # Weak password
        is_strong, errors = validate_password_strength('weak')
        self.assertFalse(is_strong)
        self.assertGreater(len(errors), 0)
    
    def test_mobile_sanitization(self):
        """Test mobile number sanitization."""
        # Valid Indian mobile
        self.assertEqual(sanitize_mobile_number('9876543210'), '9876543210')
        self.assertEqual(sanitize_mobile_number('+919876543210'), '9876543210')
        self.assertEqual(sanitize_mobile_number('919876543210'), '9876543210')
        
        # Invalid mobile
        self.assertIsNone(sanitize_mobile_number('123456'))
        self.assertIsNone(sanitize_mobile_number('abcdefghij'))


class AuthenticationAPITestCase(APITestCase):
    """Test authentication APIs."""
    
    def setUp(self):
        """Set up test data."""
        self.branch = Branch.objects.create(
            branch_code='TEST001',
            branch_name='Test Branch',
            address_line1='Test Address',
            city='Test City',
            state='Test State',
            pincode='123456',
            phone='9876543210',
            email='test@test.com'
        )
        
        self.user = UserAccount.objects.create_user(
            email='test@example.com',
            mobile='9876543210',
            first_name='Test',
            last_name='User',
            password='TestPass123!',
            branch=self.branch,
            is_active=True,
            is_email_verified=True,
            is_mobile_verified=True
        )
    
    def test_user_registration(self):
        """Test user registration API."""
        registration_data = {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'mobile': '9876543211',
            'password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
            'branch': self.branch.id
        }
        
        response = self.client.post('/erp/auth/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if user was created
        new_user = UserAccount.objects.get(email='new@example.com')
        self.assertEqual(new_user.first_name, 'New')
        self.assertEqual(new_user.mobile, '9876543211')
        self.assertFalse(new_user.is_active)  # Not active until verified
    
    def test_user_login(self):
        """Test user login API."""
        login_data = {
            'email_or_mobile': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post('/erp/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertIn('user', data)
    
    def test_invalid_login(self):
        """Test login with invalid credentials."""
        login_data = {
            'email_or_mobile': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        response = self.client.post('/erp/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_mobile_login(self):
        """Test login with mobile number."""
        login_data = {
            'email_or_mobile': '9876543210',
            'password': 'TestPass123!'
        }
        
        response = self.client.post('/erp/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class OTPAPITestCase(APITestCase):
    """Test OTP APIs."""
    
    def setUp(self):
        """Set up test data."""
        self.branch = Branch.objects.create(
            branch_code='TEST001',
            branch_name='Test Branch',
            address_line1='Test Address',
            city='Test City',
            state='Test State',
            pincode='123456',
            phone='9876543210',
            email='test@test.com'
        )
        
        self.user = UserAccount.objects.create_user(
            email='test@example.com',
            mobile='9876543210',
            first_name='Test',
            last_name='User',
            password='TestPass123!',
            branch=self.branch
        )
        
        # Generate tokens for authenticated requests
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
    
    def test_email_otp_request(self):
        """Test email OTP request."""
        otp_data = {
            'otp_type': 'email',
            'user_id': self.user.id
        }
        
        response = self.client.post('/erp/otp/request/', otp_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if OTP was set
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_otp)
        self.assertIsNotNone(self.user.email_otp_created_at)
    
    def test_otp_verification(self):
        """Test OTP verification."""
        # Set OTP for user
        otp = '123456'
        self.user.email_otp = otp
        self.user.email_otp_created_at = timezone.now()
        self.user.save()
        
        verification_data = {
            'otp_type': 'email',
            'otp': otp,
            'user_id': self.user.id
        }
        
        response = self.client.post('/erp/otp/verify/', verification_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if email was verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
    
    def test_invalid_otp_verification(self):
        """Test verification with invalid OTP."""
        # Set OTP for user
        self.user.email_otp = '123456'
        self.user.email_otp_created_at = timezone.now()
        self.user.save()
        
        verification_data = {
            'otp_type': 'email',
            'otp': '654321',  # Wrong OTP
            'user_id': self.user.id
        }
        
        response = self.client.post('/erp/otp/verify/', verification_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class KYCAPITestCase(APITestCase):
    """Test KYC APIs."""
    
    def setUp(self):
        """Set up test data."""
        self.branch = Branch.objects.create(
            branch_code='TEST001',
            branch_name='Test Branch',
            address_line1='Test Address',
            city='Test City',
            state='Test State',
            pincode='123456',
            phone='9876543210',
            email='test@test.com'
        )
        
        self.user = UserAccount.objects.create_user(
            email='test@example.com',
            mobile='9876543210',
            first_name='Test',
            last_name='User',
            password='TestPass123!',
            branch=self.branch,
            is_active=True,
            is_email_verified=True,
            is_mobile_verified=True
        )
        
        # Generate tokens for authenticated requests
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_aadhaar_kyc_submission(self):
        """Test Aadhaar KYC submission."""
        # Create test images
        front_image = SimpleUploadedFile(
            "aadhaar_front.jpg",
            b"fake front image content",
            content_type="image/jpeg"
        )
        back_image = SimpleUploadedFile(
            "aadhaar_back.jpg",
            b"fake back image content",
            content_type="image/jpeg"
        )
        
        kyc_data = {
            'aadhaar_number': '123456789012',
            'aadhaar_name': 'Test User',
            'aadhaar_front_image': front_image,
            'aadhaar_back_image': back_image
        }
        
        response = self.client.post('/erp/kyc/aadhaar/', kyc_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if KYC was created
        aadhaar_kyc = AadhaarKYC.objects.get(user=self.user)
        self.assertEqual(aadhaar_kyc.aadhaar_name, 'Test User')
        self.assertEqual(aadhaar_kyc.get_aadhaar_number(), '123456789012')
    
    def test_pan_kyc_submission(self):
        """Test PAN KYC submission."""
        pan_image = SimpleUploadedFile(
            "pan.jpg",
            b"fake pan image content",
            content_type="image/jpeg"
        )
        
        kyc_data = {
            'pan_number': 'ABCDE1234F',
            'pan_name': 'Test User',
            'date_of_birth': '1990-01-01',
            'pan_image': pan_image
        }
        
        response = self.client.post('/erp/kyc/pan/', kyc_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if KYC was created
        pan_kyc = PanKYC.objects.get(user=self.user)
        self.assertEqual(pan_kyc.pan_number, 'ABCDE1234F')
        self.assertEqual(pan_kyc.pan_name, 'Test User')


class BusinessAPITestCase(APITestCase):
    """Test Business management APIs."""
    
    def setUp(self):
        """Set up test data."""
        self.branch = Branch.objects.create(
            branch_code='TEST001',
            branch_name='Test Branch',
            address_line1='Test Address',
            city='Test City',
            state='Test State',
            pincode='123456',
            phone='9876543210',
            email='test@test.com'
        )
        
        self.user = UserAccount.objects.create_user(
            email='test@example.com',
            mobile='9876543210',
            first_name='Test',
            last_name='User',
            password='TestPass123!',
            branch=self.branch,
            is_active=True,
            is_email_verified=True,
            is_mobile_verified=True
        )
        
        # Generate tokens for authenticated requests
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_business_details_submission(self):
        """Test business details submission."""
        selfie_image = SimpleUploadedFile(
            "selfie.jpg",
            b"fake selfie content",
            content_type="image/jpeg"
        )
        
        business_data = {
            'user_selfie': selfie_image,
            'business_name': 'Test Business',
            'business_address_line1': 'Business Address',
            'city': 'Business City',
            'state': 'Business State',
            'pincode': '123456',
            'business_phone': '9876543211',
            'business_email': 'business@test.com'
        }
        
        response = self.client.post('/erp/business/details/', business_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if business details were created
        business = BusinessDetails.objects.get(user=self.user)
        self.assertEqual(business.business_name, 'Test Business')
        self.assertEqual(business.business_phone, '9876543211')


class SecurityTestCase(TestCase):
    """Test security features."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.branch = Branch.objects.create(
            branch_code='TEST001',
            branch_name='Test Branch',
            address_line1='Test Address',
            city='Test City',
            state='Test State',
            pincode='123456',
            phone='9876543210',
            email='test@test.com'
        )
        
        self.user = UserAccount.objects.create_user(
            email='test@example.com',
            mobile='9876543210',
            first_name='Test',
            last_name='User',
            password='TestPass123!',
            branch=self.branch,
            is_active=True,
            is_email_verified=True,
            is_mobile_verified=True
        )
    
    def test_login_attempt_blocking(self):
        """Test login attempt blocking after multiple failures."""
        login_data = {
            'email_or_mobile': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        # Make 3 failed login attempts
        for i in range(3):
            response = self.client.post('/erp/auth/login/', login_data)
            self.assertEqual(response.status_code, 400)
        
        # Check if user is blocked
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_login_blocked())
    
    def test_audit_trail_creation(self):
        """Test audit trail creation."""
        # Login to create audit trail
        login_data = {
            'email_or_mobile': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post('/erp/auth/login/', login_data)
        self.assertEqual(response.status_code, 200)
        
        # Check if audit trail was created
        audit_trail = AuditTrail.objects.filter(user=self.user, action='login').first()
        self.assertIsNotNone(audit_trail)
        self.assertEqual(audit_trail.resource_type, 'user_account')


class DashboardAPITestCase(APITestCase):
    """Test Dashboard APIs."""
    
    def setUp(self):
        """Set up test data."""
        self.branch = Branch.objects.create(
            branch_code='TEST001',
            branch_name='Test Branch',
            address_line1='Test Address',
            city='Test City',
            state='Test State',
            pincode='123456',
            phone='9876543210',
            email='test@test.com'
        )
        
        # Create different role users
        self.admin_user = UserAccount.objects.create_user(
            email='admin@example.com',
            mobile='9876543210',
            first_name='Admin',
            last_name='User',
            password='TestPass123!',
            role='super_admin',
            branch=self.branch,
            is_active=True,
            is_email_verified=True,
            is_mobile_verified=True
        )
        
        self.regular_user = UserAccount.objects.create_user(
            email='user@example.com',
            mobile='9876543211',
            first_name='Regular',
            last_name='User',
            password='TestPass123!',
            role='user',
            branch=self.branch,
            is_active=True,
            is_email_verified=True,
            is_mobile_verified=True
        )
    
    def test_admin_dashboard_stats(self):
        """Test admin dashboard statistics."""
        # Login as admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        response = self.client.get('/erp/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('total_users', data)
        self.assertIn('active_users', data)
        self.assertIn('verified_users', data)
    
    def test_user_dashboard_stats(self):
        """Test regular user dashboard statistics."""
        # Login as regular user
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        response = self.client.get('/erp/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('login_count', data)
        self.assertIn('verification_status', data)