---
id: 0001
title: User Authentication Spec
stage: spec
date: 2025-01-21
surface: agent
model: glm-4.6
feature: 002-user-auth
branch: 002-user-auth
user:
command: /sp.specify
labels: ["authentication","user-management","security"]
links:
  spec: specs/002-user-auth/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-user-auth/spec.md
  - specs/002-user-auth/checklists/requirements.md
tests:
  - No tests run yet (specification phase)
---

## Prompt

# Better Auth Implementation for AI Book Application

## Overview
Implement a comprehensive authentication system for the AI book application using Better Auth v2 patterns, with Neon PostgreSQL for data storage and SQLModel for database modeling. The system will use email/password authentication with existing sign-in, register, and onboarding modals.

## Prerequisites
- Node.js 18+ and npm installed
- Python 3.9+ with FastAPI backend
- UV package manager installed (`pip install uv`)
- Neon PostgreSQL database

## Phase 1: Backend Authentication Setup

### 1.1 Install Dependencies
```bash
# Backend dependencies with UV
uv add sqlmodel sqlalchemy[asyncio] asyncpg psycopg2-binary alembic
uv add python-jose[cryptography] passlib[bcrypt] python-dotenv
uv add python-multipart email-validator fastapi uvicorn

# Frontend dependencies (already installed)
# No additional dependencies needed - using existing modals
```

### 1.2 Database Setup with Neon PostgreSQL

#### 1.2.1 Database Configuration (.env)
```env
# Neon PostgreSQL Database
DATABASE_URL=postgresql://username:password@host/dbname?sslmode=require

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Email Configuration (for verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourapp.com
```

#### 1.2.2 Database Models (backend/models/auth.py)
```python
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional, List
import uuid

# Base model for all tables
class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": func.now()})

class User(BaseModel, table=True):
    __tablename__ = "users"

    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str = Field(max_length=255)
    password_hash: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None)
    password_reset_token: Optional[str] = Field(default=None)
    password_reset_expires: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)

    # Profile fields
    bio: Optional[str] = Field(default=None, max_length=500)
    avatar_url: Optional[str] = Field(default=None)
    timezone: str = Field(default="UTC")
    language: str = Field(default="en")

    # Relationships
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    user_preferences: Optional["UserPreferences"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False})

class UserPreferences(BaseModel, table=True):
    __tablename__ = "user_preferences"

    user_id: int = Field(foreign_key="users.id", primary_key=True)

    # UI Preferences
    theme: str = Field(default="light")  # light, dark, auto
    language: str = Field(default="en")
    timezone: str = Field(default="UTC")

    # Notification Settings
    email_notifications: bool = Field(default=True)
    chat_notifications: bool = Field(default=True)

    # Chat Preferences
    ai_model: str = Field(default="gpt-3.5-turbo")
    chat_mode: str = Field(default="balanced")  # creative, balanced, precise
    save_history: bool = Field(default=True)

    # Privacy Settings
    profile_visibility: str = Field(default="public")  # public, private

    # Additional settings as JSON
    extra_settings: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))

    # Relationships
    user: User = Relationship(back_populates="user_preferences")

class ChatSession(BaseModel, table=True):
    __tablename__ = "chat_sessions"

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: Optional[int] = Field(foreign_key="users.id", default=None)
    title: Optional[str] = Field(default="New Chat")
    is_anonymous: bool = Field(default=True)

    # Session metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional[User] = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session", cascade_delete=True)

class ChatMessage(BaseModel, table=True):
    __tablename__ = "chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="chat_sessions.session_id")
    role: str = Field(max_length=20)  # user, assistant, system
    content: str = Field(sa_column=Column(Text))

    # Message metadata
    sources: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSON))
    tokens_used: Optional[int] = Field(default=0)
    model_used: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    session: ChatSession = Relationship(back_populates="messages")
```

