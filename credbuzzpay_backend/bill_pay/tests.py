"""
Bill Pay App Tests
==================
Tests for Bill Pay functionality including:
- Bill Categories
- Billers
- Bill Fetch
- Bill Payment
- Payment History
"""

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from users_auth.models import User
from .models import BillCategory, Biller, BillPayment, SavedBiller, PaymentStatus


class BillCategoryModelTests(TestCase):
    """Tests for BillCategory model."""
    
    def test_create_category(self):
        """Test creating a bill category."""
        category = BillCategory.objects.create(
            name='Test Category',
            code='TEST_CAT',
            description='Test Description',
            icon='TestIcon',
            display_order=1
        )
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(str(category), 'Test Category')
        self.assertTrue(category.is_active)


class BillerModelTests(TestCase):
    """Tests for Biller model."""
    
    def setUp(self):
        """Set up test data."""
        self.category = BillCategory.objects.create(
            name='Electricity',
            code='ELEC_TEST',
            display_order=1
        )
    
    def test_create_biller(self):
        """Test creating a biller."""
        biller = Biller.objects.create(
            category=self.category,
            name='Test Electric Company',
            code='TEST_ELEC',
            min_amount=Decimal('10.00'),
            max_amount=Decimal('50000.00')
        )
        self.assertEqual(biller.name, 'Test Electric Company')
        self.assertTrue(biller.is_active)
    
    def test_calculate_fixed_fee(self):
        """Test fixed platform fee calculation."""
        biller = Biller.objects.create(
            category=self.category,
            name='Fixed Fee Biller',
            code='FIXED_FEE',
            platform_fee=Decimal('5.00'),
            platform_fee_type='FIXED'
        )
        self.assertEqual(biller.calculate_fee(Decimal('100.00')), Decimal('5.00'))
        self.assertEqual(biller.calculate_fee(Decimal('1000.00')), Decimal('5.00'))
    
    def test_calculate_percentage_fee(self):
        """Test percentage platform fee calculation."""
        biller = Biller.objects.create(
            category=self.category,
            name='Percent Fee Biller',
            code='PERCENT_FEE',
            platform_fee=Decimal('2.00'),  # 2%
            platform_fee_type='PERCENTAGE'
        )
        self.assertEqual(biller.calculate_fee(Decimal('100.00')), Decimal('2.00'))
        self.assertEqual(biller.calculate_fee(Decimal('1000.00')), Decimal('20.00'))


