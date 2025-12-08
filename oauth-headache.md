# OAuth Headache: Problems Faced and Solutions

This document describes all the OAuth implementation challenges encountered while integrating Google OAuth with the AI Book application, and the solutions implemented to resolve them.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Problems and Solutions](#problems-and-solutions)
3. [Configuration Checklist](#configuration-checklist)
4. [Troubleshooting Guide](#troubleshooting-guide)

## Architecture Overview

The OAuth implementation uses a hybrid approach:
- **Frontend**: Docusaurus site deployed on GitHub Pages at `https://mrowaisabdullah.github.io/ai-humanoid-robotics/`
- **Backend**: FastAPI server deployed on HuggingFace Spaces at `https://mrowaisabdullah-ai-humanoid-robotics.hf.space/`
- **Authentication Flow**: Google OAuth 2.0 with JWT tokens

## Problems and Solutions

### 1. SQLAlchemy Metadata Naming Conflict

**Problem**:
```
Attribute name 'metadata' is reserved when using the Declarative API
```

**Root Cause**: SQLAlchemy reserves the `metadata` attribute for its internal use. We tried to create a column named `metadata` in the `ChatMessage` model.

**Solution**:
```python
# Before (causes error):
class ChatMessage(Base):
    metadata = Column(JSON, nullable=True)

# After (fixed):
class ChatMessage(Base):
    message_metadata = Column(JSON, nullable=True)  # Renamed to avoid conflict
```

**File**: `backend/models/auth.py`

### 2. Missing Authentication Dependencies

**Problem**:
```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**Root Cause**: The backend was missing required authentication packages.

**Solution**: Added to `backend/pyproject.toml`:
```toml
dependencies = [
    # ... existing deps
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "authlib>=1.2.1",
    "itsdangerous>=2.1.0",
]
```

### 3. SessionMiddleware Missing for OAuth

**Problem**:
```
AssertionError: SessionMiddleware must be installed to access request.session
```

**Root Cause**: Authlib requires SessionMiddleware to handle OAuth state parameter.

**Solution**: Added in `backend/main.py`:
```python
from starlette.middleware.sessions import SessionMiddleware

# Add session middleware for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    session_cookie="session_id",
    max_age=3600,
    same_site="lax",
    https_only=False,
)
```

### 4. Missing itsdangerous Dependency

**Problem**:
```
ModuleNotFoundError: No module named 'itsdangerous'
```

**Root Cause**: SessionMiddleware requires itsdangerous for secure cookie signing.

**Solution**: Added `itsdangerous>=2.1.0` to dependencies.

### 5. JWT Secret Key Not Configured

**Problem**:
```
AttributeError: 'Settings' object has no attribute 'jwt_secret_key'
```

**Root Cause**: JWT secret key was not added to the Settings class.

**Solution**: Added to `backend/main.py`:
```python
class Settings(BaseSettings):
    # ... existing fields
    jwt_secret_key: str = "your-secret-key"  # Added this field
```

### 6. Invalid Google OAuth Client

**Problem**:
```
Error 401: invalid_client
The OAuth client was not found
```

**Root Cause**: Google OAuth client credentials were invalid or the client was deleted.

**Solution**:
- Create a new OAuth client in Google Cloud Console
- Update `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`

### 7. GitHub Pages Build Error

**Problem**:
```
Liquid syntax error (line 69): Variable '{{ code({ node, inline, className, children, ...props }' was not properly terminated
```

**Root Cause**: Jekyll (used by GitHub Pages) was interpreting the markdown as Liquid template.

**Solution**: Added Jekyll front matter to disable Liquid processing:
```yaml
---
liquid: false
---
```
**File**: `docs/chatgpt-style-chatbot-ui-guide.md`

### 8. OAuth Redirect URI Mismatch

**Problem**:
```
Error 400: redirect_uri_mismatch
```

**Root Cause**: The redirect URI in Google Cloud Console didn't match the actual deployment URL.

**Solution**:
- Updated AUTH_REDIRECT_URI to point to HuggingFace space
- Added `/backend` prefix for FastAPI routes

### 9. Provider Account ID Required Error

**Problem**:
```
{"detail":"OAuth authentication failed: 400: Provider account ID is required"}
```

**Root Cause**: The Google OAuth response structure changed, and we weren't properly extracting the user's Google ID (`sub` field).

**Solution**: Updated `backend/auth/auth.py`:
```python
def create_or_update_account(db: Session, user: User, provider: str, account_info: dict) -> Account:
    provider_account_id = account_info.get('sub')
    if not provider_account_id:
        # Fallback to email if sub is not available
        provider_account_id = account_info.get('email')
        if not provider_account_id:
            # Final fallback to user.id
            provider_account_id = str(user.id)
```

### 10. OAuth Callback 404 Error on GitHub Pages

**Problem**:
```
404 There isn't a GitHub Pages site here.
```

**Root Cause**: GitHub Pages didn't have a route handler for `/auth/callback`.

**Solution**: Created `src/pages/auth/callback.tsx`:
```tsx
import React from 'react';
import Head from '@docusaurus/Head';
import { OAuthCallbackHandler } from '../../../src/contexts/AuthContext';

export default function AuthCallbackPage() {
  return (
    <>
      <Head>
        <title>Authentication Callback</title>
      </Head>
      <OAuthCallbackHandler />
    </>
  );
}
```

### 11. URL Path Mismatch Issue

**Problem**: OAuth was redirecting to `https://mrowaisabdullah.github.io/auth/callback` but the site is actually deployed to `https://mrowaisabdullah.github.io/ai-humanoid-robotics/`.

**Root Cause**: Docusaurus `baseUrl` configuration adds a base path to all routes.

**Solution**: Updated `.env`:
```env
FRONTEND_URL=https://mrowaisabdullah.github.io/ai-humanoid-robotics
AUTH_REDIRECT_URI=https://mrowaisabdullah-ai-humanoid-robotics.hf.space/backend/auth/google/callback
```

## Configuration Checklist

### Google Cloud Console Setup
1. Create OAuth 2.0 Client ID
2. Add authorized redirect URI: `https://mrowaisabdullah-ai-humanoid-robotics.hf.space/backend/auth/google/callback`
3. Enable Google+ API and Google People API

### Backend Environment Variables (.env)
```env
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
AUTH_REDIRECT_URI=https://your-hf-space.hf.space/backend/auth/google/callback

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# Frontend URL (must include Docusaurus base path)
FRONTEND_URL=https://your-username.github.io/your-repo

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-username.github.io,https://huggingface.co,https://your-hf-space.hf.space
```

### Frontend Configuration
- `docusaurus.config.ts`: Ensure `baseUrl` is set correctly
- `src/contexts/AuthContext.tsx`: Handles OAuth callback
- `src/pages/auth/callback.tsx`: Callback route handler

## Troubleshooting Guide

### 1. "invalid_client" Error
- Check Google OAuth client credentials
- Ensure client is not deleted in Google Cloud Console

### 2. "redirect_uri_mismatch" Error
- Verify AUTH_REDIRECT_URI matches exactly in Google Cloud Console
- Include the full URL with `https://` and no trailing slash

### 3. 404 on Callback
- Check that `src/pages/auth/callback.tsx` exists
- Verify FRONTEND_URL includes the Docusaurus base path
- Rebuild and deploy the frontend

### 4. "Provider account ID is required" Error
- Ensure Google OAuth is returning user info
- Check the backend logs for the actual token response
- Verify the fallback logic in `create_or_update_account`

### 5. CORS Issues
- Add the frontend URL to ALLOWED_ORIGINS
- Include both HTTP and HTTPS versions for development
- Add HuggingFace Spaces URL if deploying there

## Lessons Learned

1. **Always Test in Production Environment**: Local OAuth might work even with misconfigured URLs due to different base paths.

2. **Docusaurus Base Path Matters**: Always include the `baseUrl` from `docusaurus.config.ts` in frontend URLs.

3. **Google OAuth Response Structure**: The OAuth response might vary between different Google client setups. Always add fallbacks for required fields.

4. **Session Management**: OAuth requires proper session middleware to handle the state parameter and prevent CSRF attacks.

5. **Static Site Limitations**: GitHub Pages can't handle dynamic routes, so OAuth callbacks must be static pages that handle the redirect client-side.

6. **Environment-Specific Configuration**: Use different configurations for development, staging, and production environments.

## Security Considerations

1. **State Parameter**: Always use and verify the OAuth state parameter to prevent CSRF attacks.
2. **Secure Tokens**: Use strong JWT secret keys and set appropriate expiration times.
3. **HTTPS Only**: Use HTTPS in production for all OAuth redirects.
4. **Scope Limitation**: Request only the necessary OAuth scopes (email and profile).
5. **Token Validation**: Always validate JWT tokens on the server side.

## Final Architecture Flow

1. User clicks "Sign in with Google" → redirects to Google OAuth
2. Google redirects to HuggingFace backend: `/backend/auth/google/callback`
3. Backend exchanges code for tokens, gets user info, creates JWT
4. Backend redirects to GitHub Pages: `/ai-humanoid-robotics/auth/callback?token=JWT`
5. Docusaurus serves the callback page, which processes the token
6. User is authenticated and redirected to the main app

This implementation provides a secure, scalable authentication system that works across different deployment platforms while maintaining separation between the static frontend and dynamic backend.