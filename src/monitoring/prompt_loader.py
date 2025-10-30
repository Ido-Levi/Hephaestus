"""Utility for loading and formatting trajectory monitoring prompts."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import structlog

logger = structlog.get_logger()


class PromptLoader:
    """Load and format prompts from markdown files."""

    def __init__(self):
        """Initialize prompt loader with prompts directory path."""
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        if not self.prompts_dir.exists():
            raise ValueError(f"Prompts directory not found: {self.prompts_dir}")

    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt from its markdown file.

        Args:
            prompt_name: Name of the prompt file (without .md extension)

        Returns:
            Raw prompt template string
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.md"
        if not prompt_path.exists():
            raise ValueError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r") as f:
            return f.read()

    def format_guardian_prompt(
        self,
        accumulated_context: Dict[str, Any],
        past_summaries: list,
        task_info: Dict[str, Any],
        agent_output: str,
        last_message_marker: Optional[str] = None,
    ) -> str:
        """Format the Guardian trajectory analysis prompt.

        Args:
            accumulated_context: Full accumulated context from TrajectoryContext
            past_summaries: List of past Guardian summaries
            task_info: Current task information
            agent_output: Recent agent output from tmux
            last_message_marker: Optional marker from previous cycle to identify new content

        Returns:
            Formatted prompt ready for LLM
        """
        # Load the template
        template = self.load_prompt("guardian_trajectory_analysis")

        # Format complex fields
        constraints_str = self._format_list(
            accumulated_context.get("constraints", []),
            "No active constraints"
        )

        lifted_constraints_str = self._format_list(
            accumulated_context.get("lifted_constraints", []),
            "No lifted constraints"
        )

        standing_instructions_str = self._format_list(
            accumulated_context.get("standing_instructions", []),
            "No standing instructions"
        )

        blockers_str = self._format_list(
            accumulated_context.get("discovered_blockers", []),
            "No blockers discovered"
        )

        # Format past summaries
        if past_summaries:
            summaries_str = json.dumps(past_summaries[-5:], indent=2)  # Last 5 summaries
        else:
            summaries_str = "No previous Guardian summaries"

        # Format last message marker section
        if last_message_marker:
            marker_section = f"""
In the previous monitoring cycle, Claude's last message contained: `{last_message_marker}`

**Use this to identify what's NEW** in the current agent output:
- Everything BEFORE this marker was already analyzed
- Everything AFTER this marker is new activity
- Focus your trajectory analysis on the NEW parts
- Still review full context for accumulated understanding
"""
        else:
            marker_section = "No marker from previous cycle (this is the first analysis for this agent)"

        # Format phase information if present
        phase_info = task_info.get("phase_info")
        if phase_info:
            # Truncate additional_notes if too long
            additional_notes = phase_info.get('additional_notes', '')
            if len(additional_notes) > 3000:
                additional_notes = additional_notes[:3000] + "\n\n[... Additional instructions truncated for brevity ...]"

            phase_section = f"""
**THIS AGENT IS WORKING IN A PHASED WORKFLOW**

The task belongs to **{phase_info['workflow_context']['current_position']}** in the workflow.

### Phase {phase_info['phase_number']}: {phase_info['phase_name']}

**Phase Description**:
{phase_info['phase_description']}

**Phase Done Definitions** (What this phase must accomplish):
{chr(10).join(f"- {d}" for d in phase_info.get('done_definitions', []))}

**Phase-Specific Instructions** (Agent MUST follow these):
{additional_notes}

**Expected Outputs from This Phase**:
{phase_info.get('outputs') or 'See done definitions'}

**What Happens After This Phase**:
{phase_info.get('next_steps') or 'Move to next phase'}

**Workflow Context**:
- Total Phases: {phase_info['workflow_context']['total_phases']}
- All Phases: {', '.join(phase_info['workflow_context']['all_phase_names'])}
- Workflow: {phase_info['workflow_context']['workflow_name']}

⚠️ **CRITICAL FOR TRAJECTORY ANALYSIS** ⚠️

