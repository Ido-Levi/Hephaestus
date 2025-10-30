"""Unit tests for validation prompt templates and their integration."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call, ANY
from datetime import datetime
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.monitoring.prompt_loader import PromptLoader
from src.core.database import Task


class TestPromptTemplateLoading:
    """Test that prompt templates load correctly."""

    def setup_method(self):
        """Set up test fixtures."""
        self.prompt_loader = PromptLoader()

    def test_result_validation_template_exists(self):
        """Test that result validation template file exists."""
        template_path = self.prompt_loader.prompts_dir / "result_validation_prompt.md"
        assert template_path.exists(), f"Result validation template not found at {template_path}"

    def test_task_validation_template_exists(self):
        """Test that task validation template file exists."""
        template_path = self.prompt_loader.prompts_dir / "task_validation_prompt.md"
        assert template_path.exists(), f"Task validation template not found at {template_path}"

    def test_load_result_validation_template(self):
        """Test loading result validation template."""
        template = self.prompt_loader.load_prompt("result_validation_prompt")
        assert template, "Result validation template is empty"
        assert "WORKFLOW RESULT VALIDATOR" in template, "Template missing expected header"
        assert "{validator_agent_id}" in template, "Template missing validator_agent_id placeholder"
        assert "{result_id}" in template, "Template missing result_id placeholder"
        assert "{result_file_path}" in template, "Template missing result_file_path placeholder"
        assert "submit_result_validation" in template, "Template missing submit_result_validation instruction"

    def test_load_task_validation_template(self):
        """Test loading task validation template."""
        template = self.prompt_loader.load_prompt("task_validation_prompt")
        assert template, "Task validation template is empty"
        assert "TASK COMPLETION VALIDATOR" in template, "Template missing expected header"
        assert "{validator_agent_id}" in template, "Template missing validator_agent_id placeholder"
        assert "{task_id}" in template, "Template missing task_id placeholder"
        assert "{done_definition}" in template, "Template missing done_definition placeholder"
        assert "give_validation_review" in template, "Template missing give_validation_review instruction"

    def test_format_result_validation_prompt(self):
        """Test formatting result validation prompt with values."""
        prompt = self.prompt_loader.format_result_validation_prompt(
            validator_agent_id="test-validator-123",
            result_id="result-456",
            result_file_path="/tmp/test_result.md",
            workflow_name="Test Workflow",
            workflow_id="workflow-789",
            validation_criteria="Must solve problem X correctly",
            submitted_by_agent="agent-abc",
            submitted_at="2024-01-01T12:00:00"
        )

        assert "test-validator-123" in prompt, "Validator agent ID not in formatted prompt"
        assert "result-456" in prompt, "Result ID not in formatted prompt"
        assert "/tmp/test_result.md" in prompt, "Result file path not in formatted prompt"
        assert "Test Workflow" in prompt, "Workflow name not in formatted prompt"
        assert "Must solve problem X correctly" in prompt, "Validation criteria not in formatted prompt"
        assert "submit_result_validation" in prompt, "MCP tool instruction not in formatted prompt"
        assert "{validator_agent_id}" not in prompt, "Unformatted placeholder remains"

    def test_format_task_validation_prompt(self):
        """Test formatting task validation prompt with values."""
        prompt = self.prompt_loader.format_task_validation_prompt(
            validator_agent_id="validator-xyz",
            task_id="task-123",
            task_description="Implement feature Y",
            done_definition="Feature Y must work with tests",
            enriched_description="Implement feature Y with unit tests and documentation",
            original_agent_id="agent-original",
            iteration=1,
            working_directory="/tmp/worktree",
            commit_sha="abc123def",
            previous_feedback=None
        )

        assert "validator-xyz" in prompt, "Validator agent ID not in formatted prompt"
        assert "task-123" in prompt, "Task ID not in formatted prompt"
        assert "Implement feature Y" in prompt, "Task description not in formatted prompt"
        assert "Feature Y must work with tests" in prompt, "Done definition not in formatted prompt"
        assert "give_validation_review" in prompt, "MCP tool instruction not in formatted prompt"
        assert "{task_id}" not in prompt, "Unformatted placeholder remains"

    def test_format_task_validation_prompt_with_previous_feedback(self):
        """Test task validation prompt with previous feedback."""
        prompt = self.prompt_loader.format_task_validation_prompt(
            validator_agent_id="validator-xyz",
            task_id="task-123",
            task_description="Fix bug",
            done_definition="Bug must be fixed",
            enriched_description="Fix critical bug in authentication",
            original_agent_id="agent-original",
            iteration=2,
            working_directory="/tmp/worktree",
            commit_sha="abc123def",
            previous_feedback="Missing error handling for edge case"
        )

        assert "Previous Validation Feedback" in prompt, "Previous feedback section missing"
        assert "Missing error handling for edge case" in prompt, "Previous feedback content missing"
        assert "Iteration 1" in prompt or "previous" in prompt.lower(), "Iteration context missing"


class TestAgentManagerValidatorPrompts:
    """Test that AgentManager correctly uses validation prompts."""

    def test_format_initial_message_for_result_validator(self):
        """Test that result validators get the correct prompt from enriched_data."""
        # Import and mock dependencies
        with patch('src.agents.manager.libtmux'), \
             patch('src.agents.manager.WorktreeManager'):
            from src.agents.manager import AgentManager

            # Create minimal mocks
            mock_db_manager = Mock()
            mock_llm_provider = AsyncMock()
            mock_phase_manager = Mock()

            # Create manager
            manager = AgentManager(
                db_manager=mock_db_manager,
                llm_provider=mock_llm_provider,
                phase_manager=mock_phase_manager
            )

            # Set config manually
            manager.config = Mock()
            manager.config.tmux_session_prefix = "test"

            # Create test task
            mock_task = Mock(spec=Task)
            mock_task.id = "task-123"

            enriched_data = {
                "type": "result_validation",
                "validation_prompt": "FORMATTED RESULT VALIDATION PROMPT"
            }

            # Test the format_initial_message method
            message = manager._format_initial_message(
                task=mock_task,
                agent_id="validator-123",
                worktree_path="/tmp/worktree",
                agent_type="result_validator",
                enriched_data=enriched_data
            )

            assert message == "FORMATTED RESULT VALIDATION PROMPT", "Result validator didn't get validation prompt from enriched_data"

    def test_format_initial_message_for_task_validator(self):
        """Test that task validators get the correct prompt from enriched_data."""
        with patch('src.agents.manager.libtmux'), \
             patch('src.agents.manager.WorktreeManager'):
            from src.agents.manager import AgentManager

            # Create minimal mocks
            mock_db_manager = Mock()
            mock_llm_provider = AsyncMock()
            mock_phase_manager = Mock()

            # Create manager
            manager = AgentManager(
                db_manager=mock_db_manager,
                llm_provider=mock_llm_provider,
                phase_manager=mock_phase_manager
            )

            # Set config manually
            manager.config = Mock()

            # Create test task
            mock_task = Mock(spec=Task)
            mock_task.id = "task-456"

            enriched_data = {
                "type": "task_validation",
                "validation_prompt": "FORMATTED TASK VALIDATION PROMPT"
            }

            # Test the format_initial_message method
            message = manager._format_initial_message(
                task=mock_task,
                agent_id="validator-456",
                worktree_path="/tmp/worktree",
                agent_type="validator",
                enriched_data=enriched_data
            )

            assert message == "FORMATTED TASK VALIDATION PROMPT", "Task validator didn't get validation prompt from enriched_data"

    def test_format_initial_message_for_regular_agent(self):
        """Test that regular agents get the standard task prompt."""
        with patch('src.agents.manager.libtmux'), \
             patch('src.agents.manager.WorktreeManager'):
            from src.agents.manager import AgentManager

            # Create minimal mocks
            mock_db_manager = Mock()
            mock_llm_provider = AsyncMock()
            mock_phase_manager = Mock()

            # Create manager
            manager = AgentManager(
                db_manager=mock_db_manager,
                llm_provider=mock_llm_provider,
                phase_manager=mock_phase_manager
            )

            # Set config manually
            manager.config = Mock()
            manager.phase_manager = None  # No phase manager for this test

            # Create test task with necessary attributes
            mock_task = Mock(spec=Task)
            mock_task.id = "task-789"
            mock_task.raw_description = "Implement feature"
            mock_task.enriched_description = "Implement feature with tests"
            mock_task.done_definition = "Feature works correctly"
            mock_task.phase_id = None
            mock_task.workflow_id = None

            enriched_data = {"type": "normal_task"}

            # Test the format_initial_message method
            message = manager._format_initial_message(
                task=mock_task,
                agent_id="agent-789",
                worktree_path="/tmp/worktree",
                agent_type="phase",
                enriched_data=enriched_data
            )

            assert "=== TASK ASSIGNMENT ===" in message, "Regular agent didn't get standard task prompt"
            assert "Your Agent ID: agent-789" in message, "Agent ID missing from standard prompt"
            assert "Task ID: task-789" in message, "Task ID missing from standard prompt"
            assert "FORMATTED TASK VALIDATION PROMPT" not in message, "Regular agent shouldn't get validation prompt"

    def test_validator_without_prompt_gets_fallback(self):
        """Test that validators without prompt in enriched_data get fallback message."""
        with patch('src.agents.manager.libtmux'), \
             patch('src.agents.manager.WorktreeManager'):
            from src.agents.manager import AgentManager

            # Create minimal mocks
            mock_db_manager = Mock()
            mock_llm_provider = AsyncMock()

            # Create manager
            manager = AgentManager(
                db_manager=mock_db_manager,
                llm_provider=mock_llm_provider
            )

            # Set config manually
            manager.config = Mock()

            mock_task = Mock(spec=Task)
            mock_task.id = "task-999"

            # No validation_prompt in enriched_data
            enriched_data = {"type": "result_validation"}

            message = manager._format_initial_message(
                task=mock_task,
                agent_id="validator-999",
                worktree_path="/tmp/worktree",
                agent_type="result_validator",
                enriched_data=enriched_data
            )

            assert "You are a result validator agent" in message, "Fallback message not provided"


class TestValidatorPromptIntegration:
    """Test that validator agent creation properly formats and passes prompts."""

    @pytest.mark.asyncio
    async def test_validator_agent_formats_result_prompt(self):
        """Test that result validation prompts are properly formatted."""
        from src.monitoring.prompt_loader import prompt_loader

        # Create mock objects that match what validator_agent expects
        mock_result = Mock()
        mock_result.id = "result-123"
        mock_result.result_file_path = "/tmp/result.md"
        mock_result.created_at = datetime.now()

        # Test the actual prompt formatting
        prompt = prompt_loader.format_result_validation_prompt(
            validator_agent_id="validator-test",
            result_id=mock_result.id,
            result_file_path=mock_result.result_file_path,
            workflow_name="Test Workflow",
            workflow_id="workflow-123",
            validation_criteria="Must solve the problem",
            submitted_by_agent="agent-original",
            submitted_at=mock_result.created_at.isoformat()
        )

        # Verify the prompt is properly formatted
        assert "validator-test" in prompt
        assert "result-123" in prompt
        assert "/tmp/result.md" in prompt
        assert "Test Workflow" in prompt
        assert "Must solve the problem" in prompt
        assert "submit_result_validation" in prompt

    @pytest.mark.asyncio
    async def test_validator_agent_formats_task_prompt(self):
        """Test that task validation prompts are properly formatted."""
        from src.monitoring.prompt_loader import prompt_loader

        # Test the actual prompt formatting
        prompt = prompt_loader.format_task_validation_prompt(
            validator_agent_id="validator-task",
            task_id="task-123",
            task_description="Implement feature",
            done_definition="Feature must work",
            enriched_description="Implement with tests",
            original_agent_id="agent-original",
            iteration=1,
            working_directory="/tmp/worktree",
            commit_sha="abc123",
            previous_feedback=None
        )

        # Verify the prompt is properly formatted
        assert "validator-task" in prompt
        assert "task-123" in prompt
        assert "Implement feature" in prompt
        assert "Feature must work" in prompt
        assert "give_validation_review" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])