"""
Personalization service for adaptive content delivery.

Provides content adaptation based on user experience level and preferences.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import hashlib
import time

from sqlalchemy.orm import Session
from fastapi import Depends
from src.database.base import get_db
from src.models.reading_progress import ReadingProgress
from src.models.personalization import SavedPersonalization
from src.models.auth import User, UserBackground, UserPreferences
from src.utils.errors import NotFoundError, ValidationError
from src.utils.logging import get_logger
from src.agents.personalization_agent import PersonalizationAgent
from src.cache.personalization import get_personalization_cache

logger = get_logger(__name__)


class PersonalizationService:
    """Service for personalizing content based on user preferences and behavior."""

    def __init__(self, db: Session):
        self.db = db

    # Experience level definitions
    EXPERIENCE_LEVELS = {
        "beginner": {
            "complexity_threshold": 0.3,
            "max_concepts_per_section": 3,
            "include_prerequisites": True,
            "simplify_explanations": True,
            "code_examples": "basic",
            "reading_speed_factor": 0.8
        },
        "intermediate": {
            "complexity_threshold": 0.6,
            "max_concepts_per_section": 5,
            "include_prerequisites": False,
            "simplify_explanations": False,
            "code_examples": "standard",
            "reading_speed_factor": 1.0
        },
        "advanced": {
            "complexity_threshold": 0.8,
            "max_concepts_per_section": 8,
            "include_prerequisites": False,
            "simplify_explanations": False,
            "code_examples": "advanced",
            "reading_speed_factor": 1.3
        }
    }

    async def get_user_personalization(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get personalization settings for a user."""
        # Get user preferences
        preferences = self.db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()

        if not preferences:
            # Create default preferences
            preferences = await self._create_default_preferences(user_id)

        # Analyze user's reading patterns to determine experience level
        experience_level = await self._determine_experience_level(user_id)

        # Get personalization config
        config = self.EXPERIENCE_LEVELS.get(experience_level, self.EXPERIENCE_LEVELS["intermediate"])

        return {
            "experience_level": experience_level,
            "preferences": {
                "language": preferences.language,
                "reading_pace": preferences.reading_pace,
                "preferred_depth": preferences.preferred_depth,
                "show_code_examples": preferences.show_code_examples,
                "adaptive_difficulty": preferences.adaptive_difficulty,
                "theme": preferences.theme,
                "font_size": preferences.font_size,
                "line_height": preferences.line_height,
            },
            "adaptation": {
                "complexity_threshold": config["complexity_threshold"],
                "max_concepts": config["max_concepts_per_section"],
                "include_prerequisites": config["include_prerequisites"],
                "simplify_explanations": config["simplify_explanations"],
                "code_example_level": config["code_examples"],
                "reading_speed_factor": config["reading_speed_factor"],
            }
        }

    async def adapt_content(
        self,
        content: Dict[str, Any],
        user_id: str,
        section_id: str = None
    ) -> Dict[str, Any]:
        """Adapt content based on user's personalization."""
        personalization = await self.get_user_personalization(user_id)
        config = personalization["adaptation"]

        # Get section-specific progress if available
        section_progress = None
        if section_id:
            progress = self.db.query(ReadingProgress).filter(
                ReadingProgress.user_id == user_id,
                ReadingProgress.section_id == section_id
            ).first()
            if progress:
                section_progress = {
                    "position": progress.position,
                    "time_spent": progress.time_spent,
                    "completed": progress.completed
                }

        # Adapt content based on personalization
        adapted_content = {
            "original_content": content,
            "adaptations": {
                "content_level": personalization["experience_level"],
                "simplified": config["simplify_explanations"],
                "concepts_limited": True if len(content.get("concepts", [])) > config["max_concepts"] else False,
            },
            "metadata": {
                "user_id": user_id,
                "adapted_at": datetime.utcnow().isoformat(),
                "section_progress": section_progress,
            }
        }

        # Filter concepts if needed
        if "concepts" in content and len(content["concepts"]) > config["max_concepts"]:
            # Prioritize concepts based on difficulty and relevance
            concepts = sorted(
                content["concepts"],
                key=lambda c: (c.get("difficulty", 0.5), c.get("relevance", 0.5)),
                reverse=True
            )
            adapted_content["concepts"] = concepts[:config["max_concepts"]]
            adapted_content["filtered_concepts"] = True

        # Simplify explanations if needed
        if config["simplify_explanations"] and "explanation" in content:
            adapted_content["explanation"] = self._simplify_text(
                content["explanation"],
                personalization["experience_level"]
            )

        # Adjust code examples
        if "code_examples" in content and personalization["preferences"]["show_code_examples"]:
            adapted_content["code_examples"] = self._adapt_code_examples(
                content["code_examples"],
                config["code_example_level"],
                personalization["experience_level"]
            )

        # Calculate reading time estimate
        adapted_content["estimated_reading_time"] = self._calculate_reading_time(
            adapted_content,
            config["reading_speed_factor"],
            personalization["preferences"]["reading_pace"]
        )

        return adapted_content

    async def generate_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate personalized content recommendations based on user progress."""
        # Get user's reading progress
        completed_sections = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.completed == True
        ).all()

        # Get current progress
        current_progress = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.completed == False
        ).order_by(ReadingProgress.last_accessed.desc()).limit(5).all()

        personalization = await self.get_user_personalization(user_id)
        experience_level = personalization["experience_level"]
        preferred_depth = personalization["preferences"]["preferred_depth"]

        recommendations = []

        # Recommendation strategies
        if current_progress:
            # Recommend continuing with current chapter
            for progress in current_progress:
                recommendations.append({
                    "type": "continue_reading",
                    "title": f"Continue {progress.chapter_id}",
                    "description": f"You're {progress.position:.0f}% through this section",
                    "chapter_id": progress.chapter_id,
                    "section_id": progress.section_id,
                    "priority": "high",
                    "reason": "in_progress"
                })

        # Recommend next chapters based on completion
        if completed_sections:
            completed_chapters = set(p.chapter_id for p in completed_sections)

            # Simulated content catalog - in real implementation, query from content database
            all_chapters = [
                {"id": "ch1", "title": "Introduction to AI", "difficulty": 0.2, "prerequisites": []},
                {"id": "ch2", "title": "Machine Learning Basics", "difficulty": 0.4, "prerequisites": ["ch1"]},
                {"id": "ch3", "title": "Neural Networks", "difficulty": 0.6, "prerequisites": ["ch2"]},
                {"id": "ch4", "title": "Deep Learning", "difficulty": 0.7, "prerequisites": ["ch3"]},
                {"id": "ch5", "title": "Computer Vision", "difficulty": 0.8, "prerequisites": ["ch1", "ch3"]},
            ]

            for chapter in all_chapters:
                if chapter["id"] not in completed_chapters:
                    # Check prerequisites
                    can_access = all(
                        prereq in completed_chapters
                        for prereq in chapter.get("prerequisites", [])
                    )

                    if can_access:
                        # Check if difficulty matches user level
                        difficulty_match = self._check_difficulty_match(
                            chapter["difficulty"],
                            experience_level
                        )

                        if difficulty_match:
                            recommendations.append({
                                "type": "next_chapter",
                                "title": chapter["title"],
                                "description": f"Next chapter in your learning path",
                                "chapter_id": chapter["id"],
                                "section_id": None,
                                "priority": "medium" if len(completed_chapters) > 0 else "high",
                                "reason": "sequential_learning"
                            })

        # Recommend based on preferred depth
        if preferred_depth == "overview":
            recommendations = [
                r for r in recommendations
                if r.get("type") in ["continue_reading", "next_chapter"]
            ][:3]
        elif preferred_depth == "comprehensive":
            # Add additional resources for comprehensive learners
            recommendations.extend([
                {
                    "type": "additional_resources",
                    "title": "Deep Dive Resources",
                    "description": "Additional materials for comprehensive understanding",
                    "url": f"/resources/{exp}/deep-dive",
                    "priority": "low",
                    "reason": "depth_preference"
                }
                for exp in experience_level
            ])

        # Sort by priority and limit
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(
            key=lambda r: priority_order.get(r.get("priority", "low"), 1),
            reverse=True
        )

        return recommendations[:limit]

    async def _create_default_preferences(self, user_id: str) -> UserPreferences:
        """Create default user preferences."""
        preferences = UserPreferences(
            id=str(uuid.uuid4()),
            user_id=user_id,
            language="en",
            reading_pace="medium",
            preferred_depth="detailed",
            show_code_examples=True,
            adaptive_difficulty=False,
            theme="auto",
            font_size=16,
            line_height=1.5
        )

        self.db.add(preferences)
        self.db.commit()
        self.db.refresh(preferences)

        return preferences

    async def _determine_experience_level(self, user_id: str) -> str:
        """Determine user's experience level based on reading patterns."""
        # Get user's reading statistics
        progress_records = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id
        ).all()

        if not progress_records:
            return "beginner"

        # Calculate metrics
        total_sections = len(progress_records)
        completed_sections = len([p for p in progress_records if p.completed])
        avg_time_per_section = sum(p.time_spent for p in progress_records) / max(total_sections, 1)

        # Determine experience level
        if total_sections < 3:
            return "beginner"
        elif completed_sections / total_sections > 0.8 and avg_time_per_section > 20:
            return "advanced"
        else:
            return "intermediate"

    def _simplify_text(self, text: str, experience_level: str) -> str:
        """Simplify text based on experience level."""
        if experience_level == "beginner":
            # Add more explanations and simplify complex terms
            # This is a placeholder - in real implementation, use NLP
            sentences = text.split('. ')
            simplified = []
            for sentence in sentences:
                if len(sentence.split()) > 15:
                    # Long sentence - potentially complex
                    simplified.append(sentence + " (This means: " + sentence[:50] + "...)")
                else:
                    simplified.append(sentence)
            return '. '.join(simplified)
        return text

    def _adapt_code_examples(
        self,
        examples: List[Dict[str, Any]],
        level: str,
        experience_level: str
    ) -> List[Dict[str, Any]]:
        """Adapt code examples based on level and experience."""
        adapted = []

        for example in examples:
            adapted_example = example.copy()

            if level == "basic" and experience_level == "beginner":
                # Add more comments to code
                if "code" in example:
                    lines = example["code"].split('\n')
                    commented_lines = []
                    for line in lines:
                        if line.strip() and not line.strip().startswith('//'):
                            commented_lines.append(f"// {line.strip()}")  # Simplified
                            commented_lines.append(line)
                        else:
                            commented_lines.append(line)
                    adapted_example["code"] = '\n'.join(commented_lines)

            adapted.append(adapted_example)

        return adapted

    def _calculate_reading_time(
        self,
        content: Dict[str, Any],
        speed_factor: float,
        reading_pace: str
    ) -> int:
        """Calculate estimated reading time in minutes."""
        # Get word count (simulated)
        word_count = len(str(content.get("content", "")).split())

        # Base reading speed (words per minute)
        base_speed = {
            "slow": 150,
            "medium": 250,
            "fast": 400
        }.get(reading_pace, 250)

        # Adjust for experience level and content complexity
        adjusted_speed = base_speed * speed_factor

        # Calculate time
        time_minutes = max(1, round(word_count / adjusted_speed))

        return time_minutes

    def _check_difficulty_match(self, content_difficulty: float, experience_level: str) -> bool:
        """Check if content difficulty matches user's experience level."""
        level_difficulties = {
            "beginner": (0.0, 0.5),
            "intermediate": (0.3, 0.7),
            "advanced": (0.5, 1.0)
        }

        min_diff, max_diff = level_difficulties.get(experience_level, (0.0, 1.0))
        return min_diff <= content_difficulty <= max_diff


