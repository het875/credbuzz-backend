"""
Audit and Reporting APIs.
Handles audit trails, login history, KYC reports, and security endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from accounts.models import (
    AuditTrail, LoginActivity, UserAccount, AadhaarKYC, PANKYC,
    BusinessDetails, BankDetails
)
from accounts.serializers import (
    LoginActivitySerializer, AuditTrailSerializer
)
from accounts.permissions import IsAdmin, IsActiveUser, IsNotBlocked


class AuditTrailViewSet(viewsets.ViewSet):
    """
    Audit trail and activity logging endpoints.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['get'])
    def get_audit_trail(self, request):
        """
        GET /api/v1/admin/audit/trail
        Get audit trail with optional filters.
        """
        try:
            # Get filter parameters
            user_code = request.query_params.get('user_code')
            action_type = request.query_params.get('action')
            resource_type = request.query_params.get('resource_type')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Build query
            query = AuditTrail.objects.all()
            
            if user_code:
                query = query.filter(user_code__user_code=user_code)
            
            if action_type:
                query = query.filter(action=action_type)
            
            if resource_type:
                query = query.filter(resource_type=resource_type)
            
            if start_date:
                query = query.filter(created_at__gte=start_date)
            
            if end_date:
                query = query.filter(created_at__lte=end_date)
            
            # Paginate
            total_count = query.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            trails = query.order_by('-created_at')[start_idx:end_idx]
            
            serializer = AuditTrailSerializer(trails, many=True)
            
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
    def get_user_audit(self, request):
        """
        GET /api/v1/admin/audit/user?user_code=XX
        Get audit trail for specific user.
        """
        try:
            user_code = request.query_params.get('user_code')
            if not user_code:
                return Response(
                    {'error': 'user_code is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            query = AuditTrail.objects.filter(user_code__user_code=user_code)
            
            total_count = query.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            trails = query.order_by('-created_at')[start_idx:end_idx]
            
            serializer = AuditTrailSerializer(trails, many=True)
            
            return Response({
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'user_code': user_code,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoginActivityViewSet(viewsets.ViewSet):
    """
    Login activity and session tracking endpoints.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def get_my_login_history(self, request):
        """
        GET /api/v1/user/login-history
        Get logged-in user's login history.
        """
        try:
            user = request.user
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            query = LoginActivity.objects.filter(user_code=user)
            
            total_count = query.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            activities = query.order_by('-login_timestamp')[start_idx:end_idx]
            
            serializer = LoginActivitySerializer(activities, many=True)
            
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
    def get_user_login_history(self, request):
        """
        GET /api/v1/admin/login-history?user_code=XX
        Get login history for specific user (Admin only).
        """
        try:
            user_code = request.query_params.get('user_code')
            if not user_code:
                return Response(
                    {'error': 'user_code is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            query = LoginActivity.objects.filter(user_code__user_code=user_code)
            
            total_count = query.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            activities = query.order_by('-login_timestamp')[start_idx:end_idx]
            
            serializer = LoginActivitySerializer(activities, many=True)
            
            return Response({
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'user_code': user_code,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_failed_login_attempts(self, request):
        """
        GET /api/v1/admin/failed-logins
        Get failed login attempts (Admin only).
        """
        try:
            # Get last 24 hours by default
            hours = int(request.query_params.get('hours', 24))
            start_time = timezone.now() - timedelta(hours=hours)
            
            query = LoginActivity.objects.filter(
                login_timestamp__gte=start_time,
                status__startswith='failed'
            )
            
            # Group by IP and user
            suspicious_ips = query.values('ip_address').annotate(
                attempts=Count('id')
            ).filter(attempts__gte=5).order_by('-attempts')
            
            return Response({
                'period_hours': hours,
                'start_time': start_time,
                'total_failed_attempts': query.count(),
                'suspicious_ips': list(suspicious_ips),
                'recent_attempts': LoginActivitySerializer(
                    query.order_by('-login_timestamp')[:20],
                    many=True
                ).data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class KYCReportingViewSet(viewsets.ViewSet):
    """
    KYC verification reporting and status endpoints.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['get'])
    def get_kyc_report(self, request):
        """
        GET /api/v1/admin/reports/kyc
        Get comprehensive KYC verification report.
        """
        try:
            # Calculate statistics
            total_users = UserAccount.objects.count()
            kyc_complete_users = UserAccount.objects.filter(is_kyc_complete=True).count()
            
            aadhaar_verified = AadhaarKYC.objects.filter(is_verified=True).count()
            pan_verified = PANKYC.objects.filter(is_verified=True).count()
            business_verified = BusinessDetails.objects.filter(is_verified=True).count()
            bank_verified = BankDetails.objects.filter(is_verified=True).count()
            
            aadhaar_pending = AadhaarKYC.objects.filter(is_verified=False).count()
            pan_pending = PANKYC.objects.filter(is_verified=False).count()
            business_pending = BusinessDetails.objects.filter(is_verified=False).count()
            bank_pending = BankDetails.objects.filter(is_verified=False).count()
            
            report_data = {
                'timestamp': timezone.now(),
                'total_users': total_users,
                'kyc_complete_users': kyc_complete_users,
                'kyc_completion_rate': (kyc_complete_users / total_users * 100) if total_users > 0 else 0,
                'verification_status': {
                    'aadhaar': {
                        'verified': aadhaar_verified,
                        'pending': aadhaar_pending,
                        'total': aadhaar_verified + aadhaar_pending
                    },
                    'pan': {
                        'verified': pan_verified,
                        'pending': pan_pending,
                        'total': pan_verified + pan_pending
                    },
                    'business': {
                        'verified': business_verified,
                        'pending': business_pending,
                        'total': business_verified + business_pending
                    },
                    'bank': {
                        'verified': bank_verified,
                        'pending': bank_pending,
                        'total': bank_verified + bank_pending
                    }
                }
            }
            
            return Response(report_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_pending_kyc(self, request):
        """
        GET /api/v1/admin/reports/pending-kyc
        Get list of users with pending KYC verification.
        """
        try:
            kyc_type = request.query_params.get('type', 'all')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            if kyc_type == 'aadhaar':
                query = AadhaarKYC.objects.filter(is_verified=False)
            elif kyc_type == 'pan':
                query = PANKYC.objects.filter(is_verified=False)
            elif kyc_type == 'business':
                query = BusinessDetails.objects.filter(is_verified=False)
            elif kyc_type == 'bank':
                query = BankDetails.objects.filter(is_verified=False)
            else:
                # Get users with incomplete KYC
                query = UserAccount.objects.filter(is_kyc_complete=False)
                total_count = query.count()
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                
                from accounts.serializers import UserAccountSerializer
                serializer = UserAccountSerializer(query[start_idx:end_idx], many=True)
                
                return Response({
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size,
                    'kyc_type': 'all',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            total_count = query.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            pending_records = query[start_idx:end_idx]
            
            return Response({
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'kyc_type': kyc_type,
                'data': [
                    {
                        'id': record.id,
                        'user_code': record.user_code.user_code,
                        'email': record.user_code.email,
                        'submitted_at': record.created_at,
                        'record_type': query.model.__name__
                    }
                    for record in pending_records
                ]
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SecurityReportingViewSet(viewsets.ViewSet):
    """
    Security monitoring and threat reporting endpoints.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['get'])
    def get_security_summary(self, request):
        """
        GET /api/v1/admin/reports/security
        Get security summary and threats.
        """
        try:
            # Last 24 hours
            start_time = timezone.now() - timedelta(hours=24)
            
            # Failed logins
            failed_logins = LoginActivity.objects.filter(
                login_timestamp__gte=start_time,
                status__startswith='failed'
            ).count()
            
            # Suspicious activities
            suspicious_logins = LoginActivity.objects.filter(
                login_timestamp__gte=start_time,
                is_suspicious=True
            ).count()
            
            # Blocked users
            blocked_users = UserAccount.objects.filter(user_blocked=1).count()
            
            # High risk logins
            high_risk_logins = LoginActivity.objects.filter(
                login_timestamp__gte=start_time,
                risk_score__gte=70
            ).count()
            
            security_data = {
                'period': '24_hours',
                'start_time': start_time,
                'end_time': timezone.now(),
                'metrics': {
                    'failed_login_attempts': failed_logins,
                    'suspicious_activities': suspicious_logins,
                    'currently_blocked_users': blocked_users,
                    'high_risk_logins': high_risk_logins
                },
                'threat_level': self._calculate_threat_level(failed_logins, suspicious_logins, high_risk_logins)
            }
            
            return Response(security_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_suspicious_activities(self, request):
        """
        GET /api/v1/admin/reports/suspicious
        Get suspicious activities for investigation.
        """
        try:
            hours = int(request.query_params.get('hours', 24))
            start_time = timezone.now() - timedelta(hours=hours)
            
            suspicious = LoginActivity.objects.filter(
                login_timestamp__gte=start_time,
                is_suspicious=True
            ).order_by('-risk_score')[:50]
            
            serializer = LoginActivitySerializer(suspicious, many=True)
            
            return Response({
                'period_hours': hours,
                'total_suspicious': suspicious.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @staticmethod
    def _calculate_threat_level(failed_logins, suspicious_logins, high_risk_logins):
        """Calculate overall threat level."""
        score = (failed_logins * 0.3) + (suspicious_logins * 0.5) + (high_risk_logins * 0.2)
        
        if score >= 100:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 20:
            return 'MEDIUM'
        elif score >= 5:
            return 'LOW'
        else:
            return 'NORMAL'
