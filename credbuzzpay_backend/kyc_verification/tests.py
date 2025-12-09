"""
KYC Verification Tests
=======================
Comprehensive tests for KYC/Onboarding system.
Tests cover:
- OTP verification
- KYC application flow
- Identity proof submission
- Business details submission
- Verification images upload
- Bank details submission
- Admin review functionality
"""

import json
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from users_auth.models import User
from .models import (
    OTPVerification, KYCApplication, IdentityProof, BusinessDetails,
    VerificationImages, BankDetails, KYCProgressTracker, KYCAuditLog,
    OTPType, KYCStatus, MegaStep, StepStatus, AccountType, AuditAction,
    encrypt_value, decrypt_value, mask_aadhaar, mask_pan, mask_account_number
)


# =============================================================================
# TEST UTILITIES
# =============================================================================

# Counter to generate unique phone numbers for tests
_phone_counter = [0]

def create_test_user(email='testuser@example.com', password='TestPass@123', 
                     user_role='END_USER', is_active=True):
    """Create a test user with unique phone number."""
    _phone_counter[0] += 1
    phone_number = f'987654{_phone_counter[0]:04d}'
    
    user = User(
        email=email,
        username=email.split('@')[0],
        first_name='Test',
        last_name='User',
        phone_number=phone_number,
        user_role=user_role.upper(),
        is_email_verified=True,
        is_phone_verified=True,
    )
    user.set_password(password)
    user.is_active = is_active
    user.save()
    return user


def create_test_image():
    """Create a simple test image file."""
    # 1x1 pixel transparent PNG
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return SimpleUploadedFile('test.png', png_data, content_type='image/png')


def get_auth_header(client, user):
    """Get authentication header for user."""
    response = client.post('/api/auth/login/', {
        'identifier': user.email,
        'password': 'TestPass@123'
    }, format='json')
    if response.status_code == 200:
        token = response.data.get('data', {}).get('tokens', {}).get('access_token')
        if token:
            return {'HTTP_AUTHORIZATION': f'Bearer {token}'}
    return {}


# =============================================================================
# MODEL TESTS
# =============================================================================

class EncryptionTests(TestCase):
    """Tests for encryption utilities."""
    
    def test_encrypt_decrypt_value(self):
        """Test encryption and decryption of values."""
        original = "123456789012"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        
        self.assertNotEqual(original, encrypted)
        self.assertEqual(original, decrypted)
    
    def test_encrypt_empty_value(self):
        """Test encryption of empty value."""
        self.assertIsNone(encrypt_value(None))
        self.assertEqual(encrypt_value(''), '')
    
    def test_mask_aadhaar(self):
        """Test Aadhaar number masking."""
        self.assertEqual(mask_aadhaar('123456789012'), 'XXXX-XXXX-9012')
        self.assertEqual(mask_aadhaar('1234'), 'XXXX-XXXX-1234')
        self.assertEqual(mask_aadhaar(''), 'XXXX-XXXX-XXXX')
    
    def test_mask_pan(self):
        """Test PAN number masking."""
        self.assertEqual(mask_pan('ABCDE1234F'), 'ABCXX1234X')
        self.assertEqual(mask_pan(''), 'XXXXXXXXXX')
    
    def test_mask_account_number(self):
        """Test bank account number masking."""
        self.assertEqual(mask_account_number('123456789012'), 'XXXXXXXX9012')
        self.assertEqual(mask_account_number('1234'), '1234')


