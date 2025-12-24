"""
Comprehensive authentication service for handling user authentication, registration, and token management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..core.database import get_async_db, DatabaseContext
from ..core.security import (
    verify_password, get_password_hash, validate_password_strength,
    create_access_token, create_refresh_token, verify_token,
    generate_verification_token, generate_password_reset_token,
    sanitize_email, validate_email
)
from ..core.config import settings
from ..models.user import (
    User, UserCreate, UserSession, RefreshToken,
    EmailVerification, PasswordReset, OAuthAccount,
    UserRole, UserStatus, AuthProvider
)
from ..services.email import EmailService

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user management and token operations."""

    def __init__(self):
        self.email_service = EmailService()

    # ============================================
    # User Registration
    # ============================================
    async def register_user(
        self,
        user_data: UserCreate,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Register a new user with email and password.

        Args:
            user_data: User creation data
            db: Database session

        Returns:
            Dict: Registration result with user info and tokens

        Raises:
            ValueError: If registration fails
        """
        try:
            # Validate email format
            if not validate_email(user_data.email):
                raise ValueError("Invalid email format")

            # Check if user already exists
            existing_user = await self.get_user_by_email(user_data.email, db)
            if existing_user:
                if existing_user.status == UserStatus.INACTIVE:
                    raise ValueError("Account exists but not verified. Please check your email.")
                raise ValueError("User with this email already exists")

            # Validate password if provided
            if user_data.password:
                password_validation = validate_password_strength(user_data.password)
                if not password_validation["is_valid"]:
                    raise ValueError(password_validation["message"])

            # Create new user
            user = User(
                email=sanitize_email(user_data.email),
                username=user_data.username,
                full_name=user_data.full_name,
                password_hash=get_password_hash(user_data.password) if user_data.password else None,
                auth_provider=AuthProvider.EMAIL,
                status=UserStatus.INACTIVE if settings.email_verification_required else UserStatus.ACTIVE,
                email_verified=False if settings.email_verification_required else True
            )

            db.add(user)
            await db.flush()  # Get the user ID

            # Create email verification if required
            if settings.email_verification_required:
                await self._create_email_verification(user, db)

            # Create session and tokens
            session_result = await self._create_user_session(user, db)

            await db.commit()

            # Send verification email
            if settings.email_verification_required:
                await self.email_service.send_verification_email(user.email)

            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "status": user.status,
                    "email_verified": user.email_verified,
                    "created_at": user.created_at
                },
                "tokens": session_result,
                "requires_verification": settings.email_verification_required
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"User registration failed: {e}")
            raise ValueError(f"Registration failed: {str(e)}")

    # ============================================
    # User Authentication
    # ============================================
    async def authenticate_user(
        self,
        email: str,
        password: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password
            db: Database session

        Returns:
            Dict: Authentication result with user info and tokens
            None: If authentication fails
        """
        try:
            # Get user by email
            user = await self.get_user_by_email(email, db)
            if not user:
                return None

            # Check user status
            if user.status == UserStatus.BANNED:
                raise ValueError("Account banned")
            if user.status == UserStatus.SUSPENDED:
                raise ValueError("Account suspended")

            # Verify password for email users
            if user.auth_provider == AuthProvider.EMAIL:
                if not user.password_hash or not verify_password(password, user.password_hash):
                    return None

            # Check email verification
            if settings.email_verification_required and not user.email_verified:
                raise ValueError("Email not verified")

            # Update last login
            user.last_login_at = datetime.utcnow()
            await db.flush()

            # Create session and tokens
            session_result = await self._create_user_session(user, db)
            await db.commit()

            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "status": user.status,
                    "email_verified": user.email_verified,
                    "last_login_at": user.last_login_at,
                    "created_at": user.created_at
                },
                "tokens": session_result
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"User authentication failed: {e}")
            raise

    # ============================================
    # Token Management
    # ============================================
    async def refresh_access_token(
        self,
        refresh_token: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token
            db: Database session

        Returns:
            Dict: New access token
            None: If refresh fails
        """
        try:
            # Verify refresh token
            payload = verify_token(refresh_token, "refresh")
            if not payload:
                return None

            # Check if refresh token exists and is valid
            stmt = select(RefreshToken).where(
                and_(
                    RefreshToken.token == refresh_token,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
            token_record = (await db.execute(stmt)).scalar_one_or_none()

            if not token_record:
                return None

            # Get user
            user = await self.get_user_by_id(payload["sub"], db)
            if not user or user.status != UserStatus.ACTIVE:
                return None

            # Create new access token
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email, "role": user.role.value}
            )

            return {
                "access_token": access_token,
                "token_type": "bearer"
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None

    async def revoke_refresh_token(
        self,
        refresh_token: str,
        db: AsyncSession
    ) -> bool:
        """
        Revoke a refresh token.

        Args:
            refresh_token: Refresh token to revoke
            db: Database session

        Returns:
            bool: True if revoked successfully
        """
        try:
            stmt = select(RefreshToken).where(
                RefreshToken.token == refresh_token
            )
            token_record = (await db.execute(stmt)).scalar_one_or_none()

            if token_record:
                token_record.is_revoked = True
                await db.commit()
                return True

            return False

        except Exception as e:
            await db.rollback()
            logger.error(f"Token revocation failed: {e}")
            return False

    # ============================================
    # Email Verification
    # ============================================
    async def verify_email(
        self,
        token: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Verify user email with verification token.

        Args:
            token: Email verification token
            db: Database session

        Returns:
            Dict: Verification result
        """
        try:
            # Find verification token
            stmt = select(EmailVerification).where(
                and_(
                    EmailVerification.token == token,
                    EmailVerification.is_used == False,
                    EmailVerification.expires_at > datetime.utcnow()
                )
            )
            verification = (await db.execute(stmt)).scalar_one_or_none()

            if not verification:
                raise ValueError("Invalid or expired verification token")

            # Get user
            user = await self.get_user_by_id(verification.user_id, db)
            if not user:
                raise ValueError("User not found")

            # Verify email
            user.email_verified = True
            if user.status == UserStatus.INACTIVE:
                user.status = UserStatus.ACTIVE

            # Mark token as used
            verification.is_used = True

            await db.commit()

            return {
                "success": True,
                "message": "Email verified successfully"
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Email verification failed: {e}")
            raise ValueError(f"Email verification failed: {str(e)}")

    # ============================================
    # Password Reset
    # ============================================
    async def request_password_reset(
        self,
        email: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Request password reset for user.

        Args:
            email: User email
            db: Database session

        Returns:
            Dict: Request result
        """
        try:
            user = await self.get_user_by_email(email, db)
            if not user:
                # Don't reveal if user exists
                return {
                    "success": True,
                    "message": "If the email exists, a reset link will be sent"
                }

            # Create password reset token
            reset_token = PasswordReset(
                user_id=user.id,
                token=generate_password_reset_token(),
                expires_at=datetime.utcnow() + timedelta(minutes=settings.password_reset_expire_minutes)
            )
            db.add(reset_token)
            await db.commit()

            # Send reset email
            await self.email_service.send_password_reset_email(user.email, reset_token.token)

            return {
                "success": True,
                "message": "If the email exists, a reset link will be sent"
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Password reset request failed: {e}")
            raise ValueError(f"Password reset request failed: {str(e)}")

    # ============================================
    # User Management
    # ============================================
    async def get_user_by_id(
        self,
        user_id: str,
        db: AsyncSession
    ) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        return (await db.execute(stmt)).scalar_one_or_none()

    async def get_user_by_email(
        self,
        email: str,
        db: AsyncSession
    ) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == sanitize_email(email))
        return (await db.execute(stmt)).scalar_one_or_none()

    async def get_user_by_username(
        self,
        username: str,
        db: AsyncSession
    ) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).where(User.username == username)
        return (await db.execute(stmt)).scalar_one_or_none()

    # ============================================
    # Private Helper Methods
    # ============================================
    async def _create_user_session(
        self,
        user: User,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create user session and tokens."""
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        # Store refresh token
        token_record = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.jwt_refresh_expire_days)
        )
        db.add(token_record)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_expire_minutes * 60
        }

    async def _create_email_verification(
        self,
        user: User,
        db: AsyncSession
    ) -> EmailVerification:
        """Create email verification token."""
        verification = EmailVerification(
            user_id=user.id,
            token=generate_verification_token(),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.email_verification_expire_minutes)
        )
        db.add(verification)
        return verification


# Global auth service instance
auth_service = AuthService()