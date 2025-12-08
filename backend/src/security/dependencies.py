"""
FastAPI security dependencies for authentication.

This module provides dependency functions for protecting routes
with JWT authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.database.config import get_db
from src.models.auth import User, Session, AnonymousSession
from src.services.auth import verify_token, SECRET_KEY, ALGORITHM
from src.services.auth import verify_password, get_password_hash
from src.schemas.auth import TokenData

# HTTP Bearer scheme for token authentication
bearer_scheme = HTTPBearer(auto_error=False)

# OAuth2PasswordRequestForm for login
oauth2_scheme = OAuth2PasswordRequestForm


def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> str:
    """
    Extract and verify JWT token from Authorization header.

    Returns:
        The token string if valid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token expiration
    exp = payload.get("exp")
    if exp is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing expiration",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if datetime.utcnow().timestamp() > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


def get_current_user(
    token: str = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Returns:
        The authenticated user object
    """
    # Verify token and get user_id
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Check if user is verified (optional)
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.

    This is a placeholder for future user status checks.
    """
    # In the future, you might check if user is active, suspended, etc.
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, but don't raise an error if not.

    Returns:
        The authenticated user object or None
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token)

        if payload is None:
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        return user if user and user.email_verified else None

    except Exception:
        return None


def get_current_user_with_session(
    token: str = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> tuple[User, Session]:
    """
    Get the current user and their active session.

    Returns:
        Tuple of (user, session) objects
    """
    # Get user
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Get user and session from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Get active session
    session = db.query(Session).filter(
        Session.user_id == user_id,
        Session.expires_at > datetime.utcnow()
    ).first()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session found. Please login again."
        )

    return user, session


def validate_anonymous_session(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[str]:
    """
    Validate and extract anonymous session from request headers.

    Returns:
        Anonymous session ID if valid, None otherwise
    """
    # Get session ID from header or cookie
    session_id = request.headers.get("X-Anonymous-Session-ID")

    if not session_id:
        # Check for session cookie
        session_id = request.cookies.get("anonymous_session_id")

    if not session_id:
        return None

    # Verify session exists and is not expired
    from src.services.anonymous import AnonymousSessionService
    anon_service = AnonymousSessionService(db)

    session = anon_service.get_session(session_id)
    if not session or anon_service.is_session_expired(session_id):
        return None

    return session_id


def require_auth(user: Optional[User] = Depends(get_optional_current_user)):
    """
    Dependency that requires authentication but provides a user object.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def get_current_user_or_anonymous(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user or create an anonymous user.

    Returns:
        User object (authenticated or anonymous)
    """
    # Try to get authenticated user
    if credentials:
        try:
            token = credentials.credentials
            payload = verify_token(token)

            if payload:
                user_id = payload.get("sub")
                if user_id:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user and user.email_verified:
                        user.is_authenticated = True
                        return user
        except Exception:
            pass

    # Create anonymous user object
    anon_user = User(
        id="anonymous",
        email="anonymous@example.com",
        email_verified=False
    )
    anon_user.is_authenticated = False
    return anon_user


# Common dependency for protecting routes
CurrentUser = Depends(get_current_active_user)
OptionalCurrentUser = Depends(get_optional_current_user)
RequireAuth = Depends(require_auth)