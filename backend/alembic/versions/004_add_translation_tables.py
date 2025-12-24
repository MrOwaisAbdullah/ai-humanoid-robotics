"""Add translation tables and personalization features

Revision ID: 004_add_translation_tables
Revises: 003_reader_features_tables
Create Date: 2025-01-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    # Create translations table
    op.create_table('translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('translation_model', sa.String(length=50), nullable=False),
        sa.Column('character_count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash')
    )
    op.create_index('idx_content_lookup', 'translations', ['content_hash', 'source_language', 'target_language'], unique=False)
    op.create_index(op.f('ix_translations_content_hash'), 'translations', ['content_hash'], unique=True)

    # Create translation_feedback table
    op.create_table('translation_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('translation_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['translation_id'], ['translations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('rating IN (-1, 1)', name='check_rating_range')
    )
    op.create_index('idx_user_translation', 'translation_feedback', ['user_id', 'translation_id'], unique=True)

    # Create personalization_profiles table
    op.create_table('personalization_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('reading_level', sa.String(length=20), nullable=True),
        sa.Column('preferred_language', sa.String(length=10), nullable=True),
        sa.Column('focus_areas', sa.JSON(), nullable=True),
        sa.Column('learning_style', sa.String(length=20), nullable=True),
        sa.Column('enable_transliteration', sa.Boolean(), nullable=True),
        sa.Column('technical_term_handling', sa.String(length=20), nullable=True),
        sa.Column('font_size', sa.Integer(), nullable=True),
        sa.Column('focus_mode_preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_active', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_personalization_profiles_user_id'), 'personalization_profiles', ['user_id'], unique=False)

    # Check if content_localization table exists before creating
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'content_localization' not in tables:
        # Create content_localization table
        op.create_table('content_localization',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('content_url', sa.String(length=500), nullable=False),
            sa.Column('content_hash', sa.String(length=64), nullable=False),
            sa.Column('is_translated', sa.Boolean(), nullable=True),
            sa.Column('last_translation_date', sa.DateTime(), nullable=True),
            sa.Column('translation_cache_key', sa.String(length=64), nullable=True),
            sa.Column('word_count', sa.Integer(), nullable=True),
            sa.Column('character_count', sa.Integer(), nullable=True),
            sa.Column('has_code_blocks', sa.Boolean(), nullable=True),
            sa.Column('detected_languages', sa.JSON(), nullable=True),
            sa.Column('chunk_count', sa.Integer(), nullable=True),
            sa.Column('processing_status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_content_localization_content_hash'), 'content_localization', ['content_hash'], unique=False)
        op.create_index(op.f('ix_content_localization_content_url'), 'content_localization', ['content_url'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_content_localization_content_url'), table_name='content_localization')
    op.drop_index(op.f('ix_content_localization_content_hash'), table_name='content_localization')
    op.drop_table('content_localization')

    op.drop_index(op.f('ix_personalization_profiles_user_id'), table_name='personalization_profiles')
    op.drop_table('personalization_profiles')

    op.drop_index('idx_user_translation', table_name='translation_feedback')
    op.drop_table('translation_feedback')

    op.drop_index(op.f('ix_translations_content_hash'), table_name='translations')
    op.drop_index('idx_content_lookup', table_name='translations')
    op.drop_table('translations')