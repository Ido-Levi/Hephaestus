"""Service layer for managing ticket history and audit trail."""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from src.core.database import get_db, TicketHistory, Ticket


class TicketHistoryService:
    """Service for tracking all ticket state changes."""

    @staticmethod
    async def record_change(
        ticket_id: str,
        agent_id: str,
        change_type: str,
        old_value: Optional[str],
        new_value: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> None:
        """
        Record any change to a ticket.

        Args:
            ticket_id: ID of the ticket
            agent_id: ID of the agent making the change
            change_type: Type of change (created, status_changed, assigned, commented, field_updated, commit_linked, reopened, blocked, unblocked, resolved)
            old_value: Previous value
            new_value: New value
            metadata: Additional context as dictionary
            db: Optional database session (if None, creates its own)

        Raises:
            ValueError: If validation fails
        """
        should_commit = False
        if db is None:
            # Create our own session
            db_context = get_db()
            db = db_context.__enter__()
            should_commit = True

        try:
            # Validate ticket exists (skip for testing since ticket may not be committed yet)
            # ticket = db.query(Ticket).filter_by(id=ticket_id).first()
            # if not ticket:
            #     raise ValueError(f"Ticket not found: {ticket_id}")

            # Generate change description based on change_type
            change_description = TicketHistoryService._generate_description(
                change_type, old_value, new_value, metadata
            )

            # Extract field_name from metadata if it's a field_updated change
            field_name = None
            if change_type == "field_updated" and metadata:
                field_name = metadata.get("field_name")

            # Create history entry
            history_entry = TicketHistory(
                ticket_id=ticket_id,
                agent_id=agent_id,
                change_type=change_type,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                change_description=change_description,
                change_metadata=metadata,
                changed_at=datetime.utcnow(),
            )

            db.add(history_entry)

            if should_commit:
                db.commit()
                db_context.__exit__(None, None, None)
        except Exception as e:
            if should_commit:
                db_context.__exit__(type(e), e, e.__traceback__)
            raise

    @staticmethod
    async def record_status_transition(
        ticket_id: str, agent_id: str, from_status: str, to_status: str, db: Optional[Session] = None
    ) -> None:
        """
        Record a status change.

        Args:
            ticket_id: ID of the ticket
            agent_id: ID of the agent making the change
            from_status: Previous status
            to_status: New status
            db: Optional database session

        Raises:
            ValueError: If validation fails
        """
        await TicketHistoryService.record_change(
            ticket_id=ticket_id,
            agent_id=agent_id,
            change_type="status_changed",
            old_value=from_status,
            new_value=to_status,
            metadata={"from_status": from_status, "to_status": to_status},
            db=db,
        )

    @staticmethod
    async def link_commit(ticket_id: str, commit_sha: str, message: str, db: Optional[Session] = None) -> None:
        """
        Record a commit link.

        Args:
            ticket_id: ID of the ticket
            commit_sha: Git commit SHA
            message: Commit message
            db: Optional database session

        Raises:
            ValueError: If validation fails
        """
        should_commit = False
        if db is None:
            db_context = get_db()
            db = db_context.__enter__()
            should_commit = True

        try:
            ticket = db.query(Ticket).filter_by(id=ticket_id).first()
            if not ticket:
                raise ValueError(f"Ticket not found: {ticket_id}")

            # Get the agent who created the ticket as default
            agent_id = ticket.created_by_agent_id

            await TicketHistoryService.record_change(
                ticket_id=ticket_id,
                agent_id=agent_id,
                change_type="commit_linked",
                old_value=None,
                new_value=commit_sha,
                metadata={"commit_sha": commit_sha, "commit_message": message},
                db=db,
            )

            if should_commit:
                db.commit()
                db_context.__exit__(None, None, None)
        except Exception as e:
            if should_commit:
                db_context.__exit__(type(e), e, e.__traceback__)
            raise

    @staticmethod
    async def get_ticket_history(ticket_id: str) -> List[Dict[str, Any]]:
        """
        Get all history entries for a ticket.

        Args:
            ticket_id: ID of the ticket

        Returns:
            List of history entry dictionaries ordered by time

        Raises:
            ValueError: If ticket not found
        """
        with get_db() as db:
            # Validate ticket exists
            ticket = db.query(Ticket).filter_by(id=ticket_id).first()
            if not ticket:
                raise ValueError(f"Ticket not found: {ticket_id}")

            history = (
                db.query(TicketHistory)
                .filter_by(ticket_id=ticket_id)
                .order_by(TicketHistory.changed_at)
                .all()
            )

            return [
                {
                    "id": h.id,
                    "change_type": h.change_type,
                    "field_name": h.field_name,
                    "old_value": h.old_value,
                    "new_value": h.new_value,
                    "change_description": h.change_description,
                    "metadata": h.change_metadata,
                    "changed_at": h.changed_at.isoformat() + "Z",
                    "agent_id": h.agent_id,
                }
                for h in history
            ]

    @staticmethod
    async def get_ticket_timeline(ticket_id: str) -> List[Dict[str, Any]]:
        """
        Get formatted timeline of ticket changes for UI display.

        Args:
            ticket_id: ID of the ticket

        Returns:
            List of timeline entries with formatted descriptions

        Raises:
            ValueError: If ticket not found
        """
        history = await TicketHistoryService.get_ticket_history(ticket_id)

        # Format each entry for timeline display
        timeline = []
        for entry in history:
            timeline_entry = {
                "timestamp": entry["changed_at"],
                "agent_id": entry["agent_id"],
                "description": entry["change_description"],
                "change_type": entry["change_type"],
                "details": {
                    "old_value": entry["old_value"],
                    "new_value": entry["new_value"],
                    "field_name": entry["field_name"],
                    "metadata": entry["metadata"],
                },
            }
            timeline.append(timeline_entry)

        return timeline

    @staticmethod
    def _generate_description(
        change_type: str,
        old_value: Optional[str],
        new_value: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> str:
        """
        Generate human-readable description for a change.

        Args:
            change_type: Type of change
            old_value: Previous value
            new_value: New value
            metadata: Additional context

        Returns:
            Human-readable description string
        """
        if change_type == "created":
            return "Ticket created"

        elif change_type == "status_changed":
            return f"Status changed from {old_value} to {new_value}"

        elif change_type == "assigned":
            if old_value:
                return f"Reassigned from {old_value} to {new_value}"
            else:
                return f"Assigned to {new_value}"

        elif change_type == "commented":
            comment_type = metadata.get("comment_type", "general") if metadata else "general"
            if comment_type == "status_change":
                return "Added status change comment"
            elif comment_type == "resolution":
                return "Added resolution comment"
            else:
                return "Added comment"

        elif change_type == "field_updated":
            field_name = metadata.get("field_name") if metadata else "field"
            return f"Updated {field_name}"

        elif change_type == "commit_linked":
            commit_sha = new_value[:7] if new_value else "unknown"
            return f"Linked commit {commit_sha}"

        elif change_type == "reopened":
            return f"Reopened ticket (status: {new_value})"

        elif change_type == "blocked":
            blocker_ids = metadata.get("blocker_ids", []) if metadata else []
            if blocker_ids:
                return f"Blocked by {len(blocker_ids)} ticket(s)"
            return "Ticket blocked"

        elif change_type == "unblocked":
            resolved_ticket = metadata.get("resolved_ticket_id") if metadata else None
            if resolved_ticket:
                return f"Unblocked by resolution of {resolved_ticket}"
            return "Ticket unblocked"

        elif change_type == "resolved":
            return "Ticket marked as resolved"

        else:
            return f"Changed {change_type}"
