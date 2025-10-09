# CredBuzz Backend AI Coding Guide

## Project Overview
This is a Django 5.2.6 backend for CredBuzz payment system, currently in early development phase. The project uses a hybrid architecture with both Django and FastAPI frameworks installed, suggesting plans for microservices or API gateway patterns.

## Project Structure
```
credbuzzpay_backend/    # Main Django project package
├── settings.py         # Django configuration
├── urls.py            # Main URL routing (currently only admin)
├── wsgi.py/asgi.py    # WSGI/ASGI application entry points
manage.py              # Django management script
db.sqlite3             # SQLite database (development)
credbuzz_backend_venv/ # Virtual environment
docs/                  # Documentation (empty)
logs/                  # Log files directory (empty)
```

## Development Environment

### Virtual Environment
- **Location**: `credbuzz_backend_venv/` (local to project)
- **Python**: 3.12.6
- **Activation**: Use VS Code's configured interpreter at `credbuzz_backend_venv/Scripts/python.exe`

### Key Dependencies
- **Django 5.2.6**: Primary web framework
- **FastAPI 0.116.0**: Likely for API endpoints or microservices
- **SQLAlchemy 2.0.41**: ORM (additional to Django's built-in ORM)
- **Pandas/NumPy**: Data processing capabilities
- **Selenium**: Web automation (testing/scraping)
- **APScheduler**: Task scheduling

## Development Patterns

### Django Configuration
- **Settings**: Standard Django setup in `credbuzzpay_backend/settings.py`
- **Database**: SQLite for development (production DB likely different)
- **Debug**: Currently enabled (`DEBUG = True`)
- **Apps**: Only Django built-ins registered - custom apps need to be added to `INSTALLED_APPS`

### Database & Models
- No custom Django apps created yet
- No models.py files exist
- Database migrations haven't been run (empty db.sqlite3)
- Consider using either Django ORM or SQLAlchemy (both installed)

### URL Routing
- Main URLs in `credbuzzpay_backend/urls.py` (currently only admin)
- No API endpoints defined yet
- FastAPI routes would be separate from Django URLs

## Development Workflow

### Running the Application
```bash
# Activate virtual environment (if not using VS Code)
credbuzz_backend_venv\Scripts\activate

# Run Django development server
python manage.py runserver

# Database migrations (when models are created)
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser
```

### Common Tasks
- **New Django App**: `python manage.py startapp <app_name>`
- **FastAPI Integration**: Consider mounting FastAPI app in Django URLs or running separately
- **Database**: Currently empty - migrations needed when models are added

## Code Conventions

### File Organization
- Follow Django app structure for backend logic
- Keep FastAPI routes separate from Django views
- Use `docs/` for API documentation
- Use `logs/` for application logging

### Security Notes
- Secret key is hardcoded (change for production)
- Debug mode enabled (disable for production)
- No CORS headers configured yet (django-cors-headers installed)
- No authentication endpoints configured

## Integration Points

### Hybrid Architecture
- Django for admin, ORM, and traditional web features
- FastAPI likely for high-performance API endpoints
- SQLAlchemy suggests complex data operations beyond Django ORM

### External Dependencies
- Selenium setup suggests web scraping or testing automation
- APScheduler for background tasks
- Pandas/NumPy for data processing pipelines

## Next Development Steps
1. Create Django apps for core business logic
2. Define models and run initial migrations
3. Set up FastAPI integration strategy
4. Configure proper logging and environment variables
5. Add authentication and CORS configuration
6. Create API documentation structure

## Testing
- No test files exist yet
- Consider pytest for FastAPI and Django's test framework
- Selenium tests likely for frontend integration

## Deployment Considerations
- Environment variables needed for production settings
- Database migration strategy for production
- Static file serving configuration
- ASGI server setup for both Django and FastAPI