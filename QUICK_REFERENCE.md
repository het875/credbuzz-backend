# Quick Reference Guide - CredbuzzPay ERP System

## Project Commands Cheat Sheet

### Virtual Environment

```bash
# Create virtual environment
python -m venv credbuzz_backend_venv

# Activate (Linux/macOS)
source credbuzz_backend_venv/bin/activate

# Activate (Windows)
credbuzz_backend_venv\Scripts\activate

# Deactivate
deactivate

# Install dependencies
pip install -r requirements.txt

# Upgrade pip
pip install --upgrade pip
```

---

## Django Management Commands

```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver 0.0.0.0:8000

# Collect static files
python manage.py collectstatic --noinput

# Django shell
python manage.py shell

# Run tests
python manage.py test accounts
pytest accounts/tests

# Generate test coverage
pytest --cov=accounts --cov-report=html

# Load fixtures
python manage.py loaddata fixtures/initial_data.json

# Database queries count (development)
python manage.py sqlquery select count(*) from accounts_useraccount

# Show database schema
python manage.py inspectdb > models.py

# Generate admin docs
python manage.py autodoc
```

---

## Database Commands

### PostgreSQL

```bash
# Connect to database
psql -U credbuzz_user -d credbuzz_prod -h localhost

# Common psql commands
\dt                 # List tables
\d table_name       # Describe table
\df                 # List functions
\q                  # Quit

# Backup database
pg_dump -U credbuzz_user credbuzz_prod > backup.sql

# Restore database
psql -U credbuzz_user credbuzz_prod < backup.sql

# Drop database
dropdb -U credbuzz_user credbuzz_prod

# Create database
createdb -U postgres -O credbuzz_user credbuzz_prod
```

### Redis

```bash
# Connect to Redis
redis-cli

# Verify connection
ping

# Get all keys
keys *

# Clear database
FLUSHDB

# Clear all databases
FLUSHALL

# Check memory
INFO memory

# Monitor Redis in real-time
redis-cli monitor

# Export/backup Redis
redis-cli BGSAVE
```

---

## Celery Commands

```bash
# Start worker
celery -A credbuzzpay_backend worker -l info

# Start beat scheduler
celery -A credbuzzpay_backend beat -l info

# Monitor with Flower
celery -A credbuzzpay_backend flower

# Inspect active tasks
celery -A credbuzzpay_backend inspect active

# Inspect scheduled tasks
celery -A credbuzzpay_backend inspect scheduled

# Purge all tasks
celery -A credbuzzpay_backend purge

# Show worker statistics
celery -A credbuzzpay_backend inspect stats

# Real-time events monitoring
celery -A credbuzzpay_backend events
```

---

## API Endpoints Quick Reference

### Authentication

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/auth/register/initiate` | Start registration |
| POST | `/api/v1/auth/register/verify-otp` | Verify OTP |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/logout` | User logout |
| POST | `/api/v1/auth/forgot-password` | Reset password request |
| POST | `/api/v1/auth/reset-password` | Reset password |
| POST | `/api/v1/auth/change-password` | Change password |

### Users

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/users/` | List users |
| GET | `/api/v1/users/{user_code}` | Get user details |
| PUT | `/api/v1/users/{user_code}` | Update user |
| POST | `/api/v1/users/{user_code}/assign-role` | Assign role |
| POST | `/api/v1/users/{user_code}/block` | Block user |

### KYC

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/kyc/aadhaar/submit` | Submit Aadhaar |
| POST | `/api/v1/kyc/pan/submit` | Submit PAN |
| GET | `/api/v1/kyc/status/{user_code}` | Get KYC status |

---

## Testing Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest accounts/tests/test_models.py

# Run specific test class
pytest accounts/tests/test_models.py::TestUserAccountModel

# Run specific test
pytest accounts/tests/test_models.py::TestUserAccountModel::test_create_user_account

# Run tests in parallel
pytest -n auto

# Run with coverage
pytest --cov=accounts

# Generate HTML coverage report
pytest --cov=accounts --cov-report=html

# Run with verbose output
pytest -v

# Run only failing tests
pytest --lf

# Run tests matching keyword
pytest -k "test_login"

