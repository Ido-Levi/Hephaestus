"""Comprehensive tests for the Ticket Tracking System (Wave 1)."""

import pytest
import os
import sys
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import (
    DatabaseManager,
    Ticket,
    TicketComment,
    TicketHistory,
    TicketCommit,
    BoardConfig,
    Workflow,
    Agent,
    Task,
)
from src.services.ticket_service import TicketService
from src.services.ticket_history_service import TicketHistoryService


@pytest.fixture
def db_manager():
    """Create a test database."""
    db_path = "test_ticket_system.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Set environment variable so services use the test database
    os.environ["HEPHAESTUS_TEST_DB"] = db_path

    manager = DatabaseManager(db_path)
    manager.create_tables()
    yield manager

    # Cleanup
    if "HEPHAESTUS_TEST_DB" in os.environ:
        del os.environ["HEPHAESTUS_TEST_DB"]
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def test_workflow(db_manager):
    """Create a test workflow."""
    session = db_manager.get_session()
    try:
        workflow = Workflow(
            id="workflow-test",
            name="Test Workflow",
            phases_folder_path="/test/phases",
            status="active",
        )
        session.add(workflow)
        session.commit()
        return workflow.id
    finally:
        session.close()


@pytest.fixture
def test_agent(db_manager):
    """Create a test agent."""
    session = db_manager.get_session()
    try:
        agent = Agent(
            id="agent-test",
            system_prompt="Test agent",
            status="working",
            cli_type="claude",
        )
        session.add(agent)
        session.commit()
        return agent.id
    finally:
        session.close()


@pytest.fixture
def test_board_config(db_manager, test_workflow):
    """Create a test board configuration."""
    session = db_manager.get_session()
    try:
        board = BoardConfig(
            id="board-test",
            workflow_id=test_workflow,
            name="Test Board",
            columns=[
                {"id": "backlog", "name": "Backlog", "order": 0, "color": "#9ca3af"},
                {"id": "todo", "name": "To Do", "order": 1, "color": "#6b7280"},
                {"id": "in_progress", "name": "In Progress", "order": 2, "color": "#3b82f6"},
                {"id": "done", "name": "Done", "order": 3, "color": "#10b981"},
            ],
            ticket_types=["bug", "feature", "task", "improvement"],
            default_ticket_type="task",
            initial_status="backlog",
        )
        session.add(board)
        session.commit()
        return board.id
    finally:
        session.close()


@pytest.mark.asyncio
async def test_create_ticket_basic(db_manager, test_workflow, test_agent, test_board_config):
    """Test basic ticket creation."""
    result = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Test ticket",
        description="This is a test ticket",
        ticket_type="task",
        priority="medium",
    )

    assert result["success"] is True
    assert result["ticket_id"].startswith("ticket-")
    assert result["status"] == "backlog"  # board config initial_status
    assert result["message"] == "Ticket created successfully"

    # Verify ticket exists in database
    session = db_manager.get_session()
    try:
        ticket = session.query(Ticket).filter_by(id=result["ticket_id"]).first()
        assert ticket is not None
        assert ticket.title == "Test ticket"
        assert ticket.description == "This is a test ticket"
        assert ticket.ticket_type == "task"
        assert ticket.priority == "medium"
        assert ticket.status == "backlog"
        assert ticket.is_resolved is False
    finally:
        session.close()


@pytest.mark.asyncio
async def test_create_ticket_with_blocking(db_manager, test_workflow, test_agent, test_board_config):
    """Test creating a ticket with blocked_by_ticket_ids."""
    # Create first ticket
    ticket1 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Blocking ticket",
        description="This blocks other tickets",
        ticket_type="task",
        priority="high",
    )

    # Create second ticket that is blocked by the first
    ticket2 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Blocked ticket",
        description="This is blocked",
        ticket_type="task",
        priority="medium",
        blocked_by_ticket_ids=[ticket1["ticket_id"]],
    )

    assert ticket2["success"] is True

    # Verify blocking relationship
    session = db_manager.get_session()
    try:
        blocked_ticket = session.query(Ticket).filter_by(id=ticket2["ticket_id"]).first()
        assert blocked_ticket.blocked_by_ticket_ids == [ticket1["ticket_id"]]
    finally:
        session.close()


