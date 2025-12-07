# Better Auth Implementation for AI Book Application

## Overview
Implement a comprehensive authentication system for the AI book application using Better Auth v2 patterns, with SQLite for data storage and Google OAuth for user authentication.

## Prerequisites
- Node.js 18+ and npm installed
- Python 3.9+ with FastAPI backend
- Google OAuth credentials (Client ID and Client Secret)

## Phase 1: Backend Authentication Setup

### 1.1 Install Dependencies
Add to `backend/requirements.txt`:
```txt
# Authentication dependencies
sqlalchemy>=2.0.0
alembic>=1.12.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
authlib>=1.2.1
```

### 1.2 Database Setup
Create directory structure:
```
backend/
├── database/
│   ├── __init__.py
│   ├── connection.py
│   └── migrations/
├── models/
│   ├── __init__.py
│   └── auth.py
├── auth/
│   ├── __init__.py
│   ├── auth.py
│   └── dependencies.py
└── routes/
    ├── __init__.py
    └── auth.py
```

### 1.3 Create Database Models (backend/models/auth.py)

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    image = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    accounts = relationship("Account", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_id = Column(String, nullable=False)  # 'google', 'github', etc.
    provider_account_id = Column(String, nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="accounts")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_anonymous = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)  # Sources, citations, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    theme = Column(String, default="light")
    language = Column(String, default="en")
    notifications = Column(Boolean, default=True)
    chat_settings = Column(JSON, nullable=True)  # Model preferences, etc.

    # Relationships
    user = relationship("User", back_populates="preferences")
