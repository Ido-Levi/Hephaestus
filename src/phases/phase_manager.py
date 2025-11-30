"""Phase manager for runtime orchestration of workflow phases."""

import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import joinedload
from src.core.database import (
    DatabaseManager, Workflow, Phase, PhaseExecution, Task,
    WorkflowDefinition as DBWorkflowDefinition
)
from src.phases.models import WorkflowDefinition, PhaseDefinition, PhaseContext, PhasesConfig
from src.phases.phase_loader import PhaseLoader
from src.core.simple_config import get_config

logger = logging.getLogger(__name__)


def substitute_params(text: str, params: Dict[str, Any]) -> str:
    """Replace {param_name} placeholders with actual values.

    Args:
        text: Text containing {param_name} placeholders
        params: Dictionary of parameter name -> value

    Returns:
        Text with placeholders replaced
    """
    if not text or not params:
        return text

    result = text
    for key, value in params.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value) if value is not None else "")
    return result


def substitute_params_in_list(items: List[str], params: Dict[str, Any]) -> List[str]:
    """Replace {param_name} placeholders in a list of strings.

    Args:
        items: List of strings containing placeholders
        params: Dictionary of parameter name -> value

    Returns:
        List with placeholders replaced in each item
    """
    if not items or not params:
        return items

    return [substitute_params(item, params) for item in items]


