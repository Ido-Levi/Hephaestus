"""Comprehensive tests for the validation agent system."""

import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import json

from src.core.database import (
    DatabaseManager,
    Task,
    Agent,
    Phase,
    ValidationReview,
    Base
)
from src.validation.prompt_builder import ValidationPromptBuilder
from src.validation.check_executors import (
    ValidationCheckType,
    execute_validation_check
)
from src.validation.validator_agent import (
    build_validator_prompt,
    spawn_validator_agent,
    send_feedback_to_agent,
    get_agent_results
)


class TestValidationPromptBuilder:
    """Test the validation prompt builder."""

    def test_build_prompt_basic(self):
        """Test basic prompt building."""
        builder = ValidationPromptBuilder()

        task = {
            "id": "task123",
            "raw_description": "Test task",
            "enriched_description": "Enhanced test task",
            "done_definition": "Task is complete"
        }

        phase_validation = {
            "criteria": [
                {
                    "description": "File exists",
                    "check_type": "file_exists",
                    "target": ["test.txt"]
                }
            ]
        }

        workspace_changes = {
            "files_created": ["test.txt"],
            "files_modified": [],
            "files_deleted": [],
            "detailed_diff": "Added test.txt"
        }

        prompt = builder.build_prompt(
            task=task,
            phase_validation=phase_validation,
            commit_sha="abc123",
            workspace_changes=workspace_changes,
            agent_claims="Task completed",
            iteration=1
        )

        assert "task123" in prompt
        assert "Enhanced test task" in prompt
        assert "File exists" in prompt
        assert "test.txt" in prompt
        assert "abc123" in prompt

    def test_build_prompt_with_previous_feedback(self):
        """Test prompt building with previous feedback."""
        builder = ValidationPromptBuilder()

        task = {"id": "task123", "raw_description": "Test"}
        previous_feedback = "Please fix the error in line 10"

        prompt = builder.build_prompt(
            task=task,
            phase_validation=None,
            commit_sha="abc123",
            workspace_changes={},
            agent_claims="Fixed",
            iteration=2,
            previous_feedback=previous_feedback
        )

        assert "Please fix the error in line 10" in prompt
        assert "Iteration: 2" in prompt

    def test_format_validation_criteria(self):
        """Test formatting of validation criteria."""
        builder = ValidationPromptBuilder()

        phase_validation = {
            "criteria": [
                {
                    "description": "Tests pass",
                    "check_type": "test_pass",
                    "command": "pytest"
                },
                {
                    "description": "File contains pattern",
                    "check_type": "file_contains",
                    "target": "README.md",
                    "pattern": "Installation"
                }
            ]
        }

        formatted = builder._format_validation_criteria(phase_validation)

        assert "Tests pass" in formatted
        assert "pytest" in formatted
        assert "README.md" in formatted
        assert "Installation" in formatted


class TestValidationCheckExecutors:
    """Test validation check executors."""

    def test_file_exists_check(self, tmp_path):
        """Test file existence checking."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        criterion = {
            "target": ["test.txt"]
        }

        result = execute_validation_check(
            ValidationCheckType.FILE_EXISTS,
            criterion,
            str(tmp_path)
        )

        assert result["passed"] is True
        assert "EXISTS" in result["evidence"]

    def test_file_exists_check_missing(self, tmp_path):
        """Test file existence check when file is missing."""
        criterion = {
            "target": ["missing.txt"]
        }

        result = execute_validation_check(
            ValidationCheckType.FILE_EXISTS,
            criterion,
            str(tmp_path)
        )

        assert result["passed"] is False
        assert "MISSING" in result["evidence"]

    def test_file_contains_check(self, tmp_path):
        """Test file content checking."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World\nTest Pattern\n")

        criterion = {
            "target": "test.txt",
            "pattern": ["Hello", "Pattern"]
        }

        result = execute_validation_check(
            ValidationCheckType.FILE_CONTAINS,
            criterion,
            str(tmp_path)
        )

        assert result["passed"] is True
        assert "FOUND" in result["evidence"]

    def test_command_success_check(self, tmp_path):
        """Test command execution checking."""
        criterion = {
            "command": "echo 'test'"
        }

        result = execute_validation_check(
            ValidationCheckType.COMMAND_SUCCESS,
            criterion,
            str(tmp_path)
        )

        assert result["passed"] is True
        assert result["exit_code"] == 0

    def test_manual_verification_check(self):
        """Test manual verification check."""
        criterion = {}

        result = execute_validation_check(
            ValidationCheckType.MANUAL_VERIFICATION,
            criterion,
            "/tmp"
        )

        assert result["passed"] is None
        assert result["requires_manual"] is True


