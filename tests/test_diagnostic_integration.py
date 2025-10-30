"""Integration tests for the diagnostic agent system."""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.monitoring.monitor import MonitoringLoop
from src.core.database import (
    DatabaseManager, Agent, Task, Workflow, Phase, WorkflowResult, DiagnosticRun
)
from src.core.simple_config import get_config


# Capture logs for verification
class LogCapture(logging.Handler):
    """Custom logging handler to capture logs."""
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def get_messages(self, prefix=None):
        """Get all logged messages, optionally filtered by prefix."""
        messages = [record.getMessage() for record in self.records]
        if prefix:
            messages = [m for m in messages if prefix in m]
        return messages

    def clear(self):
        """Clear captured logs."""
        self.records = []


@pytest.fixture
def log_capture():
    """Create a log capture handler and attach it to the logger."""
    # Get the monitoring logger specifically
    monitor_logger = logging.getLogger("src.monitoring.monitor")

    # Also get root logger to catch all
    root_logger = logging.getLogger()

    # Create and attach our capture handler
    capture = LogCapture()
    capture.setLevel(logging.DEBUG)

    # Add to both loggers to ensure we catch everything
    monitor_logger.addHandler(capture)
    root_logger.addHandler(capture)

    # Make sure logger level allows DEBUG
    monitor_logger.setLevel(logging.DEBUG)
    root_logger.setLevel(logging.DEBUG)

    yield capture

    # Clean up
    monitor_logger.removeHandler(capture)
    root_logger.removeHandler(capture)


@pytest.fixture
def temp_db():
    """Create a temporary test database."""
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

    # Mock agent creation
    async def create_agent_mock(task, enriched_data, memories, project_context, agent_type,
                                use_existing_worktree=False, working_directory=None):
        mock_agent = Mock()
        mock_agent.id = f"diagnostic-agent-{task.id[:8]}"
        mock_agent.agent_type = agent_type
        mock_agent.current_task_id = task.id
        return mock_agent

    manager.create_agent_for_task = AsyncMock(side_effect=create_agent_mock)
    manager.get_project_context = AsyncMock(return_value="Test context")

    return manager


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    return Mock()


@pytest.fixture
def mock_rag_system():
    """Create a mock RAG system."""
    return Mock()


@pytest.fixture
def mock_phase_manager(temp_db):
    """Create a mock phase manager with a real workflow."""
    manager = Mock()

    # Create a real workflow in the database
    session = temp_db.get_session()
    try:
        workflow = Workflow(
            id="integration-test-workflow",
            name="Integration Test Workflow",
            phases_folder_path="/tmp/test",
            status="active",
        )
        session.add(workflow)

        # Create phases
        phase1 = Phase(
            id="phase-1",
            workflow_id="integration-test-workflow",
            order=1,
            name="Planning",
            description="Planning phase",
            done_definitions=["Create plan", "Review plan"],
        )
        phase2 = Phase(
            id="phase-2",
            workflow_id="integration-test-workflow",
            order=2,
            name="Implementation",
            description="Implementation phase",
            done_definitions=["Implement solution", "Test solution"],
        )
        session.add(phase1)
        session.add(phase2)
        session.commit()
    finally:
        session.close()

    manager.workflow_id = "integration-test-workflow"

    # Mock workflow config
    workflow_config = Mock()
    workflow_config.result_criteria = "Successfully solve the test problem and submit evidence"
    manager.get_workflow_config = Mock(return_value=workflow_config)

    return manager


@pytest.fixture
def monitoring_loop(temp_db, mock_agent_manager, mock_llm_provider, mock_rag_system, mock_phase_manager):
    """Create a monitoring loop for integration testing."""
    loop = MonitoringLoop(
        db_manager=temp_db,
        agent_manager=mock_agent_manager,
        llm_provider=mock_llm_provider,
        rag_system=mock_rag_system,
        phase_manager=mock_phase_manager,
    )
    return loop


