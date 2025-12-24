# Authentication System Setup Guide

This guide covers the complete authentication system implementation for the AI Book backend using FastAPI, SQLModel, and JWT tokens.

## Overview

The authentication system provides:

- **User Registration & Login** with email/password
- **JWT Token Management** with access and refresh tokens
- **Email Verification** for new accounts
- **Password Reset** functionality
- **OAuth Integration** (Google, GitHub)
- **Role-Based Access Control** (RBAC)
- **Session Management** with secure cookies
- **Rate Limiting** and security features

## Architecture

```
backend/
├── src/
│   ├── core/
│   │   ├── config.py          # Environment configuration
│   │   ├── database.py        # Database connection setup
│   │   └── security.py        # JWT and password utilities
│   ├── models/
│   │   ├── user.py            # User and auth models (SQLModel)
│   │   └── chat.py            # Chat models
│   ├── services/
│   │   ├── auth_service.py    # Authentication business logic
│   │   └── email.py           # Email sending service
│   ├── api/v1/
│   │   └── auth.py            # FastAPI auth endpoints
│   └── middleware/
│       └── auth_middleware.py # Authentication middleware
├── alembic/                   # Database migrations
└── scripts/
    └── manage_migrations.py   # Migration management
```

## Quick Setup

### 1. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Update the following essential variables in `.env`:

```env
# Generate a strong secret key
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-at-least-32-characters-long

# Database URL (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite+aiosqlite:///./database/auth.db

# Email configuration (required for verification)
EMAIL_SERVICE=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
```

### 2. Database Setup

Run database migrations:

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python scripts/manage_migrations.py upgrade

# Or use Alembic directly
alembic upgrade head
```

### 3. Start the Application

```bash
# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 7860
```

The API will be available at `http://localhost:7860`

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123",
  "username": "johndoe",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

#### Verify Email
```http
POST /api/v1/auth/verify-email
Content-Type: application/json

{
  "token": "verification-token-from-email"
}
```

#### Request Password Reset
```http
POST /api/v1/auth/request-password-reset
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Reset Password
```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "new_password": "newSecurePassword123"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer your-access-token
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

## Using the Authentication System

### 1. Protecting Routes

Use the authentication middleware to protect routes:

```python
from fastapi import FastAPI, Depends
from src.middleware.auth_middleware import (
    get_current_user_required,
    get_current_admin_user
)
from src.models.user import User

app = FastAPI()

# Require authentication
@app.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user_required)
):
    return {"message": f"Hello {current_user.email}!"}

# Require admin role
@app.get("/admin-only")
async def admin_route(
    current_user: User = Depends(get_current_admin_user)
):
    return {"message": "Admin access granted"}
```

### 2. Adding Authentication Middleware

```python
from src.middleware.auth_middleware import AuthMiddleware

app.add_middleware(
    AuthMiddleware,
    exclude_paths=[
        "/health",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        # Add other public paths
    ]
)
```

### 3. Custom Permissions

```python
from src.middleware.auth_middleware import require_permissions

# Require specific permissions
@app.get("/analytics")
async def analytics_route(
    current_user: User = Depends(
        require_permissions(["read:analytics"])
    )
):
    return {"analytics": "data"}
```

## Security Features

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### JWT Token Configuration

- **Access Tokens**: 7 days expiry
- **Refresh Tokens**: 30 days expiry
- **Algorithm**: HS256
- **Secret Key**: Configurable via environment

### Rate Limiting

- Configurable requests per minute/hour/day
- Per-user and per-IP rate limiting
- Automatic blocking on abuse

### Email Verification

- Required for new accounts (configurable)
- Verification tokens expire in 24 hours
- Supports both Resend and SMTP providers

### Session Security

- Secure, HTTP-only cookies
- SameSite protection
- Configurable expiry
- Automatic cleanup

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(100),
    password_hash VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user',
    status VARCHAR(20) DEFAULT 'inactive',
    email_verified BOOLEAN DEFAULT FALSE,
    auth_provider VARCHAR(20) DEFAULT 'email',
    avatar_url VARCHAR(500),
    bio TEXT,
    preferences JSON,
    is_premium BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Sessions Table

```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_agent TEXT,
    ip_address INET,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Refresh Tokens Table

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## OAuth Integration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:3000/auth/callback`
6. Update environment variables:

```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### GitHub OAuth Setup

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create new OAuth App
3. Set Authorization callback URL: `http://localhost:3000/auth/callback`
4. Update environment variables:

```env
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

## Email Configuration

### Using Resend (Recommended)

1. Sign up at [Resend](https://resend.com)
2. Get your API key
3. Update environment variables:

```env
EMAIL_SERVICE=resend
RESEND_API_KEY=re_your_resend_api_key
```

### Using SMTP

For Gmail, you'll need to:
1. Enable 2-factor authentication
2. Generate an App Password
3. Update environment variables:

```env
EMAIL_SERVICE=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Creating Migrations

```bash
# Create new migration
python scripts/manage_migrations.py create "Add new feature"

# Apply migrations
python scripts/manage_migrations.py upgrade

# Check migration status
python scripts/manage_migrations.py status
```

### Database Reset

```bash
# Reset database (destructive!)
python scripts/manage_migrations.py reset
```

## Production Deployment

### Environment Variables

For production, ensure these are properly configured:

```env
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=your-production-secret-key
SESSION_COOKIE_SECURE=true
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
EMAIL_SERVICE=resend
```

### Security Checklist

- [ ] Generate strong JWT secret key
- [ ] Use HTTPS in production
- [ ] Configure proper CORS origins
- [ ] Set up email service
- [ ] Enable rate limiting
- [ ] Configure monitoring and logging
- [ ] Set up database backups
- [ ] Review OAuth redirect URIs
- [ ] Test password reset flow
- [ ] Verify email verification works

## Monitoring

### Health Check

```bash
curl http://localhost:7860/api/v1/auth/health
```

### Metrics

Prometheus metrics are available at `/metrics` when enabled.

### Logging

Logs are written to `logs/app.log` with rotation and retention.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL is correct
   - Verify database server is running
   - Ensure proper credentials

2. **JWT Token Errors**
   - Verify JWT_SECRET_KEY is set
   - Check token hasn't expired
   - Ensure proper token format

3. **Email Sending Failures**
   - Verify SMTP credentials
   - Check email service configuration
   - Test with a known good email address

4. **Migration Errors**
   - Ensure database exists
   - Check permissions
   - Verify connection string format

### Debug Mode

Enable debug logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Support

For issues and questions:

1. Check the application logs
2. Review the troubleshooting section
3. Check GitHub issues
4. Contact the development team

## License

This authentication system is part of the AI Book project and follows the same license terms.