#### 1.2.3 Database Connection (backend/database.py)
```python
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    class Config:
        env_file = ".env"

settings = Settings()

# Create async engine for Neon PostgreSQL with proper configuration
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,  # Set to True to see SQL queries
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,
    max_overflow=0,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency to get async DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

### 1.3 Authentication Service (backend/services/auth_service.py)
```python
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from email_validator import validate_email, EmailNotValidError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models.auth import User, UserPreferences
from database import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration from settings
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        # Validate email format
        try:
            validate_email(email)
        except EmailNotValidError:
            return None

        # Get user from database
        statement = select(User).where(User.email == email.lower())
        result = await self.db.execute(statement)
        user = result.scalar_one_or_none()

        # Check if user exists and password is correct
        if not user or not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()

        return user

    async def create_user(self, email: str, full_name: str, password: str) -> Tuple[User, str]:
        """Create new user and return verification token."""
        # Validate email
        try:
            validate_email(email)
        except EmailNotValidError:
            raise ValueError("Invalid email format")

        # Check if user already exists
        statement = select(User).where(User.email == email.lower())
        result = await self.db.execute(statement)
        if result.scalar_one_or_none():
            raise ValueError("User already exists")

        # Create verification token
        verification_token = secrets.token_urlsafe(32)

        # Create user
        user = User(
            email=email.lower(),
            full_name=full_name,
            password_hash=self.get_password_hash(password),
            verification_token=verification_token,
            is_verified=False  # Require email verification
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Create default preferences
        preferences = UserPreferences(user_id=user.id)
        self.db.add(preferences)
        await self.db.commit()

        return user, verification_token

    async def verify_email(self, token: str) -> bool:
        """Verify user email with token."""
        statement = select(User).where(User.verification_token == token)
        result = await self.db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.is_verified = True
        user.verification_token = None
        await self.db.commit()

        return True

    async def initiate_password_reset(self, email: str) -> Optional[str]:
        """Initiate password reset and return reset token."""
        statement = select(User).where(User.email == email.lower())
        result = await self.db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return None  # Don't reveal if user exists

        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.utcnow() + timedelta(hours=1)

        user.password_reset_token = reset_token
        user.password_reset_expires = reset_expires
        await self.db.commit()

        return reset_token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with valid token."""
        statement = select(User).where(
            (User.password_reset_token == token) &
            (User.password_reset_expires > datetime.utcnow())
        )
        result = await self.db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.password_hash = self.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        await self.db.commit()

        return True

    async def update_user_profile(self, user_id: int, **kwargs) -> User:
        """Update user profile."""
        statement = select(User).where(User.id == user_id)
        result = await self.db.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Update allowed fields
        allowed_fields = ['full_name', 'bio', 'avatar_url', 'timezone', 'language']
        for field in allowed_fields:
            if field in kwargs:
                setattr(user, field, kwargs[field])

        await self.db.commit()
        await self.db.refresh(user)

        return user
```

### 1.4 API Routes (backend/api/v1/auth.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os

from database import get_db
from models.auth import User
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(auto_error=False)

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class PasswordReset(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

# Dependency to get current user
async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    payload = AuthService.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    auth_service = AuthService(db)
    statement = select(User).where(User.id == payload.get("sub"))
    result = await db.execute(statement)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

# Optional authentication (doesn't raise error if not authenticated)
async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get user if authenticated, otherwise return None."""
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None

    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

@router.post("/register", response_model=Token)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    # Validate passwords match
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )

    auth_service = AuthService(db)
    try:
        user, verification_token = await auth_service.create_user(
            user_data.email,
            user_data.full_name,
            user_data.password
        )

        # TODO: Send verification email
        # await send_verification_email(user.email, verification_token)

        # Create access token
        access_token = auth_service.create_access_token(
            data={"sub": user.id, "email": user.email}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "avatar_url": user.avatar_url
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return access token."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(user_data.email, user_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email before logging in"
        )

    # Create access token
    access_token = auth_service.create_access_token(
        data={"sub": user.id, "email": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "timezone": user.timezone,
            "language": user.language
        }
    }

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "timezone": current_user.timezone,
        "language": current_user.language,
        "preferences": current_user.user_preferences
    }

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    auth_service = AuthService(db)
    user = await auth_service.update_user_profile(
        current_user.id,
        **profile_data.dict(exclude_unset=True)
    )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "timezone": user.timezone,
        "language": user.language
    }

@router.post("/logout")
async def logout(response: Response):
    """Logout user (client-side token removal)."""
    return {"message": "Successfully logged out"}

@router.post("/forgot-password")
async def forgot_password(
    email: EmailStr,
    db: AsyncSession = Depends(get_db)
):
    """Initiate password reset."""
    auth_service = AuthService(db)
    reset_token = await auth_service.initiate_password_reset(email)

    # TODO: Send reset email
    # if reset_token:
    #     await send_reset_email(email, reset_token)

    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token."""
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    auth_service = AuthService(db)
    if await auth_service.reset_password(reset_data.token, reset_data.new_password):
        return {"message": "Password reset successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

@router.get("/check")
async def check_auth(
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Check if user is authenticated."""
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "is_verified": current_user.is_verified,
                "avatar_url": current_user.avatar_url
            }
        }
    return {"authenticated": False}
