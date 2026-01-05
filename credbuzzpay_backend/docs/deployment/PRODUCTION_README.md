# Production Files Summary - CredBuzz Backend
**Server IP:** 80.225.194.105

## Files Created/Modified for Production

### 1. **settings.py** ✅ MODIFIED
- Updated `ALLOWED_HOSTS` to use environment variable (default: `80.225.194.105`)
- Changed `DEBUG` to be controlled by environment variable
- Improved CORS settings for production security
- All security headers enabled when DEBUG=False

### 2. **.env.production** ✅ UPDATED
- Template for production environment variables
- Configured for server IP: 80.225.194.105
- Contains all necessary configuration options

### 3. **gunicorn_config.py** ✅ CREATED
- Production-ready Gunicorn configuration
- Auto-scales workers based on CPU cores
- Configured for optimal performance and security

### 4. **nginx.conf** ✅ CREATED
- Nginx reverse proxy configuration
- Static/media file serving
- Security headers
- Ready for SSL/HTTPS

### 5. **credbuzz-backend.service** ✅ CREATED
- Systemd service file
- Auto-starts on system boot
- Manages application lifecycle

### 6. **deploy.sh** ✅ CREATED
- Automated deployment script
- Handles migrations, static files, service restart
- Color-coded output for easy reading

### 7. **setup_production.sh** ✅ CREATED
- Complete server setup automation
- Installs all dependencies
- Configures database, nginx, services
- Interactive setup wizard

### 8. **PRODUCTION_DEPLOYMENT.md** ✅ CREATED
- Comprehensive deployment guide
- Step-by-step instructions
- Troubleshooting section
- Security checklist

---

## Quick Deployment Steps

### On Your Production Server (80.225.194.105)

#### Option 1: Automated Setup (Recommended for new servers)
```bash
# Upload files to server
scp -r credbuzzpay_backend root@80.225.194.105:/var/www/credbuzz-backend/

# SSH into server
ssh root@80.225.194.105

# Run setup script
cd /var/www/credbuzz-backend/credbuzzpay_backend
chmod +x setup_production.sh
sudo ./setup_production.sh
```

#### Option 2: Manual Setup
See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for detailed instructions.

---

## Critical Configuration Steps

### 1. Configure Environment Variables
```bash
cd /var/www/credbuzz-backend/credbuzzpay_backend
cp .env.production .env
nano .env
```

**Must Update:**
- `DEBUG=False`
- `SECRET_KEY=` (generate new random key)
- `JWT_SECRET_KEY=` (generate new random key)
- `ALLOWED_HOSTS=80.225.194.105,yourdomain.com`
- `DATABASE_URL=` (PostgreSQL recommended)
- `CORS_ALLOWED_ORIGINS=` (your frontend URL)

### 2. Generate Secret Keys
```bash
# Generate Django SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copy output and paste into .env file
```

### 3. Setup Database (PostgreSQL Recommended)
```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE credbuzz_db;
CREATE USER credbuzz_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE credbuzz_db TO credbuzz_user;
\q
```

Update `.env`:
```
DATABASE_URL=postgresql://credbuzz_user:your-secure-password@localhost:5432/credbuzz_db
```

### 4. Run Migrations
```bash
source /var/www/credbuzz-backend/venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 5. Start Services
```bash
# Copy service file
sudo cp credbuzz-backend.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable credbuzz-backend
sudo systemctl start credbuzz-backend

# Check status
sudo systemctl status credbuzz-backend
```

### 6. Configure Nginx
```bash
# Copy nginx config
sudo cp nginx.conf /etc/nginx/sites-available/credbuzz-backend
sudo ln -s /etc/nginx/sites-available/credbuzz-backend /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Configure Firewall
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

---

## Testing Deployment

### Health Check
```bash
curl http://80.225.194.105/health/
```

### API Test
```bash
curl http://80.225.194.105/api/v1/
```

### View Logs
```bash
# Application logs
sudo journalctl -u credbuzz-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/credbuzz-backend-error.log
```

---

## File Permissions Checklist

```bash
# Set ownership
sudo chown -R www-data:www-data /var/www/credbuzz-backend

# Secure .env file
sudo chmod 600 /var/www/credbuzz-backend/credbuzzpay_backend/.env

# Make scripts executable
chmod +x /var/www/credbuzz-backend/credbuzzpay_backend/deploy.sh
chmod +x /var/www/credbuzz-backend/credbuzzpay_backend/setup_production.sh
```

---

## Future Deployments

After initial setup, use the deployment script for updates:

```bash
cd /var/www/credbuzz-backend/credbuzzpay_backend
./deploy.sh
```

---

## Security Considerations

✅ **Implemented:**
- DEBUG=False in production
- ALLOWED_HOSTS restricted
- CORS origins restricted
- CSRF protection enabled
- Security headers configured
- Session security enabled
- HTTPS ready (SSL/TLS)

⚠️ **You Must Do:**
1. Change SECRET_KEY and JWT_SECRET_KEY
2. Use strong database passwords
3. Configure firewall (UFW)
4. Setup SSL certificate (Let's Encrypt)
5. Regular backups
6. Keep dependencies updated
7. Monitor logs regularly

---

## Common Commands Reference

```bash
# Service management
sudo systemctl start credbuzz-backend
sudo systemctl stop credbuzz-backend
sudo systemctl restart credbuzz-backend
sudo systemctl status credbuzz-backend

# View logs
sudo journalctl -u credbuzz-backend -f
sudo tail -f /var/log/nginx/credbuzz-backend-error.log

# Django commands
source /var/www/credbuzz-backend/venv/bin/activate
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser

# Deploy updates
cd /var/www/credbuzz-backend/credbuzzpay_backend
./deploy.sh
```

---

## Troubleshooting

### Service won't start
```bash
sudo journalctl -u credbuzz-backend -n 50
```

### Nginx errors
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Permission denied errors
```bash
sudo chown -R www-data:www-data /var/www/credbuzz-backend
```

### Database connection issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U credbuzz_user -d credbuzz_db
```

---

## Support & Documentation

- **Full Guide:** [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **Django Docs:** https://docs.djangoproject.com/
- **Gunicorn Docs:** https://docs.gunicorn.org/
- **Nginx Docs:** https://nginx.org/en/docs/

---

**Last Updated:** January 3, 2026  
**Server IP:** 80.225.194.105  
**Status:** Ready for Production Deployment
