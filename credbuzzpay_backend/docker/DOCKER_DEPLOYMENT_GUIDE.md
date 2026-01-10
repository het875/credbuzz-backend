# 🐳 CredBuzz Backend - Docker Deployment Guide for Ubuntu

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Installing Docker](#installing-docker)
4. [Project Setup](#project-setup)
5. [Configuration](#configuration)
6. [Building and Running](#building-and-running)
7. [Database Setup](#database-setup)
8. [SSL/HTTPS Setup (Optional)](#ssl-https-setup)
9. [Monitoring and Logs](#monitoring-and-logs)
10. [Troubleshooting](#troubleshooting)
11. [Useful Commands](#useful-commands)

---

## 📦 Prerequisites

Before starting, ensure you have:
- Fresh Ubuntu server (20.04 LTS or 22.04 LTS recommended)
- Root or sudo access
- Git installed
- Domain name (optional, but recommended for production)
- Minimum 2GB RAM, 20GB disk space

---

## 🖥️ Server Setup

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Basic Dependencies

```bash
sudo apt install -y \
    curl \
    wget \
    git \
    ufw \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
```

### 3. Configure Firewall

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Django dev port (optional, for testing)
sudo ufw allow 8000/tcp

# Check status
sudo ufw status
```

---

## 🐋 Installing Docker

### 1. Install Docker Engine

```bash
# Remove old versions (if any)
sudo apt remove docker docker-engine docker.io containerd runc

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
sudo docker --version
```

### 2. Install Docker Compose (Standalone)

```bash
# Download latest version
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### 3. Configure Docker (Optional but Recommended)

```bash
# Add current user to docker group (avoid using sudo)
sudo usermod -aG docker $USER

# Apply group changes (logout and login, or run)
newgrp docker

# Verify you can run docker without sudo
docker ps
```

---

## 📂 Project Setup

### 1. Clone Your Repository

```bash
# Create application directory
sudo mkdir -p /var/www
cd /var/www

# Clone repository
sudo git clone https://github.com/het875/credbuzz-backend.git

# Navigate to project directory
cd credbuzz-backend/credbuzz-backend/credbuzzpay_backend

# Set proper permissions
sudo chown -R $USER:$USER /var/www/credbuzz-backend
```

### 2. Checkout Branch (if needed)

```bash
# If you're using a specific branch (e.g., by_pass_otp)
git checkout by_pass_otp

# Or pull latest from main
git pull origin main
```

---

## ⚙️ Configuration

### 1. Create Environment File

```bash
# Copy example environment file
cp .env.docker.example .env.docker

# Edit with your production values
nano .env.docker
```

### 2. Update .env.docker with Production Values

**CRITICAL SETTINGS TO CHANGE:**

```bash
# Generate SECRET_KEY (run this on your server)
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Then update .env.docker:
DEBUG=False
SECRET_KEY=your-generated-secret-key-here
JWT_SECRET_KEY=another-different-secret-key-here
ALLOWED_HOSTS=your-server-ip,yourdomain.com,localhost

# Database settings
DATABASE_NAME=credbuzz_db
DATABASE_USER=credbuzz_user
DATABASE_PASSWORD=your-strong-password-here

# Email settings (use your actual email credentials)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# CORS (update with your frontend URL)
CORS_ALLOWED_ORIGINS=http://your-frontend-ip,https://yourdomain.com
```

### 3. Create Required Directories

```bash
# Create directories for volumes
mkdir -p staticfiles media logs

# Set permissions
chmod -R 755 staticfiles media logs
```

---

## 🚀 Building and Running

### 1. Build Docker Images

```bash
# Build the Docker image (this may take 5-10 minutes)
docker-compose build

# Or build without cache (if you made changes)
docker-compose build --no-cache
```

### 2. Start Services

```bash
# Start all services in detached mode
docker-compose up -d

# Check if containers are running
docker-compose ps

# You should see 4 services running:
# - credbuzz-db (PostgreSQL)
# - credbuzz-redis (Redis)
# - credbuzz-backend (Django)
# - credbuzz-nginx (Nginx)
```

### 3. View Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f web
```

---

## 🗄️ Database Setup

### 1. Run Migrations

```bash
# Access Django container
docker-compose exec web python manage.py migrate

# Or run as one command
docker-compose exec web sh -c "python manage.py migrate"
```

### 2. Create Superuser

```bash
# Create Django superuser
docker-compose exec web python manage.py createsuperuser

# Follow the prompts to create your admin account
```

### 3. Collect Static Files

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 4. Create Initial Developer User (Optional)

```bash
# Access Django shell
docker-compose exec web python manage.py shell

# Run the following in Python shell:
from users_auth.models import User

# Create developer user
dev_user = User(
    email='dev@credbuzz.com',
    username='developer',
    first_name='Developer',
    last_name='User',
    user_role='DEVELOPER',
    is_active=True,
    is_verified=True,
    is_email_verified=True,
    is_phone_verified=True
)
dev_user.set_password('YourStrongPassword123!')
dev_user.save()
print(f"Developer user created: {dev_user.email}")
exit()
```

---

## 🔒 SSL/HTTPS Setup (Optional but Recommended)

### Option 1: Using Certbot with Nginx

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx container temporarily
docker-compose stop nginx

# Get SSL certificate (replace with your domain)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Update nginx.conf to use SSL certificates
# Edit nginx.conf and add SSL configuration

# Restart nginx
docker-compose up -d nginx
```

### Option 2: Using Let's Encrypt in Docker

See separate documentation for automated SSL with Docker.

---

## 📊 Monitoring and Logs

### 1. Check Container Health

```bash
# Check container status
docker-compose ps

# Check container health
docker inspect --format='{{.State.Health.Status}}' credbuzz-backend

# View resource usage
docker stats
```

### 2. View Application Logs

```bash
# Django logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 web
```

### 3. Access Django Shell

```bash
# Python shell
docker-compose exec web python manage.py shell

# Database shell
docker-compose exec web python manage.py dbshell
```

---

## 🐛 Troubleshooting

### Issue: Container Won't Start

```bash
# Check logs
docker-compose logs web

# Check if port is already in use
sudo netstat -tulpn | grep :8000

# Restart services
docker-compose restart

# Complete rebuild
docker-compose down
docker-compose up -d --build
```

### Issue: Database Connection Error

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Access database container
docker-compose exec db psql -U credbuzz_user -d credbuzz_db

# Test connection from web container
docker-compose exec web python manage.py dbshell
```

### Issue: Permission Denied

```bash
# Fix file permissions
sudo chown -R $USER:$USER /var/www/credbuzz-backend

# Fix volume permissions
docker-compose exec web chown -R appuser:appuser /app/staticfiles /app/media
```

### Issue: Out of Disk Space

```bash
# Clean up Docker
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Check disk usage
df -h
```

---

## 🛠️ Useful Commands

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove everything including volumes
docker-compose down -v

# Rebuild and start
docker-compose up -d --build

# View running containers
docker-compose ps

# Execute command in container
docker-compose exec web python manage.py <command>

# Access bash in container
docker-compose exec web bash
```

### Django Management Commands

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Shell
docker-compose exec web python manage.py shell

# Database shell
docker-compose exec web python manage.py dbshell

# Check deployment
docker-compose exec web python manage.py check --deploy
```

### Database Commands

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U credbuzz_user -d credbuzz_db

# Backup database
docker-compose exec db pg_dump -U credbuzz_user credbuzz_db > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U credbuzz_user -d credbuzz_db

# List databases
docker-compose exec db psql -U credbuzz_user -c "\l"
```

### Logs and Monitoring

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 web

# Specific service logs
docker-compose logs web
docker-compose logs db
docker-compose logs nginx

# Container stats
docker stats

# Inspect container
docker inspect credbuzz-backend
```

---

## 🔄 Updating and Redeploying

### 1. Pull Latest Changes

```bash
cd /var/www/credbuzz-backend/credbuzz-backend/credbuzzpay_backend

# Pull latest code
git pull origin main

# Or specific branch
git pull origin by_pass_otp
```

### 2. Rebuild and Restart

```bash
# Rebuild image
docker-compose build

# Restart services
docker-compose up -d

# Run migrations (if any)
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

---

## 🔐 Security Best Practices

1. **Always use strong passwords** for:
   - SECRET_KEY
   - JWT_SECRET_KEY
   - Database passwords
   - Email passwords

2. **Enable firewall (UFW)**:
   ```bash
   sudo ufw enable
   sudo ufw allow 80,443/tcp
   ```

3. **Use SSL/HTTPS in production** with Certbot or Let's Encrypt

4. **Keep Docker and system updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker-compose pull
   ```

5. **Regular backups**:
   - Database backups
   - Media files backups
   - Environment files backup

6. **Monitor logs regularly**:
   ```bash
   docker-compose logs -f
   ```

---

## 📞 Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Check documentation: `/docs/` directory
- GitHub Issues: https://github.com/het875/credbuzz-backend/issues

---

## ✅ Quick Start Checklist

- [ ] Ubuntu server prepared (2GB RAM minimum)
- [ ] Docker and Docker Compose installed
- [ ] Repository cloned to `/var/www/credbuzz-backend`
- [ ] `.env.docker` configured with production values
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] Docker images built (`docker-compose build`)
- [ ] Services started (`docker-compose up -d`)
- [ ] Migrations run (`docker-compose exec web python manage.py migrate`)
- [ ] Static files collected
- [ ] Superuser created
- [ ] Application accessible via browser
- [ ] SSL/HTTPS configured (recommended)

---

**🎉 Congratulations! Your CredBuzz Backend is now running with Docker on Ubuntu!**

Access your application at:
- **HTTP**: http://your-server-ip:8000
- **With Nginx**: http://your-server-ip
- **API Health Check**: http://your-server-ip:8000/api/health/
- **Admin Panel**: http://your-server-ip:8000/admin/
- **API Documentation**: http://your-server-ip:8000/swagger/
