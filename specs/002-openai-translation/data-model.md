# Data Model: OpenAI Translation System

**Date**: 2025-12-12
**Feature**: 002-openai-translation

## Overview

This data model supports a robust translation system using OpenAI Agents SDK with Gemini API. It handles translation jobs, caching, error tracking, and user sessions with full observability.

## Core Entities

### 1. TranslationJob

Represents a complete translation request for a page or document.

```python
class TranslationJob:
    id: UUID (primary)
    page_url: str (indexed)
    source_language: str (default: "en")
    target_language: str (default: "ur")
    status: enum (PENDING, QUEUED, PROCESSING, CHUNK_PROCESSING, COMPLETED, FAILED, CANCELLED)
    total_chunks: int
    completed_chunks: int
    total_tokens: int
    cost_usd: decimal
    quality_score: float (0-1)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime (nullable)
    error_message: text (nullable)

    # Relationships
    chunks: List[TranslationChunk] (one-to-many)
    errors: List[TranslationError] (one-to-many)
    cache_entries: List[TranslationCache] (one-to-many)
```

### 2. TranslationChunk

Represents individual chunks of content for large translations.

```python
class TranslationChunk:
    id: UUID (primary)
    job_id: UUID (foreign key)
    chunk_index: int
    source_text: text
    translated_text: text (nullable)
    status: enum (PENDING, PROCESSING, COMPLETED, FAILED, RETRY, SKIPPED)
    retry_count: int (default: 0)
    token_count: int
    has_code_blocks: boolean
    processing_time_ms: int
    created_at: datetime
    updated_at: datetime
    error_detail: json (nullable)

    # Relationships
    job: TranslationJob (many-to-one)
    errors: List[TranslationError] (one-to-many)
```

### 3. TranslationCache

Stores cached translations with intelligent invalidation.

```python
class TranslationCache:
    id: UUID (primary)
    page_url: str (indexed)
    content_hash: str (indexed)
    source_language: str
    target_language: str
    translated_content: text
    translation_metadata: json
    quality_score: float (0-1)
    hit_count: int (default: 0)
    last_hit_at: datetime (nullable)
    ttl_hours: int (default: 24)
    priority: enum (LOW, MEDIUM, HIGH)
    created_at: datetime
    updated_at: datetime

    # Composite index: (page_url, content_hash, target_language)
```

### 4. TranslationError

Tracks all errors with retry logic and resolution tracking.

```python
class TranslationError:
    id: UUID (primary)
    job_id: UUID (foreign key, nullable)
    chunk_id: UUID (foreign key, nullable)
    error_type: enum (API_ERROR, RATE_LIMIT, CONTENT_TOO_LARGE, INVALID_CONTENT, SYSTEM_ERROR)
    severity: enum (LOW, MEDIUM, HIGH, CRITICAL)
    error_code: str (nullable)
    error_message: text
    retry_attempt: int
    next_retry_at: datetime
    resolved_at: datetime (nullable)
    resolution_note: text (nullable)
    debug_info: json (nullable)
    created_at: datetime

    # Relationships
    job: TranslationJob (many-to-one, optional)
    chunk: TranslationChunk (many-to-one, optional)
```

### 5. TranslationSession

Manages user sessions with rate limiting and preferences.

```python
class TranslationSession:
    id: UUID (primary)
    session_key: str (unique, indexed)
    user_id: str (nullable, indexed)
    ip_address: str (indexed)
    user_agent: text
    preferences: json (default: {})
    rate_limit_remaining: int (default: 100)
    rate_limit_reset_at: datetime
    last_activity_at: datetime
    created_at: datetime
    expires_at: datetime

    # Relationships
    jobs: List[TranslationJob] (one-to-many)
    metrics: List[TranslationMetrics] (one-to-many)
```

### 6. TranslationMetrics

Stores analytics and performance metrics.

