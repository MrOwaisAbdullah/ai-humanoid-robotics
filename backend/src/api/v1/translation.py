"""
Translation API endpoints using OpenAI Agents SDK.

Provides RESTful endpoints for translating text from English to Urdu
using the OpenAI Agents SDK with Gemini API integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi import status
from typing import Optional, Dict, Any
import time

from src.services.openai_translation.translation_agent import OpenAITranslationAgent, TranslationContext
from src.services.openai_translation.client import get_gemini_client
from src.services.translation_cache import cache_service
from src.models.auth import User
from src.security.dependencies import get_current_user_or_anonymous

router = APIRouter(prefix="/translation", tags=["translation"])


@router.post("/translate", response_model=dict)
async def translate_text(
    request: dict,
    http_request: Request,
    current_user: Optional[User] = Depends(get_current_user_or_anonymous)
) -> JSONResponse:
    """
    Legacy translation endpoint (for backward compatibility).

    This endpoint uses the OpenAI Agents SDK with the improved agent implementation.

    Args:
        request: Translation request with text and parameters
        http_request: FastAPI request object
        current_user: Optional current user

    Returns:
        Translation result
    """
    try:
        # Extract request data
        text = request.get("text", "")
        source_language = request.get("source_language", "en")
        target_language = request.get("target_language", "ur")
        document_type = request.get("document_type")
        technical_domain = request.get("technical_domain")
        target_audience = request.get("target_audience")
        model = request.get("model", "gemini-2.0-flash-lite")

        # Create translation context
        context = TranslationContext(
            document_type=document_type,
            technical_domain=technical_domain,
            target_audience=target_audience
        )

        # Create agent and translate
        agent = OpenAITranslationAgent(
            gemini_client=get_gemini_client(),
            model=model
        )

        result = await agent.translate_with_agent(
            text=text,
            context=context,
            user_id=current_user.id if current_user else None
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "job_id": f"translate_{int(time.time())}",
                "translated_text": result["translated_text"],
                "status": "completed",
                "progress": 100.0,
                "chunks": [],
                "processing_time_ms": 0,
                "cached": False,
                "input_tokens": result.get("tokens_used", 0),
                "output_tokens": 0,
                "estimated_cost_usd": 0.0,
                "confidence_score": result.get("confidence_score", 0.95)
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "TRANSLATION_ERROR",
                "message": "Failed to translate text"
            }
        )


@router.post("/translate/agent")
async def translate_with_agent(
    request: dict,
    http_request: Request,
    current_user: Optional[User] = Depends(get_current_user_or_anonymous)
) -> JSONResponse:
    """
    Translate text using OpenAI Agents SDK directly with caching.

    This endpoint uses the OpenAI Agents SDK for translation with enhanced
    context awareness and proper Runner.run pattern. Translations are cached
    for 1 week to avoid redundant API calls.

    Args:
        request: Translation request
        http_request: FastAPI request object
        current_user: Optional current user

    Returns:
        Translation result with detailed metadata
    """
    try:
        # Extract request parameters
        text = request.get("text", "")
        source_language = request.get("source_language", "en")
        target_language = request.get("target_language", "ur")
        page_url = request.get("page_url")
        model = request.get("model", "gemini-2.0-flash-lite")

        # Check cache first
        cached_result = await cache_service.get_cached_translation(
            text=text,
            source_language=source_language,
            target_language=target_language,
            page_url=page_url
        )

        if cached_result:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "translated_text": cached_result["translated_text"],
                    "original_text": cached_result["original_text"],
                    "cached": True,
                    "cache_created_at": cached_result["cache_created_at"],
                    "cache_expires_at": cached_result["cache_expires_at"],
                    "hit_count": cached_result["hit_count"],
                    "tokens_used": 0,  # No tokens used for cached result
                    "model": cached_result["model"],
                    "confidence_score": cached_result["confidence_score"],
                    "has_code_blocks": False,  # Would need to be stored in cache
                    "code_blocks": []  # Would need to be stored in cache
                }
            )

        # Not in cache, proceed with translation
        # Create translation context
        context = TranslationContext(
            page_url=page_url,
            document_type=request.get("document_type"),
            technical_domain=request.get("technical_domain"),
            target_audience=request.get("target_audience")
        )

        # Create agent and translate
        agent = OpenAITranslationAgent(
            gemini_client=get_gemini_client(),
            model=model
        )

        start_time = time.time()
        result = await agent.translate_with_agent(
            text=text,
            context=context,
            user_id=current_user.id if current_user else None
        )
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Cache the translation result
        await cache_service.cache_translation(
            text=text,
            translated_text=result["translated_text"],
            source_language=source_language,
            target_language=target_language,
            model=result.get("model", model),
            confidence_score=result.get("confidence_score", 0.95),
            processing_time_ms=processing_time_ms,
            page_url=page_url
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "translated_text": result["translated_text"],
                "original_text": result["original_text"],
                "cached": False,
                "tokens_used": result.get("tokens_used", 0),
                "model": result.get("model", model),
                "confidence_score": result.get("confidence_score", 0.95),
                "has_code_blocks": result.get("has_code_blocks", False),
                "code_blocks": result.get("code_blocks", []),
                "processing_time_ms": processing_time_ms
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "AGENT_TRANSLATION_ERROR",
                "message": "Failed to translate text using agent"
            }
        )


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Simple health check endpoint for translation service.

    Returns:
        Health status
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "translation",
            "version": "2.0.0",
            "features": ["openai_agents_sdk", "gemini_api", "translation_cache"]
        }
    )


@router.post("/cache/clear-expired")
async def clear_expired_cache(
    current_user: Optional[User] = Depends(get_current_user_or_anonymous)
) -> JSONResponse:
    """
    Clear expired cache entries.

    Returns:
        Number of cleared entries
    """
    try:
        cleared_count = await cache_service.clear_expired_cache()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Cleared {cleared_count} expired cache entries",
                "cleared_count": cleared_count
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "CACHE_CLEAR_ERROR",
                "message": "Failed to clear expired cache"
            }
        )


@router.post("/cache/clear-url")
async def clear_cache_by_url(
    request: dict,
    current_user: Optional[User] = Depends(get_current_user_or_anonymous)
) -> JSONResponse:
    """
    Clear cache entries for a specific URL.

    Args:
        request: Dict containing 'url' and optional 'source_language' and 'target_language'

    Returns:
        Number of cleared entries
    """
    try:
        url = request.get("url")
        if not url:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "INVALID_REQUEST",
                    "message": "URL is required"
                }
            )

        source_language = request.get("source_language")
        target_language = request.get("target_language")

        cleared_count = await cache_service.clear_cache_by_url(
            page_url=url,
            source_language=source_language,
            target_language=target_language
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Cleared {cleared_count} cache entries for URL",
                "url": url,
                "cleared_count": cleared_count
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "CACHE_CLEAR_URL_ERROR",
                "message": "Failed to clear cache for URL"
            }
        )


@router.post("/cache/clear-all")
async def clear_all_cache(
    current_user: Optional[User] = Depends(get_current_user_or_anonymous)
) -> JSONResponse:
    """
    Clear ALL translation cache entries.
    Useful for resetting cache on deployment.
    """
    try:
        # Assuming cache_service has a method or we access DB directly
        # Since cache_service is imported, let's check if it has clear_all
        # If not, we might need to add it to cache_service first.
        # Checking previous files, CacheService in services/translation_cache.py wasn't read fully.
        # But OpenAITranslationService has clear_cache(older_than_hours=None).
        
        # We'll use the cache_service instance.
        # If cache_service.clear_all() exists? Probably not.
        # Let's try to use clear_expired_cache with 0 hours expiration if possible?
        # Or just access DB.
        
        # To be safe and follow pattern, let's implement it directly here using cache_service's session if exposed,
        # or better, add clear_all to CacheService in a separate step? 
        # The user asked for a script, I gave one. Now adding endpoint.
        # I'll simply use the logic from the script but inside the endpoint.
        
        from src.models.translation_openai import TranslationCache
        from src.database.config import get_db
        
        db_gen = get_db()
        db = next(db_gen)
        try:
            count = db.query(TranslationCache).delete()
            db.commit()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": f"Cleared all {count} cache entries",
                    "cleared_count": count
                }
            )
        finally:
            db.close()

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "CACHE_CLEAR_ALL_ERROR",
                "message": f"Failed to clear all cache: {str(e)}"
            }
        )


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: Optional[User] = Depends(get_current_user_or_anonymous)
) -> JSONResponse:
    """
    Get translation cache statistics.

    Returns:
        Cache statistics
    """
    try:
        stats = await cache_service.get_cache_stats()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=stats
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "CACHE_STATS_ERROR",
                "message": "Failed to retrieve cache statistics"
            }
        )