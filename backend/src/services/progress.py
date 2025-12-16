"""
Reading progress service.

Tracks and manages user reading progress through chapters and sections.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from src.models.reading_progress import ReadingProgress
from src.models.auth import UserPreferences
from src.utils.errors import NotFoundError, ValidationError, handle_errors
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReadingProgressService:
    """Service for managing user reading progress."""

    def __init__(self, db: Session):
        self.db = db

    @handle_errors
    async def get_chapter_progress(
        self,
        user_id: str,
        chapter_id: str
    ) -> Dict[str, any]:
        """Get comprehensive progress for a chapter."""
        # Get all section progress for this chapter
        progress_records = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.chapter_id == chapter_id
        ).all()

        if not progress_records:
            return {
                "chapter_id": chapter_id,
                "overall_progress": 0.0,
                "sections_completed": 0,
                "total_sections": 0,
                "time_spent": 0,
                "sections": [],
                "last_accessed": None
            }

        # Calculate overall metrics
        sections = []
        total_position = 0
        sections_completed = 0
        total_time_spent = 0
        last_accessed = None

        for record in progress_records:
            section_data = {
                "section_id": record.section_id,
                "position": record.position,
                "completed": record.completed,
                "time_spent": record.time_spent,
                "last_accessed": record.last_accessed.isoformat() if record.last_accessed else None
            }
            sections.append(section_data)

            total_position += record.position
            if record.completed:
                sections_completed += 1
            total_time_spent += record.time_spent

            if record.last_accessed and (not last_accessed or record.last_accessed > last_accessed):
                last_accessed = record.last_accessed

        # Calculate overall progress
        total_sections = len(progress_records)
        overall_progress = (total_position / total_sections) if total_sections > 0 else 0

        return {
            "chapter_id": chapter_id,
            "overall_progress": round(overall_progress, 2),
            "sections_completed": sections_completed,
            "total_sections": total_sections,
            "time_spent": total_time_spent,
            "sections": sections,
            "last_accessed": last_accessed.isoformat() if last_accessed else None,
            "estimated_completion": self._estimate_completion(user_id, chapter_id)
        }

    @handle_errors
    async def update_section_progress(
        self,
        user_id: str,
        chapter_id: str,
        section_id: str,
        position: float,
        time_spent_delta: Optional[int] = None,
        completed: Optional[bool] = None
    ) -> ReadingProgress:
        """Update progress for a specific section."""
        # Validate inputs
        if not 0 <= position <= 100:
            raise ValidationError("Position must be between 0 and 100")

        # Find existing progress record
        progress = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.chapter_id == chapter_id,
            ReadingProgress.section_id == section_id
        ).first()

        if progress:
            # Update existing record
            progress.position = position
            progress.last_accessed = datetime.utcnow()

            if time_spent_delta is not None:
                progress.time_spent += time_spent_delta

            if completed is not None:
                progress.completed = completed
                if completed:
                    progress.position = 100

            logger.info(
                "Updated reading progress",
                user_id=user_id,
                chapter_id=chapter_id,
                section_id=section_id,
                position=position,
                time_spent_delta=time_spent_delta
            )
        else:
            # Create new progress record
            progress = ReadingProgress(
                id=str(uuid.uuid4()),
                user_id=user_id,
                chapter_id=chapter_id,
                section_id=section_id,
                position=position,
                completed=completed or False,
                time_spent=time_spent_delta or 0,
                last_accessed=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(progress)
            logger.info(
                "Created new reading progress",
                user_id=user_id,
                chapter_id=chapter_id,
                section_id=section_id,
                position=position
            )

        self.db.commit()
        self.db.refresh(progress)
        return progress

    @handle_errors
    async def mark_section_complete(
        self,
        user_id: str,
        chapter_id: str,
        section_id: str,
        time_spent_delta: Optional[int] = None
    ) -> ReadingProgress:
        """Mark a section as completed."""
        return await self.update_section_progress(
            user_id=user_id,
            chapter_id=chapter_id,
            section_id=section_id,
            position=100,
            time_spent_delta=time_spent_delta,
            completed=True
        )

    @handle_errors
    async def get_user_progress_summary(
        self,
        user_id: str
    ) -> Dict[str, any]:
        """Get overall progress summary for a user."""
        # Get all progress records
        progress_records = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id
        ).all()

        if not progress_records:
            return {
                "total_chapters_started": 0,
                "total_chapters_completed": 0,
                "total_sections_completed": 0,
                "total_time_spent": 0,
                "average_session_length": 0,
                "reading_streak": 0,
                "recent_activity": []
            }

        # Calculate metrics
        chapters_started = set()
        chapters_completed = set()
        sections_completed = 0
        total_time_spent = 0
        session_times = []

        # Group by chapter for analysis
        chapter_progress = {}
        for record in progress_records:
            chapters_started.add(record.chapter_id)

            if record.completed:
                sections_completed += 1

            if record.time_spent > 0:
                total_time_spent += record.time_spent
                session_times.append(record.time_spent)

            # Calculate chapter completion
            if record.chapter_id not in chapter_progress:
                chapter_progress[record.chapter_id] = {
                    "total_position": 0,
                    "total_sections": 0,
                    "completed_sections": 0
                }

            chapter_progress[record.chapter_id]["total_position"] += record.position
            chapter_progress[record.chapter_id]["total_sections"] += 1
            if record.completed:
                chapter_progress[record.chapter_id]["completed_sections"] += 1

        # Determine completed chapters (80% or more completion)
        for chapter_id, metrics in chapter_progress.items():
            completion_rate = metrics["total_position"] / metrics["total_sections"]
            if completion_rate >= 80:
                chapters_completed.add(chapter_id)

        # Calculate reading streak
        reading_streak = await self._calculate_reading_streak(user_id)

        # Get recent activity
        recent_activity = await self._get_recent_activity(user_id, limit=5)

        # Calculate averages
        average_session = sum(session_times) / len(session_times) if session_times else 0

        return {
            "total_chapters_started": len(chapters_started),
            "total_chapters_completed": len(chapters_completed),
            "total_sections_completed": sections_completed,
            "total_time_spent": total_time_spent,
            "average_session_length": round(average_session, 1),
            "reading_streak": reading_streak,
            "recent_activity": recent_activity,
            "progress_by_chapter": {
                chapter_id: {
                    "progress": round(metrics["total_position"] / metrics["total_sections"], 2),
                    "sections_total": metrics["total_sections"],
                    "sections_completed": metrics["completed_sections"]
                }
                for chapter_id, metrics in chapter_progress.items()
            }
        }

    @handle_errors
    async def get_reading_analytics(
        self,
        user_id: str,
        timeframe: str = "month"
    ) -> Dict[str, any]:
        """Get detailed reading analytics for a user."""
        # Calculate date range
        end_date = datetime.utcnow()
        if timeframe == "day":
            start_date = end_date - timedelta(days=1)
        elif timeframe == "week":
            start_date = end_date - timedelta(weeks=1)
        elif timeframe == "year":
            start_date = end_date - timedelta(days=365)
        else:  # month
            start_date = end_date - timedelta(days=30)

        # Get progress records within timeframe
        progress_records = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.last_accessed >= start_date
        ).all()

        # Analyze reading patterns
        daily_reading = {}
        hourly_reading = {str(i): 0 for i in range(24)}
        total_time = 0
        total_sessions = len(progress_records)

        for record in progress_records:
            if record.last_accessed:
                day = record.last_accessed.strftime("%Y-%m-%d")
                hour = record.last_accessed.strftime("%H")

                if day not in daily_reading:
                    daily_reading[day] = {"time": 0, "sessions": 0}

                daily_reading[day]["time"] += record.time_spent
                daily_reading[day]["sessions"] += 1
                hourly_reading[hour] += record.time_spent
                total_time += record.time_spent

        # Find peak reading hours
        peak_hours = sorted(
            hourly_reading.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        # Calculate trends
        trend_data = await self._calculate_reading_trends(user_id, start_date, end_date)

        return {
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_time_spent": total_time,
            "total_sessions": total_sessions,
            "average_session_time": round(total_time / total_sessions, 1) if total_sessions > 0 else 0,
            "peak_reading_hours": [{"hour": int(h), "time": t} for h, t in peak_hours],
            "daily_breakdown": daily_reading,
            "trends": trend_data,
            "reading_velocity": await self._calculate_reading_velocity(user_id)
        }

    async def restore_progress(
        self,
        user_id: str,
        chapter_id: str
    ) -> Dict[str, any]:
        """Restore user's last position in a chapter."""
        # Get most recently accessed section
        last_progress = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.chapter_id == chapter_id
        ).order_by(desc(ReadingProgress.last_accessed)).first()

        if not last_progress:
            return {
                "chapter_id": chapter_id,
                "section_id": None,
                "position": 0,
                "message": "No previous progress found"
            }

        return {
            "chapter_id": chapter_id,
            "section_id": last_progress.section_id,
            "position": last_progress.position,
            "completed": last_progress.completed,
            "last_accessed": last_progress.last_accessed.isoformat(),
            "message": "Progress restored successfully"
        }

    # Private helper methods
    def _estimate_completion(
        self,
        user_id: str,
        chapter_id: str
    ) -> Optional[Dict[str, any]]:
        """Estimate when chapter will be completed based on reading patterns."""
        # Get recent reading pace
        recent_progress = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.last_accessed >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(ReadingProgress.last_accessed)).limit(10).all()

        if len(recent_progress) < 3:
            return None

        # Calculate average reading speed
        total_position = sum(p.position for p in recent_progress)
        avg_position_per_session = total_position / len(recent_progress)

        # Get current progress
        current_progress = await self.get_chapter_progress(user_id, chapter_id)
        remaining = 100 - current_progress["overall_progress"]

        if avg_position_per_session > 0:
            sessions_needed = remaining / avg_position_per_session
            # Estimate days based on recent activity frequency
            days_between_sessions = self._calculate_avg_days_between_sessions(recent_progress)
            estimated_days = sessions_needed * days_between_sessions

            estimated_completion = datetime.utcnow() + timedelta(days=estimated_days)

            return {
                "estimated_completion_date": estimated_completion.isoformat(),
                "sessions_needed": max(1, round(sessions_needed)),
                "confidence": "medium" if len(recent_progress) >= 5 else "low"
            }

        return None

    def _calculate_reading_streak(self, user_id: str) -> int:
        """Calculate consecutive days of reading."""
        # Get last 30 days of activity
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        progress_records = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.last_accessed >= thirty_days_ago
        ).distinct(ReadingProgress.last_accessed).all()

        if not progress_records:
            return 0

        # Get unique reading days
        reading_days = {
            record.last_accessed.date()
            for record in progress_records
            if record.last_accessed
        }

        # Sort days in descending order
        sorted_days = sorted(reading_days, reverse=True)

        # Calculate streak
        streak = 0
        current_date = datetime.utcnow().date()

        for day in sorted_days:
            if day == current_date - timedelta(days=streak):
                streak += 1
            else:
                break

        return streak

    async def _get_recent_activity(self, user_id: str, limit: int = 5) -> List[Dict[str, any]]:
        """Get recent reading activity."""
        recent_progress = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id
        ).order_by(desc(ReadingProgress.last_accessed)).limit(limit).all()

        return [
            {
                "chapter_id": record.chapter_id,
                "section_id": record.section_id,
                "position": record.position,
                "completed": record.completed,
                "time_spent": record.time_spent,
                "timestamp": record.last_accessed.isoformat()
            }
            for record in recent_progress
        ]

    async def _calculate_reading_trends(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, any]:
        """Calculate reading trends over time."""
        # Get progress grouped by week
        progress_records = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.last_accessed >= start_date,
            ReadingProgress.last_accessed <= end_date
        ).all()

        # Group by week
        weekly_data = {}
        for record in progress_records:
            week = record.last_accessed.isocalendar()[1]  # ISO week number
            year = record.last_accessed.isocalendar()[0]
            week_key = f"{year}-W{week:02d}"

            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "time_spent": 0,
                    "sections_completed": 0,
                    "sessions": 0
                }

            weekly_data[week_key]["time_spent"] += record.time_spent
            if record.completed:
                weekly_data[week_key]["sections_completed"] += 1
            weekly_data[week_key]["sessions"] += 1

        return {
            "weekly_breakdown": weekly_data,
            "trend": "increasing" if len(weekly_data) > 1 else "stable"
        }

    def _calculate_reading_velocity(self, user_id: str) -> Dict[str, float]:
        """Calculate reading velocity (chapters per month)."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Get chapters completed in last 30 days
        completed_chapters = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.completed == True,
            ReadingProgress.last_accessed >= thirty_days_ago
        ).distinct(ReadingProgress.chapter_id).count()

        return {
            "chapters_per_month": float(completed_chapters),
            "section_completion_rate": 0.0  # Calculate based on total sections
        }

    def _calculate_avg_days_between_sessions(self, progress_records: List[ReadingProgress]) -> float:
        """Calculate average days between reading sessions."""
        if len(progress_records) < 2:
            return 1.0  # Default to 1 day if insufficient data

        # Sort by last_accessed
        sorted_records = sorted(
            progress_records,
            key=lambda x: x.last_accessed
        )

        # Calculate days between consecutive sessions
        days_between = []
        for i in range(1, len(sorted_records)):
            days = (sorted_records[i].last_accessed - sorted_records[i-1].last_accessed).days
            if days > 0:  # Ignore multiple sessions in same day
                days_between.append(days)

        return sum(days_between) / len(days_between) if days_between else 1.0


# Dependency injection function
def get_progress_service(db: Session) -> ReadingProgressService:
    """Get progress service instance."""
    return ReadingProgressService(db)