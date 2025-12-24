"""Create tables for reader experience features

Revision ID: 003_reader_features_tables
Revises: 002_add_onboarding_tables
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

def upgrade():
    # Get inspector to check existing tables
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create reading_progress table
    if not inspector.has_table('reading_progress'):
        op.create_table('reading_progress',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('chapter_id', sa.String(), nullable=False),
            sa.Column('section_id', sa.String(), nullable=False),
            sa.Column('position', sa.Float(), nullable=False),
            sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('time_spent', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_accessed', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'chapter_id', 'section_id')
        )
        op.create_index('idx_reading_progress_user_chapter', 'reading_progress', ['user_id', 'chapter_id'])
        op.create_index('idx_reading_progress_last_accessed', 'reading_progress', ['last_accessed'])

    # Create bookmarks table
    if not inspector.has_table('bookmarks'):
        op.create_table('bookmarks',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('chapter_id', sa.String(), nullable=False),
            sa.Column('section_id', sa.String(), nullable=True),
            sa.Column('page_url', sa.String(), nullable=False),
            sa.Column('page_title', sa.String(length=255), nullable=False),
            sa.Column('snippet', sa.String(), nullable=True),
            sa.Column('note', sa.String(length=1000), nullable=True),
            sa.Column('is_private', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_bookmarks_user_created', 'bookmarks', ['user_id', 'created_at'])
        op.create_index('idx_bookmarks_chapter', 'bookmarks', ['chapter_id'])

    # Create bookmark_tags table
    if not inspector.has_table('bookmark_tags'):
        op.create_table('bookmark_tags',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('bookmark_id', sa.String(), nullable=False),
            sa.Column('tag', sa.String(length=50), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['bookmark_id'], ['bookmarks.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('bookmark_id', 'tag')
        )
        op.create_index('idx_bookmark_tags_tag', 'bookmark_tags', ['tag'])

    # Note: user_preferences table was already created in migration 0001
    # Skip creating it here, but create user_custom_notes if user_preferences exists

    # Create user_custom_notes table (only if user_preferences exists)
    if inspector.has_table('user_preferences') and not inspector.has_table('user_custom_notes'):
        op.create_table('user_custom_notes',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_preference_id', sa.String(), nullable=False),
            sa.Column('key', sa.String(), nullable=False),
            sa.Column('value', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_preference_id'], ['user_preferences.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_preference_id', 'key')
        )

    # Create content_localization table
    if not inspector.has_table('content_localization'):
        op.create_table('content_localization',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('content_id', sa.String(), nullable=False),
            sa.Column('language', sa.String(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('content', sa.String(), nullable=False),
            sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('reading_time_minutes', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_updated', sa.DateTime(), nullable=False),
            sa.Column('translator', sa.String(), nullable=True),
            sa.Column('reviewed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('content_id', 'language')
        )
        op.create_index('idx_content_localization_language', 'content_localization', ['language'])
        op.create_index('idx_content_localization_content', 'content_localization', ['content_id'])

    # Note: Skip search_index and FTS tables for PostgreSQL (SQLite-specific)
    # These would need to be implemented differently for PostgreSQL using GIN indexes

def downgrade():
    # Drop tables in reverse order (only those that were created in this migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if inspector.has_table('content_localization'):
        op.drop_index('idx_content_localization_content', table_name='content_localization')
        op.drop_index('idx_content_localization_language', table_name='content_localization')
        op.drop_table('content_localization')

    if inspector.has_table('user_custom_notes'):
        op.drop_table('user_custom_notes')

    # Note: user_preferences table is managed by migration 0001, don't drop here

    if inspector.has_table('bookmark_tags'):
        op.drop_index('idx_bookmark_tags_tag', table_name='bookmark_tags')
        op.drop_table('bookmark_tags')

    if inspector.has_table('bookmarks'):
        op.drop_index('idx_bookmarks_chapter', table_name='bookmarks')
        op.drop_index('idx_bookmarks_user_created', table_name='bookmarks')
        op.drop_table('bookmarks')

    if inspector.has_table('reading_progress'):
        op.drop_index('idx_reading_progress_last_accessed', table_name='reading_progress')
        op.drop_index('idx_reading_progress_user_chapter', table_name='reading_progress')
        op.drop_table('reading_progress')