"""
Admin Email Views
=================
Admin-only views for sending system-wide emails like maintenance notices and important announcements.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rbac.permissions import IsSuperAdmin, IsDeveloper, IsAdmin
from users_auth.email_service import send_maintenance_email, send_important_notice_email
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class IsSystemAdministrator(IsAuthenticated):
    """
    Custom permission to check if user has system administrator privileges.
    Allows Super Admin, Developer, or Admin roles.
    """
    message = "Only system administrators can perform this action."
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        # Check if user has admin/superuser status
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check specific roles
        try:
            user_roles = request.user.roles.values_list('name', flat=True)
            allowed_roles = ['Super Admin', 'Developer', 'System Administrator', 'Admin']
            return any(role in allowed_roles for role in user_roles)
        except:
            return False


class SendMaintenanceEmailView(APIView):
    """
    Send maintenance notification email to users.
    Admin/Developer only.
    
    POST /api/admin/emails/maintenance/
    
    Required permissions: Super Admin, Developer, or specific admin role
    """
    permission_classes = [IsSystemAdministrator]
    
    def post(self, request):
        # Validate request data
        affected_service = request.data.get('affected_service')
        maintenance_start = request.data.get('maintenance_start')
        maintenance_end = request.data.get('maintenance_end')
        description = request.data.get('description', '')
        recipient_type = request.data.get('recipient_type', 'all')  # 'all' or 'active'
        
        if not all([affected_service, maintenance_start, maintenance_end]):
            return Response({
                'success': False,
                'message': 'Missing required fields: affected_service, maintenance_start, maintenance_end'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get recipient emails based on type
        if recipient_type == 'active':
            users = User.objects.filter(is_active=True, email_verified=True)
        else:  # all
            users = User.objects.filter(is_active=True)
        
        recipient_emails = list(users.values_list('email', flat=True))
        
        if not recipient_emails:
            return Response({
                'success': False,
                'message': 'No recipients found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send emails
        try:
            results = send_maintenance_email(
                recipient_emails=recipient_emails,
                affected_service=affected_service,
                maintenance_start=maintenance_start,
                maintenance_end=maintenance_end,
                description=description
            )
            
            # Log the action
            logger.info(
                f"Maintenance email sent by {request.user.username} | "
                f"Service: {affected_service} | "
                f"Sent: {len(results['sent'])} | Failed: {len(results['failed'])}"
            )
            
            return Response({
                'success': True,
                'message': 'Maintenance emails sent',
                'data': {
                    'sent_count': len(results['sent']),
                    'failed_count': len(results['failed']),
                    'sent_to': results['sent'][:10],  # Show first 10
                    'failed': results['failed'][:10] if results['failed'] else []
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error sending maintenance emails: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to send emails: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendImportantNoticeEmailView(APIView):
    """
    Send important notice/announcement email to users.
    Admin/Developer only.
    
    POST /api/admin/emails/notice/
    
    Required permissions: Super Admin, Developer, or specific admin role
    """
    permission_classes = [IsSystemAdministrator]
    
    def post(self, request):
        # Validate request data
        notice_title = request.data.get('notice_title')
        notice_message = request.data.get('notice_message')
        action_required = request.data.get('action_required', False)
        action_url = request.data.get('action_url', None)
        recipient_type = request.data.get('recipient_type', 'all')
        
        if not all([notice_title, notice_message]):
            return Response({
                'success': False,
                'message': 'Missing required fields: notice_title, notice_message'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get recipient emails
        if recipient_type == 'active':
            users = User.objects.filter(is_active=True, email_verified=True)
        elif recipient_type == 'kyc_completed':
            # Users with completed KYC
            from kyc_verification.models import KYCApplication, KYCStatus
            completed_kyc_users = KYCApplication.objects.filter(
                status=KYCStatus.APPROVED
            ).values_list('user__email', flat=True)
            users = User.objects.filter(email__in=completed_kyc_users, is_active=True)
        else:  # all
            users = User.objects.filter(is_active=True)
        
        recipient_emails = list(users.values_list('email', flat=True))
        
        if not recipient_emails:
            return Response({
                'success': False,
                'message': 'No recipients found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send emails
        try:
            results = send_important_notice_email(
                recipient_emails=recipient_emails,
                notice_title=notice_title,
                notice_message=notice_message,
                action_required=action_required,
                action_url=action_url
            )
            
            # Log the action
            logger.info(
                f"Important notice sent by {request.user.username} | "
                f"Title: {notice_title} | "
                f"Sent: {len(results['sent'])} | Failed: {len(results['failed'])}"
            )
            
            return Response({
                'success': True,
                'message': 'Important notice emails sent',
                'data': {
                    'sent_count': len(results['sent']),
                    'failed_count': len(results['failed']),
                    'sent_to': results['sent'][:10],
                    'failed': results['failed'][:10] if results['failed'] else []
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error sending important notice emails: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to send emails: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendTestEmailView(APIView):
    """
    Send test email to admin's own email address.
    Useful for testing email configuration and templates.
    
    POST /api/admin/emails/test/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        email_type = request.data.get('email_type', 'otp')
        
        try:
            if email_type == 'otp':
                from users_auth.email_service import send_otp_email
                success = send_otp_email(
                    email=request.user.email,
                    otp_code='123456',
                    user_name=request.user.get_full_name() or request.user.username
                )
            elif email_type == 'welcome':
                from users_auth.email_service import send_welcome_email
                success = send_welcome_email(
                    email=request.user.email,
                    user_name=request.user.get_full_name() or request.user.username
                )
            elif email_type == 'kyc_completion':
                from users_auth.email_service import send_kyc_completion_welcome_email
                success = send_kyc_completion_welcome_email(
                    email=request.user.email,
                    user_name=request.user.get_full_name() or request.user.username
                )
            elif email_type == 'kyc_reminder':
                from users_auth.email_service import send_kyc_pending_reminder_email
                success = send_kyc_pending_reminder_email(
                    email=request.user.email,
                    user_name=request.user.get_full_name() or request.user.username,
                    current_step=3,
                    total_steps=7
                )
            elif email_type == 'support_ticket':
                from users_auth.email_service import send_support_ticket_auto_reply
                success = send_support_ticket_auto_reply(
                    email=request.user.email,
                    user_name=request.user.get_full_name() or request.user.username,
                    ticket_id='TEST123',
                    ticket_subject='Test Support Ticket'
                )
            else:
                return Response({
                    'success': False,
                    'message': f'Unknown email type: {email_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if success:
                return Response({
                    'success': True,
                    'message': f'Test {email_type} email sent to {request.user.email}'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to send test email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
