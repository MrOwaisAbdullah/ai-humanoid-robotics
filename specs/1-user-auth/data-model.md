# Data Model: User Authentication System

## Entity Relationship Diagram

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│    User     │      │    Account   │      │   Session   │
├─────────────┤      ├──────────────┤      ├─────────────┤
│ id (PK)     │◄─────┤ user_id (FK) │◄─────┤ user_id(FK) │
│ email      │      │ id (PK)      │      │ id (PK)     │
│ name       │      │ provider     │      │ token       │
│ image_url  │      │ provider_id  │      │ expires_at  │
│ email_verified│  │ access_token │      │ created_at  │
│ created_at │      │ refresh_token│      └─────────────┘
│ updated_at │      │ expires_at   │
└─────────────┘      │ created_at   │
        │             │ updated_at   │
        │             └──────────────┘
        │
        ▼
┌─────────────────┐      ┌──────────────┐
│ UserPreferences │      │  ChatSession  │
├─────────────────┤      ├──────────────┤
│ id (PK)         │◄─────┤ user_id (FK) │
│ user_id (FK)    │      │ id (PK)      │
│ theme           │      │ title        │
│ language        │      │ created_at   │
│ notifications   │      │ updated_at   │
│ chat_settings   │      └──────────────┘
│ created_at      │             │
│ updated_at      │             ▼
└─────────────────┘      ┌──────────────┐
                          │  ChatMessage  │
                          ├──────────────┤
                          │ id (PK)      │
                          │ session_id(FK)│
                          │ role         │
                          │ content      │
                          │ metadata     │
                          │ created_at   │
                          └──────────────┘
