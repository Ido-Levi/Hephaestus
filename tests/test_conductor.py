"""Unit tests for the Conductor system orchestration."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.monitoring.conductor import Conductor, SystemDecision
from src.core.database import AgentLog


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
    mock.send_message_to_agent = Mock()
    mock.terminate_agent = AsyncMock()
    return mock


@pytest.fixture
def conductor(mock_db_manager, mock_agent_manager):
    """Create Conductor instance with mocked dependencies."""
    return Conductor(
        db_manager=mock_db_manager,
        agent_manager=mock_agent_manager
    )


class TestConductor:
    """Test the Conductor system orchestration."""

    @pytest.mark.asyncio
    async def test_analyze_system_state_with_duplicates(self, conductor):
        """Test Conductor detects duplicate work."""
        # Mock LLM provider - patch where it's used, not where it's defined
        with patch('src.interfaces.get_llm_provider') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.analyze_system_coherence = AsyncMock(return_value={
                "coherence_score": 0.5,
                "duplicates": [
                    {
                        "agent1": "agent-1",
                        "agent2": "agent-2",
                        "similarity": 0.9,
                        "work": "Both implementing authentication"
                    }
                ],
                "alignment_issues": ["Two agents duplicating work"],
                "termination_recommendations": [
                    {
                        "agent_id": "agent-2",
                        "reason": "Duplicate with agent-1"
                    }
                ],
                "coordination_needs": [],
                "system_summary": "System has duplicates needing resolution"
            })
            mock_get_llm.return_value = mock_llm

            # Guardian summaries showing duplicate work
            summaries = [
                {
                    "agent_id": "agent-1",
                    "trajectory_summary": "Implementing auth module",
                    "accumulated_goal": "Build JWT authentication",
                    "current_phase": "implementation",
                    "trajectory_aligned": True,
                },
                {
                    "agent_id": "agent-2",
                    "trajectory_summary": "Creating auth system",
                    "accumulated_goal": "Implement JWT auth",
                    "current_phase": "implementation",
                    "trajectory_aligned": True,
                }
            ]

            # Execute
            result = await conductor.analyze_system_state(summaries)

        # Assert
        assert result['num_agents'] == 2
        assert len(result['duplicates']) == 1
        assert result['duplicates'][0]['agent1'] == "agent-1"
        assert result['duplicates'][0]['agent2'] == "agent-2"
        assert result['coherence']['score'] == 0.5

        # Check decisions
        assert len(result['decisions']) == 1
        assert result['decisions'][0]['type'] == SystemDecision.TERMINATE_DUPLICATE.value
        assert result['decisions'][0]['target'] == "agent-2"

    @pytest.mark.asyncio
    async def test_analyze_system_state_low_coherence(self, conductor):
        """Test Conductor handles low system coherence."""
        with patch('src.interfaces.get_llm_provider') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.analyze_system_coherence = AsyncMock(return_value={
                "coherence_score": 0.3,  # Very low coherence
                "duplicates": [],
                "alignment_issues": [
                    "Agents working on unrelated tasks",
                    "No coordination between agents"
                ],
                "termination_recommendations": [],
                "coordination_needs": [],
                "system_summary": "System coherence critically low"
            })
            mock_get_llm.return_value = mock_llm

            summaries = [{"agent_id": "agent-1"}, {"agent_id": "agent-2"}]
            result = await conductor.analyze_system_state(summaries)

        # Should escalate due to low coherence
        assert result['coherence']['score'] == 0.3
        escalation_decisions = [d for d in result['decisions']
                               if d['type'] == SystemDecision.ESCALATE.value]
        assert len(escalation_decisions) == 1
        assert "too low" in escalation_decisions[0]['reason']

    @pytest.mark.asyncio
    async def test_analyze_system_state_coordination_needs(self, conductor):
        """Test Conductor identifies resource coordination needs."""
        with patch('src.interfaces.get_llm_provider') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.analyze_system_coherence = AsyncMock(return_value={
                "coherence_score": 0.7,
                "duplicates": [],
                "alignment_issues": [],
                "termination_recommendations": [],
                "coordination_needs": [
                    {
                        "agents": ["agent-1", "agent-2"],
                        "resource": "database/schema.sql",
                        "action": "agent-1 goes first"
                    }
                ],
                "system_summary": "Good coherence but needs coordination"
            })
            mock_get_llm.return_value = mock_llm

            summaries = [{"agent_id": "agent-1"}, {"agent_id": "agent-2"}]
            result = await conductor.analyze_system_state(summaries)

        # Check coordination decision
        coord_decisions = [d for d in result['decisions']
                          if d['type'] == SystemDecision.COORDINATE_RESOURCES.value]
        assert len(coord_decisions) == 1
        assert coord_decisions[0]['resource'] == "database/schema.sql"
        assert set(coord_decisions[0]['agents']) == {"agent-1", "agent-2"}

    @pytest.mark.asyncio
    async def test_empty_summaries(self, conductor):
        """Test Conductor handles empty agent list."""
        result = await conductor.analyze_system_state([])

        assert result['num_agents'] == 0
        assert result['system_status'] == "No agents active"
        assert len(result['decisions']) == 0
        assert result['coherence']['score'] == 1.0  # Perfect when no agents

    @pytest.mark.asyncio
    async def test_execute_duplicate_termination(self, conductor, mock_agent_manager, mock_db_manager):
        """Test executing duplicate termination decision."""
        mock_session = Mock()
        mock_db_manager.get_session.return_value = mock_session

        decision = {
            "type": SystemDecision.TERMINATE_DUPLICATE.value,
            "target": "agent-duplicate",
            "reason": "Duplicate work with agent-primary"
        }

        await conductor.execute_decisions([decision])

        # Verify termination
        mock_agent_manager.terminate_agent.assert_called_once_with("agent-duplicate")
        mock_session.add.assert_called()  # Log added
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_execute_resource_coordination(self, conductor, mock_agent_manager):
        """Test executing resource coordination decision."""
        decision = {
            "type": SystemDecision.COORDINATE_RESOURCES.value,
            "agents": ["agent-1", "agent-2"],
            "resource": "config.json"
        }

        await conductor.execute_decisions([decision])

        # Verify coordination messages sent
        assert mock_agent_manager.send_message_to_agent.call_count == 2
        calls = mock_agent_manager.send_message_to_agent.call_args_list

        # First agent gets priority
        assert "priority access" in calls[0][0][1]
        # Second agent waits
        assert "wait for agent" in calls[1][0][1]

    @pytest.mark.asyncio
    async def test_execute_escalation(self, conductor):
        """Test executing escalation decision."""
        decision = {
            "type": SystemDecision.ESCALATE.value,
            "reason": "System coherence too low",
            "details": ["Multiple issues detected"]
        }

        with patch('src.monitoring.conductor.logger') as mock_logger:
            await conductor.execute_decisions([decision])

            # Verify critical logging
            mock_logger.critical.assert_called()
            calls = [str(call) for call in mock_logger.critical.call_args_list]
            assert any("CONDUCTOR ESCALATION" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_llm_failure_handling(self, conductor):
        """Test handling when LLM analysis fails."""
        with patch('src.interfaces.get_llm_provider') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.analyze_system_coherence = AsyncMock(side_effect=Exception("LLM Error"))
            mock_get_llm.return_value = mock_llm

            summaries = [{"agent_id": "agent-1"}]
            result = await conductor.analyze_system_state(summaries)

        # Should return empty analysis on failure
        assert result['num_agents'] == 0
        assert result['system_status'] == "No agents active"

    def test_get_system_summary(self, conductor):
        """Test getting system summary."""
        # Before any analysis
        summary = conductor.get_system_summary()
        assert "not yet analyzed" in summary

        # After analysis
        conductor.system_state = {
            "last_analysis": datetime.utcnow(),
            "duplicate_pairs": [{"agent1": "a", "agent2": "b"}],
            "coherence_score": 0.75
        }

        summary = conductor.get_system_summary()
        assert "1 duplicates" in summary
        assert "0.75" in summary

    @pytest.mark.asyncio
    async def test_generate_detailed_report(self, conductor):
        """Test generating detailed system report."""
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "num_agents": 3,
            "system_status": "3 agents working on tasks",
            "coherence": {
                "score": 0.8,
                "issues": ["Minor alignment issues"]
            },
            "duplicates": [
                {
                    "agent1": "agent-1",
                    "agent2": "agent-2",
                    "similarity": 0.9,
                    "work": "Authentication"
                }
            ],
            "decisions": [
                {
                    "type": SystemDecision.TERMINATE_DUPLICATE.value,
                    "target": "agent-2",
                    "reason": "Duplicate",
                    "confidence": 0.9
                }
            ],
            "gpt5_analysis": {
                "termination_recommendations": [
                    {"agent_id": "agent-2", "reason": "Duplicate"}
                ]
            }
        }

        report = await conductor.generate_detailed_report(analysis)

        # Verify report contains key sections
        assert "CONDUCTOR GPT-5 SYSTEM ANALYSIS REPORT" in report
        assert "Active Agents: 3" in report
        assert "SYSTEM COHERENCE" in report
        assert "Score: 0.80" in report
        assert "DUPLICATE WORK DETECTED" in report
        assert "CONDUCTOR DECISIONS" in report
        assert "GPT-5 TERMINATION RECOMMENDATIONS" in report

    @pytest.mark.asyncio
    async def test_execution_failure_handling(self, conductor, mock_agent_manager):
        """Test handling execution failures gracefully."""
        mock_agent_manager.terminate_agent.side_effect = Exception("Termination failed")

        decision = {
            "type": SystemDecision.TERMINATE_DUPLICATE.value,
            "target": "agent-fail",
            "reason": "Test"
        }

        # Should not raise, just log error
        await conductor.execute_decisions([decision])

        # Verify attempted
        mock_agent_manager.terminate_agent.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])