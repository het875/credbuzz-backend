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