class TestDiagnosticIntegration:
    """Integration tests for diagnostic agent system."""

    @pytest.mark.asyncio
    async def test_diagnostic_not_triggered_no_tasks(self, monitoring_loop, log_capture):
        """Test that diagnostic is not triggered when there are no tasks."""
        log_capture.clear()

        await monitoring_loop._check_workflow_stuck_state()

        # Check logs
        messages = log_capture.get_messages("[DIAGNOSTIC MONITOR]")

        # Should have status report
        assert any("DIAGNOSTIC STATUS REPORT" in m for m in messages)
        assert any("No tasks in workflow" in m for m in messages)
        assert any("NOT TRIGGERING" in m for m in messages)

        # Should show conditions
        assert any("Has Tasks:            ❌" in m for m in messages)

    @pytest.mark.asyncio
    async def test_diagnostic_not_triggered_active_tasks(self, monitoring_loop, temp_db, log_capture):
        """Test that diagnostic is not triggered when tasks are still active."""
        # Create an active task
        session = temp_db.get_session()
        try:
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="in_progress",  # Active
                workflow_id="integration-test-workflow",
                phase_id="phase-1",
            )
            session.add(task)
            session.commit()
        finally:
            session.close()

        log_capture.clear()
        await monitoring_loop._check_workflow_stuck_state()

        # Check logs
        messages = log_capture.get_messages("[DIAGNOSTIC MONITOR]")

        assert any("DIAGNOSTIC STATUS REPORT" in m for m in messages)
        assert any("Tasks still active" in m for m in messages)
        assert any("NOT TRIGGERING" in m for m in messages)

        # Should show active tasks condition failed
        assert any("All Tasks Finished:   ❌" in m for m in messages)

    @pytest.mark.asyncio
    async def test_diagnostic_not_triggered_too_recent(self, monitoring_loop, temp_db, log_capture):
        """Test that diagnostic is not triggered when task completed too recently."""
        # Create a recently completed task
        session = temp_db.get_session()
        try:
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="done",
                workflow_id="integration-test-workflow",
                phase_id="phase-1",
                completed_at=datetime.utcnow() - timedelta(seconds=30),  # 30s ago, less than 60s threshold
            )
            session.add(task)
            session.commit()
        finally:
            session.close()

        log_capture.clear()
        await monitoring_loop._check_workflow_stuck_state()

        # Check logs
        messages = log_capture.get_messages("[DIAGNOSTIC MONITOR]")

        assert any("DIAGNOSTIC STATUS REPORT" in m for m in messages)
        assert any("Not stuck long enough" in m for m in messages)
        assert any("NOT TRIGGERING" in m for m in messages)

        # Should show stuck time condition failed
        assert any("Stuck Long Enough:    ❌" in m for m in messages)

    @pytest.mark.asyncio
    async def test_diagnostic_triggered_workflow_stuck(self, monitoring_loop, temp_db, log_capture):
        """Test that diagnostic agent is triggered when workflow is stuck."""
        # Create a task that completed long ago
        session = temp_db.get_session()
        try:
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="done",
                workflow_id="integration-test-workflow",
                phase_id="phase-1",
                completed_at=datetime.utcnow() - timedelta(minutes=5),  # 5 min ago
            )
            session.add(task)
            session.commit()
        finally:
            session.close()

        log_capture.clear()
        await monitoring_loop._check_workflow_stuck_state()

        # Check logs
        messages = log_capture.get_messages("[DIAGNOSTIC MONITOR]")

        # Should have triggered
        assert any("WORKFLOW STUCK DETECTED" in m for m in messages)
        assert any("TRIGGERING DIAGNOSTIC AGENT" in m for m in messages)

        # All conditions should pass
        assert any("Enabled:              ✅" in m for m in messages)
        assert any("Workflow Exists:      ✅" in m for m in messages)
        assert any("Has Tasks:            ✅" in m for m in messages)
        assert any("All Tasks Finished:   ✅" in m for m in messages)
        assert any("No Validated Result:  ✅" in m for m in messages)
        assert any("Cooldown Passed:      ✅" in m for m in messages)
        assert any("Stuck Long Enough:    ✅" in m for m in messages)

        # Should have created diagnostic agent
        assert any("Creating diagnostic agent" in m for m in messages)
        assert any("Diagnostic agent created successfully" in m for m in messages)

        # Verify diagnostic run was created
        session = temp_db.get_session()
        try:
            diagnostic_runs = session.query(DiagnosticRun).all()
            assert len(diagnostic_runs) == 1

            run = diagnostic_runs[0]
            assert run.workflow_id == "integration-test-workflow"
            assert run.total_tasks_at_trigger == 1
            assert run.done_tasks_at_trigger == 1
            assert run.status in ['created', 'running']
        finally:
            session.close()

    @pytest.mark.asyncio
    async def test_diagnostic_respects_cooldown(self, monitoring_loop, temp_db, log_capture):
        """Test that diagnostic respects cooldown period."""
        # Create a completed task
        session = temp_db.get_session()
        try:
            task = Task(
                id="task-1",
                raw_description="Test task",
                enriched_description="Test task",
                done_definition="Complete test",
                status="done",
                workflow_id="integration-test-workflow",
                phase_id="phase-1",
                completed_at=datetime.utcnow() - timedelta(minutes=5),
            )
            session.add(task)

            # Create a recent diagnostic run
            diagnostic_run = DiagnosticRun(
                id="diag-1",
                workflow_id="integration-test-workflow",
                triggered_at=datetime.utcnow() - timedelta(seconds=30),  # 30s ago
                total_tasks_at_trigger=1,
                done_tasks_at_trigger=1,
                failed_tasks_at_trigger=0,
                time_since_last_task_seconds=300,
                workflow_goal="Test goal",
            )
            session.add(diagnostic_run)
            session.commit()
        finally:
            session.close()

        log_capture.clear()
        await monitoring_loop._check_workflow_stuck_state()

        # Check logs
        messages = log_capture.get_messages("[DIAGNOSTIC MONITOR]")

        assert any("DIAGNOSTIC STATUS REPORT" in m for m in messages)
        assert any("Cooldown active" in m for m in messages)
        assert any("NOT TRIGGERING" in m for m in messages)

        # Should show cooldown condition failed
        assert any("Cooldown Passed:      ❌" in m for m in messages)

    @pytest.mark.asyncio
    async def test_full_diagnostic_flow_with_logging(self, monitoring_loop, temp_db, log_capture):
        """Test the complete diagnostic flow and verify all logs."""
        # Setup: Create multiple completed tasks representing a stuck workflow
        session = temp_db.get_session()
        try:
            # Phase 1 tasks (completed)
            task1 = Task(
                id="task-1",
                raw_description="Planning task",
                enriched_description="Create project plan",
                done_definition="Plan documented",
                status="done",
                workflow_id="integration-test-workflow",
                phase_id="phase-1",
                completed_at=datetime.utcnow() - timedelta(minutes=10),
                completion_notes="Created plan.md with approach",
            )

            # Phase 2 tasks (completed)
            task2 = Task(
                id="task-2",
                raw_description="Implementation task",
                enriched_description="Implement solution",
                done_definition="Code written",
                status="done",
                workflow_id="integration-test-workflow",
                phase_id="phase-2",
                completed_at=datetime.utcnow() - timedelta(minutes=5),
                completion_notes="Implemented main.py",
            )

            # Create agents for these tasks
            agent1 = Agent(
                id="agent-1",
                system_prompt="Planning agent",
                status="terminated",
                cli_type="claude",
                current_task_id="task-1",
                agent_type="phase",
            )

            agent2 = Agent(
                id="agent-2",
                system_prompt="Implementation agent",
                status="terminated",
                cli_type="claude",
                current_task_id="task-2",
                agent_type="phase",
            )

            session.add(task1)
            session.add(task2)
            session.add(agent1)
            session.add(agent2)
            session.commit()
        finally:
            session.close()

        log_capture.clear()

        # Run diagnostic check
        await monitoring_loop._check_workflow_stuck_state()

        # Verify logs in detail
        messages = log_capture.get_messages("[DIAGNOSTIC MONITOR]")

        print("\n" + "="*80)
        print("CAPTURED DIAGNOSTIC MONITOR LOGS:")
        print("="*80)
        for msg in messages:
            print(msg)
        print("="*80 + "\n")

        # 1. Check initial detection
        assert any("Starting workflow stuck state check" in m for m in messages), \
            "Should log start of check"

        # 2. Check condition evaluations
        assert any("Workflow exists:" in m for m in messages), \
            "Should log workflow existence"
        assert any("Has tasks: 2 total" in m for m in messages), \
            "Should log task count"
        assert any("All tasks finished: 2 tasks" in m for m in messages), \
            "Should log all tasks finished"
        assert any("No validated result" in m for m in messages), \
            "Should log no validated result"
        assert any("Cooldown passed" in m for m in messages), \
            "Should log cooldown status"
        assert any("Stuck long enough" in m for m in messages), \
            "Should log stuck time"

        # 3. Check status report
        assert any("DIAGNOSTIC STATUS REPORT" in m for m in messages), \
            "Should have status report"
        assert any("Enabled:              ✅" in m for m in messages), \
            "Should show enabled"
        assert any("Workflow Exists:      ✅" in m for m in messages), \
            "Should show workflow exists"
        assert any("Has Tasks:            ✅" in m for m in messages), \
            "Should show has tasks"
        assert any("All Tasks Finished:   ✅" in m for m in messages), \
            "Should show all finished"
        assert any("No Validated Result:  ✅" in m for m in messages), \
            "Should show no result"
        assert any("Cooldown Passed:      ✅" in m for m in messages), \
            "Should show cooldown passed"
        assert any("Stuck Long Enough:    ✅" in m for m in messages), \
            "Should show stuck long enough"

        # 4. Check trigger decision
        assert any("TRIGGERING DIAGNOSTIC AGENT" in m for m in messages), \
            "Should show triggering decision"

        # 5. Check agent creation process
        assert any("Creating diagnostic agent" in m for m in messages), \
            "Should log agent creation start"
        assert any("Gathering diagnostic context" in m for m in messages), \
            "Should log context gathering"
        assert any("Context gathered: 2 phases" in m for m in messages), \
            "Should log context details"
        assert any("Created diagnostic task:" in m for m in messages), \
            "Should log task creation"
        assert any("Created diagnostic run:" in m for m in messages), \
            "Should log run creation"
        assert any("Generating diagnostic prompt" in m for m in messages), \
            "Should log prompt generation"
        assert any("Spawning diagnostic agent" in m for m in messages), \
            "Should log agent spawning"
        assert any("Diagnostic agent created successfully" in m for m in messages), \
            "Should log success"

        # 6. Verify database state
        session = temp_db.get_session()
        try:
            # Should have created diagnostic run
            diagnostic_runs = session.query(DiagnosticRun).all()
            assert len(diagnostic_runs) == 1, "Should create one diagnostic run"

            run = diagnostic_runs[0]
            assert run.workflow_id == "integration-test-workflow"
            assert run.total_tasks_at_trigger == 2
            assert run.done_tasks_at_trigger == 2
            assert run.failed_tasks_at_trigger == 0
            assert run.status in ['created', 'running']

            # Should have created diagnostic task
            diagnostic_tasks = session.query(Task).filter(
                Task.raw_description.like("DIAGNOSTIC%")
            ).all()
            assert len(diagnostic_tasks) == 1, "Should create one diagnostic task"

            diagnostic_task = diagnostic_tasks[0]
            assert diagnostic_task.workflow_id == "integration-test-workflow"
            assert diagnostic_task.priority == "high"
            assert diagnostic_task.phase_id is None  # Phase-agnostic

        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
