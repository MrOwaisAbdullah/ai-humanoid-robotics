# Data Model: Content Personalization Feature

## 1. Core Entities

### 1.1 PersonalizationRequest
Represents a request to personalize content for a user.

```python
class PersonalizationRequest(BaseModel):
    """Request model for content personalization"""

    # Input data
    content: str = Field(..., min_length=100, max_length=5000,
                         description="Original content to personalize")
    content_hash: str = Field(..., description="SHA-256 hash of original content")
    context: Optional[str] = Field(None, description="Additional context about the content")

    # User information (populated from auth)
    user_id: UUID = Field(..., description="User requesting personalization")
    user_background: UserBackground = Field(..., description="User's technical background")

    # Personalization options
    target_length: int = Field(default=2000, ge=500, le=3000,
                               description="Target word count for personalized content")
    save_result: bool = Field(default=False, description="Whether to save the result")

    class Config:
        schema_extra = {
            "example": {
                "content": "ROS nodes are the fundamental computational units...",
                "context": "Chapter about ROS fundamentals",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_background": {
                    "experience_level": "intermediate",
                    "primary_expertise": "software",
                    "hardware_expertise": "none"
                },
                "target_length": 2000,
                "save_result": False
            }
        }
```

### 1.2 PersonalizationResult
Represents the result of content personalization.

```python
class PersonalizationResult(BaseModel):
    """Result model for personalized content"""

    # Core result
    personalized_content: str = Field(..., description="Personalized version of content")
    adaptations_made: List[str] = Field(default_factory=list,
                                      description="List of adaptations applied")
    complexity_score: Literal["basic", "intermediate", "advanced"] = Field(
        ..., description="Complexity level of personalized content")

    # Metadata
    original_length: int = Field(..., description="Word count of original content")
    personalized_length: int = Field(..., description="Word count of personalized content")
    processing_time: float = Field(..., description="Time taken to process (seconds)")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")

    # Quality metrics
    relevance_score: Optional[float] = Field(None, ge=0, le=1,
                                           description="Relevance to user profile")

    class Config:
        schema_extra = {
            "example": {
                "personalized_content": "For a software engineer, think of ROS nodes...",
                "adaptations_made": [
                    "Added Python code examples",
                    "Included software architecture analogies",
                    "Simplified hardware terminology"
                ],
                "complexity_score": "intermediate",
                "original_length": 1850,
                "personalized_length": 1920,
                "processing_time": 3.45,
                "tokens_used": 850,
                "relevance_score": 0.92
            }
        }
```

### 1.3 SavedPersonalization
Represents a saved personalized content entry for a user.

```python
class SavedPersonalization(Base):
    """Database model for saved personalized content"""

    __tablename__ = "saved_personalizations"

    # Primary keys
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Content tracking
    original_content_hash = Column(String(64), nullable=False, index=True)
    content_url = Column(String(512), nullable=False)  # URL to original content
    content_title = Column(String(200), nullable=False)

    # Personalization data
    personalized_content = Column(Text, nullable=False)
    personalization_metadata = Column(JSON, nullable=False)
    adaptations_applied = Column(JSON, nullable=False)

    # User feedback
    user_rating = Column(Integer, CheckConstraint('user_rating >= 1 AND user_rating <= 5'))
    user_feedback = Column(Text)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_accessed = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="saved_personalizations")

    # Constraints
    __table_args__ = (
        Index('idx_user_content_hash', 'user_id', 'original_content_hash', unique=True),
        Index('idx_user_created', 'user_id', 'created_at'),
    )
```

## 2. Extended User Models

### 2.1 UserBackground Extensions
Additional fields for better personalization.

```python
class UserBackgroundExtended(UserBackground):
    """Extended user background model for personalization"""

    # Learning preferences
    learning_style = Column(Enum(LearningStyle), default=LearningStyle.MIXED)
    preferred_explanation_depth = Column(Enum(ExplanationDepth),
                                        default=ExplanationDepth.MEDIUM)
    analogy_preference = Column(Enum(AnalogyType), default=AnalogyType.MIXED)

    # Content preferences
    code_example_preference = Column(Boolean, default=True)
    practical_application_focus = Column(Boolean, default=True)
    theoretical_background_preference = Column(Boolean, default=False)

    # Expertise mapping (structured)
    domain_expertise = Column(JSON, default=dict)  # {domain: level}
    technology_stack = Column(JSON, default=list)  # Familiar technologies

    # Personalization history
    total_personalizations = Column(Integer, default=0)
    average_rating_given = Column(Float, default=0)

    class LearningStyle(Enum):
        VISUAL = "visual"
        TEXTUAL = "textual"
        CODE_FOCUSED = "code_focused"
        MIXED = "mixed"

    class ExplanationDepth(Enum):
        SHALLOW = "shallow"      # Overview only
        MEDIUM = "medium"        # Balanced depth
        DEEP = "deep"           # Detailed explanations

    class AnalogyType(Enum):
        SOFTWARE = "software"    # Software engineering analogies
        HARDWARE = "hardware"    # Hardware/electrical analogies
        REAL_WORLD = "real_world"  # Everyday analogies
        MIXED = "mixed"         # Variety of analogies
```

