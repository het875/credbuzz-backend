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
    UserActivateView,
)

app_name = 'users_auth'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password management
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Token management
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    
    # User profile (current user)
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # User management (CRUD)
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/<str:action>/', UserActivateView.as_view(), name='user-action'),
]
