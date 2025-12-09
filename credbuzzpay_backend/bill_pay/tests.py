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