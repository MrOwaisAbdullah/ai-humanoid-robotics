"""
Personalization API Routes
Handles content personalization endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta
import hashlib
import uuid

from src.core.database import get_async_db
from src.security.dependencies import get_current_user_from_request
from src.models.auth import User, UserBackground
from src.models.personalization import SavedPersonalization
from src.agents.personalization_agent import PersonalizationAgent
from src.services.personalization import PersonalizationService

router = APIRouter(prefix="/personalize", tags=["personalization"])
security = HTTPBearer()


def clean_content_for_personalization(content: str) -> str:
    """
    Clean content to remove UI elements and noise before personalization.
    """
    import re

    # Split into lines and filter
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        trimmed_line = line.strip()
        if not trimmed_line:
            continue

        lower_line = trimmed_line.lower()

        # Only filter the most obvious UI patterns
        ui_patterns = [
            'personalize', 'translate to', 'read aloud',
            'edit this page', 'last updated',
            'ai features', 'share', 'copy link',
            'skip to main content',
            'facebook', 'twitter', 'linkedin', 'github'
        ]

        # Skip lines with obvious UI patterns
        if any(pattern in lower_line for pattern in ui_patterns):
            continue

        # Skip very short lines that are clearly UI (like single navigation items)
        if len(trimmed_line) < 3:
            continue

        # Skip lines that are just navigation indicators
        if trimmed_line in ['Previous', 'Next', 'Home', 'Menu', 'Search', 'Close']:
            continue

        # Skip lines that are just numbers (very short ones)
        if re.match(r'^\d{1,2}$', trimmed_line):
            continue

        # Don't skip breadcrumbs or paths - they might contain useful context
        # Don't be aggressive with filtering to preserve content

        cleaned_lines.append(trimmed_line)

    # Join and do final regex cleanup
    cleaned_content = '\n'.join(cleaned_lines)

    # Remove any remaining UI patterns with regex
    cleaned_content = re.sub(r'\b(min read|edit this page|last updated|ai features)\b', '', cleaned_content, flags=re.IGNORECASE)
    cleaned_content = re.sub(r'\b(\d+ min read|minute read)\b', '', cleaned_content, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)
    cleaned_content = re.sub(r' +', ' ', cleaned_content)

    return cleaned_content.strip()


@router.get("/saved")  # Matches /api/v1/personalize/saved
async def list_personalizations(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    List saved personalizations for the current user.
    """
    current_user: User = await get_current_user_from_request(request)
    result = await db.execute(
        select(SavedPersonalization)
        .filter(SavedPersonalization.user_id == current_user.id)
        .order_by(SavedPersonalization.created_at.desc())
    )
    saved_items = result.scalars().all()

    return {
        "personalizations": [
            {
                "id": str(item.id),
                "title": item.content_title,
                "original_content": item.personalization_metadata.get("original_excerpt", ""),
                "explanation": item.personalized_content,
                "created_at": item.created_at.isoformat(),
                "expires_at": (item.created_at + timedelta(days=30)).isoformat()
            }
            for item in saved_items
        ],
        "total": len(saved_items),
        "message": "Saved personalizations retrieved successfully"
    }


