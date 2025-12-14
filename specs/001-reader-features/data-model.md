# Data Model: Reader Experience Enhancements

**Date**: 2025-01-09
**Phase**: 1 - Design & Contracts

## Entity Definitions

### 1. ReadingProgress

Tracks user's reading progress through chapters and sections.

```typescript
interface ReadingProgress {
  id: string;
  userId: string;
  chapterId: string;
  sectionId: string;
  position: number; // 0-100 (scroll position percentage)
  completed: boolean;
  timeSpent: number; // Total minutes spent in this section
  lastAccessed: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

**Validation Rules**:
- `position` must be between 0 and 100
- `timeSpent` must be non-negative
- `userId` must reference valid user
- `chapterId` and `sectionId` must match content structure

**Relationships**:
- Many-to-One with User (userId)
- Many-to-One with Chapter (chapterId)

### 2. Bookmark

Represents user-saved page references with optional metadata.

```typescript
interface Bookmark {
  id: string;
  userId: string;
  chapterId: string;
  sectionId?: string;
  pageUrl: string;
  pageTitle: string;
  snippet: string; // Text snippet or highlighted content
  note: string; // User's private note
  tags: string[]; // User-defined tags for organization
  isPrivate: boolean; // Whether bookmark is private
  createdAt: Date;
  updatedAt: Date;
}
```

**Validation Rules**:
- `pageTitle` required, max 255 characters
- `note` optional, max 1000 characters
- `tags` array max 10 items, each max 50 characters
- Soft limit of 1000 bookmarks per user

**Relationships**:
- Many-to-One with User (userId)
- Many-to-One with Chapter (chapterId)

### 3. UserPreference

Stores user personalization settings.

```typescript
interface UserPreference {
  id: string;
  userId: string;
  language: 'en' | 'ur' | 'ur-roman';
  readingPace: 'slow' | 'medium' | 'fast';
  preferredDepth: 'overview' | 'detailed' | 'comprehensive';
  showCodeExamples: boolean;
  adaptiveDifficulty: boolean;
  theme: 'light' | 'dark' | 'auto';
  fontSize: number; // 12-24px
  lineHeight: number; // 1.2-2.0
  customNotes: Map<string, string>; // Key-value pairs for custom settings
  createdAt: Date;
  updatedAt: Date;
}
```

**Validation Rules**:
- `fontSize` must be between 12 and 24
- `lineHeight` must be between 1.2 and 2.0
- `customNotes` max 10 entries
- Language must be one of supported locales

**Relationships**:
- One-to-One with User (userId)

### 4. ContentLocalization

Represents translated content variants.

```typescript
interface ContentLocalization {
  id: string;
  contentId: string; // Reference to original content
  language: 'en' | 'ur' | 'ur-roman';
  title: string;
  content: string;
  metadata: {
    wordCount: number;
    readingTimeMinutes: number;
    lastUpdated: Date;
    translator?: string;
    reviewed: boolean;
  };
  createdAt: Date;
  updatedAt: Date;
}
```

**Validation Rules**:
- `title` required, max 255 characters
- `content` required
- `wordCount` must match actual content
- `readingTimeMinutes` calculated based on 200 WPM

### 5. SearchIndex

Enables fast content retrieval across languages.

```typescript
interface SearchIndex {
  id: string;
  contentId: string;
  language: 'en' | 'ur' | 'ur-roman';
  contentType: 'chapter' | 'section' | 'bookmark';
  title: string;
  content: string;
  keywords: string[];
  chapterId: string;
  sectionId?: string;
  rank: number; // Search relevance rank
  indexedAt: Date;
}
```

**Validation Rules**:
- `keywords` array max 20 items
- `rank` between 0 and 1
- Must be indexed with content updates

## State Transitions

### Reading Progress States

```
Not Started → In Progress → Completed
     ↑              ↓
     └─────── Resume ─┘
```

- **Not Started**: Initial state when user hasn't accessed content
- **In Progress**: User has started reading, position > 0
- **Completed**: User has reached end of section (position = 100)

### Bookmark Lifecycle

```
Created → Updated → Deleted
   ↑
   └── Modified
```

- **Created**: Initial bookmark creation
- **Updated**: Note or metadata changes
- **Deleted**: User removes bookmark

## Data Integrity Constraints

### Uniqueness Constraints

1. **ReadingProgress**:
   - Unique combination of (userId, chapterId, sectionId)

2. **UserPreference**:
   - Unique userId (one-to-one relationship)

3. **ContentLocalization**:
   - Unique combination of (contentId, language)

### Referential Integrity

1. **Cascade Deletes**:
   - Deleting User → Delete their ReadingProgress, Bookmarks, UserPreference
   - Deleting Content → Delete related ContentLocalization and SearchIndex

2. **Null Constraints**:
   - ReadingProgress.userId cannot be null
   - Bookmark.userId cannot be null
   - UserPreference.userId cannot be null

## Performance Considerations

### Indexing Strategy

```sql
-- Reading Progress
CREATE INDEX idx_reading_progress_user_chapter
ON reading_progress(userId, chapterId);

-- Bookmarks
CREATE INDEX idx_bookmarks_user_created
ON bookmarks(userId, createdAt DESC);
CREATE INDEX idx_bookmarks_tags
ON bookmarks USING GIN(tags);

-- Search Index
CREATE INDEX idx_search_index_language_rank
ON search_index(language, rank DESC);
```

### Data Partitioning

Consider partitioning ReadingProgress by userId for large datasets:
```sql
-- Partition by user_id hash for scalability
CREATE TABLE reading_progress_partitioned (
  LIKE reading_progress INCLUDING ALL
) PARTITION BY HASH (userId);
```

## Security Considerations

### Data Privacy

1. **User Data**:
   - All user-specific data must be associated with authenticated user
   - Private bookmarks marked with isPrivate flag

2. **Access Control**:
   - Users can only access their own ReadingProgress and Bookmarks
   - Admin users can access aggregated analytics only

### Data Sanitization

1. **Input Validation**:
   - Strip HTML from user notes
   - Validate URL formats for pageUrl
   - Limit tag lengths and counts

2. **Output Encoding**:
   - Encode all user-generated content
   - Prevent XSS in bookmark snippets and notes

## Migration Strategy

### Phase 1: Initial Tables

```sql
-- Create tables without data
CREATE TABLE reading_progress (...);
CREATE TABLE bookmarks (...);
CREATE TABLE user_preferences (...);
```

### Phase 2: Populate Initial Data

```sql
-- Set default preferences for existing users
INSERT INTO user_preferences (userId, language, ...)
SELECT id, 'en', ... FROM users;
```

### Phase 3: Add Constraints

```sql
-- Add unique constraints after initial data
ALTER TABLE reading_progress
ADD CONSTRAINT unique_user_section
UNIQUE (userId, chapterId, sectionId);
```