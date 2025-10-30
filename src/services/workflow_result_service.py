"""Service layer for managing workflow-level results."""

import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.core.database import get_db, WorkflowResult, Workflow, Agent
from src.services.validation_helpers import (
    validate_file_path,
    validate_file_size,
    validate_markdown_format,
)


class WorkflowResultService:
    """Service for managing workflow-level results."""

    @staticmethod
    def submit_result(
        agent_id: str,
        workflow_id: str,
        markdown_file_path: str,
        explanation: str = "",
        evidence: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a workflow result for validation.

        Args:
            agent_id: ID of the agent submitting the result
            workflow_id: ID of the workflow this result belongs to
            markdown_file_path: Path to the markdown file containing the result
            explanation: Brief explanation of what was accomplished
            evidence: List of evidence supporting completion

        Returns:
            Dictionary containing result details and status

        Raises:
            ValueError: If validation fails or workflow not found
            FileNotFoundError: If markdown file doesn't exist
        """
        # Validate file path (prevent directory traversal)
        validate_file_path(markdown_file_path)

        # Check file exists
        if not os.path.exists(markdown_file_path):
            raise FileNotFoundError(f"Markdown file not found: {markdown_file_path}")

        # Validate file size (1MB limit for workflow results)
        validate_file_size(markdown_file_path, max_size_kb=1024)

        # Validate markdown format
        validate_markdown_format(markdown_file_path)

        # Read markdown content
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        with get_db() as db:
            # Validate workflow exists
            workflow = db.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Validate agent exists
            agent = db.query(Agent).filter_by(id=agent_id).first()
            if not agent:
                raise ValueError(f"Agent not found: {agent_id}")

            # Check if workflow already has a validated result
            existing_result = db.query(WorkflowResult).filter_by(
                workflow_id=workflow_id,
                status="validated"
            ).first()

            if existing_result:
                return {
                    "status": "rejected",
                    "message": "Workflow already has a validated result",
                    "existing_result_id": existing_result.id,
                }

            # Create result
            result_id = f"result-{uuid.uuid4()}"
            result = WorkflowResult(
                id=result_id,
                workflow_id=workflow_id,
                agent_id=agent_id,
                result_file_path=markdown_file_path,
                result_content=markdown_content,
                status="pending_validation",
                created_at=datetime.utcnow(),
            )

            db.add(result)
            db.commit()

            return {
                "status": "submitted",
                "result_id": result_id,
                "workflow_id": workflow_id,
                "agent_id": agent_id,
                "validation_status": "pending_validation",
                "created_at": result.created_at.isoformat(),
            }

    @staticmethod
    def get_workflow_results(workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get all results for a specific workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            List of result dictionaries
        """
        with get_db() as db:
            results = db.query(WorkflowResult).filter_by(workflow_id=workflow_id).all()

            return [
                {
                    "result_id": result.id,
                    "agent_id": result.agent_id,
                    "workflow_id": result.workflow_id,
                    "status": result.status,
                    "validation_feedback": result.validation_feedback,
                    "created_at": result.created_at.isoformat(),
                    "validated_at": result.validated_at.isoformat() if result.validated_at else None,
                    "validated_by_agent_id": result.validated_by_agent_id,
                    "result_file_path": result.result_file_path,
                }
                for result in results
            ]

    @staticmethod
    def update_result_status(
        result_id: str,
        status: str,
        feedback: str = "",
        evidence: Optional[Dict[str, Any]] = None,
        validator_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update the validation status of a result.

        Args:
            result_id: ID of the result to update
            status: New status (validated, rejected)
            feedback: Validation feedback
            evidence: Validation evidence
            validator_agent_id: ID of the validator agent

        Returns:
            Updated result information

        Raises:
            ValueError: If result not found or invalid status
        """
        if status not in ["validated", "rejected"]:
            raise ValueError(f"Invalid status: {status}. Must be 'validated' or 'rejected'")

        with get_db() as db:
            result = db.query(WorkflowResult).filter_by(id=result_id).first()

            if not result:
                raise ValueError(f"Result not found: {result_id}")

            # Update result
            result.status = status
            result.validation_feedback = feedback
            result.validation_evidence = evidence
            result.validated_at = datetime.utcnow()
            if validator_agent_id:
                result.validated_by_agent_id = validator_agent_id

            # Update workflow if result is validated
            if status == "validated":
                workflow = db.query(Workflow).filter_by(id=result.workflow_id).first()
                if workflow:
                    workflow.result_found = True
                    workflow.result_id = result_id

            db.commit()

            return {
                "result_id": result.id,
                "status": result.status,
                "validation_feedback": result.validation_feedback,
                "validated_at": result.validated_at.isoformat(),
                "validated_by": validator_agent_id,
            }

    @staticmethod
    def get_result_content(result_id: str) -> Optional[str]:
        """
        Get the markdown content of a specific result.

        Args:
            result_id: ID of the result

        Returns:
            Markdown content or None if not found
        """
        with get_db() as db:
            result = db.query(WorkflowResult).filter_by(id=result_id).first()
            return result.result_content if result else None

    @staticmethod
    def check_workflow_completion(workflow_id: str) -> bool:
        """
        Check if a workflow has been completed by a validated result.

        Args:
            workflow_id: ID of the workflow

        Returns:
            True if workflow has a validated result
        """
        with get_db() as db:
            workflow = db.query(Workflow).filter_by(id=workflow_id).first()
            return workflow.result_found if workflow else False

    @staticmethod
    def get_validated_result_for_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the validated result for a workflow if it exists.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Validated result dictionary or None
        """
        with get_db() as db:
            result = db.query(WorkflowResult).filter_by(
                workflow_id=workflow_id,
                status="validated"
            ).first()

            if not result:
                return None

            return {
                "result_id": result.id,
                "agent_id": result.agent_id,
                "workflow_id": result.workflow_id,
                "status": result.status,
                "validation_feedback": result.validation_feedback,
                "validation_evidence": result.validation_evidence,
                "created_at": result.created_at.isoformat(),
                "validated_at": result.validated_at.isoformat(),
                "validated_by_agent_id": result.validated_by_agent_id,
                "result_file_path": result.result_file_path,
                "result_content": result.result_content,
            }