@router.post("")  # Matches /api/v1/personalize
async def generate_personalization(
    request_body: Dict[str, Any],
    http_request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate a personalized explanation for the given content.
    """
    current_user: User = await get_current_user_from_request(http_request)
    try:
        content = request_body.get("content", "")
        context_type = request_body.get("context_type", "page")
        word_count = request_body.get("word_count", 0)

        # Clean content to remove UI elements that might have slipped through
        # Only clean if content is not empty
        if content:
            content = clean_content_for_personalization(content)

        # Initialize services
        personalization_service = PersonalizationService(db)
        agent = PersonalizationAgent()

        # Build user profile directly
        user_profile = await _build_user_profile(current_user, db)

        # Generate personalized content
        result = await agent.personalize_content(content, user_profile)

        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Personalization failed: {result['error']}"
            )

        # Agent returns "personalized_content" but simple fallback might return "content"
        explanation = result.get("personalized_content") or result.get("content")
        
        print(f"[DEBUG] Result keys: {list(result.keys())}")
        print(f"[DEBUG] Explanation length: {len(explanation) if explanation else 'None'}")
        print(f"[DEBUG] Success status: {result.get('success')}")

        if not explanation:
            raise HTTPException(
                status_code=500,
                detail="No personalization generated"
            )

        response_data = {
            "explanation": explanation,
            "context_type": context_type,
            "word_count": word_count,
            "generated_at": datetime.utcnow().isoformat(),
            "adaptations_made": result.get("adaptations", []),
            "processing_time": result.get("processing_metadata", {})
        }

        print(f"[DEBUG] Returning response with explanation length: {len(response_data['explanation'])}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate personalization: {str(e)}"
        )


@router.post("/saved/{personalization_id}")  # Matches /api/v1/personalize/saved/{id}
async def save_personalization(
    personalization_id: str,
    request_body: Dict[str, Any],
    http_request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Save a personalization for later reference.

    Accepts either:
    - { content, explanation } - Full personalization save
    - { title, tags, notes } - Update existing personalization metadata
    """
    current_user: User = await get_current_user_from_request(http_request)
    try:
        title = request_body.get("title")
        tags = request_body.get("tags")
        notes = request_body.get("notes")

        # Check if this is a metadata update (from frontend)
        if title or tags or notes:
            # Try to find existing personalization
            result = await db.execute(
                select(SavedPersonalization).filter(
                    SavedPersonalization.id == personalization_id,
                    SavedPersonalization.user_id == current_user.id
                )
            )
            saved_item = result.scalar_one_or_none()

            if saved_item:
                # Update existing item
                if title:
                    saved_item.content_title = title
                if tags:
                    # Store tags in metadata
                    metadata = saved_item.personalization_metadata or {}
                    metadata["tags"] = tags
                    saved_item.personalization_metadata = metadata
                if notes:
                    # Store notes in metadata
                    metadata = saved_item.personalization_metadata or {}
                    metadata["notes"] = notes
                    saved_item.personalization_metadata = metadata

                await db.commit()
                await db.refresh(saved_item)

                return {
                    "id": str(saved_item.id),
                    "message": "Personalization updated successfully",
                    "title": saved_item.content_title,
                    "tags": tags,
                    "notes": notes
                }

        # Original save behavior (fallback)
        content = request_body.get("content", "")
        explanation = request_body.get("explanation", "")
        context_type = request_body.get("context_type", "page")
        word_count = request_body.get("word_count", 0)

        if not explanation.strip():
            raise HTTPException(
                status_code=400,
                detail="Explanation is required to save personalization"
            )

        # Clean content to remove UI elements
        content = clean_content_for_personalization(content)

        # Calculate hash
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # Generate title if not provided
        if not title:
            title = content[:50] + "..." if len(content) > 50 else content

        saved_item = SavedPersonalization(
            user_id=current_user.id,
            original_content_hash=content_hash,
            content_url="", # Placeholder
            content_title=title,
            personalized_content=explanation,
            personalization_metadata={
                "context_type": context_type,
                "word_count": word_count,
                "original_excerpt": content[:200],
                "tags": tags or [],
                "notes": notes or ""
            },
            adaptations_applied=[]
        )

        db.add(saved_item)
        await db.commit()
        await db.refresh(saved_item)

        return {
            "id": str(saved_item.id),
            "message": "Personalization saved successfully",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "title": title,
            "tags": tags or [],
            "notes": notes or ""
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save personalization: {str(e)}"
        )


async def _build_user_profile(user: User, db: AsyncSession) -> Dict[str, Any]:
    """Build user profile for personalization."""
    # Get user background if exists
    result = await db.execute(
        select(UserBackground).filter(UserBackground.user_id == user.id)
    )
    background = result.scalar_one_or_none()

    # Initialize with basic profile
    profile = {
        "user_id": user.id,
        "experience_level": "beginner",
        "primary_expertise": "general"
    }

    # Safely extract background information if it exists
    if background:
        try:
            # Experience level - handle Enum safely
            if hasattr(background, 'experience_level') and background.experience_level:
                profile["experience_level"] = (
                    background.experience_level.lower() if hasattr(background.experience_level, 'lower')
                    else str(background.experience_level).lower()
                )
        except Exception:
            # Keep default beginner level
            pass

        try:
            # Hardware expertise - handle JSON/Dict safely
            if hasattr(background, 'hardware_expertise') and background.hardware_expertise:
                if isinstance(background.hardware_expertise, dict):
                    # Extract primary hardware expertise from dict
                    if background.hardware_expertise:
                        # Get the first key or a summary
                        primary = list(background.hardware_expertise.keys())[0] if background.hardware_expertise else "general"
                        profile["primary_expertise"] = primary.lower()
                    else:
                        profile["primary_expertise"] = "general"
                else:
                    # Handle as string/enum
                    profile["primary_expertise"] = (
                        background.hardware_expertise.lower() if hasattr(background.hardware_expertise, 'lower')
                        else str(background.hardware_expertise).lower()
                    )
        except Exception:
            # Keep default general expertise
            pass

        try:
            # Years of experience - handle numeric field
            if hasattr(background, 'years_of_experience') and background.years_of_experience is not None:
                profile["years_of_experience"] = int(background.years_of_experience)
        except Exception:
            # Skip if invalid
            pass

        try:
            # Preferred languages - handle JSON list
            if hasattr(background, 'preferred_languages') and background.preferred_languages:
                if isinstance(background.preferred_languages, list) and background.preferred_languages:
                    profile["preferred_languages"] = [
                        str(lang).lower() for lang in background.preferred_languages if lang
                    ]
                elif isinstance(background.preferred_languages, str):
                    profile["preferred_languages"] = [background.preferred_languages.lower()]
        except Exception:
            # Skip if invalid
            pass

        # Determine if user has hardware or software focus based on available data
        try:
            if isinstance(getattr(background, 'hardware_expertise', None), dict):
                hw_exp = background.hardware_expertise or {}
                # Check if they have significant hardware expertise
                if hw_exp and any(k != 'None' for k in hw_exp.keys()):
                    profile["technical_focus"] = "hardware"
                else:
                    profile["technical_focus"] = "software"
            else:
                # Default to software if hardware_expertise is not a dict
                profile["technical_focus"] = "software"
        except Exception:
            profile["technical_focus"] = "general"

    # Add preferences if available (handle missing UserPreferences model gracefully)
    try:
        # Check if UserPreferences model exists
        from src.models.auth import UserPreferences
        pref_result = await db.execute(
            select(UserPreferences).filter(UserPreferences.user_id == user.id)
        )
        preferences = pref_result.scalar_one_or_none()

        if preferences:
            pref_dict = {}
            # Add each preference field safely
            for field in ['language', 'reading_pace', 'show_code_examples', 'learning_style']:
                if hasattr(preferences, field):
                    value = getattr(preferences, field)
                    if value is not None:
                        pref_dict[field] = value
            if pref_dict:
                profile["preferences"] = pref_dict
    except (ImportError, AttributeError, Exception):
        # UserPreferences model or fields don't exist - skip preferences
        pass

    return profile
