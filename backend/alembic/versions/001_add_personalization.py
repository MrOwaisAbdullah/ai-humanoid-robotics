"""Add personalization tables

Revision ID: 001_add_personalization
Revises:
Create Date: 2025-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    # Create saved_personalizations table
    op.create_table(
        'saved_personalizations',
        sa.Column('id', sa.String(36), nullable=False),  # Changed from UUID to VARCHAR to match users.id
        sa.Column('user_id', sa.String(36), nullable=False),  # Changed from UUID to VARCHAR to match users.id
        sa.Column('original_content_hash', sa.String(64), nullable=False),
        sa.Column('content_url', sa.String(512), nullable=False),
        sa.Column('content_title', sa.String(200), nullable=False),
        sa.Column('personalized_content', sa.Text(), nullable=False),
        sa.Column('personalization_metadata', sa.JSON(), nullable=False),
        sa.Column('adaptations_applied', sa.JSON(), nullable=False),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_accessed', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'original_content_hash', name='uq_user_content_hash')
    )

    # Create indexes
    op.create_index(
        'idx_saved_personalizations_user_hash',
        'saved_personalizations',
        ['user_id', 'original_content_hash'],
        unique=True
    )
    op.create_index(
        'idx_saved_personalizations_user_created',
        'saved_personalizations',
        ['user_id', 'created_at']
    )
    op.create_index(
        'idx_saved_personalizations_hash',
        'saved_personalizations',
        ['original_content_hash']
    )

    # Add columns to users table for tracking
    op.add_column('users', sa.Column('total_personalizations', sa.Integer(), server_default='0'))
    op.add_column('users', sa.Column('average_personalization_rating', sa.Float(), server_default='0.0'))


def downgrade():
    # Remove columns from users table
    op.drop_column('users', 'average_personalization_rating')
    op.drop_column('users', 'total_personalizations')

    # Drop indexes
    op.drop_index('idx_saved_personalizations_hash', table_name='saved_personalizations')
    op.drop_index('idx_saved_personalizations_user_created', table_name='saved_personalizations')
    op.drop_index('idx_saved_personalizations_user_hash', table_name='saved_personalizations')

    # Drop table
    op.drop_table('saved_personalizations')