@pytest.mark.asyncio
async def test_blocked_ticket_cannot_change_status(db_manager, test_workflow, test_agent, test_board_config):
    """Test that blocked tickets cannot change status."""
    # Create blocking ticket
    ticket1 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Blocking ticket",
        description="This blocks other tickets",
        ticket_type="task",
        priority="high",
    )

    # Create blocked ticket
    ticket2 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Blocked ticket",
        description="This is blocked",
        ticket_type="task",
        priority="medium",
        blocked_by_ticket_ids=[ticket1["ticket_id"]],
    )

    # Try to change status of blocked ticket
    result = await TicketService.change_status(
        ticket_id=ticket2["ticket_id"],
        agent_id=test_agent,
        new_status="in_progress",
        comment="Trying to move blocked ticket",
    )

    assert result["success"] is False
    assert result["blocked"] is True
    assert ticket1["ticket_id"] in result["blocking_ticket_ids"]
    assert result["old_status"] == "backlog"
    assert result["new_status"] == "backlog"  # Status unchanged


@pytest.mark.asyncio
async def test_resolve_ticket_unblocks_dependencies(db_manager, test_workflow, test_agent, test_board_config):
    """Test that resolving a ticket unblocks dependent tickets."""
    # Create blocking ticket
    ticket1 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Blocking ticket",
        description="This blocks other tickets",
        ticket_type="task",
        priority="high",
    )

    # Create two blocked tickets
    ticket2 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Blocked ticket 1",
        description="Blocked by ticket1",
        ticket_type="task",
        priority="medium",
        blocked_by_ticket_ids=[ticket1["ticket_id"]],
    )

    ticket3 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Blocked ticket 2",
        description="Also blocked by ticket1",
        ticket_type="task",
        priority="medium",
        blocked_by_ticket_ids=[ticket1["ticket_id"]],
    )

    # Resolve the blocking ticket
    result = await TicketService.resolve_ticket(
        ticket_id=ticket1["ticket_id"],
        agent_id=test_agent,
        resolution_comment="Blocking work is done",
    )

    assert result["success"] is True
    assert len(result["unblocked_tickets"]) == 2
    assert ticket2["ticket_id"] in result["unblocked_tickets"]
    assert ticket3["ticket_id"] in result["unblocked_tickets"]

    # Verify tickets are actually unblocked
    session = db_manager.get_session()
    try:
        unblocked1 = session.query(Ticket).filter_by(id=ticket2["ticket_id"]).first()
        unblocked2 = session.query(Ticket).filter_by(id=ticket3["ticket_id"]).first()

        assert unblocked1.blocked_by_ticket_ids == []
        assert unblocked2.blocked_by_ticket_ids == []

        # Verify blocking ticket is resolved
        blocking = session.query(Ticket).filter_by(id=ticket1["ticket_id"]).first()
        assert blocking.is_resolved is True
        assert blocking.resolved_at is not None
    finally:
        session.close()


@pytest.mark.asyncio
async def test_update_ticket_fields(db_manager, test_workflow, test_agent, test_board_config):
    """Test updating ticket fields."""
    # Create ticket
    ticket = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Original title",
        description="Original description",
        ticket_type="task",
        priority="low",
        tags=["tag1"],
    )

    # Update multiple fields
    result = await TicketService.update_ticket(
        ticket_id=ticket["ticket_id"],
        agent_id=test_agent,
        updates={
            "title": "Updated title",
            "priority": "high",
            "tags": ["tag1", "tag2", "tag3"],
        },
        update_comment="Updating ticket details",
    )

    assert result["success"] is True
    assert len(result["fields_updated"]) == 3
    assert "title" in result["fields_updated"]
    assert "priority" in result["fields_updated"]
    assert "tags" in result["fields_updated"]

    # Verify updates in database
    session = db_manager.get_session()
    try:
        updated_ticket = session.query(Ticket).filter_by(id=ticket["ticket_id"]).first()
        assert updated_ticket.title == "Updated title"
        assert updated_ticket.priority == "high"
        assert updated_ticket.tags == ["tag1", "tag2", "tag3"]
    finally:
        session.close()


