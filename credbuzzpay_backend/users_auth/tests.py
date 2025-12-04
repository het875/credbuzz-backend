"""
Tests for users_auth app
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import User, PasswordResetToken, UserSession, LoginAttempt
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
    
    def test_user_code_auto_generation(self):
        """Test that user_code is auto-generated if not provided"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        self.assertIsNotNone(user.user_code)
        self.assertEqual(len(user.user_code), 6)


class LoginAttemptTests(TestCase):
    """Tests for LoginAttempt model and lockout logic"""
    
    def setUp(self):
        self.user = User(email='test@example.com', username='testuser')
        self.user.set_password('Test@1234')
        self.user.save()
    
    def test_create_login_attempt(self):
        """Test creating a login attempt record"""
        attempt = LoginAttempt.get_or_create_for_identifier(
            identifier='test@example.com',
            identifier_type='EMAIL',
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(attempt.identifier, 'test@example.com')
        self.assertEqual(attempt.identifier_type, 'EMAIL')
        self.assertEqual(attempt.attempt_count, 0)
    
    def test_record_failed_attempts(self):
        """Test recording failed login attempts"""
        attempt = LoginAttempt.get_or_create_for_identifier(
            identifier='test@example.com',
            identifier_type='EMAIL'
        )
        
        # Record 4 failed attempts
        for i in range(4):
            result = attempt.record_failed_attempt()
            self.assertEqual(result['remaining_attempts'], 4 - i)
        
        # Should still not be locked
        is_locked, _ = attempt.is_locked_out()
        self.assertFalse(is_locked)
    
    def test_lockout_after_max_attempts(self):
        """Test lockout triggers after max attempts"""
        attempt = LoginAttempt.get_or_create_for_identifier(
            identifier='test@example.com',
            identifier_type='EMAIL'
        )
        
        # Record 5 failed attempts (max for first stage)
        for _ in range(5):
            attempt.record_failed_attempt()
        
        # Should now be locked
        is_locked, message = attempt.is_locked_out()
        self.assertTrue(is_locked)
        self.assertIn('try again', message.lower())
        self.assertEqual(attempt.lockout_stage, 1)
    
    def test_progressive_lockout_stages(self):
        """Test progressive lockout through stages"""
        attempt = LoginAttempt.get_or_create_for_identifier(
            identifier='test@example.com',
            identifier_type='EMAIL'
        )
        
        # Go through first 3 lockout stages
        for stage in range(3):
            # Clear lockout for testing
            attempt.lockout_until = None
            attempt.attempt_count = 0
            
            # Trigger lockout
            for _ in range(5):
                attempt.record_failed_attempt()
        
        self.assertEqual(attempt.lockout_stage, 3)
    
    def test_successful_login_resets_attempts(self):
        """Test that successful login resets attempt tracking"""
        attempt = LoginAttempt.get_or_create_for_identifier(
            identifier='test@example.com',
            identifier_type='EMAIL'
        )
        
        # Record some failed attempts
        for _ in range(3):
            attempt.record_failed_attempt()
        
        # Successful login
        attempt.record_successful_login(user=self.user)
        
        self.assertEqual(attempt.attempt_count, 0)
        self.assertEqual(attempt.lockout_stage, 0)
        self.assertIsNone(attempt.lockout_until)
    
    def test_blocked_account(self):
        """Test permanent block after all stages"""
        attempt = LoginAttempt.get_or_create_for_identifier(
            identifier='test@example.com',
            identifier_type='EMAIL'
        )
        
        # Go through all stages to reach blocked state
        for stage in range(6):
            attempt.lockout_until = None
            attempt.attempt_count = 0
            for _ in range(5):
                attempt.record_failed_attempt()
        
        # Should be permanently blocked
        self.assertTrue(attempt.is_blocked)
        is_locked, message = attempt.is_locked_out()
        self.assertTrue(is_locked)
        self.assertIn('blocked', message.lower())


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


class UserSessionTests(TestCase):
    """Tests for UserSession model with inactivity timeout"""
    
    def setUp(self):
        self.user = User(email='test@example.com', username='testuser')
        self.user.set_password('Test@1234')
        self.user.save()
    
    def test_session_activity_tracking(self):
        """Test session activity timestamp updates"""
        session = UserSession.objects.create(
            user=self.user,
            token_id='test-token-id',
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True
        )
        
        old_activity = session.last_activity
        session.update_activity()
        
        self.assertGreaterEqual(session.last_activity, old_activity)
    
    def test_inactivity_expiry(self):
        """Test session expiry due to inactivity"""
        session = UserSession.objects.create(
            user=self.user,
            token_id='test-token-id',
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True
        )
        
        # Session is fresh, should not be expired
        self.assertFalse(session.is_inactive_expired(inactivity_minutes=30))
        
        # Simulate old activity (31 minutes ago)
        session.last_activity = timezone.now() - timedelta(minutes=31)
        session.save()
        
        # Now should be expired
        self.assertTrue(session.is_inactive_expired(inactivity_minutes=30))


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
    
    def test_token_includes_user_details(self):
        """Test that token includes user_code and user_role"""
        token, _, _ = JWTManager.generate_access_token(self.user)
        payload = JWTManager.decode_token(token)
        
        self.assertEqual(payload['user_code'], self.user.user_code)
        self.assertEqual(payload['user_role'], self.user.user_role)
        self.assertIn('app_access', payload)
        self.assertIn('feature_access', payload)
    
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
    
    def test_login_with_email(self):
        """Test user login with email as identifier"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        data = {
            'identifier': 'test@example.com',
            'password': 'Test@1234'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data['data']['tokens'])
        self.assertIn('app_access', response.data['data'])
        self.assertIn('feature_access', response.data['data'])
    
    def test_login_with_username(self):
        """Test user login with username as identifier"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        data = {
            'identifier': 'testuser',
            'password': 'Test@1234'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_login_with_user_code(self):
        """Test user login with user_code as identifier"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        data = {
            'identifier': user.user_code,
            'password': 'Test@1234'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_login_with_phone_number(self):
        """Test user login with phone number as identifier"""
        user = User(email='test@example.com', username='testuser', phone_number='+1234567890')
        user.set_password('Test@1234')
        user.save()
        
        data = {
            'identifier': '+1234567890',
            'password': 'Test@1234'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_login_response_includes_permissions(self):
        """Test login response includes app_access and feature_access"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        data = {
            'identifier': 'test@example.com',
            'password': 'Test@1234'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('app_access', response.data['data'])
        self.assertIn('feature_access', response.data['data'])
        self.assertIn('session', response.data['data'])
        self.assertIn('inactivity_timeout_minutes', response.data['data']['session'])
    
    def test_login_invalid_credentials_shows_remaining_attempts(self):
        """Test login with invalid credentials shows remaining attempts"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        data = {
            'identifier': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
        self.assertIn('remaining_attempts', response.data['data'])
    
    def test_login_lockout_after_max_attempts(self):
        """Test login lockout after max failed attempts"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        # Make 5 failed attempts
        for _ in range(5):
            data = {
                'identifier': 'test@example.com',
                'password': 'wrongpassword'
            }
            self.client.post('/api/auth/login/', data, format='json')
        
        # 6th attempt should be locked out
        data = {
            'identifier': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(response.data['success'])
        self.assertTrue(response.data['data']['is_locked'])
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'identifier': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_get_profile_authenticated(self):
        """Test getting profile when authenticated"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        # Create session for activity tracking
        tokens = JWTManager.generate_tokens(user)
        UserSession.objects.create(
            user=user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
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
        
        tokens = JWTManager.generate_tokens(user)
        UserSession.objects.create(
            user=user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
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
        
        tokens = JWTManager.generate_tokens(user)
        UserSession.objects.create(
            user=user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
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
        
        tokens = JWTManager.generate_tokens(user)
        UserSession.objects.create(
            user=user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
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
        
        tokens = JWTManager.generate_tokens(user1)
        UserSession.objects.create(
            user=user1,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
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
    
    def test_refresh_token_fails_on_inactive_session(self):
        """Test token refresh fails if session is expired due to inactivity"""
        user = User(email='test@example.com', username='testuser')
        user.set_password('Test@1234')
        user.save()
        
        tokens = JWTManager.generate_tokens(user)
        
        # Create session with old activity (expired)
        session = UserSession.objects.create(
            user=user,
            token_id=tokens['refresh_token_id'],
            expires_at=tokens['refresh_token_expiry'],
            is_active=True
        )
        # Simulate inactivity
        session.last_activity = timezone.now() - timedelta(minutes=31)
        session.save()
        
        data = {'refresh_token': tokens['refresh_token']}
        response = self.client.post('/api/auth/refresh-token/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

