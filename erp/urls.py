"""
ERP URLs Configuration
Authentication, Registration, KYC, Business Management
"""
from django.urls import path
from . import views

app_name = 'erp'

urlpatterns = [
    # Health Check
    path('health/', views.health_check, name='health_check'),
    
    # Authentication & Registration
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    # OTP Management
    path('otp/request/', views.OTPRequestView.as_view(), name='otp_request'),
    path('otp/verify/', views.OTPVerificationView.as_view(), name='otp_verify'),
    
    # User Profile
    path('user/profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('branches/', views.BranchListView.as_view(), name='branch_list'),
    
    # KYC Management
    path('kyc/aadhaar/', views.AadhaarKYCView.as_view(), name='aadhaar_kyc'),
    path('kyc/pan/', views.PanKYCView.as_view(), name='pan_kyc'),
    
    # Business Management
    path('business/details/', views.BusinessDetailsView.as_view(), name='business_details'),
    path('business/images/', views.BusinessImagesView.as_view(), name='business_images'),
    path('business/images/<str:image_id>/', views.BusinessImagesView.as_view(), name='business_image_delete'),
    
    # Bank Details
    path('bank/details/', views.BankDetailsView.as_view(), name='bank_details'),
    
    # Activity & Reporting
    path('activity/login/', views.LoginActivityListView.as_view(), name='login_activity'),
    path('activity/audit/', views.AuditTrailListView.as_view(), name='audit_trail'),
    
    # Dashboard
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
]