@pytest.mark.asyncio
async def test_change_status_unblocked_ticket(db_manager, test_workflow, test_agent, test_board_config):
    """Test changing status of an unblocked ticket."""
    # Create ticket
    ticket = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Test ticket",
        description="Test description",
        ticket_type="task",
        priority="medium",
    )

    # Change status
    result = await TicketService.change_status(
        ticket_id=ticket["ticket_id"],
        agent_id=test_agent,
        new_status="in_progress",
        comment="Starting work on this ticket",
    )

    assert result["success"] is True
    assert result["old_status"] == "backlog"
    assert result["new_status"] == "in_progress"
    assert result["blocked"] is False

    # Verify status change in database
    session = db_manager.get_session()
    try:
        updated_ticket = session.query(Ticket).filter_by(id=ticket["ticket_id"]).first()
        assert updated_ticket.status == "in_progress"
        assert updated_ticket.started_at is not None
    finally:
        session.close()


@pytest.mark.asyncio
async def test_add_comment(db_manager, test_workflow, test_agent, test_board_config):
    """Test adding comments to a ticket."""
    # Create ticket
    ticket = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Test ticket",
        description="Test description",
        ticket_type="task",
        priority="medium",
    )

    # Add comment
    result = await TicketService.add_comment(
        ticket_id=ticket["ticket_id"],
        agent_id=test_agent,
        comment_text="This is a test comment",
        comment_type="general",
    )

    assert result["success"] is True
    assert result["comment_id"].startswith("comment-")
    assert result["ticket_id"] == ticket["ticket_id"]

    # Verify comment in database
    session = db_manager.get_session()
    try:
        comment = session.query(TicketComment).filter_by(id=result["comment_id"]).first()
        assert comment is not None
        assert comment.comment_text == "This is a test comment"
        assert comment.comment_type == "general"
        assert comment.ticket_id == ticket["ticket_id"]
    finally:
        session.close()


@pytest.mark.asyncio
async def test_get_ticket_full_details(db_manager, test_workflow, test_agent, test_board_config):
    """Test getting full ticket details."""
    # Create ticket
    ticket = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Test ticket",
        description="Test description",
        ticket_type="task",
        priority="medium",
        tags=["test"],
    )

    # Add a comment
    await TicketService.add_comment(
        ticket_id=ticket["ticket_id"],
        agent_id=test_agent,
        comment_text="Test comment",
    )

    # Get full details
    details = await TicketService.get_ticket(ticket["ticket_id"])

    assert details is not None
    assert details["ticket_id"] == ticket["ticket_id"]
    assert details["title"] == "Test ticket"
    assert details["description"] == "Test description"
    assert len(details["comments"]) >= 1
    assert len(details["history"]) >= 1  # Should have creation history
    assert details["tags"] == ["test"]


@pytest.mark.asyncio
async def test_ticket_history_tracking(db_manager, test_workflow, test_agent, test_board_config):
    """Test that all changes are tracked in history."""
    # Create ticket
    ticket = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Test ticket",
        description="Test description",
        ticket_type="task",
        priority="medium",
    )

    # Perform various operations
    await TicketService.update_ticket(
        ticket_id=ticket["ticket_id"],
        agent_id=test_agent,
        updates={"priority": "high"},
    )

    await TicketService.change_status(
        ticket_id=ticket["ticket_id"],
        agent_id=test_agent,
        new_status="in_progress",
        comment="Starting work",
    )

    await TicketService.add_comment(
        ticket_id=ticket["ticket_id"],
        agent_id=test_agent,
        comment_text="Progress update",
    )

    # Get history
    history = await TicketHistoryService.get_ticket_history(ticket["ticket_id"])

    # Should have multiple history entries
    assert len(history) >= 4  # created, field_updated, status_changed, commented

    # Verify different change types are present
    change_types = [h["change_type"] for h in history]
    assert "created" in change_types
    assert "field_updated" in change_types
    assert "status_changed" in change_types
    assert "commented" in change_types


