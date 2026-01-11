"""
Email Logging Models
====================
Track all emails sent from the system for audit and troubleshooting purposes.
"""

from django.db import models
from django.conf import settings
from users_auth.email_constants import EmailType, EmailStatus, EmailPriority


class EmailLog(models.Model):
    """
    Log all emails sent from the system.
    """
    # Basic Info
    email_type = models.CharField(
        max_length=50,
        choices=[(k, k) for k in [
            EmailType.OTP_VERIFICATION,
            EmailType.WELCOME,
            EmailType.PASSWORD_RESET,
            EmailType.PASSWORD_RESET_CONFIRMATION,
            EmailType.KYC_PENDING_REMINDER,
            EmailType.KYC_REJECTION,
            EmailType.KYC_COMPLETION_WELCOME,
            EmailType.SUPPORT_TICKET_AUTO_REPLY,
            EmailType.MAINTENANCE,
            EmailType.IMPORTANT_NOTICE,
        ]],
        help_text="Type of email sent"
    )
    
    recipient_email = models.EmailField(help_text="Email address of recipient")
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_emails',
        help_text="User who received the email (if applicable)"
    )
    
    # Email Content
    subject = models.CharField(max_length=255)
    # Don't store full email body for privacy/size reasons
    # Just store metadata
    
    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=[
            (EmailStatus.PENDING, 'Pending'),
            (EmailStatus.SENT, 'Sent'),
            (EmailStatus.FAILED, 'Failed'),
            (EmailStatus.QUEUED, 'Queued'),
        ],
        default=EmailStatus.PENDING
    )
    
    priority = models.IntegerField(
        choices=[
            (EmailPriority.HIGH, 'High'),
            (EmailPriority.MEDIUM, 'Medium'),
            (EmailPriority.LOW, 'Low'),
        ],
        default=EmailPriority.MEDIUM
    )
    
    # Retry Logic
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Error Tracking
    error_message = models.TextField(blank=True, null=True)
    
    # Metadata
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_emails',
        help_text="User who triggered the email (for admin-sent emails)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email_type', 'status']),
            models.Index(fields=['recipient_email', '-created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"{self.email_type} to {self.recipient_email} - {self.status}"
    
    @classmethod
    def log_email(cls, email_type, recipient_email, subject, status=EmailStatus.SENT, 
                  recipient_user=None, sent_by=None, priority=EmailPriority.MEDIUM, 
                  error_message=None):
        """
        Helper method to create email log entry.
        """
        return cls.objects.create(
            email_type=email_type,
            recipient_email=recipient_email,
            recipient_user=recipient_user,
            subject=subject,
            status=status,
            priority=priority,
            sent_by=sent_by,
            error_message=error_message
        )
    
    def mark_as_sent(self):
        """Mark email as successfully sent."""
        from django.utils import timezone
        self.status = EmailStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_as_failed(self, error_message):
        """Mark email as failed with error message."""
        self.status = EmailStatus.FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])
    
    def increment_retry(self):
        """Increment retry count."""
        from django.utils import timezone
        self.retry_count += 1
        self.last_retry_at = timezone.now()
        if self.retry_count >= self.max_retries:
            self.status = EmailStatus.FAILED
            self.error_message = f"Max retries ({self.max_retries}) exceeded"
        self.save(update_fields=['retry_count', 'last_retry_at', 'status', 'error_message', 'updated_at'])


class EmailTemplate(models.Model):
    """
    Store customizable email templates (optional - for future use).
    Allows admins to modify email templates without code changes.
    """
    name = models.CharField(max_length=100, unique=True)
    email_type = models.CharField(max_length=50, unique=True)
    subject_template = models.CharField(max_length=255)
    html_template = models.TextField()
    plain_text_template = models.TextField()
    
    # Variables that can be used in template
    available_variables = models.JSONField(
        default=dict,
        help_text="JSON dict of available variables for this template"
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.email_type})"
