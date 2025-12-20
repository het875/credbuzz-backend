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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

# Import OTP views for auth endpoints
from kyc_verification.views import OTPSendView, OTPVerifyView, OTPResendView
# Import Health Check views
from credbuzzpay_backend.health import HealthCheckView, DetailedHealthCheckView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
   openapi.Info(
      title="My API",
      default_version='v1',
      description="Test description",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('admin/', admin.site.urls),
    
    # Health Check endpoints (no auth required)
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/health/detailed/', DetailedHealthCheckView.as_view(), name='health-check-detailed'),
    
    # API endpoints
    path('api/auth-user/', include('users_auth.urls')),
    path('api/rbac/', include('rbac.urls', namespace='rbac')),
    path('api/kyc/', include('kyc_verification.urls', namespace='kyc_verification')),
    path('api/bills/', include('bill_pay.urls', namespace='bill_pay')),
    
    # OTP endpoints under auth
    path('api/auth-user/send-otp/', OTPSendView.as_view(), name='send-otp'),
    path('api/auth-user/verify-otp/', OTPVerifyView.as_view(), name='verify-otp'),
    path('api/auth-user/resend-otp/', OTPResendView.as_view(), name='resend-otp'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
