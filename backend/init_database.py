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

from src.core.database import create_all_tables, sync_engine
from src.core.config import settings


def ensure_database_directory():
    """Ensure the database directory exists."""
    db_path = Path(settings.database_url_sync.replace("sqlite:///", ""))

    if not db_path.exists():
        db_dir = db_path.parent
        db_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created database directory: {db_dir}")

    return db_path


from sqlalchemy import text, inspect, Integer

def fix_schema():
    """Fix database schema issues on existing databases."""
    try:
        inspector = inspect(sync_engine)
        if inspector.has_table("users"):
            columns = inspector.get_columns("users")
            col_names = [col["name"] for col in columns]
            
            # Check for ID type mismatch (Integer vs String/UUID)
            id_col = next((c for c in columns if c["name"] == "id"), None)
            is_integer_id = False
            if id_col:
                # Check type - SQLite INTEGER often reflects as Integer in SQLAlchemy
                if isinstance(id_col["type"], Integer):
                    is_integer_id = True
            
            if is_integer_id:
                print("⚠️ Detected incompatible 'users.id' type (INTEGER). Dropping table to allow recreation with UUID support...")
                with engine.connect() as conn:
                    # Drop dependent tables first to avoid foreign key errors
                    conn.execute(text("DROP TABLE IF EXISTS accounts"))
                    conn.execute(text("DROP TABLE IF EXISTS sessions"))
                    conn.execute(text("DROP TABLE IF EXISTS user_backgrounds"))
                    conn.execute(text("DROP TABLE IF EXISTS user_preferences"))
                    conn.execute(text("DROP TABLE IF EXISTS password_reset_tokens"))
                    conn.execute(text("DROP TABLE IF EXISTS users"))
                    conn.commit()
                print("✅ Dropped incompatible tables.")
                return # Table dropped, create_tables will handle recreation

            with engine.connect() as conn:
                if "password_hash" not in col_names:
                    print("🔧 Adding missing column 'password_hash' to 'users' table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                    conn.commit()
                    print("✅ Added 'password_hash' column.")
                
                # Check for other potential missing columns from recent updates
                if "provider" not in col_names:
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