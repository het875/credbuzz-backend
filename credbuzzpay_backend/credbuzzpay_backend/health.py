"""
Health Check Views
==================
API endpoints for health monitoring and system status.
"""

from django.db import connection
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring and deployment verification.
    
    GET /api/health/
    
    Returns system health status including:
    - Server status
    - Database connectivity
    - Current timestamp
    - Version info
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # No auth required
    
    def get(self, request):
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'service': 'CredBuzzPay Backend API',
            'checks': {}
        }
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_data['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            health_data['status'] = 'unhealthy'
        
        # Return appropriate status code
        status_code = status.HTTP_200_OK if health_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=status_code)


class DetailedHealthCheckView(APIView):
    """
    Detailed health check with more system information.
    
    GET /api/health/detailed/
    
    Returns detailed system information (requires authentication).
    """
    permission_classes = [AllowAny]  # Can change to IsAuthenticated for production
    
    def get(self, request):
        from django.conf import settings
        import sys
        import django
        
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'service': 'CredBuzzPay Backend API',
            'environment': {
                'debug': settings.DEBUG,
                'python_version': sys.version,
                'django_version': django.__version__,
            },
            'checks': {}
        }
        
        # Database check with table count
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                # Get table info
                if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                else:
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables")
                table_count = cursor.fetchone()[0]
            
            health_data['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful',
                'tables': table_count
            }
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            health_data['status'] = 'unhealthy'
        
        # Email configuration check
        email_configured = bool(
            getattr(settings, 'EMAIL_HOST_USER', None) and 
            getattr(settings, 'EMAIL_HOST_PASSWORD', None)
        )
        health_data['checks']['email'] = {
            'status': 'configured' if email_configured else 'not_configured',
            'backend': getattr(settings, 'EMAIL_BACKEND', 'Not set')
        }
        
        status_code = status.HTTP_200_OK if health_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=status_code)
