"""Data models for phase system."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
import re


def validate_cli_tool(cli_tool: Optional[str]) -> bool:
    """Validate that cli_tool is a recognized CLI agent type.

    Args:
        cli_tool: The CLI tool name to validate (or None for default)

    Returns:
        True if valid

    Raises:
        ValueError: If cli_tool is not in the valid list
    """
    if cli_tool is None:
        return True  # None is valid (uses default from global config)

    # Import here to avoid circular dependency
    from src.interfaces.cli_interface import CLI_AGENTS

    valid_tools = list(CLI_AGENTS.keys())

    if cli_tool not in valid_tools:
        raise ValueError(
            f"Invalid cli_tool '{cli_tool}'. Must be one of: {', '.join(valid_tools)}"
        )

    return True


class PhaseDefinition(BaseModel):
    """Model for a single phase definition from YAML."""

    filename: str = Field(..., description="Original filename (e.g., '01_phase_planning.yaml')")
    order: int = Field(..., description="Phase order extracted from filename prefix")
    name: str = Field(..., description="Phase name extracted from filename")
    description: str = Field(..., description="Detailed description of the phase")
    done_definitions: List[str] = Field(
        default_factory=list,
        description="List of criteria that must be met for phase completion"
    )
    additional_notes: Optional[str] = Field(
        None,
        description="Additional context or notes for the phase"
    )
    outputs: Optional[str] = Field(
        None,
        description="Expected outputs or deliverables from this phase"
    )
    next_steps: Optional[str] = Field(
        None,
        description="Instructions for transitioning to next phase"
    )
    working_directory: Optional[str] = Field(
        None,
        description="Default working directory for agents in this phase"
    )
    validation: Optional[Dict[str, Any]] = Field(
        None,
        description="Validation configuration for the phase"
    )
    # Per-phase CLI configuration (optional - falls back to global defaults)
    cli_tool: Optional[str] = Field(
        None,
        description="CLI tool to use for this phase (claude, opencode, droid, codex, swarm)"
    )
    cli_model: Optional[str] = Field(
        None,
        description="CLI model to use for this phase (sonnet, opus, haiku, GLM-4.6, etc.)"
    )
    glm_api_token_env: Optional[str] = Field(
        None,
        description="Environment variable name for GLM API token"
    )

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate that filename follows XX_name.yaml pattern."""
        pattern = r'^\d{2}_[\w_]+\.yaml$'
        if not re.match(pattern, v):
            raise ValueError(
                f"Filename '{v}' must follow pattern: XX_phase_name.yaml "
                "(where XX is a two-digit number)"
            )
        return v

    @field_validator('cli_tool')
    @classmethod
    def validate_cli_tool_field(cls, v: Optional[str]) -> Optional[str]:
        """Validate that cli_tool is a recognized CLI agent type."""
        validate_cli_tool(v)  # Will raise ValueError if invalid
        return v

    @classmethod
    def from_yaml_content(cls, filename: str, content: Dict[str, Any]) -> "PhaseDefinition":
        """Create PhaseDefinition from YAML content.

        Args:
            filename: The YAML file name
            content: Parsed YAML content

        Returns:
            PhaseDefinition instance
        """
        # Extract order and name from filename
        match = re.match(r'^(\d{2})_(.+)\.yaml$', filename)
        if not match:
            raise ValueError(f"Invalid filename format: {filename}")

        order = int(match.group(1))
        name = match.group(2).replace('_', ' ').title()

        # Handle both snake_case and Title Case field names from YAML
        description = content.get('description') or content.get('Description', '')
        done_definitions = (
            content.get('done_definitions') or
            content.get('Done_Definitions') or
            content.get('done_definition') or
            content.get('Done_Definition') or
            []
        )

        # Ensure done_definitions is a list
        if isinstance(done_definitions, str):
            done_definitions = [done_definitions]

        additional_notes = (
            content.get('additional_notes') or
            content.get('Additional_Notes')
        )

        outputs = content.get('outputs') or content.get('Outputs')
        next_steps = content.get('next_steps') or content.get('Next_Steps')
        working_directory = (
            content.get('working_directory') or
            content.get('Working_Directory')
        )

        # Parse validation configuration
        validation = content.get('validation') or content.get('Validation')

        # Parse CLI configuration
        cli_tool = content.get('cli_tool') or content.get('Cli_Tool')
        cli_model = content.get('cli_model') or content.get('Cli_Model')
        glm_api_token_env = content.get('glm_api_token_env') or content.get('Glm_Api_Token_Env')

        return cls(
            filename=filename,
            order=order,
            name=name,
            description=description,
            done_definitions=done_definitions,
            additional_notes=additional_notes,
            outputs=outputs,
            next_steps=next_steps,
            working_directory=working_directory,
            validation=validation,
            cli_tool=cli_tool,
            cli_model=cli_model,
            glm_api_token_env=glm_api_token_env,
        )


