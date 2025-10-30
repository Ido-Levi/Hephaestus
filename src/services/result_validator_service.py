"""Service for spawning and managing result validator agents."""

import uuid
import logging
from typing import Dict, Any, Optional

from src.core.database import DatabaseManager, WorkflowResult, Workflow, Agent, Task
from src.services.result_validation_helpers import (
    validate_result_criteria,
    validate_file_contains_solution,
    ValidationResult,
)
from src.phases.phase_manager import PhaseManager

logger = logging.getLogger(__name__)


class ResultValidatorService:
    """Service for validating workflow results."""

    def __init__(self, db_manager: DatabaseManager, phase_manager: PhaseManager):
        """Initialize the result validator service.

        Args:
            db_manager: Database manager instance
            phase_manager: Phase manager for accessing workflow configuration
        """
        self.db_manager = db_manager
        self.phase_manager = phase_manager

    def validate_result_against_criteria(
        self,
        result_content: str,
        criteria: str
    ) -> ValidationResult:
        """
        Validate result content against criteria.

        Args:
            result_content: Markdown content of the result
            criteria: Validation criteria from workflow configuration

        Returns:
            ValidationResult with validation outcome
        """
        return validate_result_criteria(result_content, criteria)

    def should_spawn_validator(self, workflow_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if a validator should be spawned for the workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Tuple of (should_spawn, criteria) where criteria is None if no validation needed
        """
        try:
            config = self.phase_manager.get_workflow_config(workflow_id)

            if not config.has_result:
                logger.info(f"Workflow {workflow_id} does not expect results")
                return False, None

            if not config.result_criteria:
                logger.info(f"Workflow {workflow_id} has no validation criteria")
                return False, None

            logger.info(f"Workflow {workflow_id} requires validation with criteria")
            return True, config.result_criteria

        except Exception as e:
            logger.error(f"Error checking workflow config: {e}")
            return False, None

    async def spawn_result_validator(
        self,
        result_id: str,
        workflow_id: str,
        criteria: str
    ) -> str:
        """
        Spawn a result validator agent for a submitted result.

        Args:
            result_id: ID of the result to validate
            workflow_id: ID of the workflow
            criteria: Validation criteria

        Returns:
            ID of the spawned validator agent

        Raises:
            ValueError: If result or workflow not found
        """
        session = self.db_manager.get_session()

        try:
            # Get the result and workflow
            result = session.query(WorkflowResult).filter_by(id=result_id).first()
            if not result:
                raise ValueError(f"Result not found: {result_id}")

            workflow = session.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Create validator agent ID
            validator_agent_id = f"result-validator-{uuid.uuid4().hex[:8]}"

            # Build validator prompt
            from src.validation.result_prompt_builder import build_result_validator_prompt
            validator_prompt = build_result_validator_prompt(
                result=result,
                workflow=workflow,
                criteria=criteria,
                validator_agent_id=validator_agent_id
            )

            # Find the original task assigned to the agent that submitted the result
            # Be explicit about the join to avoid ambiguity
            original_task = session.query(Task).filter(Task.assigned_agent_id == result.agent_id).first()

            # Create validation task
            validation_task_id = str(uuid.uuid4())
            validation_task = Task(
                id=validation_task_id,
                raw_description=f"Validate result submission for task: {original_task.raw_description if original_task else 'Unknown'}",
                enriched_description=f"Validate the result submitted by agent {result.agent_id} for workflow {workflow_id}",
                done_definition=f"Review and validate the submitted result against workflow criteria, then submit validation using submit_result_validation tool",
                status="assigned",
                priority="high",
                assigned_agent_id=validator_agent_id,
                parent_task_id=original_task.id if original_task else None,
                phase_id=original_task.phase_id if original_task else None,
                workflow_id=workflow_id,
                validation_enabled=False  # Validators don't need validation themselves
            )
            session.add(validation_task)

            # Create validator agent in database
            validator_agent = Agent(
                id=validator_agent_id,
                agent_type="result_validator",
                system_prompt=validator_prompt,
                cli_type="claude",  # Use Claude for result validation
                status="working",
                tmux_session_name=f"agent_{validator_agent_id}"
            )
            session.add(validator_agent)
            session.commit()

            # Get working directory (read-only access to workflow)
            working_directory = workflow.phases_folder_path

            # Spawn tmux session for validator
            from src.validation.result_validator_agent import spawn_result_validator_tmux_session
            await spawn_result_validator_tmux_session(
                agent_id=validator_agent_id,
                working_directory=working_directory,
                prompt=validator_prompt,
                result_file_path=result.result_file_path,
                read_only=True
            )

            logger.info(f"Spawned result validator agent {validator_agent_id} for result {result_id}")
            return validator_agent_id

        except Exception as e:
            logger.error(f"Failed to spawn result validator: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def process_validation_outcome(
        self,
        result_id: str,
        passed: bool,
        feedback: str,
        evidence: Optional[Dict[str, Any]] = None,
        validator_agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process the outcome of result validation.

        Args:
            result_id: ID of the result that was validated
            passed: Whether validation passed
            feedback: Validation feedback
            evidence: Validation evidence
            validator_agent_id: ID of the validator agent

        Returns:
            Dictionary with processing outcome and next actions

        Raises:
            ValueError: If result not found
        """
        session = self.db_manager.get_session()

        try:
            result = session.query(WorkflowResult).filter_by(id=result_id).first()
            if not result:
                raise ValueError(f"Result not found: {result_id}")

            # Update result status
            from src.services.workflow_result_service import WorkflowResultService
            result_info = WorkflowResultService.update_result_status(
                result_id=result_id,
                status="validated" if passed else "rejected",
                feedback=feedback,
                evidence=evidence,
                validator_agent_id=validator_agent_id
            )

            # If validation passed, check workflow termination action
            next_actions = []
            if passed:
                try:
                    config = self.phase_manager.get_workflow_config(result.workflow_id)

                    if config.on_result_found == "stop_all":
                        next_actions.append("terminate_workflow")
                        logger.info(f"Workflow {result.workflow_id} will be terminated due to validated result")
                    elif config.on_result_found == "do_nothing":
                        next_actions.append("continue_workflow")
                        logger.info(f"Workflow {result.workflow_id} will continue after validated result")

                except Exception as e:
                    logger.error(f"Error checking workflow termination action: {e}")
                    next_actions.append("continue_workflow")  # Default to continue

            return {
                "result_validation": result_info,
                "validation_passed": passed,
                "next_actions": next_actions,
                "workflow_id": result.workflow_id,
            }

        finally:
            session.close()

    def get_validation_status(self, result_id: str) -> Dict[str, Any]:
        """
        Get the current validation status of a result.

        Args:
            result_id: ID of the result

        Returns:
            Dictionary with validation status information
        """
        session = self.db_manager.get_session()

        try:
            result = session.query(WorkflowResult).filter_by(id=result_id).first()
            if not result:
                return {"error": "Result not found"}

            return {
                "result_id": result.id,
                "status": result.status,
                "validation_feedback": result.validation_feedback,
                "validation_evidence": result.validation_evidence,
                "validated_at": result.validated_at.isoformat() if result.validated_at else None,
                "validated_by_agent_id": result.validated_by_agent_id,
            }

        finally:
            session.close()