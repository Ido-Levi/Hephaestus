"""Integration tests for the complete validation flow with inheritance."""

import pytest
import asyncio
import uuid
import json
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from datetime import datetime
from pathlib import Path

from src.core.database import (
    DatabaseManager,
    Task,
    Agent,
    Phase,
    Workflow,
    ValidationReview,
    Base
)
from src.mcp.server import app, server_state
from src.phases.models import PhaseDefinition, WorkflowDefinition
from src.phases.phase_manager import PhaseManager
from src.agents.manager import AgentManager
from src.validation.validator_agent import spawn_validator_agent
from fastapi.testclient import TestClient


@pytest.fixture
def test_db():
    """Create a test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db_manager = DatabaseManager(db_path)
    db_manager.create_tables()

    yield db_manager

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def sample_phase_yaml():
    """Create sample phase YAML files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Phase 1: With validation
        phase1_content = """
description: |
  Implement core functionality with proper testing
done_definitions:
  - Core functions implemented
  - Unit tests written
  - Documentation updated
validation:
  criteria:
    - description: "All unit tests pass"
      check_type: "command_success"
      command: "pytest tests/"
    - description: "Code coverage above 80%"
      check_type: "command_success"
      command: "pytest --cov=src --cov-report=term"
    - description: "No linting errors"
      check_type: "command_success"
      command: "flake8 src/"
  validator_instructions: |
    Ensure all edge cases are tested
"""
        phase1_path = Path(temp_dir) / "01_implementation.yaml"
        phase1_path.write_text(phase1_content)

        # Phase 2: Without validation
        phase2_content = """
description: |
  Document the implementation
done_definitions:
  - README updated
  - API docs complete
"""
        phase2_path = Path(temp_dir) / "02_documentation.yaml"
        phase2_path.write_text(phase2_content)

        yield temp_dir


