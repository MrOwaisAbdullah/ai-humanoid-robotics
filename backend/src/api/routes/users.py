"""
User management API routes.

This module provides endpoints for user profile management,
onboarding, and preferences.
"""

from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

# Import async database session
from src.core.database import get_async_db

# Import User model from new location
from src.models.user import User

# Import other models from old location (they're still there)
from src.models.auth import UserBackground, OnboardingResponse, UserPreferences

# Import schemas (these might need updating too)
from src.schemas.auth import (
    UserResponse as UserSchema,
    UserBackgroundResponse,
    UserBackgroundCreate,
    UserBackgroundUpdate,
    OnboardingResponseResponse as OnboardingResponseSchema,
    OnboardingResponseCreate,
    OnboardingBatch,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    SuccessResponse
)

# Remove the old dependency - we'll use middleware's user
# from src.security.dependencies import get_current_active_user

router = APIRouter(tags=["users"])


async def get_current_user(request: Request) -> User:
    """
    Get the current authenticated user from middleware.
    The middleware has already validated the token and set request.state.user.
    """
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.user


@router.get("/me", response_model=UserSchema)
async def get_user_profile(
    request: Request
) -> Any:
    """
    Get current user's profile information.

    Args:
        request: FastAPI request object (user from middleware)

    Returns:
        User profile data
    """
    user = await get_current_user(request)
    return user


