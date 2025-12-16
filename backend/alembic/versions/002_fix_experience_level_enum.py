"""Fix experience level enum values

Revision ID: 002_fix_experience_level_enum
Revises: 001_initial_authentication_tables
Create Date: 2025-12-16 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_fix_experience_level_enum'
down_revision = '001_initial_authentication_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update experience_level enum to use capitalized values."""

    # Create new enum type with capitalized values
    op.execute("ALTER TYPE experiencelevel RENAME TO experiencelevel_old")

    # Create new enum with correct values
    new_enum = postgresql.ENUM('Beginner', 'Intermediate', 'Advanced', name='experiencelevel')
    new_enum.create(op.get_bind())

    # Update existing data to use capitalized values
    op.execute("""
        UPDATE user_background
        SET experience_level = CASE experience_level
            WHEN 'beginner' THEN 'Beginner'
            WHEN 'intermediate' THEN 'Intermediate'
            WHEN 'advanced' THEN 'Advanced'
            ELSE 'Intermediate'
        END
    """)

    # Alter the column to use the new enum type
    op.execute("""
        ALTER TABLE user_background
        ALTER COLUMN experience_level TYPE experiencelevel
        USING experience_level::experiencelevel
    """)

    # Drop the old enum type
    op.execute("DROP TYPE experiencelevel_old")


def downgrade() -> None:
    """Revert to lowercase enum values."""

    # Create old enum type
    op.execute("ALTER TYPE experiencelevel RENAME TO experiencelevel_new")

    old_enum = postgresql.ENUM('beginner', 'intermediate', 'advanced', name='experiencelevel')
    old_enum.create(op.get_bind())

    # Update data back to lowercase
    op.execute("""
        UPDATE user_background
        SET experience_level = CASE experience_level
            WHEN 'Beginner' THEN 'beginner'
            WHEN 'Intermediate' THEN 'intermediate'
            WHEN 'Advanced' THEN 'advanced'
            ELSE 'intermediate'
        END
    """)

    # Alter column back
    op.execute("""
        ALTER TABLE user_background
        ALTER COLUMN experience_level TYPE experiencelevel
        USING experience_level::experiencelevel
    """)

    # Drop the new enum
    op.execute("DROP TYPE experiencelevel_new")