## 3. API Contract Models

### 3.1 Request/Response DTOs

```python
# Personalization API
class PersonalizeRequest(BaseModel):
    content: str = Field(..., min_length=100, max_length=5000)
    context: Optional[str] = None
    target_length: int = Field(default=2000, ge=500, le=3000)
    save_result: bool = Field(default=False)

class PersonalizeResponse(BaseModel):
    success: bool
    data: Optional[PersonalizationResult] = None
    error: Optional[str] = None

# Saved Personalizations API
class ListSavedRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=50)
    sort_by: Literal["created_at", "last_accessed", "user_rating"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"

class ListSavedResponse(BaseModel):
    success: bool
    data: List[SavedPersonalizationResponse]
    pagination: PaginationInfo
    error: Optional[str] = None
```

## 4. State Management

### 4.1 Frontend State Models

```typescript
// Personalization state
interface PersonalizationState {
  // Current personalization
  isProcessing: boolean;
  currentResult: PersonalizationResult | null;

  // Saved personalizations
  savedItems: SavedPersonalization[];
  savedItemsLoading: boolean;

  // User preferences
  preferences: PersonalizationPreferences;

  // Error state
  error: string | null;
}

interface PersonalizationPreferences {
  autoSave: boolean;
  defaultTargetLength: number;
  showCodeExamples: boolean;
  preferredDepth: "shallow" | "medium" | "deep";
}

// Component props
interface PersonalizeButtonProps {
  content: string;
  context?: string;
  onComplete?: (result: PersonalizationResult) => void;
  onError?: (error: string) => void;
}

interface PersonalizationModalProps {
  result: PersonalizationResult;
  isOpen: boolean;
  onClose: () => void;
  onSave?: () => void;
}
```

## 5. Validation Rules

### 5.1 Input Validation
- Content length: 100-5000 characters
- Target length: 500-3000 words
- Content hash validation for deduplication
- User authentication required

### 5.2 Output Validation
- Personalized content must be different from original
- Minimum adaptations: 1
- Maximum processing time: 30 seconds
- Content similarity score: 0.3-0.9

## 6. Database Schema Updates

### 6.1 New Tables

```sql
-- Saved personalizations
CREATE TABLE saved_personalizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_content_hash VARCHAR(64) NOT NULL,
    content_url VARCHAR(512) NOT NULL,
    content_title VARCHAR(200) NOT NULL,
    personalized_content TEXT NOT NULL,
    personalization_metadata JSONB NOT NULL,
    adaptations_applied JSONB NOT NULL,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_accessed TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, original_content_hash)
);

-- Indexes for performance
CREATE INDEX idx_saved_personalizations_user_hash
    ON saved_personalizations(user_id, original_content_hash);
CREATE INDEX idx_saved_personalizations_user_created
    ON saved_personalizations(user_id, created_at DESC);
CREATE INDEX idx_saved_personalizations_hash
    ON saved_personalizations(original_content_hash);

-- Add to users table (tracking)
ALTER TABLE users ADD COLUMN total_personalizations INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN average_personalization_rating FLOAT DEFAULT 0;
```

### 6.2 UserBackground Extensions

```sql
-- Add personalization preferences to user_backgrounds
ALTER TABLE user_backgrounds ADD COLUMN learning_style VARCHAR(20) DEFAULT 'mixed';
ALTER TABLE user_backgrounds ADD COLUMN preferred_explanation_depth VARCHAR(20) DEFAULT 'medium';
ALTER TABLE user_backgrounds ADD COLUMN analogy_preference VARCHAR(20) DEFAULT 'mixed';
ALTER TABLE user_backgrounds ADD COLUMN code_example_preference BOOLEAN DEFAULT TRUE;
ALTER TABLE user_backgrounds ADD COLUMN practical_application_focus BOOLEAN DEFAULT TRUE;
ALTER TABLE user_backgrounds ADD COLUMN domain_expertise JSONB DEFAULT '{}';
ALTER TABLE user_backgrounds ADD COLUMN technology_stack JSONB DEFAULT '[]';
```

## 7. Caching Strategy

### 7.1 Redis Cache Keys
- `personalization:{content_hash}:{user_background_hash}` - Cached result
- `user_background:{user_id}` - User background cache
- `personalization_stats:daily:{date}` - Daily statistics

### 7.2 Cache TTL
- Personalization results: 24 hours
- User background: 1 hour
- Statistics: 24 hours