# Data Retention Policies for OpenAI Translation System

This document outlines the data retention policies for the OpenAI translation system, ensuring compliance with privacy regulations, optimal performance, and cost management.

## Overview

The translation system stores various types of data with different retention requirements:
- Translation jobs and chunks
- Cached translations
- Error logs
- Session data
- Usage metrics
- User preferences

## Retention Policies by Entity

### 1. Translation Jobs

**Table**: `translation_jobs`

| Data Field | Retention Period | Reason |
|------------|------------------|---------|
| Job metadata (ID, status, timestamps) | 90 days | Audit trail and support |
| Original and translated text | 30 days (unless pinned) | Privacy and storage optimization |
| Performance metrics | 90 days | Analytics and improvement |
| Cost tracking | 365 days | Financial records |
| Quality scores | 90 days | Model improvement |

**Special Cases**:
- Jobs marked as "pinned" or "featured" are retained indefinitely
- Jobs with user feedback are retained for 180 days
- Failed jobs are retained for 30 days for debugging

### 2. Translation Chunks

**Table**: `translation_chunks`

| Data Field | Retention Period | Reason |
|------------|------------------|---------|
| All chunk data | 30 days | Linked to parent job retention |
| Error information | 90 days | Debugging and improvement |

**Cleanup Strategy**:
- Chunks are automatically deleted when their parent job is deleted
- Independent cleanup runs every 7 days to remove orphaned chunks

### 3. Translation Cache

**Table**: `translation_cache`

| Cache Type | Retention Period | TTL | Auto-Cleanup |
|------------|------------------|-----|--------------|
| Standard translations | 7 days | 168 hours | Yes |
| High-quality translations (score ≥ 4.5) | 30 days | 720 hours | Yes |
| Pinned entries | Indefinite | None | No |
| Low-quality translations (score < 3.0) | 1 day | 24 hours | Yes |
| Page-specific cache | 7 days | 168 hours | Yes |

**Cache Eviction Strategy**:
1. Expired entries are removed first
2. Low-priority entries are evicted based on LRU
3. Low hit-rate entries are prioritized for eviction
4. Cache cleanup runs every 6 hours

### 4. Translation Errors

**Table**: `translation_errors`

| Error Severity | Retention Period | Reason |
|----------------|------------------|---------|
| Critical | 365 days | Compliance and audit |
| High | 180 days | Service improvement |
| Medium | 90 days | Debugging |
| Low | 30 days | Pattern analysis |

**Additional Rules**:
- Unresolved errors are retained until resolution
- Frequently recurring errors are retained for 365 days regardless of severity
- Resolved errors are anonymized after 180 days

### 5. Translation Sessions

**Table**: `translation_sessions`

| Data Field | Retention Period | Reason |
|------------|------------------|---------|
| Active sessions | Until expiry (24 hours inactivity) | Security |
| Session metadata | 30 days | Analytics |
| IP addresses | 30 days | Security monitoring |
- User agents | 30 days | Compatibility tracking |
- Preferences | 365 days | User experience |

**Cleanup Strategy**:
- Expired sessions are cleaned every hour
- Inactive sessions (>24 hours) are automatically marked as expired
- Session data is aggregated into metrics before deletion

### 6. Translation Metrics

**Table**: `translation_metrics`

| Metric Type | Retention Period | Aggregation |
|-------------|------------------|------------|
| Hourly metrics | 7 days | → Daily |
| Daily metrics | 90 days | → Weekly/Monthly |
| Weekly metrics | 365 days | → Monthly |
| Monthly metrics | Indefinite | — |
| Error metrics | 180 days | — |

**Data Lifecycle**:
1. Raw hourly data is kept for 7 days
2. Aggregated to daily metrics and kept for 90 days
3. Further aggregated to weekly/monthly for long-term storage

## Automated Cleanup Jobs

### Daily Cleanup (2:00 AM UTC)
1. Delete expired translation jobs (older than retention period)
2. Remove expired cache entries
3. Clean up resolved errors past retention
4. Delete expired sessions

### Weekly Cleanup (Sunday 3:00 AM UTC)
1. Aggregate and purge detailed metrics
2. Optimize table sizes
3. Update statistics
4. Identify orphaned records

### Monthly Cleanup (1st of month, 4:00 AM UTC)
1. Archive critical data to long-term storage
2. Compress historical metrics
3. Review and adjust retention policies
4. Generate retention compliance report

## Privacy and Compliance

### Data Anonymization
After retention period expiration, sensitive data is anonymized:
- User IDs → Random UUIDs
- IP addresses → Hashed values
- User agents → Generic identifiers
- Original text content → SHA-256 hashes

### Right to Deletion
Users can request deletion of their data:
- Immediate deletion of personal identifiers
- Translation jobs anonymized after 48 hours
- Cache entries invalidated and deleted
- Session data immediately purged

### GDPR Compliance
- Data retention periods documented
- Automated cleanup processes
- Audit trails for deletion activities
- Data portability exports available

## Storage Optimization

### Partitioning Strategy
Large tables are partitioned by date:
```sql
-- translation_jobs partitioned by month
-- translation_metrics partitioned by year
-- translation_errors partitioned by severity and date
```

### Compression
- Historical data compressed using table-level compression
- JSONB columns use TOAST compression
- Text fields stored as external TOAST for large content

### Archive Storage
- Data older than 1 year moved to archival storage
- Cold storage for metrics older than 2 years
- Backup retention: 30 days for recent, 1 year for monthly

## Monitoring and Alerts

### Retention Monitoring
- Daily reports on data volume by age
- Alerts for tables exceeding size thresholds
- Monitoring of cleanup job success/failure
- Compliance dashboards

### Storage Metrics
```python
# Example monitoring queries
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size(table_name)) as size,
    COUNT(*) as row_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_name LIKE 'translation_%'
GROUP BY table_name;
```

## Configuration

Retention periods are configurable via environment variables:
```bash
# Default retention periods in days
TRANSLATION_JOB_RETENTION=90
TRANSLATION_CACHE_RETENTION=7
TRANSLATION_ERROR_RETENTION=90
TRANSLATION_SESSION_RETENTION=30
TRANSLATION_METRICS_DAILY_RETENTION=90
TRANSLATION_METRICS_MONTHLY_RETENTION=365
```

## Emergency Procedures

### Data Purge Request
For immediate data deletion due to security or privacy concerns:
1. Execute emergency purge script
2. Truncate affected tables
3. Log emergency action with audit trail
4. Notify compliance team

### Backup Restoration
- Point-in-time recovery available for 30 days
- Selective restoration possible
- Audit log tracks all restoration activities

## Implementation Notes

### Database Triggers
```sql
-- Example: Automatic expiration trigger
CREATE OR REPLACE FUNCTION update_translation_job_expires_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.expires_at = NOW() + INTERVAL '90 days';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_translation_job_expires_at
    BEFORE INSERT ON translation_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_translation_job_expires_at();
```

### Batch Deletion
```sql
-- Efficient batch deletion for large datasets
DELETE FROM translation_jobs
WHERE created_at < NOW() - INTERVAL '90 days'
    AND id IN (
        SELECT id FROM translation_jobs
        WHERE created_at < NOW() - INTERVAL '90 days'
        LIMIT 10000
    );
```

This retention policy ensures compliance with privacy regulations while maintaining system performance and providing valuable analytics for service improvement.