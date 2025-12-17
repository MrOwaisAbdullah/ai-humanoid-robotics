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


from sqlalchemy import text, inspect

def fix_schema():
    """Fix database schema issues on existing databases."""
    try:
        inspector = inspect(engine)
        if inspector.has_table("users"):
            columns = [col["name"] for col in inspector.get_columns("users")]
            
            with engine.connect() as conn:
                if "password_hash" not in columns:
                    print("🔧 Adding missing column 'password_hash' to 'users' table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                    conn.commit()
                    print("✅ Added 'password_hash' column.")
                
                # Check for other potential missing columns from recent updates
                if "provider" not in columns:
                     print("🔧 Adding missing column 'provider' to 'users' table...")
                     conn.execute(text("ALTER TABLE users ADD COLUMN provider VARCHAR(50) DEFAULT 'local'"))
                     conn.commit()
                     print("✅ Added 'provider' column.")

    except Exception as e:
        print(f"⚠️ Schema fix attempt failed (this is expected if tables don't exist yet): {e}")

def initialize_database():
    """Initialize the database with all required tables."""
    print(f"Initializing database at: {DATABASE_URL}")

    # Ensure database directory exists
    db_path = ensure_database_directory()
    print(f"Database path: {db_path}")

    # Run schema fix BEFORE creating tables (in case table exists but is old)
    fix_schema()

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