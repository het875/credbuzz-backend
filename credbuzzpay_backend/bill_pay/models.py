"""
Bill Pay Models
================
Models for bill payment functionality including:
- Bill Categories (Electricity, Gas, Water, DTH, Mobile, etc.)
- Billers (Service providers)
- Bill Payments (User transactions)
- Transaction History
"""

import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Import custom User model directly
from users_auth.models import User


class BillCategory(models.Model):
    """Categories for different types of bills."""
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)  # e.g., ELECTRICITY, GAS, WATER
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)  # Icon name for frontend
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bill_categories'
        verbose_name = 'Bill Category'
        verbose_name_plural = 'Bill Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class Biller(models.Model):
    """Service providers for bill payments."""
    
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(BillCategory, on_delete=models.CASCADE, related_name='billers')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)  # Unique biller code
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='billers/logos/', blank=True, null=True)
    
    # Biller configuration
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    
    # Required fields for bill fetch (JSON configuration)
    # e.g., {"consumer_number": {"label": "Consumer Number", "type": "text", "required": true}}
    required_fields = models.JSONField(default=dict, blank=True)
    
    # Commission/fee settings
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    platform_fee_type = models.CharField(
        max_length=20,
        choices=[('FIXED', 'Fixed'), ('PERCENTAGE', 'Percentage')],
        default='FIXED'
    )
    
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billers'
        verbose_name = 'Biller'
        verbose_name_plural = 'Billers'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    def calculate_fee(self, amount):
        """Calculate platform fee for a given amount."""
        if self.platform_fee_type == 'FIXED':
            return self.platform_fee
        else:
            return (amount * self.platform_fee) / 100


class PaymentStatus:
    """Payment status choices."""
    INITIATED = 'INITIATED'
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'
    CANCELLED = 'CANCELLED'
    
    CHOICES = [
        (INITIATED, 'Initiated'),
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
        (REFUNDED, 'Refunded'),
        (CANCELLED, 'Cancelled'),
    ]


class BillPayment(models.Model):
    """Records of bill payments made by users."""
    
    id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=50, unique=True, editable=False)
    
    # User and Biller
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='bill_payments'
    )
    biller = models.ForeignKey(Biller, on_delete=models.PROTECT, related_name='payments')
    
    # Consumer/Account details
    consumer_number = models.CharField(max_length=100)
    consumer_name = models.CharField(max_length=200, blank=True)
    consumer_details = models.JSONField(default=dict, blank=True)  # Additional details from bill fetch
    
    # Amount details
    bill_amount = models.DecimalField(max_digits=12, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Bill details (from bill fetch)
    bill_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    bill_number = models.CharField(max_length=100, blank=True)
    bill_period = models.CharField(max_length=100, blank=True)
    
    # Payment status
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.CHOICES,
        default=PaymentStatus.INITIATED
    )
    
    # Payment gateway details
    payment_method = models.CharField(max_length=50, blank=True)  # WALLET, UPI, CARD, NETBANKING
    payment_gateway_ref = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Biller response
    biller_ref_number = models.CharField(max_length=100, blank=True)
    biller_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # For failed/refunded transactions
    failure_reason = models.TextField(blank=True)
    refund_details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'bill_payments'
        verbose_name = 'Bill Payment'
        verbose_name_plural = 'Bill Payments'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['biller', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['consumer_number']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.biller.name} - ₹{self.total_amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate unique transaction ID: BP + timestamp + random
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_suffix = uuid.uuid4().hex[:6].upper()
            self.transaction_id = f"BP{timestamp}{random_suffix}"
        
        # Calculate total amount
        if self.bill_amount and not self.total_amount:
            self.total_amount = self.bill_amount + self.platform_fee
        
        super().save(*args, **kwargs)
    
    def mark_success(self, biller_ref=None, gateway_ref=None):
        """Mark payment as successful."""
        self.status = PaymentStatus.SUCCESS
        self.completed_at = timezone.now()
        if biller_ref:
            self.biller_ref_number = biller_ref
        if gateway_ref:
            self.payment_gateway_ref = gateway_ref
        self.save()
    
    def mark_failed(self, reason):
        """Mark payment as failed."""
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.completed_at = timezone.now()
        self.save()


class SavedBiller(models.Model):
    """User's saved billers for quick access."""
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_billers'
    )
    biller = models.ForeignKey(Biller, on_delete=models.CASCADE)
    consumer_number = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, blank=True)  # e.g., "Home Electricity"
    
    is_autopay_enabled = models.BooleanField(default=False)
    autopay_amount_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'saved_billers'
        verbose_name = 'Saved Biller'
        verbose_name_plural = 'Saved Billers'
        unique_together = ['user', 'biller', 'consumer_number']
    
    def __str__(self):
        return f"{self.user.username} - {self.biller.name} - {self.consumer_number}"


