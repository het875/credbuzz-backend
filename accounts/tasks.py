"""
Celery tasks for async operations like OTP sending, email notifications, data cleanup.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from accounts.models import OTPRecord, UserAccount, AuditTrail
from accounts.services.otp_service import OTPService
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


# ===========================
# OTP Tasks
# ===========================

@shared_task
def send_otp_email(otp_record_id, otp_code, otp_type='registration'):
    """
    Send OTP via email asynchronously.
    """
    try:
        otp_record = OTPRecord.objects.get(id=otp_record_id)
        email_to = otp_record.sent_to_email or otp_record.user_code.email
        
        context = {
            'user_name': otp_record.user_code.first_name or 'User',
            'otp_code': otp_code,
            'otp_type': otp_type,
            'validity_minutes': settings.OTP_VALIDITY.get(otp_type, 10),
        }
        
        subject = f'Your OTP for {otp_type} - CredbuzzPay'
        message = render_to_string('emails/otp_email.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email_to],
            html_message=message,
            fail_silently=False,
        )
        
        logger.info(f"OTP email sent to {email_to} for {otp_type}")
        return {'status': 'sent', 'email': email_to}
    
    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def send_otp_sms(otp_record_id, otp_code, otp_type='registration'):
    """
    Send OTP via SMS asynchronously.
    """
    try:
        otp_record = OTPRecord.objects.get(id=otp_record_id)
        phone_to = otp_record.sent_to_mobile or otp_record.user_code.mobile
        
        message = f"Your {otp_type} OTP is: {otp_code}. Valid for {settings.OTP_VALIDITY.get(otp_type, 10)} minutes. Never share this OTP."
        
        # Integration with SMS provider (Twilio, AWS SNS, etc.)
        send_sms_to_phone(phone_to, message)
        
        logger.info(f"OTP SMS sent to {phone_to} for {otp_type}")
        return {'status': 'sent', 'phone': phone_to}
    
    except Exception as e:
        logger.error(f"Failed to send OTP SMS: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


def send_sms_to_phone(phone_number, message):
    """
    Send SMS using configured provider.
    """
    sms_provider = settings.SMS_PROVIDER if hasattr(settings, 'SMS_PROVIDER') else 'twilio'
    
    if sms_provider == 'twilio':
        send_sms_twilio(phone_number, message)
    elif sms_provider == 'aws':
        send_sms_aws(phone_number, message)
    else:
        logger.warning(f"Unknown SMS provider: {sms_provider}")


def send_sms_twilio(phone_number, message):
    """Send SMS using Twilio."""
    try:
        from twilio.rest import Client
        
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_PHONE_NUMBER
        
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_number,
            to=phone_number
        )
    except Exception as e:
        logger.error(f"Twilio SMS failed: {str(e)}")


def send_sms_aws(phone_number, message):
    """Send SMS using AWS SNS."""
    try:
        import boto3
        
        sns_client = boto3.client(
            'sns',
            region_name=settings.AWS_SNS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        sns_client.publish(
            PhoneNumber=phone_number,
            Message=message
        )
    except Exception as e:
        logger.error(f"AWS SNS SMS failed: {str(e)}")


# ===========================
# Email Notification Tasks
# ===========================

@shared_task
def send_registration_confirmation_email(user_id):
    """
    Send registration confirmation email.
    """
    try:
        user = UserAccount.objects.get(id=user_id)
        
        context = {
            'user_name': user.first_name or user.email,
            'user_code': user.user_code,
            'login_url': f"{settings.FRONTEND_URL}/login",
        }
        
        subject = 'Welcome to CredbuzzPay - Registration Confirmation'
        message = render_to_string('emails/registration_confirmation.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )
        
        logger.info(f"Registration confirmation email sent to {user.email}")
    
    except Exception as e:
        logger.error(f"Failed to send registration confirmation: {str(e)}")


@shared_task
def send_kyc_status_email(user_id, kyc_type, status):
    """
    Send KYC verification status email.
    """
    try:
        user = UserAccount.objects.get(id=user_id)
        
        context = {
            'user_name': user.first_name or user.email,
            'kyc_type': kyc_type,
            'status': status,
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
        }
        
        subject = f'{kyc_type} Verification {status.title()} - CredbuzzPay'
        message = render_to_string('emails/kyc_status.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )
        
        logger.info(f"KYC status email sent to {user.email}")
    
    except Exception as e:
        logger.error(f"Failed to send KYC status email: {str(e)}")


@shared_task
def send_suspicious_activity_alert(user_id, activity_description):
    """
    Send suspicious activity alert email.
    """
    try:
        user = UserAccount.objects.get(id=user_id)
        
        context = {
            'user_name': user.first_name or user.email,
            'activity': activity_description,
            'security_url': f"{settings.FRONTEND_URL}/security",
        }
        
        subject = 'Security Alert - Suspicious Activity Detected'
        message = render_to_string('emails/suspicious_activity.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )
        
        logger.info(f"Suspicious activity alert sent to {user.email}")
    
    except Exception as e:
        logger.error(f"Failed to send suspicious activity alert: {str(e)}")


# ===========================
# Data Cleanup Tasks
# ===========================

@shared_task
def cleanup_expired_otps():
    """
    Delete expired OTP records (runs daily).
    """
    try:
        # Get OTP validity period
        max_validity = max(settings.OTP_VALIDITY.values())
        cutoff_time = timezone.now() - timedelta(minutes=max_validity + 60)
        
        deleted_count, _ = OTPRecord.objects.filter(
            created_at__lt=cutoff_time,
            is_used=False
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} expired OTP records")
        return {'deleted': deleted_count}
    
    except Exception as e:
        logger.error(f"Failed to cleanup expired OTPs: {str(e)}")
        return {'error': str(e)}


@shared_task
def cleanup_old_audit_logs(days=90):
    """
    Delete audit logs older than specified days (runs monthly).
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count, _ = AuditTrail.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old audit logs")
        return {'deleted': deleted_count}
    
    except Exception as e:
        logger.error(f"Failed to cleanup old audit logs: {str(e)}")
        return {'error': str(e)}


