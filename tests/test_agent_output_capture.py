"""Tests for agent output capture on termination."""

import asyncio
import uuid
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, AsyncMock
import pytest

from src.agents.manager import AgentManager
from src.core.database import DatabaseManager, Agent, AgentLog, Task


class TestAgentOutputCapture:
    """Test suite for agent output capture functionality."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        db_manager = Mock(spec=DatabaseManager)
        return db_manager

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        llm_provider = Mock()
        llm_provider.generate_agent_prompt = AsyncMock(return_value="Test prompt")
        return llm_provider

    @pytest.fixture
    def mock_tmux_server(self):
        """Create a mock tmux server."""
        server = Mock()
        return server

    @pytest.fixture
    def agent_manager(self, mock_db_manager, mock_llm_provider, mock_tmux_server):
        """Create an agent manager with mocked dependencies."""
        with patch('src.agents.manager.libtmux.Server', return_value=mock_tmux_server):
            manager = AgentManager(mock_db_manager, mock_llm_provider)
            manager.tmux_server = mock_tmux_server
            return manager

    @pytest.mark.asyncio
    async def test_terminate_agent_captures_output(self, agent_manager, mock_db_manager, mock_tmux_server):
        """Test that terminate_agent captures output before killing the session."""
        # Setup
        agent_id = str(uuid.uuid4())
        session_name = f"test_session_{agent_id[:8]}"
        test_output_lines = [
            "Line 1: Starting task",
            "Line 2: Processing...",
            "Line 3: Task completed successfully"
        ]

        # Create mock agent
        mock_agent = Mock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.tmux_session_name = session_name
        mock_agent.status = "working"

        # Create mock tmux session
        mock_tmux_session = Mock()
        mock_pane = Mock()
        mock_pane.cmd.return_value = Mock(stdout=test_output_lines)
        mock_tmux_session.attached_window.attached_pane = mock_pane

        # Setup database session mock
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_manager.get_session.return_value = mock_db_session

        # Setup tmux server mock
        mock_tmux_server.has_session.return_value = True
        mock_tmux_server.sessions = [mock_tmux_session]
        mock_tmux_session.name = session_name

        # Execute
        await agent_manager.terminate_agent(agent_id)

        # Verify output was captured
        mock_pane.cmd.assert_called_with("capture-pane", "-p", "-S", "-10000")

        # Verify agent status was updated
        assert mock_agent.status == "terminated"

        # Verify AgentLog was created with output
        mock_db_session.add.assert_called_once()
        log_entry = mock_db_session.add.call_args[0][0]
        assert isinstance(log_entry, AgentLog)
        assert log_entry.agent_id == agent_id
        assert log_entry.log_type == "terminated"
        assert log_entry.details["final_output"] == "\n".join(test_output_lines)
        assert log_entry.details["output_lines"] == len(test_output_lines)

        # Verify session was killed after capturing output
        mock_tmux_session.kill_session.assert_called_once()

        # Verify database commit
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_terminate_agent_handles_no_session(self, agent_manager, mock_db_manager, mock_tmux_server):
        """Test that terminate_agent handles missing tmux session gracefully."""
        # Setup
        agent_id = str(uuid.uuid4())
        session_name = f"test_session_{agent_id[:8]}"

        # Create mock agent
        mock_agent = Mock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.tmux_session_name = session_name
        mock_agent.status = "working"

        # Setup database session mock
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_manager.get_session.return_value = mock_db_session

        # Setup tmux server mock - no session exists
        mock_tmux_server.has_session.return_value = False

        # Execute
        await agent_manager.terminate_agent(agent_id)

        # Verify agent status was still updated
        assert mock_agent.status == "terminated"

        # Verify AgentLog was created with empty output
        mock_db_session.add.assert_called_once()
        log_entry = mock_db_session.add.call_args[0][0]
        assert isinstance(log_entry, AgentLog)
        assert log_entry.agent_id == agent_id
        assert log_entry.log_type == "terminated"
        assert log_entry.details["final_output"] == ""
        assert log_entry.details["output_lines"] == 0

        # Verify database commit
        mock_db_session.commit.assert_called_once()

    def test_get_agent_output_retrieves_from_log_for_terminated(self, agent_manager, mock_db_manager):
        """Test that get_agent_output retrieves from AgentLog for terminated agents."""
        # Setup
        agent_id = str(uuid.uuid4())
        stored_output = "This is the stored final output\nLine 2\nLine 3"

        # Create mock agent
        mock_agent = Mock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.status = "terminated"

        # Create mock AgentLog with stored output
        mock_log = Mock(spec=AgentLog)
        mock_log.details = {
            "final_output": stored_output,
            "output_lines": 3,
            "captured_at": datetime.utcnow().isoformat()
        }

        # Setup database session mock
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter_by.side_effect = [
            Mock(first=Mock(return_value=mock_agent)),  # First call for Agent
            Mock(order_by=Mock(return_value=Mock(first=Mock(return_value=mock_log))))  # Second call for AgentLog
        ]
        mock_db_manager.get_session.return_value = mock_db_session

        # Execute
        output = agent_manager.get_agent_output(agent_id)

        # Verify
        assert output == stored_output

    def test_get_agent_output_retrieves_last_n_lines_for_terminated(self, agent_manager, mock_db_manager):
        """Test that get_agent_output respects lines parameter for terminated agents."""
        # Setup
        agent_id = str(uuid.uuid4())
        stored_output = "\n".join([f"Line {i}" for i in range(1, 11)])  # 10 lines

        # Create mock agent
        mock_agent = Mock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.status = "terminated"

        # Create mock AgentLog with stored output
        mock_log = Mock(spec=AgentLog)
        mock_log.details = {
            "final_output": stored_output,
            "output_lines": 10,
            "captured_at": datetime.utcnow().isoformat()
        }

        # Setup database session mock
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter_by.side_effect = [
            Mock(first=Mock(return_value=mock_agent)),  # First call for Agent
            Mock(order_by=Mock(return_value=Mock(first=Mock(return_value=mock_log))))  # Second call for AgentLog
        ]
        mock_db_manager.get_session.return_value = mock_db_session

        # Execute - request only last 5 lines
        output = agent_manager.get_agent_output(agent_id, lines=5)

        # Verify - should get last 5 lines
        expected_lines = ["Line 6", "Line 7", "Line 8", "Line 9", "Line 10"]
        assert output == "\n".join(expected_lines)

    def test_get_agent_output_from_tmux_for_active_agent(self, agent_manager, mock_db_manager, mock_tmux_server):
        """Test that get_agent_output retrieves from tmux for active agents."""
        # Setup
        agent_id = str(uuid.uuid4())
        session_name = f"test_session_{agent_id[:8]}"
        test_output_lines = ["Active output line 1", "Active output line 2"]

        # Create mock agent (not terminated)
        mock_agent = Mock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.status = "working"
        mock_agent.tmux_session_name = session_name

        # Create mock tmux session
        mock_tmux_session = Mock()
        mock_pane = Mock()
        mock_pane.cmd.return_value = Mock(stdout=test_output_lines)
        mock_tmux_session.attached_window.attached_pane = mock_pane
        mock_tmux_session.name = session_name

        # Setup database session mock
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_db_manager.get_session.return_value = mock_db_session

        # Setup tmux server mock
        mock_tmux_server.has_session.return_value = True
        mock_tmux_server.sessions = [mock_tmux_session]

        # Execute
        output = agent_manager.get_agent_output(agent_id, lines=200)

        # Verify tmux was called
        mock_pane.cmd.assert_called_with("capture-pane", "-p", "-S -200")

        # Verify output
        assert output == "\n".join(test_output_lines)

    def test_get_agent_output_handles_no_stored_output(self, agent_manager, mock_db_manager):
        """Test that get_agent_output handles terminated agents with no stored output."""
        # Setup
        agent_id = str(uuid.uuid4())

        # Create mock agent
        mock_agent = Mock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.status = "terminated"

        # No AgentLog found
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter_by.side_effect = [
            Mock(first=Mock(return_value=mock_agent)),  # First call for Agent
            Mock(order_by=Mock(return_value=Mock(first=Mock(return_value=None))))  # Second call for AgentLog
        ]
        mock_db_manager.get_session.return_value = mock_db_session

        # Execute
        output = agent_manager.get_agent_output(agent_id)

        # Verify
        assert output == "Agent terminated - no output was captured"

    @pytest.mark.asyncio
    async def test_terminate_agent_handles_output_capture_failure(self, agent_manager, mock_db_manager, mock_tmux_server):
        """Test that terminate_agent handles output capture failure gracefully."""
        # Setup
        agent_id = str(uuid.uuid4())
        session_name = f"test_session_{agent_id[:8]}"

        # Create mock agent
        mock_agent = Mock(spec=Agent)
        mock_agent.id = agent_id
        mock_agent.tmux_session_name = session_name
        mock_agent.status = "working"

        # Create mock tmux session that fails to capture
        mock_tmux_session = Mock()
        mock_pane = Mock()
        mock_pane.cmd.side_effect = Exception("Failed to capture pane")
        mock_tmux_session.attached_window.attached_pane = mock_pane
        mock_tmux_session.name = session_name

        # Setup database session mock
        mock_db_session = Mock()
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_manager.get_session.return_value = mock_db_session

        # Setup tmux server mock
        mock_tmux_server.has_session.return_value = True
        mock_tmux_server.sessions = [mock_tmux_session]

        # Execute
        await agent_manager.terminate_agent(agent_id)

        # Verify agent was still terminated despite capture failure
        assert mock_agent.status == "terminated"

        # Verify AgentLog was created with empty output
        mock_db_session.add.assert_called_once()
        log_entry = mock_db_session.add.call_args[0][0]
        assert log_entry.details["final_output"] == ""
        assert log_entry.details["output_lines"] == 0

        # Verify session was still killed
        mock_tmux_session.kill_session.assert_called_once()

        # Verify database commit
        mock_db_session.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])