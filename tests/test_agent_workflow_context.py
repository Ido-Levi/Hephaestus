"""Tests for agent workflow context in prompts.

This module tests that agents receive proper workflow context in their initial prompts:
1. Initial message includes workflow_id
2. Initial message instructs agents to use workflow_id
3. Workflow context is properly formatted
4. Different agent types receive appropriate prompts
"""

import pytest
import os
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

# Set test environment before imports
os.environ["HEPHAESTUS_TEST_DB"] = ":memory:"

from src.core.database import DatabaseManager, Task, Workflow, Phase
from src.agents.manager import AgentManager
from src.phases.phase_manager import PhaseManager


class MockTask:
    """Mock task for testing."""

    def __init__(self, task_id=None, workflow_id=None, description="Test task",
                 enriched_description=None, done_definition="Task is done", phase_id=None):
        self.id = task_id or str(uuid.uuid4())
        self.workflow_id = workflow_id
        self.raw_description = description
        self.enriched_description = enriched_description or description
        self.done_definition = done_definition
        self.phase_id = phase_id
        self.created_by_agent_id = "test-agent"


class TestAgentWorkflowContext:
    """Test that agents receive proper workflow context in prompts."""

    @pytest.fixture
    def agent_manager(self, db_manager, mock_llm_provider):
        """Create an agent manager with mocked dependencies."""
        with patch('src.agents.manager.WorktreeManager') as mock_worktree:
            mock_worktree.return_value = MagicMock()
            manager = AgentManager(
                db_manager=db_manager,
                llm_provider=mock_llm_provider,
                phase_manager=None
            )
            return manager

    @pytest.fixture
    def agent_manager_with_phases(self, db_manager, mock_llm_provider, initialized_phase_manager):
        """Create an agent manager with phase manager."""
        with patch('src.agents.manager.WorktreeManager') as mock_worktree:
            mock_worktree.return_value = MagicMock()
            manager = AgentManager(
                db_manager=db_manager,
                llm_provider=mock_llm_provider,
                phase_manager=initialized_phase_manager
            )
            return manager

    def test_initial_message_includes_workflow_id(self, agent_manager):
        """Test that initial message includes workflow_id."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(
            workflow_id=workflow_id,
            description="Test task description"
        )

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project"
        )

        # Verify workflow_id is in the message
        assert workflow_id in message
        assert "Workflow ID:" in message or "workflow_id:" in message.lower()

    def test_initial_message_includes_agent_id(self, agent_manager):
        """Test that initial message includes agent_id."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(workflow_id=workflow_id)

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project"
        )

        # Verify agent_id is in the message
        assert agent_id in message
        assert "Agent ID:" in message or "agent_id:" in message.lower()

    def test_initial_message_instructs_workflow_usage(self, agent_manager):
        """Test that initial message tells agent to use workflow_id in MCP calls."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(workflow_id=workflow_id)

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project"
        )

        # Should instruct agent about workflow_id usage
        assert "workflow_id" in message.lower()
        # Should mention critical workflow information
        assert "CRITICAL" in message.upper() or "IMPORTANT" in message.upper()

    def test_initial_message_includes_task_description(self, agent_manager):
        """Test that initial message includes task description."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())
        task_description = "Write comprehensive unit tests for auth module"

        task = MockTask(
            workflow_id=workflow_id,
            description=task_description
        )

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project"
        )

        # Verify task description is included
        assert task_description in message

    def test_initial_message_includes_working_directory(self, agent_manager):
        """Test that initial message includes working directory path."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())
        worktree_path = "/home/test/project/worktree"

        task = MockTask(workflow_id=workflow_id)

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path=worktree_path
        )

        # Verify working directory is included
        assert worktree_path in message
        assert "Working Directory" in message or "directory" in message.lower()

    def test_initial_message_without_workflow_id(self, agent_manager):
        """Test initial message when workflow_id is None (standalone task)."""
        agent_id = str(uuid.uuid4())

        task = MockTask(
            workflow_id=None,
            description="Standalone task"
        )

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project"
        )

        # Should still have agent_id
        assert agent_id in message
        # Should handle missing workflow_id gracefully
        assert "N/A" in message or "standalone" in message.lower() or "none" in message.lower()

    def test_validator_agent_uses_specialized_prompt(self, agent_manager):
        """Test that validator agents use specialized prompts."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(workflow_id=workflow_id)

        # Test with validation_prompt in enriched_data
        validation_prompt = "You are validating task X. Check these criteria..."
        enriched_data = {"validation_prompt": validation_prompt}

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project",
            agent_type="validator",
            enriched_data=enriched_data
        )

        # Should use the validation prompt
        assert message == validation_prompt

    def test_result_validator_agent_uses_specialized_prompt(self, agent_manager):
        """Test that result validator agents use specialized prompts."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(workflow_id=workflow_id)

        # Test with validation_prompt in enriched_data
        validation_prompt = "You are validating the workflow result. Verify..."
        enriched_data = {"validation_prompt": validation_prompt}

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project",
            agent_type="result_validator",
            enriched_data=enriched_data
        )

        # Should use the validation prompt
        assert message == validation_prompt

    def test_diagnostic_agent_uses_specialized_prompt(self, agent_manager):
        """Test that diagnostic agents use specialized prompts."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(workflow_id=workflow_id)

        # Test with validation_prompt in enriched_data
        diagnostic_prompt = "Analyze the workflow state and create tasks..."
        enriched_data = {"validation_prompt": diagnostic_prompt}

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project",
            agent_type="diagnostic",
            enriched_data=enriched_data
        )

        # Should use the diagnostic prompt
        assert message == diagnostic_prompt

    def test_validator_fallback_message(self, agent_manager):
        """Test that validators get fallback message when no prompt provided."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(workflow_id=workflow_id)

        # No enriched_data provided
        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project",
            agent_type="validator",
            enriched_data=None
        )

        # Should get a fallback validator message
        assert "validator" in message.lower()

    def test_phase_agent_message_format(self, agent_manager):
        """Test that phase agents get full formatted message."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(
            workflow_id=workflow_id,
            description="Implement user authentication"
        )

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project",
            agent_type="phase"
        )

        # Should have full task assignment format
        assert "TASK ASSIGNMENT" in message
        assert agent_id in message
        assert workflow_id in message
        assert "Implement user authentication" in message

    def test_message_includes_mcp_tool_instructions(self, agent_manager):
        """Test that message includes instructions for MCP tool usage."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())

        task = MockTask(workflow_id=workflow_id)

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project"
        )

        # Should mention MCP tools
        assert "MCP" in message or "tool" in message.lower()
        # Should mention not using placeholders
        assert "agent-mcp" in message.lower() or "placeholder" in message.lower()


class TestAgentManagerWithPhaseContext:
    """Test agent manager with phase context integration."""

    @pytest.fixture
    def agent_manager_with_workflow(self, db_manager, mock_llm_provider, workflow_with_execution):
        """Create agent manager with an active workflow execution."""
        phase_manager, workflow_id = workflow_with_execution

        with patch('src.agents.manager.WorktreeManager') as mock_worktree:
            mock_worktree.return_value = MagicMock()
            manager = AgentManager(
                db_manager=db_manager,
                llm_provider=mock_llm_provider,
                phase_manager=phase_manager
            )
            return manager, workflow_id, phase_manager

    def test_message_with_phase_context(self, agent_manager_with_workflow):
        """Test that message includes phase context when available."""
        agent_manager, workflow_id, phase_manager = agent_manager_with_workflow
        agent_id = str(uuid.uuid4())

        # Get a phase from the workflow
        phases = phase_manager.get_phases_for_workflow(workflow_id)
        if phases:
            phase_id = phases[0].id

            task = MockTask(
                workflow_id=workflow_id,
                phase_id=phase_id,
                description="Task with phase context"
            )

            message = agent_manager._format_initial_message(
                task=task,
                agent_id=agent_id,
                worktree_path="/test/project"
            )

            # Should include workflow context section
            assert workflow_id in message

    def test_workflow_description_in_context(self, db_manager, mock_llm_provider, initialized_phase_manager):
        """Test that workflow description is included in context."""
        # Start a workflow with description
        workflow_id = initialized_phase_manager.start_execution(
            definition_id="test-workflow",
            description="Build a URL shortener with analytics",
            working_directory="/project"
        )

        with patch('src.agents.manager.WorktreeManager') as mock_worktree:
            mock_worktree.return_value = MagicMock()
            agent_manager = AgentManager(
                db_manager=db_manager,
                llm_provider=mock_llm_provider,
                phase_manager=initialized_phase_manager
            )

            agent_id = str(uuid.uuid4())
            task = MockTask(
                workflow_id=workflow_id,
                description="Implement redirect endpoint"
            )

            message = agent_manager._format_initial_message(
                task=task,
                agent_id=agent_id,
                worktree_path="/test/project"
            )

            # Should include workflow_id at minimum
            assert workflow_id in message


class TestWorkflowContextFormats:
    """Test different workflow context format scenarios."""

    @pytest.fixture
    def agent_manager(self, db_manager, mock_llm_provider):
        """Create basic agent manager."""
        with patch('src.agents.manager.WorktreeManager') as mock_worktree:
            mock_worktree.return_value = MagicMock()
            return AgentManager(
                db_manager=db_manager,
                llm_provider=mock_llm_provider,
                phase_manager=None
            )

    def test_message_format_with_all_fields(self, agent_manager):
        """Test message format when all fields are provided."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        task = MockTask(
            task_id=task_id,
            workflow_id=workflow_id,
            description="Complete feature implementation",
            enriched_description="Implement user registration with email verification",
            done_definition="Users can register and verify email"
        )

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/project/worktree"
        )

        # Verify all key elements are present
        assert task_id in message
        assert workflow_id in message
        assert agent_id in message
        assert "/project/worktree" in message
        # Should use enriched description if available
        assert "email verification" in message.lower()

    def test_task_id_in_message(self, agent_manager):
        """Test that task ID is included in message."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())
        task_id = f"task-{uuid.uuid4()}"

        task = MockTask(
            task_id=task_id,
            workflow_id=workflow_id
        )

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project"
        )

        # Task ID should be in message
        assert task_id in message
        assert "Task ID" in message

    def test_priority_and_phase_handling(self, agent_manager):
        """Test handling of phase_id in message."""
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        agent_id = str(uuid.uuid4())
        phase_id = str(uuid.uuid4())

        task = MockTask(
            workflow_id=workflow_id,
            phase_id=phase_id
        )

        message = agent_manager._format_initial_message(
            task=task,
            agent_id=agent_id,
            worktree_path="/test/project"
        )

        # Phase ID should be in message
        assert phase_id in message
        assert "Phase" in message


class TestAgentCreationContext:
    """Test workflow context during agent creation process."""

    @pytest.fixture
    def mock_task_db_object(self, db_manager):
        """Create a real task object in the database."""
        session = db_manager.get_session()
        workflow_id = str(uuid.uuid4())

        # Create workflow first
        workflow = Workflow(
            id=workflow_id,
            name="Test Workflow",
            description="Test workflow for agent creation",
            phases_folder_path="/tmp/test",
            status="active",
        )
        session.add(workflow)

        # Create task
        task = Task(
            id=str(uuid.uuid4()),
            raw_description="Test task for agent creation",
            enriched_description="Enriched test task description",
            done_definition="Task is complete",
            created_by_agent_id="test-agent",
            workflow_id=workflow_id,
            status="pending",
            priority="medium",
        )
        session.add(task)
        session.commit()

        task_id = task.id
        session.close()

        return task_id, workflow_id

    def test_task_has_workflow_id(self, db_manager, mock_task_db_object):
        """Test that task has workflow_id attribute set."""
        task_id, expected_workflow_id = mock_task_db_object

        session = db_manager.get_session()
        task = session.query(Task).filter_by(id=task_id).first()

        assert task is not None
        assert task.workflow_id == expected_workflow_id

        session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
