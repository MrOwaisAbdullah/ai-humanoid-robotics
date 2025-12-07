# Authentication System Documentation

## Overview

This document describes the authentication system implemented for the AI Book application. The system provides secure user authentication using Google OAuth, session management, and protection against common web vulnerabilities.

## Architecture

### Components

1. **Authentication Middleware** (`middleware/auth.py`)
   - Handles session validation
   - Manages anonymous user tracking
   - Enforces message limits for anonymous users
   - Implements session expiration checks

2. **CSRF Protection** (`middleware/csrf.py`)
   - Implements double-submit cookie pattern
   - Generates and validates CSRF tokens
   - Protects against Cross-Site Request Forgery attacks

3. **Authentication Routes** (`routes/auth.py`)
   - Google OAuth integration
   - User profile management
   - Session management (login/logout)
   - User preferences CRUD operations

4. **Database Models** (`models/auth.py`)
   - User, Account, Session entities
   - ChatSession and ChatMessage for persistent chat history
   - UserPreferences for user settings

## Security Features

### 1. CSRF Protection
- Double-submit cookie pattern implementation
- Automatic token generation and validation
- Exempt paths for safe endpoints
- Configurable token expiration (default: 1 hour)

### 2. Rate Limiting
- OAuth endpoints: 10 requests/minute
- Logout endpoint: 20 requests/minute
- Token refresh: 30 requests/minute
- Prevents brute force attacks

### 3. Session Management
- HTTP-only JWT cookies for token storage
- Session expiration with automatic cleanup
- Single session enforcement per user
- Secure session invalidation on logout

### 4. Anonymous Access Control
- Limited to 3 messages per anonymous session
- Session tracking with UUID generation
- Automatic cleanup of expired sessions
- Migration path to authenticated user

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/auth/login/google` | Initiate Google OAuth | 10/min |
| GET | `/auth/google/callback` | Handle OAuth callback | 10/min |
| GET | `/auth/me` | Get current user info | - |
| POST | `/auth/logout` | Logout user | 20/min |
| GET | `/auth/preferences` | Get user preferences | - |
| PUT | `/auth/preferences` | Update user preferences | - |
| POST | `/auth/refresh` | Refresh access token | 30/min |

### Request/Response Examples

#### Get Current User
```bash
curl -X GET "http://localhost:7860/auth/me" \
     -H "Authorization: Bearer <jwt_token>" \
     -H "X-CSRF-Token: <csrf_token>"
```

Response:
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "image_url": "https://example.com/avatar.jpg",
  "email_verified": true
}
```

#### Update User Preferences
```bash
curl -X PUT "http://localhost:7860/auth/preferences" \
     -H "Authorization: Bearer <jwt_token>" \
     -H "X-CSRF-Token: <csrf_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "theme": "dark",
       "language": "en",
       "notifications_enabled": true,
       "chat_settings": {
         "model": "gpt-4o-mini",
         "temperature": 0.7,
         "max_tokens": 1000
       }
     }'
```

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
AUTH_REDIRECT_URI=http://localhost:3000/auth/google/callback
FRONTEND_URL=http://localhost:3000

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080  # 7 days

# Database Configuration
DATABASE_URL=sqlite:///./database/auth.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=7860

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Google OAuth Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API and Google OAuth2 API

### 2. Create OAuth Credentials

1. Navigate to APIs & Services → Credentials
2. Click "Create Credentials" → OAuth 2.0 Client IDs
3. Select "Web application"
4. Add authorized redirect URIs:
   - Development: `http://localhost:7860/auth/google/callback`
   - Production: `https://yourdomain.com/auth/google/callback`
5. Save the Client ID and Client Secret

### 3. Configure Consent Screen

1. Go to OAuth consent screen
2. Add required scopes:
   - `email`
   - `profile`
   - `openid`
3. Add test users for development

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    image_url VARCHAR,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token VARCHAR UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Chat Sessions Table
```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/test_auth.py -v

# Run specific test class
pytest tests/test_auth.py::TestAuthenticationEndpoints -v

# Run with coverage
pytest tests/test_auth.py --cov=auth --cov-report=html
```

### Test Coverage

The test suite covers:
- JWT token creation and validation
- CSRF protection mechanisms
- Rate limiting enforcement
- Session management
- Anonymous access controls
- User preferences CRUD
- Error handling and security
- OAuth flow simulation

## Security Best Practices Implemented

### 1. Token Security
- JWT tokens with expiration
- HTTP-only cookies for storage
- Secure token generation with secrets

### 2. CSRF Protection
- Double-submit cookie pattern
- Automatic token validation
- State-changing request protection

### 3. Session Security
- Single session enforcement
- Automatic session expiration
- Secure session invalidation

### 4. Input Validation
- Pydantic models for request validation
- SQL injection prevention through ORM
- XSS protection through output encoding

### 5. Rate Limiting
- Per-endpoint rate limits
- IP-based limiting
- Protection against brute force attacks

## Deployment Considerations

### Production Environment Variables

```env
# Production settings
CSRF_SECURE=True  # Enable secure flag for HTTPS
JWT_SECRET_KEY=<production-secret-key>
DATABASE_URL=postgresql://user:pass@localhost/authdb
ALLOWED_ORIGINS=https://yourdomain.com
```

### Security Headers

The application sets security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HTTPS only)

### Monitoring

Enable logging for security events:
- Failed authentication attempts
- Rate limit violations
- CSRF validation failures
- Session expiration events

## Troubleshooting

### Common Issues

1. **OAuth Callback URL Mismatch**
   - Ensure redirect URI matches Google Console exactly
   - Check for trailing slashes

2. **CORS Errors**
   - Verify frontend URL in ALLOWED_ORIGINS
   - Check credentials flag in CORS config

3. **CSRF Token Missing**
   - Include X-CSRF-Token header in requests
   - Ensure client reads token from cookies

4. **Session Not Persisting**
   - Check database connection
   - Verify JWT_SECRET_KEY is set

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Multi-Provider Authentication**
   - GitHub OAuth
   - Microsoft OAuth
   - Email/password authentication

2. **Advanced Security**
   - Two-factor authentication
   - Device fingerprinting
   - Anomaly detection

3. **Session Management**
   - Session analytics
   - Concurrent session limits
   - Session revocation API

4. **User Management**
   - Admin dashboard
   - User roles and permissions
   - Audit logging

## References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth 2.0 Best Practices](https://oauth.net/articles/)