"""
Email Constants and Configurations
===================================
Centralized constants for email service management.
"""

# Email Types/Categories
class EmailType:
    """Email type identifiers for logging and tracking."""
    OTP_VERIFICATION = "otp_verification"
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    PASSWORD_RESET_CONFIRMATION = "password_reset_confirmation"
    KYC_PENDING_REMINDER = "kyc_pending_reminder"
    KYC_REJECTION = "kyc_rejection"
    KYC_COMPLETION_WELCOME = "kyc_completion_welcome"
    SUPPORT_TICKET_AUTO_REPLY = "support_ticket_auto_reply"
    MAINTENANCE = "maintenance"
    IMPORTANT_NOTICE = "important_notice"


# Email Status
class EmailStatus:
    """Status of email sending operations."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    QUEUED = "queued"


# Email Priorities
class EmailPriority:
    """Priority levels for email queue."""
    HIGH = 1  # OTP, Password Reset
    MEDIUM = 2  # Welcome, KYC notifications
    LOW = 3  # Newsletters, announcements


# Default Email Settings
DEFAULT_FROM_NAME = "CredBuzzPay"
DEFAULT_SUPPORT_EMAIL = "support@credbuzzpay.com"
DEFAULT_SECURITY_EMAIL = "security@credbuzzpay.com"
DEFAULT_NO_REPLY_EMAIL = "noreply@credbuzzpay.com"

# OTP Settings
OTP_EMAIL_PRIORITY = EmailPriority.HIGH
OTP_MAX_RETRIES = 3

# KYC Settings
KYC_TOTAL_STEPS = 7  # Total KYC steps
KYC_REMINDER_DELAY_HOURS = 24  # Send reminder after 24 hours

# Email Templates Subject Lines
SUBJECT_LINES = {
    EmailType.OTP_VERIFICATION: "🔐 CredBuzzPay - Your Verification Code",
    EmailType.WELCOME: "🎉 Welcome to CredBuzzPay - Let's Get Started!",
    EmailType.PASSWORD_RESET: "🔑 CredBuzzPay - Password Reset Request",
    EmailType.PASSWORD_RESET_CONFIRMATION: "✅ CredBuzzPay - Password Successfully Reset",
    EmailType.KYC_PENDING_REMINDER: "⏰ CredBuzzPay - Complete Your KYC Verification",
    EmailType.KYC_REJECTION: "❌ CredBuzzPay - KYC Application Rejected",
    EmailType.KYC_COMPLETION_WELCOME: "🎉 CredBuzzPay - KYC Verified! Your Account is Fully Active",
    EmailType.SUPPORT_TICKET_AUTO_REPLY: "🎫 CredBuzzPay - Support Ticket Received",
    EmailType.MAINTENANCE: "🛠️ CredBuzzPay - Scheduled Maintenance",
    EmailType.IMPORTANT_NOTICE: "📢 CredBuzzPay - Important Notice",
}

# Brand Colors (for reference in templates)
BRAND_COLORS = {
    'teal_primary': '#00A38D',
    'teal_secondary': '#00D2B8',
    'orange_accent': '#FF8C00',
    'navy': '#1A233A',
    'gray_dark': '#4B5563',
    'gray_medium': '#6B7280',
    'gray_light': '#9CA3AF',
}

# Email Retry Configuration
MAX_EMAIL_RETRIES = 3
RETRY_DELAY_SECONDS = 60  # Wait 60 seconds before retry

# Bulk Email Configuration
BULK_EMAIL_BATCH_SIZE = 50  # Send emails in batches of 50
BULK_EMAIL_DELAY_MS = 100  # Delay between batch sends

# Email Logging
LOG_EMAIL_CONTENT = False  # Set to True only in development for debugging
LOG_EMAIL_RECIPIENTS = True
LOG_EMAIL_FAILURES = True
