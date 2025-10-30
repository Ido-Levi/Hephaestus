"""Build prompts for validator agents."""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime


class ValidationPromptBuilder:
    """Builder for validator agent prompts."""

    VALIDATOR_PROMPT_TEMPLATE = """
You are a Validation Agent responsible for verifying task completion.

YOUR AGENT ID: {validator_agent_id}

TASK INFORMATION:
Task ID: {task_id}
Description: {task_description}
Iteration: {iteration}
Previous Feedback: {previous_feedback}

VALIDATION CRITERIA:
{validation_criteria}

WORKSPACE CHANGES (from commit {commit_sha}):
Files Created: {files_created}
Files Modified: {files_modified}
Files Deleted: {files_deleted}

Detailed Changes:
{detailed_diff}

AGENT CLAIMS:
{agent_results}

YOUR RESPONSIBILITIES:
1. Check EACH validation criterion systematically
2. Run commands to verify functionality
3. Test any claims made by the agent
4. Provide specific, actionable feedback if validation fails
5. Call mcp__hephaestus__give_validation_review with your decision

IMPORTANT:
- You have READ-ONLY access (cannot modify files)
- Be thorough but fair in your assessment
- Provide constructive feedback for improvements
- Include evidence for your decisions
- You MUST use your agent ID ({validator_agent_id}) when calling MCP functions

For EACH criterion, you must:
1. State the criterion
2. Describe how you're testing it
3. Show the evidence (command output, file content, etc.)
4. Make a pass/fail determination

After checking all criteria, call mcp__hephaestus__give_validation_review with:
- task_id: {task_id}
- validator_agent_id: {validator_agent_id}
- validation_passed: true/false
- feedback: Specific details about what passed/failed
- evidence: Array of test results and checks performed
- recommendations: Optional follow-up tasks if validation passes (only if validation passes)
"""

    def __init__(self):
        """Initialize the prompt builder."""
        pass

    def build_prompt(
        self,
        task: Dict[str, Any],
        phase_validation: Optional[Dict[str, Any]],
        commit_sha: str,
        workspace_changes: Dict[str, Any],
        agent_claims: str,
        iteration: int,
        previous_feedback: Optional[str] = None,
        validator_agent_id: Optional[str] = None
    ) -> str:
        """Build a validation prompt for the validator agent.

        Args:
            task: Task information
            phase_validation: Validation configuration from phase YAML
            commit_sha: Commit SHA to validate
            workspace_changes: Changes made by the agent
            agent_claims: Results claimed by the agent
            iteration: Current validation iteration number
            previous_feedback: Feedback from previous iteration if any

        Returns:
            Complete prompt for validator agent
        """
        # Format validation criteria
        validation_criteria = self._format_validation_criteria(phase_validation)

        # Format workspace changes
        files_created = ", ".join(workspace_changes.get("files_created", []))
        files_modified = ", ".join(workspace_changes.get("files_modified", []))
        files_deleted = ", ".join(workspace_changes.get("files_deleted", []))
        detailed_diff = workspace_changes.get("detailed_diff", "No changes")

        # Truncate diff if too long
        if len(detailed_diff) > 5000:
            detailed_diff = detailed_diff[:5000] + "\n... (truncated)"

        # Format previous feedback
        if not previous_feedback:
            previous_feedback = "None (first iteration)"

        # Build the prompt
        prompt = self.VALIDATOR_PROMPT_TEMPLATE.format(
            validator_agent_id=validator_agent_id or "validator-unknown",
            task_id=task.get("id", "unknown"),
            task_description=task.get("enriched_description") or task.get("raw_description", ""),
            iteration=iteration,
            previous_feedback=previous_feedback,
            validation_criteria=validation_criteria,
            commit_sha=commit_sha,
            files_created=files_created or "None",
            files_modified=files_modified or "None",
            files_deleted=files_deleted or "None",
            detailed_diff=detailed_diff,
            agent_results=agent_claims
        )

        # Add custom validator instructions if provided
        if phase_validation and "validator_instructions" in phase_validation:
            prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{phase_validation['validator_instructions']}"

        return prompt

    def _format_validation_criteria(self, phase_validation: Optional[Dict[str, Any]]) -> str:
        """Format validation criteria into readable list.

        Args:
            phase_validation: Validation configuration from phase

        Returns:
            Formatted criteria string
        """
        if not phase_validation or "criteria" not in phase_validation:
            return "No specific validation criteria defined. Use your best judgment."

        criteria = phase_validation["criteria"]
        if not criteria:
            return "No specific validation criteria defined. Use your best judgment."

        formatted = []
        for i, criterion in enumerate(criteria, 1):
            desc = criterion.get("description", "Unnamed criterion")
            check_type = criterion.get("check_type", "manual_verification")

            formatted.append(f"{i}. {desc}")
            formatted.append(f"   Check Type: {check_type}")

            # Add type-specific details
            if check_type == "file_exists":
                target = criterion.get("target", [])
                if isinstance(target, str):
                    target = [target]
                formatted.append(f"   Target Files: {', '.join(target)}")

            elif check_type == "file_contains":
                target = criterion.get("target", "")
                pattern = criterion.get("pattern", "")
                formatted.append(f"   Target File: {target}")
                formatted.append(f"   Pattern to Find: {pattern}")

            elif check_type == "command_success":
                command = criterion.get("command", "")
                formatted.append(f"   Command to Run: {command}")

            elif check_type == "code_review":
                focus_areas = criterion.get("focus_areas", [])
                formatted.append(f"   Focus Areas: {', '.join(focus_areas)}")

            elif check_type == "test_pass":
                command = criterion.get("command", "")
                formatted.append(f"   Test Command: {command}")

            elif check_type == "performance_metric":
                metric = criterion.get("metric", "")
                threshold = criterion.get("threshold", "")
                formatted.append(f"   Metric: {metric}")
                formatted.append(f"   Threshold: {threshold}")

            if criterion.get("evidence_required"):
                formatted.append(f"   Evidence Required: Yes")

            formatted.append("")  # Empty line between criteria

        return "\n".join(formatted)