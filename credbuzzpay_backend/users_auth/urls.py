"""
URL configuration for users_auth app
"""
from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView,
    RefreshTokenView,
    UserProfileView,
    UserListView,
    UserDetailView,
    UserHardDeleteView,
    UserRestoreView,
    UserActivateView,
    VerifyRegistrationOTPView,
    ResendRegistrationOTPView,
    UserActivityLogListView,
    MyActivityLogView,
    UserProfileWithAccessView,
    CreatePrivilegedUserView,
)

app_name = 'users_auth'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # OTP Verification for Registration
    path('verify-registration-otp/', VerifyRegistrationOTPView.as_view(), name='verify-registration-otp'),
    path('resend-registration-otp/', ResendRegistrationOTPView.as_view(), name='resend-registration-otp'),
    
    # Password management
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Token management
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    
    # User profile (current user)
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile-full/', UserProfileWithAccessView.as_view(), name='profile-full'),
    
    # Activity Logs
    path('activity-logs/', UserActivityLogListView.as_view(), name='activity-logs'),
    path('my-activity/', MyActivityLogView.as_view(), name='my-activity'),
    
    # User management (CRUD)
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/hard-delete/', UserHardDeleteView.as_view(), name='user-hard-delete'),
    path('users/<int:user_id>/restore/', UserRestoreView.as_view(), name='user-restore'),
    path('users/<int:user_id>/<str:action>/', UserActivateView.as_view(), name='user-action'),
    
    # System Setup (Protected by Secret Key)
    path('system/create-privileged-user/', CreatePrivilegedUserView.as_view(), name='create-privileged-user'),
]
