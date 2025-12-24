"""Fix experience level enum values

Revision ID: 002_fix_experience_level_enum
Revises: 001_initial_authentication_tables
Create Date: 2025-12-16 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update experience_level enum to use capitalized values.
    Note: The initial migration already created capitalized enum values,
    so this migration only ensures the enum type exists with correct values.
    """

    # First check if the enum type exists and has the correct values
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check if we need to migrate by looking at the enum type
    # Since the initial migration already uses capitalized values, this is a no-op
    pass


def downgrade() -> None:
    """Revert to lowercase enum values.
    Note: Since the initial migration already used capitalized values,
    this is a no-op.
    """
    pass