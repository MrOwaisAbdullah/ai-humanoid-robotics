"""
User models for authentication and user management.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Text, Boolean, DateTime, JSON, Index, Enum as SQLEnum
from sqlalchemy.sql import func

from ..core.database import Base


class UserRole(str, Enum):
    """User roles with different permission levels."""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(str, Enum):
    """User account status."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class AuthProvider(str, Enum):
    """Authentication providers."""
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"
    MICROSOFT = "microsoft"


# Create SQLAlchemy Enum types for database columns
user_role_enum = SQLEnum(
    UserRole,
    values_callable=lambda obj: [e.value for e in obj],
    name="userrole"
)

user_status_enum = SQLEnum(
    UserStatus,
    values_callable=lambda obj: [e.value for e in obj],
    name="userstatus"
)

auth_provider_enum = SQLEnum(
    AuthProvider,
    values_callable=lambda obj: [e.value for e in obj],
    name="authprovider"
)


# ============================================
# User Model
# ============================================
class UserBase(SQLModel):
    """Base user model with common fields."""
    email: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="User's email address (unique identifier)"
    )
    username: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique username for the user"
    )
    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="User's full name",
        alias="fullName"
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL to user's avatar image",
        alias="avatarUrl"
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User biography or description"
    )
    role: UserRole = Field(
        default=UserRole.USER,
        sa_column=Column(user_role_enum, nullable=False, server_default="user"),
        description="User role for permissions"
    )
    status: UserStatus = Field(
        default=UserStatus.INACTIVE,
        sa_column=Column(user_status_enum, nullable=False, server_default="inactive"),
        description="Account status"
    )
    email_verified: bool = Field(
        default=False,
        description="Whether the user's email has been verified",
        alias="emailVerified"
    )
    auth_provider: AuthProvider = Field(
        default=AuthProvider.EMAIL,
        sa_column=Column(auth_provider_enum, nullable=False, server_default="email"),
        description="Primary authentication provider",
        alias="authProvider"
    )
    is_premium: bool = Field(
        default=False,
        description="Whether user has premium access",
        alias="isPremium"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="User preferences and settings"
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="Last login timestamp"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Last update timestamp"
    )

    class Config:
        populate_by_name = True


class User(UserBase, table=True):
    """User model with database table configuration."""
    __tablename__ = "users"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="Primary key (UUID)"
    )
    password_hash: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Hashed password (null for OAuth users)"
    )

    # Define indexes for performance
    __table_args__ = (
        Index('idx_user_email_status', 'email', 'status'),
        Index('idx_user_role_status', 'role', 'status'),
        Index('idx_user_auth_provider', 'auth_provider'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_username', 'username'),
    )

    # Relationships
    sessions: List["UserSession"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    refresh_tokens: List["RefreshToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    email_verifications: List["EmailVerification"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    password_resets: List["PasswordReset"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    oauth_accounts: List["OAuthAccount"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    chat_sessions: List["ChatSession"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class UserCreate(UserBase):
    """User creation schema."""
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Password for email authentication"
    )


class UserUpdate(SQLModel):
    """User update schema."""
    username: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Updated username"
    )
    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Updated full name"
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated avatar URL"
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated biography"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated preferences"
    )


class UserRead(UserBase):
    """User read schema (safe for API responses)."""
    id: str
    last_login_at: Optional[datetime] = Field(alias="lastLoginAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        populate_by_name = True


class UserPublic(SQLModel):
    """Public user information (safe for sharing)."""
    id: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    role: UserRole
    is_premium: bool


# ============================================
# User Session Model
# ============================================
class UserSessionBase(SQLModel):
    """Base session model."""
    session_token: str = Field(
        max_length=255,
        unique=True,
        index=True,
        description="Unique session token"
    )
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string"
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,  # IPv6 compatible
        description="IP address of the client"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the session is active"
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Session expiration time"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Session creation time"
    )


class UserSession(UserSessionBase, table=True):
    """User session model with database table."""
    __tablename__ = "user_sessions"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    user_id: str = Field(
        foreign_key="users.id",
        nullable=False,
        index=True
    )

    # Relationships
    user: User = Relationship(back_populates="sessions")


# ============================================
# Refresh Token Model
# ============================================
class RefreshTokenBase(SQLModel):
    """Base refresh token model."""
    token: str = Field(
        max_length=500,
        unique=True,
        index=True,
        description="Unique refresh token"
    )
    is_revoked: bool = Field(
        default=False,
        description="Whether the token has been revoked"
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Token expiration time"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Token creation time"
    )


class RefreshToken(RefreshTokenBase, table=True):
    """Refresh token model with database table."""
    __tablename__ = "refresh_tokens"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    user_id: str = Field(
        foreign_key="users.id",
        nullable=False,
        index=True
    )

    # Relationships
    user: User = Relationship(back_populates="refresh_tokens")


# ============================================
# Email Verification Model
# ============================================
class EmailVerificationBase(SQLModel):
    """Base email verification model."""
    token: str = Field(
        max_length=255,
        unique=True,
        index=True,
        description="Unique verification token"
    )
    is_used: bool = Field(
        default=False,
        description="Whether the token has been used"
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Token expiration time"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Token creation time"
    )


class EmailVerification(EmailVerificationBase, table=True):
    """Email verification model with database table."""
    __tablename__ = "email_verifications"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    user_id: str = Field(
        foreign_key="users.id",
        nullable=False,
        index=True
    )

    # Relationships
    user: User = Relationship(back_populates="email_verifications")


# ============================================
# Password Reset Model
# ============================================
class PasswordResetBase(SQLModel):
    """Base password reset model."""
    token: str = Field(
        max_length=255,
        unique=True,
        index=True,
        description="Unique reset token"
    )
    is_used: bool = Field(
        default=False,
        description="Whether the token has been used"
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Token expiration time"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Token creation time"
    )


class PasswordReset(PasswordResetBase, table=True):
    """Password reset model with database table."""
    __tablename__ = "password_resets"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    user_id: str = Field(
        foreign_key="users.id",
        nullable=False,
        index=True
    )

    # Relationships
    user: User = Relationship(back_populates="password_resets")


# ============================================
# OAuth Account Model
# ============================================
class OAuthAccountBase(SQLModel):
    """Base OAuth account model."""
    provider: str = Field(
        sa_column=Column(String(length=50), nullable=False),
        description="OAuth provider name"
    )
    provider_account_id: str = Field(
        max_length=255,
        description="User ID from the OAuth provider"
    )
    provider_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Additional data from the OAuth provider"
    )
    is_primary: bool = Field(
        default=False,
        description="Whether this is the primary OAuth account"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Account linking time"
    )


class OAuthAccount(OAuthAccountBase, table=True):
    """OAuth account model with database table."""
    __tablename__ = "oauth_accounts"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    user_id: str = Field(
        foreign_key="users.id",
        nullable=False,
        index=True
    )

    # Relationships
    user: User = Relationship(back_populates="oauth_accounts")

    # Define unique constraint for provider + provider_account_id
    __table_args__ = (
        Index('idx_oauth_provider_account', 'provider', 'provider_account_id', unique=True),
    )


# ============================================
# Import related models to avoid circular imports
# ============================================
try:
    from .chat import ChatSession
except ImportError:
    # Chat models might not be created yet
    pass