class OTPVerificationModelTests(TestCase):
    """Tests for OTP Verification model."""
    
    def setUp(self):
        self.user = create_test_user()
    
    def test_create_otp(self):
        """Test OTP creation."""
        otp = OTPVerification.objects.create(
            user=self.user,
            otp_type=OTPType.EMAIL,
            otp_code='123456',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        self.assertEqual(otp.otp_code, '123456')
        self.assertFalse(otp.is_verified)
        self.assertFalse(otp.is_expired)
        self.assertTrue(otp.is_valid)
    
    def test_otp_expiry(self):
        """Test OTP expiry check."""
        otp = OTPVerification.objects.create(
            user=self.user,
            otp_type=OTPType.EMAIL,
            otp_code='123456',
            expires_at=timezone.now() - timedelta(minutes=1)  # Expired
        )
        
        self.assertTrue(otp.is_expired)
        self.assertFalse(otp.is_valid)
    
    def test_otp_verification(self):
        """Test OTP verification."""
        otp = OTPVerification.objects.create(
            user=self.user,
            otp_type=OTPType.EMAIL,
            otp_code='123456',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Wrong code
        success, message = otp.verify('000000')
        self.assertFalse(success)
        self.assertEqual(otp.attempts, 1)
        
        # Correct code
        success, message = otp.verify('123456')
        self.assertTrue(success)
        self.assertTrue(otp.is_verified)
        self.assertIsNotNone(otp.verified_at)


class KYCApplicationModelTests(TestCase):
    """Tests for KYC Application model."""
    
    def setUp(self):
        self.user = create_test_user()
    
    def test_create_kyc_application(self):
        """Test KYC application creation."""
        kyc = KYCApplication.objects.create(
            user=self.user,
            status=KYCStatus.IN_PROGRESS
        )
        
        self.assertIsNotNone(kyc.application_id)
        self.assertTrue(kyc.application_id.startswith('KYC'))
        self.assertEqual(kyc.status, KYCStatus.IN_PROGRESS)
        self.assertEqual(kyc.mega_step, MegaStep.IDENTITY_PROOF)
        
        # Check related models are created
        self.assertTrue(hasattr(kyc, 'identity_proof'))
        self.assertTrue(hasattr(kyc, 'business_details'))
        self.assertTrue(hasattr(kyc, 'verification_images'))
        self.assertTrue(hasattr(kyc, 'bank_details'))
        
        # Check progress steps created
        self.assertEqual(kyc.progress_steps.count(), 8)
    
    def test_kyc_status_transitions(self):
        """Test KYC status transitions."""
        kyc = KYCApplication.objects.create(
            user=self.user,
            status=KYCStatus.IN_PROGRESS
        )
        admin_user = create_test_user(email='admin@example.com', user_role='super_admin')
        
        # Submit (would fail in real scenario due to incomplete steps)
        kyc.status = KYCStatus.SUBMITTED
        kyc.submitted_at = timezone.now()
        kyc.save()
        self.assertEqual(kyc.status, KYCStatus.SUBMITTED)
        
        # Start review
        kyc.start_review(admin_user)
        self.assertEqual(kyc.status, KYCStatus.UNDER_REVIEW)
        
        # Approve
        kyc.approve(admin_user, 'Approved after review')
        self.assertEqual(kyc.status, KYCStatus.APPROVED)
        self.assertIsNotNone(kyc.approved_at)


class IdentityProofModelTests(TestCase):
    """Tests for Identity Proof model."""
    
    def setUp(self):
        self.user = create_test_user()
        self.kyc = KYCApplication.objects.create(
            user=self.user,
            status=KYCStatus.IN_PROGRESS
        )
    
    def test_aadhaar_encryption(self):
        """Test Aadhaar number encryption."""
        identity = self.kyc.identity_proof
        identity.aadhaar_number = '123456789012'
        identity.save()
        
        # Check encrypted value stored
        self.assertNotEqual(identity.aadhaar_number_encrypted, '123456789012')
        
        # Check decryption works
        self.assertEqual(identity.aadhaar_number, '123456789012')
        
        # Check masking
        self.assertEqual(identity.aadhaar_masked, 'XXXX-XXXX-9012')
    
    def test_pan_encryption(self):
        """Test PAN number encryption."""
        identity = self.kyc.identity_proof
        identity.pan_number = 'ABCDE1234F'
        identity.save()
        
        # Check encrypted value stored
        self.assertNotEqual(identity.pan_number_encrypted, 'ABCDE1234F')
        
        # Check decryption works
        self.assertEqual(identity.pan_number, 'ABCDE1234F')
        
        # Check masking
        self.assertEqual(identity.pan_masked, 'ABCXX1234X')
    
    def test_is_complete_check(self):
        """Test identity proof completeness check."""
        identity = self.kyc.identity_proof
        
        # Initially not complete
        self.assertFalse(identity.is_aadhaar_complete)
        self.assertFalse(identity.is_pan_complete)
        self.assertFalse(identity.is_complete)


class BankDetailsModelTests(TestCase):
    """Tests for Bank Details model."""
    
    def setUp(self):
        self.user = create_test_user()
        self.kyc = KYCApplication.objects.create(
            user=self.user,
            status=KYCStatus.IN_PROGRESS
        )
    
    def test_account_number_encryption(self):
        """Test account number encryption."""
        bank = self.kyc.bank_details
        bank.account_number = '123456789012'
        bank.save()
        
        # Check encrypted value stored
        self.assertNotEqual(bank.account_number_encrypted, '123456789012')
        
        # Check decryption works
        self.assertEqual(bank.account_number, '123456789012')
        
        # Check masking
        self.assertEqual(bank.account_number_masked, 'XXXXXXXX9012')


# =============================================================================
# API TESTS
# =============================================================================

class OTPAPITests(APITestCase):
    """Tests for OTP API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.auth_header = get_auth_header(self.client, self.user)
    
    def test_send_email_otp(self):
        """Test sending email OTP."""
        response = self.client.post(
            '/api/auth/send-otp/',
            {'otp_type': 'EMAIL', 'email': self.user.email},
            format='json',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('otp_id', response.data)
        
        # Check OTP created
        otp = OTPVerification.objects.filter(user=self.user, otp_type=OTPType.EMAIL).first()
        self.assertIsNotNone(otp)
    
    def test_verify_otp(self):
        """Test verifying OTP."""
        # Create OTP
        otp = OTPVerification.objects.create(
            user=self.user,
            otp_type=OTPType.EMAIL,
            otp_code='123456',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        response = self.client.post(
            '/api/auth/verify-otp/',
            {'otp_type': 'EMAIL', 'otp_code': '123456'},
            format='json',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_verify_wrong_otp(self):
        """Test verifying wrong OTP."""
        # Create OTP
        OTPVerification.objects.create(
            user=self.user,
            otp_type=OTPType.EMAIL,
            otp_code='123456',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        response = self.client.post(
            '/api/auth/verify-otp/',
            {'otp_type': 'EMAIL', 'otp_code': '000000'},
            format='json',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class KYCStatusAPITests(APITestCase):
    """Tests for KYC Status API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.auth_header = get_auth_header(self.client, self.user)
    
    def test_get_status_no_kyc(self):
        """Test getting status when no KYC exists."""
        response = self.client.get(
            '/api/kyc/status/',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_kyc'])
    
    def test_start_kyc(self):
        """Test starting KYC process."""
        response = self.client.post(
            '/api/kyc/start/',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('kyc', response.data)
        self.assertEqual(response.data['kyc']['status'], KYCStatus.IN_PROGRESS)
    
    def test_get_status_with_kyc(self):
        """Test getting status when KYC exists."""
        # Start KYC first
        self.client.post('/api/kyc/start/', **self.auth_header)
        
        response = self.client.get(
            '/api/kyc/status/',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_kyc'])
        self.assertIn('kyc', response.data)


class IdentityProofAPITests(APITestCase):
    """Tests for Identity Proof API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.auth_header = get_auth_header(self.client, self.user)
        
        # Start KYC
        self.client.post('/api/kyc/start/', **self.auth_header)
    
    def test_submit_aadhaar_details(self):
        """Test submitting Aadhaar details."""
        response = self.client.post(
            '/api/kyc/identity/aadhaar/',
            {
                'aadhaar_number': '123456789012',
                'aadhaar_name': 'Test User',
                'aadhaar_dob': '1990-01-15',
                'aadhaar_address': 'Test Address'
            },
            format='json',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['aadhaar_masked'], 'XXXX-XXXX-9012')
    
    def test_submit_invalid_aadhaar(self):
        """Test submitting invalid Aadhaar number."""
        response = self.client.post(
            '/api/kyc/identity/aadhaar/',
            {
                'aadhaar_number': '12345',  # Invalid
                'aadhaar_name': 'Test User',
                'aadhaar_dob': '1990-01-15'
            },
            format='json',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_submit_pan_details(self):
        """Test submitting PAN details."""
        response = self.client.post(
            '/api/kyc/identity/pan/',
            {
                'pan_number': 'ABCDE1234F',
                'pan_name': 'Test User',
                'pan_dob': '1990-01-15'
            },
            format='json',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['pan_masked'], 'ABCXX1234X')
    
    def test_submit_invalid_pan(self):
        """Test submitting invalid PAN number."""
        response = self.client.post(
            '/api/kyc/identity/pan/',
            {
                'pan_number': 'INVALID',  # Invalid
                'pan_name': 'Test User',
                'pan_dob': '1990-01-15'
            },
            format='json',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BusinessDetailsAPITests(APITestCase):
    """Tests for Business Details API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.auth_header = get_auth_header(self.client, self.user)
        
        # Start KYC
        self.client.post('/api/kyc/start/', **self.auth_header)
    
    def test_submit_business_details(self):
        """Test submitting business details."""
        response = self.client.post(
            '/api/kyc/business/',
            {
                'business_name': 'Test Business',
                'business_phone': '9876543210',
                'address_line_1': '123 Main Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400001'
            },
            format='json',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['business']['business_name'], 'Test Business')
    
    def test_get_business_details(self):
        """Test getting business details."""
        response = self.client.get(
            '/api/kyc/business/',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('business', response.data)


class BankDetailsAPITests(APITestCase):
    """Tests for Bank Details API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.auth_header = get_auth_header(self.client, self.user)
        
        # Start KYC
        self.client.post('/api/kyc/start/', **self.auth_header)
    
    def test_submit_bank_details(self):
        """Test submitting bank details."""
        image = create_test_image()
        
        response = self.client.post(
            '/api/kyc/bank/',
            {
                'account_holder_name': 'Test User',
                'account_number': '123456789012',
                'confirm_account_number': '123456789012',
                'ifsc_code': 'SBIN0001234',
                'account_type': 'SAVINGS',
                'bank_name': 'State Bank of India',
                'bank_document': image
            },
            format='multipart',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_submit_mismatched_account_numbers(self):
        """Test submitting mismatched account numbers."""
        image = create_test_image()
        
        response = self.client.post(
            '/api/kyc/bank/',
            {
                'account_holder_name': 'Test User',
                'account_number': '123456789012',
                'confirm_account_number': '123456789999',  # Mismatch
                'ifsc_code': 'SBIN0001234',
                'account_type': 'SAVINGS',
                'bank_name': 'State Bank of India',
                'bank_document': image
            },
            format='multipart',
            **self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class KYCAdminAPITests(APITestCase):
    """Tests for KYC Admin API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Regular user (END_USER - no admin access)
        self.user = create_test_user()
        self.user_auth = get_auth_header(self.client, self.user)
        
        # Admin user (SUPER_ADMIN - has admin access)
        self.admin = create_test_user(email='admin@example.com', user_role='SUPER_ADMIN')
        self.admin_auth = get_auth_header(self.client, self.admin)
        
        # Create KYC for user
        self.client.post('/api/kyc/start/', **self.user_auth)
        self.kyc = KYCApplication.objects.get(user=self.user)
    
    def test_admin_list_applications(self):
        """Test admin listing KYC applications."""
        response = self.client.get(
            '/api/kyc/admin/applications/',
            **self.admin_auth
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
    
    def test_admin_get_application_detail(self):
        """Test admin getting application detail."""
        response = self.client.get(
            f'/api/kyc/admin/applications/{self.kyc.application_id}/',
            **self.admin_auth
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['kyc']['application_id'], self.kyc.application_id)
    
    def test_non_admin_cannot_access_admin_endpoints(self):
        """Test non-admin cannot access admin endpoints."""
        response = self.client.get(
            '/api/kyc/admin/applications/',
            **self.user_auth
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_start_review(self):
        """Test admin starting review."""
        # First submit KYC
        self.kyc.status = KYCStatus.SUBMITTED
        self.kyc.submitted_at = timezone.now()
        self.kyc.save()
        
        response = self.client.post(
            f'/api/kyc/admin/applications/{self.kyc.application_id}/start-review/',
            **self.admin_auth
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['status'], KYCStatus.UNDER_REVIEW)
    
    def test_admin_approve(self):
        """Test admin approving KYC."""
        # Set status to under review
        self.kyc.status = KYCStatus.UNDER_REVIEW
        self.kyc.save()
        
        response = self.client.post(
            f'/api/kyc/admin/applications/{self.kyc.application_id}/review/',
            {'action': 'approve', 'remarks': 'All good'},
            format='json',
            **self.admin_auth
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['status'], KYCStatus.APPROVED)
    
    def test_admin_reject_requires_remarks(self):
        """Test admin rejecting requires remarks."""
        self.kyc.status = KYCStatus.UNDER_REVIEW
        self.kyc.save()
        
        response = self.client.post(
            f'/api/kyc/admin/applications/{self.kyc.application_id}/review/',
            {'action': 'reject'},  # No remarks
            format='json',
            **self.admin_auth
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class KYCProgressTrackerTests(TestCase):
    """Tests for KYC Progress Tracker."""
    
    def setUp(self):
        self.user = create_test_user()
        self.kyc = KYCApplication.objects.create(
            user=self.user,
            status=KYCStatus.IN_PROGRESS
        )
    
    def test_progress_steps_created(self):
        """Test progress steps are created with KYC application."""
        self.assertEqual(self.kyc.progress_steps.count(), 8)
        
        # Check step names
        step_names = list(self.kyc.progress_steps.values_list('step_name', flat=True).order_by('step_number'))
        expected = [
            'Aadhaar Details', 'Aadhaar Photos', 'PAN Details', 'PAN Photo',
            'Business Details', 'Verification Images', 'Address Proof', 'Bank Details'
        ]
        self.assertEqual(step_names, expected)
    
    def test_step_completion(self):
        """Test marking step as completed."""
        step = self.kyc.progress_steps.get(step_number=1)
        
        self.assertEqual(step.status, StepStatus.NOT_STARTED)
        
        step.complete(data_snapshot={'test': 'data'})
        step.refresh_from_db()
        
        self.assertEqual(step.status, StepStatus.COMPLETED)
        self.assertIsNotNone(step.completed_at)
        self.assertEqual(step.data_snapshot, {'test': 'data'})


class KYCAuditLogTests(TestCase):
    """Tests for KYC Audit Log."""
    
    def setUp(self):
        self.user = create_test_user()
        self.kyc = KYCApplication.objects.create(
            user=self.user,
            status=KYCStatus.IN_PROGRESS
        )
    
    def test_audit_log_created_on_kyc_start(self):
        """Test audit log is created when KYC starts."""
        # KYC creation should log the start action
        log = self.kyc.audit_logs.first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.action, AuditAction.KYC_STARTED)
        self.assertEqual(log.performed_by, self.user)
    
    def test_log_action(self):
        """Test manual audit log creation."""
        admin = create_test_user(email='admin@example.com', user_role='super_admin')
        
        log = KYCAuditLog.log_action(
            kyc_application=self.kyc,
            action=AuditAction.ADMIN_APPROVED,
            performed_by=admin,
            old_status=KYCStatus.UNDER_REVIEW,
            new_status=KYCStatus.APPROVED,
            remarks='Approved after verification'
        )
        
        self.assertEqual(log.action, AuditAction.ADMIN_APPROVED)
        self.assertEqual(log.performed_by, admin)
        self.assertEqual(log.old_status, KYCStatus.UNDER_REVIEW)
        self.assertEqual(log.new_status, KYCStatus.APPROVED)

