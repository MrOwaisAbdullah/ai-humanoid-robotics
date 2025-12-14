"""
Progress tracking API endpoints.

Manages user reading progress through chapters and sections.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from src.database.base import get_db
from src.middleware.auth import get_current_active_user, require_user
from src.models.auth import User
from src.models.reading_progress import ReadingProgress
from src.models.user_preferences import UserPreference
from src.services.progress import ReadingProgressService
from src.services.personalization import PersonalizationService
from src.utils.errors import handle_errors, NotFoundError, ValidationError
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/progress",
    tags=["progress"]
)

# Pydantic models for API
class SectionProgress(BaseModel):
    section_id: str = Field(..., description="Section identifier")
    position: float = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    time_spent: int = Field(0, ge=0, description="Time spent in minutes")
    completed: bool = Field(False, description="Whether section is completed")

    @validator('position')
    def validate_position(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Position must be between 0 and 100")
        return v

class ChapterProgressUpdate(BaseModel):
    chapter_id: str = Field(..., description="Chapter identifier")
    sections: List[SectionProgress] = Field(..., description="Section progress updates")

class ProgressResponse(BaseModel):
    chapter_id: str
    overall_progress: float
    sections_completed: int
    total_sections: int
    time_spent: int
    sections: List[Dict[str, Any]]
    last_accessed: Optional[str]
    estimated_completion: Optional[Dict[str, Any]]

class SessionStart(BaseModel):
    chapter_id: str = Field(..., description="Chapter identifier")
    section_id: Optional[str] = Field(None, description="Section identifier")

class SessionEnd(BaseModel):
    chapter_id: str = Field(..., description="Chapter identifier")
    section_id: Optional[str] = Field(None, description="Section identifier")
    position: float = Field(..., ge=0, le=100, description="Final position")
    time_spent: int = Field(..., ge=0, description="Time spent in minutes")


# Helper function to get services
def get_progress_service(db: Session = Depends(get_db)) -> ReadingProgressService:
    return ReadingProgressService(db)

def get_personalization_service(db: Session = Depends(get_db)) -> PersonalizationService:
    return PersonalizationService(db)


@router.get("/chapter/{chapter_id}")
@handle_errors
async def get_chapter_progress(
    chapter_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> ProgressResponse:
    """Get comprehensive progress for a specific chapter."""
    progress = await service.get_chapter_progress(current_user.id, chapter_id)

    if not progress["total_sections"]:
        raise NotFoundError("Chapter", chapter_id)

    return ProgressResponse(**progress)


@router.get("/summary")
@handle_errors
async def get_progress_summary(
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Get overall reading progress summary for the user."""
    summary = await service.get_user_progress_summary(current_user.id)

    # Add personalization info
    personalization_service = PersonalizationService(service.db)
    personalization = await personalization_service.get_user_personalization(current_user.id)

    return {
        **summary,
        "personalization": personalization,
        "last_updated": datetime.utcnow().isoformat()
    }


