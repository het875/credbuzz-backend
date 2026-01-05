# CredBuzz Backend - Setup Guide

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **pip** - Python package manager (comes with Python)
- **Git** - Version control system

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd credbuzz-backend
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv credbuzz_backend_venv
credbuzz_backend_venv\Scripts\activate

# Linux/macOS
python3 -m venv credbuzz_backend_venv
source credbuzz_backend_venv/bin/activate
```

### 3. Install Dependencies

```bash
cd credbuzzpay_backend
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install manually:

```bash
pip install django djangorestframework django-cors-headers pyjwt python-dotenv cryptography pillow
```

### 4. Environment Configuration

Create a `.env` file in the `credbuzzpay_backend` directory:

```env
# Django Settings
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (SQLite by default)
# For PostgreSQL:
# DATABASE_URL=postgres://user:password@localhost:5432/credbuzz

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Initialize Default Roles

```bash
python manage.py init_roles
```

This creates the 5 default system roles:
- Developer (Level 1)
- Super Admin (Level 2)
- Admin (Level 3)
- Client (Level 4)
- End User (Level 5)

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 8. Run Development Server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

## Project Structure

```
credbuzzpay_backend/
├── manage.py                 # Django management script
├── credbuzzpay_backend/      # Main project settings
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Root URL configuration
│   ├── asgi.py              # ASGI config
│   └── wsgi.py              # WSGI config
├── users_auth/              # Authentication app
│   ├── models.py            # User, PasswordResetToken, UserSession
│   ├── views.py             # Auth API views
│   ├── serializers.py       # DRF serializers
│   ├── urls.py              # Auth URL routes
│   ├── jwt_utils.py         # JWT token management
│   ├── authentication.py    # Custom JWT authentication
│   ├── admin.py             # Django admin config
│   └── tests.py             # Unit tests
├── rbac/                    # RBAC app
│   ├── models.py            # 8 RBAC models
│   ├── views.py             # RBAC API views
│   ├── serializers.py       # DRF serializers
│   ├── urls.py              # RBAC URL routes
│   ├── permissions.py       # Permission classes & helpers
│   ├── admin.py             # Django admin config
│   ├── tests.py             # Unit tests (45 tests)
│   └── management/
│       └── commands/
│           └── init_roles.py  # Initialize default roles
├── docs/                    # Documentation
│   ├── README.md            # Project overview
│   ├── DATABASE_SCHEMA.md   # Database documentation
│   ├── API_DOCUMENTATION.md # API reference
│   ├── RBAC_GUIDE.md        # RBAC usage guide
│   ├── SETUP_GUIDE.md       # This file
│   └── postman/             # Postman collections
└── db.sqlite3               # SQLite database (development)
```

## API Endpoints Overview

### Authentication (`/api/auth-user/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register/` | Register new user |
| POST | `/login/` | Login and get tokens |
| POST | `/logout/` | Logout and invalidate session |
| POST | `/refresh-token/` | Refresh access token |
| POST | `/forgot-password/` | Request password reset |
| POST | `/reset-password/` | Reset password with token |
| GET | `/me/` | Get current user profile |
| PUT | `/me/` | Update current user profile |
| GET | `/users/` | List all users |
| GET/PUT/DELETE | `/users/<id>/` | User CRUD |

### RBAC (`/api/rbac/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/roles/` | List/Create roles |
| GET/PUT/DELETE | `/roles/<id>/` | Role CRUD |
| GET/POST | `/apps/` | List/Create apps |
| GET/PUT/DELETE | `/apps/<id>/` | App CRUD |
| GET/POST | `/features/` | List/Create features |
| GET/PUT/DELETE | `/features/<id>/` | Feature CRUD |
| GET/POST | `/role-app-mappings/` | Role-App mappings |
| POST | `/role-app-mappings/bulk/` | Bulk assign apps |
| GET/POST | `/role-feature-mappings/` | Role-Feature mappings |
| POST | `/role-feature-mappings/bulk/` | Bulk assign features |
| GET/POST | `/user-role-assignments/` | User role assignments |
| POST | `/user-role-assignments/bulk/` | Bulk assign users |
| GET | `/my-permissions/` | Current user permissions |
| GET | `/check-permission/` | Check specific permission |
| GET | `/audit-logs/` | View audit logs |

## Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users_auth
python manage.py test rbac

# Run with verbosity
python manage.py test -v 2

# Run specific test class
python manage.py test rbac.tests.UserRoleTests

# Run with coverage (install coverage first)
pip install coverage
coverage run manage.py test
coverage report
coverage html  # Generate HTML report
```

## Using Postman

1. Import the collection from `docs/postman/CredBuzz_Backend_API.postman_collection.json`
2. Import the environment from `docs/postman/CredBuzz_Backend_Local.postman_environment.json`
3. Select "CredBuzz Backend - Local" environment
4. Run "Login" request to authenticate (tokens are auto-saved)
5. All other requests will use the saved token automatically

## Development Tips

### Adding New Migrations

```bash
python manage.py makemigrations <app_name>
python manage.py migrate
```

### Creating New App

```bash
python manage.py startapp <app_name>
```

Then add to `INSTALLED_APPS` in `settings.py`.

### Django Shell

```bash
python manage.py shell
```

```python
from users_auth.models import User
from rbac.models import UserRole, App, Feature

# Query examples
User.objects.all()
UserRole.objects.filter(level__gte=3)
```

### Reset Database (Development Only)

```bash
# Delete database and migrations
rm db.sqlite3
rm -rf users_auth/migrations/00*.py
rm -rf rbac/migrations/00*.py

# Recreate
python manage.py makemigrations users_auth
python manage.py makemigrations rbac
python manage.py migrate
python manage.py init_roles
python manage.py createsuperuser
```

## Production Deployment

### Environment Variables

Set these in production:

```env
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:pass@host:5432/dbname
```

### Collect Static Files

```bash
python manage.py collectstatic
```

### WSGI/ASGI Server

Use Gunicorn or uWSGI:

```bash
pip install gunicorn
gunicorn credbuzzpay_backend.wsgi:application --bind 0.0.0.0:8000
```

### Database

For production, switch to PostgreSQL:

```bash
pip install psycopg2-binary
```

Update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

## Troubleshooting

### ModuleNotFoundError

Ensure virtual environment is activated:
```bash
# Windows
credbuzz_backend_venv\Scripts\activate

# Linux/macOS
source credbuzz_backend_venv/bin/activate
```

### Migration Errors

```bash
python manage.py showmigrations  # Check status
python manage.py migrate --fake <app> zero  # Reset app migrations
python manage.py migrate
```

### JWT Token Issues

- Ensure `JWT_SECRET_KEY` is set in `.env`
- Check token expiration times
- Verify token format in Authorization header: `Bearer <token>`

### Permission Denied (403)

1. Check user has valid access token
2. Verify user has required role level
3. Check role has required app/feature permissions
4. Review RBAC_GUIDE.md for permission system details

## Support

For issues or questions:
1. Check documentation in `/docs` folder
2. Review test files for usage examples
3. Check Django admin at `/admin/` for data management
