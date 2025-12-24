# Research Findings: User Authentication

**Date**: 2025-01-21
**Feature**: User Authentication
**Status**: Research Complete

## 1. Better Auth v2 vs Other Auth Solutions

### Evaluation Results

**Winner**: Better Auth v2

**Rationale**:
- **TypeScript-first**: Native TypeScript support with excellent type safety
- **Framework Agnostic**: Works with FastAPI, not limited to Next.js
- **PostgreSQL Support**: Built-in adapter for PostgreSQL with full SQLModel compatibility
- **Custom Flows**: Excellent support for custom verification and password reset flows
- **Session Management**: Flexible session handling with custom expiry times
- **Modern Architecture**: Designed for 2024+ security best practices

### Alternative Analysis

1. **Lucia Auth**: Strong contender but less TypeScript-first design
2. **NextAuth.js/Auth.js**: Tied to Next.js ecosystem, not suitable for FastAPI
3. **Firebase Auth**: Proprietary, vendor lock-in, limited customization
4. **Passlib + Custom**: Would require building all auth flows from scratch

## 2. Neon PostgreSQL Integration Patterns

### Best Practices Identified

1. **Connection Pooling**:
   ```python
   # Using asyncpg with SQLAlchemy
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True,
       pool_recycle=300
   )
   ```

2. **Migration Strategy**:
   - Use Alembic for database migrations
   - Start with version 001_create_users_table.py
   - Include both DDL and initial data migrations

3. **Local Development**:
   - Use Docker with PostgreSQL for local testing
   - Environment-specific database URLs
   - Seed data for testing

4. **Backup & Recovery**:
   - Neon handles automated backups
   - Point-in-time recovery available
   - Export capabilities for compliance

## 3. JWT Implementation Security (2025 Best Practices)

### Security Recommendations

1. **Token Storage**:
   - **Production**: httpOnly, secure, sameSite cookies
   - **Development**: localStorage with additional CSRF protection
   - **Recommended**: Hybrid approach with fallback support

2. **Token Rotation**:
   - Implement sliding session expiration
   - Refresh tokens on 50% of expiry time
   - Maintain token blacklist for immediate logout

3. **Security Headers**:
   ```python
   {
       "X-Content-Type-Options": "nosniff",
       "X-Frame-Options": "DENY",
       "X-XSS-Protection": "1; mode=block",
       "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
   }
   ```

4. **CSRF Protection**:
   - Required when using cookies
   - Implement double-submit cookie pattern
   - SameSite attribute set to 'strict'

## 4. Email Service Integration

### Evaluation Results

**Winner**: Resend

**Key Advantages**:
- **Developer Experience**: Simple, clean API design
- **Deliverability**: Built on proven email infrastructure
- **Pricing**: Competitive at $0.003 per email
- **Templates**: Support for React email templates
- **Analytics**: Real-time delivery tracking

### Comparison Table

| Service | Cost/1k emails | API Simplicity | Templates | Analytics |
|---------|----------------|----------------|-----------|-----------|
| Resend | $3.00 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| SendGrid | $0.80 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| AWS SES | $0.10 | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| Postmark | $1.50 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

## 5. Rate Limiting and Security

### Recommended Implementation

1. **Login Attempts**:
   ```python
   # Rate limit: 5 attempts per 15 minutes per IP
   # Account lock: 10 failed attempts triggers 30-minute lock
   ```

2. **Password Reset**:
   - Limit: 3 requests per hour per email
   - Token expiry: 1 hour (as specified)
   - Invalidate all user sessions on password change

3. **Session Management**:
   - Maximum concurrent sessions: 5 per user
   - Session rotation on sensitive actions
   - Automatic cleanup of expired sessions

4. **Security Measures**:
   - Enforce HTTPS in production
   - Implement CORS properly
   - Use parameterized queries to prevent SQLi
   - Input validation on all endpoints

## 6. Integration Points Analysis

### Existing UI Components Status

**Current State**: Authentication modals identified in the codebase
- `SignInModal.tsx`: Exists, needs backend integration
- `RegisterModal.tsx`: Exists, needs backend integration
- `OnboardingModal.tsx`: Exists, needs auth state integration

**Integration Requirements**:
1. Connect form submissions to new auth endpoints
2. Add loading states and error handling
3. Implement redirect after successful auth
4. Add session persistence across page reloads

### Chat Session Linking Strategy

**Current Implementation**: Anonymous sessions stored with session IDs

**Migration Strategy**:
1. Keep existing anonymous sessions intact
2. On user registration/login, offer to link previous sessions
3. Update ChatSession model with optional user_id foreign key
4. Implement session migration service

## 7. Technical Specifications Resolved

### Better Auth v2 Configuration

```python
# Core configuration resolved
auth = BetterAuth(
    database=DATABASE_URL,
    emailAndPassword={
        "enabled": True,
        "requireEmailVerification": True
    },
    session={
        "expiresIn": 60 * 60 * 24 * 7,  # 7 days
        "cookieCache": {
            "enabled": True,
            "maxAge": 60 * 5  # 5 minutes
        }
    },
    emailVerification={
        "sendOnSignUp": True,
        "expiresIn": 60 * 60 * 24  # 24 hours
    }
)
```

### Database Schema Design

```sql
-- Key indexes identified
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_verified ON users(email_verified);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_verification_token ON verification_tokens(token, expires_at);
```

### Frontend Auth State

**Implementation Strategy**:
- Use React Context for auth state management
- Implement token refresh interceptor in API client
- Store tokens in httpOnly cookies (production) or localStorage (dev)
- Protected routes using HOC pattern

## 8. Implementation Recommendations

### Priority Order

1. **Phase 1**: Core Authentication (P1)
   - User registration and login
   - JWT token management
   - Basic session handling

2. **Phase 2**: Security Features (P1)
   - Email verification
   - Password reset
   - Rate limiting

3. **Phase 3**: User Experience (P2)
   - Profile management
   - Session persistence
   - Chat session linking

### Risk Mitigation

1. **Security Risks**:
   - Comprehensive security review before production
   - Penetration testing of auth endpoints
   - Regular dependency updates

2. **Performance Risks**:
   - Implement caching for frequently accessed user data
   - Database query optimization with proper indexes
   - Monitor authentication response times

3. **Availability Risks**:
   - Circuit breaker pattern for email service
   - Database connection pooling
   - Graceful degradation for auth failures

## 9. Conclusion

All research questions have been resolved with clear implementation paths identified. The chosen technology stack (Better Auth v2 + Neon PostgreSQL + Resend) provides a solid foundation for secure, scalable authentication that meets all specified requirements.

Key decisions made:
- Better Auth v2 for authentication framework
- Neon PostgreSQL for data storage
- Resend for email delivery
- httpOnly cookies for token storage
- Hybrid approach for development vs production

The implementation can proceed with confidence in the technical approach.