```

## Entity Definitions

### User
Represents a registered user in the system.

**Fields:**
- `id` (Integer, Primary Key): Unique identifier
- `email` (String, Unique, Required): User's email address
- `name` (String, Required): Display name
- `image_url` (String, Optional): Profile picture URL
- `email_verified` (Boolean, Default: false): Verification status from OAuth
- `created_at` (DateTime, Auto): Account creation timestamp
- `updated_at` (DateTime, Auto): Last update timestamp

**Validation Rules:**
- Email must be valid format
- Name must be non-empty
- Email must be unique across all users

**Indexes:**
- Primary key on `id`
- Unique index on `email`

### Account
Stores OAuth provider account information linked to users.

**Fields:**
- `id` (Integer, Primary Key): Unique identifier
- `user_id` (Integer, Foreign Key → User.id): Associated user
- `provider` (String, Required): OAuth provider name (e.g., 'google')
- `provider_account_id` (String, Required): Provider's user ID
- `access_token` (Text, Optional): OAuth access token
- `refresh_token` (Text, Optional): OAuth refresh token
- `expires_at` (DateTime, Optional): Token expiration time
- `token_type` (String, Optional): Type of token (Bearer, etc.)
- `scope` (String, Optional): Granted permissions
- `created_at` (DateTime, Auto): Account linkage timestamp
- `updated_at` (DateTime, Auto): Last update timestamp

**Validation Rules:**
- user_id must exist in Users table
- Provider must be from allowed list
- provider_account_id must be unique per provider

**Indexes:**
- Primary key on `id`
- Unique index on (provider, provider_account_id)
- Foreign key index on `user_id`

### Session
Manages active user sessions with JWT tokens.

**Fields:**
- `id` (Integer, Primary Key): Unique identifier
- `user_id` (Integer, Foreign Key → User.id): Session owner
- `token` (String, Unique, Required): JWT token or session identifier
- `expires_at` (DateTime, Required): Session expiration time
- `created_at` (DateTime, Auto): Session creation timestamp
- `updated_at` (DateTime, Auto): Last activity timestamp

**Validation Rules:**
- user_id must exist in Users table
- token must be unique
- expires_at must be in the future

**Constraints:**
- Single active session per user (new login invalidates old ones)

**Indexes:**
- Primary key on `id`
- Unique index on `token`
- Foreign key index on `user_id`
- Index on `expires_at` for cleanup

### ChatSession
Represents conversation threads for users.

**Fields:**
- `id` (Integer, Primary Key): Unique identifier
- `user_id` (Integer, Foreign Key → User.id): Session owner
- `title` (String, Required): Display title for the chat
- `created_at` (DateTime, Auto): Session creation timestamp
- `updated_at` (DateTime, Auto): Last message timestamp

**Validation Rules:**
- user_id must exist in Users table
- title must be non-empty
- Title auto-generated from first message if not provided

**Behavior:**
- Title auto-generated from first user message (first 50 chars)
- Updated_at refreshed on each new message

**Indexes:**
- Primary key on `id`
- Foreign key index on `user_id`
- Index on `updated_at` for sorting recent chats

### ChatMessage
Individual messages within chat sessions.

**Fields:**
- `id` (Integer, Primary Key): Unique identifier
- `session_id` (Integer, Foreign Key → ChatSession.id): Parent session
- `role` (String, Required): Message role ('user', 'assistant', 'system')
- `content` (Text, Required): Message content
- `metadata` (JSON, Optional): Additional data (citations, model info)
- `created_at` (DateTime, Auto): Message timestamp

**Validation Rules:**
- session_id must exist in ChatSession table
- role must be one of: 'user', 'assistant', 'system'
- content must be non-empty

**Metadata Schema:**
```json
{
  "model": "gpt-4o-mini",
  "citations": ["doc1.pdf:page-23", "doc2.pdf:page-45"],
  "tokens_used": 150,
  "processing_time_ms": 1250
}
```

**Indexes:**
- Primary key on `id`
- Foreign key index on `session_id`
- Index on `created_at` for message ordering

### UserPreferences
User-specific settings and preferences.

**Fields:**
- `id` (Integer, Primary Key): Unique identifier
- `user_id` (Integer, Foreign Key → User.id, Unique): Preference owner
- `theme` (String, Default: 'light'): UI theme ('light', 'dark', 'auto')
- `language` (String, Default: 'en'): Interface language
- `notifications_enabled` (Boolean, Default: true): Notification settings
- `chat_settings` (JSON, Optional): Chat-specific preferences
- `created_at` (DateTime, Auto): Preference creation timestamp
- `updated_at` (DateTime, Auto): Last update timestamp

**Validation Rules:**
- user_id must exist and be unique
- theme must be from allowed list
- language must be valid language code

**chat_settings Schema:**
```json
{
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 1000,
  "show_citations": true,
  "auto_save": true
}
```

**Indexes:**
- Primary key on `id`
- Unique index on `user_id`

## Data Flow Examples

### Authentication Flow
1. User clicks "Sign in with Google"
2. Redirect to Google OAuth
3. Google redirects back with authorization code
4. Exchange code for tokens
5. Create/update Account record
6. Create/update User record
7. Create Session record with JWT
8. Set HTTP-only cookie with session token

### Chat Message Flow
1. User sends message (authenticated or anonymous)
2. Create/verify Session
3. Create ChatMessage record
4. Process with RAG system
5. Create assistant response ChatMessage
6. Update ChatSession.updated_at
7. Return streaming response

### Anonymous Migration Flow
1. User has anonymous session with messages
2. User signs in with Google
3. Create User and Account records
4. Create new ChatSession for user
5. Copy anonymous messages to ChatMessage records
6. Delete anonymous session data
7. Establish user session

## Database Schema SQL

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    image_url TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table for OAuth
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    provider_account_id TEXT NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at DATETIME,
    token_type TEXT,
    scope TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(provider, provider_account_id)
);

-- Sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Chat sessions
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL DEFAULT 'New Chat',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Chat messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

-- User preferences
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    theme TEXT DEFAULT 'light' CHECK (theme IN ('light', 'dark', 'auto')),
    language TEXT DEFAULT 'en',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    chat_settings TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Performance indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_updated_at ON chat_sessions(updated_at);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
```

## Migration Strategy

### Initial Migration
1. Create all tables with indexes
2. Migrate existing anonymous sessions to new structure
3. Set up foreign key constraints

### Data Migration from Current System
1. Extract existing chat data
2. Create user accounts for anonymous sessions
3. Preserve message order and metadata
4. Update application to use new schema

### Rollback Plan
1. Keep backup of original database
2. Version migration scripts with rollback
3. Test rollback procedure in staging