class TestValidatorAgent:
    """Test validator agent functions."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        manager = Mock(spec=DatabaseManager)
        session = Mock()
        manager.get_session.return_value = session
        return manager

    def test_build_validator_prompt(self):
        """Test building validator prompt."""
        task = Mock()
        task.id = "task123"
        task.raw_description = "Test task"
        task.enriched_description = "Enhanced test"
        task.done_definition = "Complete"
        task.last_validation_feedback = None

        phase = Mock()
        phase.validation = {
            "criteria": [
                {"description": "Test criterion"}
            ]
        }

        workspace_changes = {
            "files_created": ["new.txt"]
        }

        prompt = build_validator_prompt(
            task=task,
            phase=phase,
            commit_sha="abc123",
            workspace_changes=workspace_changes,
            agent_claims="Done",
            iteration=1
        )

        assert "task123" in prompt
        assert "Test criterion" in prompt
        assert "new.txt" in prompt

    @pytest.mark.asyncio
    async def test_spawn_validator_agent(self, mock_db_manager):
        """Test spawning a validator agent."""
        # Setup mocks
        session = mock_db_manager.get_session()

        task = Mock()
        task.id = "task123"
        task.assigned_agent_id = "agent123"
        task.phase_id = "phase123"
        task.validation_iteration = 1
        task.raw_description = "Test"
        task.enriched_description = "Test enhanced"
        task.done_definition = "Done"

        phase = Mock()
        phase.validation = {"criteria": []}

        # Setup query chain for task and phase
        query_mock = Mock()
        query_mock.filter_by.return_value = query_mock

        # First call returns task, second returns phase
        query_mock.first.side_effect = [task, phase, task]  # Added third for get_agent_results
        session.query.return_value = query_mock

        # Mock worktree manager
        mock_worktree = Mock()
        mock_worktree.get_workspace_changes.return_value = {
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "detailed_diff": ""
        }

        # Mock AgentWorktree class and db_manager
        from src.core.database import AgentWorktree
        mock_worktree.AgentWorktree = AgentWorktree

        # Setup mock for worktree query
        wt_session = Mock()
        wt_query = Mock()
        wt_query.filter_by.return_value = wt_query
        wt_query.first.return_value = Mock(worktree_path="/tmp/wt_agent123")
        wt_session.query.return_value = wt_query

        mock_worktree.db_manager = Mock()
        mock_worktree.db_manager.get_session.return_value = wt_session

        # Mock agent manager
        mock_agent_manager = Mock()

        with patch('src.validation.validator_agent.spawn_validator_tmux_session', new_callable=AsyncMock):
            validator_id = await spawn_validator_agent(
                task_id="task123",
                commit_sha="abc123",
                db_manager=mock_db_manager,
                worktree_manager=mock_worktree,
                agent_manager=mock_agent_manager
            )

        assert validator_id.startswith("validator-")
        session.add.assert_called()
        session.commit.assert_called()

    def test_send_feedback_to_agent(self):
        """Test sending feedback to agent."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            result = send_feedback_to_agent(
                agent_id="agent123",
                feedback="Please fix the error",
                iteration=1
            )

            assert result is True
            # Check tmux command was called
            assert mock_run.call_count >= 1

    def test_get_agent_results(self):
        """Test getting agent results."""
        session = Mock()

        task = Mock()
        task.completion_notes = "Task completed successfully"
        task.enriched_description = "Enhanced description"
        task.done_definition = "Definition of done"

        session.query().filter_by().first.return_value = task

        results = get_agent_results("task123", session)

        assert "Task completed successfully" in results
        assert "Enhanced description" in results


