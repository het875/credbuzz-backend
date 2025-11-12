"""
Celery configuration for credbuzzpay_backend.
"""
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'credbuzzpay_backend.settings')

app = Celery('credbuzzpay_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # OTP Cleanup
    'cleanup-expired-otps': {
        'task': 'accounts.tasks.cleanup_expired_otps',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    
    # Auto-unblock users
    'auto-unblock-users': {
        'task': 'accounts.tasks.auto_unblock_user_accounts',
        'schedule': 300,  # Every 5 minutes
    },
    
    # Cleanup old audit logs
    'cleanup-old-audit-logs': {
        'task': 'accounts.tasks.cleanup_old_audit_logs',
        'schedule': crontab(day_of_month=1, hour=3, minute=0),  # First day of month at 3 AM
    },
    
    # Cleanup old login activities
    'cleanup-old-login-activities': {
        'task': 'accounts.tasks.cleanup_old_login_activities',
        'schedule': crontab(day_of_week=0, hour=4, minute=0),  # Weekly on Sunday at 4 AM
    },
    
    # Check inactive accounts
    'check-inactive-accounts': {
        'task': 'accounts.tasks.check_inactive_accounts',
        'schedule': crontab(day_of_week=1, hour=10, minute=0),  # Weekly on Monday at 10 AM
    },
    
    # Generate daily report
    'generate-daily-report': {
        'task': 'accounts.tasks.generate_daily_report',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
