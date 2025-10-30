"""Data models for the Hephaestus SDK."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any


@dataclass
class ValidationCriteria:
    """Validation criteria for a phase."""

    enabled: bool = False
    criteria: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Phase:
    """
    Represents a workflow phase.

    Can be loaded from YAML or created programmatically in Python.
    """

    id: int
    name: str
    description: str
    done_definitions: List[str]
    working_directory: str
    additional_notes: str = ""
    outputs: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    validation: Optional[ValidationCriteria] = None

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert Phase to YAML-compatible dictionary."""
        # Convert lists to multiline strings for outputs and next_steps
        outputs_str = "\n".join(f"- {item}" for item in self.outputs) if self.outputs else ""
        next_steps_str = "\n".join(f"- {item}" for item in self.next_steps) if self.next_steps else ""

        data = {
            "description": self.description,
            "Done_Definitions": self.done_definitions,
            "working_directory": self.working_directory,
        }

        if outputs_str:
            data["Outputs"] = outputs_str

        if next_steps_str:
            data["Next_Steps"] = next_steps_str

        if self.additional_notes:
            data["Additional_Notes"] = self.additional_notes

        if self.validation and self.validation.enabled:
            data["validation"] = {
                "enabled": True,
                "criteria": self.validation.criteria,
            }

        return data


@dataclass
class TaskStatus:
    """Status information for a task."""

    id: str
    status: str  # "pending", "assigned", "in_progress", "done", "failed"
    description: str
    agent_id: Optional[str]
    phase_id: int
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    priority: str = "medium"


@dataclass
class TaskUpdate:
    """Real-time update for a task (from streaming)."""

    task_id: str
    status: str
    timestamp: datetime
    output: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStatus:
    """Status information for an agent."""

    id: str
    task_id: str
    status: str
    created_at: datetime
    last_active: datetime
    tmux_session: Optional[str] = None


@dataclass
class WorkflowResult:
    """Result of a completed workflow execution."""

    workflow_name: str
    status: str  # "completed", "failed", "partial"
    tasks: List[TaskStatus]
    outputs: Dict[int, List[str]]  # phase_id -> output files
    duration: timedelta
    error: Optional[str] = None


@dataclass
class WorkflowConfig:
    """
    Workflow-level configuration for result handling and ticket tracking.

    This corresponds to phases_config.yaml in YAML-based workflows.
    """

    has_result: bool = False
    result_criteria: Optional[str] = None
    on_result_found: str = "do_nothing"  # "stop_all" or "do_nothing"
    enable_tickets: bool = False
    board_config: Optional[Dict[str, Any]] = None

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-compatible dictionary."""
        data = {
            "has_result": self.has_result,
            "on_result_found": self.on_result_found,
            "enable_tickets": self.enable_tickets,
        }

        if self.result_criteria:
            data["result_criteria"] = self.result_criteria

        if self.board_config:
            data["board_config"] = self.board_config

        return data


@dataclass
class Workflow:
    """A workflow consisting of multiple phases."""

    name: str
    phases: List[Phase]
    config: Optional[WorkflowConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
