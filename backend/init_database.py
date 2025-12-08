"""
Database initialization script for Hugging Face Spaces deployment.
This script ensures the database directory exists and creates necessary tables.
"""
import os
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from database.config import create_tables, engine, DATABASE_URL


def ensure_database_directory():
    """Ensure the database directory exists."""
    db_path = Path(DATABASE_URL.replace("sqlite:///", ""))

    if not db_path.exists():
        db_dir = db_path.parent
        db_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created database directory: {db_dir}")

    return db_path


def initialize_database():
    """Initialize the database with all required tables."""
    print(f"Initializing database at: {DATABASE_URL}")

    # Ensure database directory exists
    db_path = ensure_database_directory()
    print(f"Database path: {db_path}")

    # Create tables
    try:
        create_tables()
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Database initialization script running...")

    # Set environment variables for Hugging Face Spaces
    os.environ.setdefault("DATABASE_URL", "sqlite:///./database/auth.db")

    success = initialize_database()

    if success:
        print("✅ Database is ready for use!")
    else:
        print("❌ Database initialization failed!")
        sys.exit(1)