"""Validator agent spawning and management."""

import uuid
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from src.core.database import (
    DatabaseManager,
    Agent,
    Task,
    Phase,
    ValidationReview,
    WorktreeCommit,
    AgentWorktree
)
from src.core.worktree_manager import WorktreeManager
from src.validation.prompt_builder import ValidationPromptBuilder
from src.agents.manager import AgentManager

logger = logging.getLogger(__name__)


def build_validator_prompt(
    task: Task,
    phase: Phase,
    commit_sha: str,
    workspace_changes: Dict[str, Any],
    agent_claims: str,
    iteration: int,
    validator_agent_id: str
) -> str:
    """Build a prompt for the validator agent.

    Args:
        task: Task being validated
        phase: Phase configuration
        commit_sha: Commit to validate
        workspace_changes: Changes made by agent
        agent_claims: Agent's result claims
        iteration: Validation iteration number
        validator_agent_id: ID of the validator agent

    Returns:
        Complete validator prompt
    """
    builder = ValidationPromptBuilder()

    # Convert task to dict for prompt builder
    task_dict = {
        "id": task.id,
        "raw_description": task.raw_description,
        "enriched_description": task.enriched_description,
        "done_definition": task.done_definition
    }

    # Get phase validation config
    phase_validation = phase.validation if phase else None

    # Get previous feedback if this is not the first iteration
    previous_feedback = task.last_validation_feedback if iteration > 1 else None

    return builder.build_prompt(
        task=task_dict,
        phase_validation=phase_validation,
        commit_sha=commit_sha,
        workspace_changes=workspace_changes,
        agent_claims=agent_claims,
        iteration=iteration,
        previous_feedback=previous_feedback,
        validator_agent_id=validator_agent_id
    )


async def spawn_validator_agent(
    validation_type: str,
    target_id: str,
    workflow_id: str,
    commit_sha: str,
    db_manager: DatabaseManager,
    worktree_manager: WorktreeManager,
    agent_manager: AgentManager,
    original_agent_id: str,
    criteria: str = None
) -> str:
    """Spawn a validator agent for either task or result validation.

    Args:
        validation_type: "task" or "result"
        target_id: ID of task or result to validate
        workflow_id: ID of the workflow
        commit_sha: Commit SHA to validate
        db_manager: Database manager
        worktree_manager: Worktree manager
        agent_manager: Agent manager
        original_agent_id: ID of the agent that created the task/result
        criteria: Validation criteria (for result validation)

    Returns:
        ID of spawned validator agent
    """
    logger.info(f"Spawning {validation_type} validator agent for {target_id}")

    session = db_manager.get_session()
    try:
        # Create validator agent ID first (needed for prompt)
        validator_agent_id = f"{validation_type}-validator-{uuid.uuid4().hex[:8]}"

        # Build validator prompt based on type
        if validation_type == "task":
            # Get task and phase for task validation
            task = session.query(Task).filter_by(id=target_id).first()
            if not task:
                raise ValueError(f"Task {target_id} not found")

            phase = None
            if task.phase_id:
                phase = session.query(Phase).filter_by(id=task.phase_id).first()

            # Get workspace changes
            workspace_changes = worktree_manager.get_workspace_changes(
                agent_id=original_agent_id,
                since_commit=None  # Get all changes
            )

            # Get agent claims/results
            agent_claims = get_agent_results(target_id, session)

            # Build task validation prompt using the new prompt loader
            from src.monitoring.prompt_loader import prompt_loader

            # Get previous feedback if any
            previous_feedback = getattr(task, 'last_validation_feedback', None)

            validator_prompt = prompt_loader.format_task_validation_prompt(
                validator_agent_id=validator_agent_id,
                task_id=target_id,
                task_description=task.raw_description,
                done_definition=task.done_definition,
                enriched_description=task.enriched_description or task.raw_description,
                original_agent_id=original_agent_id,
                iteration=task.validation_iteration,
                working_directory=worktree_manager.get_agent_worktree_path(original_agent_id) or "/tmp",
                commit_sha=commit_sha,
                previous_feedback=previous_feedback
            )

            # Create validation task for task validator
            validation_task_id = str(uuid.uuid4())
            validation_task = Task(
                id=validation_task_id,
                raw_description=f"Validate task completion: {task.raw_description}",
                enriched_description=f"Validate the work completed by agent {original_agent_id} for task {target_id}",
                done_definition="Review task completion and provide validation feedback using give_validation_review",
                status="assigned",
                priority="high",
                assigned_agent_id=validator_agent_id,
                parent_task_id=target_id,
                phase_id=task.phase_id,
                workflow_id=workflow_id,
                validation_enabled=False
            )
            session.add(validation_task)

        elif validation_type == "result":
            # Get result and workflow for result validation
            from src.core.database import WorkflowResult, Workflow
            result = session.query(WorkflowResult).filter_by(id=target_id).first()
            if not result:
                raise ValueError(f"Result {target_id} not found")

            workflow = session.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Build result validation prompt using the new prompt loader
            from src.monitoring.prompt_loader import prompt_loader

            validator_prompt = prompt_loader.format_result_validation_prompt(
                validator_agent_id=validator_agent_id,
                result_id=result.id,
                result_file_path=result.result_file_path,
                workflow_name=workflow.name,
                workflow_id=workflow_id,
                validation_criteria=criteria,
                submitted_by_agent=original_agent_id,
                submitted_at=result.created_at.isoformat()
            )

            # Create validation task for result validator
            validation_task_id = str(uuid.uuid4())
            validation_task = Task(
                id=validation_task_id,
                raw_description=f"Validate result submission for workflow: {workflow.name}",
                enriched_description=f"Validate the result submitted by agent {original_agent_id} for workflow {workflow_id}",
                done_definition="Review and validate the submitted result against workflow criteria using submit_result_validation",
                status="assigned",
                priority="high",
                assigned_agent_id=validator_agent_id,
                workflow_id=workflow_id,
                validation_enabled=False
            )
            session.add(validation_task)

        else:
            raise ValueError(f"Invalid validation_type: {validation_type}")

        # For result validators, we need the commit SHA to create worktree from
        # The commit_sha parameter should have been passed from submit_result

        # Use AgentManager to create agent properly (like normal agents)
        # Pass commit_sha to create worktree from the specific commit
        validator_agent_obj = await agent_manager.create_agent_for_task(
            task=validation_task,
            enriched_data={
                "type": f"{validation_type}_validation",
                "target_id": target_id,
                "validation_prompt": validator_prompt  # Pass the formatted prompt
            },
            memories=[],  # Validators don't need memories
            project_context="",  # Validators have read-only access
            cli_type="claude",
            working_directory=None,  # Will be created from commit
            agent_type="result_validator" if validation_type == "result" else "validator",
            use_existing_worktree=False,  # Create new worktree from commit
            commit_sha=commit_sha  # Create worktree from this commit
        )

        logger.info(f"Spawned {validation_type} validator agent {validator_agent_id} for {target_id}")
        return validator_agent_id

    except Exception as e:
        logger.error(f"Failed to spawn {validation_type} validator agent: {e}")
        session.rollback()
        raise
    finally:
        session.close()


