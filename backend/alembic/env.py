"""
Alembic environment configuration for SQLModel.

This module configures Alembic to work with SQLModel models and handle
database migrations for the AI Book backend.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import SQLModel and our models
from sqlmodel import SQLModel
from src.core.database import Base
from src.models import *  # Import all models to register them

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add our model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """
    Get database URL from environment or config.

    Returns:
        str: Database URL
    """
    # Try to get URL from environment variable first
    url = os.getenv("DATABASE_URL")
    if url:
        # Convert async URL to sync for Alembic
        if url.startswith("sqlite+aiosqlite"):
            url = url.replace("sqlite+aiosqlite", "sqlite")
        elif url.startswith("postgresql+asyncpg"):
            url = url.replace("postgresql+asyncpg", "postgresql")
        return url

    # Fall back to config file
    return config.get_main_option("sqlalchemy.url")


def get_database_url():
    """
    Get the correct database URL for Alembic (synchronous).

    Returns:
        str: Synchronous database URL
    """
    url = get_url()

    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Ensure we have a synchronous URL for Alembic
    if url.startswith("sqlite+aiosqlite"):
        url = url.replace("sqlite+aiosqlite", "sqlite")
    elif url.startswith("postgresql+asyncpg"):
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    elif url.startswith("postgresql"):
        url = url.replace("postgresql", "postgresql+psycopg2")

    return url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Override the sqlalchemy.url in configuration
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()

    # Create engine with proper settings for migrations
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            "check_same_thread": False,  # For SQLite
        } if "sqlite" in get_database_url() else {}
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            # Include object for naming conventions
            render_item=_render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


def _render_item(type_, obj, autogen_context):
    """
    Custom render function for migration items.

    This helps with proper naming conventions and schema handling.
    """
    # Add custom naming for indexes, constraints, etc.
    if type_ == "index" and hasattr(obj, 'name') and obj.name:
        # Ensure index names are properly quoted if needed
        return f'"{obj.name}"'
    return False


def _process_revision_directives(context, revision, directives):
    """
    Process revision directives for better migration handling.
    """
    # Custom processing of migration directives can go here
    pass


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


# ============================================
# Migration Helper Functions
# ============================================

def get_migration_context():
    """
    Get the current migration context.

    Returns:
        MigrationContext: Current migration context
    """
    return context.get_context()


def is_migration_running():
    """
    Check if migrations are currently running.

    Returns:
        bool: True if migrations are running
    """
    return context.is_offline_mode() is False