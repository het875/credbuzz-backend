"""
Middleware for automatic audit logging of all requests and responses.
"""
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from accounts.services.audit_service import log_audit_trail


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests and responses to audit trail.
    """
    
    # Endpoints that should not be audited
    EXCLUDE_PATHS = [
        '/health',
        '/metrics',
        '/static',
        '/media',
    ]
    
    def should_audit(self, path):
        """Check if the path should be audited."""
        for exclude in self.EXCLUDE_PATHS:
            if path.startswith(exclude):
                return False
        return True
    
    def process_request(self, request):
        """Store request data in the request object for later auditing."""
        if not self.should_audit(request.path):
            return None
        
        # Store request metadata
        request.audit_data = {
            'method': request.method,
            'path': request.path,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': None,
        }
        
        return None
    
    def process_response(self, request, response):
        """Log the request to audit trail after response is generated."""
        if not self.should_audit(request.path):
            return response
        
        if not hasattr(request, 'audit_data'):
            return response
        
        # Don't log file uploads or downloads
        if response.get('Content-Type', '').startswith('application/'):
            if 'attachment' in response.get('Content-Disposition', ''):
                return response
        
        # Get user from request
        user_code = None
        if hasattr(request, 'user') and request.user and not isinstance(request.user, AnonymousUser):
            try:
                user_code = request.user
            except Exception:
                pass
        
        # Log to audit trail
        try:
            log_audit_trail(
                action='api_call',
                resource_type=request.path.split('/')[-2] if '/' in request.path else 'API',
                description=f"{request.method} {request.path} - Status {response.status_code}",
                user_code=user_code,
                ip_address=request.audit_data['ip_address'],
                user_agent=request.audit_data['user_agent'],
                request_method=request.audit_data['method'],
                request_path=request.audit_data['path'],
                new_values={'status_code': response.status_code},
            )
        except Exception:
            # Don't let audit logging break the response
            pass
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """
        Get the client's IP address from the request.
        Handles X-Forwarded-For header for proxied requests.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '0.0.0.0'
