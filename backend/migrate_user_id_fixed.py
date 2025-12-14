#!/usr/bin/env python
"""
Migration script to change user_id from UUID to String in translation tables.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from src.database.base import engine, Base
from src.models import *  # Import all models

def migrate_user_id_columns():
    """Migrate user_id columns from UUID to String in translation tables."""

    # Tables to modify
    tables = [
        'translation_jobs',
        'translation_sessions',
        'translation_metrics'
    ]

    with engine.connect() as connection:
        # Begin transaction
        trans = connection.begin()

        try:
            for table in tables:
                print(f"Dropping {table}...")
                connection.execute(text(f"DROP TABLE IF EXISTS {table}"))

            # Commit transaction
            trans.commit()
            print("\nDropped all translation tables successfully!")

        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"\nMigration failed: {e}")
            raise

    # Recreate tables with new schema
    print("Recreating tables with new schema...")
    Base.metadata.create_all(bind=engine)
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate_user_id_columns()