@shared_task
def cleanup_old_login_activities(days=60):
    """
    Delete old login activity records (runs weekly).
    """
    try:
        from accounts.models import LoginActivity
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count, _ = LoginActivity.objects.filter(
            login_timestamp__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old login activity records")
        return {'deleted': deleted_count}
    
    except Exception as e:
        logger.error(f"Failed to cleanup old login activities: {str(e)}")
        return {'error': str(e)}


# ===========================
# Account Management Tasks
# ===========================

@shared_task
def auto_unblock_user_accounts():
    """
    Auto-unblock users whose block duration has expired (runs every 5 minutes).
    """
    try:
        now = timezone.now()
        
        unblocked_count = 0
        users_to_unblock = UserAccount.objects.filter(
            blocked_until__lte=now,
            user_blocked__gt=0
        )
        
        for user in users_to_unblock:
            user.user_blocked = 0
            user.user_block_reason = None
            user.blocked_until = None
            user.save()
            unblocked_count += 1
        
        logger.info(f"Auto-unblocked {unblocked_count} user accounts")
        return {'unblocked': unblocked_count}
    
    except Exception as e:
        logger.error(f"Failed to auto-unblock user accounts: {str(e)}")
        return {'error': str(e)}


@shared_task
def check_inactive_accounts(days=30):
    """
    Send email to inactive users (runs weekly).
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        inactive_users = UserAccount.objects.filter(
            last_login__lt=cutoff_date,
            is_active=True
        )
        
        for user in inactive_users:
            context = {
                'user_name': user.first_name or user.email,
                'days': days,
                'login_url': f"{settings.FRONTEND_URL}/login",
            }
            
            subject = 'We miss you! Come back to CredbuzzPay'
            message = render_to_string('emails/inactive_user.html', context)
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=message,
                fail_silently=True,
            )
        
        logger.info(f"Sent inactive account emails to {inactive_users.count()} users")
        return {'emailed': inactive_users.count()}
    
    except Exception as e:
        logger.error(f"Failed to check inactive accounts: {str(e)}")
        return {'error': str(e)}


# ===========================
# Report Generation Tasks
# ===========================

@shared_task
def generate_daily_report():
    """
    Generate and send daily report to admins (runs daily at 6 AM).
    """
    try:
        from django.db.models import Count
        from datetime import date
        
        today = timezone.now().date()
        
        stats = {
            'new_registrations': UserAccount.objects.filter(created_at__date=today).count(),
            'kyc_submissions': AuditTrail.objects.filter(
                action='kyc_submit',
                created_at__date=today
            ).count(),
            'failed_logins': LoginActivity.objects.filter(
                login_timestamp__date=today,
                status__startswith='failed'
            ).count(),
            'suspicious_activities': LoginActivity.objects.filter(
                login_timestamp__date=today,
                is_suspicious=True
            ).count(),
        }
        
        context = {
            'date': today,
            'stats': stats,
        }
        
        message = render_to_string('emails/daily_report.html', context)
        
        admin_emails = UserAccount.objects.filter(
            user_role='super_admin'
        ).values_list('email', flat=True)
        
        send_mail(
            f'Daily Report - {today}',
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(admin_emails),
            html_message=message,
            fail_silently=True,
        )
        
        logger.info("Daily report sent to admins")
        return {'status': 'sent'}
    
    except Exception as e:
        logger.error(f"Failed to generate daily report: {str(e)}")
        return {'error': str(e)}
