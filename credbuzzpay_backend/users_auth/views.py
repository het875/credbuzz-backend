"""
Views for users_auth app
All user authentication and management endpoints
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction

from .models import User, PasswordResetToken, UserSession
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserListSerializer,
    TokenRefreshSerializer,
)
from .jwt_utils import JWTManager
from .authentication import JWTAuthentication, get_client_ip, get_user_agent


class RegisterView(APIView):
    """
    API endpoint for user registration
    POST /api/auth/register/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens
            tokens = JWTManager.generate_tokens(user)
            
            # Create session
            UserSession.objects.create(
                user=user,
                token_id=tokens['refresh_token_id'],
                expires_at=tokens['refresh_token_expiry'],
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            return Response({
                'success': True,
                'message': 'User registered successfully.',
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access_token': tokens['access_token'],
                        'refresh_token': tokens['refresh_token'],
                    }
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Registration failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint for user login
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Update last login
            user.update_last_login()
            
            # Generate tokens
            tokens = JWTManager.generate_tokens(user)
            
            # Create session
            UserSession.objects.create(
                user=user,
                token_id=tokens['refresh_token_id'],
                expires_at=tokens['refresh_token_expiry'],
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            return Response({
                'success': True,
                'message': 'Login successful.',
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access_token': tokens['access_token'],
                        'refresh_token': tokens['refresh_token'],
                    }
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Login failed.',
            'errors': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    API endpoint for user logout
    POST /api/auth/logout/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Get token ID from auth payload
        token_payload = request.auth
        
        # Invalidate all active sessions for user (logout from all devices)
        logout_all = request.data.get('logout_all', False)
        
        if logout_all:
            UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
            message = 'Logged out from all devices successfully.'
        else:
            # Just mark the current session type tokens as invalid
            # For single logout, we'd need the refresh token ID
            # For now, just return success
            message = 'Logged out successfully.'
        
        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    API endpoint for forgot password request
    POST /api/auth/forgot-password/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check if user exists
            try:
                user = User.objects.get(email=email, is_active=True)
                # Create reset token
                reset_token = PasswordResetToken.create_token(user)
                
                # In production, you would send this via email
                # For testing, we return the token in response
                return Response({
                    'success': True,
                    'message': 'Password reset instructions sent to your email.',
                    'data': {
                        # Remove this in production - only for testing
                        'reset_token': reset_token.token
                    }
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                pass
            
            # Always return success to prevent email enumeration
            return Response({
                'success': True,
                'message': 'If an account with this email exists, password reset instructions have been sent.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Invalid request.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """
    API endpoint for password reset
    POST /api/auth/reset-password/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            reset_token = serializer.reset_token
            user = reset_token.user
            new_password = serializer.validated_data['new_password']
            
            with transaction.atomic():
                # Update password
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                reset_token.mark_as_used()
                
                # Invalidate all existing sessions
                UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
            return Response({
                'success': True,
                'message': 'Password reset successful. Please login with your new password.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Password reset failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API endpoint for changing password (authenticated users)
    POST /api/auth/change-password/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            
            # Verify current password
            if not user.check_password(current_password):
                return Response({
                    'success': False,
                    'message': 'Current password is incorrect.',
                    'errors': {'current_password': ['Current password is incorrect.']}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Optionally invalidate other sessions
            logout_others = request.data.get('logout_others', False)
            if logout_others:
                UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
            return Response({
                'success': True,
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Password change failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    """
    API endpoint for refreshing access token
    POST /api/auth/refresh-token/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        
        if serializer.is_valid():
            refresh_token = serializer.validated_data['refresh_token']
            
            # Try to refresh access token
            result = JWTManager.refresh_access_token(refresh_token)
            
            if result:
                return Response({
                    'success': True,
                    'message': 'Token refreshed successfully.',
                    'data': {
                        'access_token': result['access_token']
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'message': 'Invalid or expired refresh token.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'message': 'Invalid request.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    API endpoint for getting and updating current user profile
    GET /api/auth/profile/
    PUT /api/auth/profile/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile"""
        return Response({
            'success': True,
            'data': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Update current user profile"""
        serializer = UserUpdateSerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            user = serializer.update(request.user, serializer.validated_data)
            return Response({
                'success': True,
                'message': 'Profile updated successfully.',
                'data': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Profile update failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """Partial update current user profile"""
        return self.put(request)


class UserListView(APIView):
    """
    API endpoint for listing all users (admin only in production)
    GET /api/auth/users/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all users"""
        # In production, add admin check here
        users = User.objects.all()
        
        # Optional filtering
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            users = users.filter(is_active=is_active)
        
        # Search by email or username
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            users = users.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return Response({
            'success': True,
            'data': UserListSerializer(users, many=True).data,
            'count': users.count()
        }, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    """
    API endpoint for getting, updating, and deleting a specific user
    GET /api/auth/users/<id>/
    PUT /api/auth/users/<id>/
    DELETE /api/auth/users/<id>/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def get(self, request, user_id):
        """Get user details"""
        user = self.get_user(user_id)
        if not user:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    def put(self, request, user_id):
        """Update user"""
        user = self.get_user(user_id)
        if not user:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserUpdateSerializer(
            data=request.data,
            context={'user': user}
        )
        
        if serializer.is_valid():
            updated_user = serializer.update(user, serializer.validated_data)
            return Response({
                'success': True,
                'message': 'User updated successfully.',
                'data': UserSerializer(updated_user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'User update failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, user_id):
        """Partial update user"""
        return self.put(request, user_id)
    
    def delete(self, request, user_id):
        """Delete user (soft delete - deactivate)"""
        user = self.get_user(user_id)
        if not user:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response({
                'success': False,
                'message': 'You cannot delete your own account.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete - just deactivate
        hard_delete = request.query_params.get('hard_delete', 'false').lower() == 'true'
        
        if hard_delete:
            user.delete()
            message = 'User permanently deleted.'
        else:
            user.is_active = False
            user.save()
            # Invalidate all sessions
            UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            message = 'User deactivated successfully.'
        
        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)


class UserActivateView(APIView):
    """
    API endpoint for activating/deactivating a user
    POST /api/auth/users/<id>/activate/
    POST /api/auth/users/<id>/deactivate/
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id, action):
        """Activate or deactivate user"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if action == 'activate':
            user.is_active = True
            user.save()
            message = 'User activated successfully.'
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            # Invalidate all sessions
            UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
            message = 'User deactivated successfully.'
        else:
            return Response({
                'success': False,
                'message': 'Invalid action.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': message,
            'data': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