class BillFetchLog(models.Model):
    """Log of bill fetch attempts for debugging and audit."""
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bill_fetch_logs'
    )
    biller = models.ForeignKey(Biller, on_delete=models.SET_NULL, null=True)
    consumer_number = models.CharField(max_length=100)
    
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    is_success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bill_fetch_logs'
        verbose_name = 'Bill Fetch Log'
        verbose_name_plural = 'Bill Fetch Logs'
        ordering = ['-created_at']


# =============================================================================
# ENCRYPTION UTILITIES (reused from kyc_verification)
# =============================================================================

import hashlib
import base64
from django.conf import settings

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False


def get_encryption_key():
    """Get or generate encryption key for sensitive data."""
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    if not key:
        secret = settings.SECRET_KEY.encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return key


def encrypt_value(value):
    """Encrypt sensitive value."""
    if not value or not ENCRYPTION_AVAILABLE:
        return value
    try:
        f = Fernet(get_encryption_key())
        return f.encrypt(value.encode()).decode()
    except Exception:
        return value


def decrypt_value(encrypted_value):
    """Decrypt sensitive value."""
    if not encrypted_value or not ENCRYPTION_AVAILABLE:
        return encrypted_value
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception:
        return encrypted_value


def mask_account_number(account_number):
    """Mask bank account number: XXXXXX1234"""
    if not account_number or len(account_number) < 4:
        return "XXXXXXXXXX"
    return f"{'X' * (len(account_number) - 4)}{account_number[-4:]}"


def mask_card_number(card_number):
    """Mask card number: XXXX-XXXX-XXXX-1234"""
    if not card_number or len(card_number) < 4:
        return "XXXX-XXXX-XXXX-XXXX"
    clean = card_number.replace(' ', '').replace('-', '')
    return f"XXXX-XXXX-XXXX-{clean[-4:]}"


# =============================================================================
# USER BANK ACCOUNT MODEL
# =============================================================================

class UserBankAccount(models.Model):
    """User's saved bank accounts for payments and transfers."""
    
    ACCOUNT_TYPES = [
        ('SAVINGS', 'Savings Account'),
        ('CURRENT', 'Current Account'),
    ]
    
    VERIFICATION_STATUS = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('FAILED', 'Verification Failed'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    
    # Bank details
    account_holder_name = models.CharField(max_length=200)
    account_number_encrypted = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=11)
    bank_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='SAVINGS')
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_response = models.JSONField(default=dict, blank=True)
    
    # Settings
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    nickname = models.CharField(max_length=100, blank=True)  # e.g., "Salary Account"
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_bank_accounts'
        verbose_name = 'User Bank Account'
        verbose_name_plural = 'User Bank Accounts'
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['ifsc_code']),
        ]
    
    def __str__(self):
        return f"{self.account_holder_name} - {self.bank_name} ({self.account_number_masked})"
    
    @property
    def account_number(self):
        """Get decrypted account number."""
        return decrypt_value(self.account_number_encrypted)
    
    @account_number.setter
    def account_number(self, value):
        """Set encrypted account number."""
        if value:
            self.account_number_encrypted = encrypt_value(value)
    
    @property
    def account_number_masked(self):
        """Get masked account number for display."""
        return mask_account_number(self.account_number)
    
    def save(self, *args, **kwargs):
        # Ensure only one primary account per user
        if self.is_primary:
            UserBankAccount.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


# =============================================================================
# USER CARD MODEL
# =============================================================================

