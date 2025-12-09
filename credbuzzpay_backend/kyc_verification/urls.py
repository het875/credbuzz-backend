"""
KYC Verification URL Configuration
====================================
URL patterns for KYC/Onboarding API endpoints.

OTP Endpoints (in users_auth):
    /api/auth/send-otp/          - Send OTP
    /api/auth/verify-otp/        - Verify OTP
    /api/auth/resend-otp/        - Resend OTP

KYC User Endpoints:
    /api/kyc/status/             - Get KYC status
    /api/kyc/start/              - Start KYC process
    /api/kyc/detail/             - Get full KYC details
    /api/kyc/submit/             - Submit KYC for review

Identity Proof:
    /api/kyc/identity/aadhaar/           - Submit Aadhaar details
    /api/kyc/identity/aadhaar/upload/    - Upload Aadhaar images
    /api/kyc/identity/pan/               - Submit PAN details
    /api/kyc/identity/pan/upload/        - Upload PAN image

Business Details:
    /api/kyc/business/           - Submit/Get business details

Verification Images:
    /api/kyc/verification/                  - Get verification images status
    /api/kyc/verification/selfie/           - Upload selfie
    /api/kyc/verification/office/           - Upload office photos
    /api/kyc/verification/address-proof/    - Upload address proof

Bank Details:
    /api/kyc/bank/               - Submit/Get bank details

Admin Endpoints:
    /api/kyc/admin/applications/                          - List all applications
    /api/kyc/admin/applications/<id>/                     - Get application details
    /api/kyc/admin/applications/<id>/start-review/        - Start review
    /api/kyc/admin/applications/<id>/review/              - Approve/Reject/Request resubmit
"""

from django.urls import path
from . import views

app_name = 'kyc_verification'

# OTP URL patterns (to be included in users_auth urls)
otp_urlpatterns = [
    path('send-otp/', views.OTPSendView.as_view(), name='send-otp'),
    path('verify-otp/', views.OTPVerifyView.as_view(), name='verify-otp'),
    path('resend-otp/', views.OTPResendView.as_view(), name='resend-otp'),
]

# KYC URL patterns
urlpatterns = [
    # KYC Status & Start
    path('status/', views.KYCStatusView.as_view(), name='kyc-status'),
    path('start/', views.KYCStartView.as_view(), name='kyc-start'),
    path('detail/', views.KYCDetailView.as_view(), name='kyc-detail'),
    path('submit/', views.KYCSubmitView.as_view(), name='kyc-submit'),
    
    # Identity Proof - Aadhaar
    path('identity/aadhaar/', views.AadhaarDetailsView.as_view(), name='aadhaar-details'),
    path('identity/aadhaar/upload/', views.AadhaarUploadView.as_view(), name='aadhaar-upload'),
    
    # Identity Proof - PAN
    path('identity/pan/', views.PANDetailsView.as_view(), name='pan-details'),
    path('identity/pan/upload/', views.PANUploadView.as_view(), name='pan-upload'),
    
    # Business Details
    path('business/', views.BusinessDetailsView.as_view(), name='business-details'),
    
    # Verification Images
    path('verification/', views.VerificationImagesView.as_view(), name='verification-images'),
    path('verification/selfie/', views.SelfieUploadView.as_view(), name='selfie-upload'),
    path('verification/office/', views.OfficePhotosUploadView.as_view(), name='office-upload'),
    path('verification/address-proof/', views.AddressProofUploadView.as_view(), name='address-proof-upload'),
    
    # Bank Details
    path('bank/', views.BankDetailsView.as_view(), name='bank-details'),
    
    # Admin Endpoints
    path('admin/applications/', views.KYCAdminListView.as_view(), name='admin-list'),
    path('admin/applications/<str:application_id>/', views.KYCAdminDetailView.as_view(), name='admin-detail'),
    path('admin/applications/<str:application_id>/start-review/', views.KYCAdminStartReviewView.as_view(), name='admin-start-review'),
    path('admin/applications/<str:application_id>/review/', views.KYCAdminReviewView.as_view(), name='admin-review'),
]
