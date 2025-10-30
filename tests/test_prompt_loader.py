"""Unit tests for the PromptLoader system."""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json
from datetime import datetime, timedelta

from src.monitoring.prompt_loader import PromptLoader


@pytest.fixture
def prompt_loader():
    """Create PromptLoader instance."""
    with patch('src.monitoring.prompt_loader.Path.exists', return_value=True):
        return PromptLoader()


@pytest.fixture
def sample_accumulated_context():
    """Create sample accumulated context for testing."""
    return {
        "overall_goal": "Build a REST API with authentication",
        "session_duration": "2:30:00",
        "current_focus": "implementing JWT validation",
        "conversation_length": 42,
        "constraints": ["no external databases", "must use TypeScript"],
        "lifted_constraints": ["can now use MongoDB"],
        "standing_instructions": ["add comprehensive tests", "document all endpoints"],
        "discovered_blockers": ["CORS configuration issue", "Rate limiting not working"],
        "session_start": datetime.utcnow() - timedelta(hours=2, minutes=30)
    }


@pytest.fixture
def sample_task_info():
    """Create sample task info for testing."""
    return {
        "description": "Implement user authentication endpoints",
        "done_definition": "All auth endpoints working with tests passing",
        "task_id": "task-123",
        "agent_id": "agent-456"
    }


@pytest.fixture
def sample_guardian_summaries():
    """Create sample Guardian summaries for Conductor testing."""
    return [
        {
            "agent_id": "agent-1",
            "trajectory_summary": "Building authentication module with JWT",
            "current_phase": "implementation",
            "trajectory_aligned": True,
            "needs_steering": False,
            "accumulated_goal": "Implement complete authentication system with JWT tokens and refresh logic"
        },
        {
            "agent_id": "agent-2",
            "trajectory_summary": "Creating user management endpoints",
            "current_phase": "testing",
            "trajectory_aligned": True,
            "needs_steering": False,
            "accumulated_goal": "Build CRUD operations for user management with proper validation"
        },
        {
            "agent_id": "agent-3",
            "trajectory_summary": "Implementing authentication logic",
            "current_phase": "implementation",
            "trajectory_aligned": False,
            "needs_steering": True,
            "accumulated_goal": "Create auth system with JWT"
        }
    ]


