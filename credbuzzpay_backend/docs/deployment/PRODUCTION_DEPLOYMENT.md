# Production Deployment Guide for CredBuzz Backend
**Server IP:** 80.225.194.105

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Server Setup](#initial-server-setup)
3. [Application Setup](#application-setup)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Maintenance](#maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### On Production Server
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.9+
- PostgreSQL 12+ (recommended) or SQLite
- Nginx
- Git
- sudo access

---

## Initial Server Setup

### 1. Connect to Your Server
```bash
ssh root@80.225.194.105
# or
ssh your-user@80.225.194.105
```

### 2. Update System Packages
```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Install Required System Packages
```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    nginx git supervisor postgresql postgresql-contrib \
    libpq-dev build-essential
```

### 4. Create Application User (Optional but Recommended)
```bash
sudo adduser --system --group --home /var/www/credbuzz-backend credbuzz
```

---

## Application Setup

### 1. Create Project Directory
```bash
sudo mkdir -p /var/www/credbuzz-backend
cd /var/www/credbuzz-backend
```

### 2. Clone Repository
```bash
# If using the existing user
sudo git clone https://github.com/het875/credbuzz-backend.git .

# Or if created credbuzz user
sudo -u credbuzz git clone https://github.com/het875/credbuzz-backend.git .
```

### 3. Set Proper Permissions
```bash
# If using www-data user
sudo chown -R www-data:www-data /var/www/credbuzz-backend

# Or if using credbuzz user
sudo chown -R credbuzz:credbuzz /var/www/credbuzz-backend
```

### 4. Navigate to Django Project
```bash
cd credbuzzpay_backend
```

### 5. Create Virtual Environment
```bash
python3 -m venv /var/www/credbuzz-backend/venv
source /var/www/credbuzz-backend/venv/bin/activate
```

### 6. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration

### 1. Setup Environment Variables
```bash
# Copy the production environment template
cp .env.production .env

# Edit the file with your actual values
nano .env
```

**Important variables to set in `.env`:**
```bash
DEBUG=False
SECRET_KEY=your-super-long-random-secret-key-here
ALLOWED_HOSTS=80.225.194.105,yourdomain.com
JWT_SECRET_KEY=another-different-random-secret-key

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://dbuser:dbpassword@localhost:5432/credbuzz_db

# CORS (add your frontend domain)
CORS_ALLOWED_ORIGINS=http://80.225.194.105,https://yourdomain.com

# Email settings (update with your actual credentials)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### 2. Generate SECRET_KEY
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Setup Database (PostgreSQL - Recommended)
```bash
# Switch to postgres user
sudo -u postgres psql

# Inside PostgreSQL prompt:
CREATE DATABASE credbuzz_db;
CREATE USER credbuzz_user WITH PASSWORD 'your-secure-password';
ALTER ROLE credbuzz_user SET client_encoding TO 'utf8';
ALTER ROLE credbuzz_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE credbuzz_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE credbuzz_db TO credbuzz_user;
\q
```

### 4. Run Migrations
```bash
source /var/www/credbuzz-backend/venv/bin/activate
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

---

## Running the Application

### 1. Setup Systemd Service

Copy the service file:
```bash
sudo cp credbuzz-backend.service /etc/systemd/system/
```

Edit the service file if needed:
```bash
sudo nano /etc/systemd/system/credbuzz-backend.service
```

**Update these lines to match your setup:**
- `User=www-data` (or your user)
- `Group=www-data` (or your group)

Reload systemd and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable credbuzz-backend
sudo systemctl start credbuzz-backend
sudo systemctl status credbuzz-backend
```

### 2. Setup Nginx

Copy the nginx configuration:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/credbuzz-backend
sudo ln -s /etc/nginx/sites-available/credbuzz-backend /etc/nginx/sites-enabled/
```

Test nginx configuration:
```bash
sudo nginx -t
```

If successful, reload nginx:
```bash
sudo systemctl reload nginx
```

### 3. Configure Firewall
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### 4. Test the Application
```bash
# Test health endpoint
curl http://80.225.194.105/health/

# Test API
curl http://80.225.194.105/api/v1/users/
```

---

## Maintenance

### View Logs
```bash
# Application logs
sudo journalctl -u credbuzz-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/credbuzz-backend-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/credbuzz-backend-error.log
```

### Deploy Updates
```bash
cd /var/www/credbuzz-backend/credbuzzpay_backend

# Pull latest code
git pull origin main

# Run deployment script
./deploy.sh

# Or manually:
source /var/www/credbuzz-backend/venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart credbuzz-backend
sudo systemctl reload nginx
```

### Backup Database
```bash
# PostgreSQL backup
sudo -u postgres pg_dump credbuzz_db > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite backup (if using SQLite)
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

---

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status credbuzz-backend
sudo systemctl status nginx
```

### Restart Services
```bash
sudo systemctl restart credbuzz-backend
sudo systemctl restart nginx
```

### Check for Port Conflicts
```bash
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :80
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/credbuzz-backend

# Fix permissions
sudo chmod -R 755 /var/www/credbuzz-backend
sudo chmod 600 /var/www/credbuzz-backend/credbuzzpay_backend/.env
```

### Database Connection Issues
```bash
# Test database connection
python manage.py dbshell

# Check PostgreSQL is running
sudo systemctl status postgresql
```

### Static Files Not Loading
```bash
# Re-collect static files
python manage.py collectstatic --clear --noinput

# Check nginx static file permissions
ls -la /var/www/credbuzz-backend/credbuzzpay_backend/staticfiles/
```

---

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY and JWT_SECRET_KEY
- [ ] ALLOWED_HOSTS configured correctly
- [ ] CORS_ALLOWED_ORIGINS restricted to your domains
- [ ] Database using PostgreSQL with strong password
- [ ] Firewall configured (UFW)
- [ ] Regular backups scheduled
- [ ] SSL/HTTPS certificate installed (Let's Encrypt recommended)
- [ ] Admin panel access restricted
- [ ] Environment variables file (.env) has secure permissions (600)
- [ ] Regular security updates applied

---

## Setting up SSL/HTTPS (Optional but Recommended)

### Using Let's Encrypt (Free)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## Quick Reference Commands

```bash
# Start/Stop/Restart services
sudo systemctl start credbuzz-backend
sudo systemctl stop credbuzz-backend
sudo systemctl restart credbuzz-backend
sudo systemctl status credbuzz-backend

# View logs
sudo journalctl -u credbuzz-backend -f
sudo tail -f /var/log/nginx/credbuzz-backend-error.log

# Django management
source /var/www/credbuzz-backend/venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

# Deploy updates
cd /var/www/credbuzz-backend/credbuzzpay_backend
./deploy.sh
```

---

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u credbuzz-backend -f`
2. Review nginx logs: `sudo tail -f /var/log/nginx/credbuzz-backend-error.log`
3. Verify all environment variables are set correctly
4. Ensure database is accessible

---

**Last Updated:** January 3, 2026
**Server IP:** 80.225.194.105
