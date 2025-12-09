"""
Bill Pay API Views
===================
API endpoints for bill payment functionality.
"""

from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import BillCategory, Biller, BillPayment, SavedBiller, BillFetchLog, PaymentStatus
from .serializers import (
    BillCategorySerializer, BillerSerializer, BillerListSerializer,
    BillFetchRequestSerializer, BillFetchResponseSerializer,
    BillPaymentRequestSerializer, BillPaymentSerializer, BillPaymentListSerializer,
    SavedBillerSerializer, SavedBillerCreateSerializer,
    PaymentHistoryFilterSerializer
)


class BillCategoryListView(APIView):
    """
    List all active bill categories.
    
    GET /api/bills/categories/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        categories = BillCategory.objects.filter(is_active=True)
        serializer = BillCategorySerializer(categories, many=True)
        
        return Response({
            'success': True,
            'message': 'Bill categories retrieved successfully.',
            'data': {
                'categories': serializer.data
            }
        })


class BillerListView(APIView):
    """
    List billers with optional filtering by category.
    
    GET /api/bills/billers/
    GET /api/bills/billers/?category_id=1
    GET /api/bills/billers/?search=electricity
    GET /api/bills/billers/?featured=true
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        billers = Biller.objects.filter(is_active=True).select_related('category')
        
        # Filter by category
        category_id = request.query_params.get('category_id')
        if category_id:
            billers = billers.filter(category_id=category_id)
        
        # Filter by category code
        category_code = request.query_params.get('category_code')
        if category_code:
            billers = billers.filter(category__code=category_code.upper())
        
        # Search by name
        search = request.query_params.get('search')
        if search:
            billers = billers.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        # Filter featured only
        featured = request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            billers = billers.filter(is_featured=True)
        
        serializer = BillerListSerializer(billers, many=True)
        
        return Response({
            'success': True,
            'message': 'Billers retrieved successfully.',
            'data': {
                'billers': serializer.data,
                'count': len(serializer.data)
            }
        })


class BillerDetailView(APIView):
    """
    Get biller details including required fields for bill fetch.
    
    GET /api/bills/billers/<biller_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, biller_id):
        try:
            biller = Biller.objects.select_related('category').get(id=biller_id, is_active=True)
        except Biller.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Biller not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BillerSerializer(biller)
        
        return Response({
            'success': True,
            'message': 'Biller details retrieved successfully.',
            'data': {
                'biller': serializer.data
            }
        })


class FeaturedBillersView(APIView):
    """
    List featured billers across all categories.
    
    GET /api/bills/featured/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        billers = Biller.objects.filter(
            is_active=True, 
            is_featured=True
        ).select_related('category')[:10]
        
        serializer = BillerListSerializer(billers, many=True)
        
        return Response({
            'success': True,
            'message': 'Featured billers retrieved successfully.',
            'data': {
                'billers': serializer.data
            }
        })


