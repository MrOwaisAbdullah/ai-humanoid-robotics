# FastAPI JWT Authentication and Session Management Best Practices

## Table of Contents
1. [JWT Token Creation, Validation, and Refresh Patterns](#jwt-token-patterns)
2. [Anonymous Session Tracking in FastAPI](#anonymous-session-tracking)
3. [API Endpoint Patterns for Guest and Authenticated Users](#api-endpoint-patterns)
4. [Database Schema Design for Sessions and User Backgrounds](#database-schema-design)
5. [Security Best Practices for JWT in FastAPI](#security-best-practices)
6. [Rate Limiting and CSRF Protection Patterns](#rate-limiting-csrf)
7. [Recommended Libraries and Tools](#recommended-libraries)

## JWT Token Creation, Validation, and Refresh Patterns <a name="jwt-token-patterns"></a>

### 1. JWT Token Creation with FastAPI

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings

# Configuration
class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Creation Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
```

### 2. Token Validation Patterns

```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if username is None or token_type != "access":
            raise credentials_exception

        # Fetch user from database
        user = get_user_from_db(username)
        if user is None:
            raise credentials_exception

        return user
    except JWTError:
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### 3. Refresh Token Pattern

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    # Store refresh token in database
    store_refresh_token(user.id, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/refresh")
async def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if username is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Verify refresh token exists in database
        if not verify_refresh_token(username, refresh_token):
            raise HTTPException(status_code=401, detail="Refresh token not found")

        # Create new access token
        access_token = create_access_token(data={"sub": username})

        return {"access_token": access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
```

### 4. Using FastAPI-JWT Library (Recommended)

```python
from datetime import timedelta
from fastapi import FastAPI, Security, HTTPException
from fastapi_jwt import (
    JwtAccessBearerCookie,
    JwtAuthorizationCredentials,
    JwtRefreshBearer,
)

app = FastAPI()

# Access token from bearer header and cookie (bearer priority)
access_security = JwtAccessBearerCookie(
    secret_key=settings.SECRET_KEY,
    auto_error=False,
    access_expires_delta=timedelta(hours=1)
)

# Refresh token from bearer header
refresh_security = JwtRefreshBearer(
    secret_key=settings.SECRET_KEY,
    auto_error=True
)

@app.post("/auth")
def auth():
    subject = {"username": "username", "role": "user", "user_id": 123}

    access_token = access_security.create_access_token(subject=subject)
    refresh_token = refresh_security.create_refresh_token(subject=subject)

    return {"access_token": access_token, "refresh_token": refresh_token}

@app.post("/refresh")
def refresh(credentials: JwtAuthorizationCredentials = Security(refresh_security)):
    access_token = access_security.create_access_token(subject=credentials.subject)
    refresh_token = refresh_security.create_refresh_token(
        subject=credentials.subject,
        expires_delta=timedelta(days=2)
    )
    return {"access_token": access_token, "refresh_token": refresh_token}
```

## Anonymous Session Tracking in FastAPI <a name="anonymous-session-tracking"></a>

### 1. Session Middleware Implementation

```python
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import json
from datetime import datetime, timedelta

class AnonymousSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, session_timeout: int = 3600):
        super().__init__(app)
        self.session_timeout = session_timeout

    async def dispatch(self, request: Request, call_next):
        # Get session ID from cookie or create new one
        session_id = request.cookies.get("anonymous_session")

        if not session_id:
            session_id = str(uuid.uuid4())

        # Add session info to request state
        request.state.session_id = session_id
        request.state.is_anonymous = True

        # Process request
        response = await call_next(request)

        # Set session cookie if new session
        if not request.cookies.get("anonymous_session"):
            response.set_cookie(
                key="anonymous_session",
                value=session_id,
                max_age=self.session_timeout,
                httponly=True,
                secure=True,
                samesite="lax"
            )

        return response

app.add_middleware(AnonymousSessionMiddleware, session_timeout=3600)
```

### 2. Session Storage with Redis

```python
import redis
import json
from datetime import datetime, timezone

class SessionManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)

    async def create_anonymous_session(self, session_id: str) -> dict:
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "is_anonymous": True,
            "page_views": 0,
            "actions": []
        }

        # Store in Redis with TTL
        await self.redis_client.setex(
            f"session:{session_id}",
            3600,  # 1 hour TTL
            json.dumps(session_data)
        )

        return session_data

    async def get_session(self, session_id: str) -> dict:
        session_data = await self.redis_client.get(f"session:{session_id}")
        if session_data:
            return json.loads(session_data)
        return None

    async def update_session(self, session_id: str, updates: dict):
        session = await self.get_session(session_id)
        if session:
            session.update(updates)
            session["last_activity"] = datetime.now(timezone.utc).isoformat()

            await self.redis_client.setex(
                f"session:{session_id}",
                3600,
                json.dumps(session)
            )

    async def convert_anonymous_to_user(self, session_id: str, user_id: int):
        session = await self.get_session(session_id)
        if session:
            # Migrate session data to user
            await self.migrate_session_to_user(session, user_id)
            # Delete anonymous session
            await self.redis_client.delete(f"session:{session_id}")
```

### 3. Dependency for Session Management

```python
from typing import Optional
from fastapi import Depends, HTTPException
from starlette.requests import Request

async def get_session_info(request: Request) -> dict:
    session_id = getattr(request.state, 'session_id', None)
    if not session_id:
        raise HTTPException(status_code=400, detail="Session not found")

    session_manager = SessionManager()
    session = await session_manager.get_session(session_id)

    if not session:
        # Create new session if not exists
        session = await session_manager.create_anonymous_session(session_id)

    return session

async def get_current_user_or_session(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    session: dict = Depends(get_session_info)
):
    if token:
        # Try to get authenticated user
        try:
            return await get_current_user(token)
        except HTTPException:
            # Invalid token, fall back to session
            pass

    # Return anonymous user with session info
    return {
        "is_anonymous": True,
        "session_id": session["session_id"],
        "created_at": session["created_at"]
    }
```

## API Endpoint Patterns for Guest and Authenticated Users <a name="api-endpoint-patterns"></a>

### 1. Flexible Endpoint Design

```python
from typing import Union, Optional
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

# Response models
class GuestResponse(BaseModel):
    message: str
    is_guest: bool = True
    session_data: Optional[dict] = None

class AuthResponse(BaseModel):
    message: str
    user_data: dict
    is_guest: bool = False

class UnifiedResponse(BaseModel):
    message: str
    data: Union[GuestResponse, AuthResponse]

# Endpoint with dual support
@app.get("/api/items", response_model=UnifiedResponse)
async def get_items(
    current_user_or_session = Depends(get_current_user_or_session),
    session: dict = Depends(get_session_info)
):
    if current_user_or_session.get("is_anonymous"):
        # Guest user logic
        items = await get_guest_items(session["session_id"])
        return UnifiedResponse(
            message="Items retrieved for guest",
            data=GuestResponse(
                message="Guest access",
                session_data={"page_views": session.get("page_views", 0)}
            )
        )
    else:
        # Authenticated user logic
        items = await get_user_items(current_user_or_session.id)
        return UnifiedResponse(
            message="Items retrieved for authenticated user",
            data=AuthResponse(
                message="Authenticated access",
                user_data={"username": current_user_or_session.username}
            )
        )
```

### 2. Progressive Authentication Pattern

```python
@app.post("/api/action")
async def perform_action(
    action_data: ActionCreate,
    current_user_or_session = Depends(get_current_user_or_session),
    session: dict = Depends(get_session_info),
    session_manager: SessionManager = Depends()
):
    if current_user_or_session.get("is_anonymous"):
        # Check if action requires authentication
        if action_data.requires_auth:
            raise HTTPException(
                status_code=401,
                detail="Authentication required for this action"
            )

        # Track anonymous action
        await session_manager.update_session(
            session["session_id"],
            {
                "actions": session.get("actions", []) + [{
                    "type": action_data.type,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            }
        )

        # Perform guest action
        result = await perform_guest_action(action_data, session["session_id"])

    else:
        # Authenticated user action
        result = await perform_user_action(action_data, current_user_or_session.id)

    return result
```

### 3. Middleware for Request Context

```python
class UserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Try to get user from token
        token = request.headers.get("authorization")
        user = None
        is_anonymous = True

        if token:
            try:
                user = await get_user_from_token(token)
                is_anonymous = False
            except:
                pass

        # Get session info
        session_id = request.cookies.get("anonymous_session")
        if session_id:
            session = await get_session(session_id)
        else:
            session = None

        # Add to request state
        request.state.user = user
        request.state.is_anonymous = is_anonymous
        request.state.session = session

        response = await call_next(request)
        return response
```

## Database Schema Design for Sessions and User Backgrounds <a name="database-schema-design"></a>

### 1. SQLAlchemy Models

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)

    # Status fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Background/preference fields
    background_info = Column(Text)  # User's professional/background info
    preferences = Column(JSON)  # User preferences as JSON
    skill_level = Column(String, default="beginner")  # beginner, intermediate, advanced

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    sessions = relationship("Session", back_populates="user")
    oauth_accounts = relationship("OAuthAccount", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for anonymous

    # Session data
    session_data = Column(JSON)  # Stores session state, preferences, etc.
    page_views = Column(Integer, default=0)
    actions_taken = Column(JSON)  # Track user actions

    # Metadata
    ip_address = Column(String)
    user_agent = Column(Text)
    is_anonymous = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="sessions")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Status
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True))
    device_info = Column(JSON)

    # Relationships
    user = relationship("User")

class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # google, github, etc.
    provider_user_id = Column(String, nullable=False)

    # OAuth data
    access_token = Column(Text)
    refresh_token = Column(Text)
    expires_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="oauth_accounts")

class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=True)

    # Activity details
    activity_type = Column(String, nullable=False)  # login, page_view, action, etc.
    activity_data = Column(JSON)  # Additional data about the activity
    resource_id = Column(String)  # ID of resource if applicable
    resource_type = Column(String)  # Type of resource

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 2. Migration for Session/User Tracking

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('background_info', sa.Text(), nullable=True),
        sa.Column('preferences', postgresql.JSONB(), nullable=True),
        sa.Column('skill_level', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_data', postgresql.JSONB(), nullable=True),
        sa.Column('page_views', sa.Integer(), nullable=True),
        sa.Column('actions_taken', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_session_id'), 'sessions', ['session_id'], unique=True)
```

## Security Best Practices for JWT in FastAPI <a name="security-best-practices"></a>

### 1. Token Security Configuration

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import base64

# Generate secure key
def generate_secret_key():
    password = secrets.token_bytes(32)
    salt = secrets.token_bytes(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key.decode('utf-8')

# JWT Configuration
class JWTSettings(BaseSettings):
    SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Token audience and issuer
    TOKEN_AUDIENCE: str = "my-app:api"
    TOKEN_ISSUER: str = "my-app:auth"

    class Config:
        env_file = ".env"

jwt_settings = JWTSettings()
```

### 2. Enhanced Token Creation

```python
def create_secure_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    # Add security claims
    to_encode.update({
        "iss": jwt_settings.TOKEN_ISSUER,
        "aud": jwt_settings.TOKEN_AUDIENCE,
        "type": "access",
        "jti": str(uuid.uuid4()),  # Unique token ID
        "iat": datetime.now(timezone.utc)
    })

    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode["exp"] = expire

    # Create token
    encoded_jwt = jwt.encode(
        to_encode,
        jwt_settings.SECRET_KEY,
        algorithm=jwt_settings.ALGORITHM,
        headers={"kid": "key1"}  # Key ID for rotation
    )

    # Store token metadata in database
    await store_token_metadata(to_encode["jti"], to_encode["sub"], expire)

    return encoded_jwt
```

### 3. Token Validation with Security Checks

```python
async def validate_jwt_token(token: str) -> dict:
    try:
        # Decode token with validation
        payload = jwt.decode(
            token,
            jwt_settings.SECRET_KEY,
            algorithms=[jwt_settings.ALGORITHM],
            audience=jwt_settings.TOKEN_AUDIENCE,
            issuer=jwt_settings.TOKEN_ISSUER
        )

        # Additional security checks
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Invalid token format")

        # Check if token is revoked
        if await is_token_revoked(jti):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        # Check if token blacklisted
        if await is_token_blacklisted(jti):
            raise HTTPException(status_code=401, detail="Token is blacklisted")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Token revocation
async def revoke_token(jti: str):
    await add_to_blacklist(jti)

# Token refresh validation
async def validate_refresh_token(token: str):
    payload = await validate_jwt_token(token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check if refresh token exists and is not revoked
    refresh_token = await get_refresh_token_by_jti(payload.get("jti"))
    if not refresh_token or refresh_token.is_revoked:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    return payload
```

### 4. CSRF Protection

```python
from fastapi import FastAPI, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

security = HTTPBearer()

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exempt_paths: list = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or []

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for exempt paths and GET/HEAD/OPTIONS
        if (request.url.path in self.exempt_paths or
            request.method in ["GET", "HEAD", "OPTIONS"]):
            return await call_next(request)

        # Check for CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            raise HTTPException(status_code=403, detail="CSRF token missing")

        # Validate CSRF token against session
        session_csrf = await get_session_csrf_token(request)
        if not secrets.compare_digest(csrf_token, session_csrf):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")

        return await call_next(request)

# Generate CSRF token
async def generate_csrf_token(session_id: str) -> str:
    token = secrets.token_urlsafe(32)
    await store_csrf_token(session_id, token)
    return token
```

## Rate Limiting and CSRF Protection Patterns <a name="rate-limiting-csrf"></a>

### 1. Rate Limiting with fastapi-cap

```python
from fastapicap import (
    RateLimiter,
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter
)
from fastapi import Depends, FastAPI, Request
from typing import Callable

app = FastAPI()

# Different rate limiters for different use cases
# Anonymous users: 10 requests per minute
anonymous_limiter = RateLimiter(limit=10, minutes=1)

# Authenticated users: 100 requests per minute
auth_limiter = RateLimiter(limit=100, minutes=1)

# Login endpoint: 5 attempts per 15 minutes
login_limiter = RateLimiter(limit=5, minutes=15)

# Token refresh: 10 per hour
refresh_limiter = RateLimiter(limit=10, hours=1)

# Custom key function for user-based rate limiting
def get_user_key(request: Request) -> str:
    # Try to get user ID from JWT
    auth_header = request.headers.get("authorization")
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, jwt_settings.SECRET_KEY, algorithms=[jwt_settings.ALGORITHM])
            return f"user:{payload.get('sub')}"
        except:
            pass

    # Fall back to IP
    return f"ip:{request.client.host}"

# User-specific rate limiter
user_limiter = RateLimiter(
    limit=1000,
    hours=1,
    key_func=get_user_key
)

@app.post("/token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    _: None = Depends(login_limiter)
):
    # Login logic
    pass

@app.post("/refresh")
async def refresh_token(
    request: Request,
    _: None = Depends(refresh_limiter)
):
    # Refresh logic
    pass

@app.get("/api/data")
async def get_data(
    request: Request,
    current_user_or_session = Depends(get_current_user_or_session)
):
    # Apply different rate limits based on authentication
    if current_user_or_session.get("is_anonymous"):
        await anonymous_limiter(request)
    else:
        await auth_limiter(request)

    # API logic
    pass
```

### 2. Advanced Rate Limiting with Redis

```python
import redis
import asyncio
from typing import Optional

class AdvancedRateLimiter:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        unit: str = "seconds"
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed using sliding window algorithm
        Returns: (is_allowed, info_dict)
        """
        current_time = int(time.time())
        window_start = current_time - window

        # Remove old entries
        await self.redis.zremrangebyscore(key, 0, window_start)

        # Count current requests
        current_requests = await self.redis.zcard(key)

        if current_requests >= limit:
            # Get oldest request for retry-after
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            retry_after = int(oldest[0][1] + window - current_time) if oldest else window

            return False, {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "retry_after": retry_after,
                "reset_time": oldest[0][1] + window if oldest else current_time + window
            }

        # Add current request
        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, window)
        await pipe.execute()

        return True, {
            "allowed": True,
            "limit": limit,
            "remaining": limit - current_requests - 1,
            "retry_after": 0,
            "reset_time": current_time + window
        }

    async def check_multiple_limits(
        self,
        key: str,
        limits: list[tuple[int, int, str]]
    ) -> tuple[bool, dict]:
        """
        Check multiple rate limits
        limits: List of (limit, window, unit) tuples
        """
        for limit, window, unit in limits:
            allowed, info = await self.is_allowed(key, limit, window, unit)
            if not allowed:
                return False, info

        return True, {"allowed": True, "limits_checked": len(limits)}

# Usage with FastAPI
rate_limiter = AdvancedRateLimiter()

@app.get("/api/protected")
async def protected_endpoint(
    request: Request,
    current_user_or_session = Depends(get_current_user_or_session)
):
    # Get rate limit key
    if current_user_or_session.get("is_anonymous"):
        key = f"anonymous:{request.client.host}"
        limits = [(100, 3600, "seconds")]  # 100 per hour
    else:
        key = f"user:{current_user_or_session.id}"
        limits = [
            (1000, 3600, "seconds"),  # 1000 per hour
            (100, 60, "seconds")      # 100 per minute
        ]

    allowed, info = await rate_limiter.check_multiple_limits(key, limits)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset_time"]),
                "Retry-After": str(info["retry_after"])
            }
        )

    # API logic
    pass
```

### 3. IP-based Protection

```python
from fastapi_guard import SecurityMiddleware, SecurityConfig

app = FastAPI()

# Security configuration
security_config = SecurityConfig(
    # Rate limiting
    rate_limit=100,
    rate_limit_window=60,

    # IP filtering
    whitelist=["127.0.0.1", "10.0.0.0/8"],
    blacklist=["192.168.1.100"],

    # Auto-banning for suspicious activity
    enable_penetration_detection=True,
    auto_ban_threshold=10,
    auto_ban_duration=3600,

    # Country blocking
    blocked_countries=["XX"],  # Add country codes to block

    # Enable Redis for distributed deployments
    enable_redis=True,
    redis_url="redis://localhost:6379"
)

app.add_middleware(SecurityMiddleware, config=security_config)
```

## Recommended Libraries and Tools <a name="recommended-libraries"></a>

### 1. Authentication Libraries

- **fastapi-jwt** - Native FastAPI JWT extension with OpenAPI support
  ```bash
  pip install fastapi-jwt
  ```

- **fastapi-users** - Complete user management system
  ```bash
  pip install fastapi-users[sqlalchemy]
  ```

- **python-jose** - JWT implementation
  ```bash
  pip install python-jose[cryptography]
  ```

- **passlib** - Password hashing
  ```bash
  pip install passlib[bcrypt]
  ```

### 2. Session Management

- **redis** - For fast session storage
  ```bash
  pip install redis
  ```

- **aiosession** - Async session management
  ```bash
  pip install aiosession
  ```

### 3. Security and Rate Limiting

- **fastapi-cap** - Advanced rate limiting
  ```bash
  pip install fastapi-cap
  ```

- **fastapi-guard** - Security middleware
  ```bash
  pip install fastapi-guard
  ```

- **itsdangerous** - CSRF token generation
  ```bash
  pip install itsdangerous
  ```

### 4. Database

- **SQLAlchemy** - ORM for database operations
  ```bash
  pip install sqlalchemy
  ```

- **alembic** - Database migrations
  ```bash
  pip install alembic
  ```

- **asyncpg** - Async PostgreSQL driver
  ```bash
  pip install asyncpg
  ```

## Summary

This comprehensive guide covers the essential patterns and best practices for implementing JWT authentication and session management in FastAPI applications. Key takeaways:

1. **Use short-lived access tokens** with refresh tokens for better security
2. **Implement anonymous session tracking** to improve user experience
3. **Design flexible endpoints** that work for both authenticated and guest users
4. **Use proper database schema** to track sessions and user backgrounds
5. **Implement multiple layers of security** including CSRF protection and rate limiting
6. **Choose appropriate libraries** that integrate well with FastAPI's ecosystem

Remember to:
- Always use HTTPS in production
- Store secrets securely using environment variables
- Implement proper error handling and logging
- Regularly rotate JWT secrets
- Monitor and audit authentication attempts
- Follow OWASP security guidelines

This research provides a solid foundation for building secure, scalable authentication systems in FastAPI applications.

## Sources

1. [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
2. [fastapi-jwt Library](https://github.com/k4black/fastapi-jwt)
3. [fastapi-cap Rate Limiting](https://github.com/devbijay/fastapi-cap)
4. [fastapi-guard Security](https://github.com/rennf93/fastapi-guard)
5. [FastAPI Session Management Research](https://testdriven.io/blog/fastapi-sessions-authentication/)
6. [FastAPI-Users Documentation](https://fastapi-users.github.io/fastapi-users/)