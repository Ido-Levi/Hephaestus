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

    # Per-phase CLI configuration (optional - falls back to global defaults)
    cli_tool: Optional[str] = None           # "claude", "opencode", "droid", "codex", "swarm"
    cli_model: Optional[str] = None          # "sonnet", "opus", "haiku", "GLM-4.6", etc.
    glm_api_token_env: Optional[str] = None  # Environment variable name for GLM token

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

        # Include CLI configuration if set
        if self.cli_tool:
            data["cli_tool"] = self.cli_tool

        if self.cli_model:
            data["cli_model"] = self.cli_model

        if self.glm_api_token_env:
            data["glm_api_token_env"] = self.glm_api_token_env

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


@dataclass
class LaunchParameter:
    """
    A single parameter in a launch template.

    Used to generate dynamic forms for starting workflow executions from the UI.
    User inputs are substituted into phase fields using {param_name} placeholders.
    """

    name: str  # Parameter key, e.g., "bug_description"
    label: str  # Display label, e.g., "Bug Description"
    type: str  # "text", "textarea", "number", "boolean", "dropdown"
    required: bool = True
    default: Optional[Any] = None
    description: str = ""  # Help text shown below field
    options: List[str] = field(default_factory=list)  # For dropdown type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }
        if self.default is not None:
            data["default"] = self.default
        if self.options:
            data["options"] = self.options
        return data


@dataclass
class LaunchTemplate:
    """
    Template for launching a workflow from the UI.

    Defines the parameters needed to start a workflow and the initial task prompt.
    Parameters are substituted into phase fields using {param_name} syntax.
    """

    parameters: List[LaunchParameter]
    phase_1_task_prompt: str  # Template for first task, e.g., "Analyze bug: {bug_description}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "parameters": [p.to_dict() for p in self.parameters],
            "phase_1_task_prompt": self.phase_1_task_prompt,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LaunchTemplate":
        """Create LaunchTemplate from dictionary."""
        parameters = [
            LaunchParameter(
                name=p["name"],
                label=p["label"],
                type=p["type"],
                required=p.get("required", True),
                default=p.get("default"),
                description=p.get("description", ""),
                options=p.get("options", []),
            )
            for p in data.get("parameters", [])
        ]
        return cls(
            parameters=parameters,
            phase_1_task_prompt=data.get("phase_1_task_prompt", ""),
        )


@dataclass
class WorkflowDefinition:
    """
    A workflow definition (template) that can be executed multiple times.

    This represents a reusable workflow template that describes the phases
    and configuration. Multiple concurrent executions can be started from
    a single definition.
    """

    id: str  # Unique identifier (e.g., "prd-to-software", "bugfix")
    name: str  # Human-readable name (e.g., "PRD to Software Builder")
    phases: List[Phase]  # List of phases in this workflow
    config: Optional[WorkflowConfig] = None  # Workflow configuration
    description: str = ""  # Description of what this workflow does
    launch_template: Optional[LaunchTemplate] = None  # Template for UI-based workflow launching


@dataclass
class WorkflowExecution:
    """
    A running instance of a workflow definition.

    Each execution tracks its own tasks, agents, and progress independently.
    Multiple executions can run concurrently from the same definition.
    """

    id: str  # UUID - unique execution ID
    definition_id: str  # Reference to the workflow definition
    description: str  # What this execution is doing (e.g., "Building URL Shortener")
    status: str  # "active", "paused", "completed", "failed"
    created_at: datetime

    # Statistics
    active_tasks: int = 0
    total_tasks: int = 0
    done_tasks: int = 0
    failed_tasks: int = 0
    active_agents: int = 0

    # Optional metadata
    working_directory: Optional[str] = None
    definition_name: Optional[str] = None  # Cached from definition for convenience