async def spawn_validator_tmux_session(
    agent_id: str,
    working_directory: str,
    prompt: str,
    read_only: bool = True
) -> None:
    """Spawn a tmux session for validator agent.

    Args:
        agent_id: Validator agent ID
        working_directory: Working directory for agent
        prompt: Agent prompt
        read_only: Whether agent has read-only access
    """
    import subprocess
    import libtmux
    from src.interfaces.cli_interface import get_cli_agent

    session_name = f"agent_{agent_id}"

    try:
        # Use libtmux to create and manage the session
        tmux_server = libtmux.Server()

        # Kill existing session if it exists
        if tmux_server.has_session(session_name):
            existing = tmux_server.get_by_id(session_name)
            if existing:
                existing.kill_session()

        # Create new tmux session
        tmux_session = tmux_server.new_session(
            session_name=session_name,
            window_name="validator",
            start_directory=working_directory
        )

        # Get the pane
        pane = tmux_session.attached_window.attached_pane

        # If read-only, show indicator (optional)
        if read_only:
            pane.send_keys("echo 'READ-ONLY MODE: Validator agent starting...'", enter=True)
            await asyncio.sleep(1)

        # Get CLI agent (use 'claude' for validators)
        cli_agent = get_cli_agent("claude")

        # Generate launch command with minimal system prompt (like normal agents)
        launch_command = cli_agent.get_launch_command(
            system_prompt="You are a validation agent for the Hephaestus system.",
            task_id=agent_id
        )

        # Launch Claude Code
        pane.send_keys(launch_command, enter=True)

        logger.info(f"Launched Claude Code for validator agent {agent_id}")

        # Wait for Claude to initialize (same as normal agents)
        await asyncio.sleep(8)

        # Send the validation prompt as an initial message
        formatted_message = cli_agent.format_message(prompt)
        pane.send_keys(formatted_message)

        # Wait a moment then send Enter to submit the message
        await asyncio.sleep(1)
        pane.send_keys('', enter=True)  # Send Enter to submit

        logger.info(f"Sent validation prompt to validator agent {agent_id}")
        logger.debug(f"Validator prompt preview:\n{prompt[:500]}...")

    except Exception as e:
        logger.error(f"Failed to create validator tmux session: {e}")
        raise


def get_agent_results(task_id: str, session: Session) -> str:
    """Get results/claims from the agent working on the task.

    Args:
        task_id: Task ID
        session: Database session

    Returns:
        Agent results as string
    """
    task = session.query(Task).filter_by(id=task_id).first()
    if not task:
        return "No task found"

    # Get completion notes or other results
    results = []

    if task.completion_notes:
        results.append(f"Completion Notes: {task.completion_notes}")

    if task.enriched_description:
        results.append(f"Task Description: {task.enriched_description}")

    if task.done_definition:
        results.append(f"Done Definition: {task.done_definition}")

    # Could also fetch from agent logs or other sources
    # For now, return what we have
    if results:
        return "\n\n".join(results)
    else:
        return "Agent has not provided specific results yet"


def send_feedback_to_agent(
    agent_id: str,
    feedback: str,
    iteration: int
) -> bool:
    """Send validation feedback to a running agent via tmux.

    Args:
        agent_id: Agent ID
        feedback: Feedback message
        iteration: Validation iteration number

    Returns:
        True if feedback sent successfully
    """
    import subprocess
    import tempfile

    session_name = f"agent_{agent_id}"

    try:
        # Create feedback file
        feedback_content = f"""
VALIDATION FEEDBACK (Iteration {iteration}):
=====================================
{feedback}
=====================================

Please address the issues above and try again.
When ready, you can claim completion again.
"""

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(feedback_content)
            feedback_file = f.name

        # Send to tmux pane
        cmd = f"cat {feedback_file}"
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, cmd, "Enter"],
            check=True
        )

        logger.info(f"Sent feedback to agent {agent_id}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to send feedback to agent: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending feedback: {e}")
        return False