"""Test the Agent Trajectory Monitoring System."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.monitoring.guardian import Guardian, SteeringType, TrajectoryPhase
from src.monitoring.conductor import Conductor, SystemDecision
from src.monitoring.trajectory_context import TrajectoryContext
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
        "progress_estimate": 60,
        "needs_steering": False,
        "steering_type": None,
        "steering_recommendation": None,
        "trajectory_summary": "Agent implementing task successfully"
    })
    return mock


class TestGuardian:
    """Test Guardian monitoring with trajectory thinking."""

    @pytest.mark.asyncio
    async def test_guardian_trajectory_analysis(
        self,
        mock_db_manager,
        mock_agent_manager,
        mock_llm_provider,
    ):
        """Test Guardian analyzes agent with trajectory thinking."""
        # Setup Guardian
        guardian = Guardian(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=mock_llm_provider,
        )

        # Create test agent
        agent = Agent(
            id="test-agent-1",
            current_task_id="task-1",
            tmux_session_name="agent-test-1",
        )

        # Mock task retrieval
        mock_task = Task(
            id="task-1",
            raw_description="Implement authentication",
            enriched_description="Implement JWT authentication system",
            done_definition="Authentication working with tests",
        )

        with patch.object(guardian, '_get_agent_task', return_value=mock_task):
            with patch.object(guardian, '_build_accumulated_context', return_value={
                "overall_goal": "Implement JWT authentication",
                "constraints": ["no external libraries"],
                "session_start": datetime.utcnow() - timedelta(minutes=5),
            }):
                # Perform analysis
                result = await guardian.analyze_agent_with_trajectory(
                    agent=agent,
                    tmux_output="Creating auth module...",
                    past_summaries=[],
                )

        # Verify results
        assert result['agent_id'] == "test-agent-1"
        assert result['trajectory_aligned'] is True
        assert result['alignment_score'] == 0.8
        assert result['current_phase'] == "implementation"
        assert result['progress_percentage'] == 60

    @pytest.mark.asyncio
    async def test_guardian_detects_constraint_violation(
        self,
        mock_db_manager,
        mock_agent_manager,
        mock_llm_provider,
    ):
        """Test Guardian detects constraint violations."""
        guardian = Guardian(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=mock_llm_provider,
        )

        agent = Agent(
            id="test-agent-2",
            current_task_id="task-2",
        )

        mock_task = Task(
            id="task-2",
            enriched_description="Build simple API",
            done_definition="API endpoints working",
        )

        # Setup to detect violation
        with patch.object(guardian, '_get_agent_task', return_value=mock_task):
            with patch.object(guardian, '_build_accumulated_context', return_value={
                "overall_goal": "Build simple API",
                "constraints": ["no external libraries", "keep it simple"],
                "session_start": datetime.utcnow(),
            }):
                with patch.object(guardian, '_check_trajectory_alignment', return_value={
                    "aligned": False,
                    "score": 0.3,
                    "issues": ["Installing packages violates: no external libraries"],
                    "progress": 20,
                }):
                    result = await guardian.analyze_agent_with_trajectory(
                        agent=agent,
                        tmux_output="pip install requests flask sqlalchemy",
                        past_summaries=[],
                    )

        # Should detect misalignment
        assert result['trajectory_aligned'] is False
        assert result['alignment_score'] < 0.5

    @pytest.mark.asyncio
    async def test_guardian_steering_decision(
        self,
        mock_db_manager,
        mock_agent_manager,
        mock_llm_provider,
    ):
        """Test Guardian makes appropriate steering decisions."""
        guardian = Guardian(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=mock_llm_provider,
        )

        # Test steering for stuck agent
        agent = Agent(id="test-agent-3", current_task_id="task-3")

        # Mock being stuck
        mock_llm_provider.analyze_agent_trajectory.return_value = {
            "current_phase": "implementation",
            "trajectory_aligned": False,
            "alignment_score": 0.4,
            "alignment_issues": ["Stuck on same error for 5 minutes"],
            "progress_estimate": 30,
            "needs_steering": True,
            "steering_type": "stuck",
            "steering_recommendation": "Check your imports",
            "trajectory_summary": "Agent stuck on error"
        }

        await guardian.steer_agent(
            agent=agent,
            steering_type="stuck",
            message="The error suggests missing import. Check the top of the file.",
        )

        # Verify steering message sent
        mock_agent_manager.send_message_to_agent.assert_called_once()
        call_args = mock_agent_manager.send_message_to_agent.call_args
        assert "GUARDIAN GUIDANCE" in call_args[0][1]


class TestConductor:
    """Test Conductor system orchestration."""

    @pytest.mark.asyncio
    async def test_conductor_detects_duplicates(
        self,
        mock_db_manager,
        mock_agent_manager,
    ):
        """Test Conductor detects duplicate work."""
        conductor = Conductor(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
        )

        # Create Guardian summaries showing duplicate work
        summaries = [
            {
                "agent_id": "agent-1",
                "summary": "Implementing authentication module",
                "accumulated_goal": "Build JWT authentication system",
                "current_phase": "implementation",
                "progress_percentage": 60,
                "trajectory_aligned": True,
            },
            {
                "agent_id": "agent-2",
                "summary": "Creating auth system with JWT",
                "accumulated_goal": "Implement JWT auth module",
                "current_phase": "implementation",
                "progress_percentage": 40,
                "trajectory_aligned": True,
            },
            {
                "agent_id": "agent-3",
                "summary": "Building user profile API",
                "accumulated_goal": "Create user profile endpoints",
                "current_phase": "planning",
                "progress_percentage": 20,
                "trajectory_aligned": True,
            },
        ]

        result = await conductor.analyze_system_state(summaries)

        # Should detect agents 1 and 2 doing similar work
        assert len(result['duplicates']) > 0
        duplicate = result['duplicates'][0]
        assert 'agent-1' in [duplicate['agent1'], duplicate['agent2']]
        assert 'agent-2' in [duplicate['agent1'], duplicate['agent2']]

    @pytest.mark.asyncio
    async def test_conductor_system_coherence(
        self,
        mock_db_manager,
        mock_agent_manager,
    ):
        """Test Conductor evaluates system coherence."""
        conductor = Conductor(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
        )

        # Mix of aligned and misaligned agents
        summaries = [
            {
                "agent_id": "agent-1",
                "summary": "On track with task",
                "trajectory_aligned": True,
                "needs_steering": False,
                "progress_percentage": 70,
            },
            {
                "agent_id": "agent-2",
                "summary": "Drifting from goal",
                "trajectory_aligned": False,
                "needs_steering": True,
                "progress_percentage": 20,
            },
            {
                "agent_id": "agent-3",
                "summary": "Stuck on error",
                "trajectory_aligned": False,
                "needs_steering": True,
                "progress_percentage": 10,
            },
        ]

        result = await conductor.analyze_system_state(summaries)

        # System coherence should be degraded
        coherence = result['coherence']
        assert coherence['score'] < 0.7  # Low due to misaligned agents
        assert coherence['misaligned_agents'] == 2
        assert len(coherence['issues']) > 0

    @pytest.mark.asyncio
    async def test_conductor_makes_decisions(
        self,
        mock_db_manager,
        mock_agent_manager,
    ):
        """Test Conductor makes appropriate system decisions."""
        conductor = Conductor(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
        )

        # Setup scenario requiring decisions
        summaries = [
            {
                "agent_id": "agent-dup-1",
                "accumulated_goal": "Build API",
                "summary": "Creating REST API",
                "current_phase": "implementation",
                "progress_percentage": 30,
            },
            {
                "agent_id": "agent-dup-2",
                "accumulated_goal": "Build API",
                "summary": "Implementing REST endpoints",
                "current_phase": "implementation",
                "progress_percentage": 25,
            },
        ]

        with patch.object(conductor, '_calculate_work_similarity', return_value=0.9):
            result = await conductor.analyze_system_state(summaries)

        # Should recommend terminating duplicate
        decisions = result['decisions']
        assert len(decisions) > 0
        assert decisions[0]['type'] == SystemDecision.TERMINATE_DUPLICATE.value


class TestTrajectoryContext:
    """Test Trajectory Context Manager."""

    def test_build_accumulated_context(self, mock_db_manager):
        """Test building accumulated context from logs."""
        context_manager = TrajectoryContext(db_manager=mock_db_manager)

        # Mock agent logs
        mock_logs = [
            AgentLog(
                agent_id="agent-1",
                log_type="input",
                message="Build authentication without external libraries",
                created_at=datetime.utcnow() - timedelta(minutes=10),
            ),
            AgentLog(
                agent_id="agent-1",
                log_type="output",
                message="I'll implement JWT authentication from scratch",
                created_at=datetime.utcnow() - timedelta(minutes=9),
            ),
            AgentLog(
                agent_id="agent-1",
                log_type="input",
                message="Make sure it's simple and well-tested",
                created_at=datetime.utcnow() - timedelta(minutes=5),
            ),
        ]

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_logs
        mock_db_manager.get_session.return_value = mock_session

        context = context_manager.build_accumulated_context("agent-1")

        # Should extract constraints and goals
        assert "overall_goal" in context
        assert "constraints" in context
        assert "standing_instructions" in context
        assert context["conversation_length"] == 3

    def test_check_constraint_violations(self, mock_db_manager):
        """Test constraint violation detection."""
        context_manager = TrajectoryContext(db_manager=mock_db_manager)

        constraints = [
            "no external libraries",
            "keep it simple",
            "avoid complex patterns",
        ]

        # Test violation detection
        has_violation, violations = context_manager.check_constraint_violations(
            action="pip install requests",
            constraints=constraints,
        )

        assert has_violation is True
        assert "no external libraries" in violations

        # Test no violation
        has_violation, violations = context_manager.check_constraint_violations(
            action="import json",
            constraints=constraints,
        )

        assert has_violation is False
        assert len(violations) == 0


@pytest.mark.asyncio
async def test_full_monitoring_cycle():
    """Test complete monitoring cycle with Guardian and Conductor."""
    # This would be an integration test with all components
    # For brevity, showing the structure:

    # 1. Setup monitoring loop with trajectory components
    # 2. Add test agents with various states
    # 3. Run one monitoring cycle
    # 4. Verify:
    #    - Guardian analyses performed for each agent
    #    - Steering messages sent where needed
    #    - Conductor analyzed system state
    #    - Duplicates detected and handled
    #    - System coherence evaluated

    pass  # Full implementation would require more setup


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])