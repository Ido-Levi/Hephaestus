"""Tests for SDK data models."""

import pytest
from datetime import datetime, timedelta

from src.sdk.models import Phase, TaskStatus, ValidationCriteria, WorkflowResult


def test_phase_creation():
    """Test creating a Phase object."""
    phase = Phase(
        id=1,
        name="planning",
        description="Plan the implementation",
        done_definitions=["Plan created", "Tasks identified"],
        working_directory="/path/to/project",
        additional_notes="Important notes here",
        outputs=["plan.md"],
        next_steps=["Phase 2: Implementation"],
    )

    assert phase.id == 1
    assert phase.name == "planning"
    assert len(phase.done_definitions) == 2
    assert phase.outputs == ["plan.md"]


def test_phase_to_yaml_dict():
    """Test converting Phase to YAML dict."""
    phase = Phase(
        id=1,
        name="planning",
        description="Plan the implementation",
        done_definitions=["Plan created"],
        working_directory="/path/to/project",
    )

    yaml_dict = phase.to_yaml_dict()

    assert "description" in yaml_dict
    assert "Done_Definitions" in yaml_dict
    assert "working_directory" in yaml_dict
    assert yaml_dict["description"] == "Plan the implementation"


def test_phase_with_validation():
    """Test Phase with validation criteria."""
    criteria = ValidationCriteria(
        enabled=True,
        criteria=[
            {"description": "File exists", "check_type": "file_exists", "params": {"path": "plan.md"}}
        ],
    )

    phase = Phase(
        id=1,
        name="planning",
        description="Plan",
        done_definitions=["Done"],
        working_directory=".",
        validation=criteria,
    )

    assert phase.validation.enabled is True
    assert len(phase.validation.criteria) == 1

    yaml_dict = phase.to_yaml_dict()
    assert "validation" in yaml_dict
    assert yaml_dict["validation"]["enabled"] is True


def test_task_status_creation():
    """Test creating TaskStatus object."""
    task = TaskStatus(
        id="task-123",
        status="in_progress",
        description="Fix the bug",
        agent_id="agent-456",
        phase_id=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        summary="Working on it",
        priority="high",
    )

    assert task.id == "task-123"
    assert task.status == "in_progress"
    assert task.priority == "high"


def test_workflow_result():
    """Test WorkflowResult creation."""
    tasks = [
        TaskStatus(
            id="task-1",
            status="done",
            description="Task 1",
            agent_id="agent-1",
            phase_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    ]

    result = WorkflowResult(
        workflow_name="test_workflow",
        status="completed",
        tasks=tasks,
        outputs={1: ["plan.md", "analysis.md"]},
        duration=timedelta(minutes=5),
    )

    assert result.workflow_name == "test_workflow"
    assert result.status == "completed"
    assert len(result.tasks) == 1
    assert 1 in result.outputs
    assert result.error is None
