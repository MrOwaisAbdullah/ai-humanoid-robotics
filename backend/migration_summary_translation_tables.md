# Database Migration: Translation Tables (Phase 2, Task T010)

## Overview
Created Alembic migration `004_add_translation_tables.py` to add support for translation features, user feedback, personalization, and content localization.

## Migration Details
- **Revision ID**: `004_add_translation_tables`
- **Revises**: `003_reader_features_tables`
- **File**: `backend/alembic/versions/004_add_translation_tables.py`

## Tables Created

### 1. `translations` Table
Stores cached translations with content hashing for deduplication.

**Columns:**
- `id` (Integer, Primary Key)
- `content_hash` (String(64), Unique, Indexed) - SHA-256 hash for deduplication
- `source_language` (String(10)) - Source language code
- `target_language` (String(10)) - Target language code
- `original_text` (Text) - Original text to translate
- `translated_text` (Text) - Translated text
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `translation_model` (String(50)) - Model used for translation (e.g., "gemini-1.5-pro")
- `character_count` (Integer) - Character count of the text

**Indexes:**
- Unique index on `content_hash`
- Composite index `idx_content_lookup` on (`content_hash`, `source_language`, `target_language`)

### 2. `translation_feedback` Table
Stores user feedback on translations for quality improvement.

**Columns:**
- `id` (Integer, Primary Key)
- `translation_id` (Integer, Foreign Key → translations.id)
- `user_id` (String(36)) - User UUID from auth system
- `rating` (SmallInteger) - -1 (downvote) or 1 (upvote)
- `comment` (Text, Optional) - User comment on the translation
- `created_at` (DateTime) - Feedback timestamp

**Constraints:**
- Check constraint: `rating IN (-1, 1)`
- Unique composite index on (`user_id`, `translation_id`) - One feedback per user per translation

### 3. `personalization_profiles` Table
Stores user preferences for personalized content delivery.

**Columns:**
- `id` (Integer, Primary Key)
- `user_id` (String(36), Unique, Indexed) - User UUID
- `reading_level` (Enum: 'beginner', 'intermediate', 'advanced')
- `preferred_language` (String(10)) - User's preferred language
- `focus_areas` (JSON) - Array of topics user cares about
- `learning_style` (Enum: 'visual', 'practical', 'theoretical', 'balanced')
- `enable_transliteration` (Boolean) - Whether to show transliterations
- `technical_term_handling` (Enum: 'translate', 'transliterate', 'keep_english')
- `font_size` (Integer) - Preferred font size
- `focus_mode_preferences` (JSON) - Preferences for focus mode
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `last_active` (DateTime)

### 4. `content_localization` Table (Conditional Creation)
Tracks translation status and metadata for content pages.
This table is only created if it doesn't already exist.

**Columns:**
- `id` (Integer, Primary Key)
- `content_url` (String(500), Indexed) - URL of the content page
- `content_hash` (String(64), Indexed) - Content hash for change detection
- `is_translated` (Boolean) - Whether the content has been translated
- `last_translation_date` (DateTime) - When translation was last updated
- `translation_cache_key` (String(64)) - Cache key for translations
- `word_count` (Integer) - Number of words in content
- `character_count` (Integer) - Number of characters
- `has_code_blocks` (Boolean) - Whether content contains code blocks
- `detected_languages` (JSON) - Array of detected languages in content
- `chunk_count` (Integer) - Number of chunks for processing
- `processing_status` (Enum: 'pending', 'processing', 'completed', 'failed', 'partial')
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Indexes:**
- Index on `content_hash`
- Index on `content_url`

## Database Compatibility
The migration is designed to work with SQLite (current database) but is compatible with PostgreSQL as well.

## Foreign Key Relationships
- `translation_feedback.translation_id` → `translations.id`
- (Other foreign keys would be to the users table from auth system)

## Migration Usage

### To apply the migration:
```bash
cd backend
alembic upgrade head
```

### To revert the migration:
```bash
cd backend
alembic downgrade -1
```

### To check current status:
```bash
cd backend
alembic current
```

## Notes
1. The migration uses SQLite-compatible syntax but will work with PostgreSQL
2. Enum types are stored as strings with length constraints for compatibility
3. JSON fields use SQLite's JSON extension (available in SQLite 3.38+)
4. The content_localization table check prevents errors if it already exists

## Updated Files
1. `backend/alembic/versions/004_add_translation_tables.py` - Main migration file
2. `backend/alembic/env.py` - Updated to import new models for metadata registration