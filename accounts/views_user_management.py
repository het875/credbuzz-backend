"""
User Management APIs.
Handles profile management, user listing, role management, and user blocking.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from accounts.models import UserAccount, AppAccessControl, UserPlatformAccess, SecuritySettings
from accounts.serializers import UserAccountSerializer, UserAccountDetailSerializer
from accounts.utils.security import block_user, unblock_user
from accounts.services.audit_service import log_user_action
from accounts.permissions import IsActiveUser, IsNotBlocked, IsAdmin


class UserProfileViewSet(viewsets.ViewSet):
    """
    User profile management endpoints.
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsNotBlocked]
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """
        GET /api/v1/user/profile
        Get logged-in user's profile.
        """
        try:
            user = request.user
            serializer = UserAccountDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        PUT/PATCH /api/v1/user/profile/update
        Update logged-in user's profile.
        """
        try:
            user = request.user
            
            # Update allowed fields
            allowed_fields = ['first_name', 'middle_name', 'last_name', 'gender', 
                            'address_line1', 'address_line2', 'city', 'state', 'pincode']
            
            for field in allowed_fields:
                if field in request.data:
                    setattr(user, field, request.data[field])
            
            user.updated_last_field = 'profile'
            user.save()
            
            # Log audit
            log_user_action(
                action='update',
                user_code=user,
                description='User profile updated',
                resource_type='UserAccount',
                resource_id=user.user_code,
                ip_address=self._get_client_ip(request)
            )
            
            serializer = UserAccountDetailSerializer(user)
            return Response({
                'message': 'Profile updated successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        POST /api/v1/user/profile/change-password
        Change user password.
        """
        try:
            user = request.user
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            
            if not all([old_password, new_password, confirm_password]):
                return Response(
                    {'error': 'All password fields are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_password != confirm_password:
                return Response(
                    {'error': 'New passwords do not match.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(new_password) < 8:
                return Response(
                    {'error': 'Password must be at least 8 characters long.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify old password (basic check - use proper hashing in production)
            if user.password != old_password:
                return Response(
                    {'error': 'Old password is incorrect.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Update password
            user.password = new_password
            user.password_changed_at = timezone.now()
            user.save()
            
            # Log audit
            log_user_action(
                action='password_change',
                user_code=user,
                description='Password changed',
                resource_type='UserAccount',
                resource_id=user.user_code,
                ip_address=self._get_client_ip(request)
            )
            
            return Response({
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserListViewSet(viewsets.ViewSet):
    """
    User listing and filtering endpoints (Admin only).
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['get'])
    def list_users(self, request):
        """
        GET /api/v1/admin/users/list
        List all users with optional filters.
        """
        try:
            # Get filter parameters
            role = request.query_params.get('role')
            is_active = request.query_params.get('is_active')
            is_blocked = request.query_params.get('is_blocked')
            search = request.query_params.get('search')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Build query
            query = UserAccount.objects.all()
            
            if role:
                query = query.filter(user_role=role)
            
            if is_active is not None:
                query = query.filter(is_active=is_active.lower() == 'true')
            
            if is_blocked is not None:
                query = query.filter(user_blocked=int(is_blocked) if is_blocked in ['0', '1'] else 0)
            
            if search:
                query = query.filter(
                    Q(email__icontains=search) |
                    Q(mobile__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(user_code__icontains=search)
                )
            
            # Paginate
            total_count = query.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            users = query[start_idx:end_idx]
            
            serializer = UserAccountSerializer(users, many=True)
            
            return Response({
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_user(self, request):
        """
        GET /api/v1/admin/users/get?user_code=XX
        Get specific user details.
        """
        try:
            user_code = request.query_params.get('user_code')
            if not user_code:
                return Response(
                    {'error': 'user_code is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = UserAccount.objects.get(user_code=user_code)
            serializer = UserAccountDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserBlockingViewSet(viewsets.ViewSet):
    """
    User blocking/unblocking endpoints (Admin only).
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['post'])
    def block_user(self, request):
        """
        POST /api/v1/admin/users/block
        Block a user account.
        """
        try:
            user_code = request.data.get('user_code')
            reason = request.data.get('reason', '')
            duration_hours = request.data.get('duration_hours', 24)
            
            if not user_code:
                return Response(
                    {'error': 'user_code is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = UserAccount.objects.get(user_code=user_code)
            
            # Block user
            block_user(
                user=user,
                reason=reason,
                duration_hours=duration_hours
            )
            
            # Log audit
            log_user_action(
                action='user_block',
                user_code=request.user,
                description=f'User {user_code} blocked. Reason: {reason}',
                resource_type='UserAccount',
                resource_id=user_code,
                ip_address=self._get_client_ip(request)
            )
            
            return Response({
                'message': f'User {user_code} blocked successfully.',
                'blocked_until': user.blocked_until
            }, status=status.HTTP_200_OK)
        
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def unblock_user(self, request):
        """
        POST /api/v1/admin/users/unblock
        Unblock a user account.
        """
        try:
            user_code = request.data.get('user_code')
            
            if not user_code:
                return Response(
                    {'error': 'user_code is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = UserAccount.objects.get(user_code=user_code)
            
            # Unblock user
            unblock_user(user)
            
            # Log audit
            log_user_action(
                action='user_unblock',
                user_code=request.user,
                description=f'User {user_code} unblocked.',
                resource_type='UserAccount',
                resource_id=user_code,
                ip_address=self._get_client_ip(request)
            )
            
            return Response({
                'message': f'User {user_code} unblocked successfully.'
            }, status=status.HTTP_200_OK)
        
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserRoleManagementViewSet(viewsets.ViewSet):
    """
    User role and permission management endpoints.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['post'])
    def change_role(self, request):
        """
        POST /api/v1/admin/users/change-role
        Change user role.
        """
        try:
            user_code = request.data.get('user_code')
            new_role = request.data.get('new_role')
            
            if not all([user_code, new_role]):
                return Response(
                    {'error': 'user_code and new_role are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = UserAccount.objects.get(user_code=user_code)
            old_role = user.user_role
            
            user.user_role = new_role
            user.save()
            
            # Log audit
            log_user_action(
                action='role_change',
                user_code=request.user,
                description=f'User role changed from {old_role} to {new_role}',
                resource_type='UserAccount',
                resource_id=user_code,
                ip_address=self._get_client_ip(request),
                old_values={'role': old_role},
                new_values={'role': new_role}
            )
            
            return Response({
                'message': 'User role updated successfully.',
                'user_code': user_code,
                'old_role': old_role,
                'new_role': new_role
            }, status=status.HTTP_200_OK)
        
        except UserAccount.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
