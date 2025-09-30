"""
ERP Middleware
Role-based access control, security logging, and API rate limiting
"""
import json
import logging
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import LoginActivity, AuditTrail, UserPlatformAccess, AppAccessControl
from .utils import get_client_ip, get_device_fingerprint, log_security_event

logger = logging.getLogger(__name__)
User = get_user_model()


class SecurityLoggingMiddleware:
    """Log all API requests for security monitoring."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Record request time
        start_time = time.time()
        
        # Get client info
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Process request
        response = self.get_response(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # milliseconds
        
        # Log request if it's an API call
        if request.path.startswith('/erp/') or request.path.startswith('/api/'):
            self._log_api_request(request, response, ip_address, user_agent, response_time)
        
        return response
    
    def _log_api_request(self, request, response, ip_address, user_agent, response_time):
        """Log API request details."""
        try:
            # Prepare log data
            log_data = {
                'method': request.method,
                'path': request.path,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'user_id': request.user.id if request.user.is_authenticated else None,
                'timestamp': timezone.now().isoformat()
            }
            
            # Log query parameters for GET requests
            if request.method == 'GET' and request.GET:
                log_data['query_params'] = dict(request.GET)
            
            # Don't log sensitive data (passwords, tokens, etc.)
            if request.method in ['POST', 'PATCH', 'PUT'] and hasattr(request, 'body'):
                try:
                    body = json.loads(request.body)
                    # Remove sensitive fields
                    sensitive_fields = ['password', 'confirm_password', 'otp', 'token', 'access_token', 'refresh_token']
                    for field in sensitive_fields:
                        if field in body:
                            body[field] = '***REDACTED***'
                    log_data['request_body'] = body
                except (json.JSONDecodeError, ValueError):
                    log_data['request_body'] = '***NON_JSON_DATA***'
            
            # Log to Django logger
            if response.status_code >= 400:
                logger.warning(f"API Request Failed: {json.dumps(log_data)}")
            else:
                logger.info(f"API Request: {json.dumps(log_data)}")
            
            # Log suspicious activity
            if response.status_code in [401, 403, 429]:
                self._check_suspicious_activity(request, ip_address, response.status_code)
                
        except Exception as e:
            logger.error(f"Error logging API request: {str(e)}")
    
    def _check_suspicious_activity(self, request, ip_address, status_code):
        """Check for suspicious activity patterns."""
        try:
            # Count failed requests from this IP in the last hour
            cache_key = f"failed_requests_{ip_address}"
            failed_count = cache.get(cache_key, 0)
            
            if failed_count >= 10:  # More than 10 failed requests per hour
                log_security_event(
                    user=request.user if request.user.is_authenticated else None,
                    event_type='suspicious_activity',
                    description=f'Multiple failed requests from IP {ip_address}',
                    request=request,
                    severity='warning'
                )
                
        except Exception as e:
            logger.error(f"Error checking suspicious activity: {str(e)}")


class RoleBasedAccessMiddleware:
    """Enforce role-based access control for protected endpoints."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define role-based access rules
        self.role_access_rules = {
            '/erp/admin/': ['master_superadmin', 'super_admin'],
            '/erp/branch/manage/': ['master_superadmin', 'super_admin', 'admin'],
            '/erp/user/create/': ['master_superadmin', 'super_admin', 'admin'],
            '/erp/activity/audit/': ['master_superadmin', 'super_admin', 'admin'],
            '/erp/dashboard/stats/': ['master_superadmin', 'super_admin', 'admin'],
        }
    
    def __call__(self, request):
        # Check role-based access before processing request
        if not self._check_role_access(request):
            return JsonResponse(
                {
                    'error': 'Insufficient permissions',
                    'detail': 'Your role does not have access to this resource'
                }, 
                status=403
            )
        
        response = self.get_response(request)
        return response
    
    def _check_role_access(self, request):
        """Check if user's role has access to the requested endpoint."""
        try:
            # Skip check for non-ERP endpoints
            if not request.path.startswith('/erp/'):
                return True
            
            # Skip check for public endpoints
            public_endpoints = [
                '/erp/health/',
                '/erp/auth/register/',
                '/erp/auth/login/',
                '/erp/branches/',
                '/erp/otp/request/',
                '/erp/otp/verify/'
            ]
            
            if any(request.path.startswith(endpoint) for endpoint in public_endpoints):
                return True
            
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return False
            
            # Check specific role requirements
            for endpoint_pattern, required_roles in self.role_access_rules.items():
                if request.path.startswith(endpoint_pattern):
                    if request.user.role not in required_roles:
                        # Log access denial
                        log_security_event(
                            user=request.user,
                            event_type='access_denied',
                            description=f'Role {request.user.role} attempted to access {request.path}',
                            request=request,
                            severity='warning'
                        )
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking role access: {str(e)}")
            return False


