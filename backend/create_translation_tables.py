#!/usr/bin/env python
"""
Create translation tables in the database.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from src.database.base import engine, Base
from src.models import *  # Import all models

def create_tables():
    """Create all tables in the database."""
    try:
        # Import models to register them
        from src.models.auth import User
        from src.models.translation_openai import (
            TranslationJob, TranslationChunk, TranslationError,
            TranslationSession, TranslationCache, TranslationMetrics
        )

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Translation tables created successfully!")

        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("\nAvailable tables:")
        for table in sorted(tables):
            if 'translation' in table.lower():
                print(f"  - {table}")

    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()