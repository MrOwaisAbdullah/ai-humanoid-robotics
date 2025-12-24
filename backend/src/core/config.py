"""
Core configuration for the AI Book backend application.
Handles environment variables, database settings, and authentication configuration.
"""

from functools import lru_cache
from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # ============================================
    # Core Application Settings
    # ============================================
    environment: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 7860
    log_level: str = "INFO"

    # ============================================
    # Database Configuration
    # ============================================
    database_url: str = "sqlite:///./database/auth_fixed_v3.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_auto_migrate: bool = True

    # ============================================
    # JWT Authentication Configuration
    # ============================================
    jwt_secret_key: str = "your-super-secret-jwt-key-at-least-32-characters-long"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days
    jwt_refresh_expire_days: int = 30

    # ============================================
    # Email Configuration
    # ============================================
    email_service: str = "smtp"  # resend, smtp
    resend_api_key: Optional[str] = Field(default=None)
    smtp_host: Optional[str] = Field(default=None)
    smtp_port: Optional[int] = Field(default=None)
    smtp_user: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_tls: bool = True
    email_from_name: str = "AI Book"
    email_from_address: str = "noreply@ai-book.com"

    # ============================================
    # OAuth Configuration
    # ============================================
    google_client_id: Optional[str] = Field(default=None)
    google_client_secret: Optional[str] = Field(default=None)
    github_client_id: Optional[str] = Field(default=None)
    github_client_secret: Optional[str] = Field(default=None)

    # OAuth URLs
    auth_redirect_uri: str = "http://localhost:3000/auth/callback"
    frontend_url: str = "http://localhost:3000"

    # ============================================
    # Security Configuration
    # ============================================
    # Store as string in env, parse to list in property
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:8080,https://mrowaisabdullah.github.io,https://huggingface.co",
        alias="CORS_ORIGINS"
    )
    cors_methods_str: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", alias="CORS_METHODS")
    cors_headers_str: str = Field(default="*", alias="CORS_HEADERS")

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_rpm: int = 60
    rate_limit_rph: int = 1000

    # Password requirements
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True

    # ============================================
    # Session Configuration
    # ============================================
    session_expire_minutes: int = 10080  # 7 days
    session_cookie_name: str = "session_id"
    session_cookie_secure: bool = False  # Set to True in production
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"

    # ============================================
    # Email Verification Configuration
    # ============================================
    email_verification_required: bool = True
    email_verification_expire_minutes: int = 1440  # 24 hours
    password_reset_expire_minutes: int = 60  # 1 hour

    # Properties for parsed values
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    @property
    def cors_methods(self) -> List[str]:
        """Parse CORS methods from comma-separated string."""
        return [method.strip() for method in self.cors_methods_str.split(",") if method.strip()]

    @property
    def cors_headers(self) -> List[str]:
        """Parse CORS headers from comma-separated string."""
        return [header.strip() for header in self.cors_headers_str.split(",") if header.strip()]

    # Validators
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v

    # Additional properties
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def database_url_sync(self) -> str:
        """Return synchronous database URL for Alembic."""
        if self.database_url.startswith("sqlite+aiosqlite"):
            return self.database_url.replace("sqlite+aiosqlite", "sqlite")
        elif self.database_url.startswith("postgresql+asyncpg"):
            # Convert to psycopg2-compatible format for sync operations
            return self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        elif self.database_url.startswith("postgresql"):
            return self.database_url.replace("postgresql", "postgresql+psycopg2")
        return self.database_url

    @property
    def database_url_async(self) -> str:
        """Return asynchronous database URL for SQLModel."""
        url = self.database_url
        if url.startswith("sqlite"):
            return url.replace("sqlite", "sqlite+aiosqlite")
        elif url.startswith("postgresql+asyncpg"):
            # Already has async driver, but remove sslmode parameter for asyncpg
            # SSL is handled via connect_args instead
            return url.split("?")[0]  # Remove query parameters
        elif url.startswith("postgresql"):
            # Remove query parameters and convert to asyncpg
            return url.split("?")[0].replace("postgresql", "postgresql+asyncpg")
        return url

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive = False,
        extra = "ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
