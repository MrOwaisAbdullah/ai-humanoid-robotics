
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from database.config import get_db
from auth.auth import (
    oauth, create_access_token, get_or_create_user,
    create_or_update_account, create_user_session,
    invalidate_user_sessions, get_current_active_user,
    verify_password, get_password_hash
)
from src.models.auth import User, UserPreferences, AnonymousSession
from src.services.session_migration import SessionMigrationService, migrate_anonymous_session_on_auth
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    image_url: Optional[str] = None
    email_verified: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    migrated_sessions: Optional[int] = 0
    migrated_messages: Optional[int] = 0


class PreferencesResponse(BaseModel):
    theme: str = "light"
    language: str = "en"
    notifications_enabled: bool = True
    chat_settings: Optional[dict] = None

    class Config:
        from_attributes = True

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.get("/anonymous-session/{session_id}")
async def get_anonymous_session(session_id: str, db: Session = Depends(get_db)):
    """Get anonymous session data including message count."""
    
    session = db.query(AnonymousSession).filter(
        AnonymousSession.id == session_id
    ).first()
    
    if session:
        return {
            "id": session.id,
            "message_count": session.message_count,
            "exists": True
        }
    
    return {
        "id": session_id,
        "message_count": 0,
        "exists": False
    }

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == register_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = get_password_hash(register_data.password)

    # Create user
    new_user = User(
        email=register_data.email,
        password_hash=hashed_password,
        name=register_data.name,
        email_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default preferences
    preferences = UserPreferences(user_id=new_user.id)
    db.add(preferences)
    db.commit()

    # Check for anonymous session to migrate
    anonymous_session_id = request.headers.get("X-Anonymous-Session-ID")
    migrated_sessions = 0
    migrated_messages = 0

    if anonymous_session_id:
        try:
            migration_service = SessionMigrationService(db)
            migration_result = migration_service.migrate_anonymous_session(
                anonymous_session_id=anonymous_session_id,
                authenticated_user_id=str(new_user.id)
            )
            if migration_result["success"]:
                migrated_sessions = migration_result["migrated_sessions_count"]
                migrated_messages = migration_result["migrated_messages_count"]
        except Exception as e:
            # Log error but don't fail registration
            print(f"Session migration failed during registration: {e}")

    # Create session
    session_token = create_user_session(db, new_user)
    access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})

    return LoginResponse(
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            image_url=new_user.image_url,
            email_verified=new_user.email_verified
        ),
        access_token=access_token,
        migrated_sessions=migrated_sessions,
        migrated_messages=migrated_messages
    )

@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check for anonymous session to migrate
    anonymous_session_id = request.headers.get("X-Anonymous-Session-ID")
    migrated_sessions = 0
    migrated_messages = 0

    if anonymous_session_id:
        try:
            migration_service = SessionMigrationService(db)
            migration_result = migration_service.migrate_anonymous_session(
                anonymous_session_id=anonymous_session_id,
                authenticated_user_id=str(user.id)
            )
            if migration_result["success"]:
                migrated_sessions = migration_result["migrated_sessions_count"]
                migrated_messages = migration_result["migrated_messages_count"]
        except Exception as e:
            # Log error but don't fail login
            print(f"Session migration failed during login: {e}")

    # Create session
    session_token = create_user_session(db, user)
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return LoginResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            image_url=user.image_url,
            email_verified=user.email_verified
        ),
        access_token=access_token,
        migrated_sessions=migrated_sessions,
        migrated_messages=migrated_messages
    )

@router.get("/login/google")
@limiter.limit("10/minute")  # Limit OAuth initiation attempts
async def login_via_google(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = os.getenv("AUTH_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
@limiter.limit("10/minute")  # Limit OAuth callback attempts
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        # Get access token from Google
        token = await oauth.google.authorize_access_token(request)

        # Debug: Print the entire token structure
        import sys
        print(f"Full token: {token}", file=sys.stderr)
        print(f"Token type: {type(token)}", file=sys.stderr)
        if hasattr(token, 'keys'):
            print(f"Token keys: {list(token.keys())}", file=sys.stderr)

        # Get user info from Google
        # For Google OAuth, we need to make an additional API call to get user info
        resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
        user_info = resp.json()
        print(f"Userinfo from API: {user_info}", file=sys.stderr)

        # If we can't get user info from API, try parsing ID token
        if not user_info or not user_info.get('email'):
            try:
                user_info = await oauth.google.parse_id_token(request, token)
                print(f"ID token user_info: {user_info}", file=sys.stderr)
            except Exception as e:
                print(f"Error parsing ID token: {e}", file=sys.stderr)

        if not user_info.get('email'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required from OAuth provider"
            )

        # Get or create user
        user = get_or_create_user(db, user_info)

        # Create or update OAuth account
        # Pass both user_info and token info
        account_data = {
            **user_info,  # Contains 'sub', 'email', 'name', etc.
            'access_token': token.get('access_token'),
            'refresh_token': token.get('refresh_token'),
            'expires_at': token.get('expires_at'),
            'token_type': token.get('token_type'),
            'scope': token.get('scope')
        }
        create_or_update_account(db, user, 'google', account_data)

        # Create user session and JWT token
        session_token = create_user_session(db, user)
        jwt_token = create_access_token(data={"sub": str(user.id), "email": user.email})

        # Redirect to frontend with token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        redirect_url = f"{frontend_url}/auth/callback?token={jwt_token}"

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        image_url=current_user.image_url,
        email_verified=current_user.email_verified
    )


@router.post("/logout")
@limiter.limit("20/minute")  # Limit logout attempts
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout current user"""
    # Invalidate all sessions for this user
    invalidate_user_sessions(db, current_user)

    # Clear HTTP-only cookie if using one
    response.delete_cookie(key="access_token")

    return {"message": "Successfully logged out"}


@router.get("/preferences", response_model=PreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user preferences"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()

    if not preferences:
        # Create default preferences
        preferences = UserPreferences(user_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return PreferencesResponse(
        theme=preferences.theme,
        language=preferences.language,
        notifications_enabled=preferences.notifications_enabled,
        chat_settings=preferences.chat_settings
    )


@router.put("/preferences", response_model=PreferencesResponse)
async def update_user_preferences(
    preferences_update: PreferencesResponse,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()

    if not preferences:
        preferences = UserPreferences(user_id=current_user.id)
        db.add(preferences)

    # Update fields
    preferences.theme = preferences_update.theme
    preferences.language = preferences_update.language
    preferences.notifications_enabled = preferences_update.notifications_enabled
    preferences.chat_settings = preferences_update.chat_settings

    db.commit()
    db.refresh(preferences)

    return PreferencesResponse(
        theme=preferences.theme,
        language=preferences.language,
        notifications_enabled=preferences.notifications_enabled,
        chat_settings=preferences.chat_settings
    )


@router.post("/refresh")
@limiter.limit("30/minute")  # Limit token refresh attempts
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    # Create new session and token
    session_token = create_user_session(db, current_user)
    access_token = create_access_token(data={"sub": str(current_user.id), "email": current_user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
