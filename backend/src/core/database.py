"""
Database configuration and connection management.
Handles async SQLModel database connections with PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# ============================================
# Base Model Classes
# ============================================
class Base(DeclarativeBase):
    """Base model for all database models."""
    pass


class AsyncBase(DeclarativeBase):
    """Base model for async database models."""
    pass


# ============================================
# Database Engine Configuration
# ============================================
# Prepare connect args for PostgreSQL
async_connect_args = {}
if "postgresql" in settings.database_url_async or "postgres" in settings.database_url_async:
    async_connect_args = {
        "server_settings": {
            "application_name": "ai_book_backend",
            "jit": "off",  # Disable JIT for better performance in some cases
            "timezone": "utc"
        },
        "command_timeout": 60,
        # Note: SSL is configured via DATABASE_URL (sslmode=require)
        # Don't set ssl directly in connect_args for asyncpg
    }

# Async engine for SQLModel operations
# Use smaller pool for async to prevent connection exhaustion
async_engine = create_async_engine(
    settings.database_url_async,
    echo=settings.debug,
    pool_size=3,  # Reduced from settings.db_pool_size (5) for async
    max_overflow=5,  # Reduced from settings.db_max_overflow (10)
    pool_timeout=30,
    pool_recycle=1800,  # 30 minutes (reduced from 3600 for Neon's idle timeout)
    pool_pre_ping=True,  # CRITICAL: Check connections before using them
    connect_args=async_connect_args,
    # Additional async-specific settings
    pool_use_lifo=True,  # Use LIFO to reduce stale connections
    pool_drop_on_rollback=False,  # Don't drop connections on rollback
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    # SQLite specific settings
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    } if "sqlite" in settings.database_url_sync else {}
)

# ============================================
# Session Factories
# ============================================
# Async session factory with better error handling
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Changed from True to False for better control
    autocommit=False
)

# Sync session factory for migrations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


# ============================================
# Database Dependency
# ============================================
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    Yields:
        AsyncSession: Database session for async operations

    Usage:
        ```python
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_async_db)):
            # Use db session here
            pass
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            # Always close the session to return connection to pool
            await session.close()


def get_sync_db():
    """
    Get sync database session.

    Yields:
        Session: Database session for sync operations (migrations)

    Usage:
        ```python
        def run_migrations():
            db = get_sync_db()
            # Use db session for migrations
            db.close()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Sync database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ============================================
# Database Connection Management
# ============================================
async def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables if they don't exist.
    """
    try:
        # Import all models here to ensure they are registered
        from ..models import user, chat  # noqa

        # Create all tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    try:
        await async_engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


async def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


# ============================================
# Database Migration Helpers
# ============================================
async def create_all_tables() -> None:
    """Create all database tables."""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def drop_all_tables() -> None:
    """Drop all database tables (use with caution!)."""
    if settings.is_production:
        raise RuntimeError("Cannot drop tables in production environment")

    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


# ============================================
# Database Health Check
# ============================================
async def get_db_health() -> dict:
    """
    Get database health status.

    Returns:
        dict: Database health information
    """
    try:
        # Test connection
        connection_ok = await check_db_connection()

        # Get connection pool status
        pool = async_engine.pool
        pool_status = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        } if hasattr(pool, 'size') else {}

        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "connection": connection_ok,
            "database_url": settings.database_url_async.split("@")[-1] if "@" in settings.database_url_async else "local",
            "pool": pool_status,
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


# ============================================
# Transaction Management
# ============================================
class DatabaseTransaction:
    """Context manager for database transactions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
            self.rolled_back = True
        else:
            await self.session.commit()
            self.committed = True

    async def commit(self):
        """Manually commit the transaction."""
        await self.session.commit()
        self.committed = True

    async def rollback(self):
        """Manually rollback the transaction."""
        await self.session.rollback()
        self.rolled_back = True


# ============================================
# Database Utilities
# ============================================
async def execute_raw_sql(sql: str, params: dict = None) -> any:
    """
    Execute raw SQL query.

    Args:
        sql: SQL query string
        params: Query parameters

    Returns:
        Query result
    """
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(sql, params or {})
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Raw SQL execution failed: {e}")
            raise


# ============================================
# Database Connection Context
# ============================================
class DatabaseContext:
    """Context manager for database operations."""

    def __init__(self):
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionLocal()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type is not None:
                    await self.session.rollback()
                else:
                    await self.session.commit()
            finally:
                await self.session.close()