class PhaseManager:
    """Manages workflow phases at runtime with support for multiple concurrent workflows."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize phase manager.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

        # Legacy single workflow support (for backward compatibility)
        self.active_workflow: Optional[WorkflowDefinition] = None
        self.workflow_id: Optional[str] = None

        # Multi-workflow support
        self.definitions: Dict[str, DBWorkflowDefinition] = {}  # definition_id -> definition
        self.active_executions: Dict[str, str] = {}  # workflow_id -> definition_id

        self.phases_config_cache: Dict[str, PhasesConfig] = {}  # Cache for workflow configs

    def load_active_workflow(self) -> Optional[str]:
        """Load the first active workflow from the database.

        This is called on monitor startup to resume tracking an existing workflow.
        If multiple active workflows exist, loads the one with the most tasks.

        Returns:
            Workflow ID if found, None otherwise
        """
        session = self.db_manager.get_session()
        try:
            # Find ALL active workflows
            all_workflows = session.query(Workflow).filter_by(
                status='active'
            ).order_by(Workflow.created_at.desc()).all()

            if not all_workflows:
                logger.info("[DIAGNOSTIC] No active workflows found in database")
                return None

            logger.info(f"[DIAGNOSTIC] Found {len(all_workflows)} active workflows:")

            # Check task count for each workflow
            workflow_with_tasks = None
            max_tasks = 0

            for wf in all_workflows:
                task_count = session.query(Task).filter_by(workflow_id=wf.id).count()
                done_count = session.query(Task).filter_by(workflow_id=wf.id, status='done').count()
                failed_count = session.query(Task).filter_by(workflow_id=wf.id, status='failed').count()
                active_count = session.query(Task).filter(
                    Task.workflow_id == wf.id,
                    Task.status.in_(['pending', 'assigned', 'in_progress'])
                ).count()

                logger.info(f"[DIAGNOSTIC]   - {wf.name} (ID: {wf.id[:8]}...)")
                logger.info(f"[DIAGNOSTIC]     Created: {wf.created_at}")
                logger.info(f"[DIAGNOSTIC]     Tasks: {task_count} total ({done_count} done, {failed_count} failed, {active_count} active)")
                logger.info(f"[DIAGNOSTIC]     Phases folder: {wf.phases_folder_path}")

                if task_count > max_tasks:
                    max_tasks = task_count
                    workflow_with_tasks = wf

            # Select the workflow with the most tasks (or newest if tie)
            workflow = workflow_with_tasks if workflow_with_tasks else all_workflows[0]

            logger.info(f"[DIAGNOSTIC] Selected workflow: {workflow.name} (ID: {workflow.id[:8]}...)")
            logger.info(f"[DIAGNOSTIC] Reason: {'Most tasks' if workflow == workflow_with_tasks and max_tasks > 0 else 'Newest created'}")
            logger.info(f"[DIAGNOSTIC] Phases folder: {workflow.phases_folder_path}")

            # Load the workflow definition from the phases folder
            try:
                workflow_def = PhaseLoader.load_phases_from_folder(workflow.phases_folder_path)
                self.active_workflow = workflow_def
                self.workflow_id = workflow.id

                logger.info(f"[DIAGNOSTIC] Successfully loaded workflow '{workflow.name}' with {len(workflow_def.phases)} phases")
                logger.info(f"[DIAGNOSTIC] PhaseManager.workflow_id set to: {self.workflow_id[:8]}...")

                return self.workflow_id

            except Exception as e:
                logger.error(f"[DIAGNOSTIC] Failed to load workflow definition from {workflow.phases_folder_path}: {e}")
                logger.warning(f"[DIAGNOSTIC] Will set workflow_id anyway to allow diagnostic agent to work")
                # Even if we can't load the full definition, set the workflow_id
                # so diagnostic checks can still run
                self.workflow_id = workflow.id
                return self.workflow_id

        except Exception as e:
            logger.error(f"[DIAGNOSTIC] Failed to load active workflow: {e}")
            return None
        finally:
            session.close()

    def initialize_workflow(self, workflow_def: WorkflowDefinition, phases_config: Optional['PhasesConfig'] = None) -> str:
        """Initialize a workflow and its phases in the database.

        If a workflow with the same name already exists, updates its phases_folder_path
        instead of creating a new one. This allows config updates on service restart.

        Args:
            workflow_def: Workflow definition loaded from YAML
            phases_config: Phases configuration for ticket tracking and result handling

        Returns:
            Workflow ID
        """
        session = self.db_manager.get_session()

        try:
            # SINGLE WORKFLOW POLICY: Check if ANY active workflow exists
            # We maintain only ONE workflow at a time - reuse it on restart
            existing_workflow = session.query(Workflow).filter(
                Workflow.status.in_(["active", "paused"])
            ).first()

            if existing_workflow:
                # Reuse existing workflow - update phases folder path
                logger.info(f"♻️  Reusing existing workflow '{existing_workflow.name}' (ID: {existing_workflow.id})")
                logger.info(f"   Updating phases_folder_path from {existing_workflow.phases_folder_path} to {workflow_def.phases_folder}")

                existing_workflow.phases_folder_path = workflow_def.phases_folder
                # Update the name to match the current workflow definition
                existing_workflow.name = workflow_def.name
                session.commit()

                workflow_id = existing_workflow.id
                logger.info(f"✅ Updated workflow with new phases folder path")
            else:
                # Create new workflow record
                workflow_id = str(uuid.uuid4())
                workflow = Workflow(
                    id=workflow_id,
                    name=workflow_def.name,
                    phases_folder_path=workflow_def.phases_folder,
                    status="active",
                )
                session.add(workflow)

                # Only create phase records for NEW workflows
                for phase_def in workflow_def.phases:
                    phase_id = str(uuid.uuid4())
                    phase = Phase(
                        id=phase_id,
                        workflow_id=workflow_id,
                        order=phase_def.order,
                        name=phase_def.name,
                        description=phase_def.description,
                        done_definitions=phase_def.done_definitions,
                        additional_notes=phase_def.additional_notes,
                        outputs=phase_def.outputs,
                        next_steps=phase_def.next_steps,
                        working_directory=phase_def.working_directory,
                        validation=phase_def.validation,  # Add validation config
                    )
                    session.add(phase)

                    # Create initial execution record
                    execution = PhaseExecution(
                        id=str(uuid.uuid4()),
                        phase_id=phase_id,
                        workflow_execution_id=workflow_id,
                        status="pending",
                    )
                    session.add(execution)

                # Create BoardConfig if ticket tracking is enabled
                if phases_config and phases_config.enable_tickets and phases_config.board_config:
                    from src.core.database import BoardConfig

                    board_id = f"board-{str(uuid.uuid4())}"
                    # Read global defaults for human approval
                    config = get_config()
                    default_human_review = getattr(config, 'default_human_review', False)
                    default_approval_timeout = getattr(config, 'default_approval_timeout', 1800)

                    board_config = BoardConfig(
                        id=board_id,
                        workflow_id=workflow_id,
                        name=f"{workflow_def.name} Board",
                        columns=phases_config.board_config.get('columns', []),
                        ticket_types=phases_config.board_config.get('ticket_types', ['task']),
                        default_ticket_type=phases_config.board_config.get('default_ticket_type', 'task'),
                        initial_status=phases_config.board_config.get('initial_status', 'backlog'),
                        auto_assign=phases_config.board_config.get('auto_assign', False),
                        require_comments_on_status_change=phases_config.board_config.get('require_comments_on_status_change', False),
                        allow_reopen=phases_config.board_config.get('allow_reopen', True),
                        track_time=phases_config.board_config.get('track_time', False),
                        # Human approval settings (with global defaults, can be overridden in board_config)
                        ticket_human_review=phases_config.board_config.get('ticket_human_review', default_human_review),
                        approval_timeout_seconds=phases_config.board_config.get('approval_timeout_seconds', default_approval_timeout),
                    )
                    session.add(board_config)
                    logger.info(f"Created BoardConfig for workflow '{workflow_def.name}' with {len(phases_config.board_config.get('columns', []))} columns")

                session.commit()
                logger.info(f"Created new workflow '{workflow_def.name}' with {len(workflow_def.phases)} phases")

            # Store as active workflow
            self.active_workflow = workflow_def
            self.workflow_id = workflow_id

            return workflow_id

        except Exception as e:
            logger.error(f"Failed to initialize workflow: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def get_phase_for_task(self, phase_id: Optional[str] = None, order: Optional[int] = None,
                          requesting_agent_id: Optional[str] = None) -> Optional[str]:
        """Get phase ID for task creation.

        Args:
            phase_id: Explicit phase ID (for cross-phase task creation)
            order: Phase order number (for cross-phase task creation)
            requesting_agent_id: ID of the agent creating the task

        Returns:
            Phase ID or None if not found
        """
        # If explicit phase_id provided, use it (cross-phase task creation)
        if phase_id:
            return phase_id

        # If phase order provided, find that phase (cross-phase task creation)
        if order is not None and self.workflow_id:
            session = self.db_manager.get_session()
            try:
                phase = session.query(Phase).filter_by(
                    workflow_id=self.workflow_id,
                    order=order
                ).first()
                return phase.id if phase else None
            finally:
                session.close()

        # If agent is creating the task, use the agent's current phase
        if requesting_agent_id and requesting_agent_id != "claude-mcp":
            session = self.db_manager.get_session()
            try:
                # Find the agent's current task and its phase
                from src.core.database import Agent, Task
                agent = session.query(Agent).filter_by(id=requesting_agent_id).first()
                if agent and agent.current_task_id:
                    task = session.query(Task).filter_by(id=agent.current_task_id).first()
                    if task and task.phase_id:
                        return task.phase_id
            finally:
                session.close()

        # Default to first pending/in_progress phase
        return self.get_current_phase_id()

    def get_current_phase_id(self) -> Optional[str]:
        """Get the current active phase ID.

        Returns:
            Phase ID of the current active phase
        """
        if not self.workflow_id:
            return None

        session = self.db_manager.get_session()
        try:
            # Find first non-completed phase
            execution = session.query(PhaseExecution).join(Phase).filter(
                Phase.workflow_id == self.workflow_id,
                PhaseExecution.status.in_(["pending", "in_progress"])
            ).order_by(Phase.order).first()

            return execution.phase_id if execution else None
        finally:
            session.close()

    def get_phase_context(self, phase_id: str) -> Optional[PhaseContext]:
        """Get context for a specific phase.

        Args:
            phase_id: Phase ID

        Returns:
            PhaseContext or None if not found
        """
        logger.info(f"=== GET_PHASE_CONTEXT DEBUG for phase_id: {phase_id} ===")
        logger.info(f"PhaseManager workflow_id: {self.workflow_id}")
        logger.debug(f"PhaseManager active_workflow: {self.active_workflow}")

        session = self.db_manager.get_session()
        try:
            logger.info(f"Querying database for phase with id: {phase_id}")
            phase = session.query(Phase).filter_by(id=phase_id).first()
            logger.info(f"Database query result: {phase}")

            if not phase:
                logger.warning(f"No phase found in database with id: {phase_id}")
                # List all phases for debugging
                all_phases = session.query(Phase).all()
                logger.info(f"All phases in database: {[(p.id, p.name, p.order) for p in all_phases]}")
                return None

            logger.info(f"Found phase: {phase.name} (order: {phase.order}) in workflow: {phase.workflow_id}")

            # Get all phases in workflow
            all_phases = session.query(Phase).filter_by(
                workflow_id=phase.workflow_id
            ).order_by(Phase.order).all()

            # Convert to PhaseDefinition objects
            phase_defs = []
            current_def = None
            for p in all_phases:
                phase_def = PhaseDefinition(
                    filename=f"{p.order:02d}_{p.name.lower().replace(' ', '_')}.yaml",
                    order=p.order,
                    name=p.name,
                    description=p.description,
                    done_definitions=p.done_definitions or [],
                    additional_notes=p.additional_notes,
                    outputs=p.outputs,
                    next_steps=p.next_steps,
                    working_directory=p.working_directory,
                    validation=p.validation,  # Include validation config
                )
                phase_defs.append(phase_def)
                if p.id == phase_id:
                    current_def = phase_def

            if not current_def:
                return None

            # Count tasks
            active_tasks = session.query(Task).filter_by(
                phase_id=phase_id,
            ).filter(
                Task.status.in_(["pending", "assigned", "in_progress"])
            ).count()

            completed_tasks = session.query(Task).filter_by(
                phase_id=phase_id,
                status="done"
            ).count()

            # Get execution status
            execution = session.query(PhaseExecution).filter_by(
                phase_id=phase_id
            ).first()
            status = execution.status if execution else "pending"

            return PhaseContext(
                phase_id=phase_id,
                workflow_id=phase.workflow_id,
                phase_definition=current_def,
                all_phases=phase_defs,
                current_status=status,
                active_tasks=active_tasks,
                completed_tasks=completed_tasks,
            )

        finally:
            session.close()

    def check_phase_completion(self, phase_id: str) -> bool:
        """Check if a phase is complete based on its done_definitions.

        Args:
            phase_id: Phase ID to check

        Returns:
            True if phase is complete
        """
        session = self.db_manager.get_session()
        try:
            phase = session.query(Phase).filter_by(id=phase_id).first()
            if not phase:
                return False

            # Check if all tasks in phase are complete
            incomplete_tasks = session.query(Task).filter_by(
                phase_id=phase_id
            ).filter(
                Task.status.in_(["pending", "assigned", "in_progress", "failed"])
            ).count()

            if incomplete_tasks > 0:
                return False

            # Check if phase has any completed tasks
            completed_tasks = session.query(Task).filter_by(
                phase_id=phase_id,
                status="done"
            ).count()

            # Phase is complete if it has completed tasks and no incomplete ones
            return completed_tasks > 0

        finally:
            session.close()

    def mark_phase_complete(self, phase_id: str, summary: str = "") -> None:
        """Mark a phase as complete.

        Args:
            phase_id: Phase ID to mark complete
            summary: Completion summary
        """
        session = self.db_manager.get_session()
        try:
            execution = session.query(PhaseExecution).filter_by(
                phase_id=phase_id
            ).first()

            if execution:
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                execution.completion_summary = summary
                session.commit()

                logger.info(f"Marked phase {phase_id} as complete")

                # Start next phase if exists
                self._start_next_phase(session, phase_id)

        except Exception as e:
            logger.error(f"Failed to mark phase complete: {e}")
            session.rollback()
        finally:
            session.close()

    def _start_next_phase(self, session, current_phase_id: str) -> None:
        """Start the next phase after current one completes.

        Args:
            session: Database session
            current_phase_id: Current phase ID
        """
        current_phase = session.query(Phase).filter_by(id=current_phase_id).first()
        if not current_phase:
            return

        # Find next phase
        next_phase = session.query(Phase).filter(
            Phase.workflow_id == current_phase.workflow_id,
            Phase.order > current_phase.order
        ).order_by(Phase.order).first()

        if next_phase:
            # Update execution status
            execution = session.query(PhaseExecution).filter_by(
                phase_id=next_phase.id
            ).first()

            if execution and execution.status == "pending":
                execution.status = "in_progress"
                execution.started_at = datetime.utcnow()
                session.commit()

                logger.info(f"Started next phase: {next_phase.name}")

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status.

        Returns:
            Dictionary with workflow status information
        """
        if not self.workflow_id:
            return {"error": "No active workflow"}

        session = self.db_manager.get_session()
        try:
            workflow = session.query(Workflow).filter_by(id=self.workflow_id).first()
            if not workflow:
                return {"error": "Workflow not found"}

            # Get phase statuses
            phases = session.query(Phase).filter_by(
                workflow_id=self.workflow_id
            ).order_by(Phase.order).all()

            phase_statuses = []
            for phase in phases:
                execution = session.query(PhaseExecution).filter_by(
                    phase_id=phase.id
                ).first()

                task_stats = {
                    "total": session.query(Task).filter_by(phase_id=phase.id).count(),
                    "completed": session.query(Task).filter_by(
                        phase_id=phase.id, status="done"
                    ).count(),
                    "active": session.query(Task).filter_by(phase_id=phase.id).filter(
                        Task.status.in_(["assigned", "in_progress"])
                    ).count(),
                    "failed": session.query(Task).filter_by(
                        phase_id=phase.id, status="failed"
                    ).count(),
                }

                phase_statuses.append({
                    "order": phase.order,
                    "name": phase.name,
                    "status": execution.status if execution else "pending",
                    "tasks": task_stats,
                })

            return {
                "workflow_id": self.workflow_id,
                "workflow_name": workflow.name,
                "workflow_status": workflow.status,
                "phases": phase_statuses,
            }

        finally:
            session.close()

    def should_create_next_phase_task(self, phase_id: str) -> bool:
        """Check if we should auto-create a task for the next phase.

        Args:
            phase_id: Current phase ID

        Returns:
            True if next phase task should be created
        """
        if not self.check_phase_completion(phase_id):
            return False

        session = self.db_manager.get_session()
        try:
            current_phase = session.query(Phase).filter_by(id=phase_id).first()
            if not current_phase:
                return False

            # Check if next phase exists
            next_phase = session.query(Phase).filter(
                Phase.workflow_id == current_phase.workflow_id,
                Phase.order > current_phase.order
            ).order_by(Phase.order).first()

            if not next_phase:
                return False

            # Check if next phase already has tasks
            existing_tasks = session.query(Task).filter_by(
                phase_id=next_phase.id
            ).count()

            # Create task if next phase has no tasks
            return existing_tasks == 0

        finally:
            session.close()

    def get_workflow_config(self, workflow_id: str) -> PhasesConfig:
        """Get phases configuration for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            PhasesConfig with loaded configuration or defaults

        Raises:
            ValueError: If workflow not found
        """
        # Check cache first
        if workflow_id in self.phases_config_cache:
            return self.phases_config_cache[workflow_id]

        session = self.db_manager.get_session()
        try:
            workflow = session.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Load configuration from phases folder
            config = PhaseLoader.load_phases_config(workflow.phases_folder_path)

            # Cache the configuration
            self.phases_config_cache[workflow_id] = config

            logger.info(f"Loaded phases config for workflow {workflow_id}: has_result={config.has_result}")
            return config

        finally:
            session.close()

    # ==================== Multi-Workflow Support Methods ====================

    def register_definition(self, definition_id: str, name: str, description: str = "",
                           phases_config: List[Dict[str, Any]] = None,
                           workflow_config: Dict[str, Any] = None) -> str:
        """Register a workflow definition.

        Args:
            definition_id: Unique ID for the definition (e.g., "prd-to-software")
            name: Human-readable name for the workflow
            description: Description of what this workflow does
            phases_config: List of phase definitions (serialized)
            workflow_config: Workflow configuration (has_result, result_criteria, etc.)

        Returns:
            The definition_id
        """
        session = self.db_manager.get_session()
        try:
            # Check if definition already exists
            existing = session.query(DBWorkflowDefinition).filter_by(id=definition_id).first()
            if existing:
                # Update existing definition
                existing.name = name
                existing.description = description
                existing.phases_config = phases_config or []
                existing.workflow_config = workflow_config or {}
                session.commit()
                logger.info(f"Updated workflow definition: {definition_id}")
            else:
                # Create new definition
                db_definition = DBWorkflowDefinition(
                    id=definition_id,
                    name=name,
                    description=description,
                    phases_config=phases_config or [],
                    workflow_config=workflow_config or {},
                )
                session.add(db_definition)
                session.commit()
                logger.info(f"Registered workflow definition: {definition_id}")

            # Cache in memory
            self.definitions[definition_id] = session.query(DBWorkflowDefinition).filter_by(
                id=definition_id
            ).first()

            return definition_id

        except Exception as e:
            logger.error(f"Failed to register workflow definition: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def start_execution(self, definition_id: str, description: str,
                       working_directory: str = None,
                       launch_params: Dict[str, Any] = None) -> str:
        """Start a new workflow execution from a definition.

        Args:
            definition_id: ID of the workflow definition to execute
            description: Description of this specific execution (e.g., "Building URL Shortener")
            working_directory: Working directory for this execution
            launch_params: Parameters from UI launch form to substitute into phases

        Returns:
            workflow_id of the new execution
        """
        session = self.db_manager.get_session()
        try:
            # Get the definition
            db_definition = session.query(DBWorkflowDefinition).filter_by(id=definition_id).first()
            if not db_definition:
                raise ValueError(f"Workflow definition not found: {definition_id}")

            # Generate unique workflow ID
            workflow_id = str(uuid.uuid4())

            # Create workflow execution
            workflow = Workflow(
                id=workflow_id,
                name=db_definition.name,
                description=description,
                definition_id=definition_id,
                phases_folder_path=working_directory or ".",  # Store working dir
                working_directory=working_directory,
                launch_params=launch_params,  # Store launch params for reference
                status="active",
            )
            session.add(workflow)

            # Create phases from definition with parameter substitution
            phases_config = db_definition.phases_config or []
            first_phase_id = None

            for idx, phase_config in enumerate(phases_config):
                phase_id = str(uuid.uuid4())

                # Track first phase for initial task creation
                if idx == 0:
                    first_phase_id = phase_id

                # Helper to serialize lists/dicts as JSON strings for Text columns
                def serialize_for_text(value):
                    if value is None or value == 'null':
                        return None
                    if isinstance(value, (list, dict)):
                        return json.dumps(value)
                    return value

                # Apply parameter substitution if launch_params provided
                phase_description = phase_config.get("description", "")
                phase_additional_notes = phase_config.get("additional_notes")
                phase_done_definitions = phase_config.get("done_definitions", [])
                phase_outputs = phase_config.get("outputs")
                phase_next_steps = phase_config.get("next_steps")

                if launch_params:
                    phase_description = substitute_params(phase_description, launch_params)
                    if phase_additional_notes:
                        phase_additional_notes = substitute_params(phase_additional_notes, launch_params)
                    if phase_done_definitions:
                        phase_done_definitions = substitute_params_in_list(phase_done_definitions, launch_params)
                    if phase_outputs:
                        if isinstance(phase_outputs, list):
                            phase_outputs = substitute_params_in_list(phase_outputs, launch_params)
                        elif isinstance(phase_outputs, str):
                            phase_outputs = substitute_params(phase_outputs, launch_params)
                    if phase_next_steps:
                        if isinstance(phase_next_steps, list):
                            phase_next_steps = substitute_params_in_list(phase_next_steps, launch_params)
                        elif isinstance(phase_next_steps, str):
                            phase_next_steps = substitute_params(phase_next_steps, launch_params)

                phase = Phase(
                    id=phase_id,
                    workflow_id=workflow_id,
                    order=phase_config.get("order", idx + 1),
                    name=phase_config.get("name", f"Phase {idx + 1}"),
                    description=phase_description,
                    done_definitions=phase_done_definitions,
                    additional_notes=serialize_for_text(phase_additional_notes),
                    outputs=serialize_for_text(phase_outputs),
                    next_steps=serialize_for_text(phase_next_steps),
                    working_directory=phase_config.get("working_directory") or working_directory,
                    validation=serialize_for_text(phase_config.get("validation")),
                    # Per-phase CLI configuration (optional - falls back to global defaults)
                    cli_tool=phase_config.get("cli_tool"),
                    cli_model=phase_config.get("cli_model"),
                    glm_api_token_env=phase_config.get("glm_api_token_env"),
                )
                session.add(phase)

                # Create initial execution record
                execution = PhaseExecution(
                    id=str(uuid.uuid4()),
                    phase_id=phase_id,
                    workflow_execution_id=workflow_id,
                    status="pending",
                )
                session.add(execution)

            # Create BoardConfig if ticket tracking is enabled
            workflow_config_data = db_definition.workflow_config or {}
            if workflow_config_data.get("enable_tickets") and workflow_config_data.get("board_config"):
                from src.core.database import BoardConfig

                board_id = f"board-{str(uuid.uuid4())}"
                config = get_config()
                default_human_review = getattr(config, 'default_human_review', False)
                default_approval_timeout = getattr(config, 'default_approval_timeout', 1800)
                board_config_data = workflow_config_data.get("board_config", {})

                board_config = BoardConfig(
                    id=board_id,
                    workflow_id=workflow_id,
                    name=f"{db_definition.name} Board",
                    columns=board_config_data.get('columns', []),
                    ticket_types=board_config_data.get('ticket_types', ['task']),
                    default_ticket_type=board_config_data.get('default_ticket_type', 'task'),
                    initial_status=board_config_data.get('initial_status', 'backlog'),
                    auto_assign=board_config_data.get('auto_assign', False),
                    require_comments_on_status_change=board_config_data.get(
                        'require_comments_on_status_change', False
                    ),
                    allow_reopen=board_config_data.get('allow_reopen', True),
                    track_time=board_config_data.get('track_time', False),
                    ticket_human_review=board_config_data.get(
                        'ticket_human_review', default_human_review
                    ),
                    approval_timeout_seconds=board_config_data.get(
                        'approval_timeout_seconds', default_approval_timeout
                    ),
                )
                session.add(board_config)

            # Prepare initial task info if launch_template has phase_1_task_prompt
            # (actual task creation will be done by the API endpoint using the proper flow)
            initial_task_info = None
            launch_template = workflow_config_data.get("launch_template")
            if launch_template and first_phase_id:
                phase_1_task_prompt = launch_template.get("phase_1_task_prompt")
                if phase_1_task_prompt:
                    # Substitute launch params into the task prompt
                    if launch_params:
                        phase_1_task_prompt = substitute_params(phase_1_task_prompt, launch_params)

                    # Return task info for the API endpoint to create properly
                    initial_task_info = {
                        "task_description": phase_1_task_prompt,
                        "phase_id": "1",  # Phase order, not UUID
                        "priority": "high",
                        "workflow_id": workflow_id,
                    }
                    logger.info(f"Prepared Phase 1 task info for workflow {workflow_id}")

            session.commit()

            # Track active execution
            self.active_executions[workflow_id] = definition_id

            # For backward compatibility, also set as the active workflow
            if not self.workflow_id:
                self.workflow_id = workflow_id

            logger.info(f"Started workflow execution: {workflow_id} (definition: {definition_id})")

            # Return both workflow_id and initial task info
            return workflow_id, initial_task_info

        except Exception as e:
            logger.error(f"Failed to start workflow execution: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a specific workflow execution by ID.

        Args:
            workflow_id: The workflow execution ID

        Returns:
            Workflow object or None if not found
        """
        session = self.db_manager.get_session()
        try:
            workflow = session.query(Workflow).options(
                joinedload(Workflow.definition)
            ).filter_by(id=workflow_id).first()
            if workflow:
                session.expunge(workflow)
            return workflow
        finally:
            session.close()

    def get_definition(self, definition_id: str) -> Optional[DBWorkflowDefinition]:
        """Get a workflow definition by ID.

        Args:
            definition_id: The definition ID

        Returns:
            WorkflowDefinition object or None if not found
        """
        # Check cache first
        if definition_id in self.definitions:
            return self.definitions[definition_id]

        session = self.db_manager.get_session()
        try:
            definition = session.query(DBWorkflowDefinition).filter_by(id=definition_id).first()
            if definition:
                self.definitions[definition_id] = definition
            return definition
        finally:
            session.close()

    def list_definitions(self) -> List[DBWorkflowDefinition]:
        """List all registered workflow definitions.

        Returns:
            List of WorkflowDefinition objects
        """
        session = self.db_manager.get_session()
        try:
            definitions = session.query(DBWorkflowDefinition).all()
            # Expunge objects so they can be accessed after session closes
            for defn in definitions:
                session.expunge(defn)
                self.definitions[defn.id] = defn
            return definitions
        finally:
            session.close()

    def list_active_executions(self, status: str = "all") -> List[Workflow]:
        """List all active workflow executions.

        Args:
            status: Filter by status ("all", "active", "completed", "paused", "failed")

        Returns:
            List of Workflow execution objects
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(Workflow).options(joinedload(Workflow.definition))
            if status != "all":
                query = query.filter_by(status=status)
            else:
                # Default to showing active workflows
                query = query.filter(Workflow.status.in_(["active", "paused"]))

            workflows = query.order_by(Workflow.created_at.desc()).all()
            # Expunge from session to allow access after session closes
            for w in workflows:
                session.expunge(w)
            return workflows
        finally:
            session.close()

    def get_phases_for_workflow(self, workflow_id: str) -> List[Phase]:
        """Get phases for a specific workflow execution.

        Args:
            workflow_id: The workflow execution ID

        Returns:
            List of Phase objects ordered by phase order
        """
        session = self.db_manager.get_session()
        try:
            return session.query(Phase).filter_by(
                workflow_id=workflow_id
            ).order_by(Phase.order).all()
        finally:
            session.close()

    def get_execution_stats(self, workflow_id: str) -> Dict[str, int]:
        """Get task statistics for a workflow execution.

        Args:
            workflow_id: The workflow execution ID

        Returns:
            Dictionary with task counts (active_tasks, total_tasks, done_tasks, failed_tasks)
        """
        session = self.db_manager.get_session()
        try:
            total = session.query(Task).filter_by(workflow_id=workflow_id).count()
            done = session.query(Task).filter_by(workflow_id=workflow_id, status="done").count()
            failed = session.query(Task).filter_by(workflow_id=workflow_id, status="failed").count()
            active = session.query(Task).filter(
                Task.workflow_id == workflow_id,
                Task.status.in_(["pending", "assigned", "in_progress"])
            ).count()

            return {
                "total_tasks": total,
                "done_tasks": done,
                "failed_tasks": failed,
                "active_tasks": active,
            }
        finally:
            session.close()

    def get_active_agents_count(self, workflow_id: str) -> int:
        """Get count of active agents for a workflow.

        Args:
            workflow_id: The workflow execution ID

        Returns:
            Number of active agents
        """
        from src.core.database import Agent
        session = self.db_manager.get_session()
        try:
            # Count agents working on tasks in this workflow
            return session.query(Agent).join(
                Task, Agent.current_task_id == Task.id
            ).filter(
                Task.workflow_id == workflow_id,
                Agent.status.in_(["working", "idle"])
            ).count()
        finally:
            session.close()

    def load_active_executions(self) -> None:
        """Load all active workflow executions into memory.

        Called on startup to restore state.
        """
        session = self.db_manager.get_session()
        try:
            # Load all active workflows
            workflows = session.query(Workflow).filter(
                Workflow.status.in_(["active", "paused"])
            ).all()

            for workflow in workflows:
                if workflow.definition_id:
                    self.active_executions[workflow.id] = workflow.definition_id

            # Load all definitions
            definitions = session.query(DBWorkflowDefinition).all()
            for defn in definitions:
                self.definitions[defn.id] = defn

            logger.info(f"Loaded {len(self.active_executions)} active workflow executions")
            logger.info(f"Loaded {len(self.definitions)} workflow definitions")

        finally:
            session.close()