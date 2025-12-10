"""Create tables for reader experience features

Revision ID: 003_reader_features_tables
Revises: 002_add_onboarding_tables
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003_reader_features_tables'
down_revision = '002_add_onboarding_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Create reading_progress table
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

    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('reading_pace', sa.String(), nullable=False),
        sa.Column('preferred_depth', sa.String(), nullable=False),
        sa.Column('show_code_examples', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('adaptive_difficulty', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('theme', sa.String(), nullable=False),
        sa.Column('font_size', sa.Integer(), nullable=False, server_default='16'),
        sa.Column('line_height', sa.Float(), nullable=False, server_default='1.5'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create user_custom_notes table
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

    # Create search_index table
    op.create_table('search_index',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('content_id', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('chapter_id', sa.String(), nullable=False),
        sa.Column('section_id', sa.String(), nullable=True),
        sa.Column('rank', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('indexed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_search_index_language_rank', 'search_index', ['language', 'rank'])
    op.create_index('idx_search_index_chapter', 'search_index', ['chapter_id'])

    # Create FTS virtual table for search
    op.execute("""
        CREATE VIRTUAL TABLE search_index_fts USING fts5(
            title,
            content,
            keywords,
            content=search_index
        )
    """)

    # Create FTS triggers
    op.execute("""
        CREATE TRIGGER search_index_ai AFTER INSERT ON search_index BEGIN
            INSERT INTO search_index_fts(rowid, title, content, keywords)
            VALUES (new.id, new.title, new.content, new.title || ' ' || new.content);
        END
    """)

    op.execute("""
        CREATE TRIGGER search_index_ad AFTER DELETE ON search_index BEGIN
            INSERT INTO search_index_fts(search_index_fts, rowid, title, content, keywords)
            VALUES ('delete', old.id, old.title, old.content, NULL);
        END
    """)

    op.execute("""
        CREATE TRIGGER search_index_au AFTER UPDATE ON search_index BEGIN
            DELETE FROM search_index_fts WHERE rowid = old.id;
            INSERT INTO search_index_fts(rowid, title, content, keywords)
            VALUES (new.id, new.title, new.content, new.title || ' ' || new.content);
        END
    """)

def downgrade():
    # Drop tables in reverse order
    op.drop_table('search_index')
    op.execute('DROP TABLE IF EXISTS search_index_fts')
    op.drop_table('content_localization')
    op.drop_table('user_custom_notes')
    op.drop_table('user_preferences')
    op.drop_table('bookmark_tags')
    op.drop_table('bookmarks')
    op.drop_table('reading_progress')