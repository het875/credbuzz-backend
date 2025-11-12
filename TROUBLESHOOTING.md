# Troubleshooting & FAQ Guide - CredbuzzPay ERP System

## Table of Contents

1. [Common Issues](#common-issues)
2. [Database Issues](#database-issues)
3. [Authentication Issues](#authentication-issues)
4. [Celery Issues](#celery-issues)
5. [Performance Issues](#performance-issues)
6. [Deployment Issues](#deployment-issues)
7. [Frequently Asked Questions](#frequently-asked-questions)
8. [Debugging Tips](#debugging-tips)

---

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'credbuzzpay_backend'`

**Cause**: Virtual environment not activated or dependencies not installed.

**Solution**:
```bash
# Activate virtual environment
source credbuzz_backend_venv/bin/activate  # Linux/macOS
# or
credbuzz_backend_venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import django; print(django.get_version())"
```

---

### Issue: `SECRET_KEY must be provided`

**Cause**: Django SECRET_KEY not configured in settings.

**Solution**:
```bash
# Generate new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Add to .env
SECRET_KEY=generated-secret-key-here

# Or add to settings.py
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-development-secret-key')
```

---

### Issue: `Import Error: cannot import name 'OTPService'`

**Cause**: Service module not found in Python path.

**Solution**:
```bash
# Ensure accounts/services/__init__.py exists
touch accounts/services/__init__.py

# Add imports to __init__.py
# accounts/services/__init__.py
from .otp_service import OTPService
from .audit_service import *

__all__ = ['OTPService']
```

---

### Issue: `JSONDecodeError: Expecting value`

**Cause**: Invalid JSON in request body.

**Solution**:
```python
# Check Content-Type header
headers = {
    'Content-Type': 'application/json'
}

# Ensure valid JSON
import json
data = json.dumps({
    'email': 'user@example.com',
    'password': 'SecurePass@123'
})

# Or use requests library
import requests
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json=data  # Automatically handles JSON encoding
)
```

---

### Issue: `CORS Error: Access-Control-Allow-Origin header missing`

**Cause**: CORS headers not configured.

**Solution**:
```python
# settings.py
INSTALLED_APPS = [
    'corsheaders',
    # ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ...
]

# Allow specific origins
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'https://yourdomain.com',
]

# Or allow all (development only)
CORS_ALLOW_ALL_ORIGINS = True  # NOT for production
```

---

## Database Issues

### Issue: `ProgrammingError: relation "accounts_useraccount" does not exist`

**Cause**: Database tables not created (migrations not applied).

**Solution**:
```bash
# Check migration status
python manage.py showmigrations

# Create new migrations
python manage.py makemigrations accounts

# Apply migrations
python manage.py migrate

# Check if successful
python manage.py migrate --plan
```

---

### Issue: `IntegrityError: duplicate key value violates unique constraint`

**Cause**: Attempting to create duplicate record with unique field.

**Solution**:
```python
# Use get_or_create
user, created = UserAccount.objects.get_or_create(
    email='test@example.com',
    defaults={
        'mobile': '+919876543210',
        'user_code': 'ABC123'
    }
)

# Or update_or_create
user, created = UserAccount.objects.update_or_create(
    email='test@example.com',
    defaults={
        'mobile': '+919876543210'
    }
)
```

---

### Issue: `OperationalError: could not connect to server`

**Cause**: Database server not running or connection settings incorrect.

**Solution**:
```bash
# Check if PostgreSQL is running
# Linux/macOS
sudo systemctl status postgresql

# Windows
Get-Service postgresql-x64-15  # or your version

# Test connection
psql -U credbuzz_user -d credbuzz_prod -h localhost -p 5432

# Check settings.py
# Database connection should be:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'credbuzz'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

---

### Issue: `TransactionManagementError: An error occurred in the wrapped function`

**Cause**: Database transaction handling error.

**Solution**:
```python
# Use transaction.atomic for complex operations
from django.db import transaction

@transaction.atomic
def create_user_with_records(email, mobile):
    user = UserAccount.objects.create(
        email=email,
        mobile=mobile
    )
    
    # Create related records
    SecuritySettings.objects.create(user_account=user)
    RegistrationProgress.objects.create(user_account=user)
    
    return user
```

---

## Authentication Issues

### Issue: `401 Unauthorized: Authentication credentials were not provided`

**Cause**: JWT token missing from Authorization header.

**Solution**:
```bash
# Correct header format
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

# Example with curl
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/users/

# Example with Python requests
import requests
headers = {
    'Authorization': f'Bearer {access_token}'
}
response = requests.get(
    'http://localhost:8000/api/v1/users/',
    headers=headers
)
```

---

### Issue: `401 Unauthorized: Given token not valid for any token type`

**Cause**: JWT token expired or invalid.

**Solution**:
```python
# Refresh token to get new access token
import requests

refresh_data = {
    'refresh': refresh_token
}
response = requests.post(
    'http://localhost:8000/api/token/refresh/',
    json=refresh_data
)

new_access_token = response.json()['access']

# Update Authorization header
headers = {
    'Authorization': f'Bearer {new_access_token}'
}
```

---

### Issue: `403 Forbidden: You do not have permission to perform this action`

**Cause**: User lacks required permissions.

**Solution**:
```python
# Check user role
print(request.user.user_role)  # Should be 'admin' or 'super_admin'

# Check permissions
from accounts.permissions import IsAdmin, HasFeatureAccess
permission = IsAdmin()
has_permission = permission.has_permission(request, view)

# Assign required role
user.user_role = 'admin'
user.save()

# Grant feature access
from accounts.models import AppAccessControl
AppAccessControl.objects.create(
    user_code=user.user_code,
    app_feature_id=feature.id,
    access_level='full'
)
```

---

### Issue: `ValidationError: This field may not be blank`

**Cause**: Required field not provided in request.

**Solution**:
```python
# Include all required fields
data = {
    'email': 'user@example.com',
    'mobile': '+919876543210',
    'password': 'SecurePass@123',
    'password_confirm': 'SecurePass@123'
}

# Check serializer validation
from accounts.serializers import UserAccountSerializer
serializer = UserAccountSerializer(data=data)
if not serializer.is_valid():
    print(serializer.errors)
    # {'email': ['This field may not be blank.']}
```

---

## Celery Issues

### Issue: `Celery tasks not executing`

**Cause**: Celery worker not running or Redis connection issue.

**Solution**:
```bash
# Check if Redis is running
redis-cli ping
# Output: PONG

# Start Celery worker
celery -A credbuzzpay_backend worker -l info

# Start Celery beat (for scheduled tasks)
celery -A credbuzzpay_backend beat -l info

# Check Celery status
celery -A credbuzzpay_backend inspect active
```

---

### Issue: `ConnectionRefusedError: [Errno 111] Connection refused`

**Cause**: Redis server not running or incorrect connection URL.

**Solution**:
```python
# settings.py
CELERY_BROKER_URL = os.environ.get(
    'REDIS_URL',
    'redis://localhost:6379/0'
)

# Verify Redis connection
import redis
try:
    r = redis.Redis(host='localhost', port=6379)
    r.ping()
    print("Redis connected")
except redis.ConnectionError:
    print("Redis not connected")

# Start Redis
redis-server

# Or via Docker
docker run -d -p 6379:6379 redis:7
```

---

### Issue: `Task failed with KeyError: 'Message queue does not exist'`

**Cause**: Celery queue not configured properly.

**Solution**:
```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERY_TASK_QUEUE_ROUTING = {
    'accounts.tasks.send_otp_email': {'queue': 'default'},
    'accounts.tasks.send_otp_sms': {'queue': 'default'},
}

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Restart Celery worker
celery -A credbuzzpay_backend worker -l info
```

---

### Issue: `Celery beat scheduled tasks not running`

**Cause**: Beat scheduler not running or schedule not configured.

**Solution**:
```python
# settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-otps': {
        'task': 'accounts.tasks.cleanup_expired_otps',
        'schedule': crontab(hour=2, minute=0),  # Daily 2 AM
    },
    'auto-unblock-users': {
        'task': 'accounts.tasks.auto_unblock_user_accounts',
        'schedule': 300,  # Every 5 minutes
    },
}

# Start beat scheduler
celery -A credbuzzpay_backend beat -l info

# Monitor beat
celery -A credbuzzpay_backend events
```

---

## Performance Issues

### Issue: `Request timeout: Response took too long`

**Cause**: Slow database queries or missing indexes.

**Solution**:
```python
# Profile database queries (development only)
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# Or use Django Debug Toolbar
pip install django-debug-toolbar

# Add to INSTALLED_APPS and MIDDLEWARE
INSTALLED_APPS = ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Optimize queries
users = UserAccount.objects.select_related(
    'branch'
).prefetch_related(
    'app_access_control'
)[:100]  # Limit results
```

---

### Issue: `MemoryError: Unable to allocate memory`

**Cause**: Large dataset operations without pagination or chunking.

**Solution**:
```python
# Use pagination
from django.core.paginator import Paginator

users = UserAccount.objects.all()
paginator = Paginator(users, 1000)

for page_num in paginator.page_range:
    page = paginator.get_page(page_num)
    for user in page:
        # Process user

# Or use iterator for large querysets
for user in UserAccount.objects.iterator(chunk_size=1000):
    # Process user

# Or use values to select only needed fields
users = UserAccount.objects.values_list('user_code', 'email')
```

---

### Issue: `Redis memory limit exceeded`

**Cause**: Cache filling up without eviction.

**Solution**:
```python
# Configure Redis eviction policy
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru  # Remove least recently used

# Or configure in settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        }
    }
}

# Monitor Redis memory
redis-cli INFO memory

# Clear cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## Deployment Issues

### Issue: `ModuleNotFoundError: No module named 'credbuzzpay_backend'`

**Cause**: Python path not set correctly in production.

**Solution**:
```bash
# Add absolute path to WSGI
# gunicorn_config.py
import sys
sys.path.insert(0, '/home/credbuzz/credbuzz-backend')

# Or set PYTHONPATH environment variable
export PYTHONPATH=/home/credbuzz/credbuzz-backend:$PYTHONPATH

# In supervisor config
[program:credbuzz-django]
environment=PYTHONPATH="/home/credbuzz/credbuzz-backend"
```

---

### Issue: `403 Forbidden: CSRF verification failed`

**Cause**: CSRF token missing or domain mismatch.

**Solution**:
```python
# settings.py
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://*.yourdomain.com',
]

# Include CSRF token in requests
import requests
from bs4 import BeautifulSoup

response = requests.get('http://localhost:8000/')
csrf_token = response.cookies['csrftoken']

headers = {
    'X-CSRFToken': csrf_token
}
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json=data,
    headers=headers
)
```

---

### Issue: `502 Bad Gateway: Connection refused`

**Cause**: Gunicorn/application server not responding.

**Solution**:
```bash
# Check if Gunicorn is running
ps aux | grep gunicorn

# Start Gunicorn
gunicorn -c gunicorn_config.py credbuzzpay_backend.wsgi:application

# Check Supervisor status
sudo supervisorctl status

# Restart service
sudo supervisorctl restart credbuzz-django

# Check Nginx config
sudo nginx -t
sudo systemctl restart nginx

# Check logs
tail -f /var/log/nginx/error.log
tail -f /home/credbuzz/credbuzz-backend/logs/gunicorn_error.log
```

---

### Issue: `SSL certificate verification failed`

**Cause**: SSL certificate not installed or expired.

**Solution**:
```bash
# Install Let's Encrypt certificate
sudo certbot certonly --nginx -d yourdomain.com

# Renew certificate
sudo certbot renew

# Check certificate expiry
sudo openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout

# Auto-renew
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Frequently Asked Questions

### Q1: How do I reset a user's password if they forget it?

**A**: Use the password reset flow:
```python
from django.utils import timezone
from accounts.models import UserAccount

# Admin can reset password
user = UserAccount.objects.get(user_code='ABC123')
user.set_password('TempPass@123')
user.save()

# Notify user to change password after login
```

---

### Q2: How do I unlock a blocked user account?

**A**: Update the blocked status:
```python
from django.utils import timezone
from accounts.models import UserAccount

user = UserAccount.objects.get(user_code='ABC123')
user.is_blocked = False
user.blocked_until = None
user.save()
```

---

### Q3: How do I verify a user's KYC manually?

**A**: Update verification status in admin or programmatically:
```python
from django.utils import timezone
from accounts.models import AadhaarKYC, UserAccount

kyc = AadhaarKYC.objects.get(user_account__user_code='ABC123')
kyc.is_verified = True
kyc.verification_method = 'manual'
kyc.verified_at = timezone.now()
kyc.verified_by_user_id = admin_user.id
kyc.save()

# Update user KYC flag
user = kyc.user_account
user.is_kyc_complete = True
user.kyc_verified_at = timezone.now()
user.save()
```

---

### Q4: How do I export audit logs?

**A**: Query and export audit trail:
```python
import csv
from django.utils import timezone
from accounts.models import AuditTrail
from datetime import timedelta

# Get logs from last 30 days
thirty_days_ago = timezone.now() - timedelta(days=30)
audit_logs = AuditTrail.objects.filter(
    created_at__gte=thirty_days_ago
).order_by('-created_at')

# Export to CSV
with open('audit_logs.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        'Timestamp', 'User', 'Action', 'Resource Type',
        'Resource ID', 'IP Address', 'Status'
    ])
    
    for log in audit_logs:
        writer.writerow([
            log.created_at,
            log.user_account.user_code,
            log.action,
            log.resource_type,
            log.resource_identifier,
            log.ip_address,
            'Success'
        ])
```

---

### Q5: How do I handle OTP rate limiting?

**A**: OTP service handles this automatically, but you can query:
```python
from accounts.models import OTPRecord
from accounts.services.security import increment_otp_attempts
from django.utils import timezone
from datetime import timedelta

# Check if user is blocked
otp = OTPRecord.objects.filter(
    user_account__user_code='ABC123',
    otp_type='email'
).latest('created_at')

if otp.otp_attempts >= 3:
    # User is blocked
    print("Max attempts reached")
    # User must wait for cooldown (default: 5 minutes)
```

---

### Q6: How do I generate test data?

**A**: Use factories:
```bash
pip install factory-boy

python manage.py shell
>>> from accounts.tests.factories import UserAccountFactory, OTPRecordFactory
>>> 
>>> # Create 100 test users
>>> users = [UserAccountFactory() for _ in range(100)]
>>> 
>>> # Create OTP records
>>> otps = [OTPRecordFactory(user_account=user) for user in users[:10]]
```

---

### Q7: How do I monitor application health?

**A**: Setup health check endpoint:
```python
# urls.py
from django.http import JsonResponse

urlpatterns = [
    path('health/', lambda request: JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    }))
]

# Check health
curl http://localhost:8000/health/
```

---

### Q8: How do I backup the database?

**A**: Use PostgreSQL dump:
```bash
# Backup
pg_dump -U credbuzz_user -d credbuzz_prod > backup.sql

# Restore
psql -U credbuzz_user -d credbuzz_prod < backup.sql

# Or automated backup
0 2 * * * pg_dump -U credbuzz_user credbuzz_prod > \
    /backups/db-$(date +\%Y\%m\%d).sql
```

---

### Q9: How do I enable debug logging?

**A**: Configure logging:
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'DEBUG',
    },
}
```

---

### Q10: How do I migrate from SQLite to PostgreSQL?

**A**: Use dumpdata and loaddata:
```bash
# On SQLite environment
python manage.py dumpdata > data.json

# On PostgreSQL environment
python manage.py migrate
python manage.py loaddata data.json
```

---

## Debugging Tips

### Enable SQL Query Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Use Django Shell for Testing

```bash
python manage.py shell

# Test OTP verification
>>> from accounts.services.otp_service import OTPService
>>> from accounts.models import UserAccount
>>> user = UserAccount.objects.first()
>>> service = OTPService()
>>> otp_record = service.generate_otp_record(user, 'email_verification')
>>> print(otp_record.email_otp)  # Plain OTP for testing
```

### Check Celery Task Status

```bash
# List active tasks
celery -A credbuzzpay_backend inspect active

# Check scheduled tasks
celery -A credbuzzpay_backend inspect scheduled

# Monitor in real-time
celery -A credbuzzpay_backend events

# Or use Flower UI
celery -A credbuzzpay_backend flower
# Access at http://localhost:5555
```

### Monitor Database Queries

```bash
# In Django shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> with CaptureQueriesContext(connection) as queries:
...     users = UserAccount.objects.filter(is_active=True)[:10]
>>> len(queries)  # Number of queries
>>> for q in queries:
...     print(q['sql'])
```

---

**Last Updated:** November 2025
**Version:** 1.0.0