# Run with markers
pytest -m django_db
```

---

## Deployment Commands

```bash
# Setup production environment
pip install gunicorn
pip install supervisor

# Collect static files
python manage.py collectstatic --noinput --clear

# Run migrations
python manage.py migrate

# Start Gunicorn
gunicorn -b 0.0.0.0:8000 credbuzzpay_backend.wsgi:application

# Check Supervisor status
sudo supervisorctl status

# Restart service
sudo supervisorctl restart credbuzz-django

# View logs
tail -f /var/log/supervisor/credbuzz-django.log

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx configuration
sudo nginx -t
```

---

## Docker Commands

```bash
# Build Docker image
docker build -t credbuzz:latest .

# Run Docker container
docker run -d -p 8000:8000 --env-file .env credbuzz:latest

# Docker Compose up
docker-compose up -d

# Docker Compose down
docker-compose down

# View logs
docker logs container_id
docker-compose logs -f web

# Execute command in container
docker exec -it container_id python manage.py migrate

# Stop container
docker stop container_id

# Remove container
docker rm container_id
```

---

## File Structure Quick Reference

```
credbuzz-backend/
├── credbuzzpay_backend/          # Project settings
│   ├── settings.py              # Django configuration
│   ├── urls.py                  # URL routing
│   ├── wsgi.py                  # WSGI for production
│   ├── asgi.py                  # ASGI for async
│   └── celery.py                # Celery configuration
│
├── accounts/                     # Main application
│   ├── migrations/              # Database migrations
│   ├── tests/                   # Test files
│   ├── utils/                   # Utility modules
│   │   ├── code_generator.py
│   │   ├── validators.py
│   │   ├── encryption.py
│   │   └── security.py
│   ├── services/                # Business logic
│   │   ├── otp_service.py
│   │   └── audit_service.py
│   ├── middleware/              # Custom middleware
│   │   └── audit_middleware.py
│   ├── models.py                # Database models
│   ├── views.py                 # API views
│   ├── serializers.py           # DRF serializers
│   ├── permissions.py           # Custom permissions
│   ├── admin.py                 # Admin configuration
│   ├── urls.py                  # App URL routing
│   ├── tasks.py                 # Celery tasks
│   └── apps.py                  # App configuration
│
├── docs/                        # Documentation
├── logs/                        # Application logs
├── media/                       # User uploads
├── static/                      # Static files
├── staticfiles/                 # Collected static files
│
├── requirements.txt             # Python dependencies
├── manage.py                    # Django CLI
├── docker-compose.yml           # Docker Compose
├── Dockerfile                   # Docker image
├── .env.example                 # Environment template
├── .env                         # Environment variables (gitignored)
├── .gitignore                   # Git ignore file
├── README.md                    # Project documentation
├── API_DOCUMENTATION.md         # API reference
├── DEPLOYMENT_GUIDE.md          # Deployment instructions
├── ARCHITECTURE.md              # System architecture
├── TESTING_GUIDE.md             # Testing guide
├── TROUBLESHOOTING.md           # Common issues
└── db.sqlite3                   # SQLite database (development)
```

---

## Environment Variables

### Required Variables

```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ENVIRONMENT=production

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=credbuzz_prod
DB_USER=credbuzz_user
DB_PASSWORD=secure-password
DB_HOST=localhost
DB_PORT=5432

# Redis/Cache
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# SMS
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
```

---

## Git Commands

```bash
# Clone repository
git clone https://github.com/yourusername/credbuzz-backend.git

# Create new branch
git checkout -b feature/new-feature

# Stage changes
git add .

# Commit changes
git commit -m "Add new feature"

# Push to remote
git push origin feature/new-feature

# Pull latest changes
git pull origin main

# Merge branch
git merge feature/new-feature

# View status
git status

# View commit history
git log --oneline

# Revert changes
git revert commit-hash

# Reset to previous commit
git reset --hard HEAD~1
```

---

## Performance Monitoring

```bash
# Monitor CPU and Memory
top

# Check disk usage
df -h

# Monitor network
netstat -an | grep ESTABLISHED | wc -l

# Check PostgreSQL connections
psql -U credbuzz_user -d credbuzz_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor Redis memory
redis-cli INFO memory