```python
class TranslationMetrics:
    id: UUID (primary)
    session_id: UUID (foreign key, nullable)
    metric_type: enum (REQUEST_COUNT, TOKEN_USAGE, COST, LATENCY, ERROR_RATE, CACHE_HIT_RATE)
    metric_value: float
    metric_unit: str (e.g., "count", "tokens", "dollars", "ms", "percentage")
    time_period: enum (HOURLY, DAILY, WEEKLY, MONTHLY)
    recorded_at: datetime

    # Relationships
    session: TranslationSession (many-to-one, optional)
```

## State Transitions

### TranslationJob States

```
PENDING → QUEUED → PROCESSING → CHUNK_PROCESSING → COMPLETED
                      ↓                              ↓
                    FAILED ← RETRY ← FAILED ← CHUNK_FAILED
```

### TranslationChunk States

```
PENDING → PROCESSING → COMPLETED
    ↓           ↓
  RETRY → FAILED
    ↓
  SKIPPED
```

## Validation Rules

### Input Validation
- page_url: Must be valid URL, max 2048 chars
- source_language: Must be in supported languages list
- target_language: Must be in supported languages list
- source_text: Max 100,000 chars per chunk

### Business Rules
- Max 100 chunks per job
- Max 3 retries per chunk
- Session TTL: 24 hours
- Cache TTL: 7-30 days based on quality
- Rate limit: 100 requests per hour per session

## Indexes for Performance

### Primary Indexes
- All id fields (UUID primary keys)
- All unique constraints

### Secondary Indexes
1. TranslationJob
   - (status, created_at) - For monitoring
   - (page_url) - For cache lookups
   - (created_at) - For cleanup

2. TranslationChunk
   - (job_id, status) - For progress tracking
   - (status, created_at) - For retry queue

3. TranslationCache
   - (page_url, content_hash, target_language) - Unique composite
   - (created_at, ttl_hours) - For cleanup

4. TranslationSession
   - (session_key) - Unique
   - (expires_at) - For cleanup
   - (ip_address, created_at) - For rate limiting

5. TranslationMetrics
   - (metric_type, time_period, recorded_at) - For analytics
   - (session_id, recorded_at) - For user analytics

## Data Retention Policies

| Entity | Retention Period | Cleanup Method |
|--------|------------------|----------------|
| TranslationJob | 90 days (30 days for content) | Soft delete, then archive |
| TranslationChunk | 90 days | Cascade delete from job |
| TranslationCache | 7-30 days (based on quality) | TTL-based expiration |
| TranslationError | 30-365 days (based on severity) | Archive critical errors |
| TranslationSession | 24 hours active, 30 days metadata | Automatic expiration |
| TranslationMetrics | 1 year (aggregated) | Rollup to summaries |

## Migration Strategy

### Initial Migration
```sql
-- Create all tables with proper constraints
-- Add all indexes
-- Set up foreign key relationships
-- Initialize with default values
```

### Data Migration from Old System
1. Extract existing translations
2. Migrate to new schema
3. Populate cache with existing translations
4. Update all references
5. Validate data integrity

## Security Considerations

### Data Encryption
- Encrypt sensitive fields at rest
- Use TLS for all data in transit
- Hash session keys

### Access Control
- Row-level security for user data
- Audit logging for all modifications
- Rate limiting per session/IP

### Privacy
- No PII stored without consent
- Automatic data expiration
- GDPR compliance features

## Performance Optimization

### Query Optimization
- Use connection pooling
- Implement read replicas for analytics
- Cache frequent queries

### Storage Optimization
- Compress large text fields
- Use partitioning for time-series data
- Implement efficient pagination

### Monitoring
- Track slow queries
- Monitor index usage
- Alert on storage thresholds

## Scaling Considerations

### Horizontal Scaling
- Database sharding by session_id
- Distributed cache (Redis cluster)
- Load balancer for multiple instances

### Vertical Scaling
- Increase memory for cache
- SSD storage for faster I/O
- Optimize query performance

## Backup and Recovery

### Backup Strategy
- Daily full backups
- Hourly incremental backups
- Point-in-time recovery capability

### Disaster Recovery
- Multi-region replication
- Automated failover
- Recovery time objective: < 1 hour