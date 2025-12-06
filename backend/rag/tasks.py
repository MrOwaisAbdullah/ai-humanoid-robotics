"""
Task management system for RAG backend.

Handles ingestion task tracking, status updates, and progress monitoring.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import asyncio
from enum import Enum

from .models import IngestionTask, IngestionTaskStatus

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskManager:
    """Manages background tasks for the RAG system."""

    def __init__(
        self,
        max_concurrent_tasks: int = 5,
        task_timeout: int = 3600,  # 1 hour
        cleanup_interval: int = 300  # 5 minutes
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_timeout = task_timeout
        self.cleanup_interval = cleanup_interval

        # Task storage
        self.tasks: Dict[str, IngestionTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # Start cleanup task
        self.cleanup_task = None

    async def start(self):
        """Start the task manager."""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Task manager started")

    async def stop(self):
        """Stop the task manager and cancel all running tasks."""
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None

        # Cancel all running tasks
        for task_id, task in self.running_tasks.items():
            task.cancel()
            self._update_task_status(task_id, IngestionTaskStatus.CANCELLED)

        self.running_tasks.clear()
        logger.info("Task manager stopped")

    async def create_ingestion_task(
        self,
        content_path: str,
        force_reindex: bool = False,
        batch_size: int = 100,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Create a new ingestion task.

        Args:
            content_path: Path to content directory
            force_reindex: Whether to force reindexing
            batch_size: Batch size for processing
            priority: Task priority

        Returns:
            Task ID
        """
        task_id = f"ingest_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"

        task = IngestionTask(
            task_id=task_id,
            content_path=content_path,
            status=IngestionTaskStatus.PENDING,
            metadata={
                "force_reindex": force_reindex,
                "batch_size": batch_size,
                "priority": priority.value
            }
        )

        self.tasks[task_id] = task
        logger.info(f"Created ingestion task: {task_id}")

        # Try to execute task immediately if capacity allows
        await self._try_execute_task(task_id)

        return task_id

    async def execute_ingestion_task(
        self,
        task_id: str,
        ingestor,
        progress_callback: Optional[callable] = None
    ):
        """
        Execute an ingestion task.

        Args:
            task_id: Task identifier
            ingestor: DocumentIngestor instance
            progress_callback: Optional callback for progress updates
        """
        if task_id not in self.tasks:
            logger.error(f"Task not found: {task_id}")
            return

        task = self.tasks[task_id]

        try:
            # Update task status
            self._update_task_status(task_id, IngestionTaskStatus.RUNNING)
            task.started_at = datetime.utcnow()

            # Get task parameters
            content_path = task.content_path
            force_reindex = task.metadata.get("force_reindex", False)
            batch_size = task.metadata.get("batch_size", 100)

            # Progress tracking
            def progress_update(progress: float, message: str):
                task.progress = progress
                task.updated_at = datetime.utcnow()
                if progress_callback:
                    progress_callback(task_id, progress, message)

            # Execute ingestion
            logger.info(f"Executing ingestion task: {task_id}")
            result = await ingestor.ingest_directory(
                content_path
            )

            # Update task with results
            task.status = IngestionTaskStatus.COMPLETED
            task.progress = 100.0
            task.documents_found = len(ingestor._find_markdown_files(content_path, "*.md*", True))
            task.documents_processed = result.get("files_processed", 0)
            task.chunks_created = result.get("chunks_created", 0)
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()

            # Add errors if any
            errors = result.get("errors", [])
            if errors:
                task.errors.extend(errors)
                logger.warning(f"Task {task_id} completed with {len(errors)} errors")

            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            # Update task with error
            task.status = IngestionTaskStatus.FAILED
            task.errors.append(str(e))
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()

            logger.error(f"Task {task_id} failed: {str(e)}")

        finally:
            # Remove from running tasks
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

            # Try to execute pending tasks
            await self._process_pending_tasks()

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        # Can only cancel pending or running tasks
        if task.status not in [IngestionTaskStatus.PENDING, IngestionTaskStatus.RUNNING]:
            return False

        # Cancel if running
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]

        # Update status
        task.status = IngestionTaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()

        logger.info(f"Cancelled task: {task_id}")
        return True

    def get_task(self, task_id: str) -> Optional[IngestionTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_tasks(
        self,
        status: Optional[IngestionTaskStatus] = None,
        limit: Optional[int] = None
    ) -> List[IngestionTask]:
        """
        Get tasks, optionally filtered by status.

        Args:
            status: Optional status filter
            limit: Optional limit on number of tasks

        Returns:
            List of tasks
        """
        tasks = list(self.tasks.values())

        # Filter by status
        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # Apply limit
        if limit:
            tasks = tasks[:limit]

        return tasks

    def get_task_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        total_tasks = len(self.tasks)
        status_counts = {}

        for status in IngestionTaskStatus:
            count = sum(1 for t in self.tasks.values() if t.status == status)
            status_counts[status.value] = count

        return {
            "total_tasks": total_tasks,
            "running_tasks": len(self.running_tasks),
            "status_counts": status_counts,
            "max_concurrent": self.max_concurrent_tasks
        }

    async def _try_execute_task(self, task_id: str):
        """Try to execute a task if capacity allows."""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        # Check if we can execute more tasks
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            logger.info(f"Task queue full, task {task_id} will wait")
            return

        # Check task is pending
        if task.status != IngestionTaskStatus.PENDING:
            return

        # Get ingestor (this should be injected or managed better)
        # For now, we'll handle this in the main.py
        logger.info(f"Task {task_id} ready for execution")

    async def _process_pending_tasks(self):
        """Process pending tasks."""
        # Get pending tasks sorted by priority
        pending_tasks = [
            (tid, t) for tid, t in self.tasks.items()
            if t.status == IngestionTaskStatus.PENDING
        ]

        # Sort by priority (high first) and creation time (older first)
        pending_tasks.sort(
            key=lambda x: (
                -x[1].metadata.get("priority", TaskPriority.NORMAL.value),
                x[1].created_at
            )
        )

        # Execute as many as we can
        for task_id, task in pending_tasks:
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                break

            # Mark as running
            task.status = IngestionTaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()

            # Create asyncio task (actual execution happens elsewhere)
            logger.info(f"Marked task {task_id} as running")

    def _update_task_status(self, task_id: str, status: IngestionTaskStatus):
        """Update task status."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            task.updated_at = datetime.utcnow()

    async def _cleanup_loop(self):
        """Periodic cleanup of old tasks."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {str(e)}")

    async def _cleanup_old_tasks(self):
        """Clean up old completed tasks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Keep tasks for 24 hours

        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            # Remove old completed/failed/cancelled tasks
            if (
                task.status in [IngestionTaskStatus.COMPLETED, IngestionTaskStatus.FAILED, IngestionTaskStatus.CANCELLED]
                and task.completed_at
                and task.completed_at < cutoff_time
            ):
                tasks_to_remove.append(task_id)

            # Remove tasks that have been running too long
            elif (
                task.status == IngestionTaskStatus.RUNNING
                and task.started_at
                and (datetime.utcnow() - task.started_at).total_seconds() > self.task_timeout
            ):
                # Mark as failed
                self._update_task_status(task_id, IngestionTaskStatus.FAILED)
                task.errors.append("Task timeout")
                task.completed_at = datetime.utcnow()

                # Remove from running tasks
                if task_id in self.running_tasks:
                    self.running_tasks[task_id].cancel()
                    del self.running_tasks[task_id]

        # Remove old tasks
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            logger.info(f"Cleaned up old task: {task_id}")

        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")