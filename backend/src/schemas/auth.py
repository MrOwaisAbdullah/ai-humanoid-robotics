"""
Pydantic schemas for authentication-related data structures.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# User schemas
class UserBase(BaseSchema):
    """Base user schema."""
    email: EmailStr
    name: Optional[str] = None
    email_verified: bool = False


class UserCreate(BaseSchema):
    """Schema for creating a user."""
    email: EmailStr
    password: str
    name: Optional[str] = None

    # Optional background fields for knowledge collection
    software_experience: Optional[str] = None
    hardware_expertise: Optional[str] = None
    years_of_experience: Optional[int] = None
    primary_interest: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('software_experience')
    def validate_software_experience(cls, v):
        if v is not None and v not in ['Beginner', 'Intermediate', 'Advanced']:
            raise ValueError('Software experience must be one of: Beginner, Intermediate, Advanced')
        return v

    @validator('hardware_expertise')
    def validate_hardware_expertise(cls, v):
        if v is not None and v not in ['None', 'Arduino', 'ROS-Pro']:
            raise ValueError('Hardware expertise must be one of: None, Arduino, ROS-Pro')
        return v

    @validator('years_of_experience')
    def validate_years_of_experience(cls, v):
        if v is not None and (v < 0 or v > 50):
            raise ValueError('Years of experience must be between 0 and 50')
        return v

    @validator('primary_interest')
    def validate_primary_interest(cls, v):
        if v is not None and v not in [
            'Computer Vision', 'Machine Learning', 'Control Systems',
            'Path Planning', 'State Estimation', 'Sensors & Perception',
            'Hardware Integration', 'Human-Robot Interaction', 'All of the Above'
        ]:
            raise ValueError('Primary interest must be one of: Computer Vision, Machine Learning, Control Systems, Path Planning, State Estimation, Sensors & Perception, Hardware Integration, Human-Robot Interaction, or All of the Above')
        return v


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseSchema):
    """Schema for user response."""
    id: str
    email: str
    name: Optional[str]
    email_verified: bool
    created_at: datetime
    updated_at: datetime


# Authentication schemas
class Token(BaseSchema):
    """Token schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseSchema):
    """Token data schema."""
    user_id: Optional[str] = None


class LoginRequest(BaseSchema):
    """Schema for login request."""
    username: str = Field(..., description="Email address (OAuth2PasswordRequestForm uses 'username' field)")
    password: str


class EmailLoginRequest(BaseSchema):
    """Schema for email-based login request."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class LoginResponse(BaseSchema):
    """Schema for login response."""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse
    migrated_sessions: Optional[int] = 0
    migrated_messages: Optional[int] = 0


# User background schemas
class ExperienceLevel(str, Enum):
    """Experience level enum."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class HardwareExpertise(BaseSchema):
    """Hardware expertise schema."""
    cpu: str
    gpu: str
    networking: str


class UserBackgroundBase(BaseSchema):
    """Base user background schema."""
    experience_level: ExperienceLevel
    years_experience: int = Field(..., ge=0, le=50)
    preferred_languages: List[str] = Field(default_factory=list)
    hardware_expertise: HardwareExpertise


class UserBackgroundCreate(UserBackgroundBase):
    """Schema for creating user background."""
    pass


class UserBackgroundUpdate(BaseSchema):
    """Schema for updating user background."""
    experience_level: Optional[ExperienceLevel] = None
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    preferred_languages: Optional[List[str]] = None
    hardware_expertise: Optional[HardwareExpertise] = None


class UserBackgroundResponse(UserBackgroundBase):
    """Schema for user background response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


# Onboarding schemas
class OnboardingQuestion(str, Enum):
    """Onboarding question keys."""
    EXPERIENCE_LEVEL = "experience_level_selection"
    YEARS_OF_EXPERIENCE = "years_of_experience"
    PREFERRED_LANGUAGES = "preferred_languages"
    CPU_EXPERTISE = "cpu_expertise"
    GPU_EXPERTISE = "gpu_expertise"
    NETWORKING_EXPERTISE = "networking_expertise"


class OnboardingResponseBase(BaseSchema):
    """Base onboarding response schema."""
    question_key: OnboardingQuestion
    response_value: Any


class OnboardingResponseCreate(OnboardingResponseBase):
    """Schema for creating onboarding response."""
    pass


class OnboardingResponseResponse(OnboardingResponseBase):
    """Schema for onboarding response."""
    id: str
    user_id: str
    created_at: datetime


class OnboardingBatch(BaseSchema):
    """Schema for batch onboarding submission."""
    responses: List[OnboardingResponseCreate]


# Password reset schemas
class PasswordResetRequest(BaseSchema):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseSchema):
    """Schema for password reset confirmation."""
    token: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


# User preferences schemas
class Theme(str, Enum):
    """Theme options."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class NotificationSettings(BaseSchema):
    """Notification settings schema."""
    email_responses: bool = False
    browser_notifications: bool = True
    marketing_emails: bool = False


class UserPreferencesBase(BaseSchema):
    """Base user preferences schema."""
    theme: Theme = Theme.AUTO
    language: str = "en"
    notification_settings: NotificationSettings


class UserPreferencesUpdate(BaseSchema):
    """Schema for updating user preferences."""
    theme: Optional[Theme] = None
    language: Optional[str] = None
    notification_settings: Optional[NotificationSettings] = None


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


# Chat schemas
class ChatMessageRole(str, Enum):
    """Chat message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessageBase(BaseSchema):
    """Base chat message schema."""
    role: ChatMessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageCreate(ChatMessageBase):
    """Schema for creating chat message."""
    chat_session_id: str


class ChatMessageResponse(ChatMessageBase):
    """Schema for chat message response."""
    id: str
    chat_session_id: str
    created_at: datetime


class ChatSessionBase(BaseSchema):
    """Base chat session schema."""
    title: str = "New Chat"


class ChatSessionCreate(ChatSessionBase):
    """Schema for creating chat session."""
    user_id: Optional[str] = None
    anonymous_session_id: Optional[str] = None


class ChatSessionResponse(ChatSessionBase):
    """Schema for chat session response."""
    id: str
    user_id: Optional[str]
    anonymous_session_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []


# Anonymous session schemas
class AnonymousSessionResponse(BaseSchema):
    """Schema for anonymous session response."""
    id: str
    message_count: int
    remaining_messages: int
    created_at: datetime
    last_activity: datetime
    is_expired: bool
    can_send_message: bool


# API response schemas
class SuccessResponse(BaseSchema):
    """Success response schema."""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseSchema):
    """Error response schema."""
    success: bool = False
    error: str
    detail: Optional[str] = None


# Health check schemas
class HealthResponse(BaseSchema):
    """Health check response schema."""
    status: str
    timestamp: datetime
    version: Optional[str] = None


# Alias for backward compatibility
User = UserResponse