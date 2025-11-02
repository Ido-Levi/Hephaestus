"""Abstract interface for CLI AI agents."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


class CLIAgentInterface(ABC):
    """Abstract interface for CLI AI agents."""

    @abstractmethod
    def get_launch_command(self, system_prompt: str, **kwargs) -> str:
        """Generate the launch command for the CLI tool.

        Args:
            system_prompt: System prompt for the agent
            **kwargs: Additional parameters for the CLI tool

        Returns:
            Complete command to launch the CLI tool
        """
        pass

    @abstractmethod
    def get_health_check_pattern(self) -> str:
        """Return pattern to check if agent is healthy.

        Returns:
            Regex pattern or string to look for in output
        """
        pass

    @abstractmethod
    def format_message(self, message: str) -> str:
        """Format a message for the specific CLI tool.

        Args:
            message: Raw message to send

        Returns:
            Formatted message for the CLI tool
        """
        pass

    @abstractmethod
    def get_stuck_patterns(self) -> List[str]:
        """Return patterns that indicate the agent is stuck.

        Returns:
            List of patterns to check for stuck state
        """
        pass

    @abstractmethod
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse CLI output for relevant information.

        Args:
            output: Raw output from the CLI tool

        Returns:
            Parsed information dict
        """
        pass

    def is_healthy(self, output: str) -> bool:
        """Check if the agent appears healthy based on output.

        Args:
            output: Recent output from the agent

        Returns:
            True if healthy, False otherwise
        """
        pattern = self.get_health_check_pattern()
        return bool(re.search(pattern, output, re.MULTILINE | re.IGNORECASE))

    def is_stuck(self, output: str) -> bool:
        """Check if the agent appears stuck.

        Args:
            output: Recent output from the agent

        Returns:
            True if stuck, False otherwise
        """
        for pattern in self.get_stuck_patterns():
            if re.search(pattern, output, re.MULTILINE | re.IGNORECASE):
                return True
        return False