class BillFetchView(APIView):
    """
    Fetch bill details from biller.
    
    POST /api/bills/fetch/
    {
        "biller_id": 1,
        "consumer_number": "123456789",
        "additional_fields": {}
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = BillFetchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        biller_id = serializer.validated_data['biller_id']
        consumer_number = serializer.validated_data['consumer_number']
        additional_fields = serializer.validated_data.get('additional_fields', {})
        
        try:
            biller = Biller.objects.get(id=biller_id, is_active=True)
        except Biller.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Biller not found or inactive.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # In production, this would call the actual biller API
        # For now, return mock bill data
        bill_data = {
            'consumer_number': consumer_number,
            'consumer_name': 'John Doe',
            'bill_amount': Decimal('1234.56'),
            'bill_date': '2025-01-01',
            'due_date': '2025-01-15',
            'bill_number': f'BILL{consumer_number[:6]}',
            'bill_period': 'Dec 2024',
            'biller_name': biller.name,
            'platform_fee': biller.calculate_fee(Decimal('1234.56')),
        }
        
        # Log the fetch attempt
        BillFetchLog.objects.create(
            user=request.user,
            biller=biller,
            consumer_number=consumer_number,
            request_data={'additional_fields': additional_fields},
            response_data=bill_data,
            is_success=True
        )
        
        # Convert Decimal to string for JSON serialization
        bill_data['bill_amount'] = str(bill_data['bill_amount'])
        bill_data['platform_fee'] = str(bill_data['platform_fee'])
        
        return Response({
            'success': True,
            'message': 'Bill fetched successfully.',
            'data': {
                'bill': bill_data
            }
        })


class BillPaymentView(APIView):
    """
    Initiate bill payment.
    
    POST /api/bills/pay/
    {
        "biller_id": 1,
        "consumer_number": "123456789",
        "bill_amount": 1234.56,
        "consumer_name": "John Doe",
        "payment_method": "WALLET"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = BillPaymentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        biller_id = serializer.validated_data['biller_id']
        
        try:
            biller = Biller.objects.get(id=biller_id, is_active=True)
        except Biller.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Biller not found or inactive.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        bill_amount = serializer.validated_data['bill_amount']
        
        # Validate amount limits
        if bill_amount < biller.min_amount:
            return Response({
                'success': False,
                'message': f'Amount must be at least ₹{biller.min_amount}.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if bill_amount > biller.max_amount:
            return Response({
                'success': False,
                'message': f'Amount cannot exceed ₹{biller.max_amount}.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate platform fee
        platform_fee = biller.calculate_fee(bill_amount)
        total_amount = bill_amount + platform_fee
        
        # Create payment record
        payment = BillPayment.objects.create(
            user=request.user,
            biller=biller,
            consumer_number=serializer.validated_data['consumer_number'],
            consumer_name=serializer.validated_data.get('consumer_name', ''),
            bill_amount=bill_amount,
            platform_fee=platform_fee,
            total_amount=total_amount,
            payment_method=serializer.validated_data.get('payment_method', 'WALLET'),
            status=PaymentStatus.PENDING
        )
        
        # In production, this would initiate actual payment processing
        # For now, mark as success
        payment.mark_success(
            biller_ref=f'BLR{payment.transaction_id}',
            gateway_ref=f'GW{payment.transaction_id}'
        )
        
        return Response({
            'success': True,
            'message': 'Bill payment successful.',
            'data': {
                'payment': BillPaymentSerializer(payment).data
            }
        }, status=status.HTTP_201_CREATED)


class PaymentHistoryView(APIView):
    """
    Get user's payment history with filters.
    
    GET /api/bills/history/
    GET /api/bills/history/?status=SUCCESS
    GET /api/bills/history/?category_id=1
    GET /api/bills/history/?start_date=2025-01-01&end_date=2025-01-31
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payments = BillPayment.objects.filter(user=request.user).select_related('biller', 'biller__category')
        
        # Apply filters
        filter_serializer = PaymentHistoryFilterSerializer(data=request.query_params)
        if filter_serializer.is_valid():
            data = filter_serializer.validated_data
            
            if 'status' in data:
                payments = payments.filter(status=data['status'])
            
            if 'category_id' in data:
                payments = payments.filter(biller__category_id=data['category_id'])
            
            if 'biller_id' in data:
                payments = payments.filter(biller_id=data['biller_id'])
            
            if 'start_date' in data:
                payments = payments.filter(initiated_at__date__gte=data['start_date'])
            
            if 'end_date' in data:
                payments = payments.filter(initiated_at__date__lte=data['end_date'])
            
            # Pagination
            page = data.get('page', 1)
            page_size = data.get('page_size', 20)
            start = (page - 1) * page_size
            end = start + page_size
            
            total_count = payments.count()
            payments = payments[start:end]
            
            serializer = BillPaymentListSerializer(payments, many=True)
            
            return Response({
                'success': True,
                'message': 'Payment history retrieved successfully.',
                'data': {
                    'payments': serializer.data,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_count': total_count,
                        'total_pages': (total_count + page_size - 1) // page_size
                    }
                }
            })
        
        # Default without filters
        serializer = BillPaymentListSerializer(payments[:20], many=True)
        
        return Response({
            'success': True,
            'message': 'Payment history retrieved successfully.',
            'data': {
                'payments': serializer.data
            }
        })


class PaymentDetailView(APIView):
    """
    Get details of a specific payment.
    
    GET /api/bills/payments/<transaction_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, transaction_id):
        try:
            payment = BillPayment.objects.select_related('biller', 'biller__category').get(
                transaction_id=transaction_id,
                user=request.user
            )
        except BillPayment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Payment not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BillPaymentSerializer(payment)
        
        return Response({
            'success': True,
            'message': 'Payment details retrieved successfully.',
            'data': {
                'payment': serializer.data
            }
        })


class RecentPaymentsView(APIView):
    """
    Get user's recent payments (last 5).
    
    GET /api/bills/recent/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payments = BillPayment.objects.filter(
            user=request.user
        ).select_related('biller', 'biller__category')[:5]
        
        serializer = BillPaymentListSerializer(payments, many=True)
        
        return Response({
            'success': True,
            'message': 'Recent payments retrieved successfully.',
            'data': {
                'payments': serializer.data
            }
        })


class SavedBillerListView(APIView):
    """
    List user's saved billers.
    
    GET /api/bills/saved/
    POST /api/bills/saved/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        saved_billers = SavedBiller.objects.filter(user=request.user).select_related('biller', 'biller__category')
        serializer = SavedBillerSerializer(saved_billers, many=True)
        
        return Response({
            'success': True,
            'message': 'Saved billers retrieved successfully.',
            'data': {
                'saved_billers': serializer.data
            }
        })
    
    def post(self, request):
        serializer = SavedBillerCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        saved_biller = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Biller saved successfully.',
            'data': {
                'saved_biller': SavedBillerSerializer(saved_biller).data
            }
        }, status=status.HTTP_201_CREATED)


class SavedBillerDetailView(APIView):
    """
    Manage a saved biller.
    
    GET /api/bills/saved/<id>/
    PUT /api/bills/saved/<id>/
    DELETE /api/bills/saved/<id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        try:
            return SavedBiller.objects.select_related('biller', 'biller__category').get(id=pk, user=user)
        except SavedBiller.DoesNotExist:
            return None
    
    def get(self, request, pk):
        saved_biller = self.get_object(pk, request.user)
        if not saved_biller:
            return Response({
                'success': False,
                'message': 'Saved biller not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SavedBillerSerializer(saved_biller)
        
        return Response({
            'success': True,
            'message': 'Saved biller retrieved successfully.',
            'data': {
                'saved_biller': serializer.data
            }
        })
    
    def put(self, request, pk):
        saved_biller = self.get_object(pk, request.user)
        if not saved_biller:
            return Response({
                'success': False,
                'message': 'Saved biller not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow updating nickname and autopay settings
        saved_biller.nickname = request.data.get('nickname', saved_biller.nickname)
        saved_biller.is_autopay_enabled = request.data.get('is_autopay_enabled', saved_biller.is_autopay_enabled)
        saved_biller.autopay_amount_limit = request.data.get('autopay_amount_limit', saved_biller.autopay_amount_limit)
        saved_biller.save()
        
        serializer = SavedBillerSerializer(saved_biller)
        
        return Response({
            'success': True,
            'message': 'Saved biller updated successfully.',
            'data': {
                'saved_biller': serializer.data
            }
        })
    
    def delete(self, request, pk):
        saved_biller = self.get_object(pk, request.user)
        if not saved_biller:
            return Response({
                'success': False,
                'message': 'Saved biller not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        saved_biller.delete()
        
        return Response({
            'success': True,
            'message': 'Saved biller deleted successfully.'
        })