```

### 1.5 Update Main Application (backend/main.py)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database import init_db
from api.v1 import auth, chat, translation, personalization

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield

# Create FastAPI app
app = FastAPI(
    title="AI Book Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        os.getenv("FRONTEND_URL", "")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(translation.router, prefix="/api/v1")
app.include_router(personalization.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

## Phase 2: Frontend Integration

### 2.1 Update Authentication Context (src/contexts/AuthContext.tsx)

The frontend already has sign-in, register, and onboarding modals. We'll update the context to use our new API:

```typescript
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  email: string;
  full_name: string;
  is_verified: boolean;
  avatar_url?: string;
  bio?: string;
  timezone?: string;
  language?: string;
  preferences?: {
    theme: string;
    language: string;
    ai_model: string;
    chat_mode: string;
    save_history: boolean;
    email_notifications: boolean;
  };
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, fullName: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  updateUserProfile: (data: Partial<User>) => Promise<void>;
  token: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'));
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const storedToken = localStorage.getItem('auth_token');
      if (!storedToken) {
        setUser(null);
        setToken(null);
        setLoading(false);
        return;
      }

      const response = await fetch('/api/v1/auth/check', {
        headers: {
          'Authorization': `Bearer ${storedToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.authenticated) {
          setUser(data.user);
          setToken(storedToken);
        } else {
          localStorage.removeItem('auth_token');
          setUser(null);
          setToken(null);
        }
      } else {
        localStorage.removeItem('auth_token');
        setUser(null);
        setToken(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('auth_token');
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('auth_token', data.access_token);
        setUser(data.user);
        setToken(data.access_token);
        return { success: true };
      } else {
        return { success: false, error: data.detail || 'Login failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const register = async (email: string, fullName: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email,
          full_name: fullName,
          password,
          confirm_password: password
        })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('auth_token', data.access_token);
        setUser(data.user);
        setToken(data.access_token);
        return { success: true };
      } else {
        return { success: false, error: data.detail || 'Registration failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
    setToken(null);
    window.location.href = '/';
  };

  const updateUserProfile = async (data: Partial<User>) => {
    if (!token) return;

    try {
      const response = await fetch('/api/v1/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        const updatedUser = await response.json();
        setUser(updatedUser);
      }
    } catch (error) {
      console.error('Profile update failed:', error);
    }
  };

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    register,
    logout,
    checkAuth,
    updateUserProfile,
    token
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

### 2.2 Update Existing Sign-in/Register Modals

The frontend already has modals, we just need to update them to use our new auth context:

```typescript
// src/components/Auth/SignInModal.tsx
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const SignInModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(email, password);

    if (result.success) {
      onClose();
    } else {
      setError(result.error || 'Login failed');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">Sign In</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <button
          onClick={onClose}
          className="mt-4 w-full text-gray-600 hover:text-gray-800"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};
```

### 2.3 Update Chat Widget to Use Authentication

```typescript
// src/components/ChatWidget/ChatWidgetContainer.tsx
import { useAuth } from '../../contexts/AuthContext';
import SignInModal from '../Auth/SignInModal';
import RegisterModal from '../Auth/RegisterModal';

export const ChatWidgetContainer: React.FC = () => {
  const { isAuthenticated, token } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState<'signin' | 'register' | null>(null);

  const sendMessage = async (message: string) => {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: JSON.stringify({ question: message, stream: true }),
    });

    // ... rest of implementation
  };

  if (!isAuthenticated) {
    return (
      <div className="chat-widget">
        <div className="text-center p-4">
          <p className="mb-4">Sign in to start chatting</p>
          <button
            onClick={() => setShowAuthModal('signin')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 mr-2"
          >
            Sign In
          </button>
          <button
            onClick={() => setShowAuthModal('register')}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            Register
          </button>
        </div>

        {showAuthModal === 'signin' && (
          <SignInModal onClose={() => setShowAuthModal(null)} />
        )}
        {showAuthModal === 'register' && (
          <RegisterModal onClose={() => setShowAuthModal(null)} />
        )}
      </div>
    );
  }

  // Existing chat widget implementation for authenticated users
  return (
    // ... your existing chat widget UI
  );
};
```

## Phase 3: Database Migrations

### 3.1 Alembic Configuration

```bash
# Install alembic with UV if not installed
uv add alembic

# Initialize alembic
cd backend
uv run alembic init alembic

# Configure alembic.ini to use your Neon PostgreSQL URL
# Set sqlalchemy.url = postgresql://username:password@host/dbname

# Create initial migration
uv run alembic revision --autogenerate -m "Initial authentication schema"

# Apply migrations
uv run alembic upgrade head
```

### 3.2 Migration Script Template (backend/alembic/versions/001_initial_schema.py)
```python
"""Initial authentication schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_token', sa.String(), nullable=True),
        sa.Column('password_reset_token', sa.String(), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('bio', sa.String(length=500), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.Column('email_notifications', sa.Boolean(), nullable=True),
        sa.Column('chat_notifications', sa.Boolean(), nullable=True),
        sa.Column('ai_model', sa.String(), nullable=True),
        sa.Column('chat_mode', sa.String(), nullable=True),
        sa.Column('save_history', sa.Boolean(), nullable=True),
        sa.Column('profile_visibility', sa.String(), nullable=True),
        sa.Column('extra_settings', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_sessions_session_id', 'chat_sessions', ['session_id'], unique=True)

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('user_preferences')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
```

## Phase 4: Testing

### 4.1 Test Authentication Flow

1. **Register a new user**:
   - Visit the register modal
   - Enter email, full name, and password
   - Submit and verify user is created

2. **Login with existing user**:
   - Visit the sign-in modal
   - Enter credentials
   - Verify successful authentication

3. **Test protected routes**:
   - Try accessing chat without authentication
   - Verify prompt to sign in/register
   - Verify chat works after authentication

4. **Test profile updates**:
   - Update user profile information
   - Verify changes persist

### 4.2 Run the Application with UV

```bash
# Start the backend server with UV
cd backend
uv run python main.py

# The server will start on http://localhost:8000

# The frontend should already be running or start it with:
cd src
npm start
```

### 4.2 Database Testing

```bash
# Connect to Neon PostgreSQL
psql postgresql://username:password@host/dbname

# Verify tables created
\dt

# Verify user creation
SELECT * FROM users LIMIT 5;

# Check relationships
SELECT u.full_name, up.theme FROM users u
LEFT JOIN user_preferences up ON u.id = up.user_id;
```

## Security Considerations

1. **Password Security**:
   - Minimum 8 characters
   - Hashed with bcrypt
   - Secure password reset flow

2. **Token Security**:
   - JWT tokens with 7-day expiry
   - Store tokens in localStorage (or secure cookies in production)
   - Validate tokens on protected routes

3. **Database Security**:
   - Use Neon's secure PostgreSQL
   - All connections use SSL
   - Environment variables for credentials

4. **Input Validation**:
   - Email format validation
   - Password strength requirements
   - SQL injection prevention through SQLModel

5. **Rate Limiting**:
   - Implement rate limiting on auth endpoints
   - Prevent brute force attacks

## Environment Variables Summary

```env
# Database
DATABASE_URL=postgresql://username:password@host/dbname?sslmode=require

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Email (optional, for verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourapp.com

# Frontend
FRONTEND_URL=http://localhost:3000
```

This implementation provides a complete authentication system using Neon PostgreSQL, SQLModel, and integrates seamlessly with your existing frontend modals and chat functionality.

## Response snapshot

Successfully created user authentication specification with the following components:

1. **Created feature branch**: `002-user-auth`
2. **Developed comprehensive specification** (`specs/002-user-auth/spec.md`) including:
   - 5 prioritized user stories (P1-P3) covering registration, login, profile management, password reset, and email verification
   - 15 functional requirements covering all authentication aspects
   - 8 measurable success criteria focusing on performance, security, and user experience
   - Key entities definition (User, UserPreferences, ChatSession, ChatMessage, VerificationToken)

3. **Resolved 3 clarification points** through user interaction:
   - Email verification: Required before login
   - Concurrent sessions: Allow multiple sessions across devices
   - Disposable emails: Allow all valid email formats

4. **Created quality checklist** (`specs/002-user-auth/checklists/requirements.md`) validating specification completeness

5. **Created Prompt History Record** documenting the specification creation process

## Outcome

- ✅ Impact: Comprehensive authentication specification ready for implementation planning
- 🧪 Tests: No tests run yet (specification phase)
- 📁 Files: Created spec.md, requirements.md checklist, and PHR
- 🔁 Next prompts: Proceed to `/sp.plan` for implementation planning
- 🧠 Reflection: Specification is well-structured, complete, and addresses all user requirements with clear success metrics

## Evaluation notes (flywheel)

- Failure modes observed: Command line argument length limitation when creating feature
- Graders run and results (PASS/FAIL): All quality checks PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Create a more concise feature description method to avoid command line limitations