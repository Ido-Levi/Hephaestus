"""Unit tests for the diagnostic agent system."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.monitoring.monitor import MonitoringLoop
from src.core.database import (
    DatabaseManager, Agent, Task, Workflow, Phase, WorkflowResult, DiagnosticRun
)
from src.core.simple_config import get_config


@pytest.fixture
def db_manager():
    """Create a test database manager."""
    import tempfile
    import os

    # Create temp database
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db = DatabaseManager(path)
    db.create_tables()

    yield db

    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def mock_agent_manager():
    """Create a mock agent manager."""
    manager = Mock()
    manager.create_agent_for_task = AsyncMock()
    manager.get_project_context = AsyncMock(return_value="Test context")
    return manager


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    return provider


@pytest.fixture
def mock_rag_system():
    """Create a mock RAG system."""
    rag = Mock()
    return rag


@pytest.fixture
def mock_phase_manager(db_manager):
    """Create a mock phase manager."""
    manager = Mock()
    manager.workflow_id = "test-workflow-123"
    manager.get_workflow_config = Mock()

    # Create mock workflow config
    workflow_config = Mock()
    workflow_config.result_criteria = "Test workflow goal: solve the puzzle"
    manager.get_workflow_config.return_value = workflow_config

    return manager


@pytest.fixture
def monitoring_loop(db_manager, mock_agent_manager, mock_llm_provider, mock_rag_system, mock_phase_manager):
    """Create a monitoring loop for testing."""
    loop = MonitoringLoop(
        db_manager=db_manager,
        agent_manager=mock_agent_manager,
        llm_provider=mock_llm_provider,
        rag_system=mock_rag_system,
        phase_manager=mock_phase_manager,
    )
    return loop


@pytest.fixture
def workflow_with_phases(db_manager, mock_phase_manager):
    """Create a test workflow with phases."""
    session = db_manager.get_session()
    try:
        # Create workflow
        workflow = Workflow(
            id="test-workflow-123",
            name="Test Workflow",
            phases_folder_path="/tmp/test",
            status="active",
        )
        session.add(workflow)

        # Create phases
        phase1 = Phase(
            id="phase-1",
            workflow_id="test-workflow-123",
            order=1,
            name="Phase 1",
            description="Planning phase",
            done_definitions=["Create plan", "Review plan"],
        )
        phase2 = Phase(
            id="phase-2",
            workflow_id="test-workflow-123",
            order=2,
            name="Phase 2",
            description="Implementation phase",
            done_definitions=["Implement solution"],
        )
        session.add(phase1)
        session.add(phase2)
        session.commit()

        return workflow
    finally:
        session.close()


class TestDiagnosticAgentTriggers:
    """Test diagnostic agent trigger conditions."""

    @pytest.mark.asyncio
    async def test_no_trigger_when_no_workflow(self, monitoring_loop):
        """Should not trigger when no workflow exists."""
        monitoring_loop.phase_manager.workflow_id = None

        await monitoring_loop._check_workflow_stuck_state()

        # Should not create any agents
        monitoring_loop.agent_manager.create_agent_for_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_trigger_when_no_tasks(self, monitoring_loop, workflow_with_phases):
        """Should not trigger when no tasks exist."""
        await monitoring_loop._check_workflow_stuck_state()

        # Should not create diagnostic agent
        monitoring_loop.agent_manager.create_agent_for_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_trigger_when_tasks_active(self, monitoring_loop, workflow_with_phases, db_manager):
        """Should not trigger when tasks are still active."""
        session = db_manager.get_session()
        try:
            # Create active task
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="in_progress",  # Active
                workflow_id="test-workflow-123",
                phase_id="phase-1",
            )
            session.add(task)
            session.commit()
        finally:
            session.close()

        await monitoring_loop._check_workflow_stuck_state()

        # Should not create diagnostic agent
        monitoring_loop.agent_manager.create_agent_for_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_trigger_when_validated_result_exists(self, monitoring_loop, workflow_with_phases, db_manager):
        """Should not trigger when workflow has validated result."""
        session = db_manager.get_session()
        try:
            # Create completed task
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="done",
                workflow_id="test-workflow-123",
                phase_id="phase-1",
                completed_at=datetime.utcnow() - timedelta(minutes=5),
            )
            session.add(task)

            # Create validated result
            result = WorkflowResult(
                id="result-1",
                workflow_id="test-workflow-123",
                agent_id="agent-1",
                result_file_path="/tmp/result.md",
                result_content="Success!",
                status="validated",
            )
            session.add(result)
            session.commit()
        finally:
            session.close()

        await monitoring_loop._check_workflow_stuck_state()

        # Should not create diagnostic agent
        monitoring_loop.agent_manager.create_agent_for_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_trigger_during_cooldown(self, monitoring_loop, workflow_with_phases, db_manager):
        """Should not trigger if cooldown hasn't passed."""
        session = db_manager.get_session()
        try:
            # Create completed task
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="done",
                workflow_id="test-workflow-123",
                phase_id="phase-1",
                completed_at=datetime.utcnow() - timedelta(minutes=5),
            )
            session.add(task)

            # Create recent diagnostic run (within cooldown)
            diagnostic = DiagnosticRun(
                id="diag-1",
                workflow_id="test-workflow-123",
                triggered_at=datetime.utcnow() - timedelta(seconds=30),  # 30s ago < 60s cooldown
                total_tasks_at_trigger=1,
                done_tasks_at_trigger=1,
                failed_tasks_at_trigger=0,
                time_since_last_task_seconds=300,
                workflow_goal="Test goal",
            )
            session.add(diagnostic)
            session.commit()
        finally:
            session.close()

        await monitoring_loop._check_workflow_stuck_state()

        # Should not create diagnostic agent
        monitoring_loop.agent_manager.create_agent_for_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_trigger_when_not_stuck_long_enough(self, monitoring_loop, workflow_with_phases, db_manager):
        """Should not trigger if stuck time is too short."""
        session = db_manager.get_session()
        try:
            # Create recently completed task
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="done",
                workflow_id="test-workflow-123",
                phase_id="phase-1",
                completed_at=datetime.utcnow() - timedelta(seconds=30),  # 30s ago < 60s minimum
            )
            session.add(task)
            session.commit()
        finally:
            session.close()

        await monitoring_loop._check_workflow_stuck_state()

        # Should not create diagnostic agent
        monitoring_loop.agent_manager.create_agent_for_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_triggers_when_all_conditions_met(self, monitoring_loop, workflow_with_phases, db_manager):
        """Should trigger diagnostic when all conditions are met."""
        session = db_manager.get_session()
        try:
            # Create old completed task
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="done",
                workflow_id="test-workflow-123",
                phase_id="phase-1",
                completed_at=datetime.utcnow() - timedelta(minutes=5),  # 5 min ago > 60s minimum
            )
            session.add(task)
            session.commit()
        finally:
            session.close()

        # Mock the agent creation
        mock_agent = Mock()
        mock_agent.id = "diagnostic-agent-1"
        monitoring_loop.agent_manager.create_agent_for_task.return_value = mock_agent

        await monitoring_loop._check_workflow_stuck_state()

        # Should create diagnostic agent
        monitoring_loop.agent_manager.create_agent_for_task.assert_called_once()


