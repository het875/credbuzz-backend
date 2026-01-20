"""
KYC Verification URL Configuration
====================================
URL patterns for KYC/Onboarding API endpoints.

OTP Endpoints (in users_auth):
    /api/auth-user/send-otp/          - Send OTP
    /api/auth-user/verify-otp/        - Verify OTP
    /api/auth-user/resend-otp/        - Resend OTP

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
    
    # Identity Proof - Aadhaar (POST/PUT endpoints)
    path('identity/aadhaar/', views.AadhaarDetailsView.as_view(), name='aadhaar-details'),
    path('identity/aadhaar/upload/', views.AadhaarUploadView.as_view(), name='aadhaar-upload'),
    path('identity/aadhaar/update/', views.AadhaarUpdateView.as_view(), name='aadhaar-update'),
    
    # Identity Proof - Aadhaar (GET endpoints - Step-wise)
    path('identity/aadhaar/details/', views.GetAadhaarDetailsView.as_view(), name='get-aadhaar-details'),
    path('identity/aadhaar/images/', views.GetAadhaarImagesView.as_view(), name='get-aadhaar-images'),
    
    # Identity Proof - PAN (POST/PUT endpoints)
    path('identity/pan/', views.PANDetailsView.as_view(), name='pan-details'),
    path('identity/pan/upload/', views.PANUploadView.as_view(), name='pan-upload'),
    path('identity/pan/update/', views.PANUpdateView.as_view(), name='pan-update'),
    
    # Identity Proof - PAN (GET endpoints - Step-wise)
    path('identity/pan/details/', views.GetPANDetailsView.as_view(), name='get-pan-details'),
    path('identity/pan/image/', views.GetPANImageView.as_view(), name='get-pan-image'),
    
    # Business Details
    path('business/', views.BusinessDetailsView.as_view(), name='business-details'),
    
    # Verification Images (POST endpoints)
    path('verification/', views.VerificationImagesView.as_view(), name='verification-images'),
    path('verification/selfie/', views.SelfieUploadView.as_view(), name='selfie-upload'),
    path('verification/office/', views.OfficePhotosUploadView.as_view(), name='office-upload'),
    path('verification/address-proof/', views.AddressProofUploadView.as_view(), name='address-proof-upload'),
    
    # Verification Images (GET endpoints - Step-wise)
    path('verification/selfie/get/', views.GetSelfieImageView.as_view(), name='get-selfie-image'),
    path('verification/office/get/', views.GetOfficeImagesView.as_view(), name='get-office-images'),
    path('verification/address-proof/get/', views.GetAddressProofImageView.as_view(), name='get-address-proof-image'),
    
    # Bank Details (POST/PUT endpoints)
    path('bank/', views.BankDetailsView.as_view(), name='bank-details'),
    
    # Bank Details (GET endpoints - Step-wise)
    path('bank/details/', views.GetBankDetailsView.as_view(), name='get-bank-details'),
    path('bank/document/', views.GetBankDocumentView.as_view(), name='get-bank-document'),
    
    # Business Details (GET endpoint - Step-wise)
    path('business/details/', views.GetBusinessDetailsView.as_view(), name='get-business-details'),
    
    # Admin Endpoints
    path('admin/applications/', views.KYCAdminListView.as_view(), name='admin-list'),
    path('admin/applications/<str:application_id>/', views.KYCAdminDetailView.as_view(), name='admin-detail'),
    path('admin/applications/<str:application_id>/start-review/', views.KYCAdminStartReviewView.as_view(), name='admin-start-review'),
    path('admin/applications/<str:application_id>/review/', views.KYCAdminReviewView.as_view(), name='admin-review'),
]
