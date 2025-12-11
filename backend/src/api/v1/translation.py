"""
Translation API endpoints.

Provides endpoints for text translation and feedback submission
with OpenAPI compliance, error handling, and streaming support.
"""

import asyncio
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import logging
from datetime import datetime

from src.services.translation_service import (
    get_translation_service,
    GeminiTranslationService,
    TranslationRequest,
    TranslationResponse,
    TranslationStatus
)
from src.models.translation import Translation
from src.database.base import get_db
from src.security.dependencies import get_optional_current_user
from src.utils.errors import ValidationError, ServiceError, log_exception
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Router configuration
router = APIRouter(
    prefix="/translation",
    tags=["Translation"],
    responses={
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)

# Security
security = HTTPBearer(auto_error=False)


# Request/Response Schemas
class TranslationRequestSchema(BaseModel):
    """Schema for translation requests."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Text content to translate",
        example="This is a sample text for translation."
    )
    source_language: str = Field(
        ...,
        pattern="^(en|ur|ur-roman)$",
        description="Source language code",
        example="en"
    )
    target_language: str = Field(
        default="ur",
        pattern="^(en|ur|ur-roman)$",
        description="Target language code",
        example="ur"
    )
    preserve_code_blocks: bool = Field(
        default=True,
        description="Whether to skip translation for code blocks"
    )
    enable_transliteration: bool = Field(
        default=True,
        description="Enable technical term transliteration"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalized translations"
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the translation response"
    )

    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()

    @validator('target_language')
    def validate_languages(cls, v, values):
        if 'source_language' in values and v == values['source_language']:
            raise ValueError("Source and target languages must be different")
        return v


class TranslationResponseSchema(BaseModel):
    """Schema for translation responses."""
    translated_text: str = Field(
        ...,
        description="Translated text content"
    )
    content_hash: str = Field(
        ...,
        description="SHA-256 hash of original content"
    )
    chunks: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Translation chunks (if content was split)"
    )
    processing_time_ms: int = Field(
        ...,
        description="Time taken to process translation in milliseconds"
    )
    cached: bool = Field(
        ...,
        description="Whether response was from cache"
    )
    status: str = Field(
        ...,
        description="Translation status"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if translation failed"
    )


class FeedbackRequestSchema(BaseModel):
    """Schema for feedback requests."""
    rating: int = Field(
        ...,
        ge=-1,
        le=1,
        description="Rating: -1 for thumbs down, 1 for thumbs up"
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=280,
        description="Optional feedback comment"
    )

    @validator('rating')
    def validate_rating(cls, v):
        if v not in [-1, 1]:
            raise ValueError("Rating must be -1 or 1")
        return v


class FeedbackResponseSchema(BaseModel):
    """Schema for feedback responses."""
    success: bool = Field(
        ...,
        description="Whether feedback was submitted successfully"
    )
    message: str = Field(
        ...,
        description="Response message"
    )
    feedback_id: Optional[int] = Field(
        default=None,
        description="Feedback record ID"
    )


class TranslationHistorySchema(BaseModel):
    """Schema for translation history."""
    translations: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int


@router.post(
    "/",
    response_model=TranslationResponseSchema,
    summary="Translate content to Urdu",
    description="Translates the given text content to Urdu using Gemini LLM with support for code blocks preservation and technical terms transliteration."
)
async def translate_content(
    request: TranslationRequestSchema,
    background_tasks: BackgroundTasks,
    http_request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    print(f"*** TRANSLATION ENDPOINT ENTRY: text={request.text[:30] if request.text else 'None'} ***")
    """
    Translate content endpoint.

    Args:
        request: Translation request data
        background_tasks: FastAPI background tasks
        http_request: HTTP request object
        credentials: Optional HTTP bearer credentials
        current_user: Optional authenticated user

    Returns:
        Translation response or streaming response
    """
    print(f"*** TRANSLATION ENDPOINT CALLED: '{request.text[:30]}...' ***")
    # Debug logging
    logger.info(f"Translation request received: text='{request.text[:50]}...', source={request.source_language}, target={request.target_language}")

    # Validate service availability
    try:
        translation_service = await get_translation_service()
    except Exception as e:
        logger.error("Translation service not available", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Translation service is currently unavailable"
        )

    # Create translation request
    translation_request = TranslationRequest(
        text=request.text,
        source_language=request.source_language,
        target_language=request.target_language,
        user_id=request.user_id or (current_user.get("id") if current_user else None),
        preserve_code_blocks=request.preserve_code_blocks,
        enable_transliteration=request.enable_transliteration,
        streaming=request.stream
    )

    # Handle streaming request
    if request.stream:
        async def generate_stream():
            try:
                async for chunk in translation_service.translate_streaming(translation_request):
                    # Format as Server-Sent Events
                    yield f"data: {chunk.json()}\n\n"
            except Exception as e:
                logger.error("Streaming translation failed", error=str(e))
                error_chunk = {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {error_chunk.json()}\n\n"
            finally:
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )

    # Handle non-streaming request
    try:
        # Log translation request
        logger.info(
            "Translation request received",
            source_lang=request.source_language,
            target_lang=request.target_language,
            text_length=len(request.text),
            user_authenticated=current_user is not None,
            preserve_code=request.preserve_code_blocks,
            enable_transliteration=request.enable_transliteration
        )

        # Perform translation
        response = await translation_service.translate(translation_request)

        # Log successful translation
        if response.status == TranslationStatus.COMPLETED:
            # Debug: Log actual translation
            logger.info(
                "Translation completed",
                content_hash=response.content_hash[:8],
                cached=response.cached,
                processing_time_ms=response.processing_time_ms,
                chunks_count=len(response.chunks) if response.chunks else 0,
                original_text_preview=request.text[:100] + "..." if len(request.text) > 100 else request.text,
                translated_text_preview=response.translated_text[:100] + "..." if len(response.translated_text) > 100 else response.translated_text
            )

            # Add background task for analytics if needed
            if current_user and not response.cached:
                background_tasks.add_task(
                    log_translation_analytics,
                    current_user.get("id"),
                    response.content_hash,
                    request.source_language,
                    request.target_language,
                    len(request.text),
                    response.processing_time_ms
                )

        else:
            logger.warning(
                "Translation failed",
                content_hash=response.content_hash[:8],
                error=response.error_message
            )

        return TranslationResponseSchema(
            translated_text=response.translated_text,
            content_hash=response.content_hash,
            chunks=response.chunks,
            processing_time_ms=response.processing_time_ms,
            cached=response.cached,
            status=response.status.value,
            error_message=response.error_message
        )

    except ValidationError as e:
        logger.warning("Validation error in translation", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error": "VALIDATION_ERROR",
                "message": str(e)
            }
        )

    except ServiceError as e:
        logger.error("Translation service error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SERVICE_ERROR",
                "message": str(e)
            }
        )

    except Exception as e:
        log_exception(e, "Unexpected error in translation endpoint")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during translation"
            }
        )


@router.post(
    "/{translation_id}/feedback",
    response_model=FeedbackResponseSchema,
    summary="Submit feedback for translation",
    description="Submit thumbs up/down feedback for a translation to help improve quality."
)
async def submit_translation_feedback(
    translation_id: int,
    feedback: FeedbackRequestSchema,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Submit translation feedback endpoint.

    Args:
        translation_id: ID of the translation
        feedback: Feedback data
        current_user: Optional authenticated user
        credentials: HTTP bearer credentials

    Returns:
        Feedback submission response
    """
    # Require authentication for feedback
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to submit feedback"
        )

    # Validate translation exists
    db = next(get_db())
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "TRANSLATION_NOT_FOUND",
                    "message": f"Translation with ID {translation_id} not found"
                }
            )
    finally:
        db.close()

    try:
        # Submit feedback
        translation_service = await get_translation_service()
        success = await translation_service.submit_feedback(
            translation_id=translation_id,
            user_id=current_user.get("id"),
            rating=feedback.rating,
            comment=feedback.comment
        )

        if success:
            logger.info(
                "Feedback submitted successfully",
                translation_id=translation_id,
                user_id=current_user.get("id"),
                rating=feedback.rating,
                has_comment=bool(feedback.comment)
            )

            return FeedbackResponseSchema(
                success=True,
                message="Feedback submitted successfully",
                feedback_id=translation_id
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "FEEDBACK_SUBMISSION_FAILED",
                    "message": "Failed to submit feedback"
                }
            )

    except ValidationError as e:
        logger.warning("Validation error in feedback", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error": "VALIDATION_ERROR",
                "message": str(e)
            }
        )

    except Exception as e:
        log_exception(e, "Unexpected error in feedback endpoint")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while submitting feedback"
            }
        )