@pytest.mark.asyncio
async def test_invalid_ticket_type_rejected(db_manager, test_workflow, test_agent, test_board_config):
    """Test that invalid ticket types are rejected."""
    with pytest.raises(ValueError, match="Invalid ticket type"):
        await TicketService.create_ticket(
            workflow_id=test_workflow,
            agent_id=test_agent,
            title="Test ticket",
            description="Test description",
            ticket_type="invalid_type",  # Not in board_config.ticket_types
            priority="medium",
        )


@pytest.mark.asyncio
async def test_invalid_status_rejected(db_manager, test_workflow, test_agent, test_board_config):
    """Test that invalid statuses are rejected."""
    # Create ticket
    ticket = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Test ticket",
        description="Test description",
        ticket_type="task",
        priority="medium",
    )

    # Try to change to invalid status
    with pytest.raises(ValueError, match="Invalid status"):
        await TicketService.change_status(
            ticket_id=ticket["ticket_id"],
            agent_id=test_agent,
            new_status="invalid_status",
            comment="Trying invalid status",
        )


@pytest.mark.asyncio
async def test_link_commit_to_ticket(db_manager, test_workflow, test_agent, test_board_config):
    """Test linking git commits to tickets."""
    # Create ticket
    ticket = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Test ticket",
        description="Test description",
        ticket_type="task",
        priority="medium",
    )

    # Link a commit
    result = await TicketService.link_commit(
        ticket_id=ticket["ticket_id"],
        agent_id=test_agent,
        commit_sha="abc123def456",
        commit_message="Fix issue related to ticket",
        link_method="manual",
    )

    assert result["success"] is True
    assert result["commit_sha"] == "abc123def456"

    # Verify commit link in database
    session = db_manager.get_session()
    try:
        commit = session.query(TicketCommit).filter_by(
            ticket_id=ticket["ticket_id"], commit_sha="abc123def456"
        ).first()
        assert commit is not None
        assert commit.commit_message == "Fix issue related to ticket"
        assert commit.link_method == "manual"
    finally:
        session.close()


@pytest.mark.asyncio
async def test_get_tickets_by_workflow(db_manager, test_workflow, test_agent, test_board_config):
    """Test getting all tickets for a workflow."""
    # Create multiple tickets
    ticket1 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Ticket 1",
        description="Description 1",
        ticket_type="task",
        priority="high",
    )

    ticket2 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Ticket 2",
        description="Description 2",
        ticket_type="bug",
        priority="medium",
    )

    # Get all tickets
    tickets = await TicketService.get_tickets_by_workflow(test_workflow)

    assert len(tickets) >= 2
    ticket_ids = [t["ticket_id"] for t in tickets]
    assert ticket1["ticket_id"] in ticket_ids
    assert ticket2["ticket_id"] in ticket_ids


@pytest.mark.asyncio
async def test_get_tickets_by_status(db_manager, test_workflow, test_agent, test_board_config):
    """Test getting tickets by status."""
    # Create tickets with different statuses
    ticket1 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Ticket 1",
        description="Description 1",
        ticket_type="task",
        priority="high",
    )

    ticket2 = await TicketService.create_ticket(
        workflow_id=test_workflow,
        agent_id=test_agent,
        title="Ticket 2",
        description="Description 2",
        ticket_type="task",
        priority="medium",
    )

    # Move ticket2 to in_progress
    await TicketService.change_status(
        ticket_id=ticket2["ticket_id"],
        agent_id=test_agent,
        new_status="in_progress",
        comment="Starting work",
    )

    # Get backlog tickets
    backlog_tickets = await TicketService.get_tickets_by_status(test_workflow, "backlog")
    assert len(backlog_tickets) >= 1
    assert any(t["ticket_id"] == ticket1["ticket_id"] for t in backlog_tickets)

    # Get in_progress tickets
    in_progress_tickets = await TicketService.get_tickets_by_status(test_workflow, "in_progress")
    assert len(in_progress_tickets) >= 1
    assert any(t["ticket_id"] == ticket2["ticket_id"] for t in in_progress_tickets)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
