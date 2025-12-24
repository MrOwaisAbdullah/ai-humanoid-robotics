from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/auth.db")

# For PostgreSQL, convert async URL to sync URL and handle SSL
if "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
    # Remove query parameters and convert async driver to sync driver
    CLEAN_DATABASE_URL = DATABASE_URL.split("?")[0]
    # Convert asyncpg:// to regular postgresql:// for sync engine
    CLEAN_DATABASE_URL = CLEAN_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    CLEAN_DATABASE_URL = CLEAN_DATABASE_URL.replace("postgres+asyncpg://", "postgresql+psycopg2://")
    CLEAN_DATABASE_URL = CLEAN_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    # Add SSL as connect argument for psycopg2
    connect_args = {"sslmode": "require"}
    # Pool configuration for Neon PostgreSQL with SSL
    engine_kwargs = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 300,  # Recycle connections every 5 minutes
        "connect_args": connect_args,
    }
else:
    CLEAN_DATABASE_URL = DATABASE_URL
    connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    engine_kwargs = {
        "connect_args": connect_args
    }

# Create engine
engine = create_engine(CLEAN_DATABASE_URL, **engine_kwargs)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    from src.models.auth import Base as AuthBase
    AuthBase.metadata.create_all(bind=engine)
    print("Database tables created successfully")