@router.get(
    "/history",
    response_model=TranslationHistorySchema,
    summary="Get translation history",
    description="Retrieve user's translation history with pagination."
)
async def get_translation_history(
    page: int = 1,
    per_page: int = 20,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Get translation history endpoint.

    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
        current_user: Optional authenticated user
        credentials: HTTP bearer credentials

    Returns:
        Paginated translation history
    """
    # Require authentication for history
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to view translation history"
        )

    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    try:
        db = next(get_db())
        try:
            # Query translations with feedback
            query = db.query(Translation).filter(
                # This would need user_id in Translation model or a join
                # For now, return empty history
            )

            # Get total count
            total = query.count()

            # Get paginated results
            offset = (page - 1) * per_page
            translations = query.offset(offset).limit(per_page).all()

            # Convert to response format
            history_items = []
            for translation in translations:
                history_items.append({
                    "id": translation.id,
                    "content_hash": translation.content_hash,
                    "source_language": translation.source_language,
                    "target_language": translation.target_language,
                    "character_count": translation.character_count,
                    "created_at": translation.created_at.isoformat(),
                    "translation_model": translation.translation_model
                })

            return TranslationHistorySchema(
                translations=history_items,
                total=total,
                page=page,
                per_page=per_page
            )

        finally:
            db.close()

    except Exception as e:
        log_exception(e, "Error fetching translation history")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "HISTORY_FETCH_FAILED",
                "message": "Failed to fetch translation history"
            }
        )


@router.delete(
    "/cache/{content_hash}",
    summary="Clear translation cache",
    description="Clear cached translation for specific content (admin only)."
)
async def clear_translation_cache(
    content_hash: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Clear translation cache endpoint.

    Args:
        content_hash: Content hash to clear from cache
        current_user: Optional authenticated user
        credentials: HTTP bearer credentials

    Returns:
        Cache clear response
    """
    # Require admin privileges
    if not current_user or not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required to clear cache"
        )

    try:
        translation_service = await get_translation_service()
        cache_service = translation_service.cache_service

        if cache_service:
            cache_key = f"translation:{content_hash}"
            success = await cache_service.delete(cache_key)

            if success:
                logger.info(
                    "Translation cache cleared",
                    content_hash=content_hash[:8],
                    cleared_by=current_user.get("id")
                )
                return {"message": f"Cache cleared for content hash {content_hash[:8]}..."}
            else:
                return {"message": "No cache entry found for the specified content hash"}
        else:
            return {"message": "Cache service not available"}

    except Exception as e:
        log_exception(e, "Error clearing translation cache")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CACHE_CLEAR_FAILED",
                "message": "Failed to clear translation cache"
            }
        )


# Background task for analytics
async def log_translation_analytics(
    user_id: str,
    content_hash: str,
    source_lang: str,
    target_lang: str,
    char_count: int,
    processing_time_ms: int
):
    """
    Log translation analytics.

    Args:
        user_id: User ID
        content_hash: Content hash
        source_lang: Source language
        target_lang: Target language
        char_count: Character count
        processing_time_ms: Processing time
    """
    try:
        # This would integrate with your analytics system
        logger.info(
            "Translation analytics",
            user_id=user_id,
            content_hash=content_hash[:8],
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=char_count,
            processing_time_ms=processing_time_ms
        )
    except Exception as e:
        logger.error("Failed to log translation analytics", error=str(e))