# Authentication Modification: Quick Start Guide

**Created**: 2025-01-08
**Purpose**: Development setup and initial configuration

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- Git repository cloned
- Existing FastAPI backend with SQLite
- Existing Docusaurus frontend

## Environment Setup

### 1. Backend Dependencies

Add these to your `requirements.txt`:

```txt
# Authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Email
aiosmtplib>=2.0.1
jinja2>=3.1.2

# Database
alembic>=1.12.0

# Security
python-dotenv>=1.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Frontend Dependencies

Add these to your `package.json`:

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "react-hook-form": "^7.47.0",
    "@hookform/resolvers": "^3.3.1",
    "zod": "^3.22.2"
  }
}
```

Install dependencies:
```bash
npm install
```

## Environment Configuration

Create/update `.env` file in backend root:

```env
# Authentication
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 7 days in minutes

# Email
EMAIL_FROM=noreply@yourdomain.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Frontend
FRONTEND_URL=http://localhost:3000

# Database (existing)
DATABASE_URL=sqlite:///./app.db
```

## Database Setup

### 1. Create New Models

Create `backend/src/models/auth.py`:

```python
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum

class ExperienceLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String(100))
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    background = relationship("UserBackground", uselist=False, back_populates="user")
    sessions = relationship("Session", back_populates="user")

class UserBackground(Base):
    __tablename__ = "user_backgrounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    experience_level = Column(Enum(ExperienceLevel))
    years_experience = Column(Integer)
    preferred_languages = Column(JSON)
    hardware_expertise = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="background")
```

### 2. Create Migration

```bash
alembic revision --autogenerate -m "Add authentication models"
alembic upgrade head
```

## Backend Implementation

### 1. Authentication Service

Create `backend/src/services/auth.py`:

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models.auth import User
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
```

### 2. API Routes

Create `backend/src/api/routes/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.auth import User
from ...services.auth import verify_password, create_access_token
from ..schemas.auth import RegisterRequest, LoginRequest, AuthResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(request.password)
    db_user = User(
        email=request.email,
        password_hash=hashed_password,
        name=request.name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create token
    access_token = create_access_token(data={"sub": db_user.email})

    return {
        "user": db_user,
        "requires_onboarding": True
    }
```

## Frontend Implementation

### 1. Authentication Context

Create `frontend/src/contexts/AuthContext.tsx`:

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';
import axios from 'axios';

interface User {
  id: string;
  email: string;
  name?: string;
  email_verified: boolean;
  has_background: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get('/api/v1/auth/me');
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await axios.post('/api/v1/auth/login', { email, password });
    setUser(response.data.user);

    // Redirect if onboarding needed
    if (response.data.requires_onboarding) {
      // Show onboarding modal
    }
  };

  const logout = async () => {
    await axios.post('/api/v1/auth/logout');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### 2. Login Button Component

Create `frontend/src/components/Auth/LoginButton.tsx`:

```typescript
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export function LoginButton() {
  const { user, login } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  if (user) {
    return <UserProfile user={user} />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(formData.email, formData.password);
      setShowModal(false);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <>
      <button onClick={() => setShowModal(true)}>
        Login
      </button>

      {showModal && (
        <div className="modal">
          <form onSubmit={handleSubmit}>
            <h2>Login</h2>
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
            />
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
            />
            <button type="submit">Login</button>
            <button type="button" onClick={() => setShowModal(false)}>
              Cancel
            </button>
          </form>
        </div>
      )}
    </>
  );
}
```

## Testing

### Backend Tests

Create `backend/tests/test_auth.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..main import app
from ..database import get_db
from ..models.auth import User

client = TestClient(app)

def test_register_user(db: Session):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["requires_onboarding"] is True

def test_login_user(db: Session):
    # First register
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123"
    })

    # Then login
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
```

### Frontend Tests

Create `frontend/src/components/Auth/__tests__/LoginButton.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { AuthProvider } from '../../../contexts/AuthContext';
import { LoginButton } from '../LoginButton';

describe('LoginButton', () => {
  it('renders login button when not authenticated', () => {
    render(
      <AuthProvider>
        <LoginButton />
      </AuthProvider>
    );

    expect(screen.getByText('Login')).toBeInTheDocument();
  });

  it('opens modal when login button clicked', () => {
    render(
      <AuthProvider>
        <LoginButton />
      </AuthProvider>
    );

    fireEvent.click(screen.getByText('Login'));
    expect(screen.getByText('Login')).toBeInTheDocument();
  });
});
```

## Common Issues

### Backend
1. **CORS errors**: Ensure frontend URL is in CORS origins
2. **Database connection**: Check DATABASE_URL in .env
3. **JWT errors**: Verify SECRET_KEY is set

### Frontend
1. **API errors**: Check proxy configuration in package.json
2. **Auth context**: Wrap app with AuthProvider
3. **Modal styling**: Add appropriate CSS for modal

## Next Steps

1. Complete the implementation following the full plan
2. Add comprehensive error handling
3. Implement email service integration
4. Add rate limiting and security middleware
5. Write comprehensive tests
6. Set up CI/CD pipeline