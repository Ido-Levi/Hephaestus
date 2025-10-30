"""Service layer for managing agent results."""

import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.core.database import get_db, AgentResult, Task, Agent
from src.services.validation_helpers import (
    validate_file_path,
    validate_file_size,
    validate_markdown_format,
    validate_task_ownership,
)


class ResultService:
    """Service for managing agent results."""

    @staticmethod
    def create_result(
        agent_id: str,
        task_id: str,
        markdown_file_path: str,
        result_type: str,
        summary: str,
    ) -> Dict[str, Any]:
        """
        Create a new result for a task.

        Args:
            agent_id: ID of the agent submitting the result
            task_id: ID of the task the result is for
            markdown_file_path: Path to the markdown file containing the result
            result_type: Type of result (implementation, analysis, fix, etc.)
            summary: Brief summary of the result

        Returns:
            Dictionary containing result details and status

        Raises:
            ValueError: If validation fails
            FileNotFoundError: If markdown file doesn't exist
        """
        # Validate file path (prevent directory traversal)
        validate_file_path(markdown_file_path)

        # Check file exists
        if not os.path.exists(markdown_file_path):
            raise FileNotFoundError(f"Markdown file not found: {markdown_file_path}")

        # Validate file size (100KB limit)
        validate_file_size(markdown_file_path, max_size_kb=100)

        # Validate markdown format
        validate_markdown_format(markdown_file_path)

        # Read markdown content
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        with get_db() as db:
            # Validate task ownership
            validate_task_ownership(db, task_id, agent_id)

            # Create result
            result_id = f"result-{uuid.uuid4()}"
            result = AgentResult(
                id=result_id,
                agent_id=agent_id,
                task_id=task_id,
                markdown_content=markdown_content,
                markdown_file_path=markdown_file_path,
                result_type=result_type,
                summary=summary,
                verification_status="unverified",
                created_at=datetime.utcnow(),
            )

            db.add(result)

            # Update task to indicate it has results
            task = db.query(Task).filter_by(id=task_id).first()
            if task:
                task.has_results = True

            db.commit()

            return {
                "status": "stored",
                "result_id": result_id,
                "task_id": task_id,
                "agent_id": agent_id,
                "verification_status": "unverified",
                "created_at": result.created_at.isoformat(),
            }

    @staticmethod
    def get_results_for_task(task_id: str) -> List[Dict[str, Any]]:
        """
        Get all results for a specific task.

        Args:
            task_id: ID of the task

        Returns:
            List of result dictionaries
        """
        with get_db() as db:
            results = db.query(AgentResult).filter_by(task_id=task_id).all()

            return [
                {
                    "result_id": result.id,
                    "agent_id": result.agent_id,
                    "task_id": result.task_id,
                    "result_type": result.result_type,
                    "summary": result.summary,
                    "verification_status": result.verification_status,
                    "created_at": result.created_at.isoformat(),
                    "verified_at": result.verified_at.isoformat() if result.verified_at else None,
                    "markdown_file_path": result.markdown_file_path,
                }
                for result in results
            ]

    @staticmethod
    def get_results_for_agent(agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all results submitted by a specific agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of result dictionaries
        """
        with get_db() as db:
            results = db.query(AgentResult).filter_by(agent_id=agent_id).all()

            return [
                {
                    "result_id": result.id,
                    "agent_id": result.agent_id,
                    "task_id": result.task_id,
                    "result_type": result.result_type,
                    "summary": result.summary,
                    "verification_status": result.verification_status,
                    "created_at": result.created_at.isoformat(),
                    "verified_at": result.verified_at.isoformat() if result.verified_at else None,
                }
                for result in results
            ]

    @staticmethod
    def verify_result(
        result_id: str,
        validation_review_id: str,
        verified: bool = True,
    ) -> Dict[str, Any]:
        """
        Update the verification status of a result.

        Args:
            result_id: ID of the result to verify
            validation_review_id: ID of the validation review that verified this
            verified: Whether the result is verified or disputed

        Returns:
            Updated result information
        """
        with get_db() as db:
            result = db.query(AgentResult).filter_by(id=result_id).first()

            if not result:
                raise ValueError(f"Result not found: {result_id}")

            result.verification_status = "verified" if verified else "disputed"
            result.verified_at = datetime.utcnow()
            result.verified_by_validation_id = validation_review_id

            db.commit()

            return {
                "result_id": result.id,
                "verification_status": result.verification_status,
                "verified_at": result.verified_at.isoformat(),
                "verified_by": validation_review_id,
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
            result = db.query(AgentResult).filter_by(id=result_id).first()
            return result.markdown_content if result else None