You MUST evaluate whether the agent is following the Phase-specific instructions above.
Common Phase instruction patterns:
- "Create a Phase X task" → Check if agent created the task
- "Mark task as done when finished" → Check if agent called update_task_status
- "Search before creating" → Check if agent searched for duplicates
- "Include TICKET: ticket-xxx in description" → Verify format

If agent is NOT following phase instructions → needs_steering: true
"""
        else:
            phase_section = "No workflow phase information available for this task."

        # Format the prompt
        formatted = template.format(
            overall_goal=accumulated_context.get("overall_goal", "Unknown"),
            session_duration=str(accumulated_context.get("session_duration", "Unknown")),
            current_focus=accumulated_context.get("current_focus", "Unknown"),
            conversation_length=accumulated_context.get("conversation_length", 0),
            constraints=constraints_str,
            lifted_constraints=lifted_constraints_str,
            standing_instructions=standing_instructions_str,
            discovered_blockers=blockers_str,
            past_summaries=summaries_str,
            task_description=task_info.get("description", "Unknown"),
            done_definition=task_info.get("done_definition", "Unknown"),
            task_id=task_info.get("task_id", "Unknown"),
            agent_id=task_info.get("agent_id", "Unknown"),
            agent_output=agent_output[-40000:],  # Last 40000 chars to avoid token overflow
            last_message_marker_section=marker_section,
            phase_context=phase_section,  # NEW
        )

        # Prompt to send
        logger.debug("=" * 60)
        logger.debug(f"GUARDIAN PROMPT TO LLM for agent {task_info.get('agent_id', 'unknown')}:")
        logger.debug("=" * 60)
        logger.debug(formatted)
        logger.debug("=" * 60)

        return formatted

    def format_conductor_prompt(
        self,
        guardian_summaries: list,
        system_goals: Dict[str, Any],
    ) -> str:
        """Format the Conductor system analysis prompt.

        Args:
            guardian_summaries: List of all Guardian analysis results
            system_goals: System-wide goals and constraints

        Returns:
            Formatted prompt ready for LLM
        """
        # Load the template
        template = self.load_prompt("conductor_system_analysis")

        # Prepare summary data for better readability
        summary_data = []

        # Debug logging
        logger.info(f"DEBUG - format_conductor_prompt received {len(guardian_summaries)} summaries")

        for i, summary in enumerate(guardian_summaries):
            # Debug: log what we're processing
            logger.info(f"DEBUG - Processing summary {i}: keys={list(summary.keys())}")
            logger.info(f"DEBUG - Summary content: agent_id={summary.get('agent_id')}, "
                       f"trajectory_summary={summary.get('trajectory_summary', 'MISSING')[:100]}")

            summary_data.append({
                "agent_id": summary.get("agent_id"),
                "agent_type": summary.get("agent_type", "phase"),  # Include agent type for Conductor
                "summary": summary.get("trajectory_summary", "No summary"),
                "phase": summary.get("current_phase"),
                "aligned": summary.get("trajectory_aligned"),
                "needs_steering": summary.get("needs_steering"),
                "accumulated_goal": summary.get("accumulated_goal", "")[:100],  # Truncate for readability
            })

        logger.info(f"DEBUG - Prepared summary_data: {json.dumps(summary_data, default=str)[:1000]}")

        # Prepare the JSON string for the template
        summaries_json_str = json.dumps(summary_data, indent=2)
        logger.info(f"DEBUG - guardian_summaries_json string (first 500 chars): {summaries_json_str[:500]}")

        # Format the prompt
        formatted = template.format(
            primary_goal=system_goals.get("primary", "Complete all assigned tasks efficiently"),
            system_constraints=system_goals.get("constraints", "No duplicate work, efficient resource usage"),
            coordination_requirement=system_goals.get("coordination", "All agents working toward collective objectives"),
            guardian_summaries_json=summaries_json_str,
        )

        # Verify the JSON was inserted
        if "{guardian_summaries_json}" in formatted:
            logger.error("ERROR: guardian_summaries_json placeholder was not replaced!")
        elif summaries_json_str not in formatted:
            logger.error("ERROR: guardian_summaries_json content not found in formatted prompt!")
        else:
            logger.info("DEBUG - guardian_summaries_json successfully inserted into prompt")

        # Log the full prompt being sent
        logger.info("=" * 60)
        logger.info("CONDUCTOR PROMPT TO LLM:")
        logger.info("=" * 60)
        # Find and log the JSON section specifically
        json_start = formatted.find("```json")
        if json_start != -1:
            json_end = formatted.find("```", json_start + 7)
            if json_end != -1:
                json_section = formatted[json_start:json_end + 3]
                logger.info(f"JSON SECTION OF PROMPT:\n{json_section}")
            else:
                logger.info(f"JSON SECTION START:\n{formatted[json_start:json_start + 1000]}")
        else:
            logger.info("WARNING: No JSON section found in prompt!")
        # Also show beginning of prompt
        logger.info(f"FULL PROMPT (first 4000 chars):\n{formatted[:4000]}")
        logger.info("=" * 60)

        return formatted

    def format_result_validation_prompt(
        self,
        validator_agent_id: str,
        result_id: str,
        result_file_path: str,
        workflow_name: str,
        workflow_id: str,
        validation_criteria: str,
        submitted_by_agent: str,
        submitted_at: str
    ) -> str:
        """Format the result validation prompt with specific values.

        Args:
            validator_agent_id: ID of the validator agent
            result_id: ID of the result to validate
            result_file_path: Path to the result markdown file
            workflow_name: Name of the workflow
            workflow_id: ID of the workflow
            validation_criteria: The criteria to validate against
            submitted_by_agent: ID of the agent who submitted
            submitted_at: Timestamp of submission

        Returns:
            Formatted prompt ready to send to validator
        """
        template = self.load_prompt("result_validation_prompt")

        return template.format(
            validator_agent_id=validator_agent_id,
            result_id=result_id,
            result_file_path=result_file_path,
            workflow_name=workflow_name,
            workflow_id=workflow_id,
            validation_criteria=validation_criteria,
            submitted_by_agent=submitted_by_agent,
            submitted_at=submitted_at
        )

    def format_task_validation_prompt(
        self,
        validator_agent_id: str,
        task_id: str,
        task_description: str,
        done_definition: str,
        enriched_description: str,
        original_agent_id: str,
        iteration: int,
        working_directory: str,
        commit_sha: str,
        previous_feedback: str = None
    ) -> str:
        """Format the task validation prompt with specific values.

        Args:
            validator_agent_id: ID of the validator agent
            task_id: ID of the task being validated
            task_description: Raw task description
            done_definition: Task completion criteria
            enriched_description: Enriched task description
            original_agent_id: ID of agent who worked on task
            iteration: Validation iteration number
            working_directory: Working directory path
            commit_sha: Git commit to review
            previous_feedback: Previous validation feedback if any

        Returns:
            Formatted prompt ready to send to validator
        """
        template = self.load_prompt("task_validation_prompt")

        # Handle previous feedback section
        if previous_feedback and iteration > 1:
            previous_feedback_section = f"""
