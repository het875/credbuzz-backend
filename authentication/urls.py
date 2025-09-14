from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password'),
    
    # User profile and verification
    path('profile/', views.profile, name='profile'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('verify-mobile/', views.verify_mobile, name='verify_mobile'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    
    # Device and session management
    path('login-history/', views.login_history, name='login_history'),
    path('active-devices/', views.active_devices, name='active_devices'),
    path('revoke-device/', views.revoke_device, name='revoke_device'),
    path('trust-device/', views.trust_device, name='trust_device'),
    path('security-logs/', views.security_logs, name='security_logs'),
]