class ClaudeCodeAgent(CLIAgentInterface):
    """Implementation for Claude Code CLI."""

    def get_launch_command(self, system_prompt: str, **kwargs) -> str:
        """Generate launch command for Claude Code."""
        import os
        from src.core.simple_config import get_config

        config = get_config()

        # Save prompt to a temp file first to avoid shell escaping issues
        task_id = kwargs.get('task_id', 'default')
        prompt_file = f"/tmp/hep_prompt_{task_id}.txt"

        # Write the system prompt to file directly (safer than echo)
        with open(prompt_file, 'w') as f:
            f.write(system_prompt)

        # Make sure the file is readable
        os.chmod(prompt_file, 0o644)

        # Get configured model
        model = getattr(config, 'cli_model', 'sonnet')

        # For GLM models, we use "sonnet" as the CLI flag but env vars are set on tmux session
        # For standard models, use the model name directly
        if 'GLM' in model.upper():
            command = f"claude --model sonnet --dangerously-skip-permissions --append-system-prompt \"$(cat {prompt_file})\""
        else:
            command = f"claude --model {model} --dangerously-skip-permissions --append-system-prompt \"$(cat {prompt_file})\""

        return command

    def get_health_check_pattern(self) -> str:
        """Return health check pattern for Claude Code."""
        return r"(Assistant:|Human:|›)"

    def format_message(self, message: str) -> str:
        """Format message for Claude Code."""
        # Claude Code accepts plain text messages
        return message

    def get_stuck_patterns(self) -> List[str]:
        """Return stuck patterns for Claude Code."""
        return [
            r"rate limit exceeded",
            r"waiting for user input",
            r"API error",
            r"connection timeout",
            r"Error:.*API",
            r"Failed to connect",
            r"Maximum retries exceeded",
        ]

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse Claude Code output."""
        lines = output.strip().split('\n')
        last_message = ""
        is_waiting = False

        # Look for the last assistant message
        for i in range(len(lines) - 1, -1, -1):
            if "Assistant:" in lines[i]:
                # Get all lines after "Assistant:" until next prompt
                message_lines = []
                for j in range(i + 1, len(lines)):
                    if "Human:" in lines[j] or "›" in lines[j]:
                        break
                    message_lines.append(lines[j])
                last_message = "\n".join(message_lines).strip()
                break

        # Check if waiting for input
        if lines and ("›" in lines[-1] or "Human:" in lines[-1]):
            is_waiting = True

        return {
            "last_message": last_message,
            "is_waiting": is_waiting,
            "total_lines": len(lines),
        }


class OpenCodeAgent(CLIAgentInterface):
    """Implementation for OpenCode CLI (open-source alternative to Claude Code).

    OpenCode supports the -p flag to pre-load a prompt, but doesn't auto-submit it.
    We save the prompt to a temp file, launch with -p "$(cat file)", then send Enter
    after 5 seconds to submit the prompt.
    """

    def get_launch_command(self, system_prompt: str, **kwargs) -> str:
        """Generate launch command for OpenCode.

        OpenCode's -p flag adds the prompt but doesn't auto-submit.
        We'll save the prompt to a temp file and use -p "$(cat file)" to load it.
        The calling code will send Enter after 5 seconds to submit.
        """
        import os
        from src.core.simple_config import get_config

        config = get_config()

        # Save prompt to a temp file
        task_id = kwargs.get('task_id', 'default')
        prompt_file = f"/tmp/opencode_prompt_{task_id}.txt"

        # Write the system prompt to file
        with open(prompt_file, 'w') as f:
            f.write(system_prompt)

        # Make sure the file is readable
        os.chmod(prompt_file, 0o644)

        # Get configured model (OpenCode uses provider/model format)
        model = getattr(config, 'cli_model', 'anthropic/claude-sonnet-4')

        # OpenCode command with -p flag to load the prompt
        # The prompt will be added to the input but not submitted
        command = f"opencode -p \"$(cat {prompt_file})\" --model {model}"

        return command

    def get_health_check_pattern(self) -> str:
        """Return health check pattern for OpenCode.

        OpenCode uses a prompt indicator in its TUI.
        """
        return r"(›|>|opencode>)"

    def format_message(self, message: str) -> str:
        """Format message for OpenCode.

        OpenCode accepts plain text messages in its TUI.
        """
        return message

    def get_stuck_patterns(self) -> List[str]:
        """Return stuck patterns for OpenCode."""
        return [
            r"rate limit exceeded",
            r"rate limit",
            r"API error",
            r"connection timeout",
            r"Error:.*API",
            r"Failed to connect",
            r"Maximum retries exceeded",
            r"authentication failed",
            r"invalid API key",
        ]

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse OpenCode output."""
        lines = output.strip().split('\n')
        last_message = ""
        is_waiting = False

        # Look for the last response before a prompt indicator
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if "›" in line or ">" in line or "opencode>" in line:
                is_waiting = True
                # Get all lines after the previous prompt as the response
                message_lines = []
                for j in range(i - 1, -1, -1):
                    if "›" in lines[j] or ">" in lines[j] or "opencode>" in lines[j]:
                        break
                    message_lines.insert(0, lines[j])
                last_message = "\n".join(message_lines).strip()
                break

        return {
            "last_message": last_message,
            "is_waiting": is_waiting,
            "total_lines": len(lines),
        }