class PersonalizationEngine:
    """
    Service for orchestrating content personalization using AI agents
    """

    def __init__(self, db: Session):
        """
        Initialize the personalization engine

        Args:
            db: Database session
        """
        self.db = db
        self.agent = PersonalizationAgent()
        self.cache = get_personalization_cache()

    async def personalize_content(
        self,
        content: str,
        user_id: str,
        context: Optional[str] = None,
        save_result: bool = False,
        target_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Personalize content for a user

        Args:
            content: The original content to personalize
            user_id: The user ID
            context: Additional context about the content
            save_result: Whether to save the result
            target_length: Target word count for personalized content

        Returns:
            Dictionary with personalized content and metadata
        """
        # Get user and their background
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        # Get user background or use defaults
        user_profile = await self._get_user_profile(user)

        # Check cache first
        cache_key_data = {
            "content": content,
            "context": context,
            "target_length": target_length
        }
        cached_result = await self.cache.get(
            json.dumps(cache_key_data, sort_keys=True),
            user_profile
        )
        if cached_result:
            logger.info(f"Cache hit for user {user_id}")
            return cached_result

        # Start timing
        start_time = time.time()

        try:
            # Generate personalized content
            result = await self.agent.personalize_content(
                content=content,
                user_profile=user_profile
            )

            if result.get("error"):
                logger.error(f"Personalization failed for user {user_id}: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "personalized_content": None,
                    "adaptations_made": []
                }

            # Calculate processing time
            processing_time = time.time() - start_time

            # Add metadata
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Prepare response
            response = {
                "success": True,
                "personalized_content": result["personalized_content"],
                "adaptations_made": result["adaptations_made"],
                "original_length": result["original_length"],
                "personalized_length": result["personalized_length"],
                "processing_time": processing_time,
                "content_hash": content_hash,
                "user_profile": {
                    "experience_level": user_profile.get("experience_level"),
                    "primary_expertise": user_profile.get("primary_expertise"),
                    "hardware_expertise": user_profile.get("hardware_expertise")
                },
                "tokens_used": 0  # Would be populated by agent response
            }

            # Cache the result
            await self.cache.set(
                json.dumps(cache_key_data, sort_keys=True),
                user_profile,
                response,
                ttl=3600  # 1 hour cache
            )

            # Save if requested
            if save_result:
                saved_id = await self._save_personalization(
                    user_id=user_id,
                    content_hash=content_hash,
                    content_url=context or "",
                    content_title="Personalized Content",
                    personalized_content=response["personalized_content"],
                    personalization_metadata={
                        "target_length": target_length,
                        "processing_time": processing_time
                    },
                    adaptations_applied=response["adaptations_made"]
                )
                response["saved_id"] = saved_id

            # Update user stats
            await self._update_user_stats(user_id)

            logger.info(
                f"Successfully personalized content for user {user_id}",
                processing_time=processing_time,
                adaptations=len(response["adaptations_made"])
            )

            return response

        except Exception as e:
            logger.error(f"Unexpected error in personalization: {str(e)}")
            return {
                "success": False,
                "error": "An unexpected error occurred during personalization",
                "personalized_content": None,
                "adaptations_made": []
            }

    async def _get_user_profile(self, user: User) -> Dict[str, Any]:
        """
        Get user's profile for personalization

        Args:
            user: User object

        Returns:
            User profile dictionary
        """
        # Get user background if available
        profile = {}
        if hasattr(user, 'background') and user.background:
            # Handle experience level - normalize to lowercase for consistency
            exp_level = user.background.experience_level.value if user.background.experience_level else "intermediate"
            exp_level = exp_level.lower() if exp_level else "intermediate"

            profile = {
                "experience_level": exp_level,
                "years_of_experience": user.background.years_of_experience or 0,
                "primary_expertise": user.background.primary_interest or "general",
                "hardware_expertise": user.background.hardware_expertise.value if user.background.hardware_expertise else "none",
                "preferred_languages": user.background.preferred_languages or []
            }
        else:
            # Default profile for users without background
            profile = {
                "experience_level": "intermediate",
                "years_of_experience": 0,
                "primary_expertise": "general",
                "hardware_expertise": "none",
                "preferred_languages": []
            }

        return profile

    async def _save_personalization(
        self,
        user_id: str,
        content_hash: str,
        content_url: str,
        content_title: str,
        personalized_content: str,
        personalization_metadata: Dict[str, Any],
        adaptations_applied: List[str]
    ) -> str:
        """
        Save personalized content to database

        Args:
            user_id: User ID
            content_hash: Hash of original content
            content_url: URL of original content
            content_title: Title of the content
            personalized_content: The personalized content
            personalization_metadata: Metadata about personalization
            adaptations_applied: List of adaptations applied

        Returns:
            ID of saved personalization
        """
        try:
            # Check if already exists
            existing = self.db.query(SavedPersonalization).filter(
                SavedPersonalization.user_id == user_id,
                SavedPersonalization.original_content_hash == content_hash
            ).first()

            if existing:
                # Update existing
                existing.personalized_content = personalized_content
                existing.personalization_metadata = personalization_metadata
                existing.adaptations_applied = adaptations_applied
                existing.last_accessed = datetime.utcnow()
                self.db.commit()
                logger.info(f"Updated existing personalization for user {user_id}")
                return str(existing.id)
            else:
                # Create new
                saved = SavedPersonalization(
                    user_id=user_id,
                    original_content_hash=content_hash,
                    content_url=content_url,
                    content_title=content_title,
                    personalized_content=personalized_content,
                    personalization_metadata=personalization_metadata,
                    adaptations_applied=adaptations_applied
                )
                self.db.add(saved)
                self.db.commit()
                logger.info(f"Saved new personalization for user {user_id}")
                return str(saved.id)

        except Exception as e:
            logger.error(f"Failed to save personalization: {str(e)}")
            return None

    async def _update_user_stats(self, user_id: str) -> None:
        """
        Update user's personalization statistics

        Args:
            user_id: User ID to update stats for
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                # Update total personalizations if column exists
                if hasattr(user, 'total_personalizations'):
                    user.total_personalizations += 1
                self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update user stats: {str(e)}")

    async def get_saved_personalizations(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get user's saved personalizations

        Args:
            user_id: User ID
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with saved personalizations
        """
        try:
            query = self.db.query(SavedPersonalization).filter(
                SavedPersonalization.user_id == user_id
            ).order_by(SavedPersonalization.created_at.desc())

            total = query.count()
            saved = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                "personalizations": [
                    {
                        "id": str(item.id),
                        "content_title": item.content_title,
                        "content_url": item.content_url,
                        "user_rating": item.user_rating,
                        "created_at": item.created_at.isoformat(),
                        "last_accessed": item.last_accessed.isoformat(),
                        "adaptations_applied": item.adaptations_applied
                    }
                    for item in saved
                ],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f"Failed to get saved personalizations: {str(e)}")
            return {"personalizations": [], "total": 0, "page": 1, "per_page": 10, "total_pages": 0}

    async def delete_saved_personalization(
        self,
        user_id: str,
        personalization_id: str
    ) -> bool:
        """
        Delete a saved personalization

        Args:
            user_id: User ID
            personalization_id: Personalization ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            saved = self.db.query(SavedPersonalization).filter(
                SavedPersonalization.id == personalization_id,
                SavedPersonalization.user_id == user_id
            ).first()

            if saved:
                self.db.delete(saved)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete personalization: {str(e)}")
            return False

    async def rate_saved_personalization(
        self,
        user_id: str,
        personalization_id: str,
        rating: int,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Rate a saved personalization

        Args:
            user_id: User ID
            personalization_id: Personalization ID to rate
            rating: Rating (1-5)
            feedback: Optional feedback text

        Returns:
            True if rated successfully
        """
        try:
            saved = self.db.query(SavedPersonalization).filter(
                SavedPersonalization.id == personalization_id,
                SavedPersonalization.user_id == user_id
            ).first()

            if saved:
                saved.user_rating = max(1, min(5, rating))
                if feedback:
                    saved.user_feedback = feedback
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to rate personalization: {str(e)}")
            return False


# Dependency injection function
def get_personalization_service(db: Session = Depends(get_db)) -> PersonalizationService:
    """Get personalization service instance."""
    return PersonalizationService(db)


def get_personalization_engine(db: Session = Depends(get_db)) -> PersonalizationEngine:
    """Get personalization engine instance."""
    return PersonalizationEngine(db)