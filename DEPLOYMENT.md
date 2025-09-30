# ERP System Deployment Guide

## Overview

This guide covers the deployment of the Django ERP system for both development and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Database Setup](#database-setup)
7. [Security Considerations](#security-considerations)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.9 or higher
- pip (Python package manager)
- Git
- Virtual environment tool (venv or virtualenv)

### For Production
- Linux server (Ubuntu 20.04+ recommended)
- Nginx (web server)
- PostgreSQL or MySQL (database)
- Redis (caching and sessions)
- SSL certificate
- Domain name

## Development Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd credbuzz-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create `.env` file in the project root:
```env
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# SMS Configuration
FAST2SMS_API_KEY=your-fast2sms-api-key

# Security
ENCRYPTION_KEY=generate-with-cryptography-fernet
JWT_SECRET_KEY=your-jwt-secret-key

# Media Files
MEDIA_ROOT=media/
MEDIA_URL=/media/

# Logging
LOG_LEVEL=INFO
```

### 5. Database Setup
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create initial data
python manage.py shell
```

In Django shell:
```python
from erp.models import Branch, AppFeature

# Create branches
branches_data = [
    {
        'branch_code': 'MUM001',
        'branch_name': 'Mumbai Central Branch',
        'address_line1': '123 Business District',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'pincode': '400001',
        'phone': '9876543210',
        'email': 'mumbai@credbuzz.com'
    },
    {
        'branch_code': 'DEL001',
        'branch_name': 'Delhi Branch',
        'address_line1': '456 Connaught Place',
        'city': 'New Delhi',
        'state': 'Delhi',
        'pincode': '110001',
        'phone': '9876543211',
        'email': 'delhi@credbuzz.com'
    }
]

for branch_data in branches_data:
    Branch.objects.get_or_create(**branch_data)

# Create app features
features_data = [
    {'feature_code': 'USER_MANAGEMENT', 'feature_name': 'User Management', 'description': 'Manage users and roles'},
    {'feature_code': 'KYC_VERIFICATION', 'feature_name': 'KYC Verification', 'description': 'Handle KYC documents'},
    {'feature_code': 'BUSINESS_ONBOARDING', 'feature_name': 'Business Onboarding', 'description': 'Manage business details'},
    {'feature_code': 'REPORTS', 'feature_name': 'Reports & Analytics', 'description': 'Generate system reports'},
    {'feature_code': 'AUDIT_TRAIL', 'feature_name': 'Audit Trail', 'description': 'Track system activities'},
]

for feature_data in features_data:
    AppFeature.objects.get_or_create(**feature_data)

exit()
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

## Production Deployment

### 1. Server Setup (Ubuntu)

#### Update System
```bash
sudo apt update
sudo apt upgrade -y
```

#### Install Dependencies
```bash
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl -y
```

#### Create Application User
```bash
sudo adduser erp
sudo usermod -aG sudo erp
sudo su - erp
```

### 2. Application Setup

#### Clone Repository
```bash
cd /home/erp
git clone <repository-url> erp-system
cd erp-system
```

#### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

#### Production Environment File
Create `/home/erp/erp-system/.env`:
```env
# Django Settings
SECRET_KEY=generate-secure-random-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database (PostgreSQL)
DATABASE_URL=postgresql://erp_user:secure_password@localhost/erp_db

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# SMS Configuration
FAST2SMS_API_KEY=your-production-api-key

# Security
ENCRYPTION_KEY=generate-with-cryptography-fernet
JWT_SECRET_KEY=generate-secure-jwt-key

# Media and Static Files
MEDIA_ROOT=/home/erp/erp-system/media/
STATIC_ROOT=/home/erp/erp-system/static/
MEDIA_URL=/media/
STATIC_URL=/static/

# Cache and Sessions
REDIS_URL=redis://localhost:6379/0
SESSION_ENGINE=django.contrib.sessions.backends.cache
CACHE_BACKEND=redis_cache.RedisCache

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/erp/erp-system/logs/erp.log

# Security Headers
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY
```

### 3. Database Setup (PostgreSQL)

#### Create Database and User
```bash
sudo -u postgres psql

CREATE DATABASE erp_db;
CREATE USER erp_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE erp_db TO erp_user;
ALTER USER erp_user CREATEDB;
\q
```

#### Run Migrations
```bash
cd /home/erp/erp-system
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

#### Create Production Superuser
```bash
python manage.py createsuperuser
```

### 4. Gunicorn Configuration

Create `/home/erp/erp-system/gunicorn.conf.py`:
```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
user = "erp"
group = "erp"
tmp_upload_dir = None
errorlog = "/home/erp/erp-system/logs/gunicorn_error.log"
accesslog = "/home/erp/erp-system/logs/gunicorn_access.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
```

### 5. Systemd Service

Create `/etc/systemd/system/erp.service`:
```ini
[Unit]
Description=ERP System Gunicorn daemon
After=network.target

[Service]
User=erp
Group=erp
WorkingDirectory=/home/erp/erp-system
ExecStart=/home/erp/erp-system/venv/bin/gunicorn --config gunicorn.conf.py credbuzzpay_backend.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl enable erp
sudo systemctl start erp
sudo systemctl status erp
```

### 6. Nginx Configuration

Create `/etc/nginx/sites-available/erp`:
```nginx
upstream erp_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; media-src 'self'; object-src 'none'; child-src 'none'; worker-src 'none'; frame-ancestors 'none'; form-action 'self'; base-uri 'self';";

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    client_max_body_size 10M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://erp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /erp/auth/login/ {
        limit_req zone=login burst=10 nodelay;
        proxy_pass http://erp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/erp/erp-system/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /home/erp/erp-system/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Block access to sensitive files
    location ~ /\.(env|git|svn) {
        deny all;
        return 404;
    }

    location ~ /(logs|backups)/ {
        deny all;
        return 404;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Docker Deployment

### 1. Dockerfile
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        gcc \
        python3-dev \
        musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create directories
RUN mkdir -p /app/media /app/static /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "credbuzzpay_backend.wsgi:application"]
```

### 2. Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: erp_db
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: secure_password
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U erp_user -d erp_db"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=postgresql://erp_user:secure_password@db:5432/erp_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./media:/app/media
      - ./static:/app/static
      - /path/to/ssl/certs:/etc/ssl/certs
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  redis_data:
```

### 3. Deploy with Docker
```bash
# Build and start services
docker-compose up --build -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Check logs
docker-compose logs -f
```

## Environment Configuration

### Generate Secure Keys
```python
# Generate SECRET_KEY
import secrets
print(secrets.token_urlsafe(50))

# Generate ENCRYPTION_KEY
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())

# Generate JWT_SECRET_KEY
import secrets
print(secrets.token_urlsafe(32))
```

### Email Configuration (Gmail)
1. Enable 2-factor authentication
2. Generate App Password
3. Use App Password in EMAIL_HOST_PASSWORD

### SMS Configuration (Fast2SMS)
1. Register at Fast2SMS
2. Get API key from dashboard
3. Add to FAST2SMS_API_KEY

## Security Considerations

### 1. SSL/TLS Certificate
Use Let's Encrypt for free SSL certificates:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 2. Firewall Configuration
```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 3. Database Security
- Use strong passwords
- Restrict database access
- Regular backups
- Enable connection encryption

### 4. File Permissions
```bash
sudo chown -R erp:erp /home/erp/erp-system
sudo chmod -R 755 /home/erp/erp-system
sudo chmod 600 /home/erp/erp-system/.env
```

## Monitoring and Logging

### 1. Log Rotation
Create `/etc/logrotate.d/erp`:
```
/home/erp/erp-system/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su erp erp
}
```

### 2. Health Check Endpoint
Create health check view in Django:
```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({"status": "healthy"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)
```

### 3. Monitoring Script
Create `/home/erp/monitor.sh`:
```bash
#!/bin/bash
# Check if services are running
if ! systemctl is-active --quiet erp; then
    systemctl restart erp
    echo "$(date): ERP service restarted" >> /home/erp/monitor.log
fi

if ! systemctl is-active --quiet nginx; then
    systemctl restart nginx
    echo "$(date): Nginx service restarted" >> /home/erp/monitor.log
fi
```

Add to crontab:
```bash
crontab -e
# Add line: */5 * * * * /home/erp/monitor.sh
```

## Backup and Recovery

### 1. Database Backup Script
Create `/home/erp/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/home/erp/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U erp_user erp_db > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /home/erp/erp-system/media

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "$(date): Backup completed" >> /home/erp/backup.log
```

Schedule daily backups:
```bash
crontab -e
# Add line: 0 2 * * * /home/erp/backup.sh
```

### 2. Database Recovery
```bash
# Restore database
psql -h localhost -U erp_user erp_db < /home/erp/backups/db_backup_YYYYMMDD_HHMMSS.sql

# Restore media files
cd /
tar -xzf /home/erp/backups/media_backup_YYYYMMDD_HHMMSS.tar.gz
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status erp

# Check logs
sudo journalctl -u erp -f

# Check application logs
tail -f /home/erp/erp-system/logs/erp.log
```

#### 2. Database Connection Issues
```bash
# Test database connection
sudo -u postgres psql -c "SELECT version();"

# Check if user can connect
psql -h localhost -U erp_user -d erp_db -c "SELECT 1;"
```

#### 3. File Permission Issues
```bash
# Fix ownership
sudo chown -R erp:erp /home/erp/erp-system

# Fix permissions
sudo chmod -R 755 /home/erp/erp-system
sudo chmod 600 /home/erp/erp-system/.env
```

#### 4. SSL Certificate Issues
```bash
# Test SSL certificate
openssl s_client -connect your-domain.com:443

# Renew certificate
sudo certbot renew --dry-run
```

### Performance Tuning

#### 1. Database Optimization
```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_useraccount_email ON erp_useraccount(email);
CREATE INDEX idx_useraccount_mobile ON erp_useraccount(mobile);
CREATE INDEX idx_loginactivity_user_id ON erp_loginactivity(user_id);
```

#### 2. Redis Configuration
```bash
# Add to /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

#### 3. Nginx Optimization
```nginx
# Add to server block
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

# Buffer sizes
client_body_buffer_size 16K;
client_header_buffer_size 1k;
large_client_header_buffers 2 1k;
```

## Maintenance

### Regular Tasks

#### Weekly
- Check system logs
- Verify backup integrity
- Update system packages
- Monitor disk space

#### Monthly
- Update Python packages
- Review security logs
- Check SSL certificate expiry
- Performance optimization

#### Quarterly
- Security audit
- Database optimization
- Documentation updates
- Disaster recovery testing

### Update Process
```bash
# Backup before update
/home/erp/backup.sh

# Update code
cd /home/erp/erp-system
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart erp
sudo systemctl restart nginx
```

This deployment guide provides comprehensive instructions for deploying the ERP system in various environments with proper security, monitoring, and maintenance procedures.