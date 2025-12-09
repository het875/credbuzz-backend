"""
Bill Pay Serializers
=====================
Serializers for bill payment APIs.
"""

from rest_framework import serializers
from .models import BillCategory, Biller, BillPayment, SavedBiller, PaymentStatus


class BillCategorySerializer(serializers.ModelSerializer):
    """Serializer for bill categories."""
    
    billers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BillCategory
        fields = ['id', 'name', 'code', 'description', 'icon', 'is_active', 'display_order', 'billers_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_billers_count(self, obj):
        return obj.billers.filter(is_active=True).count()


class BillerSerializer(serializers.ModelSerializer):
    """Serializer for billers."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    
    class Meta:
        model = Biller
        fields = [
            'id', 'category', 'category_name', 'category_code',
            'name', 'code', 'description', 'logo',
            'min_amount', 'max_amount', 'required_fields',
            'platform_fee', 'platform_fee_type',
            'is_active', 'is_featured'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BillerListSerializer(serializers.ModelSerializer):
    """Simplified serializer for biller lists."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Biller
        fields = ['id', 'name', 'code', 'logo', 'category_name', 'is_featured']


class BillFetchRequestSerializer(serializers.Serializer):
    """Serializer for bill fetch request."""
    
    biller_id = serializers.IntegerField()
    consumer_number = serializers.CharField(max_length=100)
    # Additional fields can be passed dynamically based on biller requirements
    additional_params = serializers.JSONField(required=False, default=dict)


class BillFetchResponseSerializer(serializers.Serializer):
    """Serializer for bill fetch response."""
    
    consumer_number = serializers.CharField()
    consumer_name = serializers.CharField()
    bill_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    bill_date = serializers.DateField(allow_null=True)
    due_date = serializers.DateField(allow_null=True)
    bill_number = serializers.CharField(allow_blank=True)
    bill_period = serializers.CharField(allow_blank=True)
    additional_info = serializers.JSONField(default=dict)
    
    # Fee calculation
    platform_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class BillPaymentRequestSerializer(serializers.Serializer):
    """Serializer for bill payment request."""
    
    biller_id = serializers.IntegerField()
    consumer_number = serializers.CharField(max_length=100)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=['WALLET', 'UPI', 'CARD', 'NETBANKING'])
    
    # Optional fields from bill fetch
    consumer_name = serializers.CharField(max_length=200, required=False)
    bill_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=False)
    bill_number = serializers.CharField(max_length=100, required=False)
    bill_period = serializers.CharField(max_length=100, required=False)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


class BillPaymentSerializer(serializers.ModelSerializer):
    """Serializer for bill payment records."""
    
    biller_name = serializers.CharField(source='biller.name', read_only=True)
    biller_code = serializers.CharField(source='biller.code', read_only=True)
    category_name = serializers.CharField(source='biller.category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BillPayment
        fields = [
            'id', 'transaction_id',
            'biller', 'biller_name', 'biller_code', 'category_name',
            'consumer_number', 'consumer_name',
            'bill_amount', 'platform_fee', 'total_amount',
            'bill_date', 'due_date', 'bill_number', 'bill_period',
            'status', 'status_display',
            'payment_method', 'biller_ref_number',
            'initiated_at', 'completed_at',
            'failure_reason'
        ]
        read_only_fields = ['id', 'transaction_id', 'initiated_at', 'completed_at']


class BillPaymentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for payment list."""
    
    biller_name = serializers.CharField(source='biller.name', read_only=True)
    category_name = serializers.CharField(source='biller.category.name', read_only=True)
    
    class Meta:
        model = BillPayment
        fields = [
            'id', 'transaction_id', 'biller_name', 'category_name',
            'consumer_number', 'total_amount', 'status',
            'initiated_at', 'completed_at'
        ]


class SavedBillerSerializer(serializers.ModelSerializer):
    """Serializer for saved billers."""
    
    biller_name = serializers.CharField(source='biller.name', read_only=True)
    biller_code = serializers.CharField(source='biller.code', read_only=True)
    category_name = serializers.CharField(source='biller.category.name', read_only=True)
    biller_logo = serializers.ImageField(source='biller.logo', read_only=True)
    
    class Meta:
        model = SavedBiller
        fields = [
            'id', 'biller', 'biller_name', 'biller_code', 'category_name', 'biller_logo',
            'consumer_number', 'nickname',
            'is_autopay_enabled', 'autopay_amount_limit',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SavedBillerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating saved billers."""
    
    class Meta:
        model = SavedBiller
        fields = ['biller', 'consumer_number', 'nickname', 'is_autopay_enabled', 'autopay_amount_limit']
    
    def validate(self, attrs):
        user = self.context['request'].user
        biller = attrs.get('biller')
        consumer_number = attrs.get('consumer_number')
        
        # Check for duplicate
        if SavedBiller.objects.filter(user=user, biller=biller, consumer_number=consumer_number).exists():
            raise serializers.ValidationError("This biller is already saved with this consumer number.")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentHistoryFilterSerializer(serializers.Serializer):
    """Serializer for payment history filters."""
    
    status = serializers.ChoiceField(choices=PaymentStatus.CHOICES, required=False)
    category_id = serializers.IntegerField(required=False)
    biller_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