class TestPromptLoader:
    """Test the PromptLoader system."""

    def test_init_with_missing_directory(self):
        """Test initialization fails when prompts directory doesn't exist."""
        with patch('src.monitoring.prompt_loader.Path.exists', return_value=False):
            with pytest.raises(ValueError, match="Prompts directory not found"):
                PromptLoader()

    def test_load_prompt_success(self, prompt_loader):
        """Test successful prompt loading."""
        mock_content = "# Test Prompt\n\nThis is a {test} prompt with {variables}."

        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('src.monitoring.prompt_loader.Path.exists', return_value=True):
                content = prompt_loader.load_prompt("test_prompt")

        assert content == mock_content
        assert "{test}" in content
        assert "{variables}" in content

    def test_load_prompt_file_not_found(self, prompt_loader):
        """Test loading non-existent prompt file."""
        with patch('src.monitoring.prompt_loader.Path.exists', return_value=False):
            with pytest.raises(ValueError, match="Prompt file not found"):
                prompt_loader.load_prompt("nonexistent_prompt")

    def test_format_guardian_prompt(
        self,
        prompt_loader,
        sample_accumulated_context,
        sample_task_info
    ):
        """Test formatting Guardian prompt with all parameters."""
        template = """
        # Guardian Analysis
        Goal: {overall_goal}
        Duration: {session_duration}
        Focus: {current_focus}
        Length: {conversation_length}
        Constraints: {constraints}
        Lifted: {lifted_constraints}
        Instructions: {standing_instructions}
        Blockers: {discovered_blockers}
        Past: {past_summaries}
        Task: {task_description}
        Done: {done_definition}
        Task ID: {task_id}
        Agent ID: {agent_id}
        Output: {agent_output}
        """

        with patch.object(prompt_loader, 'load_prompt', return_value=template):
            formatted = prompt_loader.format_guardian_prompt(
                accumulated_context=sample_accumulated_context,
                past_summaries=[{"summary": "Previous analysis"}],
                task_info=sample_task_info,
                agent_output="Recent agent output here"
            )

        # Verify all fields are populated
        assert "Build a REST API with authentication" in formatted
        assert "2:30:00" in formatted
        assert "implementing JWT validation" in formatted
        assert "42" in formatted
        assert "no external databases" in formatted
        assert "must use TypeScript" in formatted
        assert "can now use MongoDB" in formatted
        assert "add comprehensive tests" in formatted
        assert "document all endpoints" in formatted
        assert "CORS configuration issue" in formatted
        assert "Previous analysis" in formatted
        assert "Implement user authentication endpoints" in formatted
        assert "task-123" in formatted
        assert "agent-456" in formatted
        assert "Recent agent output" in formatted

    def test_format_guardian_prompt_empty_lists(
        self,
        prompt_loader,
        sample_task_info
    ):
        """Test Guardian prompt formatting with empty lists."""
        minimal_context = {
            "overall_goal": "Test goal",
            "session_duration": "0:05:00",
            "current_focus": "starting",
            "conversation_length": 1,
            "constraints": [],
            "lifted_constraints": [],
            "standing_instructions": [],
            "discovered_blockers": []
        }

        template = """
        Constraints: {constraints}
        Lifted: {lifted_constraints}
        Instructions: {standing_instructions}
        Blockers: {discovered_blockers}
        Past: {past_summaries}
        """

        with patch.object(prompt_loader, 'load_prompt', return_value=template):
            formatted = prompt_loader.format_guardian_prompt(
                accumulated_context=minimal_context,
                past_summaries=[],
                task_info=sample_task_info,
                agent_output="test"
            )

        assert "No active constraints" in formatted
        assert "No lifted constraints" in formatted
        assert "No standing instructions" in formatted
        assert "No blockers discovered" in formatted
        assert "No previous Guardian summaries" in formatted

    def test_format_guardian_prompt_long_output_truncation(
        self,
        prompt_loader,
        sample_accumulated_context,
        sample_task_info
    ):
        """Test that long agent output is truncated."""
        template = "Output: {agent_output}"
        long_output = "x" * 5000  # Very long output

        with patch.object(prompt_loader, 'load_prompt', return_value=template):
            formatted = prompt_loader.format_guardian_prompt(
                accumulated_context=sample_accumulated_context,
                past_summaries=[],
                task_info=sample_task_info,
                agent_output=long_output
            )

        # Should be truncated to last 3000 characters
        assert len(formatted) < 3100  # Account for "Output: " prefix
        assert "x" * 2999 in formatted  # Most of the x's should be there

    def test_format_conductor_prompt(
        self,
        prompt_loader,
        sample_guardian_summaries
    ):
        """Test formatting Conductor prompt."""
        template = """
        # Conductor Analysis
        Primary Goal: {primary_goal}
        Constraints: {system_constraints}
        Coordination: {coordination_requirement}
        Summaries: {guardian_summaries_json}
        """

        system_goals = {
            "primary": "Complete authentication system",
            "constraints": "No duplicate work, efficient resource usage",
            "coordination": "All agents working together"
        }

        with patch.object(prompt_loader, 'load_prompt', return_value=template):
            formatted = prompt_loader.format_conductor_prompt(
                guardian_summaries=sample_guardian_summaries,
                system_goals=system_goals
            )

        assert "Complete authentication system" in formatted
        assert "No duplicate work" in formatted
        assert "All agents working together" in formatted

        # Check that summaries are properly formatted
        assert "agent-1" in formatted
        assert "agent-2" in formatted
        assert "agent-3" in formatted
        assert "Building authentication module" in formatted
        assert "Creating user management" in formatted

    def test_format_conductor_prompt_truncates_long_goals(
        self,
        prompt_loader
    ):
        """Test that long accumulated goals are truncated in Conductor prompt."""
        long_goal = "x" * 200
        summaries = [
            {
                "agent_id": "agent-1",
                "trajectory_summary": "Working",
                "current_phase": "implementation",
                "trajectory_aligned": True,
                "needs_steering": False,
                "accumulated_goal": long_goal
            }
        ]

        template = "Summaries: {guardian_summaries_json}"
        system_goals = {"primary": "Test", "constraints": "", "coordination": ""}

        with patch.object(prompt_loader, 'load_prompt', return_value=template):
            formatted = prompt_loader.format_conductor_prompt(
                guardian_summaries=summaries,
                system_goals=system_goals
            )

        # Goal should be truncated to 100 chars
        parsed = json.loads(formatted.split("Summaries: ")[1])
        assert len(parsed[0]["accumulated_goal"]) == 100

    def test_format_conductor_prompt_with_defaults(
        self,
        prompt_loader
    ):
        """Test Conductor prompt with default system goals."""
        template = """
        Primary: {primary_goal}
        Constraints: {system_constraints}
        Coordination: {coordination_requirement}
        """

        with patch.object(prompt_loader, 'load_prompt', return_value=template):
            formatted = prompt_loader.format_conductor_prompt(
                guardian_summaries=[],
                system_goals={}  # Empty goals should use defaults
            )

        assert "Complete all assigned tasks efficiently" in formatted
        assert "No duplicate work, efficient resource usage" in formatted
        assert "All agents working toward collective objectives" in formatted

    def test_format_list_helper(self, prompt_loader):
        """Test the _format_list helper method."""
        # Empty list
        result = prompt_loader._format_list([], "Empty message")
        assert result == "Empty message"

        # Single item
        result = prompt_loader._format_list(["single item"], "Empty")
        assert result == "- single item"

        # Multiple items
        result = prompt_loader._format_list(["first", "second", "third"], "Empty")
        assert result == "- first\n- second\n- third"

    def test_format_guardian_prompt_with_many_past_summaries(
        self,
        prompt_loader,
        sample_accumulated_context,
        sample_task_info
    ):
        """Test that only last 5 summaries are included."""
        template = "Past: {past_summaries}"

        # Create 10 past summaries
        many_summaries = [{"id": i, "summary": f"Summary {i}"} for i in range(10)]

        with patch.object(prompt_loader, 'load_prompt', return_value=template):
            formatted = prompt_loader.format_guardian_prompt(
                accumulated_context=sample_accumulated_context,
                past_summaries=many_summaries,
                task_info=sample_task_info,
                agent_output="test"
            )

        # Should only include summaries 5-9 (last 5)
        assert "Summary 5" in formatted
        assert "Summary 9" in formatted
        assert "Summary 0" not in formatted
        assert "Summary 4" not in formatted

    def test_format_guardian_prompt_missing_fields(
        self,
        prompt_loader
    ):
        """Test Guardian prompt with missing fields uses defaults."""
        template = """
        Goal: {overall_goal}
        Focus: {current_focus}
        Length: {conversation_length}
        """

        incomplete_context = {"conversation_length": 5}
        incomplete_task = {}

        with patch.object(prompt_loader, 'load_prompt', return_value=template):
            formatted = prompt_loader.format_guardian_prompt(
                accumulated_context=incomplete_context,
                past_summaries=[],
                task_info=incomplete_task,
                agent_output="test"
            )

        assert "Unknown" in formatted  # Default values should be used

    def test_singleton_instance(self):
        """Test that prompt_loader is available as singleton."""
        from src.monitoring.prompt_loader import prompt_loader

        with patch('src.monitoring.prompt_loader.Path.exists', return_value=True):
            assert isinstance(prompt_loader, PromptLoader)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])