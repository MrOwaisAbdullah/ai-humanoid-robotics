"""
Pydantic schemas for personalization-related data structures.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator

from .auth import BaseSchema


class PersonalizationType(str, Enum):
    """Types of content personalization available."""
    TECHNICAL_DEPTH = "technical_depth"
    EXAMPLE_RELEVANCE = "example_relevance"
    LEARNING_PATH = "learning_path"
    FULL_PERSONALIZATION = "full_personalization"


class ContentSegment(BaseSchema):
    """Schema for a content segment."""
    id: str
    content: str
    word_count: int
    order: int


class PersonalizationRequest(BaseSchema):
    """Schema for personalization request."""
    content: str = Field(..., min_length=100, max_length=50000, description="Content to personalize")
    title: Optional[str] = Field(None, max_length=200, description="Content title for context")
    personalization_type: PersonalizationType = PersonalizationType.FULL_PERSONALIZATION
    target_audience: Optional[str] = Field(None, max_length=100, description="Target audience hint")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")
    avoid_topics: Optional[List[str]] = Field(None, description="Topics to avoid")
    preferred_length: Optional[str] = Field("same", description="Preferred output length: 'shorter', 'same', or 'longer'")
    include_examples: bool = True
    include_analogies: bool = True

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        # Check for reasonable word count
        word_count = len(v.split())
        if word_count < 50:
            raise ValueError('Content must have at least 50 words')
        if word_count > 10000:
            raise ValueError('Content cannot exceed 10,000 words')
        return v

    @validator('focus_areas', 'avoid_topics')
    def validate_topic_lists(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError('Cannot specify more than 10 topics')
        return v

    @validator('preferred_length')
    def validate_preferred_length(cls, v):
        if v not in ['shorter', 'same', 'longer']:
            raise ValueError('Preferred length must be one of: shorter, same, longer')
        return v


class PersonalizationAdaptation(BaseSchema):
    """Schema for a single adaptation made."""
    type: str = Field(..., description="Type of adaptation")
    original: str = Field(..., description="Original text or concept")
    adapted: str = Field(..., description="Adapted text or concept")
    reasoning: Optional[str] = Field(None, description="Reasoning for the adaptation")


class PersonalizationResponse(BaseSchema):
    """Schema for personalization response."""
    id: str
    original_content: str
    personalized_content: str
    adaptations_made: List[PersonalizationAdaptation]
    processing_time_ms: int
    user_profile_summary: Dict[str, Any]
    content_segments: List[ContentSegment]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PersonalizationError(BaseSchema):
    """Schema for personalization error response."""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    retry_possible: bool = False
    retry_after_seconds: Optional[int] = None


class UserProfileSummary(BaseSchema):
    """Schema for user profile summary used in personalization."""
    experience_level: str
    years_experience: int
    software_background: Optional[str] = None
    hardware_expertise: Optional[str] = None
    primary_interests: List[str] = []
    preferred_learning_style: Optional[str] = None
    technical_depth_preference: str = "intermediate"


class SavedPersonalizationBase(BaseSchema):
    """Base schema for saved personalization."""
    title: str = Field(..., max_length=200)
    original_content_hash: str = Field(..., description="Hash of original content for deduplication")
    personalization_type: PersonalizationType
    tags: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError('Cannot have more than 20 tags')
        return v or []


class SavedPersonalizationCreate(SavedPersonalizationBase):
    """Schema for creating saved personalization."""
    pass


class SavedPersonalizationUpdate(BaseSchema):
    """Schema for updating saved personalization."""
    title: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=1000)


class SavedPersonalizationResponse(SavedPersonalizationBase):
    """Schema for saved personalization response."""
    id: str
    user_id: str
    personalization_id: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_favorite: bool = False
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PersonalizationRating(BaseSchema):
    """Schema for rating a saved personalization."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    feedback: Optional[str] = Field(None, max_length=500)


class PersonalizationStats(BaseSchema):
    """Schema for user personalization statistics."""
    total_personalizations: int
    saved_personalizations: int
    average_rating: Optional[float] = None
    favorite_count: int
    total_processing_time_ms: int
    average_processing_time_ms: float
    most_used_personalization_type: Optional[PersonalizationType] = None
    created_at: datetime


class PersonalizationListResponse(BaseSchema):
    """Schema for paginated list of saved personalizations."""
    items: List[SavedPersonalizationResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ContentExtractionRequest(BaseSchema):
    """Schema for extracting content from a page."""
    url: Optional[str] = None
    selector: Optional[str] = Field(None, description="CSS selector for content extraction")
    exclude_selectors: Optional[List[str]] = Field(None, description="CSS selectors to exclude")
    max_length: Optional[int] = Field(None, ge=100, le=50000, description="Maximum content length")


class ContentExtractionResponse(BaseSchema):
    """Schema for extracted content response."""
    content: str
    title: Optional[str] = None
    word_count: int
    source_url: Optional[str] = None
    extraction_method: str
    metadata: Dict[str, Any]


# Personalization Context schemas for the frontend
class PersonalizationContext(BaseSchema):
    """Schema for personalization context state."""
    isPersonalizing: bool = False
    currentRequest: Optional[PersonalizationRequest] = None
    currentResponse: Optional[PersonalizationResponse] = None
    error: Optional[PersonalizationError] = None
    savedItems: List[SavedPersonalizationResponse] = []
    userStats: Optional[PersonalizationStats] = None


class PersonalizationModalState(BaseSchema):
    """Schema for personalization modal UI state."""
    isOpen: bool = False
    isLoading: bool = False
    step: "request" | "processing" | "result" | "error" = "request"
    copiedToClipboard: bool = False
    showSaveDialog: bool = False


# Batch personalization schemas (for future use)
class BatchPersonalizationRequest(BaseSchema):
    """Schema for batch personalization request."""
    contents: List[PersonalizationRequest]
    max_concurrent: int = Field(3, ge=1, le=10)

    @validator('contents')
    def validate_contents(cls, v):
        if len(v) > 50:
            raise ValueError('Cannot process more than 50 items in a batch')
        return v


class BatchPersonalizationResponse(BaseSchema):
    """Schema for batch personalization response."""
    batch_id: str
    total_items: int
    completed_items: int
    failed_items: int
    results: List[PersonalizationResponse]
    errors: List[PersonalizationError]
    processing_time_ms: int