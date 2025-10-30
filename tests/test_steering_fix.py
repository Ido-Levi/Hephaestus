"""Test to verify steering message fix works correctly."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.core.database import DatabaseManager, Agent, Task, AgentLog
from src.agents.manager import AgentManager
from src.monitoring.guardian import Guardian
from src.monitoring.monitor import MonitoringLoop
from src.interfaces import LLMProviderInterface
from src.memory.rag import RAGSystem


@pytest.fixture
def mock_db_manager():
    """Mock database manager."""
    mock = Mock(spec=DatabaseManager)
    mock.get_session = Mock()
    return mock


@pytest.fixture
def mock_agent_manager():
    """Mock agent manager."""
    mock = Mock(spec=AgentManager)
    mock.send_message_to_agent = Mock()
    mock.get_agent_output = Mock(return_value="agent output here")
    mock.get_active_agents = Mock(return_value=[])

    # Mock tmux_server attribute
    mock.tmux_server = Mock()
    mock.tmux_server.has_session = Mock(return_value=True)

    return mock


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    mock = Mock(spec=LLMProviderInterface)
    mock.analyze_agent_trajectory = AsyncMock()
    return mock


@pytest.fixture
def mock_rag_system():
    """Mock RAG system."""
    mock = Mock(spec=RAGSystem)
    return mock


@pytest.fixture
def test_agent():
    """Test agent."""
    agent = Agent(
        id="test-agent-1",
        status="working",
        current_task_id="task-1",
        tmux_session_name="agent-session-1",
        cli_type="claude_code",
        last_activity=datetime.utcnow()
    )
    # Add missing attribute needed by monitor
    agent.health_check_failures = 0
    return agent


@pytest.fixture
def test_task():
    """Test task."""
    return Task(
        id="task-1",
        raw_description="Test task",
        enriched_description="Test task enriched",
        done_definition="Complete the test",
        status="in_progress"
    )


class TestSteeringMessageFix:
    """Test steering message field name fix."""

    @pytest.mark.asyncio
    async def test_steering_message_field_mapping(
        self,
        mock_db_manager,
        mock_agent_manager,
        mock_llm_provider,
        test_agent,
        test_task
    ):
        """Test that steering_recommendation from LLM is correctly mapped to steering_message."""

        # Setup database session mock
        session_mock = Mock()
        session_mock.query.return_value.filter_by.return_value.first.return_value = test_task
        session_mock.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        session_mock.close = Mock()
        mock_db_manager.get_session.return_value = session_mock

        # Setup LLM provider to return steering recommendation
        mock_llm_provider.analyze_agent_trajectory.return_value = {
            "current_phase": "implementation",
            "trajectory_aligned": False,
            "alignment_score": 0.3,
            "alignment_issues": ["Agent is stuck on error"],
            "needs_steering": True,
            "steering_type": "stuck",
            "steering_recommendation": "Try a different approach to fix the import error",  # LLM returns this key
            "trajectory_summary": "Agent is stuck on import error, needs help"
        }

        # Create Guardian instance
        guardian = Guardian(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=mock_llm_provider
        )

        # Perform analysis
        result = await guardian.analyze_agent_with_trajectory(
            agent=test_agent,
            tmux_output="ImportError: cannot import module",
            past_summaries=[]
        )

        # Verify the field mapping worked correctly
        assert result["needs_steering"] is True
        assert result["steering_type"] == "stuck"
        assert result["steering_message"] == "Try a different approach to fix the import error"  # Should be mapped correctly

        # Verify LLM was called
        mock_llm_provider.analyze_agent_trajectory.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitoring_loop_uses_correct_steering_field(
        self,
        mock_db_manager,
        mock_agent_manager,
        mock_llm_provider,
        mock_rag_system,
        test_agent,
        test_task
    ):
        """Test that MonitoringLoop correctly uses the steering_message field."""

        # Setup database session mock
        session_mock = Mock()
        session_mock.query.return_value.filter_by.return_value.first.return_value = test_task
        session_mock.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        session_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        session_mock.add = Mock()
        session_mock.commit = Mock()
        session_mock.flush = Mock()
        session_mock.close = Mock()
        mock_db_manager.get_session.return_value = session_mock

        # Setup agent manager to return our test agent
        mock_agent_manager.get_active_agents.return_value = [test_agent]
        mock_agent_manager.get_agent_output.return_value = "Error: cannot import module"

        # Mock tmux session check
        mock_agent_manager.tmux_server.has_session.return_value = True

        # Setup LLM provider to return steering recommendation
        mock_llm_provider.analyze_agent_trajectory.return_value = {
            "current_phase": "implementation",
            "trajectory_aligned": False,
            "alignment_score": 0.3,
            "alignment_issues": ["Agent is stuck on error"],
            "needs_steering": True,
            "steering_type": "stuck",
            "steering_recommendation": "Check your imports and try using absolute paths",
            "trajectory_summary": "Agent is stuck on import error, needs guidance"
        }

        # Create monitoring loop
        monitoring_loop = MonitoringLoop(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=mock_llm_provider,
            rag_system=mock_rag_system
        )

        # Run one monitoring cycle
        await monitoring_loop._monitoring_cycle()

        # Verify that steering was attempted with the correct message
        # The Guardian.steer_agent method should have been called with the right message
        mock_agent_manager.send_message_to_agent.assert_called()

        # Get the call arguments
        call_args = mock_agent_manager.send_message_to_agent.call_args
        agent_id_called = call_args[0][0]
        message_sent = call_args[0][1]

        assert agent_id_called == test_agent.id
        assert "Check your imports and try using absolute paths" in message_sent
        assert "GUARDIAN GUIDANCE" in message_sent

    @pytest.mark.asyncio
    async def test_steering_not_sent_when_needs_steering_false(
        self,
        mock_db_manager,
        mock_agent_manager,
        mock_llm_provider,
        mock_rag_system,
        test_agent,
        test_task
    ):
        """Test that no steering message is sent when needs_steering is False."""

        # Setup database session mock
        session_mock = Mock()
        session_mock.query.return_value.filter_by.return_value.first.return_value = test_task
        session_mock.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        session_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        session_mock.add = Mock()
        session_mock.commit = Mock()
        session_mock.flush = Mock()
        session_mock.close = Mock()
        mock_db_manager.get_session.return_value = session_mock

        # Setup agent manager
        mock_agent_manager.get_active_agents.return_value = [test_agent]
        mock_agent_manager.get_agent_output.return_value = "Working on implementation..."
        mock_agent_manager.tmux_server.has_session.return_value = True

        # Setup LLM provider to return no steering needed
        mock_llm_provider.analyze_agent_trajectory.return_value = {
            "current_phase": "implementation",
            "trajectory_aligned": True,
            "alignment_score": 0.8,
            "alignment_issues": [],
            "needs_steering": False,  # No steering needed
            "steering_type": None,
            "steering_recommendation": None,
            "trajectory_summary": "Agent is making good progress on implementation"
        }

        # Create monitoring loop
        monitoring_loop = MonitoringLoop(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=mock_llm_provider,
            rag_system=mock_rag_system
        )

        # Run one monitoring cycle
        await monitoring_loop._monitoring_cycle()

        # Verify no steering message was sent
        mock_agent_manager.send_message_to_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_when_steering_message_missing(
        self,
        mock_db_manager,
        mock_agent_manager,
        mock_llm_provider,
        mock_rag_system,
        test_agent,
        test_task
    ):
        """Test fallback behavior when steering_message is missing but needs_steering is True."""

        # Setup database session mock
        session_mock = Mock()
        session_mock.query.return_value.filter_by.return_value.first.return_value = test_task
        session_mock.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        session_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        session_mock.add = Mock()
        session_mock.commit = Mock()
        session_mock.flush = Mock()
        session_mock.close = Mock()
        mock_db_manager.get_session.return_value = session_mock

        # Setup agent manager
        mock_agent_manager.get_active_agents.return_value = [test_agent]
        mock_agent_manager.get_agent_output.return_value = "Stuck on something..."
        mock_agent_manager.tmux_server.has_session.return_value = True

        # Setup LLM provider to return steering needed but no message
        mock_llm_provider.analyze_agent_trajectory.return_value = {
            "current_phase": "implementation",
            "trajectory_aligned": False,
            "alignment_score": 0.4,
            "alignment_issues": ["Some issue"],
            "needs_steering": True,  # Needs steering
            "steering_type": "confused",
            "steering_recommendation": None,  # But no message provided
            "trajectory_summary": "Agent needs help but no specific message"
        }

        # Create monitoring loop
        monitoring_loop = MonitoringLoop(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=mock_llm_provider,
            rag_system=mock_rag_system
        )

        # Run one monitoring cycle
        await monitoring_loop._monitoring_cycle()

        # Verify steering was still attempted with fallback message
        mock_agent_manager.send_message_to_agent.assert_called()

        call_args = mock_agent_manager.send_message_to_agent.call_args
        message_sent = call_args[0][1]

        # Should use the fallback message from monitor.py line 565
        assert "Please check your trajectory" in message_sent
        assert "GUARDIAN GUIDANCE" in message_sent


if __name__ == "__main__":
    pytest.main([__file__])