class DroidAgent(CLIAgentInterface):
    """Implementation for Droid CLI.

    Droid doesn't support system prompts or command-line flags.
    We launch it with just 'droid', wait for initialization, then send the prompt
    in batches similar to Claude Code to avoid tmux buffer issues.
    """

    def get_launch_command(self, system_prompt: str, **kwargs) -> str:
        """Generate launch command for Droid.

        Droid doesn't accept any flags - just launch 'droid'.
        The prompt will be sent in batches after initialization.
        """
        return "droid"

    def get_health_check_pattern(self) -> str:
        """Return health check pattern for Droid.

        Droid uses a prompt indicator in its TUI.
        """
        return r"(›|>|droid>)"

    def format_message(self, message: str) -> str:
        """Format message for Droid.

        Droid accepts plain text messages in its TUI.
        """
        return message

    def get_stuck_patterns(self) -> List[str]:
        """Return stuck patterns for Droid."""
        return [
            r"rate limit exceeded",
            r"rate limit",
            r"API error",
            r"connection timeout",
            r"Error:.*API",
            r"Failed to connect",
            r"Maximum retries exceeded",
            r"authentication failed",
            r"invalid API key",
        ]

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse Droid output."""
        lines = output.strip().split('\n')
        last_message = ""
        is_waiting = False

        # Look for the last response before a prompt indicator
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if "›" in line or ">" in line or "droid>" in line:
                is_waiting = True
                # Get all lines after the previous prompt as the response
                message_lines = []
                for j in range(i - 1, -1, -1):
                    if "›" in lines[j] or ">" in lines[j] or "droid>" in lines[j]:
                        break
                    message_lines.insert(0, lines[j])
                last_message = "\n".join(message_lines).strip()
                break

        return {
            "last_message": last_message,
            "is_waiting": is_waiting,
            "total_lines": len(lines),
        }


class CodexAgent(CLIAgentInterface):
    """Implementation for Codex CLI."""

    def get_launch_command(self, system_prompt: str, **kwargs) -> str:
        """Generate launch command for Codex."""
        # Escape quotes in the system prompt
        escaped_prompt = system_prompt.replace('"', '\\"').replace("'", "'\"'\"'")

        # Base command
        command = "codex --mode interactive"

        # Add system prompt if provided
        if system_prompt:
            command += f" --system '{escaped_prompt}'"

        return command

    def get_health_check_pattern(self) -> str:
        """Return health check pattern for Codex."""
        return r"(>|codex>|Ready)"

    def format_message(self, message: str) -> str:
        """Format message for Codex."""
        # Codex uses command format
        if not message.startswith("/"):
            return f"/task {message}"
        return message

    def get_stuck_patterns(self) -> List[str]:
        """Return stuck patterns for Codex."""
        return [
            r"error:",
            r"connection failed",
            r"timeout",
            r"invalid response",
            r"Authentication failed",
            r"Rate limit",
        ]

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse Codex output."""
        lines = output.strip().split('\n')
        last_response = ""
        is_ready = False

        # Look for the last response
        for i in range(len(lines) - 1, -1, -1):
            if ">" in lines[i]:
                is_ready = True
                # Get previous lines as response
                if i > 0:
                    response_lines = []
                    for j in range(i - 1, -1, -1):
                        if ">" in lines[j] or lines[j].startswith("/"):
                            break
                        response_lines.insert(0, lines[j])
                    last_response = "\n".join(response_lines).strip()
                break

        return {
            "last_response": last_response,
            "is_ready": is_ready,
            "total_lines": len(lines),
        }


class SwarmCodeAgent(CLIAgentInterface):
    """Implementation for SwarmCode CLI (hypothetical advanced agent)."""

    def get_launch_command(self, system_prompt: str, **kwargs) -> str:
        """Generate launch command for SwarmCode."""
        escaped_prompt = system_prompt.replace("'", "'\"'\"'")
        command = "swarmcode --autonomous"

        if system_prompt:
            prompt_file = f"/tmp/hep_prompt_{kwargs.get('task_id', 'default')}.txt"
            command = f"echo '{escaped_prompt}' > {prompt_file} && swarmcode --autonomous --context {prompt_file}"

        return command

    def get_health_check_pattern(self) -> str:
        """Return health check pattern for SwarmCode."""
        return r"(SWARM>|Ready|Processing)"

    def format_message(self, message: str) -> str:
        """Format message for SwarmCode."""
        return f"TASK: {message}"

    def get_stuck_patterns(self) -> List[str]:
        """Return stuck patterns for SwarmCode."""
        return [
            r"BLOCKED:",
            r"WAITING FOR INPUT",
            r"ERROR:",
            r"DEADLOCK DETECTED",
        ]

    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse SwarmCode output."""
        return {
            "output": output,
            "status": "processing",
        }


# Registry for available CLI agents
CLI_AGENTS = {
    "claude": ClaudeCodeAgent,
    "opencode": OpenCodeAgent,
    "droid": DroidAgent,
    "codex": CodexAgent,
    "swarm": SwarmCodeAgent,
}


def get_cli_agent(agent_type: str) -> CLIAgentInterface:
    """Get a CLI agent instance by type.

    Args:
        agent_type: Type of CLI agent (claude, opencode, codex, etc.)

    Returns:
        CLI agent instance

    Raises:
        ValueError: If agent type is not supported
    """
    if agent_type not in CLI_AGENTS:
        raise ValueError(f"Unsupported CLI agent type: {agent_type}. Available: {list(CLI_AGENTS.keys())}")

    return CLI_AGENTS[agent_type]()