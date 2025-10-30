"""Unit tests for the Guardian trajectory monitoring system."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from src.monitoring.guardian import Guardian, SteeringType, TrajectoryPhase
from src.core.database import Agent, Task, AgentLog


@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    mock = Mock()
    mock.get_session = Mock()
    return mock


@pytest.fixture
def mock_agent_manager():
    """Create mock agent manager."""
    mock = Mock()
    mock.get_agent_output = Mock(return_value="Agent working on task...")
    mock.send_message_to_agent = Mock()
    mock.tmux_server = Mock()
    return mock


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    mock = AsyncMock()
    mock.analyze_agent_trajectory = AsyncMock(return_value={
        "current_phase": "implementation",
        "trajectory_aligned": True,
        "alignment_score": 0.8,
        "alignment_issues": [],
        "needs_steering": False,
        "steering_type": None,
        "steering_recommendation": None,
        "trajectory_summary": "Agent implementing task successfully"
    })
    return mock


@pytest.fixture
def guardian(mock_db_manager, mock_agent_manager, mock_llm_provider):
    """Create Guardian instance with mocked dependencies."""
    return Guardian(
        db_manager=mock_db_manager,
        agent_manager=mock_agent_manager,
        llm_provider=mock_llm_provider
    )


class TestGuardian:
    """Test the Guardian monitoring system."""

    @pytest.mark.asyncio
    async def test_analyze_agent_with_trajectory_success(self, guardian, mock_llm_provider):
        """Test successful trajectory analysis of an agent."""
        # Setup
        agent = Agent(
            id="test-agent-1",
            current_task_id="task-1",
            tmux_session_name="agent-test-1"
        )

        mock_task = Task(
            id="task-1",
            raw_description="Implement authentication",
            enriched_description="Implement JWT authentication system",
            done_definition="Authentication working with tests"
        )

        # Mock accumulated context
        with patch.object(guardian, '_build_accumulated_context', return_value={
            "overall_goal": "Implement JWT authentication",
            "constraints": ["no external libraries"],
            "lifted_constraints": [],
            "standing_instructions": ["keep it simple"],
            "session_start": datetime.utcnow() - timedelta(minutes=5),
            "conversation_length": 10,
            "current_focus": "implementation"
        }):
            with patch.object(guardian, '_get_agent_task', return_value=mock_task):
                # Execute
                result = await guardian.analyze_agent_with_trajectory(
                    agent=agent,
                    tmux_output="Creating auth module...",
                    past_summaries=[]
                )

        # Assert
        assert result['agent_id'] == "test-agent-1"
        assert result['trajectory_aligned'] is True
        assert result['alignment_score'] == 0.8
        assert result['current_phase'] == "implementation"
        assert "JWT authentication" in result['accumulated_goal']
        assert "no external libraries" in result['active_constraints']

        # Verify LLM was called
        mock_llm_provider.analyze_agent_trajectory.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_agent_with_steering_needed(self, guardian, mock_llm_provider):
        """Test when agent needs steering intervention."""
        # Setup - agent needs steering
        mock_llm_provider.analyze_agent_trajectory.return_value = {
            "current_phase": "implementation",
            "trajectory_aligned": False,
            "alignment_score": 0.3,
            "alignment_issues": ["Installing external packages"],
            "needs_steering": True,
            "steering_type": "violating_constraints",
            "steering_recommendation": "Remember: no external libraries allowed",
            "trajectory_summary": "Agent violating constraints"
        }

        agent = Agent(id="test-agent-2", current_task_id="task-2")
        mock_task = Task(
            id="task-2",
            enriched_description="Build API",
            done_definition="API working"
        )

        with patch.object(guardian, '_build_accumulated_context', return_value={
            "overall_goal": "Build API",
            "constraints": ["no external libraries"],
            "session_start": datetime.utcnow()
        }):
            with patch.object(guardian, '_get_agent_task', return_value=mock_task):
                # Execute
                result = await guardian.analyze_agent_with_trajectory(
                    agent=agent,
                    tmux_output="pip install requests",
                    past_summaries=[]
                )

        # Assert steering needed
        assert result['trajectory_aligned'] is False
        assert result['needs_steering'] is True
        assert result['steering_type'] == "violating_constraints"
        assert result['steering_message'] == "Remember: no external libraries allowed"

    @pytest.mark.asyncio
    async def test_guardian_caching(self, guardian):
        """Test that Guardian caches trajectory analysis."""
        agent = Agent(id="test-agent-3", current_task_id="task-3")
        mock_task = Task(id="task-3", enriched_description="Test task")

        # Provide complete accumulated context
        complete_context = {
            "overall_goal": "Test",
            "constraints": [],
            "lifted_constraints": [],
            "standing_instructions": [],
            "references": {},
            "conversation_length": 0,
            "session_start": datetime.utcnow(),
            "discovered_blockers": []
        }

        with patch.object(guardian, '_build_accumulated_context', return_value=complete_context):
            with patch.object(guardian, '_get_agent_task', return_value=mock_task):
                await guardian.analyze_agent_with_trajectory(
                    agent=agent,
                    tmux_output="test",
                    past_summaries=[]
                )

        # Check cache
        assert "test-agent-3" in guardian.trajectory_cache
        cached = guardian.trajectory_cache["test-agent-3"]
        assert "analysis" in cached
        assert "timestamp" in cached

    @pytest.mark.asyncio
    async def test_steer_agent(self, guardian, mock_agent_manager, mock_db_manager):
        """Test steering message sent to agent."""
        agent = Agent(id="test-agent-4", current_task_id="task-4")

        # Mock database session
        mock_session = Mock()
        mock_db_manager.get_session.return_value = mock_session

        # Execute steering
        await guardian.steer_agent(
            agent=agent,
            steering_type="stuck",
            message="Try checking your imports"
        )

        # Verify message sent
        mock_agent_manager.send_message_to_agent.assert_called_once()
        call_args = mock_agent_manager.send_message_to_agent.call_args[0]
        assert call_args[0] == "test-agent-4"
        assert "GUARDIAN GUIDANCE" in call_args[1]
        assert "Try checking your imports" in call_args[1]

        # Verify logged
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_build_accumulated_context(self, guardian, mock_db_manager):
        """Test building accumulated context from agent logs."""
        agent = Agent(id="test-agent-5", current_task_id="task-5")

        # Mock logs
        mock_logs = [
            AgentLog(
                agent_id="test-agent-5",
                log_type="input",
                message="Build auth without external libraries",
                created_at=datetime.utcnow() - timedelta(minutes=10),
                details={}
            ),
            AgentLog(
                agent_id="test-agent-5",
                log_type="output",
                message="I'll implement JWT from scratch",
                created_at=datetime.utcnow() - timedelta(minutes=9),
                details={}
            )
        ]

        mock_task = Task(
            id="task-5",
            enriched_description="Build authentication",
            done_definition="Auth working"
        )

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_logs
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_task
        mock_db_manager.get_session.return_value = mock_session

        # Execute
        context = await guardian._build_accumulated_context(agent, [])

        # Assert
        assert context['overall_goal'] == "Build authentication"
        assert context['done_definition'] == "Auth working"
        assert context['conversation_length'] == 2
        assert isinstance(context['constraints'], list)
        assert isinstance(context['session_start'], datetime)

    def test_should_steer_agent(self, guardian):
        """Test steering throttling logic."""
        agent_id = "test-agent-6"

        # First steering should be allowed
        assert guardian._should_steer_agent(agent_id) is True

        # Record a steering
        guardian._record_steering(agent_id, "stuck", "test message")

        # Immediate second steering should be blocked
        assert guardian._should_steer_agent(agent_id) is False

        # Simulate time passing
        guardian.steering_history[agent_id][0]['timestamp'] = (
            datetime.utcnow() - timedelta(minutes=6)
        ).isoformat()

        # Now should be allowed again
        assert guardian._should_steer_agent(agent_id) is True

    def test_extract_last_error(self, guardian):
        """Test error extraction from output."""
        output = """
        Working on task...
        Error: Module not found
        at line 42
        continuing...
        """

        error = guardian._extract_last_error(output)
        assert "Error: Module not found" in error
        assert "at line 42" in error

    @pytest.mark.asyncio
    async def test_handle_missing_task(self, guardian):
        """Test handling when task not found."""
        agent = Agent(id="test-agent-7", current_task_id="missing-task")

        with patch.object(guardian, '_get_agent_task', return_value=None):
            with patch.object(guardian, '_build_accumulated_context', return_value={"overall_goal": "Unknown"}):
                result = await guardian.analyze_agent_with_trajectory(
                    agent=agent,
                    tmux_output="test",
                    past_summaries=[]
                )

        # Should return default analysis
        assert result['agent_id'] == "test-agent-7"
        assert result['summary'] == "GPT-5 analysis unavailable - using default"

    @pytest.mark.asyncio
    async def test_llm_failure_handling(self, guardian, mock_llm_provider):
        """Test handling when LLM analysis fails."""
        # Make LLM throw exception
        mock_llm_provider.analyze_agent_trajectory.side_effect = Exception("LLM Error")

        agent = Agent(id="test-agent-8", current_task_id="task-8")
        mock_task = Task(id="task-8", enriched_description="Test")

        with patch.object(guardian, '_build_accumulated_context', return_value={"overall_goal": "Test"}):
            with patch.object(guardian, '_get_agent_task', return_value=mock_task):
                result = await guardian.analyze_agent_with_trajectory(
                    agent=agent,
                    tmux_output="test",
                    past_summaries=[]
                )

        # Should return default analysis
        assert result['summary'] == "GPT-5 analysis unavailable - using default"
        assert result['trajectory_aligned'] is True  # Safe default

    def test_clear_agent_cache(self, guardian):
        """Test clearing agent cache."""
        agent_id = "test-agent-9"

        # Add to cache
        guardian.trajectory_cache[agent_id] = {"test": "data"}
        guardian.steering_history[agent_id] = [{"test": "history"}]

        # Clear cache
        guardian.clear_agent_cache(agent_id)

        # Verify cleared
        assert agent_id not in guardian.trajectory_cache
        assert agent_id not in guardian.steering_history


if __name__ == "__main__":
    pytest.main([__file__, "-v"])