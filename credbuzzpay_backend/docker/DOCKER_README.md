# CredBuzz Backend - Docker Quick Start Guide

## 🚀 Quick Deployment (TL;DR)

For those who want to get started quickly on Ubuntu:

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Clone and setup
cd /var/www
sudo git clone https://github.com/het875/credbuzz-backend.git
cd credbuzz-backend/credbuzz-backend/credbuzzpay_backend
sudo chown -R $USER:$USER .

# 4. Configure
cp .env.docker.example .env.docker
nano .env.docker  # Update SECRET_KEY, DATABASE_PASSWORD, etc.

# 5. Deploy
chmod +x deploy.sh
./deploy.sh build
./deploy.sh start

# 6. Create admin user
./deploy.sh superuser

# Done! Access at http://your-server-ip:8000
```

---

## 📂 What's Included

### Docker Files
- **`Dockerfile`** - Multi-stage Docker image for Django
- **`docker-compose.yml`** - Complete orchestration (Django + PostgreSQL + Redis + Nginx)
- **`.dockerignore`** - Excludes unnecessary files from image
- **`.env.docker.example`** - Template for environment variables

### Scripts
- **`deploy.sh`** - Automated deployment and management script

### Documentation
- **`docs/DOCKER_DEPLOYMENT_GUIDE.md`** - Complete deployment guide

---

## 🛠️ Using the deploy.sh Script

Make the script executable:
```bash
chmod +x deploy.sh
```

### Available Commands

```bash
# Build Docker images
./deploy.sh build

# Start all services
./deploy.sh start

# Stop services
./deploy.sh stop

# Restart services
./deploy.sh restart

# View logs
./deploy.sh logs

# Check status
./deploy.sh status

# Backup database
./deploy.sh backup

# Restore database
./deploy.sh restore backup_20240110_120000.sql

# Create superuser
./deploy.sh superuser

# Run migrations
./deploy.sh migrate

# Collect static files
./deploy.sh collectstatic

# Access Django shell
./deploy.sh shell

# Access container bash
./deploy.sh bash

# Clean up Docker
./deploy.sh clean

# Show help
./deploy.sh help
```

---

## 🔧 Configuration

### Essential Settings in .env.docker

```bash
# MUST CHANGE THESE:
DEBUG=False
SECRET_KEY=your-secret-key-here  # Generate with Django
JWT_SECRET_KEY=different-key-here
ALLOWED_HOSTS=your-ip,yourdomain.com
DATABASE_PASSWORD=strong-password-here
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Generate Secret Keys

```bash
# Generate Django SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate JWT_SECRET_KEY (use different key)
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 📊 Architecture

```
┌─────────────────────────────────────────────┐
│                  Nginx                      │
│         (Reverse Proxy & Static)            │
│              Port 80/443                    │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│            Django (Gunicorn)                │
│         CredBuzz Backend API                │
│              Port 8000                      │
└─────┬──────────────────────────────┬────────┘
      │                              │
┌─────▼──────────┐          ┌────────▼────────┐
│  PostgreSQL    │          │     Redis       │
│   Database     │          │   (Cache)       │
│   Port 5432    │          │   Port 6379     │
└────────────────┘          └─────────────────┘
```

---

## 📋 Port Mapping

| Service | Internal Port | External Port | Description |
|---------|---------------|---------------|-------------|
| Django  | 8000          | 8000          | API Application |
| PostgreSQL | 5432       | 5432          | Database |
| Redis   | 6379          | 6379          | Cache |
| Nginx   | 80            | 80            | HTTP |
| Nginx   | 443           | 443           | HTTPS |

---

## 🔍 Health Checks

All services include health checks:

```bash
# Check Django health
curl http://localhost:8000/api/health/

# Check container health
docker-compose ps

# Detailed health status
docker inspect --format='{{.State.Health.Status}}' credbuzz-backend
```

---

## 📝 Common Tasks

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
./deploy.sh build
./deploy.sh restart

# Run migrations
./deploy.sh migrate
```

### Database Backup & Restore

```bash
# Backup
./deploy.sh backup
# Creates: backup_YYYYMMDD_HHMMSS.sql

# Restore
./deploy.sh restore backup_20240110_120000.sql
```

### View Logs

```bash
# All services
./deploy.sh logs

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

### Access Containers

```bash
# Django shell
./deploy.sh shell

# Container bash
./deploy.sh bash

# Database shell
docker-compose exec db psql -U credbuzz_user -d credbuzz_db
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
./deploy.sh logs

# Check status
./deploy.sh status

# Restart services
./deploy.sh restart
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec web python manage.py dbshell
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R $USER:$USER /var/www/credbuzz-backend

# Fix container permissions
docker-compose exec web chown -R appuser:appuser /app/staticfiles /app/media
```

### Port Already in Use

```bash
# Find what's using the port
sudo netstat -tulpn | grep :8000

# Kill process using port
sudo kill -9 <PID>

# Or change port in docker-compose.yml
```

---

## 🔐 Security Checklist

- [ ] Changed all default passwords in .env.docker
- [ ] Generated strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Set DEBUG=False in production
- [ ] Configured firewall (UFW)
- [ ] Updated ALLOWED_HOSTS with your domain/IP
- [ ] Configured CORS_ALLOWED_ORIGINS
- [ ] Set up SSL/HTTPS (recommended)
- [ ] Regular backups configured
- [ ] Monitoring and logging enabled

---

## 📚 Additional Resources

- **Full Guide**: See `docs/DOCKER_DEPLOYMENT_GUIDE.md`
- **API Documentation**: http://your-server/swagger/
- **Admin Panel**: http://your-server/admin/
- **Health Check**: http://your-server/api/health/

---

## 🎯 Production Checklist

Before going live:

1. **Security**
   - [ ] SSL/HTTPS configured
   - [ ] Strong passwords set
   - [ ] Firewall configured
   - [ ] DEBUG=False

2. **Performance**
   - [ ] Static files collected
   - [ ] Database optimized
   - [ ] Redis configured
   - [ ] Nginx configured

3. **Reliability**
   - [ ] Backups automated
   - [ ] Monitoring setup
   - [ ] Logs configured
   - [ ] Health checks working

4. **Testing**
   - [ ] All APIs tested
   - [ ] Database migrations run
   - [ ] Static files served correctly
   - [ ] Email sending works

---

## 💡 Tips

1. **Always backup before updates**
   ```bash
   ./deploy.sh backup
   ```

2. **Monitor logs regularly**
   ```bash
   ./deploy.sh logs
   ```

3. **Keep Docker updated**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

4. **Use strong passwords**
   - Generate random passwords
   - Use different passwords for each service

5. **Enable SSL/HTTPS**
   - Use Certbot for free SSL
   - Redirect HTTP to HTTPS

---

## 📞 Support

For detailed documentation, see:
- `docs/DOCKER_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `docs/API_DOCUMENTATION.md` - API reference
- `docs/SETUP_GUIDE.md` - Development setup

---

**Made with ❤️ for CredBuzz Backend**
