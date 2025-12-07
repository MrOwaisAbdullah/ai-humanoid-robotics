import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import secrets
import hashlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from database.config import get_db
from models.auth import User, Session, Account, UserPreferences

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 10080))  # 7 days

# Password hashing (not used for OAuth but kept for completeness)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# OAuth configuration
config = Config('.env')
oauth = OAuth(config)

# Configure Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (extension point for future features like account suspension)"""
    return current_user


def create_user_session(db: Session, user: User) -> str:
    """Create a new session for user and return token"""
    # Delete existing sessions for this user (optional - remove if you want multiple sessions)
    db.query(Session).filter(Session.user_id == user.id).delete()

    # Create new session token
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    db_session = Session(
        user_id=user.id,
        token=session_token,
        expires_at=expires_at
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return session_token


def get_or_create_user(db: Session, user_info: dict) -> User:
    """Get existing user or create new one from OAuth info"""
    email = user_info.get('email')
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()

    if user:
        # Update user info if needed
        user.name = user_info.get('name', user.name)
        user.image_url = user_info.get('picture', user.image_url)
        user.email_verified = user_info.get('email_verified', user.email_verified)
        user.updated_at = datetime.utcnow()
    else:
        # Create new user
        user = User(
            email=email,
            name=user_info.get('name', email.split('@')[0]),
            image_url=user_info.get('picture'),
            email_verified=user_info.get('email_verified', False)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create default preferences
        preferences = UserPreferences(user_id=user.id)
        db.add(preferences)
        db.commit()

    return user


def create_or_update_account(db: Session, user: User, provider: str, account_info: dict) -> Account:
    """Create or update OAuth account"""
    # For Google OAuth, the 'sub' field is in the userinfo
    provider_account_id = account_info.get('sub')
    if not provider_account_id:
        # Fallback: use email as provider account ID if sub is not available
        provider_account_id = account_info.get('email')
        if not provider_account_id:
            # Final fallback: use user.id as provider account ID
            provider_account_id = str(user.id)

    # Print for debugging
    print(f"Provider account ID: {provider_account_id}")
    print(f"Account info keys: {list(account_info.keys()) if account_info else 'None'}")

    # Check if account exists
    account = db.query(Account).filter(
        Account.user_id == user.id,
        Account.provider == provider,
        Account.provider_account_id == provider_account_id
    ).first()

    if account:
        # Update account info
        account.access_token = account_info.get('access_token')
        account.refresh_token = account_info.get('refresh_token')
        account.expires_at = datetime.fromtimestamp(account_info.get('expires_at', 0)) if account_info.get('expires_at') else None
        account.token_type = account_info.get('token_type')
        account.scope = account_info.get('scope')
        account.updated_at = datetime.utcnow()
    else:
        # Create new account
        account = Account(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=account_info.get('access_token'),
            refresh_token=account_info.get('refresh_token'),
            expires_at=datetime.fromtimestamp(account_info.get('expires_at', 0)) if account_info.get('expires_at') else None,
            token_type=account_info.get('token_type'),
            scope=account_info.get('scope')
        )
        db.add(account)

    db.commit()
    db.refresh(account)
    return account


def invalidate_user_sessions(db: Session, user: User) -> None:
    """Invalidate all sessions for a user"""
    db.query(Session).filter(Session.user_id == user.id).delete()
    db.commit()