class PlatformAccessMiddleware:
    """Enforce platform-specific access restrictions."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check platform access before processing request
        if not self._check_platform_access(request):
            return JsonResponse(
                {
                    'error': 'Platform access denied',
                    'detail': 'You do not have access to this platform'
                }, 
                status=403
            )
        
        response = self.get_response(request)
        return response
    
    def _check_platform_access(self, request):
        """Check if user has access to the current platform."""
        try:
            # Skip check for non-authenticated users on public endpoints
            if not request.user.is_authenticated:
                return True
            
            # Determine platform based on request characteristics
            platform = self._detect_platform(request)
            
            # Check if user has access to this platform
            if platform:
                try:
                    platform_access = UserPlatformAccess.objects.get(
                        user=request.user,
                        platform=platform
                    )
                    
                    if not platform_access.is_allowed:
                        # Log platform access denial
                        log_security_event(
                            user=request.user,
                            event_type='platform_access_denied',
                            description=f'User attempted to access {platform} platform',
                            request=request,
                            severity='warning'
                        )
                        return False
                        
                except UserPlatformAccess.DoesNotExist:
                    # No explicit access rule - deny access for security
                    log_security_event(
                        user=request.user,
                        event_type='platform_access_denied',
                        description=f'No platform access rule for {platform}',
                        request=request,
                        severity='warning'
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking platform access: {str(e)}")
            return True  # Allow access on error to prevent system lockout
    
    def _detect_platform(self, request):
        """Detect which platform the request is coming from."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Check for mobile app
        if 'credbuzzmobile' in user_agent:
            return 'mobile_app'
        
        # Check for admin panel access
        if request.path.startswith('/admin/'):
            return 'admin_panel'
        
        # Check for API access
        if request.path.startswith('/api/') or request.path.startswith('/erp/'):
            # Further refinement could be based on API keys or other headers
            return 'api'
        
        # Default to web
        return 'web'


class APIRateLimitMiddleware:
    """Rate limiting for API endpoints."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limit configurations
        self.rate_limits = {
            'auth': {'requests': 5, 'window': 300},      # 5 requests per 5 minutes
            'otp': {'requests': 3, 'window': 300},       # 3 requests per 5 minutes
            'default': {'requests': 100, 'window': 3600} # 100 requests per hour
        }
    
    def __call__(self, request):
        # Check rate limits before processing request
        if not self._check_rate_limit(request):
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'detail': 'Too many requests. Please try again later.'
                }, 
                status=429
            )
        
        response = self.get_response(request)
        return response
    
    def _check_rate_limit(self, request):
        """Check if request exceeds rate limits."""
        try:
            # Skip rate limiting for non-API requests
            if not (request.path.startswith('/erp/') or request.path.startswith('/api/')):
                return True
            
            # Get identifier (user ID or IP address)
            identifier = request.user.id if request.user.is_authenticated else get_client_ip(request)
            
            # Determine rate limit category
            category = self._get_rate_limit_category(request.path)
            
            # Get rate limit configuration
            limit_config = self.rate_limits.get(category, self.rate_limits['default'])
            
            # Create cache key
            cache_key = f"rate_limit_{category}_{identifier}"
            
            # Get current request count
            current_count = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if current_count >= limit_config['requests']:
                # Log rate limit violation
                log_security_event(
                    user=request.user if request.user.is_authenticated else None,
                    event_type='rate_limit_exceeded',
                    description=f'Rate limit exceeded for {category} by {identifier}',
                    request=request,
                    severity='warning'
                )
                return False
            
            # Increment counter
            cache.set(cache_key, current_count + 1, limit_config['window'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True  # Allow request on error
    
    def _get_rate_limit_category(self, path):
        """Determine rate limit category based on request path."""
        if 'auth' in path:
            return 'auth'
        elif 'otp' in path:
            return 'otp'
        else:
            return 'default'


class JWTAuthMiddleware:
    """Custom JWT authentication middleware."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
    
    def __call__(self, request):
        # Handle JWT authentication
        self._authenticate_jwt(request)
        
        response = self.get_response(request)
        return response
    
    def _authenticate_jwt(self, request):
        """Authenticate user using JWT token."""
        try:
            # Skip authentication for public endpoints
            public_endpoints = [
                '/erp/health/',
                '/erp/auth/register/',
                '/erp/auth/login/',
                '/erp/branches/',
                '/admin/',
                '/erp/otp/request/',
                '/erp/otp/verify/'
            ]
            
            if any(request.path.startswith(endpoint) for endpoint in public_endpoints):
                return
            
            # Try to authenticate using JWT
            auth_result = self.jwt_auth.authenticate(request)
            
            if auth_result:
                user, token = auth_result
                request.user = user
                request.auth = token
                
                # Log successful token authentication
                logger.debug(f"JWT authentication successful for user {user.id}")
            
        except (InvalidToken, TokenError) as e:
            # Log invalid token attempt
            logger.warning(f"Invalid JWT token: {str(e)}")
            
            # Don't set user - let the view handle authentication
            pass
        
        except Exception as e:
            logger.error(f"Error in JWT authentication: {str(e)}")


class CORSSecurityMiddleware:
    """Enhanced CORS handling with security headers."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response):
        """Add security-related headers to response."""
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevent content type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content security policy (basic)
        response['Content-Security-Policy'] = "default-src 'self'"
        
        # HTTPS enforcement (in production)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'