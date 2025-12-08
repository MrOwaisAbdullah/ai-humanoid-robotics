"""
Authentication API routes.

This module provides endpoints for user registration, login, logout,
and password management.
"""

from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database.config import get_db
from src.models.auth import User, Session as UserSession, AnonymousSession
from src.schemas.auth import (
    User as UserSchema,
    UserCreate,
    UserResponse,
    Token,
    LoginRequest,
    LoginResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    SuccessResponse,
    ErrorResponse
)
from src.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_token_hash,
    generate_password_reset_token,
    verify_password_reset_token,
    validate_password_strength
)
from src.services.email import email_service
from src.security.dependencies import get_current_user, get_current_active_user, require_auth

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    response: Response,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user with email and password.

    Args:
        user_data: User registration data
        response: FastAPI response object for setting cookies
        db: Database session

    Returns:
        Created user data

    Raises:
        HTTPException: If user already exists or validation fails
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain letters and numbers"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        email_verified=False  # Will be verified via email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create user background if provided
    if user_data.software_experience or user_data.hardware_expertise or user_data.years_of_experience is not None:
        from src.models.auth import UserBackground
        background = UserBackground(
            user_id=db_user.id,
            experience_level=user_data.software_experience or "Beginner",
            hardware_expertise=user_data.hardware_expertise or "None",
            years_of_experience=user_data.years_of_experience or 0
        )
        db.add(background)
        db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=10080)  # 7 days
    access_token = create_access_token(
        data={"sub": str(db_user.id)},
        expires_delta=access_token_expires
    )

    # Create session record
    user_session = UserSession(
        user_id=db_user.id,
        token_hash=create_token_hash(access_token),
        expires_at=datetime.utcnow() + access_token_expires
    )
    db.add(user_session)
    db.commit()

    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_token_expires.total_seconds(),
        httponly=True,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )

    # TODO: Send email verification
    # if email_service.is_configured():
    #     verification_token = generate_password_reset_token(db_user.email)
    #     await email_service.send_verification_email(
    #         db_user.email,
    #         verification_token,
    #         os.getenv("FRONTEND_URL", "http://localhost:3000")
    #     )

    return db_user


@router.post("/login", response_model=LoginResponse)
async def login(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Authenticate user with email and password.

    Args:
        response: FastAPI response object for setting cookies
        db: Database session
        form_data: OAuth2PasswordRequestForm with username (email) and password

    Returns:
        Login response with token and user data

    Raises:
        HTTPException: If authentication fails
    """
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=10080)  # 7 days
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    # Invalidate previous sessions (single session enforcement)
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.expires_at > datetime.utcnow()
    ).update({"expires_at": datetime.utcnow()})
    db.commit()

    # Create new session
    user_session = UserSession(
        user_id=user.id,
        token_hash=create_token_hash(access_token),
        expires_at=datetime.utcnow() + access_token_expires
    )
    db.add(user_session)
    db.commit()

    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_token_expires.total_seconds(),
        httponly=True,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
        "user": user
    }


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    response: Response,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Logout user and invalidate session.

    Args:
        response: FastAPI response object for clearing cookies
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Success response
    """
    # Invalidate all user sessions
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id
    ).update({"expires_at": datetime.utcnow()})
    db.commit()

    # Clear cookie
    response.delete_cookie(key="access_token")

    return {"success": True, "message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserSchema = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information.

    Args:
        current_user: Currently authenticated user

    Returns:
        Current user data
    """
    return current_user


@router.post("/refresh")
async def refresh_token(
    current_user: UserSchema = Depends(get_current_active_user),
    response: Response = None
) -> Any:
    """
    Refresh authentication token.

    Args:
        current_user: Currently authenticated user
        response: FastAPI response object for setting cookies

    Returns:
        New access token

    Raises:
        HTTPException: If refresh fails
    """
    # Create new access token
    access_token_expires = timedelta(minutes=10080)  # 7 days
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=access_token_expires
    )

    # Set HTTP-only cookie if response is provided
    if response:
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=access_token_expires.total_seconds(),
            httponly=True,
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )

    return {"token": access_token}


@router.get("/anonymous-session/{session_id}")
async def get_anonymous_session(
    session_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get anonymous session data including message count.

    Args:
        session_id: Anonymous session ID from localStorage
        db: Database session

    Returns:
        Anonymous session data with message count and existence flag
    """
    # Query for existing session
    session = db.query(AnonymousSession).filter(
        AnonymousSession.id == session_id
    ).first()

    if not session:
        # Return new session data if not found
        return {
            "id": session_id,
            "message_count": 0,
            "exists": False
        }

    # Return existing session data
    return {
        "id": session.id,
        "message_count": session.message_count,
        "exists": True
    }


@router.post("/password-reset/request", response_model=SuccessResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset email.

    Args:
        request_data: Email for password reset
        db: Database session

    Returns:
        Success response
    """
    user = db.query(User).filter(User.email == request_data.email).first()
    if not user:
        # Don't reveal if user exists
        return {"success": True, "message": "If the email exists, a reset link has been sent"}

    # Generate reset token
    reset_token = generate_password_reset_token(user.email)

    # Save reset token
    from src.models.auth import PasswordResetToken
    password_reset_token = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(password_reset_token)

    # Invalidate previous tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).update({"used": True})
    db.commit()

    # Send email
    if email_service.is_configured():
        frontend_url = "http://localhost:3000"  # TODO: Get from environment
        await email_service.send_password_reset_email_async(
            user.email,
            reset_token,
            frontend_url
        )

    return {"success": True, "message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm", response_model=SuccessResponse)
async def confirm_password_reset(
    request_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """
    Confirm password reset with token.

    Args:
        request_data: Token and new password
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If token is invalid or expired
    """
    # Verify token
    email = verify_password_reset_token(request_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Get user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Get and validate token record
    from src.models.auth import PasswordResetToken
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request_data.token,
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False
    ).first()

    if not token_record or token_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Validate new password
    if not validate_password_strength(request_data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and contain letters and numbers"
        )

    # Update password
    user.password_hash = get_password_hash(request_data.new_password)
    user.updated_at = datetime.utcnow()

    # Mark token as used
    token_record.used = True

    # Invalidate all user sessions (force re-login)
    db.query(UserSession).filter(UserSession.user_id == user.id).update(
        {"expires_at": datetime.utcnow()}
    )

    db.commit()

    return {"success": True, "message": "Password has been reset successfully"}