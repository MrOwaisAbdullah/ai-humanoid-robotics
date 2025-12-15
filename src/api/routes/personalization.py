"""
Personalization API Routes
Handles content personalization endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime

from src.database.base import get_db
from src.security.dependencies import get_current_active_user
from src.models.auth import User

router = APIRouter(prefix="/personalization", tags=["personalization"])
security = HTTPBearer()


@router.get("/list")
async def list_personalizations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List saved personalizations for the current user.
    """
    # TODO: Implement actual database retrieval
    # For now, return empty list
    return {
        "personalizations": [],
        "total": 0,
        "message": "No saved personalizations found"
    }


@router.post("/generate")
async def generate_personalization(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a personalized explanation for the given content.
    """
    try:
        content = request.get("content", "")
        context_type = request.get("context_type", "page")
        word_count = request.get("word_count", 0)

        if not content.strip():
            raise HTTPException(
                status_code=400,
                detail="Content is required for personalization"
            )

        # TODO: Integrate with the actual personalization agent
        # For now, return a mock response
        mock_explanation = f"""
This is a personalized explanation for the {context_type} content you provided.

Based on your background and preferences, here's how this content relates to you:

The material discusses key concepts that build upon foundational knowledge in this field.
Since you're interested in this topic, consider how these principles might apply to
practical scenarios you might encounter.

Key takeaways:
- The content covers important theoretical foundations
- Practical applications are emphasized throughout
- This knowledge builds upon previously established concepts

Note: This is a placeholder response. The actual personalization feature will be
implemented with the OpenAI Agents SDK integration.
        """.strip()

        return {
            "explanation": mock_explanation,
            "context_type": context_type,
            "word_count": word_count,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate personalization: {str(e)}"
        )


@router.post("/save")
async def save_personalization(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Save a personalization for later reference.
    """
    try:
        content = request.get("content", "")
        explanation = request.get("explanation", "")
        context_type = request.get("context_type", "page")
        word_count = request.get("word_count", 0)

        if not explanation.strip():
            raise HTTPException(
                status_code=400,
                detail="Explanation is required to save personalization"
            )

        # TODO: Implement actual database save
        # For now, return a mock success response
        return {
            "id": f"pers_{datetime.utcnow().timestamp()}",
            "message": "Personalization saved successfully",
            "expires_at": datetime.utcnow().isoformat(),
            "title": content[:50] + "..." if len(content) > 50 else content
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save personalization: {str(e)}"
        )