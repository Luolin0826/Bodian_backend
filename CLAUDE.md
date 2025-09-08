# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Development server**: `./dev.sh` or `python run.py` (starts Flask dev server on port 5000)
- **Production server**: `./manage.sh start` (uses Gunicorn with 4 gevent workers)
- **Stop server**: `./manage.sh stop`
- **Restart server**: `./manage.sh restart`
- **Check status**: `./manage.sh status`
- **View logs**: `./manage.sh logs`

### Testing
- **Run tests**: `./manage.sh test` or `python -m pytest tests/`
- **Test environment**: Set `FLASK_ENV=testing`

### Docker Development
- **Development container**: Use `Dockerfile.dev` (includes development tools like ipython, pytest, black, flake8)
- **Production container**: Use `Dockerfile.prod`

### Database Operations
- **Initialize database**: `python run.py` (creates tables automatically)
- **Database migrations**: Flask-Migrate is configured but no migration commands are predefined

## Architecture Overview

### Application Structure
This is a Flask-based REST API backend with the following architectural patterns:

**Application Factory Pattern**: The app is created using `create_app()` function in `app/__init__.py` with environment-based configuration.

**Blueprint-based Routing**: API endpoints are organized into feature-based blueprints:
- `/api/v1/auth` - Authentication (login, registration)
- `/api/v1/customers` - Customer management
- `/api/v1/scripts` - Script management
- `/api/v1/knowledge` - Knowledge base operations
- `/api/v1/stats` - Statistics and analytics

**Service Layer Pattern**: Business logic is separated into service classes in `app/services/`:
- `AuthService` - Authentication logic
- `CustomerService` - Customer operations

### Key Technologies
- **Web Framework**: Flask 3.0.0 with Flask-CORS for cross-origin requests
- **Database**: MySQL with SQLAlchemy ORM and Flask-Migrate
- **Authentication**: JWT tokens via Flask-JWT-Extended
- **Production Server**: Gunicorn with gevent workers
- **Caching**: Redis integration (configured but usage depends on implementation)

### Database Models
Core models in `app/models/`:
- `User` - Authentication and user management
- `Customer` - Customer data with status tracking (潜在/跟进中/已成交/已流失)
- `Script` - Script/template management
- `KnowledgeBase` - Knowledge base entries

### Configuration
Environment-based configuration in `app/config/config.py`:
- **Development**: Debug enabled, SQL echo on
- **Production**: Debug disabled, optimized for performance
- **Database**: MySQL connection configured for Azure MySQL

### API Patterns
- All API routes use `/api/v1/` prefix
- CORS configured for `localhost:13686` and wildcard localhost ports
- Health check endpoint at `/api/health`
- Consistent error handling with JSON responses

### Environment Variables
Key environment variables:
- `FLASK_ENV`: development/production/testing
- `DATABASE_URL`: MySQL connection string
- `JWT_SECRET_KEY`: JWT token secret
- `REDIS_URL`: Redis connection string

### Logging
Structured logging to files:
- Access logs: `./logs/access.log`
- Error logs: `./logs/error.log`