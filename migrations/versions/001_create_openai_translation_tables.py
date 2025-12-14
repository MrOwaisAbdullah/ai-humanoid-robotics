"""Create OpenAI translation system tables

Revision ID: 001_create_openai_translation_tables
Revises:
Create Date: 2024-01-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_openai_translation_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create translation_jobs table
    op.create_table('translation_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(length=128), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('page_url', sa.Text(), nullable=True),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('preserve_code_blocks', sa.Boolean(), nullable=False),
        sa.Column('enable_transliteration', sa.Boolean(), nullable=False),
        sa.Column('chunk_size', sa.Integer(), nullable=False),
        sa.Column('max_chunks', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=50), nullable=False),
        sa.Column('temperature', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('chunks_total', sa.Integer(), nullable=False),
        sa.Column('chunks_completed', sa.Integer(), nullable=False),
        sa.Column('chunks_failed', sa.Integer(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_ms', sa.BigInteger(), nullable=False),
        sa.Column('input_tokens', sa.BigInteger(), nullable=False),
        sa.Column('output_tokens', sa.BigInteger(), nullable=False),
        sa.Column('estimated_cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('actual_cost_usd', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )

    # Create indexes for translation_jobs
    op.create_index('ix_translation_jobs_job_id', 'translation_jobs', ['job_id'], unique=True)
    op.create_index('ix_translation_jobs_user_id', 'translation_jobs', ['user_id'])
    op.create_index('ix_translation_jobs_session_id', 'translation_jobs', ['session_id'])
    op.create_index('ix_translation_jobs_content_hash', 'translation_jobs', ['content_hash'])
    op.create_index('ix_translation_jobs_page_url', 'translation_jobs', ['page_url'])
    op.create_index('ix_translation_jobs_source_language', 'translation_jobs', ['source_language'])
    op.create_index('ix_translation_jobs_target_language', 'translation_jobs', ['target_language'])
    op.create_index('ix_translation_jobs_status', 'translation_jobs', ['status'])
    op.create_index('ix_translation_jobs_status_created', 'translation_jobs', ['status', 'created_at'])
    op.create_index('ix_translation_jobs_user_status', 'translation_jobs', ['user_id', 'status'])
    op.create_index('ix_translation_jobs_content_lookup', 'translation_jobs', ['content_hash', 'source_language', 'target_language'])
    op.create_index('ix_translation_jobs_page_cache', 'translation_jobs', ['page_url', 'content_hash'])
    op.create_index('ix_translation_jobs_activity', 'translation_jobs', ['last_activity_at'])
    op.create_index('ix_translation_jobs_progress', 'translation_jobs', ['status', 'progress_percentage'])

    # Create translation_chunks table
    op.create_table('translation_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('start_position', sa.Integer(), nullable=False),
        sa.Column('end_position', sa.Integer(), nullable=False),
        sa.Column('is_code_block', sa.Boolean(), nullable=False),
        sa.Column('code_language', sa.String(length=50), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_ms', sa.BigInteger(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('requires_review', sa.Boolean(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['translation_jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'chunk_index', name='uq_translation_chunks_job_chunk')
    )

    # Create indexes for translation_chunks
    op.create_index('ix_translation_chunks_job_id', 'translation_chunks', ['job_id'])
    op.create_index('ix_translation_chunks_job_chunk', 'translation_chunks', ['job_id', 'chunk_index'], unique=True)
    op.create_index('ix_translation_chunks_status', 'translation_chunks', ['status'])
    op.create_index('ix_translation_chunks_status_created', 'translation_chunks', ['status', 'created_at'])
    op.create_index('ix_translation_chunks_is_code_block', 'translation_chunks', ['is_code_block'])
    op.create_index('ix_translation_chunks_code_language', 'translation_chunks', ['code_language'])

    # Create translation_errors table
    op.create_table('translation_errors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_id', sa.String(length=64), nullable=False),
        sa.Column('error_type', sa.String(length=50), nullable=False),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('is_retriable', sa.Boolean(), nullable=False),
        sa.Column('retry_attempt', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('debug_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['translation_chunks.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['translation_jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('error_id')
    )

    # Create indexes for translation_errors
    op.create_index('ix_translation_errors_error_id', 'translation_errors', ['error_id'], unique=True)
    op.create_index('ix_translation_errors_job_id', 'translation_errors', ['job_id'])
    op.create_index('ix_translation_errors_chunk_id', 'translation_errors', ['chunk_id'])
    op.create_index('ix_translation_errors_error_type', 'translation_errors', ['error_type'])
    op.create_index('ix_translation_errors_severity', 'translation_errors', ['severity'])
    op.create_index('ix_translation_errors_error_type_created', 'translation_errors', ['error_type', 'created_at'])
    op.create_index('ix_translation_errors_error_severity', 'translation_errors', ['severity', 'created_at'])
    op.create_index('ix_translation_errors_job_errors', 'translation_errors', ['job_id', 'created_at'])
    op.create_index('ix_translation_errors_retry_schedule', 'translation_errors', ['next_retry_at', 'is_retriable'])

    # Create translation_sessions table
    op.create_table('translation_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(length=128), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False),
        sa.Column('character_count', sa.Integer(), nullable=False),
        sa.Column('total_cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('requests_per_minute', sa.Integer(), nullable=False),
        sa.Column('characters_per_hour', sa.Integer(), nullable=False),
        sa.Column('source_language', sa.String(length=10), nullable=True),
        sa.Column('target_language', sa.String(length=10), nullable=True),
        sa.Column('preferred_model', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=True),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )

    # Create indexes for translation_sessions
    op.create_index('ix_translation_sessions_session_id', 'translation_sessions', ['session_id'], unique=True)
    op.create_index('ix_translation_sessions_user_id', 'translation_sessions', ['user_id'])
    op.create_index('ix_translation_sessions_is_active', 'translation_sessions', ['is_active'])
    op.create_index('ix_translation_sessions_expires_at', 'translation_sessions', ['expires_at'])
    op.create_index('ix_translation_sessions_user_sessions', 'translation_sessions', ['user_id', 'is_active'])
    op.create_index('ix_translation_sessions_session_expiry', 'translation_sessions', ['expires_at', 'is_active'])
    op.create_index('ix_translation_sessions_ip_address', 'translation_sessions', ['ip_address'])

    # Create translation_cache table
    op.create_table('translation_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cache_key', sa.String(length=128), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('page_url', sa.Text(), nullable=True),
        sa.Column('url_hash', sa.String(length=64), nullable=True),
        sa.Column('source_language', sa.String(length=10), nullable=False),
        sa.Column('target_language', sa.String(length=10), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=False),
        sa.Column('last_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('processing_time_ms', sa.BigInteger(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('ttl_hours', sa.Integer(), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('is_validated', sa.Boolean(), nullable=False),
        sa.Column('validated_by', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['translation_jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )

    # Create indexes for translation_cache
    op.create_index('ix_translation_cache_cache_key', 'translation_cache', ['cache_key'], unique=True)
    op.create_index('ix_translation_cache_job_id', 'translation_cache', ['job_id'])
    op.create_index('ix_translation_cache_content_hash', 'translation_cache', ['content_hash'])
    op.create_index('ix_translation_cache_page_url', 'translation_cache', ['page_url'])
    op.create_index('ix_translation_cache_url_hash', 'translation_cache', ['url_hash'])
    op.create_index('ix_translation_cache_source_language', 'translation_cache', ['source_language'])
    op.create_index('ix_translation_cache_target_language', 'translation_cache', ['target_language'])
    op.create_index('ix_translation_cache_expires_at', 'translation_cache', ['expires_at'])
    op.create_index('ix_translation_cache_cache_lookup', 'translation_cache', ['content_hash', 'source_language', 'target_language'])
    op.create_index('ix_translation_cache_page_cache', 'translation_cache', ['url_hash', 'content_hash'])
    op.create_index('ix_translation_cache_cache_expires', 'translation_cache', ['expires_at', 'priority'])
    op.create_index('ix_translation_cache_cache_popularity', 'translation_cache', ['hit_count', 'last_hit_at'])

    # Create translation_metrics table
    op.create_table('translation_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metric_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('total_requests', sa.Integer(), nullable=False),
        sa.Column('total_characters', sa.BigInteger(), nullable=False),
        sa.Column('total_chunks', sa.Integer(), nullable=False),
        sa.Column('successful_translations', sa.Integer(), nullable=False),
        sa.Column('failed_translations', sa.Integer(), nullable=False),
        sa.Column('avg_processing_time_ms', sa.BigInteger(), nullable=False),
        sa.Column('min_processing_time_ms', sa.BigInteger(), nullable=False),
        sa.Column('max_processing_time_ms', sa.BigInteger(), nullable=False),
        sa.Column('p95_processing_time_ms', sa.BigInteger(), nullable=False),
        sa.Column('total_input_tokens', sa.BigInteger(), nullable=False),
        sa.Column('total_output_tokens', sa.BigInteger(), nullable=False),
        sa.Column('total_cost_usd', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('avg_cost_per_char', sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column('avg_quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('avg_confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('cache_hits', sa.Integer(), nullable=False),
        sa.Column('cache_misses', sa.Integer(), nullable=False),
        sa.Column('cache_hit_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('error_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('top_error_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_language', sa.String(length=10), nullable=True),
        sa.Column('target_language', sa.String(length=10), nullable=True),
        sa.Column('model_name', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['translation_jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for translation_metrics
    op.create_index('ix_translation_metrics_job_id', 'translation_metrics', ['job_id'])
    op.create_index('ix_translation_metrics_user_id', 'translation_metrics', ['user_id'])
    op.create_index('ix_translation_metrics_metric_date', 'translation_metrics', ['metric_date'])
    op.create_index('ix_translation_metrics_period_type', 'translation_metrics', ['period_type'])
    op.create_index('ix_translation_metrics_source_language', 'translation_metrics', ['source_language'])
    op.create_index('ix_translation_metrics_target_language', 'translation_metrics', ['target_language'])
    op.create_index('ix_translation_metrics_model_name', 'translation_metrics', ['model_name'])
    op.create_index('ix_translation_metrics_date_period', 'translation_metrics', ['metric_date', 'period_type'])
    op.create_index('ix_translation_metrics_user_metrics', 'translation_metrics', ['user_id', 'metric_date'])
    op.create_index('ix_translation_metrics_job_metrics', 'translation_metrics', ['job_id', 'metric_date'])
    op.create_index('ix_translation_metrics_lang_metrics', 'translation_metrics', ['source_language', 'target_language', 'metric_date'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('translation_metrics')
    op.drop_table('translation_cache')
    op.drop_table('translation_sessions')
    op.drop_table('translation_errors')
    op.drop_table('translation_chunks')
    op.drop_table('translation_jobs')