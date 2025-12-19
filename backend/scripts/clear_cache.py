"""
Script to clear translation cache.
Run this script to remove all cached translations from the database.
"""
import sys
import os
from pathlib import Path

# Add backend to path to import modules
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from src.database.config import get_db
from src.models.translation_openai import TranslationCache

def clear_all_cache():
    """Clear all entries from the translation_cache table."""
    print("🧹 Clearing all translation cache...")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Count before deletion
        count = db.query(TranslationCache).count()
        print(f"Found {count} entries.")
        
        if count > 0:
            # Delete all rows
            deleted = db.query(TranslationCache).delete()
            db.commit()
            print(f"✅ Successfully deleted {deleted} cache entries.")
        else:
            print("✨ Cache is already empty.")
            
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure DATABASE_URL is set if not in env
    if "DATABASE_URL" not in os.environ:
        # Default to local sqlite if not set (adjust for HF if needed)
        os.environ["DATABASE_URL"] = "sqlite:///./database/auth.db"
        print(f"Using default DATABASE_URL: {os.environ['DATABASE_URL']}")
    
    clear_all_cache()