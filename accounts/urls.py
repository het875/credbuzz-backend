"""
URL configuration for accounts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import AuthenticationViewSet
from accounts.views_kyc import (
    AadhaarKYCViewSet, PANKYCViewSet, BusinessKYCViewSet,
    BankKYCViewSet, KYCStatusViewSet
)
from accounts.views_user_management import (
    UserProfileViewSet, UserListViewSet, UserBlockingViewSet,
    UserRoleManagementViewSet
)
from accounts.views_audit import (
    AuditTrailViewSet, LoginActivityViewSet, KYCReportingViewSet,
    SecurityReportingViewSet
)

app_name = 'accounts'

router = DefaultRouter()

# Authentication
router.register(r'auth', AuthenticationViewSet, basename='auth')

# KYC Endpoints
router.register(r'kyc/aadhaar', AadhaarKYCViewSet, basename='aadhaar-kyc')
router.register(r'kyc/pan', PANKYCViewSet, basename='pan-kyc')
router.register(r'kyc/business', BusinessKYCViewSet, basename='business-kyc')
router.register(r'kyc/bank', BankKYCViewSet, basename='bank-kyc')
router.register(r'kyc/status', KYCStatusViewSet, basename='kyc-status')

# User Management Endpoints
router.register(r'user/profile', UserProfileViewSet, basename='user-profile')
router.register(r'admin/users', UserListViewSet, basename='admin-users')
router.register(r'admin/block', UserBlockingViewSet, basename='user-blocking')
router.register(r'admin/roles', UserRoleManagementViewSet, basename='user-roles')

# Audit and Reporting Endpoints
router.register(r'admin/audit', AuditTrailViewSet, basename='audit-trail')
router.register(r'login-activity', LoginActivityViewSet, basename='login-activity')
router.register(r'admin/reports/kyc', KYCReportingViewSet, basename='kyc-reporting')
router.register(r'admin/reports/security', SecurityReportingViewSet, basename='security-reporting')

urlpatterns = [
    path('', include(router.urls)),
]
