"""
Bug Fix Workflow - Python Phase Definitions

This workflow takes a bug report and systematically fixes it:
1. Phase 1: Reproduce & Analyze - Understand and reproduce the bug
2. Phase 2: Implement Fix - Create minimal fix with regression test
3. Phase 3: Verify & Document - Confirm fix works, write brief docs

The workflow supports looping: if Phase 3 finds issues, it creates a new
Phase 2 task (not Phase 1) to revise the fix. This continues until the
fix passes verification.

Usage:
    from example_workflows.bug_fix.phases import BUG_FIX_PHASES, BUG_FIX_WORKFLOW_CONFIG, BUG_FIX_LAUNCH_TEMPLATE
    from src.sdk.models import WorkflowDefinition

    bug_fix_workflow = WorkflowDefinition(
        id="bug-fix",
        name="Bug Fix",
        description="Systematic bug fixing with verification",
        phases=BUG_FIX_PHASES,
        config=BUG_FIX_WORKFLOW_CONFIG,
        launch_template=BUG_FIX_LAUNCH_TEMPLATE,
    )

    sdk = HephaestusSDK(workflow_definitions=[bug_fix_workflow])
"""

# Import phase definitions from separate files
from example_workflows.bug_fix.phase_1_reproduce import PHASE_1_REPRODUCE
from example_workflows.bug_fix.phase_2_fix import PHASE_2_FIX
from example_workflows.bug_fix.phase_3_verify import PHASE_3_VERIFY

# Import workflow configuration
from example_workflows.bug_fix.board_config import BUG_FIX_WORKFLOW_CONFIG

# Import launch template components
from src.sdk.models import LaunchTemplate, LaunchParameter

# Export phase list
BUG_FIX_PHASES = [
    PHASE_1_REPRODUCE,
    PHASE_2_FIX,
    PHASE_3_VERIFY,
]

# Launch Template - defines the form users fill out to start this workflow
BUG_FIX_LAUNCH_TEMPLATE = LaunchTemplate(
    parameters=[
        LaunchParameter(
            name="bug_title",
            label="Bug Title",
            type="text",
            required=True,
            description="Short, descriptive title for the bug (e.g., 'Login fails with special characters')"
        ),
        LaunchParameter(
            name="bug_description",
            label="Bug Description",
            type="textarea",
            required=True,
            description="Describe the bug: What happens? What should happen instead?"
        ),
        LaunchParameter(
            name="severity",
            label="Severity",
            type="dropdown",
            required=True,
            options=["Critical", "High", "Medium", "Low"],
            default="Medium",
            description="How severe is this bug?"
        ),
        LaunchParameter(
            name="bug_type",
            label="Bug Type",
            type="dropdown",
            required=True,
            options=["Crash/Error", "Wrong Behavior", "Performance", "Security", "UI/UX", "Data Issue", "Other"],
            default="Wrong Behavior",
            description="What type of bug is this?"
        ),
        LaunchParameter(
            name="reproduction_steps",
            label="Steps to Reproduce",
            type="textarea",
            required=False,
            description="Optional: Steps to reproduce the bug (if known)"
        ),
        LaunchParameter(
            name="expected_behavior",
            label="Expected Behavior",
            type="text",
            required=False,
            description="What should happen instead?"
        ),
        LaunchParameter(
            name="affected_component",
            label="Affected Component",
            type="text",
            required=False,
            description="Optional: Which component/module is affected? (e.g., 'auth', 'api', 'frontend')"
        ),
        LaunchParameter(
            name="error_message",
            label="Error Message",
            type="textarea",
            required=False,
            description="Optional: Paste any error messages or stack traces"
        ),
    ],
    phase_1_task_prompt="""Phase 1: Reproduce & Analyze Bug - {bug_title}

**Bug Type:** {bug_type}
**Severity:** {severity}
**Affected Component:** {affected_component}

---

## Bug Description

{bug_description}

---

## Expected Behavior

{expected_behavior}

---

## Reproduction Steps (if provided)

{reproduction_steps}

---

## Error Message (if provided)

{error_message}

---

## Your Task

You are analyzing the bug described above.

1. **READ** the bug description carefully
2. **CREATE** reliable reproduction steps
   - If steps are provided above, verify they work
   - If not provided, create your own
   - Document in reproduction.md
3. **REPRODUCE** the bug - actually trigger it!
4. **ANALYZE** the root cause
   - Find the affected file(s) and function(s)
   - Form a hypothesis about why the bug occurs
5. **CREATE** a bug ticket with full details
   - Use the information above plus your analysis
   - Include reproduction steps, root cause, fix hypothesis
6. **CREATE** a Phase 2 fix task
   - Reference the ticket ID
   - Include key information for the fixer
7. **MARK** your task as done

IMPORTANT: You must VERIFY the reproduction works before creating the ticket.
Don't just assume - actually run the reproduction steps!
""",
)

# Export everything
__all__ = ['BUG_FIX_PHASES', 'BUG_FIX_WORKFLOW_CONFIG', 'BUG_FIX_LAUNCH_TEMPLATE']
