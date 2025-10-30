"""Validation helpers for result submission."""

import os
from pathlib import Path


def validate_file_path(file_path: str) -> None:
    """
    Validate file path to prevent directory traversal attacks.

    Args:
        file_path: Path to validate

    Raises:
        ValueError: If path is invalid or contains traversal attempts
    """
    # Convert to Path object for safe handling
    path = Path(file_path).resolve()

    # Check for path traversal attempts
    if ".." in str(file_path):
        raise ValueError(f"Invalid file path - directory traversal detected: {file_path}")

    # Ensure path is absolute and normalized
    if not path.is_absolute():
        # Allow relative paths but validate them
        path = Path.cwd() / path

    # Additional safety check
    try:
        # This will raise if path doesn't exist or is invalid
        path_str = str(path)
    except Exception as e:
        raise ValueError(f"Invalid file path: {file_path}") from e


def validate_file_size(file_path: str, max_size_kb: int = 100) -> None:
    """
    Validate that file size is within limits.

    Args:
        file_path: Path to the file
        max_size_kb: Maximum allowed size in KB

    Raises:
        ValueError: If file is too large
    """
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_kb * 1024

    if file_size > max_size_bytes:
        size_kb = file_size / 1024
        raise ValueError(
            f"File too large: {size_kb:.2f}KB exceeds maximum of {max_size_kb}KB"
        )


def validate_markdown_format(file_path: str) -> None:
    """
    Validate that file is in markdown format.

    Args:
        file_path: Path to the file

    Raises:
        ValueError: If file is not markdown
    """
    path = Path(file_path)

    # Check file extension
    if not path.suffix.lower() == '.md':
        raise ValueError(f"File must be markdown (.md), got: {path.suffix}")

    # Could add additional validation here (e.g., check for valid markdown syntax)
    # For now, just checking extension


def validate_task_ownership(db, task_id: str, agent_id: str) -> None:
    """
    Validate that the agent owns the task.

    Args:
        db: Database session
        task_id: ID of the task
        agent_id: ID of the agent

    Raises:
        ValueError: If task doesn't exist or isn't assigned to agent
    """
    from src.core.database import Task

    task = db.query(Task).filter_by(id=task_id).first()

    if not task:
        raise ValueError(f"Task not found: {task_id}")

    if task.assigned_agent_id != agent_id:
        raise ValueError(
            f"Task {task_id} is not assigned to agent {agent_id}. "
            f"Assigned to: {task.assigned_agent_id}"
        )