class UserCard(models.Model):
    """User's saved debit/credit cards for payments."""
    
    CARD_TYPES = [
        ('DEBIT', 'Debit Card'),
        ('CREDIT', 'Credit Card'),
        ('PREPAID', 'Prepaid Card'),
    ]
    
    CARD_NETWORKS = [
        ('VISA', 'Visa'),
        ('MASTERCARD', 'MasterCard'),
        ('RUPAY', 'RuPay'),
        ('AMEX', 'American Express'),
        ('DINERS', 'Diners Club'),
    ]
    
    VERIFICATION_STATUS = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cards'
    )
    
    # Card details (encrypted)
    card_number_encrypted = models.CharField(max_length=255)
    card_last_four = models.CharField(max_length=4)  # Last 4 digits for display
    card_holder_name = models.CharField(max_length=200)
    expiry_month = models.CharField(max_length=2)
    expiry_year = models.CharField(max_length=4)
    
    # Card info
    card_type = models.CharField(max_length=20, choices=CARD_TYPES, default='DEBIT')
    card_network = models.CharField(max_length=20, choices=CARD_NETWORKS, blank=True)
    issuing_bank = models.CharField(max_length=200, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Settings
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    nickname = models.CharField(max_length=100, blank=True)
    
    # Card validation token (from payment gateway)
    card_token = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_cards'
        verbose_name = 'User Card'
        verbose_name_plural = 'User Cards'
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['card_last_four']),
        ]
    
    def __str__(self):
        return f"{self.card_network} {self.card_type} ending {self.card_last_four}"
    
    @property
    def card_number(self):
        """Get decrypted card number."""
        return decrypt_value(self.card_number_encrypted)
    
    @card_number.setter
    def card_number(self, value):
        """Set encrypted card number and extract last 4 digits."""
        if value:
            clean = value.replace(' ', '').replace('-', '')
            self.card_number_encrypted = encrypt_value(clean)
            self.card_last_four = clean[-4:]
    
    @property
    def card_number_masked(self):
        """Get masked card number for display."""
        return f"XXXX-XXXX-XXXX-{self.card_last_four}"
    
    @property
    def expiry_display(self):
        """Get expiry date in MM/YY format."""
        return f"{self.expiry_month}/{self.expiry_year[-2:]}"
    
    @property
    def is_expired(self):
        """Check if card is expired."""
        from datetime import datetime
        current = datetime.now()
        exp_year = int(self.expiry_year)
        exp_month = int(self.expiry_month)
        if exp_year < current.year:
            return True
        if exp_year == current.year and exp_month < current.month:
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Ensure only one primary card per user
        if self.is_primary:
            UserCard.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


# =============================================================================
# USER MPIN MODEL
# =============================================================================

class UserMPIN(models.Model):
    """User's MPIN for payment authorization."""
    
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='mpin'
    )
    
    # MPIN (encrypted, 6 digits)
    mpin_hash = models.CharField(max_length=255)
    mpin_salt = models.CharField(max_length=64)
    
    # Security
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_failed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_mpin'
        verbose_name = 'User MPIN'
        verbose_name_plural = 'User MPINs'
    
    def __str__(self):
        return f"MPIN for {self.user.email}"
    
    def set_mpin(self, raw_mpin):
        """Set MPIN with salt and hash (similar to password)."""
        import secrets
        self.mpin_salt = secrets.token_hex(32)
        salted = f"{raw_mpin}{self.mpin_salt}"
        self.mpin_hash = hashlib.sha256(salted.encode()).hexdigest()
        self.failed_attempts = 0
        self.is_locked = False
        self.locked_until = None
    
    def check_mpin(self, raw_mpin):
        """Verify MPIN against stored hash."""
        salted = f"{raw_mpin}{self.mpin_salt}"
        return self.mpin_hash == hashlib.sha256(salted.encode()).hexdigest()
    
    def record_failed_attempt(self):
        """Record failed MPIN attempt with lockout logic."""
        self.failed_attempts += 1
        self.last_failed_at = timezone.now()
        
        # Lock after 3 failed attempts for 30 minutes
        if self.failed_attempts >= 3:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        
        self.save()
    
    def record_success(self):
        """Record successful MPIN verification."""
        self.failed_attempts = 0
        self.is_locked = False
        self.locked_until = None
        self.last_used_at = timezone.now()
        self.save()
    
    def is_currently_locked(self):
        """Check if MPIN is currently locked."""
        if not self.is_locked:
            return False
        if self.locked_until and timezone.now() > self.locked_until:
            # Lock expired, reset
            self.is_locked = False
            self.failed_attempts = 0
            self.locked_until = None
            self.save()
            return False
        return True


# =============================================================================
# PAYMENT GATEWAY MODEL
# =============================================================================

