"""Build prompts for result validator agents."""

from typing import Dict, Any, Optional
from src.core.database import WorkflowResult, Workflow


def build_result_validator_prompt(
    result: WorkflowResult,
    workflow: Workflow,
    criteria: str,
    validator_agent_id: str
) -> str:
    """
    Build a validation prompt for result validator agents.

    Args:
        result: The workflow result to validate
        workflow: The workflow this result belongs to
        criteria: Validation criteria from workflow configuration
        validator_agent_id: ID of the validator agent

    Returns:
        Complete prompt for result validator agent
    """

    # Format extra files list if present
    extra_files_info = ""
    extra_files_read_commands = ""
    if result.extra_files and len(result.extra_files) > 0:
        extra_files_list = "\n".join([f"   - {file_path}" for file_path in result.extra_files])
        extra_files_info = f"""
- Extra files for validation:
{extra_files_list}

IMPORTANT: Read these extra files to assist your validation!
They contain patches, reproduction scripts, and other evidence."""

        # Add Read commands for each extra file
        extra_files_read_commands = "\n".join([
            f'   Extra file {i+1}: Read("{file_path}")'
            for i, file_path in enumerate(result.extra_files)
        ])
        extra_files_read_commands = f"\n{extra_files_read_commands}"

    prompt = f"""
================================================================================
WORKFLOW RESULT VALIDATION TASK (NOT A TASK VALIDATION!)
================================================================================

You are a RESULT VALIDATOR AGENT. Your role is to validate a workflow-level result submission.

CRITICAL INFORMATION - MEMORIZE THESE:
- Your Agent ID: {validator_agent_id}
- Result ID to validate: {result.id}
- Result file path: {result.result_file_path}{extra_files_info}

================================================================================
STEP-BY-STEP INSTRUCTIONS:
================================================================================

STEP 1: Read the result file and extra files
   Main result: Read("{result.result_file_path}"){extra_files_read_commands}

STEP 2: Evaluate against criteria
   Check if the submission meets these requirements:

{criteria}

STEP 3: Submit your validation
   You MUST use submit_result_validation (NOT give_validation_review!)

   EXACT API CALL TO USE:
   submit_result_validation(
       result_id="{result.id}",
       validation_passed=true/false,
       feedback="Your detailed assessment",
       evidence=[
           {{"type": "criterion_met", "description": "Explanation of how criterion X was met"}},
           {{"type": "quality_check", "description": "Assessment of quality/completeness"}},
           {{"type": "factual_accuracy", "description": "Verification of facts/data"}}
       ]
   )

   CRITICAL: Use ONLY the result_id parameter - do NOT add validator_agent_id!

================================================================================
CONTEXT INFORMATION:
================================================================================

Workflow: {workflow.name} (ID: {workflow.id})
Result submitted by: Agent {result.agent_id}
Submitted at: {result.created_at}

Your task is to determine if this submission successfully achieves the workflow's goal.

VALIDATION APPROACH:
1. Focus on whether the WORKFLOW GOAL is achieved
2. Check if the submission meets the specified criteria
3. Verify quality, accuracy, and completeness
4. Be fair but thorough in your evaluation

IMPORTANT NOTES:
- This is a RESULT validation, not a task validation
- Use the EXACT result_id provided: {result.id}
- You have READ-ONLY access to the files
- DO NOT modify any files
- DO NOT use give_validation_review or update_task_status
- ONLY use submit_result_validation with the exact parameters shown above

Begin now by reading the file at: {result.result_file_path}
"""

    return prompt.strip()