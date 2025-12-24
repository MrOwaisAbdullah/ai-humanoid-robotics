"""Add OpenAI Translation System tables

Revision ID: 005_add_openai_translation_tables
Revises: 004_add_translation_tables
Create Date: 2025-12-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, sqlite
import uuid

# revision identifiers
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    # Create translation_jobs table
    op.create_table('translation_jobs',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('job_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('page_url', sa.String(length=2048), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('source_language', sa.String(length=10), nullable=False, default='en'),
        sa.Column('target_language', sa.String(length=10), nullable=False, default='ur'),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='PENDING'),
        sa.Column('chunks_total', sa.Integer(), nullable=False, default=0),
        sa.Column('chunks_completed', sa.Integer(), nullable=False, default=0),
        sa.Column('chunks_failed', sa.Integer(), nullable=False, default=0),
        sa.Column('progress_percentage', sa.Float(), nullable=False, default=0.0),
        sa.Column('input_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('output_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('total_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('preserve_code_blocks', sa.Boolean(), nullable=False, default=True),
        sa.Column('enable_transliteration', sa.Boolean(), nullable=False, default=True),
        sa.Column('chunk_size', sa.Integer(), nullable=False, default=2000),
        sa.Column('max_chunks', sa.Integer(), nullable=False, default=100),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id'),
        sa.CheckConstraint('chunks_total >= 0', name='check_chunks_total_non_negative'),
        sa.CheckConstraint('chunks_completed >= 0', name='check_chunks_completed_non_negative'),
        sa.CheckConstraint('chunks_failed >= 0', name='check_chunks_failed_non_negative'),
        sa.CheckConstraint('progress_percentage >= 0.0 AND progress_percentage <= 100.0', name='check_progress_percentage_range'),
        sa.CheckConstraint('chunk_size > 0', name='check_chunk_size_positive'),
        sa.CheckConstraint('max_chunks > 0', name='check_max_chunks_positive'),
        sa.CheckConstraint('max_retries >= 0', name='check_max_retries_non_negative')
    )
    op.create_index('ix_translation_jobs_job_id', 'translation_jobs', ['job_id'], unique=False)
    op.create_index('ix_translation_jobs_user_id', 'translation_jobs', ['user_id'], unique=False)
    op.create_index('ix_translation_jobs_session_id', 'translation_jobs', ['session_id'], unique=False)
    op.create_index('ix_translation_jobs_page_url', 'translation_jobs', ['page_url'], unique=False)
    op.create_index('ix_translation_jobs_content_hash', 'translation_jobs', ['content_hash'], unique=False)
    op.create_index('ix_translation_jobs_status', 'translation_jobs', ['status'], unique=False)
    op.create_index('ix_translation_jobs_created_at', 'translation_jobs', ['created_at'], unique=False)

    # Create translation_chunks table
    op.create_table('translation_chunks',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='PENDING'),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('start_position', sa.Integer(), nullable=False),
        sa.Column('end_position', sa.Integer(), nullable=False),
        sa.Column('is_code_block', sa.Boolean(), nullable=False, default=False),
        sa.Column('code_language', sa.String(length=50), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=False, default=0),
        sa.Column('token_count', sa.Integer(), nullable=False, default=0),
        sa.Column('input_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('output_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['translation_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('chunk_index >= 0', name='check_chunk_index_non_negative'),
        sa.CheckConstraint('start_position >= 0', name='check_start_position_non_negative'),
        sa.CheckConstraint('end_position >= start_position', name='check_end_position_after_start'),
        sa.CheckConstraint('word_count >= 0', name='check_word_count_non_negative'),
        sa.CheckConstraint('token_count >= 0', name='check_token_count_non_negative'),
        sa.CheckConstraint('retry_count >= 0', name='check_retry_count_non_negative'),
        sa.UniqueConstraint('job_id', 'chunk_index', name='uq_job_chunk_index')
    )
    op.create_index('ix_translation_chunks_job_id', 'translation_chunks', ['job_id'], unique=False)
    op.create_index('ix_translation_chunks_status', 'translation_chunks', ['status'], unique=False)
    op.create_index('ix_translation_chunks_is_code_block', 'translation_chunks', ['is_code_block'], unique=False)

    # Create translation_cache table
    op.create_table('translation_cache',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('page_url', sa.String(length=2048), nullable=True),
        sa.Column('url_hash', sa.String(length=32), nullable=True),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('translation_metadata', sa.JSON(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=False, default=False),
        sa.Column('hit_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_hit_at', sa.DateTime(), nullable=True),
        sa.Column('ttl_hours', sa.Integer(), nullable=False, default=24),
        sa.Column('priority', sa.String(length=10), nullable=False, default='MEDIUM'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['job_id'], ['translation_jobs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
        sa.CheckConstraint('quality_score >= 0.0 AND quality_score <= 5.0', name='check_quality_score_range'),
        sa.CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0', name='check_confidence_score_range'),
        sa.CheckConstraint('hit_count >= 0', name='check_hit_count_non_negative'),
        sa.CheckConstraint('ttl_hours > 0', name='check_ttl_hours_positive')
    )
    op.create_index('ix_translation_cache_cache_key', 'translation_cache', ['cache_key'], unique=False)
    op.create_index('ix_translation_cache_content_hash', 'translation_cache', ['content_hash'], unique=False)
    op.create_index('ix_translation_cache_page_url', 'translation_cache', ['page_url'], unique=False)
    op.create_index('ix_translation_cache_url_hash', 'translation_cache', ['url_hash'], unique=False)
    op.create_index('ix_translation_cache_expires_at', 'translation_cache', ['expires_at'], unique=False)
    op.create_index('ix_translation_cache_priority', 'translation_cache', ['priority'], unique=False)

    # Create translation_errors table
    op.create_table('translation_errors',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('error_id', sa.String(length=255), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('chunk_id', sa.UUID(), nullable=True),
        sa.Column('error_type', sa.String(length=50), nullable=False),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, default='translation'),
        sa.Column('is_retriable', sa.Boolean(), nullable=False, default=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, default=False),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['job_id'], ['translation_jobs.id']),
        sa.ForeignKeyConstraint(['chunk_id'], ['translation_chunks.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('error_id'),
        sa.CheckConstraint('retry_count >= 0', name='check_error_retry_count_non_negative'),
        sa.CheckConstraint('max_retries >= 0', name='check_error_max_retries_non_negative')
    )
    op.create_index('ix_translation_errors_error_id', 'translation_errors', ['error_id'], unique=False)
    op.create_index('ix_translation_errors_job_id', 'translation_errors', ['job_id'], unique=False)
    op.create_index('ix_translation_errors_chunk_id', 'translation_errors', ['chunk_id'], unique=False)
    op.create_index('ix_translation_errors_error_type', 'translation_errors', ['error_type'], unique=False)
    op.create_index('ix_translation_errors_severity', 'translation_errors', ['severity'], unique=False)
    op.create_index('ix_translation_errors_created_at', 'translation_errors', ['created_at'], unique=False)

    # Create translation_sessions table
    op.create_table('translation_sessions',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('source_language', sa.String(length=10), nullable=False, default='en'),
        sa.Column('target_language', sa.String(length=10), nullable=False, default='ur'),
        sa.Column('preferred_model', sa.String(length=100), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=False, default=0),
        sa.Column('character_count', sa.Integer(), nullable=False, default=0),
        sa.Column('total_cost_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('session_data', sa.JSON(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_activity_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
        sa.CheckConstraint('request_count >= 0', name='check_session_request_count_non_negative'),
        sa.CheckConstraint('character_count >= 0', name='check_session_character_count_non_negative'),
        sa.CheckConstraint('total_cost_usd >= 0.0', name='check_session_total_cost_non_negative')
    )
    op.create_index('ix_translation_sessions_session_id', 'translation_sessions', ['session_id'], unique=False)
    op.create_index('ix_translation_sessions_user_id', 'translation_sessions', ['user_id'], unique=False)
    op.create_index('ix_translation_sessions_expires_at', 'translation_sessions', ['expires_at'], unique=False)

    # Create translation_metrics table
    op.create_table('translation_metrics',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('metric_date', sa.DateTime(), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False, default='daily'),
        sa.Column('total_requests', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_requests', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_requests', sa.Integer(), nullable=False, default=0),
        sa.Column('cached_requests', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_processing_time_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('p95_processing_time_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('p99_processing_time_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('total_characters', sa.Integer(), nullable=False, default=0),
        sa.Column('total_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('total_cost_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('avg_quality_score', sa.Float(), nullable=True),
        sa.Column('cache_hit_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('error_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('top_error_types', sa.JSON(), nullable=True),
        sa.Column('language_pairs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('total_requests >= 0', name='check_metrics_total_requests_non_negative'),
        sa.CheckConstraint('successful_requests >= 0', name='check_metrics_successful_requests_non_negative'),
        sa.CheckConstraint('failed_requests >= 0', name='check_metrics_failed_requests_non_negative'),
        sa.CheckConstraint('cached_requests >= 0', name='check_metrics_cached_requests_non_negative'),
        sa.CheckConstraint('total_characters >= 0', name='check_metrics_total_characters_non_negative'),
        sa.CheckConstraint('total_tokens >= 0', name='check_metrics_total_tokens_non_negative'),
        sa.CheckConstraint('total_cost_usd >= 0.0', name='check_metrics_total_cost_non_negative'),
        sa.CheckConstraint('avg_processing_time_ms >= 0.0', name='check_metrics_avg_processing_time_non_negative'),
        sa.CheckConstraint('p95_processing_time_ms >= 0.0', name='check_metrics_p95_processing_time_non_negative'),
        sa.CheckConstraint('p99_processing_time_ms >= 0.0', name='check_metrics_p99_processing_time_non_negative'),
        sa.CheckConstraint('cache_hit_rate >= 0.0 AND cache_hit_rate <= 1.0', name='check_metrics_cache_hit_rate_range'),
        sa.CheckConstraint('error_rate >= 0.0 AND error_rate <= 1.0', name='check_metrics_error_rate_range'),
        sa.UniqueConstraint('metric_date', 'period_type', name='uq_metrics_date_period')
    )
    op.create_index('ix_translation_metrics_metric_date', 'translation_metrics', ['metric_date'], unique=False)
    op.create_index('ix_translation_metrics_period_type', 'translation_metrics', ['period_type'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index('ix_translation_metrics_period_type', table_name='translation_metrics')
    op.drop_index('ix_translation_metrics_metric_date', table_name='translation_metrics')
    op.drop_table('translation_metrics')

    op.drop_index('ix_translation_sessions_expires_at', table_name='translation_sessions')
    op.drop_index('ix_translation_sessions_user_id', table_name='translation_sessions')
    op.drop_index('ix_translation_sessions_session_id', table_name='translation_sessions')
    op.drop_table('translation_sessions')

    op.drop_index('ix_translation_errors_created_at', table_name='translation_errors')
    op.drop_index('ix_translation_errors_severity', table_name='translation_errors')
    op.drop_index('ix_translation_errors_error_type', table_name='translation_errors')
    op.drop_index('ix_translation_errors_chunk_id', table_name='translation_errors')
    op.drop_index('ix_translation_errors_job_id', table_name='translation_errors')
    op.drop_index('ix_translation_errors_error_id', table_name='translation_errors')
    op.drop_table('translation_errors')

    op.drop_index('ix_translation_cache_priority', table_name='translation_cache')
    op.drop_index('ix_translation_cache_expires_at', table_name='translation_cache')
    op.drop_index('ix_translation_cache_url_hash', table_name='translation_cache')
    op.drop_index('ix_translation_cache_page_url', table_name='translation_cache')
    op.drop_index('ix_translation_cache_content_hash', table_name='translation_cache')
    op.drop_index('ix_translation_cache_cache_key', table_name='translation_cache')
    op.drop_table('translation_cache')

    op.drop_index('ix_translation_chunks_is_code_block', table_name='translation_chunks')
    op.drop_index('ix_translation_chunks_status', table_name='translation_chunks')
    op.drop_index('ix_translation_chunks_job_id', table_name='translation_chunks')
    op.drop_table('translation_chunks')

    op.drop_index('ix_translation_jobs_created_at', table_name='translation_jobs')
    op.drop_index('ix_translation_jobs_status', table_name='translation_jobs')
    op.drop_index('ix_translation_jobs_content_hash', table_name='translation_jobs')
    op.drop_index('ix_translation_jobs_page_url', table_name='translation_jobs')
    op.drop_index('ix_translation_jobs_session_id', table_name='translation_jobs')
    op.drop_index('ix_translation_jobs_user_id', table_name='translation_jobs')
    op.drop_index('ix_translation_jobs_job_id', table_name='translation_jobs')
    op.drop_table('translation_jobs')