class WorkflowDefinition(BaseModel):
    """Model for a complete workflow with multiple phases."""

    name: str = Field(..., description="Workflow name")
    phases_folder: str = Field(..., description="Path to folder containing phase YAML files")
    phases: List[PhaseDefinition] = Field(
        default_factory=list,
        description="Ordered list of phases in the workflow"
    )

    def get_phase_by_order(self, order: int) -> Optional[PhaseDefinition]:
        """Get a phase by its order number."""
        for phase in self.phases:
            if phase.order == order:
                return phase
        return None

    def get_phase_by_name(self, name: str) -> Optional[PhaseDefinition]:
        """Get a phase by its name."""
        for phase in self.phases:
            if phase.name.lower() == name.lower():
                return phase
        return None

    def get_next_phase(self, current_order: int) -> Optional[PhaseDefinition]:
        """Get the next phase after the given order."""
        next_phases = [p for p in self.phases if p.order > current_order]
        if next_phases:
            return min(next_phases, key=lambda p: p.order)
        return None


class PhaseContext(BaseModel):
    """Context information for a phase during execution."""

    phase_id: str = Field(..., description="Phase ID in database")
    workflow_id: str = Field(..., description="Workflow ID in database")
    phase_definition: PhaseDefinition = Field(..., description="Phase definition")
    all_phases: List[PhaseDefinition] = Field(..., description="All phases in workflow")
    current_status: str = Field(default="pending", description="Current execution status")
    active_tasks: int = Field(default=0, description="Number of active tasks in this phase")
    completed_tasks: int = Field(default=0, description="Number of completed tasks in this phase")

    def to_prompt_context(self) -> str:
        """Generate context string for agent prompts."""
        context = f"""
## WORKFLOW PHASE INFORMATION

### Current Phase: {self.phase_definition.name} (Phase {self.phase_definition.order})

**Description:**
{self.phase_definition.description}

**Completion Criteria:**
"""
        for criterion in self.phase_definition.done_definitions:
            context += f"- {criterion}\n"

        if self.phase_definition.additional_notes:
            context += f"\n**Additional Notes:**\n{self.phase_definition.additional_notes}\n"

        if self.phase_definition.outputs:
            context += f"\n**Expected Outputs:**\n{self.phase_definition.outputs}\n"

        context += "\n### All Workflow Phases:\n"
        for phase in self.all_phases:
            status_indicator = "✓" if phase.order < self.phase_definition.order else (
                "→" if phase.order == self.phase_definition.order else "○"
            )
            context += f"{status_indicator} Phase {phase.order}: {phase.name}\n"

        # Add detailed phase summaries for cross-phase awareness
        context += "\n### Phase Details for Cross-Phase Task Creation:\n\n"
        for phase in self.all_phases:
            if phase.order != self.phase_definition.order:  # Skip current phase (already detailed above)
                context += f"**Phase {phase.order}: {phase.name}**\n"
                context += f"- Purpose: {phase.description}{'...' if len(phase.description) > 20099 else ''}\n"
                context += f"- Key Outputs: {phase.outputs}{'...' if phase.outputs and len(phase.outputs) > 15099 else phase.outputs or 'Not specified'}\n"

                # Show first 2 completion criteria for context
                if phase.done_definitions:
                    context += "- Main Goals:\n"
                    for i, criterion in enumerate(phase.done_definitions):
                        context += f"  • {criterion}\n"
                context += "\n"

        context += f"""
### Creating Tasks for Different Phases:
When creating tasks, ALWAYS specify the phase number: phase=1, phase=2, etc.

**Phase Assignment Guidelines:**
"""
        # Provide specific guidance for each phase
        for phase in self.all_phases:
            context += f"- **Phase {phase.order}** ({phase.name}): {phase.description[:150]}...\n"

        context += f"""
**Examples:**
- create_task(description="Design API endpoints", done_definition="API spec complete", phase=1)
- create_task(description="Implement user auth", done_definition="Auth working", phase=2)

**Important:** You're currently in Phase {self.phase_definition.order}. You can create tasks for:
- Your own phase (phase={self.phase_definition.order}) for parallel work
- Earlier phases (phase < {self.phase_definition.order}) if you discover gaps
- Later phases (phase > {self.phase_definition.order}) for future work
"""

        return context


class PhasesConfig(BaseModel):
    """Configuration for workflow result handling and ticket tracking from phases_config.yaml."""

    has_result: bool = Field(
        default=False,
        description="Whether this workflow expects a definitive result/solution"
    )
    result_criteria: Optional[str] = Field(
        default=None,
        description="Clear criteria that submitted results must meet for validation"
    )
    on_result_found: Literal["stop_all", "do_nothing"] = Field(
        default="do_nothing",
        description="Action to take when a valid result is found and validated"
    )
    enable_tickets: bool = Field(
        default=False,
        description="Whether Kanban board ticket tracking is enabled for this workflow"
    )
    board_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Kanban board configuration (columns, ticket types, etc.)"
    )

    @field_validator('result_criteria')
    @classmethod
    def validate_result_criteria(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that result_criteria is provided when has_result is True."""
        has_result = info.data.get('has_result', False)
        if has_result and not v:
            raise ValueError("result_criteria must be provided when has_result is True")
        return v

    @classmethod
    def from_yaml_content(cls, content: Dict[str, Any]) -> "PhasesConfig":
        """Create PhasesConfig from YAML content.

        Args:
            content: Parsed YAML content from phases_config.yaml

        Returns:
            PhasesConfig instance with defaults for missing fields
        """
        return cls(
            has_result=content.get('has_result', False),
            result_criteria=content.get('result_criteria'),
            on_result_found=content.get('on_result_found', 'do_nothing'),
            enable_tickets=content.get('enable_tickets', False),
            board_config=content.get('board_config')
        )