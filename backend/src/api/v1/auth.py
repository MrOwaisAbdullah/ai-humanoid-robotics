"""
FastAPI authentication endpoints.
Handles user registration, login, token management, and email verification.
"""

from datetime import timedelta, datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, and_
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, validator
import logging

from ...core.database import get_async_db
from ...core.config import settings
from ...core.security import verify_token
from ...models.user import User, UserCreate, UserUpdate, UserRead, UserPublic
from ...services.auth_service import auth_service
from ...services.email import email_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# ============================================
# Pydantic Models for Request/Response
# ============================================
class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str

    @validator('password')
    def validate_password_length(cls, v):
        if len(v) < 1:
            raise ValueError('Password cannot be empty')
        return v


class RegisterRequest(BaseModel):
    """Registration request model."""
    email: EmailStr
    password: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None

    @validator('password')
    def validate_password_strength(cls, v, values):
        # Allow OAuth users to register without password
        if v is None:
            return v

        # Basic password validation
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        # Check for common patterns
        if v.lower() in ['password', '123456', 'qwerty', 'admin']:
            raise ValueError('Password is too common')

        return v

    @validator('username')
    def validate_username(cls, v):
        if v and len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if v and not v.replace('_', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str
    new_password: str

    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request model."""
    token: str


class UserResponse(BaseModel):
    """User response model."""
    success: bool
    user: UserRead
    tokens: Optional[TokenResponse] = None
    requires_verification: Optional[bool] = False


class MessageResponse(BaseModel):
    """Generic message response model."""
    success: bool
    message: str


# ============================================
# Authentication Endpoints
# ============================================
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Register a new user.

    Args:
        user_data: Registration data
        request: FastAPI request object
        db: Database session

    Returns:
        User registration result with tokens
    """
    try:
        # Convert to UserCreate model
        user_create = UserCreate(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username,
            full_name=user_data.full_name
        )

        # Register user
        result = await auth_service.register_user(user_create, db)

        # Format response
        response_data = {
            "success": result["success"],
            "user": result["user"],
            "requires_verification": result.get("requires_verification", False)
        }

        if "tokens" in result:
            response_data["tokens"] = TokenResponse(**result["tokens"])

        return response_data

    except ValueError as e:
        logger.warning(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )


@router.post("/login", response_model=UserResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Authenticate user and return tokens.

    Args:
        login_data: Login credentials
        request: FastAPI request object
        db: Database session

    Returns:
        Authentication result with tokens
    """
    try:
        # Authenticate user
        result = await auth_service.authenticate_user(
            login_data.email,
            login_data.password,
            db
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Format response
        return {
            "success": result["success"],
            "user": result["user"],
            "tokens": TokenResponse(**result["tokens"])
        }

    except ValueError as e:
        logger.warning(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token data
        db: Database session

    Returns:
        New access token
    """
    try:
        result = await auth_service.refresh_access_token(
            token_data.refresh_token,
            db
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Revoke refresh token (logout).

    Args:
        token_data: Refresh token to revoke
        db: Database session

    Returns:
        Logout result
    """
    try:
        success = await auth_service.revoke_refresh_token(
            token_data.refresh_token,
            db
        )

        return {
            "success": success,
            "message": "Logged out successfully" if success else "Logout failed"
        }

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {
            "success": False,
            "message": "Logout failed"
        }


# ============================================
# Email Verification Endpoints
# ============================================
@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Verify user email with verification token.

    Args:
        verification_data: Verification token
        db: Database session

    Returns:
        Verification result
    """
    try:
        result = await auth_service.verify_email(
            verification_data.token,
            db
        )

        return result

    except ValueError as e:
        logger.warning(f"Email verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    request_data: PasswordResetRequest,  # Reuse same model (email only)
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Resend email verification.

    Args:
        request_data: Email address
        db: Database session

    Returns:
        Resend result
    """
    try:
        result = await auth_service.resend_verification_email(
            request_data.email,
            db
        )

        return result

    except ValueError as e:
        logger.warning(f"Resend verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Resend verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )


# ============================================
# Password Reset Endpoints
# ============================================
@router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Request password reset.

    Args:
        request_data: Email address
        db: Database session

    Returns:
        Request result
    """
    try:
        result = await auth_service.request_password_reset(
            request_data.email,
            db
        )

        return result

    except ValueError as e:
        logger.warning(f"Password reset request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Reset password with reset token.

    Args:
        reset_data: Reset token and new password
        db: Database session

    Returns:
        Reset result
    """
    try:
        result = await auth_service.reset_password(
            reset_data.token,
            reset_data.new_password,
            db
        )

        return result

    except ValueError as e:
        logger.warning(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


# ============================================
# User Profile Endpoints
# ============================================
@router.get("/me", response_model=UserRead)
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Get current user profile.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Current user data
    """
    try:
        # Get user from request state (set by middleware)
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        return request.state.user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/me", response_model=UserRead)
async def update_current_user(
    user_update: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Update current user profile.

    Args:
        user_update: User update data
        request: FastAPI request object
        db: Database session

    Returns:
        Updated user data
    """
    try:
        # Get user from request state (set by middleware)
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        user = request.state.user

        # Update user fields
        update_data = user_update.dict(exclude_unset=True)

        # Check if username is being updated and ensure it's unique
        if 'username' in update_data and update_data['username'] != user.username:
            existing = await db.execute(
                select(User).where(
                    and_(
                        User.username == update_data['username'],
                        User.id != user.id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken"
                )

        # Apply updates
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user profile error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


# ============================================
# Health Check Endpoint
# ============================================
@router.get("/health", response_model=Dict[str, Any])
async def auth_health() -> Dict[str, Any]:
    """
    Check authentication service health.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "1.0.0",
        "email_configured": email_service.is_configured()
    }