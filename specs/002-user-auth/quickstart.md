# Quickstart Guide: User Authentication Implementation

**Feature**: User Authentication
**Estimated Time**: 2-3 days
**Prerequisites**: Access to codebase, Better Auth v1.4.x, Neon PostgreSQL, Resend account

## Quick Checklist

- [ ] Set up Neon PostgreSQL database
- [ ] Configure Better Auth v1.4.x with JWT plugin
- [ ] Set up Resend for emails
- [ ] Install required dependencies
- [ ] Run database migrations
- [ ] Implement authentication endpoints
- [ ] Update frontend components
- [ ] Test complete authentication flow

## Step 1: Environment Setup

### 1.1 Install Dependencies

```bash
# Backend dependencies
cd backend
pip install better-auth@1.4.7 sqlmodel asyncpg alembic passlib python-jose[cryptography] bcrypt resend psycopg2-binary pg

# Frontend dependencies (if not already installed)
cd ../frontend
npm install @types/react react-router-dom axios
```

### 1.2 Environment Variables

Create `.env` file in backend:

```env
# Database
DATABASE_URL="postgresql://username:password@host/database?sslmode=require"

# Better Auth
BETTER_AUTH_SECRET="your-super-secret-jwt-key-here"  # Generate: openssl rand -base64 32
BETTER_AUTH_URL="http://localhost:8000"

# JWT
JWT_SECRET_KEY="your-jwt-secret-key"  # Different from Better Auth secret

# Email
RESEND_API_KEY="re_your_resend_api_key"
FROM_EMAIL="noreply@yourdomain.com"
FRONTEND_URL="http://localhost:3000"

# Application
APP_NAME="AI Book"
```

## Step 2: Database Setup

### 2.1 Create Better Auth Configuration

```python
# backend/src/core/auth.py
from better_auth import BetterAuth
from better_auth.adapters.postgres import PostgresAdapter
import os
from pg import PGPool

# Create PostgreSQL pool for Better Auth
pool = PGPool(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    sslmode="require"
)

# Configure Better Auth
auth = BetterAuth(
    database=PostgresAdapter(pool),
    emailAndPassword={
        "enabled": True,
        "requireEmailVerification": True,
        "minPasswordLength": 8,
    },
    session={
        "expiresIn": 60 * 60 * 24 * 7,  # 7 days
        "cookieCache": {
            "enabled": True,
            "maxAge": 60 * 5  # 5 minutes
        }
    },
    emailVerification={
        "sendVerificationEmail": async ({ user, url, token }, request) => {
            # Implement email sending
            from ..services.email import send_verification_email
            await send_verification_email(user.email, url)
        }
    },
    passwordReset={
        "sendResetPassword": async ({ user, url, token }, request) => {
            # Implement password reset email
            from ..services.email import send_password_reset_email
            await send_password_reset_email(user.email, url)
        }
    }
)
```

### 2.2 Configure SQLModel Database

```python
# backend/src/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Use async connection for SQLModel
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=300,
    # Use same database as Better Auth but with async driver
    connect_args={"server_settings": {"application_name": "ai_book_sqlmodel"}}
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 2.3 Run Migrations

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Run the migration
alembic upgrade head
```

## Step 3: Backend Implementation

### 3.1 Create JWT Service

```python
# backend/src/services/jwt.py
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from ..core.config import settings

class JWTService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # 7 days

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.JWTError:
            raise Exception("Invalid token")

jwt_service = JWTService()
```

### 3.2 Create Auth API Routes

```python
# backend/src/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from ..core.database import get_db
from ..core.auth import auth
from ..services.jwt import jwt_service
from ..services.email import EmailService
from ..models.user import UserPreferences
from ..schemas.auth import (
    UserCreateSchema, UserLoginSchema, PasswordResetSchema,
    ConfirmPasswordResetSchema, UserPreferencesUpdateSchema
)
from ..services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()
auth_service = AuthService()
email_service = EmailService()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    # Use Better Auth to create user
    try:
        user = await auth.api.sign_up_email(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name
        )

        # Create user preferences
        preferences = UserPreferences(
            user_id=user.id,
            theme="system",
            language="en",
            timezone="UTC"
        )
        db.add(preferences)
        await db.commit()

        return {
            "success": True,
            "data": {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "emailVerified": user.email_verified
                },
                "message": "Registration successful. Please check your email to verify your account."
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

@router.post("/login")
async def login(
    credentials: UserLoginSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Authenticate with Better Auth
        user = await auth.api.sign_in_email(
            email=credentials.email,
            password=credentials.password
        )

        # Check email verification
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in"
            )

        # Get user preferences
        from sqlalchemy import select
        stmt = select(UserPreferences).where(UserPreferences.user_id == user.id)
        result = await db.execute(stmt)
        preferences = result.scalar_one_or_none()

        # Create JWT token
        token = jwt_service.create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "emailVerified": user.email_verified,
            "role": user.role
        })

        return {
            "success": True,
            "data": {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "emailVerified": user.email_verified,
                    "preferences": preferences.__dict__ if preferences else None
                },
                "token": token,
                "expiresAt": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

@router.get("/me")
async def get_current_user(
    token: Optional[str] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify JWT token
    try:
        payload = jwt_service.verify_token(token.credentials)
        user_id = uuid.UUID(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Get user from Better Auth
    user = await auth.api.getUser(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user preferences
    from sqlalchemy import select
    stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
    result = await db.execute(stmt)
    preferences = result.scalar_one_or_none()

    return {
        "success": True,
        "data": {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "emailVerified": user.email_verified,
                "role": user.role,
                "createdAt": user.created_at.isoformat() if user.created_at else None,
                "preferences": preferences.__dict__ if preferences else None
            }
        }
    }

@router.post("/logout")
async def logout(
    token: Optional[str] = Depends(security)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify token
    try:
        payload = jwt_service.verify_token(token.credentials)
        user_id = uuid.UUID(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Invalidate all sessions for user (Better Auth handles this)
    await auth.api.signOut(user_id)

    return {
        "success": True,
        "data": {
            "message": "Logged out successfully"
        }
    }

@router.post("/refresh")
async def refresh_token(
    token: Optional[str] = Depends(security)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify existing token
    try:
        payload = jwt_service.verify_token(token.credentials)
        user_id = uuid.UUID(payload.get("sub"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Get user from Better Auth
    user = await auth.api.getUser(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create new token
    new_token = jwt_service.create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "emailVerified": user.email_verified,
        "role": user.role
    })

    return {
        "success": True,
        "data": {
            "token": new_token,
            "expiresAt": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    }
```

