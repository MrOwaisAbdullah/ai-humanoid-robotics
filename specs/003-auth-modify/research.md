# Authentication Modification: Research Findings

**Created**: 2025-01-08
**Phase**: 0 - Research & Technical Decisions

## Email Authentication with FastAPI

### Decision
Use passlib with bcrypt for password hashing, python-jose for JWT tokens, and FastAPI's security utilities.

### Rationale
- **passlib**: Industry standard for password hashing, supports multiple algorithms
- **bcrypt**: Proven, slow hashing algorithm resistant to brute force attacks
- **python-jose**: Lightweight JWT library compatible with FastAPI
- **FastAPI Security**: Built-in utilities for OAuth2Bearer, HTTPBearer, etc.

### Implementation Pattern
```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Security, HTTPBearer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)
```

### Alternatives Considered
- **django-allauth**: Too heavyweight for FastAPI
- **authlib**: More complex than needed for email/password only
- **custom implementation**: Risk of security vulnerabilities

## Onboarding Flow Design

### Decision
Multi-step modal with progress indicator, allowing users to save and continue later.

### Rationale
- Reduces cognitive load by breaking into manageable chunks
- Improves completion rates with progress visualization
- Allows partial completion without data loss

### Flow Structure
1. **Account Creation** (already in modal)
   - Email and password
   - Terms acceptance

2. **Experience Level** (Step 1)
   - Single selection: Beginner, Intermediate, Advanced
   - Years of experience (0-1, 2-5, 6-10, 10+)

3. **Technical Background** (Step 2)
   - Preferred programming languages (multi-select)
   - Familiar frameworks/libraries
   - Development environment

4. **Hardware Knowledge** (Step 3)
   - CPU architecture familiarity
   - GPU experience level
   - Cloud/IaaS exposure

### UI Pattern
```typescript
interface OnboardingStep {
  id: string;
  title: string;
  component: React.ComponentType;
  required: boolean;
}
```

### Alternatives Considered
- **Single long form**: Higher abandonment rate
- **Separate page flow**: Disrupts user journey
- **Progressive profiling**: Collect data over time (slower personalization)

## Session Management Strategy

### Decision
JWT with 7-day sliding expiration stored in HTTP-only cookies.

### Rationale
- **Sliding expiration**: Extends session on activity, better UX
- **HTTP-only cookies**: Prevents XSS attacks accessing tokens
- **7-day duration**: Balanced security and convenience
- **JWT**: Stateless, scalable, works with existing infrastructure

### Implementation Details
```python
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### Security Considerations
- CSRF token required for state-changing operations
- Secure cookie flags: HttpOnly, Secure, SameSite=Strict
- Short-lived access tokens (1 hour) with refresh mechanism

### Alternatives Considered
- **Redis session storage**: Adds infrastructure complexity
- **Local storage**: Vulnerable to XSS
- **Session cookies without JWT**: Harder to scale across services

## Anonymous Session Migration

### Decision
UUID-based temporary sessions with automatic migration on registration.

### Rationale
- **UUID**: Globally unique, no collisions
- **Temporary**: Stored separately from user data
- **Automatic**: Seamless upgrade experience
- **Limited history**: Only recent session migrated (10 messages)

### Migration Process
1. Anonymous user starts chat → generate anonymous_id
2. Store chat messages with anonymous_id
3. User registers → create account
4. Link anonymous_id to new user_id
5. Migrate last 10 messages to user's chat history
6. Clean up anonymous session after successful migration

### Implementation Pattern
```python
class AnonymousSession:
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_count: int = 0
    messages: List[ChatMessage] = []
    created_at: datetime
    last_activity: datetime

def migrate_anonymous_session(anonymous_id: str, user_id: str):
    # Get recent messages (max 10)
    messages = get_recent_anonymous_messages(anonymous_id, limit=10)

    # Create new chat session for user
    chat_session = ChatSession(
        user_id=user_id,
        title="Migrated from anonymous chat",
        messages=messages
    )

    # Save and cleanup
    save_chat_session(chat_session)
    cleanup_anonymous_session(anonymous_id)
```

### Edge Cases Handled
- Anonymous session expires before registration
- Multiple anonymous sessions from same IP/browser
- Registration failure (session remains anonymous)
- Duplicate anonymous IDs (extremely rare with UUID)

### Alternatives Considered
- **No migration**: Users lose chat history
- **Full history migration**: Privacy concerns, storage bloat
- **Opt-in migration**: Adds complexity, lower conversion

## Email Service Integration

### Decision
Use Python's built-in smtplib with SMTP for simplicity, configurable for production services.

### Rationale
- **Built-in**: No additional dependencies
- **Configurable**: Can swap to SendGrid/SES in production
- **Template-based**: HTML and text templates
- **Queue support**: Async sending with background tasks

### Implementation Pattern
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_password_reset_email(email: str, token: str):
    reset_link = f"{BASE_URL}/reset-password?token={token}"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset your password"
    message["From"] = EMAIL_FROM
    message["To"] = email

    # HTML template
    html = f"""
    <html>
      <body>
        <p>Click <a href="{reset_link}">here</a> to reset your password.</p>
        <p>This link expires in 24 hours.</p>
      </body>
    </html>
    """

    message.attach(MIMEText(html, "html"))

    # Send asynchronously
    await send_email_async(message)
```

### Security Features
- Time-limited tokens (24 hours)
- Single-use tokens (invalidate after use)
- Rate limiting on reset requests
- No password hints in emails

### Production Considerations
- Use transactional email service (SendGrid, AWS SES)
- Implement email verification loops
- Handle bounces and spam complaints
- DKIM/SPF record configuration

### Alternatives Considered
- **Third-party service from start**: Adds cost for development
- **In-app reset only**: Less secure, poor UX
- **SMS reset**: Additional cost, privacy concerns

## Database Schema Considerations

### Decision
Extend existing SQLite schema with new tables, maintain backward compatibility.

### Rationale
- **SQLite**: Simple, no additional infrastructure
- **Backward compatible**: Existing data unaffected
- **Migration strategy**: Alembic handles schema changes
- **Indexing strategy**: Optimize for common queries

### New Tables Required
1. **UserBackground**: Stores onboarding responses
2. **PasswordResetToken**: Temporary reset tokens
3. **AnonymousSession**: Temporary chat sessions

### Indexing Strategy
```sql
-- User sessions lookup
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token);

-- User background queries for personalization
CREATE INDEX idx_user_background_user_id ON user_background(user_id);

-- Anonymous session cleanup
CREATE INDEX idx_anonymous_sessions_created ON anonymous_sessions(created_at);
```

### Migration Strategy
- Use Alembic for version control
- Backward compatible changes only
- Data migration scripts prepared
- Rollback procedures documented

### Alternatives Considered
- **PostgreSQL**: Overkill for current scale
- **NoSQL**: Not needed for structured user data
- **Separate auth database**: Adds complexity without benefit

## Security Best Practices

### Password Policy
- Minimum 8 characters
- Must include letters and numbers
- Optional special characters for stronger passwords
- Check against common password lists

### Session Security
- HTTP-only cookies
- Secure flag in production
- SameSite=Strict or Lax
- CSRF tokens for state changes

### API Security
- Rate limiting on auth endpoints
- Account lockout after failed attempts
- Request logging for monitoring
- Input validation and sanitization

### Data Protection
- Encrypt sensitive data at rest
- Hash passwords with salt
- Minimal data collection
- Clear data retention policy