# Deployment Guide - CredbuzzPay ERP System

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [AWS Deployment](#aws-deployment)
5. [Database Setup](#database-setup)
6. [Redis Cache Setup](#redis-cache-setup)
7. [Celery Workers](#celery-workers)
8. [SSL/TLS Configuration](#ssltls-configuration)
9. [Monitoring & Logging](#monitoring--logging)
10. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 12+ or SQLite
- Redis 7+
- Git

### Step-by-Step Setup

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/credbuzz-backend.git
cd credbuzz-backend
```

#### 2. Create Virtual Environment

```bash
python -m venv credbuzz_backend_venv
source credbuzz_backend_venv/bin/activate  # On Windows: credbuzz_backend_venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your development settings
nano .env
```

#### 5. Initialize Database

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

#### 6. Create Superuser

```bash
python manage.py createsuperuser
```

#### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### 8. Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

#### 9. Run Celery Worker (in new terminal)

```bash
celery -A credbuzzpay_backend worker -l info
```

#### 10. Run Celery Beat (in another new terminal)

```bash
celery -A credbuzzpay_backend beat -l info
```

Access the application at: `http://localhost:8000`

Admin panel: `http://localhost:8000/admin`

API docs: `http://localhost:8000/api/schema/swagger/`

---

## Production Deployment

### Environment Configuration

Create production `.env` file:

```bash
# Django
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ENVIRONMENT=production

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=credbuzz_prod
DB_USER=postgres
DB_PASSWORD=secure-password
DB_HOST=db.yourdomain.com
DB_PORT=5432

# Redis
REDIS_URL=redis://redis.yourdomain.com:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# SMS Configuration
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Third-party Services
SENTRY_DSN=your-sentry-dsn
STRIPE_SECRET_KEY=your-stripe-secret-key
```

### 1. Server Setup

#### Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
sudo apt-get install -y postgresql postgresql-contrib
sudo apt-get install -y redis-server
sudo apt-get install -y nginx
sudo apt-get install -y supervisor
sudo apt-get install -y git
```

#### Create Application User

```bash
sudo useradd -m -s /bin/bash credbuzz
sudo su - credbuzz
```

#### Clone Application

```bash
cd /home/credbuzz
git clone https://github.com/yourusername/credbuzz-backend.git
cd credbuzz-backend
```

### 2. PostgreSQL Setup

```bash
sudo -u postgres psql
CREATE DATABASE credbuzz_prod;
CREATE USER credbuzz_user WITH PASSWORD 'secure_password';
ALTER ROLE credbuzz_user SET client_encoding TO 'utf8';
ALTER ROLE credbuzz_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE credbuzz_user SET default_transaction_deferrable TO on;
ALTER ROLE credbuzz_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE credbuzz_prod TO credbuzz_user;
\q
```

### 3. Django Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

```bash
cp .env.example .env
nano .env  # Edit with production values
```

Run migrations:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 4. Gunicorn Configuration

Create `/home/credbuzz/credbuzz-backend/gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8001"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
access_log = "/home/credbuzz/credbuzz-backend/logs/gunicorn_access.log"
error_log = "/home/credbuzz/credbuzz-backend/logs/gunicorn_error.log"
```

### 5. Supervisor Configuration

Create `/etc/supervisor/conf.d/credbuzz.conf`:

```ini
[program:credbuzz-django]
command=/home/credbuzz/credbuzz-backend/venv/bin/gunicorn -c /home/credbuzz/credbuzz-backend/gunicorn_config.py credbuzzpay_backend.wsgi
directory=/home/credbuzz/credbuzz-backend
user=credbuzz
environment=PATH="/home/credbuzz/credbuzz-backend/venv/bin"
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/credbuzz/credbuzz-backend/logs/supervisor.log
numprocs=1
priority=999

[program:credbuzz-celery]
command=/home/credbuzz/credbuzz-backend/venv/bin/celery -A credbuzzpay_backend worker -l info
directory=/home/credbuzz/credbuzz-backend
user=credbuzz
environment=PATH="/home/credbuzz/credbuzz-backend/venv/bin"
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/credbuzz/credbuzz-backend/logs/celery.log
numprocs=1
priority=998

[program:credbuzz-celery-beat]
command=/home/credbuzz/credbuzz-backend/venv/bin/celery -A credbuzzpay_backend beat -l info
directory=/home/credbuzz/credbuzz-backend
user=credbuzz
environment=PATH="/home/credbuzz/credbuzz-backend/venv/bin"
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/credbuzz/credbuzz-backend/logs/celery_beat.log
numprocs=1
priority=997
```

Start services:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### 6. Nginx Configuration

Create `/etc/nginx/sites-available/credbuzz`:

```nginx
upstream credbuzz_app {
    server 127.0.0.1:8001;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Certificate Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/xml+rss
               application/javascript application/json;

    # Client Upload Limit
    client_max_body_size 20M;

    # Static Files
    location /static/ {
        alias /home/credbuzz/credbuzz-backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media Files
    location /media/ {
        alias /home/credbuzz/credbuzz-backend/media/;
        expires 7d;
    }

    # API Proxy
    location / {
        proxy_pass http://credbuzz_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # Health Check Endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/credbuzz /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

Auto-renewal:

```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 credbuzz && chown -R credbuzz:credbuzz /app
USER credbuzz

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "-b", "0.0.0.0:8000", "credbuzzpay_backend.wsgi:application"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    environment:
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn -b 0.0.0.0:8000 credbuzzpay_backend.wsgi:application"
    volumes:
      - ./:/app

  celery:
    build: .
    environment:
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      - web
    command: celery -A credbuzzpay_backend worker -l info
    volumes:
      - ./:/app

  celery-beat:
    build: .
    environment:
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      - web
    command: celery -A credbuzzpay_backend beat -l info
    volumes:
      - ./:/app

volumes:
  postgres_data:
```

Run with Docker Compose:

```bash
docker-compose up -d
docker-compose logs -f web
```

---

## AWS Deployment

### Using AWS EC2 + RDS + ElastiCache

#### 1. Launch EC2 Instance

```bash
# Ubuntu 22.04 LTS
Instance Type: t3.medium (minimum)
Storage: 30GB SSD
Security Group: Allow ports 22, 80, 443
```

#### 2. RDS PostgreSQL

```bash
# Create database
Engine: PostgreSQL 15
Instance: db.t3.small
Storage: 100GB SSD
Multi-AZ: Yes (for production)
Backup: 30 days retention
```

#### 3. ElastiCache Redis

```bash
# Create Redis cluster
Engine: Redis 7
Node Type: cache.t3.small
Number of Nodes: 1 (or 3 for cluster mode)
Backup: Daily
```

#### 4. Application Load Balancer

```yaml
Listeners: 
  - Port 80 → 8000 (redirect to HTTPS)
  - Port 443 → 8000 (HTTPS)
Certificate: ACM SSL certificate
```

#### 5. Auto Scaling Group

```yaml
Min Capacity: 2
Max Capacity: 10
Desired Capacity: 2
Scale Up: CPU > 70%
Scale Down: CPU < 30%
```

#### 6. Environment Variables (AWS Systems Manager Parameter Store)

```bash
aws ssm put-parameter --name /credbuzz/db-url --value "postgresql://..." --type String
aws ssm put-parameter --name /credbuzz/redis-url --value "redis://..." --type String
aws ssm put-parameter --name /credbuzz/secret-key --value "..." --type SecureString
```

---

## Database Setup

### PostgreSQL Setup Script

Create `scripts/setup_db.sh`:

```bash
#!/bin/bash

# Create database
sudo -u postgres psql << EOF
CREATE DATABASE credbuzz;
CREATE USER credbuzz_user WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE credbuzz_user SET client_encoding TO 'utf8';
ALTER ROLE credbuzz_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE credbuzz TO credbuzz_user;
EOF

# Run migrations
python manage.py migrate

# Create superuser (interactive)
python manage.py createsuperuser

# Load initial data
python manage.py loaddata fixtures/initial_data.json
```

Run migrations:

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

Create superuser:

```bash
python manage.py createsuperuser
```

---

## Redis Cache Setup

### Install Redis

```bash
# Ubuntu/Debian
sudo apt-get install -y redis-server

# CentOS/RHEL
sudo yum install -y redis

# macOS
brew install redis
```

### Configure Redis

Edit `/etc/redis/redis.conf`:

```
# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Security
requirepass your-redis-password

# AOF
appendonly yes
appendfilename "appendonly.aof"
```

Start service:

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

Verify:

```bash
redis-cli ping
# Output: PONG
```

---

## Celery Workers

### Development

```bash
# Terminal 1: Worker
celery -A credbuzzpay_backend worker -l info

# Terminal 2: Beat Scheduler
celery -A credbuzzpay_backend beat -l info
```

### Production (Supervisor)

See Supervisor configuration above.

### Monitoring

```bash
# Celery Flower (Web UI)
pip install flower
celery -A credbuzzpay_backend flower

# Access at: http://localhost:5555
```

---

## SSL/TLS Configuration

### Self-Signed Certificate (Development)

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### Let's Encrypt (Production)

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com
```

### Django Settings

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

---

## Monitoring & Logging

### Setup Sentry Error Tracking

```bash
pip install sentry-sdk

# In settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
```

### Application Logging

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

### Health Check Endpoint

```python
# urls.py
path('health/', lambda request: JsonResponse({'status': 'ok'}))
```

---

## Troubleshooting

### Celery Not Processing Tasks

```bash
# Check Redis connection
redis-cli ping

# Check Celery worker status
celery -A credbuzzpay_backend inspect active

# Check scheduled tasks
celery -A credbuzzpay_backend inspect scheduled

# Purge all tasks
celery -A credbuzzpay_backend purge
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U credbuzz_user -d credbuzz_prod -h localhost

# Check Django settings
python manage.py dbshell

# Run migrations
python manage.py showmigrations
```

### Static Files Not Loading

```bash
python manage.py collectstatic --noinput
python manage.py collectstatic --noinput --clear
```

### Memory Issues

```bash
# Monitor Redis memory
redis-cli info memory

# Clear Redis cache
redis-cli FLUSHALL

# Limit Celery workers
celery -A credbuzzpay_backend worker -l info --concurrency=2
```

---

**Last Updated:** November 2025
**Version:** 1.0.0
