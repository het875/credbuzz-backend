"""
Tests for users_auth app
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, PasswordResetToken, UserSession
from .jwt_utils import JWTManager


class UserModelTests(TestCase):
    """Tests for the custom User model"""
    
    def test_create_user(self):
        """Test creating a user"""
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        user.set_password('Test@1234')
        user.save()
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('Test@1234'))
        self.assertFalse(user.check_password('wrongpassword'))
    
    def test_password_hashing(self):
        """Test password is hashed properly"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('mypassword')
        
        self.assertNotEqual(user.password_hash, 'mypassword')
        self.assertTrue(len(user.salt) > 0)
    
    def test_full_name_property(self):
        """Test full_name property"""
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.full_name, 'John Doe')
        
        user2 = User(email='test2@example.com', username='testuser2')
        self.assertEqual(user2.full_name, 'testuser2')
    
    def test_is_authenticated_property(self):
        """Test is_authenticated property"""
        user = User(email='test@example.com', username='testuser')
        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_anonymous)


class PasswordResetTokenTests(TestCase):
    """Tests for PasswordResetToken model"""
    
    def setUp(self):
        self.user = User(email='test@example.com', username='testuser')
        self.user.set_password('Test@1234')
        self.user.save()
    
    def test_create_token(self):
        """Test creating a reset token"""
        token = PasswordResetToken.create_token(self.user)
        
        self.assertIsNotNone(token.token)
        self.assertTrue(token.is_valid())
        self.assertFalse(token.is_used)
    
    def test_mark_as_used(self):
        """Test marking token as used"""
        token = PasswordResetToken.create_token(self.user)
        token.mark_as_used()
        
        self.assertTrue(token.is_used)
        self.assertFalse(token.is_valid())


class JWTManagerTests(TestCase):
    """Tests for JWT utilities"""
    
    def setUp(self):
        self.user = User(email='test@example.com', username='testuser')
        self.user.set_password('Test@1234')
        self.user.save()
    
    def test_generate_access_token(self):
        """Test generating access token"""
        token, token_id, expiry = JWTManager.generate_access_token(self.user)
        
        self.assertIsNotNone(token)
        self.assertIsNotNone(token_id)
        self.assertIsNotNone(expiry)
    
    def test_generate_tokens(self):
        """Test generating both access and refresh tokens"""
        tokens = JWTManager.generate_tokens(self.user)
        
        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)
        self.assertIn('access_token_id', tokens)
        self.assertIn('refresh_token_id', tokens)
    
    def test_decode_token(self):
        """Test decoding a valid token"""
        token, _, _ = JWTManager.generate_access_token(self.user)
        payload = JWTManager.decode_token(token)
        
        self.assertEqual(payload['user_id'], self.user.id)
        self.assertEqual(payload['email'], self.user.email)
        self.assertEqual(payload['token_type'], 'access')
    
    def test_verify_token(self):
        """Test verifying a token"""
        token, _, _ = JWTManager.generate_access_token(self.user)
        payload = JWTManager.verify_token(token, token_type='access')
        
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], self.user.id)
    
    def test_get_user_id_from_token(self):
        """Test extracting user ID from token"""
        token, _, _ = JWTManager.generate_access_token(self.user)
        user_id = JWTManager.get_user_id_from_token(token)
        
        self.assertEqual(user_id, self.user.id)


class AuthAPITests(APITestCase):
    """Tests for authentication API endpoints"""
    
    def test_register_user(self):
        """Test user registration endpoint"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'Test@1234',
            'confirm_password': 'Test@1234',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data['data'])
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails"""
        User.objects.create(
            email='existing@example.com',
            username='existing',
            password_hash='hash',
            salt='salt'
        )
        
        data = {
            'email': 'existing@example.com',
            'username': 'newuser',
            'password': 'Test@1234',
            'confirm_password': 'Test@1234'
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_login_user(self):
        """Test user login endpoint"""
        # Create user first
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        data = {
            'email': 'test@example.com',
            'password': 'Test@1234'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data['data']['tokens'])
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_get_profile_authenticated(self):
        """Test getting profile when authenticated"""
        # Create and login user
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        token, _, _ = JWTManager.generate_access_token(user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['email'], 'test@example.com')
    
    def test_get_profile_unauthenticated(self):
        """Test getting profile without authentication"""
        response = self.client.get('/api/auth/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile(self):
        """Test updating user profile"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        token, _, _ = JWTManager.generate_access_token(user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.put('/api/auth/profile/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['first_name'], 'Updated')
    
    def test_forgot_password(self):
        """Test forgot password endpoint"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        data = {'email': 'test@example.com'}
        response = self.client.post('/api/auth/forgot-password/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_reset_password(self):
        """Test reset password endpoint"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        reset_token = PasswordResetToken.create_token(user)
        
        data = {
            'token': reset_token.token,
            'new_password': 'NewPass@1234',
            'confirm_password': 'NewPass@1234'
        }
        response = self.client.post('/api/auth/reset-password/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify new password works
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPass@1234'))
    
    def test_change_password(self):
        """Test change password endpoint"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        token, _, _ = JWTManager.generate_access_token(user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'current_password': 'Test@1234',
            'new_password': 'NewPass@1234',
            'confirm_password': 'NewPass@1234'
        }
        response = self.client.post('/api/auth/change-password/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_user_list(self):
        """Test user list endpoint"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        token, _, _ = JWTManager.generate_access_token(user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 1)
    
    def test_delete_user(self):
        """Test delete (deactivate) user endpoint"""
        user1 = User(email='test1@example.com', username='testuser1')
        user1.set_password('Test@1234')
        user1.save()
        
        user2 = User(email='test2@example.com', username='testuser2')
        user2.set_password('Test@1234')
        user2.save()
        
        token, _, _ = JWTManager.generate_access_token(user1)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.delete(f'/api/auth/users/{user2.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        user2.refresh_from_db()
        self.assertFalse(user2.is_active)
    
    def test_refresh_token(self):
        """Test token refresh endpoint"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        tokens = JWTManager.generate_tokens(user)
        
        # Create session for refresh token
        from django.utils import timezone
        UserSession.objects.create(
            user=user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            is_active=True
        )
        
        data = {'refresh_token': tokens['refresh_token']}
        response = self.client.post('/api/auth/refresh-token/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data['data'])

