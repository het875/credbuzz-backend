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
        "additional_params": {}
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
        additional_params = serializer.validated_data.get('additional_params', {})
        
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
            request_data={'additional_params': additional_params},
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
        "amount": 1234.56,
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
        
        bill_amount = serializer.validated_data['amount']
        
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


# =============================================================================
# BANK ACCOUNT VIEWS
# =============================================================================

from .models import UserBankAccount, UserCard, UserMPIN, PaymentGateway, TransactionLog, TransactionType
from .serializers import (
    UserBankAccountSerializer, UserBankAccountCreateSerializer, UserBankAccountUpdateSerializer,
    UserCardSerializer, UserCardCreateSerializer, UserCardUpdateSerializer,
    MPINSetupSerializer, MPINVerifySerializer, MPINChangeSerializer,
    PaymentGatewaySerializer,
    TransactionLogSerializer, TransactionLogDetailSerializer,
    IFSCVerifySerializer, IFSCResponseSerializer,
    MoneyTransferSerializer
)


class BankAccountListView(APIView):
    """
    List and add user bank accounts.
    
    GET /api/bills/bank-accounts/
    POST /api/bills/bank-accounts/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        accounts = UserBankAccount.objects.filter(user=request.user, is_active=True)
        serializer = UserBankAccountSerializer(accounts, many=True)
        
        return Response({
            'success': True,
            'message': 'Bank accounts retrieved successfully.',
            'data': {
                'bank_accounts': serializer.data,
                'count': len(serializer.data)
            }
        })
    
    def post(self, request):
        serializer = UserBankAccountCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        account = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Bank account added successfully.',
            'data': {
                'bank_account': UserBankAccountSerializer(account).data
            }
        }, status=status.HTTP_201_CREATED)


class BankAccountDetailView(APIView):
    """
    Manage a specific bank account.
    
    GET /api/bills/bank-accounts/<id>/
    PUT /api/bills/bank-accounts/<id>/
    DELETE /api/bills/bank-accounts/<id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        try:
            return UserBankAccount.objects.get(id=pk, user=user, is_active=True)
        except UserBankAccount.DoesNotExist:
            return None
    
    def get(self, request, pk):
        account = self.get_object(pk, request.user)
        if not account:
            return Response({
                'success': False,
                'message': 'Bank account not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserBankAccountSerializer(account)
        
        return Response({
            'success': True,
            'message': 'Bank account retrieved successfully.',
            'data': {
                'bank_account': serializer.data
            }
        })
    
    def put(self, request, pk):
        account = self.get_object(pk, request.user)
        if not account:
            return Response({
                'success': False,
                'message': 'Bank account not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserBankAccountUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update allowed fields
        if 'nickname' in serializer.validated_data:
            account.nickname = serializer.validated_data['nickname']
        if 'is_primary' in serializer.validated_data:
            account.is_primary = serializer.validated_data['is_primary']
        if 'is_active' in serializer.validated_data:
            account.is_active = serializer.validated_data['is_active']
        
        account.save()
        
        return Response({
            'success': True,
            'message': 'Bank account updated successfully.',
            'data': {
                'bank_account': UserBankAccountSerializer(account).data
            }
        })
    
    def delete(self, request, pk):
        account = self.get_object(pk, request.user)
        if not account:
            return Response({
                'success': False,
                'message': 'Bank account not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Soft delete
        account.is_active = False
        account.save()
        
        return Response({
            'success': True,
            'message': 'Bank account deleted successfully.'
        })


class BankAccountVerifyView(APIView):
    """
    Verify a bank account (mock implementation).
    
    POST /api/bills/bank-accounts/<id>/verify/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            account = UserBankAccount.objects.get(id=pk, user=request.user, is_active=True)
        except UserBankAccount.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Bank account not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if account.is_verified:
            return Response({
                'success': False,
                'message': 'Bank account is already verified.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mock verification - In production, this would call a bank verification API
        # Simulate verification success
        account.is_verified = True
        account.verification_status = 'VERIFIED'
        account.verified_at = timezone.now()
        account.verification_response = {
            'verified': True,
            'verified_at': timezone.now().isoformat(),
            'method': 'PENNY_DROP'
        }
        account.save()
        
        return Response({
            'success': True,
            'message': 'Bank account verified successfully.',
            'data': {
                'bank_account': UserBankAccountSerializer(account).data
            }
        })


# =============================================================================
# CARD VIEWS
# =============================================================================

class CardListView(APIView):
    """
    List and add user cards.
    
    GET /api/bills/cards/
    POST /api/bills/cards/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        cards = UserCard.objects.filter(user=request.user, is_active=True)
        serializer = UserCardSerializer(cards, many=True)
        
        return Response({
            'success': True,
            'message': 'Cards retrieved successfully.',
            'data': {
                'cards': serializer.data,
                'count': len(serializer.data)
            }
        })
    
    def post(self, request):
        serializer = UserCardCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        card = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Card added successfully.',
            'data': {
                'card': UserCardSerializer(card).data
            }
        }, status=status.HTTP_201_CREATED)


class CardDetailView(APIView):
    """
    Manage a specific card.
    
    GET /api/bills/cards/<id>/
    PUT /api/bills/cards/<id>/
    DELETE /api/bills/cards/<id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        try:
            return UserCard.objects.get(id=pk, user=user, is_active=True)
        except UserCard.DoesNotExist:
            return None
    
    def get(self, request, pk):
        card = self.get_object(pk, request.user)
        if not card:
            return Response({
                'success': False,
                'message': 'Card not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserCardSerializer(card)
        
        return Response({
            'success': True,
            'message': 'Card retrieved successfully.',
            'data': {
                'card': serializer.data
            }
        })
    
    def put(self, request, pk):
        card = self.get_object(pk, request.user)
        if not card:
            return Response({
                'success': False,
                'message': 'Card not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserCardUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update allowed fields
        if 'nickname' in serializer.validated_data:
            card.nickname = serializer.validated_data['nickname']
        if 'is_primary' in serializer.validated_data:
            card.is_primary = serializer.validated_data['is_primary']
        if 'is_active' in serializer.validated_data:
            card.is_active = serializer.validated_data['is_active']
        
        card.save()
        
        return Response({
            'success': True,
            'message': 'Card updated successfully.',
            'data': {
                'card': UserCardSerializer(card).data
            }
        })
    
    def delete(self, request, pk):
        card = self.get_object(pk, request.user)
        if not card:
            return Response({
                'success': False,
                'message': 'Card not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Soft delete
        card.is_active = False
        card.save()
        
        return Response({
            'success': True,
            'message': 'Card deleted successfully.'
        })


# =============================================================================
# MPIN VIEWS
# =============================================================================

class MPINSetupView(APIView):
    """
    Set up MPIN for payment authorization.
    
    POST /api/bills/mpin/setup/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Check if MPIN is already set
        has_mpin = UserMPIN.objects.filter(user=request.user).exists()
        
        return Response({
            'success': True,
            'data': {
                'has_mpin': has_mpin
            }
        })
    
    def post(self, request):
        # Check if MPIN already exists
        if UserMPIN.objects.filter(user=request.user).exists():
            return Response({
                'success': False,
                'message': 'MPIN is already set. Use change MPIN to update.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = MPINSetupSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create MPIN
        mpin = UserMPIN(user=request.user)
        mpin.set_mpin(serializer.validated_data['mpin'])
        mpin.save()
        
        return Response({
            'success': True,
            'message': 'MPIN set up successfully.',
            'data': {
                'has_mpin': True
            }
        }, status=status.HTTP_201_CREATED)


class MPINVerifyView(APIView):
    """
    Verify MPIN for payment authorization.
    
    POST /api/bills/mpin/verify/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            mpin = UserMPIN.objects.get(user=request.user)
        except UserMPIN.DoesNotExist:
            return Response({
                'success': False,
                'message': 'MPIN is not set. Please set up MPIN first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if locked
        if mpin.is_currently_locked():
            minutes_remaining = 0
            if mpin.locked_until:
                minutes_remaining = int((mpin.locked_until - timezone.now()).total_seconds() / 60) + 1
            
            return Response({
                'success': False,
                'message': f'MPIN is locked due to too many failed attempts. Try again in {minutes_remaining} minutes.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = MPINVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify MPIN
        if mpin.check_mpin(serializer.validated_data['mpin']):
            mpin.record_success()
            return Response({
                'success': True,
                'message': 'MPIN verified successfully.',
                'data': {
                    'verified': True
                }
            })
        else:
            mpin.record_failed_attempt()
            remaining_attempts = max(0, 3 - mpin.failed_attempts)
            
            return Response({
                'success': False,
                'message': f'Invalid MPIN. {remaining_attempts} attempts remaining.',
                'data': {
                    'verified': False,
                    'remaining_attempts': remaining_attempts
                }
            }, status=status.HTTP_401_UNAUTHORIZED)


class MPINChangeView(APIView):
    """
    Change MPIN.
    
    POST /api/bills/mpin/change/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            mpin = UserMPIN.objects.get(user=request.user)
        except UserMPIN.DoesNotExist:
            return Response({
                'success': False,
                'message': 'MPIN is not set. Please set up MPIN first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if locked
        if mpin.is_currently_locked():
            return Response({
                'success': False,
                'message': 'MPIN is locked due to too many failed attempts.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = MPINChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify current MPIN
        if not mpin.check_mpin(serializer.validated_data['current_mpin']):
            mpin.record_failed_attempt()
            return Response({
                'success': False,
                'message': 'Current MPIN is incorrect.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Set new MPIN
        mpin.set_mpin(serializer.validated_data['new_mpin'])
        mpin.save()
        
        return Response({
            'success': True,
            'message': 'MPIN changed successfully.'
        })


# =============================================================================
# PAYMENT GATEWAY VIEWS
# =============================================================================

class PaymentGatewayListView(APIView):
    """
    List available payment gateways.
    
    GET /api/bills/gateways/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        gateways = PaymentGateway.objects.filter(is_active=True)
        
        # Optional filter by gateway type
        gateway_type = request.query_params.get('type')
        if gateway_type:
            gateways = gateways.filter(gateway_type=gateway_type.upper())
        
        serializer = PaymentGatewaySerializer(gateways, many=True)
        
        return Response({
            'success': True,
            'message': 'Payment gateways retrieved successfully.',
            'data': {
                'gateways': serializer.data
            }
        })


# =============================================================================
# IFSC VERIFICATION VIEW
# =============================================================================

class IFSCVerifyView(APIView):
    """
    Verify IFSC code and get bank details.
    
    GET /api/bills/ifsc/<ifsc_code>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, ifsc_code):
        # Validate IFSC format
        import re
        ifsc_code = ifsc_code.upper()
        if not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc_code):
            return Response({
                'success': False,
                'message': 'Invalid IFSC code format. Expected: ABCD0XXXXXX'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mock IFSC data - In production, this would call an IFSC verification API
        # Using first 4 characters as bank code
        bank_codes = {
            'SBIN': {'bank': 'State Bank of India', 'city': 'Mumbai'},
            'HDFC': {'bank': 'HDFC Bank', 'city': 'Mumbai'},
            'ICIC': {'bank': 'ICICI Bank', 'city': 'Mumbai'},
            'KKBK': {'bank': 'Kotak Mahindra Bank', 'city': 'Mumbai'},
            'UTIB': {'bank': 'Axis Bank', 'city': 'Mumbai'},
            'PUNB': {'bank': 'Punjab National Bank', 'city': 'Delhi'},
            'BARB': {'bank': 'Bank of Baroda', 'city': 'Vadodara'},
            'CNRB': {'bank': 'Canara Bank', 'city': 'Bangalore'},
            'UBIN': {'bank': 'Union Bank of India', 'city': 'Mumbai'},
            'IOBA': {'bank': 'Indian Overseas Bank', 'city': 'Chennai'},
        }
        
        bank_code = ifsc_code[:4]
        bank_info = bank_codes.get(bank_code, {'bank': 'Unknown Bank', 'city': 'Unknown'})
        
        ifsc_data = {
            'ifsc_code': ifsc_code,
            'bank_name': bank_info['bank'],
            'branch_name': f'{bank_info["city"]} Branch',
            'address': f'{bank_info["city"]}, India',
            'city': bank_info['city'],
            'state': 'Maharashtra' if bank_info['city'] == 'Mumbai' else 'India',
            'contact': '+91-1800-XXX-XXXX'
        }
        
        return Response({
            'success': True,
            'message': 'IFSC code verified successfully.',
            'data': ifsc_data
        })


# =============================================================================
# TRANSACTION LOG VIEWS
# =============================================================================

class TransactionLogListView(APIView):
    """
    List user's transaction logs.
    
    GET /api/bills/transactions/
    GET /api/bills/transactions/?type=BILL_PAYMENT
    GET /api/bills/transactions/?status=SUCCESS
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        transactions = TransactionLog.objects.filter(user=request.user)
        
        # Filter by transaction type
        txn_type = request.query_params.get('type')
        if txn_type:
            transactions = transactions.filter(transaction_type=txn_type.upper())
        
        # Filter by status
        txn_status = request.query_params.get('status')
        if txn_status:
            transactions = transactions.filter(status=txn_status.upper())
        
        # Filter by date range
        start_date = request.query_params.get('start_date')
        if start_date:
            transactions = transactions.filter(initiated_at__date__gte=start_date)
        
        end_date = request.query_params.get('end_date')
        if end_date:
            transactions = transactions.filter(initiated_at__date__lte=end_date)
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        page_size = min(page_size, 100)  # Max 100 per page
        
        total_count = transactions.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        transactions = transactions[start:end]
        serializer = TransactionLogSerializer(transactions, many=True)
        
        return Response({
            'success': True,
            'message': 'Transaction logs retrieved successfully.',
            'data': {
                'transactions': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        })


class TransactionLogDetailView(APIView):
    """
    Get details of a specific transaction.
    
    GET /api/bills/transactions/<transaction_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, transaction_id):
        try:
            transaction = TransactionLog.objects.get(
                transaction_id=transaction_id,
                user=request.user
            )
        except TransactionLog.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Transaction not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TransactionLogDetailSerializer(transaction)
        
        return Response({
            'success': True,
            'message': 'Transaction details retrieved successfully.',
            'data': {
                'transaction': serializer.data
            }
        })


# =============================================================================
# MONEY TRANSFER VIEW
# =============================================================================

class MoneyTransferView(APIView):
    """
    Transfer money to another bank account.
    
    POST /api/bills/transfer/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = MoneyTransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get source bank account
        try:
            source_account = UserBankAccount.objects.get(
                id=serializer.validated_data['source_bank_account_id'],
                user=request.user,
                is_active=True
            )
        except UserBankAccount.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Source bank account not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not source_account.is_verified:
            return Response({
                'success': False,
                'message': 'Source bank account must be verified before making transfers.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify MPIN
        try:
            mpin = UserMPIN.objects.get(user=request.user)
        except UserMPIN.DoesNotExist:
            return Response({
                'success': False,
                'message': 'MPIN is not set. Please set up MPIN first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if mpin.is_currently_locked():
            return Response({
                'success': False,
                'message': 'MPIN is locked due to too many failed attempts.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        if not mpin.check_mpin(serializer.validated_data['mpin']):
            mpin.record_failed_attempt()
            return Response({
                'success': False,
                'message': 'Invalid MPIN.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        mpin.record_success()
        
        # Create transaction log
        from .models import encrypt_value
        transaction = TransactionLog.create_log(
            user=request.user,
            transaction_type=TransactionType.MONEY_TRANSFER,
            amount=serializer.validated_data['amount'],
            payment_method='NEFT',
            description=f"Transfer to {serializer.validated_data['beneficiary_name']}",
            source_bank_account=source_account,
            destination_account_number=encrypt_value(serializer.validated_data['beneficiary_account_number']),
            destination_ifsc=serializer.validated_data['beneficiary_ifsc'].upper(),
            destination_name=serializer.validated_data['beneficiary_name'],
            remarks=serializer.validated_data.get('remarks', ''),
            request=request
        )
        
        # In production, this would initiate actual bank transfer via payment gateway
        # For now, simulate success
        transaction.mark_success(
            gateway_txn_id=f'NEFT{transaction.transaction_id}',
            gateway_response={
                'status': 'SUCCESS',
                'reference_number': f'NEFT{transaction.transaction_id}',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        return Response({
            'success': True,
            'message': 'Money transfer initiated successfully.',
            'data': {
                'transaction': TransactionLogSerializer(transaction).data
            }
        }, status=status.HTTP_201_CREATED)