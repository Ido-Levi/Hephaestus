"""Tests for agent and task cleanup when prompt delivery fails."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime

from src.agents.manager import AgentManager
from src.core.database import DatabaseManager, Agent, Task
from src.interfaces import LLMProviderInterface


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    db_manager = Mock(spec=DatabaseManager)

    # Mock get_session to return a mock session
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.close = Mock()
    mock_session.query = Mock()

    db_manager.get_session = Mock(return_value=mock_session)

    return db_manager


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock(spec=LLMProviderInterface)
    provider.generate_agent_prompt = AsyncMock(return_value="Test system prompt")
    return provider


@pytest.fixture
def mock_worktree_manager():
    """Create a mock worktree manager."""
    worktree_manager = Mock()
    worktree_manager.create_agent_worktree = Mock(return_value={
        "working_directory": "/tmp/test-worktree",
        "branch_name": "agent/test-branch"
    })
    return worktree_manager


@pytest.fixture
def mock_tmux_server():
    """Create a mock tmux server."""
    server = Mock()
    server.has_session = Mock(return_value=True)

    # Mock session and pane
    mock_session = Mock()
    mock_pane = Mock()
    mock_pane.send_keys = Mock()
    mock_pane.cmd = Mock()

    mock_window = Mock()
    mock_window.attached_pane = mock_pane
    mock_session.attached_window = mock_window
    mock_session.kill_session = Mock()

    server.new_session = Mock(return_value=mock_session)

    return server


@pytest.mark.asyncio
async def test_agent_and_task_cleanup_on_prompt_delivery_failure(
    mock_db_manager, mock_llm_provider, mock_worktree_manager, mock_tmux_server
):
    """Test that agent and task are properly cleaned up when prompt delivery fails."""

    # Create agent manager with mocks
    agent_manager = AgentManager(
        db_manager=mock_db_manager,
        llm_provider=mock_llm_provider
    )

    # Replace worktree manager and tmux server with mocks
    agent_manager.worktree_manager = mock_worktree_manager
    agent_manager.tmux_server = mock_tmux_server

    # Create a mock task
    task = Task(
        id="test-task-123",
        raw_description="Test task",
        enriched_description="Test task enriched",
        done_definition="Complete the test",
        status="pending"
    )

    # Mock _send_initial_prompt_with_retry to always fail
    agent_manager._send_initial_prompt_with_retry = AsyncMock(
        side_effect=Exception("Failed to deliver initial prompt to agent test-agent after 3 attempts")
    )

    # Mock database query results
    mock_agent_record = Mock(spec=Agent)
    mock_task_record = Mock(spec=Task)
    mock_task_record.id = task.id

    mock_query = Mock()
    mock_query.filter_by = Mock(return_value=mock_query)
    mock_query.first = Mock(side_effect=[mock_agent_record, mock_task_record])

    mock_session = mock_db_manager.get_session()
    mock_session.query = Mock(return_value=mock_query)

    # Try to create agent - should fail and clean up
    with pytest.raises(Exception) as exc_info:
        await agent_manager.create_agent_for_task(
            task=task,
            enriched_data={},
            memories=[],
            project_context="Test context"
        )

    # Verify the exception was raised
    assert "Failed to deliver initial prompt" in str(exc_info.value)

    # Verify tmux session was killed
    tmux_session = mock_tmux_server.new_session.return_value
    tmux_session.kill_session.assert_called_once()

    # Verify database cleanup was attempted
    # Should get a new session for cleanup
    assert mock_db_manager.get_session.call_count >= 2  # Once for agent creation, once for cleanup

    # Verify agent was marked as terminated
    assert mock_agent_record.status == "terminated"

    # Verify task was marked as failed
    assert mock_task_record.status == "failed"
    assert "Agent creation failed" in mock_task_record.failure_reason
    assert mock_task_record.completed_at is not None

    # Verify session was committed and closed
    cleanup_session = mock_db_manager.get_session.return_value
    cleanup_session.commit.assert_called()
    cleanup_session.close.assert_called()


@pytest.mark.asyncio
async def test_cleanup_handles_database_errors_gracefully(
    mock_db_manager, mock_llm_provider, mock_worktree_manager, mock_tmux_server
):
    """Test that cleanup handles database errors gracefully and still raises original exception."""

    # Create agent manager with mocks
    agent_manager = AgentManager(
        db_manager=mock_db_manager,
        llm_provider=mock_llm_provider
    )

    # Replace worktree manager and tmux server with mocks
    agent_manager.worktree_manager = mock_worktree_manager
    agent_manager.tmux_server = mock_tmux_server

    # Create a mock task
    task = Task(
        id="test-task-123",
        raw_description="Test task",
        enriched_description="Test task enriched",
        done_definition="Complete the test",
        status="pending"
    )

    # Mock _send_initial_prompt_with_retry to always fail
    agent_manager._send_initial_prompt_with_retry = AsyncMock(
        side_effect=Exception("Failed to deliver initial prompt to agent test-agent after 3 attempts")
    )

    # Mock database to raise an error during cleanup
    mock_db_manager.get_session.side_effect = [
        Mock(),  # First call during agent creation
        Exception("Database connection error")  # Second call during cleanup
    ]

    # Try to create agent - should fail and attempt cleanup
    with pytest.raises(Exception) as exc_info:
        await agent_manager.create_agent_for_task(
            task=task,
            enriched_data={},
            memories=[],
            project_context="Test context"
        )

    # Verify the ORIGINAL exception was raised (not the database error)
    assert "Failed to deliver initial prompt" in str(exc_info.value)

    # Verify tmux session was still killed despite database error
    tmux_session = mock_tmux_server.new_session.return_value
    tmux_session.kill_session.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_handles_tmux_kill_errors_gracefully(
    mock_db_manager, mock_llm_provider, mock_worktree_manager, mock_tmux_server
):
    """Test that cleanup continues even if tmux session kill fails."""

    # Create agent manager with mocks
    agent_manager = AgentManager(
        db_manager=mock_db_manager,
        llm_provider=mock_llm_provider
    )

    # Replace worktree manager and tmux server with mocks
    agent_manager.worktree_manager = mock_worktree_manager
    agent_manager.tmux_server = mock_tmux_server

    # Create a mock task
    task = Task(
        id="test-task-123",
        raw_description="Test task",
        enriched_description="Test task enriched",
        done_definition="Complete the test",
        status="pending"
    )

    # Mock _send_initial_prompt_with_retry to always fail
    agent_manager._send_initial_prompt_with_retry = AsyncMock(
        side_effect=Exception("Failed to deliver initial prompt to agent test-agent after 3 attempts")
    )

    # Mock tmux session kill to raise an error
    tmux_session = mock_tmux_server.new_session.return_value
    tmux_session.kill_session = Mock(side_effect=Exception("Failed to kill tmux session"))

    # Mock database query results for cleanup
    mock_agent_record = Mock(spec=Agent)
    mock_task_record = Mock(spec=Task)
    mock_task_record.id = task.id

    mock_query = Mock()
    mock_query.filter_by = Mock(return_value=mock_query)
    mock_query.first = Mock(side_effect=[mock_agent_record, mock_task_record])

    mock_session = mock_db_manager.get_session()
    mock_session.query = Mock(return_value=mock_query)

    # Try to create agent - should fail and attempt cleanup
    with pytest.raises(Exception) as exc_info:
        await agent_manager.create_agent_for_task(
            task=task,
            enriched_data={},
            memories=[],
            project_context="Test context"
        )

    # Verify the original exception was raised (not the tmux error)
    assert "Failed to deliver initial prompt" in str(exc_info.value)

    # Verify database cleanup still happened despite tmux error
    assert mock_agent_record.status == "terminated"
    assert mock_task_record.status == "failed"