# Check Celery queue size
celery -A credbuzzpay_backend inspect active_queues

# Monitor logs in real-time
tail -f debug.log
tail -f logs/gunicorn_error.log
```

---

## Debugging Tips

```python
# Print debug info in Django shell
python manage.py shell

# Test OTP generation
>>> from accounts.services.otp_service import OTPService
>>> service = OTPService()
>>> user = UserAccount.objects.first()
>>> otp = service.generate_otp_record(user, 'email_verification')
>>> print(otp.email_otp)  # See plaintext OTP

# Test encryption
>>> from accounts.utils.encryption import encrypt_data, decrypt_data
>>> encrypted = encrypt_data('123456789012')
>>> decrypted = decrypt_data(encrypted)

# Check user permissions
>>> user = UserAccount.objects.first()
>>> print(user.user_role)
>>> print(user.app_access_control.all())

# Query database
>>> from accounts.models import LoginActivity
>>> activities = LoginActivity.objects.filter(status='failed')
>>> print(activities.count())
```

---

## Common Error Solutions

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError` | Activate venv & install requirements |
| `ProgrammingError: relation does not exist` | Run `python manage.py migrate` |
| `ConnectionRefusedError: Redis` | Start Redis: `redis-server` |
| `401 Unauthorized` | Check JWT token in Authorization header |
| `403 Forbidden` | Verify user has required permissions |
| `CORS Error` | Configure CORS_ALLOWED_ORIGINS in settings |
| `504 Gateway Timeout` | Optimize database queries or increase timeout |
| `Celery tasks not executing` | Start worker: `celery -A credbuzzpay_backend worker` |

---

## Important URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:8000` | Development server |
| `http://localhost:8000/admin` | Django admin |
| `http://localhost:8000/api/v1` | API root |
| `http://localhost:8000/api/schema/swagger` | Swagger documentation |
| `http://localhost:5555` | Celery Flower (monitoring) |
| `http://localhost:5000` | PostgreSQL (remote connection) |
| `http://localhost:6379` | Redis (default) |

---

## Security Checklist

- [ ] Change default `SECRET_KEY` in production
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` with actual domain
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure CORS for specific origins only
- [ ] Set strong database password
- [ ] Enable rate limiting on sensitive endpoints
- [ ] Configure firewall rules
- [ ] Enable automated backups
- [ ] Monitor audit trails regularly
- [ ] Update dependencies regularly
- [ ] Implement proper logging and monitoring
- [ ] Use strong encryption keys
- [ ] Rotate JWT tokens properly
- [ ] Implement request signing for sensitive operations

---

## Performance Optimization Checklist

- [ ] Enable database query caching
- [ ] Use Redis for session storage
- [ ] Implement pagination on list endpoints
- [ ] Add database indexes on frequently queried fields
- [ ] Use select_related/prefetch_related for relationships
- [ ] Implement API response compression (Gzip)
- [ ] Use CDN for static files
- [ ] Enable HTTP caching headers
- [ ] Monitor and optimize slow queries
- [ ] Use Celery for long-running tasks
- [ ] Implement request rate limiting
- [ ] Monitor and optimize memory usage
- [ ] Use connection pooling for database
- [ ] Implement query result caching

---

## Useful Resources

### Django Documentation
- https://docs.djangoproject.com
- https://www.django-rest-framework.org

### Security
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Security: https://docs.djangoproject.com/en/stable/topics/security/

### Performance
- Django Performance Optimization: https://docs.djangoproject.com/en/stable/topics/performance/
- PostgreSQL Documentation: https://www.postgresql.org/docs/

### Tools
- Postman: https://www.postman.com
- Redis CLI: https://redis.io/cli/
- Celery: https://docs.celeryproject.io
- Flower: https://flower.readthedocs.io

---

**Last Updated:** November 2025
**Version:** 1.0.0

---

## Support & Contribution

For issues, bugs, or feature requests:
1. Check the TROUBLESHOOTING.md guide
2. Review existing issues on GitHub
3. Create a detailed issue with reproduction steps
4. Follow contributing guidelines in CONTRIBUTING.md

---