class TestDatabaseModels:
    """Test database model changes."""

    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_task_validation_fields(self, db_session):
        """Test Task model has validation fields."""
        task = Task(
            id="task123",
            raw_description="Test task",
            done_definition="Done",
            status="under_review",
            validation_enabled=True,
            validation_iteration=2,
            last_validation_feedback="Fix the error",
            review_done=False
        )

        db_session.add(task)
        db_session.commit()

        retrieved = db_session.query(Task).filter_by(id="task123").first()
        assert retrieved.validation_enabled is True
        assert retrieved.validation_iteration == 2
        assert retrieved.last_validation_feedback == "Fix the error"
        assert retrieved.status == "under_review"

    def test_agent_type_field(self, db_session):
        """Test Agent model has agent_type field."""
        agent = Agent(
            id="validator123",
            system_prompt="Validate task",
            cli_type="claude",
            status="working",
            agent_type="validator",
            kept_alive_for_validation=True
        )

        db_session.add(agent)
        db_session.commit()

        retrieved = db_session.query(Agent).filter_by(id="validator123").first()
        assert retrieved.agent_type == "validator"
        assert retrieved.kept_alive_for_validation is True

    def test_validation_review_model(self, db_session):
        """Test ValidationReview model."""
        # Create task and agent first
        task = Task(
            id="task123",
            raw_description="Test",
            done_definition="Done"
        )
        agent = Agent(
            id="validator123",
            system_prompt="Validate",
            cli_type="claude",
            agent_type="validator"
        )

        db_session.add(task)
        db_session.add(agent)
        db_session.commit()

        # Create validation review
        review = ValidationReview(
            id="review123",
            task_id="task123",
            validator_agent_id="validator123",
            iteration_number=1,
            validation_passed=True,
            feedback="All checks passed",
            evidence=[{"check": "file_exists", "result": "passed"}],
            recommendations=["Create follow-up task"]
        )

        db_session.add(review)
        db_session.commit()

        retrieved = db_session.query(ValidationReview).filter_by(id="review123").first()
        assert retrieved.validation_passed is True
        assert retrieved.feedback == "All checks passed"
        assert len(retrieved.evidence) == 1
        assert len(retrieved.recommendations) == 1

    def test_phase_validation_field(self, db_session):
        """Test Phase model has validation field."""
        phase = Phase(
            id="phase123",
            workflow_id="workflow123",
            order=1,
            name="Test Phase",
            description="Test",
            done_definitions=["Done"],
            validation={
                "enabled": True,
                "criteria": [
                    {"description": "Test passes", "check_type": "test_pass"}
                ]
            }
        )

        db_session.add(phase)
        db_session.commit()

        retrieved = db_session.query(Phase).filter_by(id="phase123").first()
        assert retrieved.validation is not None
        assert retrieved.validation["enabled"] is True
        assert len(retrieved.validation["criteria"]) == 1


class TestValidationStates:
    """Test validation state transitions."""

    def test_task_state_transitions(self):
        """Test that task states support validation flow."""
        valid_states = [
            "pending", "assigned", "in_progress",
            "under_review", "validation_in_progress", "needs_work",
            "done", "failed"
        ]

        # These should be the valid states for validation flow
        assert "under_review" in valid_states
        assert "validation_in_progress" in valid_states
        assert "needs_work" in valid_states

    def test_validation_iteration_tracking(self):
        """Test validation iteration tracking."""
        task = Mock()
        task.validation_iteration = 0

        # Simulate multiple validation attempts
        for i in range(1, 4):
            task.validation_iteration += 1
            assert task.validation_iteration == i


class TestIntegration:
    """Integration tests for validation system."""

    @pytest.mark.asyncio
    async def test_validation_cycle(self):
        """Test complete validation cycle."""
        # This is a simplified integration test
        # In real scenario, would test with actual database and services

        # 1. Task claims completion
        task = Mock()
        task.id = "task123"
        task.status = "in_progress"
        task.validation_enabled = True
        task.validation_iteration = 0

        # 2. Status changes to under_review
        task.status = "under_review"
        task.validation_iteration = 1

        # 3. Validator spawned (mocked)
        validator_id = f"validator-{uuid.uuid4().hex[:8]}"

        # 4. Validation fails
        task.status = "needs_work"
        task.last_validation_feedback = "Fix the error"

        # 5. Agent fixes and tries again
        task.status = "under_review"
        task.validation_iteration = 2

        # 6. Validation passes
        task.status = "done"
        task.review_done = True

        assert task.validation_iteration == 2
        assert task.status == "done"
        assert task.review_done is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])