@router.put("/me", response_model=UserSchema)
async def update_user_profile(
    user_update: dict,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Update current user's profile information.

    Args:
        user_update: User data to update
        request: FastAPI request object (user from middleware)
        db: Database session

    Returns:
        Updated user data
    """
    user = await get_current_user(request)

    # Get user from database (using async)
    result = await db.execute(
        select(User).where(User.id == user.id)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update allowed fields
    if "name" in user_update and user_update["name"] is not None:
        db_user.full_name = user_update["name"]

    if "email" in user_update and user_update["email"] is not None:
        # Check if email is already taken by another user
        result = await db.execute(
            select(User).where(
                User.email == user_update["email"],
                User.id != user.id
            )
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken by another user"
            )
        db_user.email = user_update["email"]
        db_user.email_verified = False  # Require re-verification

    db_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.get("/background", response_model=UserBackgroundResponse)
async def get_user_background(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Get user's background information.

    Args:
        request: FastAPI request object (user from middleware)
        db: Database session

    Returns:
        User background data
    """
    user = await get_current_user(request)

    # Query using async
    result = await db.execute(
        select(UserBackground).where(UserBackground.user_id == user.id)
    )
    background = result.scalar_one_or_none()

    if not background:
        # Return default background
        return {
            "id": "",
            "user_id": user.id,
            "experience_level": "beginner",
            "years_experience": 0,
            "preferred_languages": [],
            "hardware_expertise": {"cpu": "none", "gpu": "none", "networking": "none"},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    # Convert background to dict to handle enum values properly
    return {
        "id": background.id,
        "user_id": background.user_id,
        "experience_level": background.experience_level.value.lower() if background.experience_level else "beginner",
        "years_experience": background.years_of_experience,
        "preferred_languages": background.preferred_languages or [],
        "hardware_expertise": background.hardware_expertise or {"cpu": "none", "gpu": "none", "networking": "none"},
        "created_at": background.created_at,
        "updated_at": background.updated_at
    }


@router.post("/background", response_model=UserBackgroundResponse)
async def create_or_update_user_background(
    background_data: UserBackgroundCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Create or update user's background information.

    Args:
        background_data: User background data
        request: FastAPI request object (user from middleware)
        db: Database session

    Returns:
        Created/updated user background data
    """
    user = await get_current_user(request)

    # Check if background exists (using async)
    result = await db.execute(
        select(UserBackground).where(UserBackground.user_id == user.id)
    )
    background = result.scalar_one_or_none()

    if background:
        # Update existing background
        if background_data.experience_level:
            # Normalize experience level
            exp_level = str(background_data.experience_level).lower()
            if exp_level == "beginner":
                background.experience_level = UserBackground.ExperienceLevel.BEGINNER
            elif exp_level == "intermediate":
                background.experience_level = UserBackground.ExperienceLevel.INTERMEDIATE
            elif exp_level == "advanced":
                background.experience_level = UserBackground.ExperienceLevel.ADVANCED
        background.years_of_experience = background_data.years_experience
        background.preferred_languages = background_data.preferred_languages
        background.hardware_expertise = background_data.hardware_expertise
        background.updated_at = datetime.utcnow()
    else:
        # Create new background
        exp_level_enum = UserBackground.ExperienceLevel.INTERMEDIATE
        if background_data.experience_level:
            exp_level = str(background_data.experience_level).lower()
            if exp_level == "beginner":
                exp_level_enum = UserBackground.ExperienceLevel.BEGINNER
            elif exp_level == "intermediate":
                exp_level_enum = UserBackground.ExperienceLevel.INTERMEDIATE
            elif exp_level == "advanced":
                exp_level_enum = UserBackground.ExperienceLevel.ADVANCED

        background = UserBackground(
            user_id=user.id,
            experience_level=exp_level_enum,
            years_of_experience=background_data.years_experience,
            preferred_languages=background_data.preferred_languages,
            hardware_expertise=background_data.hardware_expertise
        )
        db.add(background)

    await db.commit()
    await db.refresh(background)

    return background


@router.post("/onboarding", response_model=SuccessResponse)
async def submit_onboarding(
    onboarding_data: OnboardingBatch,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Submit onboarding responses.

    Args:
        onboarding_data: Batch of onboarding responses
        request: FastAPI request object (user from middleware)
        db: Database session

    Returns:
        Success response
    """
    user = await get_current_user(request)

    # Clear existing onboarding responses for this user (using async)
    await db.execute(
        select(OnboardingResponse).where(OnboardingResponse.user_id == user.id)
    )
    # Delete properly
    from sqlalchemy import delete
    await db.execute(
        delete(OnboardingResponse).where(OnboardingResponse.user_id == user.id)
    )

    # Add new responses
    for response_data in onboarding_data.responses:
        response = OnboardingResponse(
            user_id=user.id,
            question_key=response_data.question_key,
            response_value=response_data.response_value
        )
        db.add(response)

    await db.commit()

    # Optionally update user background based on responses
    background_responses = {
        resp.question_key: resp.response_value
        for resp in onboarding_data.responses
    }

    # Map onboarding responses to background fields
    background_update = {}
    if "experience_level_selection" in background_responses:
        # Normalize experience level to match enum (capitalize first letter)
        exp_level = background_responses["experience_level_selection"]
        if isinstance(exp_level, str):
            exp_level = exp_level.lower()
            if exp_level == "beginner":
                exp_level = "Beginner"
            elif exp_level == "intermediate":
                exp_level = "Intermediate"
            elif exp_level == "advanced":
                exp_level = "Advanced"
        background_update["experience_level"] = exp_level
    if "years_of_experience" in background_responses:
        background_update["years_experience"] = int(background_responses["years_of_experience"])
    if "preferred_languages" in background_responses:
        background_update["preferred_languages"] = background_responses["preferred_languages"]
    if "cpu_expertise" in background_responses:
        if "hardware_expertise" not in background_update:
            background_update["hardware_expertise"] = {}
        background_update["hardware_expertise"]["cpu"] = background_responses["cpu_expertise"]
    if "gpu_expertise" in background_responses:
        if "hardware_expertise" not in background_update:
            background_update["hardware_expertise"] = {}
        background_update["hardware_expertise"]["gpu"] = background_responses["gpu_expertise"]
    if "networking_expertise" in background_responses:
        if "hardware_expertise" not in background_update:
            background_update["hardware_expertise"] = {}
        background_update["hardware_expertise"]["networking"] = background_responses["networking_expertise"]

    # Create or update user background
    if background_update:
        result = await db.execute(
            select(UserBackground).where(UserBackground.user_id == user.id)
        )
        background = result.scalar_one_or_none()

        if background:
            # Update existing background - handle enum specially
            if "experience_level" in background_update:
                exp_level = background_update["experience_level"]
                if isinstance(exp_level, str):
                    exp_level = exp_level.lower()
                    if exp_level == "beginner":
                        background.experience_level = UserBackground.ExperienceLevel.BEGINNER
                    elif exp_level == "intermediate":
                        background.experience_level = UserBackground.ExperienceLevel.INTERMEDIATE
                    elif exp_level == "advanced":
                        background.experience_level = UserBackground.ExperienceLevel.ADVANCED

            for key, value in background_update.items():
                if key != "experience_level" and hasattr(background, key):
                    setattr(background, key, value)
            background.updated_at = datetime.utcnow()
        else:
            # Create new background - handle enum properly
            exp_level_enum = UserBackground.ExperienceLevel.BEGINNER
            if "experience_level" in background_update:
                exp_level = background_update["experience_level"]
                if isinstance(exp_level, str):
                    exp_level = exp_level.lower()
                    if exp_level == "beginner":
                        exp_level_enum = UserBackground.ExperienceLevel.BEGINNER
                    elif exp_level == "intermediate":
                        exp_level_enum = UserBackground.ExperienceLevel.INTERMEDIATE
                    elif exp_level == "advanced":
                        exp_level_enum = UserBackground.ExperienceLevel.ADVANCED

            background = UserBackground(
                user_id=user.id,
                experience_level=exp_level_enum,
                years_of_experience=background_update.get("years_of_experience", 0),
                preferred_languages=background_update.get("preferred_languages", []),
                hardware_expertise=background_update.get("hardware_expertise", {"cpu": "none", "gpu": "none", "networking": "none"})
            )
            db.add(background)

        await db.commit()

    return {"success": True, "message": "Onboarding responses saved successfully"}


@router.get("/onboarding", response_model=List[OnboardingResponseSchema])
async def get_onboarding_responses(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Get user's onboarding responses.

    Args:
        request: FastAPI request object (user from middleware)
        db: Database session

    Returns:
        List of onboarding responses
    """
    user = await get_current_user(request)

    result = await db.execute(
        select(OnboardingResponse).where(OnboardingResponse.user_id == user.id)
    )
    responses = result.scalars().all()

    return responses


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Get user's preferences.

    Args:
        request: FastAPI request object (user from middleware)
        db: Database session

    Returns:
        User preferences data
    """
    user = await get_current_user(request)

    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    preferences = result.scalar_one_or_none()

    if not preferences:
        # Return default preferences
        return {
            "id": "",
            "user_id": user.id,
            "theme": "auto",
            "language": "en",
            "notification_settings": {
                "email_responses": False,
                "browser_notifications": True,
                "marketing_emails": False
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    return preferences


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Update user's preferences.

    Args:
        preferences_data: Preferences data to update
        request: FastAPI request object (user from middleware)
        db: Database session

    Returns:
        Updated preferences data
    """
    user = await get_current_user(request)

    # Get or create preferences (using async)
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    preferences = result.scalar_one_or_none()

    if preferences:
        # Update existing preferences
        if preferences_data.theme is not None:
            preferences.theme = preferences_data.theme
        if preferences_data.language is not None:
            preferences.language = preferences_data.language
        if preferences_data.notification_settings is not None:
            preferences.notification_settings.update(preferences_data.notification_settings)
        preferences.updated_at = datetime.utcnow()
    else:
        # Create new preferences with defaults
        preferences = UserPreferences(
            user_id=user.id,
            theme=preferences_data.theme or "auto",
            language=preferences_data.language or "en",
            notification_settings=preferences_data.notification_settings or {
                "email_responses": False,
                "browser_notifications": True,
                "marketing_emails": False
            }
        )
        db.add(preferences)

    await db.commit()
    await db.refresh(preferences)

    return preferences