### 3.3 Update Main App

```python
# backend/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.auth import router as auth_router
from .core.auth import auth

app = FastAPI(title="AI Book API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router, prefix="/api/v1")

# Mount Better Auth handler
app.mount("/api/auth", auth.handler)

# JWT validation middleware for protected routes
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Step 4: Frontend Integration

### 4.1 Create Auth Context

```typescript
// frontend/src/context/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, AuthResponse, LoginData, CreateUserData } from '../types/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: CreateUserData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setUser(data.data.user);
        } else {
          setToken(null);
          localStorage.removeItem('auth_token');
        }
      })
      .catch(() => {
        setToken(null);
        localStorage.removeItem('auth_token');
      })
      .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (data: LoginData) => {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    const result: AuthResponse = await response.json();

    if (result.success && result.data?.token) {
      setToken(result.data.token);
      setUser(result.data.user || null);
      localStorage.setItem('auth_token', result.data.token);
    } else {
      throw new Error(result.error || 'Login failed');
    }
  };

  const register = async (data: CreateUserData) => {
    const response = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    const result: AuthResponse = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Registration failed');
    }
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
  };

  const refreshToken = async () => {
    if (!token) return;

    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const result = await response.json();

    if (result.success && result.data?.token) {
      setToken(result.data.token);
      localStorage.setItem('auth_token', result.data.token);
    } else {
      logout();
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      register,
      logout,
      refreshToken
    }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### 4.2 Update Login Modal

```typescript
// frontend/src/components/Auth/SignInModal.tsx
import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LoginData } from '../../types/auth';

export const SignInModal: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login({ email, password });
      // Close modal and redirect
      window.location.href = '/chat';
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal">
      <form onSubmit={handleSubmit} className="auth-form">
        <h2>Sign In</h2>
        {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>

        <div className="auth-links">
          <a href="/forgot-password">Forgot password?</a>
          <span> | </span>
          <a href="/register">Create account</a>
        </div>
      </form>
    </div>
  );
};
```

## Step 5: Testing

### 5.1 Test Registration Flow

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "TestPass123",
    "confirmPassword": "TestPass123"
  }'
```

### 5.2 Test Login Flow

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'
```

### 5.3 Test Protected Route

```bash
# Using JWT token from login response
TOKEN="your-jwt-token-here"

curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 5.4 Frontend Testing

1. Open browser to `http://localhost:3000`
2. Click "Register" button
3. Fill out registration form
4. Check email for verification link
5. Click verification link
6. Try to login with new credentials
7. Verify user is logged in and redirected to chat

## Step 6: Integration with Chat System

### 6.1 Update Chat Widget Hook

```typescript
// frontend/src/components/ChatWidget/hooks/useChatSession.tsx
import { useAuth } from '../../../context/AuthContext';

export const useChatSession = () => {
  const { user, token } = useAuth();

  const createSession = async () => {
    const response = await fetch('/api/v1/chat/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: JSON.stringify({
        user_id: user?.id
      })
    });

    return response.json();
  };

  const linkAnonymousSessions = async (sessionIds: string[]) => {
    if (!token || !user) return;

    const response = await fetch('/api/v1/auth/link-sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        anonymousSessionIds: sessionIds
      })
    });

    return response.json();
  };

  // ... rest of the hook implementation
  return {
    createSession,
    linkAnonymousSessions,
    // ... other methods
  };
};
```

## Common Issues & Solutions

### Issue: CORS Errors
**Solution**: Ensure CORS is properly configured in FastAPI with the correct frontend URL.

### Issue: Token Not Validating
**Solution**: Check that JWT_SECRET_KEY is the same in all environments and tokens are properly signed.

### Issue: Database Connection Errors
**Solution**: Verify DATABASE_URL is correct and includes SSL mode for Neon PostgreSQL.

### Issue: Emails Not Sending
**Solution**: Check Resend API key is valid and from email is verified in Resend dashboard.

### Issue: Better Auth Tables Not Found
**Solution**: Ensure Better Auth has permissions to create tables, or manually run the SQL schema.

### Issue: Session Expiration
**Solution**: JWT tokens are stateless; implement client-side token refresh before 7-day expiry.

## Next Steps

1. Add password reset functionality
2. Implement rate limiting on auth endpoints
3. Add social login providers (Google, GitHub)
4. Set up monitoring and analytics
5. Write comprehensive tests
6. Deploy to staging environment

## Support

- Better Auth v1.4.x Documentation: https://better-auth.com/docs
- Neon PostgreSQL Docs: https://neon.tech/docs
- Resend Email Docs: https://resend.com/docs
- FastAPI Documentation: https://fastapi.tiangolo.com