@router.post("/session/start")
@handle_errors
async def start_reading_session(
    session_data: SessionStart,
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Start a new reading session."""
    # Log session start
    logger.info(
        "Reading session started",
        user_id=current_user.id,
        chapter_id=session_data.chapter_id,
        section_id=session_data.section_id
    )

    # Get or create progress record
    progress = await service.update_section_progress(
        user_id=current_user.id,
        chapter_id=session_data.chapter_id,
        section_id=session_data.section_id or f"{session_data.chapter_id}_intro",
        position=0,
        time_spent_delta=0
    )

    return {
        "session_id": progress.id,
        "chapter_id": session_data.chapter_id,
        "section_id": session_data.section_id,
        "started_at": progress.last_accessed.isoformat(),
        "message": "Reading session started successfully"
    }


@router.post("/session/end")
@handle_errors
async def end_reading_session(
    session_data: SessionEnd,
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """End a reading session with final progress."""
    # Update progress with session data
    progress = await service.update_section_progress(
        user_id=current_user.id,
        chapter_id=session_data.chapter_id,
        section_id=session_data.section_id or f"{session_data.chapter_id}_intro",
        position=session_data.position,
        time_spent_delta=session_data.time_spent,
        completed=session_data.position >= 100
    )

    # Get updated chapter progress
    chapter_progress = await service.get_chapter_progress(current_user.id, session_data.chapter_id)

    # Generate session summary
    session_summary = {
        "chapter_id": session_data.chapter_id,
        "section_id": session_data.section_id,
        "final_position": session_data.position,
        "time_spent": session_data.time_spent,
        "chapter_progress": chapter_progress["overall_progress"],
        "sections_completed": chapter_progress["sections_completed"],
        "completed_at": datetime.utcnow().isoformat()
    }

    # Log session end
    logger.info(
        "Reading session ended",
        user_id=current_user.id,
        **session_summary
    )

    return {
        "session_id": progress.id,
        "summary": session_summary,
        "message": "Reading session completed successfully"
    }


@router.post("/update")
@handle_errors
async def update_progress(
    progress_update: ChapterProgressUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Update progress for multiple sections in a chapter."""
    updated_sections = []
    errors = []

    for section in progress_update.sections:
        try:
            updated = await service.update_section_progress(
                user_id=current_user.id,
                chapter_id=progress_update.chapter_id,
                section_id=section.section_id,
                position=section.position,
                time_spent_delta=section.time_spent,
                completed=section.completed
            )
            updated_sections.append({
                "section_id": section.section_id,
                "position": updated.position,
                "completed": updated.completed,
                "updated_at": updated.updated_at.isoformat()
            })
        except Exception as e:
            logger.error(
                "Failed to update section progress",
                user_id=current_user.id,
                chapter_id=progress_update.chapter_id,
                section_id=section.section_id,
                error=str(e)
            )
            errors.append({
                "section_id": section.section_id,
                "error": str(e)
            })

    # Schedule background task to calculate recommendations
    if updated_sections:
        background_tasks.add_task(
            calculate_recommendations_delayed,
            current_user.id
        )

    return {
        "chapter_id": progress_update.chapter_id,
        "updated_sections": updated_sections,
        "errors": errors,
        "total_updated": len(updated_sections),
        "total_errors": len(errors),
        "message": f"Updated {len(updated_sections)} sections successfully"
    }


@router.post("/section/{section_id}/complete")
@handle_errors
async def complete_section(
    chapter_id: str,
    section_id: str,
    time_spent: int = Query(0, ge=0, description="Time spent in minutes"),
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Mark a section as completed."""
    progress = await service.mark_section_complete(
        user_id=current_user.id,
        chapter_id=chapter_id,
        section_id=section_id,
        time_spent_delta=time_spent
    )

    # Get updated chapter progress
    chapter_progress = await service.get_chapter_progress(current_user.id, chapter_id)

    # Log completion
    logger.info(
        "Section completed",
        user_id=current_user.id,
        chapter_id=chapter_id,
        section_id=section_id,
        position=100,
        time_spent=time_spent
    )

    return {
        "section_id": section_id,
        "chapter_id": chapter_id,
        "completed_at": progress.updated_at.isoformat(),
        "time_spent": time_spent,
        "chapter_progress": chapter_progress["overall_progress"],
        "sections_completed": chapter_progress["sections_completed"],
        "message": "Section marked as completed"
    }


@router.get("/restore/{chapter_id}")
@handle_errors
async def restore_progress(
    chapter_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Restore user's last position in a chapter."""
    restored = await service.restore_progress(current_user.id, chapter_id)

    if restored["section_id"]:
        # Update last accessed
        progress = await service.update_section_progress(
            user_id=current_user.id,
            chapter_id=chapter_id,
            section_id=restored["section_id"],
            position=restored["position"],
            time_spent_delta=0
        )

        logger.info(
            "Progress restored",
            user_id=current_user.id,
            chapter_id=chapter_id,
            section_id=restored["section_id"],
            position=restored["position"]
        )

    return restored


@router.get("/analytics")
@handle_errors
async def get_progress_analytics(
    timeframe: str = Query("month", regex="^(day|week|month|year)$"),
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Get detailed reading analytics."""
    analytics = await service.get_reading_analytics(current_user.id, timeframe)

    # Add additional user-specific analytics
    personalization_service = PersonalizationService(service.db)
    personalization = await personalization_service.get_user_personalization(current_user.id)

    return {
        **analytics,
        "user_experience_level": personalization["experience_level"],
        "user_preferences": personalization["preferences"],
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/bulk")
@handle_errors
async def bulk_update_progress(
    updates: List[ChapterProgressUpdate],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    service: ReadingProgressService = Depends(get_progress_service)
) -> Dict[str, Any]:
    """Bulk update progress for multiple chapters."""
    results = []
    total_updated = 0
    total_errors = 0

    for chapter_update in updates:
        try:
            chapter_result = await update_progress(
                progress_update=chapter_update,
                background_tasks=background_tasks,
                current_user=current_user,
                service=service
            )
            results.append(chapter_result)
            total_updated += chapter_result["total_updated"]
            total_errors += chapter_result["total_errors"]
        except Exception as e:
            logger.error(
                "Failed to bulk update chapter progress",
                user_id=current_user.id,
                chapter_id=chapter_update.chapter_id,
                error=str(e)
            )
            results.append({
                "chapter_id": chapter_update.chapter_id,
                "updated_sections": [],
                "errors": [{"error": str(e)}],
                "total_updated": 0,
                "total_errors": 1
            })
            total_errors += 1

    return {
        "results": results,
        "summary": {
            "total_chapters": len(updates),
            "total_updated": total_updated,
            "total_errors": total_errors,
            "success_rate": (total_updated / (total_updated + total_errors)) * 100 if (total_updated + total_errors) > 0 else 0
        },
        "message": f"Bulk update completed: {total_updated} sections updated, {total_errors} errors"
    }


@router.delete("/chapter/{chapter_id}")
@handle_errors
async def reset_chapter_progress(
    chapter_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Reset all progress for a specific chapter."""
    # Delete all progress records for this chapter
    deleted = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.chapter_id == chapter_id
    ).delete()

    db.commit()

    logger.info(
        "Chapter progress reset",
        user_id=current_user.id,
        chapter_id=chapter_id,
        deleted_sections=deleted
    )

    return {
        "chapter_id": chapter_id,
        "deleted_sections": deleted,
        "message": f"Progress for chapter {chapter_id} has been reset"
    }


# Background task helper
async def calculate_recommendations_delayed(user_id: str):
    """Background task to calculate recommendations after progress update."""
    try:
        from src.services.personalization import PersonalizationService
        from src.database.base import SessionLocal

        db = SessionLocal()
        try:
            service = PersonalizationService(db)
            recommendations = await service.generate_recommendations(user_id, limit=5)

            logger.info(
                "Recommendations calculated",
                user_id=user_id,
                recommendations_count=len(recommendations)
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(
            "Failed to calculate recommendations in background task",
            user_id=user_id,
            error=str(e)
        )