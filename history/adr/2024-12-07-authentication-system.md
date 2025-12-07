# ADR: Authentication System Implementation

## Status
Accepted

## Date
2024-12-07

## Context
The AI Book application requires a secure authentication system to:
- Provide user identification and session management
- Enable persistent chat history storage
- Support anonymous users with limited access
- Protect against common web vulnerabilities
- Support future feature expansions (user preferences, etc.)

## Decision
We will implement a custom authentication system with the following architecture:

### 1. Authentication Strategy
- **Google OAuth 2.0** as the single identity provider
- **JWT tokens** for session management with HTTP-only cookies
- **Custom implementation** instead of third-party services (e.g., Auth0) for:
  - Greater control over user data and privacy
  - Reduced external dependencies
  - Lower complexity and cost

### 2. Session Management
- **HTTP-only cookies** to store JWT tokens (prevents XSS attacks)
- **Single session enforcement** per user (new logins invalidate previous sessions)
- **Anonymous session tracking** with UUIDs for unauthenticated users
- **Automatic session expiration** with cleanup

### 3. Security Measures
- **CSRF Protection** using double-submit cookie pattern
- **Rate Limiting** on all authentication endpoints
- **CORS Configuration** for cross-origin requests
- **Input Validation** using Pydantic models

### 4. Database Schema
- **SQLite** for simplicity and easy deployment
- **SQLAlchemy ORM** for type-safe database operations
- **Separate tables** for Users, Accounts, Sessions, Chat data, and Preferences

### 5. Anonymous Access
- **3-message limit** for anonymous users
- **Session migration** when anonymous users authenticate
- **In-memory tracking** with cleanup for expired sessions

## Consequences

### Positive
- **Security**: Comprehensive protection against CSRF, XSS, and injection attacks
- **Simplicity**: Single provider (Google) reduces implementation complexity
- **Control**: Full ownership of user data and authentication flow
- **Scalability**: Modular architecture allows easy expansion of features
- **Performance**: In-memory session tracking for anonymous users

### Negative
- **Vendor Lock-in**: Dependent on Google OAuth
- **Limited Options**: No email/password authentication alternative
- **Implementation Burden**: Custom code requires maintenance
- **Single Point of Failure**: No backup authentication method

### Neutral
- **Database Choice**: SQLite is simple but may need migration for scale
- **Cookie-based Storage**: Secure but requires proper CORS configuration

## Implementation Details

### Core Components

1. **Authentication Middleware** (`middleware/auth.py`)
   ```python
   class AuthMiddleware(BaseHTTPMiddleware):
       - Session validation
       - Anonymous user tracking
       - Message limit enforcement
   ```

2. **CSRF Middleware** (`middleware/csrf.py`)
   ```python
   class CSRFMiddleware(BaseHTTPMiddleware):
       - Double-submit cookie pattern
       - Token generation and validation
   ```

3. **Authentication Routes** (`routes/auth.py`)
   ```python
   @router.get("/login/google")  # OAuth initiation
   @router.get("/google/callback")  # OAuth callback
   @router.get("/me")  # User info
   @router.post("/logout")  # Session invalidation
   ```

4. **Database Models** (`models/auth.py`)
   ```python
   User, Account, Session, ChatSession, ChatMessage, UserPreferences
   ```

### Security Implementation

- **JWT Tokens**: 7-day expiration with rotation
- **CSRF Tokens**: 1-hour expiration with automatic refresh
- **Rate Limits**: 10-30 requests/minute per endpoint
- **Session Expiration**: Automatic cleanup after 24 hours of inactivity

### API Contract

The authentication system provides the following endpoints:

- `GET /auth/login/google` - Initiate OAuth flow
- `GET /auth/google/callback` - Handle OAuth callback
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Invalidate user session
- `GET /auth/preferences` - Get user preferences
- `PUT /auth/preferences` - Update user preferences
- `POST /auth/refresh` - Refresh access token

## Alternatives Considered

1. **Auth0 Integration**
   - **Pros**: Feature-complete, reduced implementation burden
   - **Cons**: Cost, data privacy concerns, vendor lock-in
   - **Rejected**: Privacy and cost concerns outweighed benefits

2. **Multiple OAuth Providers**
   - **Pros**: User choice, wider reach
   - **Cons**: Implementation complexity, management overhead
   - **Rejected**: Google provides sufficient coverage for our target audience

3. **Session-based Authentication (no JWT)**
   - **Pros**: Simpler implementation
   - **Cons**: Stateless constraints, scaling challenges
   - **Rejected**: JWT provides better scalability and flexibility

4. **PostgreSQL Database**
   - **Pros**: More robust, better for scaling
   - **Cons**: Additional operational complexity
   - **Rejected**: SQLite is sufficient for current needs with easy migration path

## Future Considerations

1. **Multi-provider Support**: Architecture supports adding GitHub, Microsoft OAuth
2. **Email/Password Authentication**: Can be added alongside OAuth
3. **Two-Factor Authentication**: Security enhancement path
4. **Database Migration**: Clear path from SQLite to PostgreSQL for scaling
5. **Session Analytics**: Logging and monitoring capabilities

## Testing Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end authentication flows
- **Security Tests**: CSRF protection, rate limiting, input validation
- **Performance Tests**: Session handling under load

## Security Review Checklist

- [x] CSRF protection implemented
- [x] Rate limiting configured
- [x] HTTP-only cookies for tokens
- [x] Secure JWT implementation
- [x] Input validation with Pydantic
- [x] SQL injection prevention via ORM
- [x] CORS configuration
- [x] Session expiration handling
- [x] Anonymous user limits
- [x] Comprehensive test coverage

## References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)