class BillPaymentAPITests(APITestCase):
    """Tests for Bill Pay API endpoints."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        # Create test user using the custom User model
        cls.user = User.objects.create(
            username='testuser',
            email='test@example.com',
            phone_number='9876543210'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
        
        # Create test category
        cls.category = BillCategory.objects.create(
            name='Electricity',
            code='ELECTRICITY',
            display_order=1
        )
        
        # Create test biller
        cls.biller = Biller.objects.create(
            category=cls.category,
            name='Test Electric',
            code='TEST_ELEC',
            min_amount=Decimal('10.00'),
            max_amount=Decimal('50000.00'),
            is_featured=True
        )
    
    def authenticate(self):
        """Helper to authenticate the test client."""
        from users_auth.jwt_utils import JWTManager
        from users_auth.models import UserSession
        
        tokens = JWTManager.generate_tokens(self.user)
        # Create session for authentication to work
        UserSession.objects.create(
            user=self.user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address='127.0.0.1',
            user_agent='Test Client'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    
    def test_list_categories(self):
        """Test listing bill categories."""
        self.authenticate()
        response = self.client.get('/api/bills/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        # Categories are nested under 'data' key
        data = response.data.get('data', {})
        self.assertGreaterEqual(len(data.get('categories', [])), 1)
    
    def test_list_billers(self):
        """Test listing billers."""
        self.authenticate()
        response = self.client.get('/api/bills/billers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
    
    def test_list_billers_by_category(self):
        """Test listing billers filtered by category."""
        self.authenticate()
        response = self.client.get(f'/api/bills/billers/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
    
    def test_featured_billers(self):
        """Test listing featured billers."""
        self.authenticate()
        response = self.client.get('/api/bills/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
    
    def test_biller_detail(self):
        """Test getting biller details."""
        self.authenticate()
        response = self.client.get(f'/api/bills/billers/{self.biller.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        # Biller data is nested under 'data' key
        data = response.data.get('data', {})
        self.assertEqual(data.get('biller', {}).get('name'), 'Test Electric')
    
    def test_payment_history_empty(self):
        """Test payment history when empty."""
        self.authenticate()
        response = self.client.get('/api/bills/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated access is rejected."""
        response = self.client.get('/api/bills/categories/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SavedBillerTests(APITestCase):
    """Tests for Saved Biller functionality."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create(
            username='saveduser',
            email='saved@example.com',
            phone_number='9876543211'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
        
        cls.category = BillCategory.objects.create(
            name='Water',
            code='WATER_TEST',
            display_order=1
        )
        
        cls.biller = Biller.objects.create(
            category=cls.category,
            name='Water Board',
            code='WATER_BOARD'
        )
    
    def authenticate(self):
        """Helper to authenticate the test client."""
        from users_auth.jwt_utils import JWTManager
        from users_auth.models import UserSession
        
        tokens = JWTManager.generate_tokens(self.user)
        UserSession.objects.create(
            user=self.user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address='127.0.0.1',
            user_agent='Test Client'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    
    def test_save_biller(self):
        """Test saving a biller for quick access."""
        self.authenticate()
        response = self.client.post('/api/bills/saved/', {
            'biller': self.biller.id,  # Use 'biller' not 'biller_id'
            'consumer_number': 'WATER123',
            'nickname': 'Home Water'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))
    
    def test_list_saved_billers(self):
        """Test listing saved billers."""
        self.authenticate()
        
        # First save a biller
        SavedBiller.objects.create(
            user=self.user,
            biller=self.biller,
            consumer_number='TEST123',
            nickname='Test Saved'
        )
        
        response = self.client.get('/api/bills/saved/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        # Saved billers are nested under 'data' key
        data = response.data.get('data', {})
        self.assertEqual(len(data.get('saved_billers', [])), 1)
    
    def test_delete_saved_biller(self):
        """Test deleting a saved biller."""
        self.authenticate()
        
        saved = SavedBiller.objects.create(
            user=self.user,
            biller=self.biller,
            consumer_number='DEL123',
            nickname='To Delete'
        )
        
        response = self.client.delete(f'/api/bills/saved/{saved.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SavedBiller.objects.filter(id=saved.id).exists())


# =============================================================================
# NEW TESTS FOR BILL PAY EXPANSION
# =============================================================================

from .models import UserBankAccount, UserCard, UserMPIN, PaymentGateway, TransactionLog


class BankAccountTests(APITestCase):
    """Tests for Bank Account management."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='bankuser',
            email='bank@example.com',
            phone_number='9876543212'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
    
    def authenticate(self):
        from users_auth.jwt_utils import JWTManager
        from users_auth.models import UserSession
        
        tokens = JWTManager.generate_tokens(self.user)
        UserSession.objects.create(
            user=self.user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address='127.0.0.1',
            user_agent='Test Client'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    
    def test_list_bank_accounts_empty(self):
        """Test listing bank accounts when empty."""
        self.authenticate()
        response = self.client.get('/api/bills/bank-accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data['data']['count'], 0)
    
    def test_add_bank_account(self):
        """Test adding a bank account."""
        self.authenticate()
        response = self.client.post('/api/bills/bank-accounts/', {
            'account_holder_name': 'Test User',
            'account_number': '123456789012',
            'confirm_account_number': '123456789012',
            'ifsc_code': 'SBIN0001234',
            'bank_name': 'State Bank of India',
            'account_type': 'SAVINGS',
            'nickname': 'Salary Account'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))
    
    def test_add_bank_account_mismatched_numbers(self):
        """Test that mismatched account numbers are rejected."""
        self.authenticate()
        response = self.client.post('/api/bills/bank-accounts/', {
            'account_holder_name': 'Test User',
            'account_number': '123456789012',
            'confirm_account_number': '987654321012',
            'ifsc_code': 'SBIN0001234',
            'bank_name': 'State Bank of India',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_bank_account_invalid_ifsc(self):
        """Test that invalid IFSC is rejected."""
        self.authenticate()
        response = self.client.post('/api/bills/bank-accounts/', {
            'account_holder_name': 'Test User',
            'account_number': '123456789012',
            'confirm_account_number': '123456789012',
            'ifsc_code': 'INVALID',
            'bank_name': 'State Bank of India',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CardTests(APITestCase):
    """Tests for Card management."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='carduser',
            email='card@example.com',
            phone_number='9876543213'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
    
    def authenticate(self):
        from users_auth.jwt_utils import JWTManager
        from users_auth.models import UserSession
        
        tokens = JWTManager.generate_tokens(self.user)
        UserSession.objects.create(
            user=self.user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address='127.0.0.1',
            user_agent='Test Client'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    
    def test_list_cards_empty(self):
        """Test listing cards when empty."""
        self.authenticate()
        response = self.client.get('/api/bills/cards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data['data']['count'], 0)
    
    def test_add_card(self):
        """Test adding a card."""
        self.authenticate()
        response = self.client.post('/api/bills/cards/', {
            'card_number': '4111111111111111',
            'card_holder_name': 'Test User',
            'expiry_month': '12',
            'expiry_year': '2028',
            'card_type': 'DEBIT',
            'card_network': 'VISA',
            'nickname': 'Primary Card'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))


class MPINTests(APITestCase):
    """Tests for MPIN functionality."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='mpinuser',
            email='mpin@example.com',
            phone_number='9876543214'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
    
    def authenticate(self):
        from users_auth.jwt_utils import JWTManager
        from users_auth.models import UserSession
        
        tokens = JWTManager.generate_tokens(self.user)
        UserSession.objects.create(
            user=self.user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address='127.0.0.1',
            user_agent='Test Client'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    
    def test_mpin_status_not_set(self):
        """Test checking MPIN status when not set."""
        self.authenticate()
        response = self.client.get('/api/bills/mpin/setup/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['data']['has_mpin'])
    
    def test_mpin_setup(self):
        """Test setting up MPIN."""
        self.authenticate()
        response = self.client.post('/api/bills/mpin/setup/', {
            'mpin': '123456',
            'confirm_mpin': '123456',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['data']['has_mpin'])
    
    def test_mpin_setup_wrong_password(self):
        """Test MPIN setup with wrong password is rejected."""
        self.authenticate()
        response = self.client.post('/api/bills/mpin/setup/', {
            'mpin': '123456',
            'confirm_mpin': '123456',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_mpin_verify(self):
        """Test verifying MPIN."""
        self.authenticate()
        # First setup MPIN
        self.client.post('/api/bills/mpin/setup/', {
            'mpin': '654321',
            'confirm_mpin': '654321',
            'password': 'testpass123'
        })
        # Now verify
        response = self.client.post('/api/bills/mpin/verify/', {
            'mpin': '654321'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['verified'])
    
    def test_mpin_verify_wrong(self):
        """Test that wrong MPIN is rejected."""
        self.authenticate()
        # First setup MPIN
        self.client.post('/api/bills/mpin/setup/', {
            'mpin': '654321',
            'confirm_mpin': '654321',
            'password': 'testpass123'
        })
        # Try wrong MPIN
        response = self.client.post('/api/bills/mpin/verify/', {
            'mpin': '999999'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class IFSCTests(APITestCase):
    """Tests for IFSC verification."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='ifscuser',
            email='ifsc@example.com',
            phone_number='9876543215'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
    
    def authenticate(self):
        from users_auth.jwt_utils import JWTManager
        from users_auth.models import UserSession
        
        tokens = JWTManager.generate_tokens(self.user)
        UserSession.objects.create(
            user=self.user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address='127.0.0.1',
            user_agent='Test Client'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    
    def test_ifsc_verify_valid(self):
        """Test IFSC verification with valid code."""
        self.authenticate()
        response = self.client.get('/api/bills/ifsc/SBIN0001234/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data['data']['bank_name'], 'State Bank of India')
    
    def test_ifsc_verify_invalid_format(self):
        """Test IFSC verification with invalid format."""
        self.authenticate()
        response = self.client.get('/api/bills/ifsc/INVALID/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TransactionLogTests(APITestCase):
    """Tests for Transaction Logs."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='txnuser',
            email='txn@example.com',
            phone_number='9876543216'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
    
    def authenticate(self):
        from users_auth.jwt_utils import JWTManager
        from users_auth.models import UserSession
        
        tokens = JWTManager.generate_tokens(self.user)
        UserSession.objects.create(
            user=self.user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address='127.0.0.1',
            user_agent='Test Client'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    
    def test_list_transactions_empty(self):
        """Test listing transactions when empty."""
        self.authenticate()
        response = self.client.get('/api/bills/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data['data']['pagination']['total_count'], 0)


class PaymentGatewayTests(APITestCase):
    """Tests for Payment Gateways."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='gatewayuser',
            email='gateway@example.com',
            phone_number='9876543217'
        )
        cls.user.set_password('testpass123')
        cls.user.save()
        
        # Create test gateway
        PaymentGateway.objects.create(
            name='Razorpay',
            code='RAZORPAY',
            gateway_type='UPI',
            is_active=True
        )
    
    def authenticate(self):
        from users_auth.jwt_utils import JWTManager
        from users_auth.models import UserSession
        
        tokens = JWTManager.generate_tokens(self.user)
        UserSession.objects.create(
            user=self.user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            ip_address='127.0.0.1',
            user_agent='Test Client'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    
    def test_list_gateways(self):
        """Test listing payment gateways."""
        self.authenticate()
        response = self.client.get('/api/bills/gateways/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertGreaterEqual(len(response.data['data']['gateways']), 1)
