"""Integration tests for the complete monitoring system."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from src.monitoring.guardian import Guardian
from src.monitoring.conductor import Conductor
from src.monitoring.trajectory_context import TrajectoryContext
from src.monitoring.prompt_loader import PromptLoader
from src.core.database import Agent, Task, AgentLog
from src.agents.manager import AgentManager


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
    mock.terminate_agent = AsyncMock()
    mock.tmux_server = Mock()
    return mock


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    mock = AsyncMock()
    mock.analyze_agent_trajectory = AsyncMock()
    mock.analyze_system_coherence = AsyncMock()
    return mock


@pytest.fixture
def monitoring_system(mock_db_manager, mock_agent_manager, mock_llm_provider):
    """Create complete monitoring system."""
    guardian = Guardian(
        db_manager=mock_db_manager,
        agent_manager=mock_agent_manager,
        llm_provider=mock_llm_provider
    )

    conductor = Conductor(
        db_manager=mock_db_manager,
        agent_manager=mock_agent_manager
    )

    trajectory_context = TrajectoryContext(db_manager=mock_db_manager)

    return {
        "guardian": guardian,
        "conductor": conductor,
        "trajectory_context": trajectory_context,
        "llm_provider": mock_llm_provider
    }


class TestMonitoringIntegration:
    """Test the complete monitoring system integration."""

    @pytest.mark.asyncio
    async def test_full_monitoring_cycle_healthy_agents(self, monitoring_system, mock_db_manager, mock_agent_manager):
        """Test full monitoring cycle with healthy, aligned agents."""
        # Setup agents and tasks
        agents = [
            Agent(id="agent-1", current_task_id="task-1", tmux_session_name="agent-1"),
            Agent(id="agent-2", current_task_id="task-2", tmux_session_name="agent-2"),
            Agent(id="agent-3", current_task_id="task-3", tmux_session_name="agent-3")
        ]

        tasks = [
            Task(id="task-1", enriched_description="Build auth API", done_definition="Auth working"),
            Task(id="task-2", enriched_description="Create frontend", done_definition="UI complete"),
            Task(id="task-3", enriched_description="Write tests", done_definition="90% coverage")
        ]

        # Mock database responses
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.all.return_value = agents
        mock_session.query.return_value.filter_by.return_value.first.side_effect = tasks
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_db_manager.get_session.return_value = mock_session

        # Mock healthy Guardian analyses
        monitoring_system["llm_provider"].analyze_agent_trajectory.side_effect = [
            {
                "current_phase": "implementation",
                "trajectory_aligned": True,
                "alignment_score": 0.9,
                "needs_steering": False,
                "trajectory_summary": "Agent 1 building auth API successfully"
            },
            {
                "current_phase": "implementation",
                "trajectory_aligned": True,
                "alignment_score": 0.85,
                "needs_steering": False,
                "trajectory_summary": "Agent 2 creating frontend components"
            },
            {
                "current_phase": "testing",
                "trajectory_aligned": True,
                "alignment_score": 0.8,
                "needs_steering": False,
                "trajectory_summary": "Agent 3 writing comprehensive tests"
            }
        ]

        # Mock healthy Conductor analysis
        monitoring_system["llm_provider"].analyze_system_coherence.return_value = {
            "coherence_score": 0.9,
            "duplicates": [],
            "alignment_issues": [],
            "termination_recommendations": [],
            "coordination_needs": [],
            "system_summary": "All 3 agents working efficiently on separate tasks"
        }

        # Execute monitoring cycle
        guardian = monitoring_system["guardian"]
        conductor = monitoring_system["conductor"]

        # Step 1: Guardian analyzes each agent
        guardian_summaries = []
        for agent in agents:
            summary = await guardian.analyze_agent_with_trajectory(
                agent=agent,
                tmux_output=f"Working on {agent.current_task_id}",
                past_summaries=[]
            )
            guardian_summaries.append(summary)

        # Verify Guardian analyses
        assert len(guardian_summaries) == 3
        assert all(s["trajectory_aligned"] for s in guardian_summaries)
        assert all(not s["needs_steering"] for s in guardian_summaries)

        # Step 2: Conductor analyzes system
        system_analysis = await conductor.analyze_system_state(guardian_summaries)

        # Verify Conductor analysis
        assert system_analysis["coherence"]["score"] == 0.9
        assert len(system_analysis["duplicates"]) == 0
        assert len(system_analysis["decisions"]) == 0  # No interventions needed

        # Verify no steering or termination
        mock_agent_manager.send_message_to_agent.assert_not_called()
        mock_agent_manager.terminate_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_monitoring_with_duplicate_detection(self, monitoring_system, mock_db_manager, mock_agent_manager):
        """Test monitoring detects and handles duplicate work."""
        agents = [
            Agent(id="agent-1", current_task_id="task-1"),
            Agent(id="agent-2", current_task_id="task-2")
        ]

        # Mock database
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.all.return_value = agents
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock(
            enriched_description="Build auth"
        )
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_db_manager.get_session.return_value = mock_session

        # Mock Guardian showing similar work
        monitoring_system["llm_provider"].analyze_agent_trajectory.side_effect = [
            {
                "current_phase": "implementation",
                "trajectory_aligned": True,
                "alignment_score": 0.8,
                "needs_steering": False,
                "trajectory_summary": "Building JWT authentication"
            },
            {
                "current_phase": "implementation",
                "trajectory_aligned": True,
                "alignment_score": 0.7,
                "needs_steering": False,
                "trajectory_summary": "Implementing JWT auth system"
            }
        ]

        # Mock Conductor detecting duplicates
        monitoring_system["llm_provider"].analyze_system_coherence.return_value = {
            "coherence_score": 0.5,
            "duplicates": [
                {
                    "agent1": "agent-1",
                    "agent2": "agent-2",
                    "similarity": 0.9,
                    "work": "Both implementing JWT authentication"
                }
            ],
            "termination_recommendations": [
                {
                    "agent_id": "agent-2",
                    "reason": "Duplicate with agent-1 who is further along"
                }
            ],
            "alignment_issues": ["Two agents duplicating auth work"],
            "coordination_needs": [],
            "system_summary": "Duplicate work detected on authentication"
        }

        guardian = monitoring_system["guardian"]
        conductor = monitoring_system["conductor"]

        # Execute monitoring
        summaries = []
        for agent in agents:
            summary = await guardian.analyze_agent_with_trajectory(agent, "working", [])
            summaries.append(summary)

        system_analysis = await conductor.analyze_system_state(summaries)

        # Verify duplicate detection
        assert len(system_analysis["duplicates"]) == 1
        assert system_analysis["duplicates"][0]["similarity"] == 0.9

        # Execute decisions
        await conductor.execute_decisions(system_analysis["decisions"])

        # Verify termination was called
        mock_agent_manager.terminate_agent.assert_called_once_with("agent-2")

    @pytest.mark.asyncio
    async def test_monitoring_with_steering_intervention(self, monitoring_system, mock_db_manager, mock_agent_manager):
        """Test monitoring steers agents that need guidance."""
        agent = Agent(id="agent-stuck", current_task_id="task-1")

        # Mock database
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.all.return_value = [agent]
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock(
            enriched_description="Build API"
        )
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [
            AgentLog(
                agent_id="agent-stuck",
                log_type="input",
                message="Build API without external libs",
                created_at=datetime.utcnow() - timedelta(hours=1),
                details={}
            )
        ]
        mock_db_manager.get_session.return_value = mock_session

        # Mock Guardian detecting steering need
        monitoring_system["llm_provider"].analyze_agent_trajectory.return_value = {
            "current_phase": "stuck",
            "trajectory_aligned": False,
            "alignment_score": 0.3,
            "needs_steering": True,
            "steering_type": "violating_constraints",
            "steering_recommendation": "Remember: no external libraries allowed",
            "trajectory_summary": "Agent trying to install Flask"
        }

        guardian = monitoring_system["guardian"]

        # Analyze agent
        summary = await guardian.analyze_agent_with_trajectory(
            agent=agent,
            tmux_output="pip install flask",
            past_summaries=[]
        )

        # Verify steering needed
        assert summary["needs_steering"] is True
        assert summary["steering_type"] == "violating_constraints"

        # Execute steering
        await guardian.steer_agent(
            agent=agent,
            steering_type=summary["steering_type"],
            message=summary["steering_message"]
        )

        # Verify steering message sent
        mock_agent_manager.send_message_to_agent.assert_called_once()
        call_args = mock_agent_manager.send_message_to_agent.call_args[0]
        assert "GUARDIAN GUIDANCE" in call_args[1]
        assert "no external libraries" in call_args[1]

    @pytest.mark.asyncio
    async def test_monitoring_with_resource_coordination(self, monitoring_system, mock_db_manager, mock_agent_manager):
        """Test monitoring coordinates resource access between agents."""
        agents = [
            Agent(id="agent-1", current_task_id="task-1"),
            Agent(id="agent-2", current_task_id="task-2")
        ]

        # Mock database
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.all.return_value = agents
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock(
            enriched_description="Modify schema"
        )
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_db_manager.get_session.return_value = mock_session

        # Mock Guardian analyses
        monitoring_system["llm_provider"].analyze_agent_trajectory.side_effect = [
            {
                "current_phase": "implementation",
                "trajectory_aligned": True,
                "alignment_score": 0.8,
                "needs_steering": False,
                "trajectory_summary": "Modifying database schema"
            },
            {
                "current_phase": "implementation",
                "trajectory_aligned": True,
                "alignment_score": 0.8,
                "needs_steering": False,
                "trajectory_summary": "Updating schema file"
            }
        ]

        # Mock Conductor detecting resource conflict
        monitoring_system["llm_provider"].analyze_system_coherence.return_value = {
            "coherence_score": 0.7,
            "duplicates": [],
            "alignment_issues": ["Two agents modifying same schema file"],
            "termination_recommendations": [],
            "coordination_needs": [
                {
                    "agents": ["agent-1", "agent-2"],
                    "resource": "database/schema.sql",
                    "action": "agent-1 completes first, then agent-2"
                }
            ],
            "system_summary": "Agents need coordination for schema access"
        }

        guardian = monitoring_system["guardian"]
        conductor = monitoring_system["conductor"]

        # Execute monitoring
        summaries = []
        for agent in agents:
            summary = await guardian.analyze_agent_with_trajectory(agent, "working", [])
            summaries.append(summary)

        system_analysis = await conductor.analyze_system_state(summaries)

        # Verify coordination needed
        assert len(system_analysis["decisions"]) == 1
        assert system_analysis["decisions"][0]["type"] == "coordinate_resources"

        # Execute coordination
        await conductor.execute_decisions(system_analysis["decisions"])

        # Verify coordination messages sent
        assert mock_agent_manager.send_message_to_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_monitoring_escalation_on_low_coherence(self, monitoring_system, mock_db_manager):
        """Test monitoring escalates when system coherence is too low."""
        agents = [Agent(id=f"agent-{i}", current_task_id=f"task-{i}") for i in range(5)]

        # Mock database
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.all.return_value = agents
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock(
            enriched_description="Various tasks"
        )
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_db_manager.get_session.return_value = mock_session

        # Mock Guardian analyses showing chaos
        monitoring_system["llm_provider"].analyze_agent_trajectory.return_value = {
            "current_phase": "confused",
            "trajectory_aligned": False,
            "alignment_score": 0.2,
            "needs_steering": True,
            "trajectory_summary": "Agent working on wrong task"
        }

        # Mock Conductor detecting system chaos
        monitoring_system["llm_provider"].analyze_system_coherence.return_value = {
            "coherence_score": 0.2,  # Very low
            "duplicates": [],
            "alignment_issues": [
                "Agents working on unrelated tasks",
                "No coordination",
                "Multiple conflicts"
            ],
            "termination_recommendations": [],
            "coordination_needs": [],
            "system_summary": "System in chaos, needs human intervention"
        }

        guardian = monitoring_system["guardian"]
        conductor = monitoring_system["conductor"]

        # Execute monitoring
        summaries = []
        for agent in agents:
            summary = await guardian.analyze_agent_with_trajectory(agent, "confused", [])
            summaries.append(summary)

        system_analysis = await conductor.analyze_system_state(summaries)

        # Verify escalation decision
        escalation = [d for d in system_analysis["decisions"]
                     if d["type"] == "escalate"]
        assert len(escalation) == 1
        assert "too low" in escalation[0]["reason"]

    @pytest.mark.asyncio
    async def test_monitoring_cache_usage(self, monitoring_system, mock_db_manager):
        """Test monitoring uses caching to avoid redundant analysis."""
        agent = Agent(id="agent-cached", current_task_id="task-1")

        # Mock database
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock(
            enriched_description="Test task"
        )
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_db_manager.get_session.return_value = mock_session

        # Mock LLM response
        monitoring_system["llm_provider"].analyze_agent_trajectory.return_value = {
            "current_phase": "implementation",
            "trajectory_aligned": True,
            "alignment_score": 0.8,
            "trajectory_summary": "Working well"
        }

        guardian = monitoring_system["guardian"]

        # First call should hit LLM
        await guardian.analyze_agent_with_trajectory(agent, "working", [])
        assert monitoring_system["llm_provider"].analyze_agent_trajectory.call_count == 1

        # Second call should use cache
        await guardian.analyze_agent_with_trajectory(agent, "working", [])
        assert monitoring_system["llm_provider"].analyze_agent_trajectory.call_count == 1  # Still 1

        # Verify cache exists
        assert "agent-cached" in guardian.trajectory_cache

    @pytest.mark.asyncio
    async def test_monitoring_error_recovery(self, monitoring_system, mock_db_manager):
        """Test monitoring handles errors gracefully."""
        agent = Agent(id="agent-error", current_task_id="task-1")

        # Mock database to throw error
        mock_db_manager.get_session.side_effect = Exception("Database error")

        guardian = monitoring_system["guardian"]

        # Should handle error and return default
        result = await guardian.analyze_agent_with_trajectory(agent, "test", [])

        assert result["agent_id"] == "agent-error"
        assert result["summary"] == "GPT-5 analysis unavailable - using default"
        assert result["trajectory_aligned"] is True  # Safe default

    @pytest.mark.asyncio
    async def test_full_monitor_loop_simulation(self, monitoring_system, mock_db_manager, mock_agent_manager):
        """Simulate a full monitoring loop as would be called by run_monitor.py."""
        # This simulates what run_monitor.py would do

        # Setup initial agents
        agents = [
            Agent(id="agent-1", current_task_id="task-1", health_status="healthy"),
            Agent(id="agent-2", current_task_id="task-2", health_status="healthy")
        ]

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.all.return_value = agents
        mock_session.query.return_value.filter_by.return_value.all.return_value = agents
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock(
            enriched_description="Test task"
        )
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_db_manager.get_session.return_value = mock_session

        # Mock healthy analyses
        monitoring_system["llm_provider"].analyze_agent_trajectory.return_value = {
            "current_phase": "implementation",
            "trajectory_aligned": True,
            "alignment_score": 0.8,
            "needs_steering": False,
            "trajectory_summary": "Working well"
        }

        monitoring_system["llm_provider"].analyze_system_coherence.return_value = {
            "coherence_score": 0.85,
            "duplicates": [],
            "alignment_issues": [],
            "termination_recommendations": [],
            "coordination_needs": [],
            "system_summary": "System running smoothly"
        }

        guardian = monitoring_system["guardian"]
        conductor = monitoring_system["conductor"]

        # Simulate monitoring loop iteration
        async def monitor_iteration():
            # Get all active agents
            active_agents = agents

            if not active_agents:
                return

            # Guardian analysis for each agent
            guardian_summaries = []
            for agent in active_agents:
                output = mock_agent_manager.get_agent_output(agent.tmux_session_name)
                summary = await guardian.analyze_agent_with_trajectory(
                    agent=agent,
                    tmux_output=output or "",
                    past_summaries=[]
                )

                # Handle steering if needed
                if summary.get("needs_steering"):
                    await guardian.steer_agent(
                        agent=agent,
                        steering_type=summary.get("steering_type", "guidance"),
                        message=summary.get("steering_message", "")
                    )

                guardian_summaries.append(summary)

            # Conductor system analysis
            if len(guardian_summaries) > 1:
                system_analysis = await conductor.analyze_system_state(guardian_summaries)

                # Execute any decisions
                if system_analysis.get("decisions"):
                    await conductor.execute_decisions(system_analysis["decisions"])

                return system_analysis

            return None

        # Run one iteration
        result = await monitor_iteration()

        # Verify monitoring ran successfully
        assert result is not None
        assert result["coherence"]["score"] == 0.85
        assert result["system_status"] == "2 agents active"
        assert len(result["decisions"]) == 0  # No interventions needed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])