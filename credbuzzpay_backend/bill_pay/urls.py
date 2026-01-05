"""
Bill Pay URL Configuration
===========================
API endpoints for bill payment functionality.
"""

from django.urls import path
from .views import (
    # Existing views
    BillCategoryListView,
    BillerListView,
    BillerDetailView,
    BillFetchView,
    BillPaymentView,
    PaymentHistoryView,
    PaymentDetailView,
    SavedBillerListView,
    SavedBillerDetailView,
    FeaturedBillersView,
    RecentPaymentsView,
    # New views
    BankAccountListView,
    BankAccountDetailView,
    BankAccountVerifyView,
    CardListView,
    CardDetailView,
    MPINSetupView,
    MPINVerifyView,
    MPINChangeView,
    PaymentGatewayListView,
    IFSCVerifyView,
    TransactionLogListView,
    TransactionLogDetailView,
    MoneyTransferView,
)

app_name = 'bill_pay'

urlpatterns = [
    # Categories
    path('categories/', BillCategoryListView.as_view(), name='category-list'),
    
    # Billers
    path('billers/', BillerListView.as_view(), name='biller-list'),
    path('billers/<int:biller_id>/', BillerDetailView.as_view(), name='biller-detail'),
    path('featured/', FeaturedBillersView.as_view(), name='featured-billers'),
    
    # Bill Fetch & Payment
    path('fetch/', BillFetchView.as_view(), name='bill-fetch'),
    path('pay/', BillPaymentView.as_view(), name='bill-pay'),
    
    # Payment History
    path('history/', PaymentHistoryView.as_view(), name='payment-history'),
    path('payments/<str:transaction_id>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('recent/', RecentPaymentsView.as_view(), name='recent-payments'),
    
    # Saved Billers
    path('saved/', SavedBillerListView.as_view(), name='saved-biller-list'),
    path('saved/<int:pk>/', SavedBillerDetailView.as_view(), name='saved-biller-detail'),
    
    # Bank Accounts
    path('bank-accounts/', BankAccountListView.as_view(), name='bank-account-list'),
    path('bank-accounts/<int:pk>/', BankAccountDetailView.as_view(), name='bank-account-detail'),
    path('bank-accounts/<int:pk>/verify/', BankAccountVerifyView.as_view(), name='bank-account-verify'),
    
    # Cards
    path('cards/', CardListView.as_view(), name='card-list'),
    path('cards/<int:pk>/', CardDetailView.as_view(), name='card-detail'),
    
    # MPIN
    path('mpin/setup/', MPINSetupView.as_view(), name='mpin-setup'),
    path('mpin/verify/', MPINVerifyView.as_view(), name='mpin-verify'),
    path('mpin/change/', MPINChangeView.as_view(), name='mpin-change'),
    
    # Payment Gateways
    path('gateways/', PaymentGatewayListView.as_view(), name='gateway-list'),
    
    # IFSC Verification
    path('ifsc/<str:ifsc_code>/', IFSCVerifyView.as_view(), name='ifsc-verify'),
    
    # Transaction Logs
    path('transactions/', TransactionLogListView.as_view(), name='transaction-list'),
    path('transactions/<str:transaction_id>/', TransactionLogDetailView.as_view(), name='transaction-detail'),
    
    # Money Transfer
    path('transfer/', MoneyTransferView.as_view(), name='money-transfer'),
]

