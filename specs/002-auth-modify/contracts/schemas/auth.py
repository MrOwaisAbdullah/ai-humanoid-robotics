"""
Pydantic schemas for authentication API
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class RegisterRequest(BaseModel):
    """Schema for user registration request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$',
        description="Password (min 8 chars, letters and numbers)"
    )
    name: Optional[str] = Field(None, max_length=100, description="Optional display name")


class LoginRequest(BaseModel):
    """Schema for user login request"""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Schema for authentication response"""
    user: 'UserResponse'
    requires_onboarding: bool = Field(description="Whether user needs to complete onboarding")


class UserResponse(BaseModel):
    """Schema for user information response"""
    id: UUID
    email: EmailStr
    name: Optional[str]
    email_verified: bool
    created_at: datetime
    has_background: bool = Field(description="Whether user has completed onboarding")

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class ValidateResetTokenRequest(BaseModel):
    """Schema for validating reset token"""
    token: str = Field(description="Password reset token")


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password"""
    token: str = Field(description="Password reset token")
    password: str = Field(
        ...,
        min_length=8,
        regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$'
    )


class HardwareExpertise(BaseModel):
    """Schema for hardware expertise levels"""
    cpu: str = Field(..., regex=r'^(none|basic|intermediate|advanced)$')
    gpu: str = Field(..., regex=r'^(none|basic|intermediate|advanced)$')
    networking: str = Field(..., regex=r'^(none|basic|intermediate|advanced)$')


class OnboardingRequest(BaseModel):
    """Schema for onboarding data submission"""
    experience_level: Optional[str] = Field(None, regex=r'^(beginner|intermediate|advanced)$')
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    preferred_languages: Optional[List[str]] = Field(
        None,
        max_items=10,
        items=Field(regex=r'^(python|javascript|java|cpp|rust|go|typescript|php|ruby|swift|kotlin|other)$')
    )
    hardware_expertise: Optional[HardwareExpertise] = None


class UserBackgroundResponse(BaseModel):
    """Schema for user background response"""
    experience_level: Optional[str]
    years_experience: Optional[int]
    preferred_languages: Optional[List[str]]
    hardware_expertise: Optional[HardwareExpertise]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateBackgroundRequest(BaseModel):
    """Schema for updating user background"""
    experience_level: Optional[str] = Field(None, regex=r'^(beginner|intermediate|advanced)$')
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    preferred_languages: Optional[List[str]] = Field(
        None,
        max_items=10,
        items=Field(regex=r'^(python|javascript|java|cpp|rust|go|typescript|php|ruby|swift|kotlin|other)$')
    )
    hardware_expertise: Optional[HardwareExpertise] = None


class NotificationSettings(BaseModel):
    """Schema for notification preferences"""
    email_responses: bool = False
    browser_notifications: bool = True
    marketing_emails: bool = False


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences response"""
    theme: str = Field(regex=r'^(light|dark|auto)$')
    language: str = Field(regex=r'^[a-z]{2}(-[A-Z]{2})?$')
    notification_settings: NotificationSettings

    class Config:
        from_attributes = True


class UpdatePreferencesRequest(BaseModel):
    """Schema for updating user preferences"""
    theme: Optional[str] = Field(None, regex=r'^(light|dark|auto)$')
    language: Optional[str] = Field(None, regex=r'^[a-z]{2}(-[A-Z]{2})?$')
    notification_settings: Optional[NotificationSettings] = None


class Error(BaseModel):
    """Schema for error responses"""
    error: str = Field(description="Error message")
    code: str = Field(description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")


# Forward references for AuthResponse
AuthResponse.model_rebuild()