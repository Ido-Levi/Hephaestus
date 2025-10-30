"""Service for managing task blocking based on ticket blocking."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.core.database import get_db, Task, Ticket

logger = logging.getLogger(__name__)


class TaskBlockingService:
    """Service for managing task blocking based on ticket dependencies."""

    @staticmethod
    def check_task_blocked(task_id: str) -> Dict[str, Any]:
        """Check if a task is blocked by its associated ticket.

        Args:
            task_id: ID of the task to check

        Returns:
            Dictionary with:
                - is_blocked: bool
                - blocking_ticket_ids: list of ticket IDs blocking this task
                - blocking_tickets: list of dicts with ticket details
        """
        with get_db() as db:
            task = db.query(Task).filter_by(id=task_id).first()

            if not task:
                logger.error(f"Task {task_id} not found")
                return {
                    "is_blocked": False,
                    "blocking_ticket_ids": [],
                    "blocking_tickets": [],
                    "error": "Task not found"
                }

            # If task has no associated ticket, it can't be blocked by tickets
            if not task.ticket_id:
                return {
                    "is_blocked": False,
                    "blocking_ticket_ids": [],
                    "blocking_tickets": []
                }

            # Get the associated ticket
            ticket = db.query(Ticket).filter_by(id=task.ticket_id).first()

            if not ticket:
                logger.warning(f"Task {task_id} references non-existent ticket {task.ticket_id}")
                return {
                    "is_blocked": False,
                    "blocking_ticket_ids": [],
                    "blocking_tickets": []
                }

            # Check if ticket is blocked
            if not ticket.blocked_by_ticket_ids or len(ticket.blocked_by_ticket_ids) == 0:
                return {
                    "is_blocked": False,
                    "blocking_ticket_ids": [],
                    "blocking_tickets": []
                }

            # Ticket is blocked - get blocker details
            blocker_ids = ticket.blocked_by_ticket_ids
            blocker_tickets = db.query(Ticket).filter(Ticket.id.in_(blocker_ids)).all()

            blocker_details = [
                {
                    "ticket_id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "is_resolved": t.is_resolved
                }
                for t in blocker_tickets
            ]

            return {
                "is_blocked": True,
                "blocking_ticket_ids": blocker_ids,
                "blocking_tickets": blocker_details
            }

    @staticmethod
    def block_task(task_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Set task status to 'blocked'.

        Args:
            task_id: ID of the task to block
            reason: Optional reason for blocking

        Returns:
            Dictionary with success status and details
        """
        logger.info(f"Blocking task {task_id}")

        with get_db() as db:
            task = db.query(Task).filter_by(id=task_id).first()

            if not task:
                logger.error(f"Task {task_id} not found")
                return {"success": False, "error": "Task not found"}

            old_status = task.status
            task.status = "blocked"

            # Store the reason in completion_notes (we can use this field for blocking info)
            if reason:
                task.completion_notes = f"Blocked: {reason}"

            db.commit()

            logger.info(f"Task {task_id} status changed from {old_status} to 'blocked'")

            return {
                "success": True,
                "task_id": task_id,
                "old_status": old_status,
                "new_status": "blocked",
                "reason": reason
            }

    @staticmethod
    def unblock_task(task_id: str) -> Dict[str, Any]:
        """Set task status to 'queued' and enqueue for processing.

        BUG FIX: Changed from 'pending' to 'queued' to ensure tasks actually get started.
        Tasks in 'pending' status never get picked up by process_queue().

        Args:
            task_id: ID of the task to unblock

        Returns:
            Dictionary with success status and details
        """
        logger.info(f"Unblocking task {task_id}")

        with get_db() as db:
            task = db.query(Task).filter_by(id=task_id).first()

            if not task:
                logger.error(f"Task {task_id} not found")
                return {"success": False, "error": "Task not found"}

            if task.status != "blocked":
                logger.warning(f"Task {task_id} is not blocked (status={task.status})")
                return {
                    "success": False,
                    "error": f"Task is not blocked (status={task.status})"
                }

            old_status = task.status
            # BUG FIX: Set to 'queued' instead of 'pending' so process_queue() will pick it up
            # Tasks in 'pending' status never get started automatically
            task.status = "queued"
            task.queued_at = datetime.utcnow()

            # Clear blocking reason
            if task.completion_notes and task.completion_notes.startswith("Blocked:"):
                task.completion_notes = None

            db.commit()

            logger.info(f"Task {task_id} status changed from {old_status} to 'queued' - will be processed by queue")

        # Recalculate queue positions for all queued tasks
        # Import here to avoid circular dependencies
        try:
            from src.services.queue_service import QueueService
            from src.core.database import DatabaseManager

            db_manager = DatabaseManager()
            queue_service = QueueService(db_manager)
            queue_service._recalculate_queue_positions()
            logger.info(f"Recalculated queue positions after unblocking task {task_id}")
        except Exception as e:
            logger.warning(f"Could not recalculate queue positions: {e}")

        return {
            "success": True,
            "task_id": task_id,
            "old_status": old_status,
            "new_status": "queued"
        }

    @staticmethod
    def get_blocking_ticket_info(task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about blocking tickets.

        Args:
            task_id: ID of the task

        Returns:
            Dictionary with blocking ticket details or None
        """
        blocking_info = TaskBlockingService.check_task_blocked(task_id)

        if not blocking_info["is_blocked"]:
            return None

        return {
            "task_id": task_id,
            "is_blocked": True,
            "blocker_count": len(blocking_info["blocking_ticket_ids"]),
            "blockers": blocking_info["blocking_tickets"]
        }

    @staticmethod
    def get_all_blocked_tasks() -> List[Dict[str, Any]]:
        """Get all tasks with blocked status.

        Returns:
            List of blocked task details with blocker information
        """
        with get_db() as db:
            blocked_tasks = db.query(Task).filter_by(status="blocked").all()

            results = []
            for task in blocked_tasks:
                # Get blocking info
                blocking_info = TaskBlockingService.check_task_blocked(task.id)

                results.append({
                    "task_id": task.id,
                    "description": task.enriched_description or task.raw_description,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "ticket_id": task.ticket_id,
                    "is_blocked": blocking_info["is_blocked"],
                    "blocking_ticket_ids": blocking_info["blocking_ticket_ids"],
                    "blocking_tickets": blocking_info["blocking_tickets"],
                    "phase_id": task.phase_id,
                    "workflow_id": task.workflow_id
                })

            return results

    @staticmethod
    def sync_task_blocking_status() -> Dict[str, Any]:
        """Sync task blocking status with ticket blocking status.

        This checks all tasks with tickets and ensures their status
        matches the ticket's blocking state.

        Returns:
            Dictionary with sync results
        """
        logger.info("Starting task blocking status sync")

        tasks_blocked = 0
        tasks_unblocked = 0
        errors = []

        with get_db() as db:
            # Get all tasks that have tickets (excluding done/failed/duplicated)
            tasks = db.query(Task).filter(
                Task.ticket_id.isnot(None),
                Task.status.in_(["pending", "queued", "blocked", "assigned", "in_progress"])
            ).all()

            logger.info(f"Checking {len(tasks)} tasks for blocking status sync")

            for task in tasks:
                try:
                    # Check if task should be blocked
                    blocking_info = TaskBlockingService.check_task_blocked(task.id)

                    if blocking_info["is_blocked"] and task.status != "blocked":
                        # Task should be blocked but isn't
                        blocker_titles = [t["title"] for t in blocking_info["blocking_tickets"]]
                        reason = f"Blocked by: {', '.join(blocker_titles)}"

                        TaskBlockingService.block_task(task.id, reason)
                        tasks_blocked += 1
                        logger.info(f"Blocked task {task.id}")

                    elif not blocking_info["is_blocked"] and task.status == "blocked":
                        # Task is blocked but shouldn't be
                        TaskBlockingService.unblock_task(task.id)
                        tasks_unblocked += 1
                        logger.info(f"Unblocked task {task.id}")

                except Exception as e:
                    logger.error(f"Error syncing task {task.id}: {e}")
                    errors.append({"task_id": task.id, "error": str(e)})

        logger.info(f"Task blocking sync complete: {tasks_blocked} blocked, {tasks_unblocked} unblocked")

        return {
            "success": True,
            "tasks_blocked": tasks_blocked,
            "tasks_unblocked": tasks_unblocked,
            "errors": errors,
            "total_checked": len(tasks) if 'tasks' in locals() else 0
        }
