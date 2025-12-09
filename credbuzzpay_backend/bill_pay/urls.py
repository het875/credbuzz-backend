"""
Bill Pay URL Configuration
===========================
API endpoints for bill payment functionality.
"""

from django.urls import path
from .views import (
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
]