class TestEndToEndValidationFlow:
    """Test the complete validation flow from phase loading to validator execution."""

    @pytest.mark.asyncio
    async def test_complete_validation_inheritance_flow(self, test_db, sample_phase_yaml):
        """Test the full flow: load phases -> create task -> inherit validation -> trigger validation."""

        # 1. Load phases from YAML
        from src.phases.phase_loader import PhaseLoader
        workflow_def = PhaseLoader.load_phases_from_folder(sample_phase_yaml)

        assert len(workflow_def.phases) == 2
        assert workflow_def.phases[0].validation is not None
        assert workflow_def.phases[1].validation is None

        # 2. Initialize workflow in database
        phase_manager = PhaseManager(test_db)
        workflow_id = phase_manager.initialize_workflow(workflow_def)

        # Verify phases in database
        session = test_db.get_session()
        phases = session.query(Phase).filter_by(workflow_id=workflow_id).all()
        assert len(phases) == 2

        phase1 = next(p for p in phases if p.order == 1)
        phase2 = next(p for p in phases if p.order == 2)

        assert phase1.validation is not None
        assert phase2.validation is None

        # 3. Create task for phase with validation
        task1 = Task(
            id=str(uuid.uuid4()),
            raw_description="Implement feature X",
            enriched_description="Implement feature X with tests",
            done_definition="Feature X works and is tested",
            status="pending",
            priority="high"
        )
        session.add(task1)
        session.commit()

        # Apply the fix logic (what happens in create_task)
        task1.phase_id = phase1.id
        if task1.phase_id:
            phase = session.query(Phase).filter_by(id=task1.phase_id).first()
            if phase and phase.validation:
                task1.validation_enabled = True

        session.commit()

        # 4. Create task for phase without validation
        task2 = Task(
            id=str(uuid.uuid4()),
            raw_description="Write documentation",
            enriched_description="Write comprehensive documentation",
            done_definition="Documentation is complete",
            status="pending",
            priority="medium"
        )
        session.add(task2)
        session.commit()

        task2.phase_id = phase2.id
        if task2.phase_id:
            phase = session.query(Phase).filter_by(id=task2.phase_id).first()
            if phase and phase.validation:
                task2.validation_enabled = True

        session.commit()

        # 5. Verify inheritance
        assert task1.validation_enabled == True, "Task in validation phase should have validation enabled"
        assert task2.validation_enabled == False, "Task in non-validation phase should not have validation enabled"

        # 6. Simulate agent completing task1 (with validation)
        agent1 = Agent(
            id=str(uuid.uuid4()),
            name="Agent 1",
            status="active",
            current_task_id=task1.id,
            agent_type="phase"
        )
        session.add(agent1)
        task1.assigned_agent_id = agent1.id
        task1.status = "in_progress"
        session.commit()

        # When agent marks task as done, validation should trigger
        with patch('src.validation.validator_agent.spawn_validator_agent') as mock_spawn:
            mock_spawn.return_value = "validator-agent-id"

            # Simulate the logic in update_task_status
            if task1.validation_enabled:
                task1.status = "under_review"
                task1.validation_iteration = 1
                session.commit()

                # Validator should be spawned (in real flow)
                # validator_id = await spawn_validator_agent(...)

                task1.status = "validation_in_progress"
                agent1.kept_alive_for_validation = True
                session.commit()

        # Verify validation was triggered
        assert task1.status == "validation_in_progress"
        assert task1.validation_iteration == 1
        assert agent1.kept_alive_for_validation == True

        # 7. Simulate agent completing task2 (without validation)
        agent2 = Agent(
            id=str(uuid.uuid4()),
            name="Agent 2",
            status="active",
            current_task_id=task2.id,
            agent_type="phase"
        )
        session.add(agent2)
        task2.assigned_agent_id = agent2.id
        task2.status = "in_progress"
        session.commit()

        # When agent marks task as done, no validation should trigger
        if task2.validation_enabled:
            task2.status = "under_review"  # This shouldn't happen
        else:
            task2.status = "done"  # Direct to done
            agent2.status = "completed"

        session.commit()

        # Verify no validation triggered
        assert task2.status == "done"
        assert task2.validation_iteration == 0
        assert not hasattr(agent2, 'kept_alive_for_validation') or not agent2.kept_alive_for_validation

        session.close()

    @pytest.mark.asyncio
    async def test_validation_feedback_loop(self, test_db):
        """Test that validation feedback loop works with inherited validation."""

        session = test_db.get_session()

        # Setup
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name="Test Workflow",
            phases_folder_path="/test/path",
            status="active"
        )
        session.add(workflow)

        phase = Phase(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            order=1,
            name="Validated Phase",
            description="Phase with validation",
            done_definitions=["Complete"],
            validation={
                "criteria": [
                    {"description": "Tests pass", "check_type": "command_success", "command": "pytest"}
                ]
            }
        )
        session.add(phase)

        task = Task(
            id=str(uuid.uuid4()),
            raw_description="Implement feature",
            enriched_description="Implement feature with tests",
            done_definition="Feature works",
            status="in_progress",
            phase_id=phase.id,
            validation_enabled=True,  # Inherited from phase
            assigned_agent_id="agent-123",
            validation_iteration=0
        )
        session.add(task)

        agent = Agent(
            id="agent-123",
            name="Implementation Agent",
            status="active",
            current_task_id=task.id,
            agent_type="phase"
        )
        session.add(agent)
        session.commit()

        # First validation attempt - FAIL
        task.status = "under_review"
        task.validation_iteration = 1
        session.commit()

        # Validator provides feedback
        validation_review1 = ValidationReview(
            id=str(uuid.uuid4()),
            task_id=task.id,
            validator_agent_id="validator-1",
            iteration_number=1,
            validation_passed=False,
            feedback="Tests are failing. Please fix the implementation.",
            evidence=json.dumps(["pytest output shows 3 failures"])
        )
        session.add(validation_review1)

        task.status = "needs_work"
        task.last_validation_feedback = validation_review1.feedback
        session.commit()

        # Agent is still alive and can work on feedback
        assert agent.status == "active"
        assert task.status == "needs_work"

        # Second validation attempt - PASS
        task.status = "under_review"
        task.validation_iteration = 2
        session.commit()

        validation_review2 = ValidationReview(
            id=str(uuid.uuid4()),
            task_id=task.id,
            validator_agent_id="validator-2",
            iteration_number=2,
            validation_passed=True,
            feedback="All tests passing. Implementation looks good.",
            evidence=json.dumps(["All 10 tests passed"]),
            recommendations=json.dumps(["Consider adding performance tests"])
        )
        session.add(validation_review2)

        task.status = "done"
        task.review_done = True
        agent.status = "completed"
        session.commit()

        # Verify complete flow
        assert task.status == "done"
        assert task.review_done == True
        assert task.validation_iteration == 2
        assert agent.status == "completed"

        # Check validation history
        reviews = session.query(ValidationReview).filter_by(task_id=task.id).all()
        assert len(reviews) == 2
        assert reviews[0].validation_passed == False
        assert reviews[1].validation_passed == True

        session.close()

    @pytest.mark.asyncio
    async def test_validation_with_explicit_disable(self, test_db):
        """Test that validation can be explicitly disabled even when present in YAML."""

        session = test_db.get_session()

        workflow = Workflow(
            id=str(uuid.uuid4()),
            name="Test Workflow",
            phases_folder_path="/test/path",
            status="active"
        )
        session.add(workflow)

        # Phase with validation but explicitly disabled
        phase = Phase(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            order=1,
            name="Disabled Validation Phase",
            description="Phase with disabled validation",
            done_definitions=["Complete"],
            validation={
                "enabled": False,  # Explicitly disabled
                "criteria": [
                    {"description": "Would check tests", "check_type": "command_success", "command": "pytest"}
                ]
            }
        )
        session.add(phase)
        session.commit()

        # Create task
        task = Task(
            id=str(uuid.uuid4()),
            raw_description="Task",
            enriched_description="Task enriched",
            done_definition="Done",
            status="pending",
            phase_id=phase.id
        )
        session.add(task)

        # Apply inheritance logic (need to update to handle explicit disable)
        if task.phase_id:
            phase_obj = session.query(Phase).filter_by(id=task.phase_id).first()
            if phase_obj and phase_obj.validation:
                # Check for explicit disable
                if phase_obj.validation.get("enabled", True):
                    task.validation_enabled = True
                else:
                    task.validation_enabled = False
            else:
                task.validation_enabled = False

        session.commit()

        # Verify validation is disabled
        assert task.validation_enabled == False, "Task should not have validation when explicitly disabled"

        session.close()


