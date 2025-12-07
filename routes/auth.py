from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from database.config import get_db
from auth.auth import (
    oauth, create_access_token, get_or_create_user,
    create_or_update_account, create_user_session,
    invalidate_user_sessions, get_current_active_user
)
from models.auth import User, UserPreferences

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models
class UserResponse(BaseModel):
    id: int
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


class PreferencesResponse(BaseModel):
    theme: str = "light"
    language: str = "en"
    notifications_enabled: bool = True
    chat_settings: Optional[dict] = None

    class Config:
        from_attributes = True


@router.get("/login/google")
async def login_via_google(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = os.getenv("AUTH_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        # Get access token from Google
        token = await oauth.google.authorize_access_token(request)

        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback: fetch user info manually
            user_info = await oauth.google.parse_id_token(request, token)

        if not user_info.get('email'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required from OAuth provider"
            )

        # Get or create user
        user = get_or_create_user(db, user_info)

        # Create or update OAuth account
        create_or_update_account(db, user, 'google', token)

        # Create user session and JWT token
        session_token = create_user_session(db, user)
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

        # Redirect to frontend with token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        redirect_url = f"{frontend_url}/auth/callback?token={access_token}"

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
async def logout(
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
async def refresh_token(
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