class PaymentGateway(models.Model):
    """Configuration for payment gateways."""
    
    GATEWAY_TYPES = [
        ('UPI', 'UPI'),
        ('CARD', 'Card Payment'),
        ('NETBANKING', 'Net Banking'),
        ('WALLET', 'Wallet'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    # Gateway info
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)  # e.g., 'RAZORPAY', 'PAYTM'
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPES)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='gateways/logos/', blank=True, null=True)
    
    # Gateway configuration (e.g., API keys - encrypted in production)
    config = models.JSONField(default=dict, blank=True)
    
    # Transaction limits
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    
    # Fee settings
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fee_type = models.CharField(
        max_length=20,
        choices=[('FIXED', 'Fixed'), ('PERCENTAGE', 'Percentage')],
        default='FIXED'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_gateways'
        verbose_name = 'Payment Gateway'
        verbose_name_plural = 'Payment Gateways'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.gateway_type})"
    
    def calculate_fee(self, amount):
        """Calculate transaction fee for given amount."""
        if self.fee_type == 'FIXED':
            return self.transaction_fee
        else:
            return (amount * self.transaction_fee) / 100


# =============================================================================
# TRANSACTION LOG MODEL
# =============================================================================

class TransactionType:
    """Transaction type choices."""
    BILL_PAYMENT = 'BILL_PAYMENT'
    MONEY_TRANSFER = 'MONEY_TRANSFER'
    WALLET_TOPUP = 'WALLET_TOPUP'
    REFUND = 'REFUND'
    REVERSAL = 'REVERSAL'
    
    CHOICES = [
        (BILL_PAYMENT, 'Bill Payment'),
        (MONEY_TRANSFER, 'Money Transfer'),
        (WALLET_TOPUP, 'Wallet Top-up'),
        (REFUND, 'Refund'),
        (REVERSAL, 'Reversal'),
    ]


class TransactionLog(models.Model):
    """Comprehensive transaction log for all payment operations."""
    
    id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=50, unique=True, editable=False)
    
    # User
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='transaction_logs'
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=30, choices=TransactionType.CHOICES)
    status = models.CharField(max_length=20, choices=PaymentStatus.CHOICES, default=PaymentStatus.INITIATED)
    
    # Amount
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    # Payment method
    payment_method = models.CharField(max_length=50, blank=True)  # UPI, CARD, NETBANKING, WALLET
    payment_gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Source account (for transfers)
    source_bank_account = models.ForeignKey(
        UserBankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outgoing_transactions'
    )
    source_card = models.ForeignKey(
        UserCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Destination (for transfers)
    destination_account_number = models.CharField(max_length=255, blank=True)  # Encrypted
    destination_ifsc = models.CharField(max_length=11, blank=True)
    destination_name = models.CharField(max_length=200, blank=True)
    
    # Reference to related records
    bill_payment = models.ForeignKey(
        BillPayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transaction_logs'
    )
    
    # Gateway references
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Description and remarks
    description = models.CharField(max_length=500, blank=True)
    remarks = models.TextField(blank=True)
    
    # Failure details
    failure_code = models.CharField(max_length=50, blank=True)
    failure_reason = models.TextField(blank=True)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_info = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'transaction_logs'
        verbose_name = 'Transaction Log'
        verbose_name_plural = 'Transaction Logs'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user', '-initiated_at']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status', '-initiated_at']),
            models.Index(fields=['payment_gateway', '-initiated_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - ₹{self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate unique transaction ID: TXN + timestamp + random
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_suffix = uuid.uuid4().hex[:6].upper()
            self.transaction_id = f"TXN{timestamp}{random_suffix}"
        
        # Calculate total if not set
        if not self.total_amount:
            self.total_amount = self.amount + self.fee
        
        super().save(*args, **kwargs)
    
    def mark_success(self, gateway_txn_id=None, gateway_response=None):
        """Mark transaction as successful."""
        self.status = PaymentStatus.SUCCESS
        self.completed_at = timezone.now()
        if gateway_txn_id:
            self.gateway_transaction_id = gateway_txn_id
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()
    
    def mark_failed(self, reason, failure_code=None):
        """Mark transaction as failed."""
        self.status = PaymentStatus.FAILED
        self.completed_at = timezone.now()
        self.failure_reason = reason
        if failure_code:
            self.failure_code = failure_code
        self.save()
    
    @classmethod
    def create_log(cls, user, transaction_type, amount, payment_method='', 
                   fee=0, description='', request=None, **kwargs):
        """Helper to create a transaction log entry."""
        log = cls(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            fee=fee,
            total_amount=amount + fee,
            payment_method=payment_method,
            description=description,
            **kwargs
        )
        if request:
            log.ip_address = request.META.get('REMOTE_ADDR')
            log.user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]
        log.save()
        return log
