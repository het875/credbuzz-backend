"""
URL configuration for credbuzzpay_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import OTP views for auth endpoints
from kyc_verification.views import OTPSendView, OTPVerifyView, OTPResendView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users_auth.urls')),
    path('api/rbac/', include('rbac.urls', namespace='rbac')),
    path('api/kyc/', include('kyc_verification.urls', namespace='kyc_verification')),
    path('api/bills/', include('bill_pay.urls', namespace='bill_pay')),
    
    # OTP endpoints under auth
    path('api/auth/send-otp/', OTPSendView.as_view(), name='send-otp'),
    path('api/auth/verify-otp/', OTPVerifyView.as_view(), name='verify-otp'),
    path('api/auth/resend-otp/', OTPResendView.as_view(), name='resend-otp'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