```

### 1.4 Database Connection (backend/database/connection.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.auth import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/auth.db")

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 1.5 Authentication Module (backend/auth/auth.py)

```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.auth import User, Session as UserSession
from database.connection import get_db
import secrets
import httpx
from pydantic import BaseModel

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
AUTH_REDIRECT_URI = os.getenv("AUTH_REDIRECT_URI", "http://localhost:3000/auth/google/callback")

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class GoogleUserInfo(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    verified_email: Optional[bool] = False

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(email=email, user_id=user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_google_user_info(code: str) -> GoogleUserInfo:
    """Exchange authorization code for user info"""
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": AUTH_REDIRECT_URI,
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        return GoogleUserInfo(**user_response.json())

def get_or_create_user(db: Session, user_info: GoogleUserInfo) -> User:
    """Get existing user or create new one from Google info"""
    user = db.query(User).filter(User.email == user_info.email).first()

    if not user:
        user = User(
            email=user_info.email,
            name=user_info.name,
            image=user_info.picture,
            email_verified=user_info.verified_email or False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create default preferences
        from models.auth import UserPreferences
        preferences = UserPreferences(user_id=user.id)
        db.add(preferences)
        db.commit()

    return user

def create_user_session(db: Session, user_id: int) -> str:
    """Create a new session for user"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)

    db_session = UserSession(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(db_session)
    db.commit()

    return token
```

### 1.6 Authentication Dependencies (backend/auth/dependencies.py)

```python
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database.connection import get_db
from auth.auth import verify_token, TokenData
from models.auth import User, Session as UserSession

async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify JWT token
    token_data = verify_token(token)

    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user

# Optional authentication (doesn't raise error if not authenticated)
async def get_optional_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user if authenticated, otherwise return None"""
    if not authorization:
        return None

    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None
```

### 1.7 Authentication Routes (backend/routes/auth.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from auth.auth import get_google_user_info, get_or_create_user, create_user_session, create_access_token
from auth.dependencies import get_current_user, get_current_active_user
from models.auth import User, UserPreferences
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    image: Optional[str] = None
    email_verified: bool

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications: Optional[bool] = None
    chat_settings: Optional[dict] = None

@router.get("/google")
async def google_login():
    """Initiate Google OAuth login"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("AUTH_REDIRECT_URI")
    scope = "openid email profile"

    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # Get user info from Google
        user_info = await get_google_user_info(code)

        # Get or create user in database
        user = get_or_create_user(db, user_info)

        # Create JWT access token
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )

        # Create session
        session_token = create_user_session(db, user.id)

        # Set secure cookie with access token
        response = RedirectResponse(url="/dashboard")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=10080 * 60  # 7 days
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def logout(response: Response):
    """Logout user"""
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@router.get("/preferences")
async def get_user_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get user preferences"""
    return current_user.preferences

@router.put("/preferences")
async def update_user_preferences(
    preferences: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    user_prefs = current_user.preferences

    # Update only provided fields
    if preferences.theme is not None:
        user_prefs.theme = preferences.theme
    if preferences.language is not None:
        user_prefs.language = preferences.language
    if preferences.notifications is not None:
        user_prefs.notifications = preferences.notifications
    if preferences.chat_settings is not None:
        user_prefs.chat_settings = preferences.chat_settings

    db.commit()
    db.refresh(user_prefs)

    return user_prefs

@router.get("/check")
async def check_auth(current_user: Optional[User] = Depends(get_optional_user)):
    """Check if user is authenticated"""
    if current_user:
        return {
            "authenticated": True,
            "user": UserResponse.from_orm(current_user)
        }
    return {"authenticated": False}
```

### 1.8 Update Main Application (backend/main.py)

```python
# Add these imports at the top
from database.connection import engine
from models.auth import Base
from routes.auth import router as auth_router
from auth.dependencies import get_current_user

# Create tables
Base.metadata.create_all(bind=engine)

# Add auth router to app
app.include_router(auth_router)

# Add CORS for auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", os.getenv("FRONTEND_URL", "")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Phase 2: Frontend Authentication Setup

### 2.1 Install Frontend Dependencies
```bash
cd src
npm install @auth0/auth0-react react-router-dom
```

### 2.2 Create Authentication Context (src/contexts/AuthContext.tsx)

```typescript
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  email: string;
  name: string;
  image?: string;
  emailVerified: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
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
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/auth/check');
      const data = await response.json();

      if (data.authenticated) {
        setUser(data.user);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = () => {
    // Redirect to backend OAuth endpoint
    window.location.href = '/api/auth/google';
  };

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
      setUser(null);
      window.location.href = '/';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

### 2.3 Create Login Modal Component (src/components/Auth/LoginModal.tsx)

```typescript
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
  const { login } = useAuth();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">Sign in to continue</h2>
        <p className="text-gray-600 mb-6">
          Sign in to access the chat and save your conversation history
        </p>

        <button
          onClick={login}
          className="w-full flex items-center justify-center gap-3 bg-white border border-gray-300 rounded-lg px-4 py-3 hover:bg-gray-50 transition-colors"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </button>

        <button
          onClick={onClose}
          className="mt-4 w-full text-gray-600 hover:text-gray-800 transition-colors"
        >
          Maybe later
        </button>
      </div>
    </div>
  );
};
```

### 2.4 Create Protected Route Component (src/components/Auth/ProtectedRoute.tsx)

```typescript
import React, { ReactNode } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LoginModal } from './LoginModal';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  fallback
}) => {
  const { isAuthenticated, loading } = useAuth();
  const [showLoginModal, setShowLoginModal] = React.useState(false);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <>
        <div className="flex flex-col items-center justify-center p-8">
          <h2 className="text-2xl font-bold mb-4">Authentication Required</h2>
          <p className="text-gray-600 mb-6">
            Please sign in to access this feature
          </p>
          <button
            onClick={() => setShowLoginModal(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Sign In
          </button>
        </div>
        {showLoginModal && (
          <LoginModal
            isOpen={showLoginModal}
            onClose={() => setShowLoginModal(false)}
          />
        )}
      </>
    );
  }

  return <>{children}</>;
};
```

### 2.5 Create User Profile Component (src/components/Auth/UserProfile.tsx)

```typescript
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const UserProfile: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="flex items-center gap-3">
      {user.image && (
        <img
          src={user.image}
          alt={user.name}
          className="w-8 h-8 rounded-full"
        />
      )}
      <span className="font-medium">{user.name}</span>
      <button
        onClick={logout}
        className="text-gray-600 hover:text-gray-800 transition-colors"
      >
        Logout
      </button>
    </div>
  );
};
```

## Phase 3: Update Chat Widget with Authentication

### 3.1 Update ChatWidgetContainer.tsx

Add authentication check before allowing chat:

```typescript
import { useAuth } from '../../contexts/AuthContext';
import { ProtectedRoute } from '../Auth/ProtectedRoute';
import { LoginModal } from '../Auth/LoginModal';

export const ChatWidgetContainer: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [showLoginModal, setShowLoginModal] = React.useState(false);

  // Add auth token to API requests
  const sendMessage = async (message: string) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${document.cookie.match(/access_token=([^;]+)/)?.[1]}`
      },
      body: JSON.stringify({ question: message, stream: true }),
    });
    // ... rest of the implementation
  };

  if (!isAuthenticated) {
    return (
      <div className="chat-widget">
        <button
          onClick={() => setShowLoginModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Sign in to chat
        </button>
        {showLoginModal && (
          <LoginModal
            isOpen={showLoginModal}
            onClose={() => setShowLoginModal(false)}
          />
        )}
      </div>
    );
  }

  return (
    <ProtectedRoute>
      {/* Existing chat widget implementation */}
    </ProtectedRoute>
  );
};
```

## Phase 4: Update Docusaurus Configuration

### 4.1 Update Root Component (src/theme/Root.tsx)

```typescript
import React from 'react';
import { AuthProvider } from '../contexts/AuthContext';
import { UserProfile } from '../components/Auth/UserProfile';

