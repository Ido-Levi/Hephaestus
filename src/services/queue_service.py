"""Queue service for managing agent concurrency and task queueing."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import and_

from src.core.database import DatabaseManager, Task, Agent

logger = logging.getLogger(__name__)


class QueueService:
    """Manages task queueing and agent concurrency limits."""

    def __init__(self, db_manager: DatabaseManager, max_concurrent_agents: int):
        """Initialize queue service.

        Args:
            db_manager: Database manager instance
            max_concurrent_agents: Maximum number of agents that can run concurrently
        """
        self.db_manager = db_manager
        self.max_concurrent_agents = max_concurrent_agents
        logger.info(f"QueueService initialized with max_concurrent_agents={max_concurrent_agents}")

    def get_active_agent_count(self) -> int:
        """Get count of currently active agents (not terminated).

        Returns:
            Number of active agents
        """
        session = self.db_manager.get_session()
        try:
            count = session.query(Agent).filter(
                Agent.status != "terminated"
            ).count()
            logger.debug(f"Active agent count: {count}")
            return count
        finally:
            session.close()

    def should_queue_task(self) -> bool:
        """Check if we should queue the next task instead of creating an agent.

        Returns:
            True if we've reached the concurrent agent limit, False otherwise
        """
        active_count = self.get_active_agent_count()
        should_queue = active_count >= self.max_concurrent_agents
        logger.debug(f"Should queue: {should_queue} (active={active_count}, max={self.max_concurrent_agents})")
        return should_queue

    def enqueue_task(self, task_id: str) -> None:
        """Mark a task as queued (or blocked if ticket is blocked).

        Args:
            task_id: ID of the task to enqueue
        """
        session = self.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found for enqueueing")
                return

            # Check if task's ticket is blocked
            if task.ticket_id:
                from src.services.task_blocking_service import TaskBlockingService

                blocking_info = TaskBlockingService.check_task_blocked(task_id)

                if blocking_info["is_blocked"]:
                    # Task's ticket is blocked - set status to 'blocked' instead of 'queued'
                    task.status = "blocked"
                    task.queued_at = None  # Don't set queued_at for blocked tasks

                    blocker_titles = [t["title"] for t in blocking_info["blocking_tickets"]]
                    reason = f"Blocked by tickets: {', '.join(blocker_titles)}"

                    # Store blocking reason in completion_notes
                    task.completion_notes = f"Blocked: {reason}"

                    session.commit()

                    logger.info(
                        f"Task {task_id} marked as 'blocked' (not queued) because ticket {task.ticket_id} "
                        f"is blocked by: {blocking_info['blocking_ticket_ids']}"
                    )
                    return

            # Task is not blocked - proceed with normal queueing
            task.status = "queued"
            task.queued_at = datetime.utcnow()

            session.commit()

            # Recalculate all queue positions to ensure correct ordering
            self._recalculate_queue_positions()

            # Get updated position
            session_refresh = self.db_manager.get_session()
            try:
                task_refreshed = session_refresh.query(Task).filter_by(id=task_id).first()
                position = task_refreshed.queue_position if task_refreshed else None
                logger.info(f"Task {task_id} queued at position {position}")
            finally:
                session_refresh.close()

        except Exception as e:
            logger.error(f"Failed to enqueue task {task_id}: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def _calculate_queue_position(self, session, new_task: Task) -> int:
        """Calculate position in queue based on priority.

        Queue order:
        1. priority_boosted (should not exist for new tasks, but included for completeness)
        2. priority (high > medium > low)
        3. queued_at (earlier first)

        Args:
            session: Database session
            new_task: The task being queued

        Returns:
            Queue position (1-indexed)
        """
        from sqlalchemy import case, or_

        # Define priority ordering using case statement
        priority_order = case(
            (Task.priority == "high", 3),
            (Task.priority == "medium", 2),
            (Task.priority == "low", 1),
            else_=2
        )

        new_priority_value = {"high": 3, "medium": 2, "low": 1}.get(new_task.priority, 2)

        # Count tasks ahead in the queue
        # A task is ahead if:
        # 1. It's boosted (and new task is not boosted), OR
        # 2. It has higher priority value, OR
        # 3. It has same priority value but was queued earlier
        ahead_count = session.query(Task).filter(
            Task.status == "queued",
            Task.id != new_task.id,
            or_(
                # Boosted tasks are always ahead (unless new task is also boosted)
                and_(Task.priority_boosted == True, new_task.priority_boosted == False),
                # Among non-boosted or both boosted: higher priority is ahead
                and_(
                    or_(
                        and_(Task.priority_boosted == True, new_task.priority_boosted == True),
                        and_(Task.priority_boosted == False, new_task.priority_boosted == False),
                    ),
                    priority_order > new_priority_value
                ),
                # Same priority level and boost status: earlier queued_at is ahead
                and_(
                    or_(
                        and_(Task.priority_boosted == True, new_task.priority_boosted == True),
                        and_(Task.priority_boosted == False, new_task.priority_boosted == False),
                    ),
                    priority_order == new_priority_value,
                    Task.queued_at < new_task.queued_at
                )
            )
        ).count()

        return ahead_count + 1

    def get_next_queued_task(self) -> Optional[Task]:
        """Get the next task from the queue based on priority.

        Priority order:
        1. priority_boosted DESC (boosted tasks first)
        2. priority (high > medium > low)
        3. queued_at ASC (earlier first)

        Skips blocked tasks (status='blocked').

        Returns:
            Next task to process, or None if queue is empty
        """
        session = self.db_manager.get_session()
        try:
            # Custom ordering using CASE for priority
            from sqlalchemy import case

            priority_order = case(
                (Task.priority == "high", 3),
                (Task.priority == "medium", 2),
                (Task.priority == "low", 1),
                else_=2
            )

            # Get all queued tasks (excluding blocked)
            # Note: We only look at "queued" status, blocked tasks have status="blocked"
            tasks = session.query(Task).filter(
                Task.status == "queued"  # Blocked tasks have status='blocked', not 'queued'
            ).order_by(
                Task.priority_boosted.desc(),
                priority_order.desc(),
                Task.queued_at.asc()
            ).all()

            # Filter out any tasks that shouldn't be processed
            # (additional safety check in case a task is queued but its ticket is blocked)
            for task in tasks:
                # If task has a ticket, verify it's not blocked
                if task.ticket_id:
                    from src.services.task_blocking_service import TaskBlockingService

                    blocking_info = TaskBlockingService.check_task_blocked(task.id)
                    if blocking_info["is_blocked"]:
                        logger.warning(
                            f"Task {task.id} is queued but its ticket is blocked. "
                            f"Blocked by: {blocking_info['blocking_ticket_ids']}. "
                            f"This task should have status='blocked', not 'queued'. Skipping."
                        )
                        continue

                # Task is valid, return it
                logger.info(f"Next queued task: {task.id} (priority={task.priority}, boosted={task.priority_boosted})")
                return task

            logger.debug("No queued tasks found")
            return None
        finally:
            session.close()

    def dequeue_task(self, task_id: str) -> None:
        """Remove a task from the queue (mark as assigned).

        Args:
            task_id: ID of the task to dequeue
        """
        session = self.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found for dequeueing")
                return

            if task.status != "queued":
                logger.warning(f"Task {task_id} is not queued (status={task.status})")
                return

            task.status = "assigned"
            task.queue_position = None  # Clear queue position

            session.commit()

            # Update queue positions for remaining tasks
            self._recalculate_queue_positions()

            logger.info(f"Task {task_id} dequeued and marked as assigned")
        except Exception as e:
            logger.error(f"Failed to dequeue task {task_id}: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def _recalculate_queue_positions(self) -> None:
        """Recalculate queue positions for all queued tasks."""
        session = self.db_manager.get_session()
        try:
            from sqlalchemy import case

            priority_order = case(
                (Task.priority == "high", 3),
                (Task.priority == "medium", 2),
                (Task.priority == "low", 1),
                else_=2
            )

            queued_tasks = session.query(Task).filter(
                Task.status == "queued"
            ).order_by(
                Task.priority_boosted.desc(),
                priority_order.desc(),
                Task.queued_at.asc()
            ).all()

            for position, task in enumerate(queued_tasks, start=1):
                task.queue_position = position

            session.commit()
            logger.debug(f"Recalculated positions for {len(queued_tasks)} queued tasks")
        except Exception as e:
            logger.error(f"Failed to recalculate queue positions: {e}")
            session.rollback()
        finally:
            session.close()

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status information.

        Returns:
            Dictionary with queue status information
        """
        session = self.db_manager.get_session()
        try:
            active_agents = self.get_active_agent_count()

            queued_tasks = session.query(Task).filter(
                Task.status == "queued"
            ).order_by(
                Task.queue_position.asc()
            ).all()

            queued_task_details = [
                {
                    "task_id": task.id,
                    "description": task.enriched_description or task.raw_description,
                    "priority": task.priority,
                    "priority_boosted": task.priority_boosted,
                    "queue_position": task.queue_position,
                    "queued_at": task.queued_at.isoformat() if task.queued_at else None,
                    "phase_id": task.phase_id,
                }
                for task in queued_tasks
            ]

            slots_available = max(0, self.max_concurrent_agents - active_agents)

            return {
                "active_agents": active_agents,
                "max_concurrent_agents": self.max_concurrent_agents,
                "queued_tasks_count": len(queued_tasks),
                "queued_tasks": queued_task_details,
                "slots_available": slots_available,
                "at_capacity": active_agents >= self.max_concurrent_agents,
            }
        finally:
            session.close()

    def boost_task_priority(self, task_id: str) -> bool:
        """Boost a task's priority to bypass the queue.

        Args:
            task_id: ID of the task to boost

        Returns:
            True if successful, False otherwise
        """
        session = self.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found for priority boost")
                return False

            if task.status != "queued":
                logger.warning(f"Cannot boost task {task_id} - not queued (status={task.status})")
                return False

            task.priority_boosted = True
            task.queue_position = 1  # Move to front

            session.commit()

            # Recalculate other queue positions
            self._recalculate_queue_positions()

            logger.info(f"Task {task_id} priority boosted")
            return True
        except Exception as e:
            logger.error(f"Failed to boost task {task_id} priority: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_queued_tasks(self) -> List[Task]:
        """Get all queued tasks ordered by priority.

        Returns:
            List of queued tasks
        """
        session = self.db_manager.get_session()
        try:
            from sqlalchemy import case

            priority_order = case(
                (Task.priority == "high", 3),
                (Task.priority == "medium", 2),
                (Task.priority == "low", 1),
                else_=2
            )

            tasks = session.query(Task).filter(
                Task.status == "queued"
            ).order_by(
                Task.priority_boosted.desc(),
                priority_order.desc(),
                Task.queued_at.asc()
            ).all()

            return tasks
        finally:
            session.close()
