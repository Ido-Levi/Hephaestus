"""Result validator agent spawning and management."""

import asyncio
import logging
from typing import Optional
import libtmux

from src.interfaces import get_cli_agent

logger = logging.getLogger(__name__)


async def spawn_result_validator_tmux_session(
    agent_id: str,
    working_directory: str,
    prompt: str,
    result_file_path: str,
    read_only: bool = True
) -> None:
    """Spawn a tmux session for result validator agent.

    Args:
        agent_id: Result validator agent ID
        working_directory: Working directory for agent (workflow folder)
        prompt: Agent prompt with validation instructions
        result_file_path: Path to the result file to validate
        read_only: Whether agent has read-only access (should be True)
    """
    try:
        # Connect to tmux server
        server = libtmux.Server()

        # Create new session for the validator
        session_name = f"agent_{agent_id}"
        logger.info(f"Creating tmux session: {session_name}")

        session = server.new_session(
            session_name=session_name,
            start_directory=working_directory,
            attach=False
        )

        # Get the default pane
        panes = list(session.panes)
        if not panes:
            raise ValueError("No panes found in tmux session")
        pane = panes[0]  # Get the first (default) pane

        # Set up read-only environment
        if read_only:
            pane.send_keys("echo 'READ-ONLY MODE: Result validator starting...'", enter=True)
            pane.send_keys(f"echo 'Validating result file: {result_file_path}'", enter=True)
            await asyncio.sleep(1)

        # Get CLI agent command (use 'claude' for result validators)
        cli_agent = get_cli_agent("claude")
        if not cli_agent:
            raise ValueError("Claude CLI agent not available for result validation")

        # Start Claude Code in the session
        claude_command = cli_agent.get_launch_command()
        logger.info(f"Starting Claude Code with command: {claude_command}")
        pane.send_keys(claude_command, enter=True)

        logger.info(f"Launched Claude Code for result validator agent {agent_id}")

        # Wait for Claude to initialize
        await asyncio.sleep(8)

        # Send the validation prompt
        lines = prompt.split('\n')
        for line in lines:
            if line.strip():  # Skip empty lines
                pane.send_keys(line, enter=False)
                await asyncio.sleep(0.1)

        # Send final enter to submit the prompt
        pane.send_keys("", enter=True)
        await asyncio.sleep(2)

        logger.info(f"Sent validation prompt to result validator agent {agent_id}")
        logger.debug(f"Result validation prompt preview:\n{prompt[:500]}...")

    except Exception as e:
        logger.error(f"Failed to spawn result validator tmux session: {e}")
        raise


def terminate_result_validator_session(agent_id: str) -> bool:
    """Terminate a result validator tmux session.

    Args:
        agent_id: Result validator agent ID

    Returns:
        True if session was terminated successfully
    """
    try:
        session_name = f"agent_{agent_id}"
        server = libtmux.Server()

        # Find the session
        session = server.find_where({"session_name": session_name})
        if session:
            session.kill_session()
            logger.info(f"Terminated result validator session: {session_name}")
            return True
        else:
            logger.warning(f"Result validator session not found: {session_name}")
            return False

    except Exception as e:
        logger.error(f"Failed to terminate result validator session {agent_id}: {e}")
        return False


def send_feedback_to_result_validator(
    agent_id: str,
    feedback: str
) -> bool:
    """Send feedback to a running result validator agent.

    Args:
        agent_id: Result validator agent ID
        feedback: Feedback message

    Returns:
        True if feedback was sent successfully
    """
    try:
        session_name = f"agent_{agent_id}"
        server = libtmux.Server()

        # Find the session
        session = server.find_where({"session_name": session_name})
        if not session:
            logger.error(f"Result validator session not found: {session_name}")
            return False

        # Get the active pane
        panes = list(session.panes)
        if not panes:
            logger.error(f"No panes in result validator session: {session_name}")
            return False
        pane = panes[0]  # Get the first pane
        if not pane:
            logger.error(f"No active pane in result validator session: {session_name}")
            return False

        # Send feedback
        feedback_message = f"\n🔍 VALIDATION FEEDBACK:\n{feedback}\n"
        pane.send_keys(feedback_message, enter=True)

        logger.info(f"Sent feedback to result validator agent {agent_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send feedback to result validator {agent_id}: {e}")
        return False


def get_result_validator_status(agent_id: str) -> Optional[dict]:
    """Get status of a result validator agent.

    Args:
        agent_id: Result validator agent ID

    Returns:
        Dictionary with status information or None if not found
    """
    try:
        session_name = f"agent_{agent_id}"
        server = libtmux.Server()

        # Find the session
        session = server.find_where({"session_name": session_name})
        if not session:
            return None

        # Get session info
        panes = list(session.panes)
        active_pane = panes[0] if panes else None

        return {
            "agent_id": agent_id,
            "session_name": session_name,
            "session_id": session.session_id,
            "panes_count": len(panes),
            "active_pane_id": active_pane.pane_id if active_pane else None,
            "status": "running"
        }

    except Exception as e:
        logger.error(f"Failed to get result validator status {agent_id}: {e}")
        return None