class TestDiagnosticContextGathering:
    """Test context gathering for diagnostic agents."""

    @pytest.mark.asyncio
    async def test_gathers_workflow_goal(self, monitoring_loop, workflow_with_phases, db_manager):
        """Should gather workflow goal from config."""
        # Create a completed task
        session = db_manager.get_session()
        try:
            task = Task(
                id="task-1",
                raw_description="Test",
                enriched_description="Test",
                done_definition="Done",
                status="done",
                workflow_id="test-workflow-123",
                phase_id="phase-1",
            )
            session.add(task)
            session.commit()

            # Refresh to get the task with all attributes
            session.refresh(task)
            tasks = [task]

            context = await monitoring_loop._gather_diagnostic_context(
                "test-workflow-123",
                tasks,
                120.0
            )

            assert context['workflow_goal'] == "Test workflow goal: solve the puzzle"
        finally:
            session.close()

    @pytest.mark.asyncio
    async def test_gathers_phases_summary(self, monitoring_loop, workflow_with_phases, db_manager):
        """Should gather all phases with progress."""
        session = db_manager.get_session()
        try:
            task = Task(
                id="task-1",
                raw_description="Test",
                enriched_description="Test",
                done_definition="Done",
                status="done",
                workflow_id="test-workflow-123",
                phase_id="phase-1",
            )
            session.add(task)
            session.commit()

            # Refresh to get the task with all attributes
            session.refresh(task)
            tasks = [task]

            context = await monitoring_loop._gather_diagnostic_context(
                "test-workflow-123",
                tasks,
                120.0
            )

            assert len(context['phases_summary']) == 2
            phase1 = context['phases_summary'][0]
            assert phase1['name'] == "Phase 1"
            assert phase1['task_count'] == 1
            assert phase1['done_task_count'] == 1
        finally:
            session.close()


class TestDiagnosticPromptGeneration:
    """Test diagnostic prompt generation."""

    @pytest.mark.asyncio
    async def test_generates_valid_prompt(self, monitoring_loop):
        """Should generate prompt from template."""
        context = {
            'workflow_goal': "Test goal",
            'workflow_id': "workflow-123",
            'phases_summary': [{
                'id': 'phase-1',
                'name': 'Phase 1',
                'order': 1,
                'description': 'Test phase',
                'done_definitions': ['Task 1', 'Task 2'],
                'task_count': 5,
                'done_task_count': 3,
            }],
            'agents_summary': [{
                'agent_id': 'agent-1',
                'task_id': 'task-1',
                'task_description': 'Do something',
                'task_status': 'done',
                'completion_notes': 'Completed successfully',
                'failure_reason': None,
                'phase_id': 'phase-1',
                'created_at': '2025-01-01T10:00:00',
                'agent_type': 'phase',
            }],
            'conductor_overviews': [],
            'submitted_results': [],
            'total_tasks': 5,
            'tasks_by_phase': {'Phase 1': {'total': 5, 'done': 3, 'failed': 0}},
            'time_since_last_task': 120,
        }

        prompt = await monitoring_loop._generate_diagnostic_prompt(context)

        # Check prompt contains key sections
        assert "Test goal" in prompt
        assert "Phase 1" in prompt
        assert "agent-1" in prompt
        assert "Do something" in prompt
        assert "2.0 minutes" in prompt  # 120 seconds formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