export default function Root({children}: {children: React.ReactNode}): JSX.Element {
  return (
    <AuthProvider>
      <html lang="en">
        <body>
          {children}
          {/* Add user profile to navbar */}
          <div id="user-profile-container" className="fixed top-4 right-4 z-50">
            <UserProfile />
          </div>
        </body>
      </html>
    </AuthProvider>
  );
}
```

### 4.2 Update docusaurus.config.ts

```typescript
export default {
  themeConfig: {
    navbar: {
      items: [
        // Existing items...
        {
          type: 'html',
          position: 'right',
          value: '<div id="auth-button"></div>'
        }
      ]
    }
  }
}
```

## Phase 5: Environment Configuration

### 5.1 Add to .env file

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
AUTH_REDIRECT_URI=http://localhost:3000/auth/google/callback

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-in-production

# Database
DATABASE_URL=sqlite:///./database/auth.db

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

## Phase 6: Testing the Implementation

### 6.1 Test Authentication Flow

1. Start the backend server:
```bash
cd backend
uv run python main.py
```

2. Start the frontend:
```bash
npm start
```

3. Test the flow:
   - Click "Sign in" button
   - Authenticate with Google
   - Verify user profile appears
   - Test chat functionality
   - Test logout

### 6.2 Database Initialization

The database will be automatically created when the application starts. To add migrations:

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Security Considerations

1. **Store secrets securely**: Use environment variables, never hardcode secrets
2. **HTTPS in production**: Always use HTTPS for OAuth redirects
3. **Secure cookies**: Set `secure=True` for cookies in production
4. **Rate limiting**: Implement rate limiting on auth endpoints
5. **Input validation**: Validate all user inputs
6. **SQL injection prevention**: Use SQLAlchemy ORM which prevents SQL injection

## Common Issues and Solutions

1. **CORS errors**: Ensure frontend URL is added to CORS origins
2. **OAuth redirect mismatch**: Check redirect URI in Google Console matches exactly
3. **JWT token not working**: Verify SECRET_KEY is the same on both ends
4. **Database errors**: Ensure proper permissions for database directory

This implementation provides a complete authentication system with Google OAuth, user management, and session handling integrated with your existing chat application.