### Previous Validation Feedback (Iteration {iteration - 1}):
```
{previous_feedback}
```
Please verify that the previous issues have been addressed.
"""
        else:
            previous_feedback_section = ""

        # Handle iteration-specific guidance
        if iteration == 1:
            iteration_guidance = "This is the first validation. Be thorough but constructive."
        elif iteration == 2:
            iteration_guidance = "This is the second attempt. Check if previous feedback was addressed."
        else:
            iteration_guidance = f"This is attempt {iteration}. Focus on whether core requirements are now met."

        return template.format(
            validator_agent_id=validator_agent_id,
            task_id=task_id,
            task_description=task_description,
            done_definition=done_definition,
            enriched_description=enriched_description,
            original_agent_id=original_agent_id,
            iteration=iteration,
            working_directory=working_directory,
            commit_sha=commit_sha,
            previous_feedback_section=previous_feedback_section,
            iteration_guidance=iteration_guidance
        )

    def _format_list(self, items: list, empty_message: str) -> str:
        """Format a list for prompt insertion.

        Args:
            items: List of items to format
            empty_message: Message to show if list is empty

        Returns:
            Formatted string
        """
        if not items:
            return empty_message

        if len(items) == 1:
            return f"- {items[0]}"

        return "\n".join(f"- {item}" for item in items)


# Singleton instance
prompt_loader = PromptLoader()