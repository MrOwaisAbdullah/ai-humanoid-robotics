# Data Model: Authentication and UX Improvements

## Overview
Data models for guest session tracking, authentication persistence, and user background collection.

## Entity Relationship Diagram

```
User (1) -----> (1) UserBackground
User (1) -----> (n) PersistentSession
Session (n) --> AnonymousSession (1)
Session (n) --> UserSession (1)
```

## 1. AnonymousSession

**Purpose**: Tracks guest user message counts and activity for 24-hour periods.

```typescript
interface AnonymousSession {
  id: string;           // UUID primary key
  message_count: number; // Current message count (0-3)
  created_at: Date;     // Session creation timestamp
  last_activity: Date;  // Last activity timestamp
  expires_at: Date;     // Session expiration (24h)
  ip_address?: string;  // User IP for fallback tracking
  user_agent?: string;  // Browser user agent for fingerprint
  fingerprint?: string; // Device fingerprint for session recovery
}
```

**Validation Rules**:
- `message_count`: Must be 0-3
- `expires_at`: Must be 24 hours after `created_at`
- `fingerprint`: Optional, used for localStorage fallback recovery

**State Transitions**:
```
Created → Active → Expired
   ↓         ↓        ↓
count=0   count++   cleanup
```

## 2. UserBackground

**Purpose**: Stores user's software and hardware experience for personalization.

```typescript
interface UserBackground {
  user_id: number;                    // Foreign key to User
  software_experience: 'Beginner' | 'Intermediate' | 'Advanced';
  hardware_expertise: 'None' | 'Arduino' | 'ROS-Pro';
  years_of_experience: number;       // 0-50 validated range
  programming_languages: string[];    // Preferred languages (future enhancement)
  created_at: Date;                  // When background info was collected
  updated_at: Date;                  // Last update timestamp
}
```

**Validation Rules**:
- `years_of_experience`: Must be between 0 and 50
- `software_experience`: Required enum value
- `hardware_expertise`: Required enum value

**Relationships**:
- One-to-one with User (user_id is primary key)

## 3. PersistentSession

**Purpose**: Maintains user authentication state across browser sessions.

```typescript
interface PersistentSession {
  id: number;              // Primary key
  user_id: number;          // Foreign key to User
  token_id: string;         // JWT token identifier (jti)
  expires_at: Date;         // Token expiration time
  created_at: Date;         // Session creation
  last_used: Date;          // Last activity timestamp
  is_active: boolean;       // Session validity flag
}
```

**Validation Rules**:
- `expires_at`: Must be in the future
- `token_id`: Must be unique (JWT jti claim)

## 4. Enhanced User Model

**Purpose**: Extended user model with authentication improvements.

```typescript
interface User {
  id: number;               // Primary key
  email: string;            // Unique email address
  name: string;             // Display name
  password_hash: string;    // BCrypt hash
  email_verified: boolean;  // Verification status
  is_active: boolean;       // Account status
  created_at: Date;         // Registration date
  updated_at: Date;         // Last update
  last_login?: Date;        // Last successful login
}
```

**Relationships**:
- One-to-one with UserBackground
- One-to-many with PersistentSession

## Database Schema (SQLAlchemy)

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    background = relationship("UserBackground", back_populates="user", uselist=False)
    sessions = relationship("PersistentSession", back_populates="user")

class UserBackground(Base):
    __tablename__ = "user_backgrounds"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    software_experience = Column(Enum('Beginner', 'Intermediate', 'Advanced'), nullable=False)
    hardware_expertise = Column(Enum('None', 'Arduino', 'ROS-Pro'), nullable=False)
    years_of_experience = Column(Integer, CheckConstraint('0 <= years_of_experience <= 50'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="background")

class AnonymousSession(Base):
    __tablename__ = "anonymous_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    fingerprint = Column(String(64), index=True)

class PersistentSession(Base):
    __tablename__ = "persistent_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_id = Column(String(36), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
```

## Frontend Types

```typescript
// Session Management
interface GuestSession {
  id: string;
  messageCount: number;
  expiresAt: Date;
  exists: boolean;
}

interface AuthSession {
  token: string;
  user: {
    id: number;
    email: string;
    name: string;
    emailVerified: boolean;
  };
  expiresAt: Date;
}

// User Registration
interface RegistrationData {
  email: string;
  password: string;
  name: string;
  softwareExperience: 'Beginner' | 'Intermediate' | 'Advanced';
  hardwareExpertise: 'None' | 'Arduino' | 'ROS-Pro';
  yearsOfExperience: number;
}

// User Background
interface UserBackground {
  userId: number;
  softwareExperience: string;
  hardwareExpertise: string;
  yearsOfExperience: number;
  programmingLanguages?: string[];
}
```

## Data Flow

### Guest Session Flow
1. User sends first message → Create AnonymousSession with UUID
2. Store session ID in localStorage
3. Increment message_count on each message
4. On page refresh → Fetch session by ID
5. If localStorage fails → Use fingerprint to recover session

### Authentication Flow
1. User registers → Create User + UserBackground records
2. Generate JWT with 15-minute expiration
3. Create refresh token with 7-day expiration
4. Store refresh token in HTTP-only cookie
5. Auto-refresh token when 5 minutes from expiration

### Session Migration
1. Guest registers → Link AnonymousSession to User ID
2. Transfer chat history to User account
3. Create UserBackground from registration data
4. Activate PersistentSession tracking

## Security Considerations

1. **Anonymous Sessions**:
   - No personal data stored
   - Automatic cleanup after 24 hours
   - IP-based rate limiting

2. **Persistent Sessions**:
   - HTTP-only cookies for tokens
   - SameSite protection
   - Automatic refresh to prevent expiration

3. **User Background**:
   - Optional data collection
   - Clear privacy policy
   - User consent during registration

## Performance Optimizations

1. **Session Storage**:
   - Use in-memory cache for active sessions
   - Batch cleanup for expired sessions
   - Index on frequently queried fields

2. **Token Management**:
   - Refresh tokens in background
   - Queue multiple refresh attempts
   - Use efficient JWT libraries

3. **Database Queries**:
   - Use indexes on foreign keys
   - Limit query results for pagination
   - Implement connection pooling