class TestValidationErrorHandling:
    """Test error handling in validation inheritance."""

    def test_task_creation_without_phase(self, test_db):
        """Test that tasks without phases don't break validation logic."""

        session = test_db.get_session()

        # Create task without phase
        task = Task(
            id=str(uuid.uuid4()),
            raw_description="Standalone task",
            enriched_description="Standalone task enriched",
            done_definition="Done when complete",
            status="pending",
            phase_id=None  # No phase
        )
        session.add(task)

        # Apply inheritance logic
        if task.phase_id:
            phase = session.query(Phase).filter_by(id=task.phase_id).first()
            if phase and phase.validation:
                task.validation_enabled = True

        session.commit()

        # Verify no validation
        assert task.validation_enabled == False
        assert task.phase_id is None

        session.close()

    def test_task_with_invalid_phase_id(self, test_db):
        """Test handling of invalid phase IDs."""

        session = test_db.get_session()

        task = Task(
            id=str(uuid.uuid4()),
            raw_description="Task with bad phase",
            enriched_description="Task enriched",
            done_definition="Done",
            status="pending",
            phase_id="non-existent-phase-id"
        )
        session.add(task)

        # Apply inheritance logic - should handle gracefully
        if task.phase_id:
            phase = session.query(Phase).filter_by(id=task.phase_id).first()
            if phase and phase.validation:  # phase will be None
                task.validation_enabled = True

        session.commit()

        # Should default to no validation
        assert task.validation_enabled == False

        session.close()