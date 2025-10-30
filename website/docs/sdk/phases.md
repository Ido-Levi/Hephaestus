# Defining Workflow Phases

Phases are Python objects that tell agents how to work. They're instruction sets — each phase defines a type of work, completion criteria, and guidance for agents.

## The Phase Object

Here's what a phase looks like:

```python
from src.sdk.models import Phase

Phase(
    id=1,
    name="bug_reproduction",
    description="Reproduce the reported bug and capture evidence",
    done_definitions=[
        "Bug reproduced successfully",
        "Error logs captured",
        "Reproduction steps documented",
        "Phase 2 investigation task created",
        "Task marked as done"
    ],
    working_directory=".",
    additional_notes="""
    🎯 YOUR MISSION: Confirm the bug exists

    STEP 1: Read the bug report carefully
    STEP 2: Follow the exact reproduction steps
    STEP 3: Capture error messages, stack traces, and screenshots
    STEP 4: Document what you found
    STEP 5: Create a Phase 2 task for root cause analysis
    STEP 6: Mark your task as done

    ✅ GOOD: "Bug reproduced. Error: 'Cannot read property of undefined' at login.js:47. Screenshot saved."
    ❌ BAD: "It crashed"
    """
)
```

## Required Fields

### id (int)
The phase number. Must be unique across your workflow.

```python
id=1  # Phase 1
id=2  # Phase 2
id=3  # Phase 3
```

Agents use this when creating tasks: `create_task(description="...", phase_id=2)`

### name (str)
Short identifier for the phase. Use snake_case.

```python
name="bug_reproduction"
name="root_cause_analysis"
name="implementation"
```

This becomes part of the phase filename when the SDK internally converts to YAML.

### description (str)
One-line summary of what this phase does.

```python
description="Reproduce the reported bug and capture evidence"
description="Find the root cause of the bug"
description="Implement and test the bug fix"
```

Agents see this as the phase's purpose.

### done_definitions (List[str])
**This is the most important field.**

Concrete, checkable criteria for completion. These tell agents exactly what "done" means.

```python
done_definitions=[
    "Bug reproduced successfully",           # Specific outcome
    "Error logs captured",                   # Artifact created
    "Reproduction steps documented",         # Evidence exists
    "Phase 2 investigation task created",    # Next work spawned
    "Task marked as done"                    # Cleanup action
]
```

**Write these like acceptance criteria:**
- ✅ "All tests pass" (checkable)
- ❌ "Tests are good" (vague)

- ✅ "plan.md file created with 5+ sections" (measurable)
- ❌ "Create a plan" (unclear)

- ✅ "Phase 3 implementation task created with phase_id=3" (specific)
- ❌ "Create next task" (ambiguous)

### working_directory (str)
Where the agent operates. Usually the project root.

```python
working_directory="."                           # Current directory
working_directory="/path/to/project"            # Absolute path
working_directory="/tmp/swebench_django_issue"  # Isolated workspace
```

Agents will `cd` here before starting work.

## Optional Fields

### additional_notes (str)
**The phase's system prompt.**

This is where you tell agents exactly how to think and work. Be specific. Be direct.

```python
additional_notes="""
🎯 YOUR MISSION: Find the root cause

You are a software engineer debugging a critical production issue.

MANDATORY STEPS:
1. Review the reproduction evidence from Phase 1
2. Read the error logs line by line
3. Trace through the codebase to find the faulty code
4. Identify WHY the bug happens (not just where)
5. Propose a specific fix with file names and line numbers
6. Create a Phase 3 task with your fix proposal
7. Mark your task as done

DO NOT:
- Make assumptions without evidence
- Skip steps to save time
- Create Phase 3 tasks without a clear fix plan

EVIDENCE REQUIREMENTS:
- Name the exact file and line number
- Explain the logical error
- Show what the code should do instead
"""
```

**Good practices:**
- Use clear section headers (YOUR MISSION, MANDATORY STEPS, DO NOT, etc.)
- Number your steps
- Include examples of good vs bad outcomes
- Specify required artifacts
- Mention what to avoid

### outputs (List[str])
Expected artifacts this phase produces.

```python
outputs=[
    "plan.md",                    # Documentation
    "implementation.py",           # Code files
    "test_results.txt",           # Test output
    "architecture_diagram.png"    # Visual artifacts
]
```

Helps agents know what to create. Also useful for validation.

### next_steps (List[str])
What happens after this phase completes.

```python
next_steps=[
    "Phase 2 agent will investigate the root cause",
    "If critical: Phase 2 may spawn multiple investigation tasks",
    "If not reproducible: Workflow ends"
]
```

Gives agents context about the bigger picture. They're not working in isolation.

### validation (ValidationCriteria)
Automated validation rules (optional, advanced feature).

```python
from src.sdk.models import ValidationCriteria

validation=ValidationCriteria(
    enabled=True,
    criteria=[
        {
            "description": "plan.md file exists",
            "check_type": "file_exists",
            "params": {"path": "plan.md"}
        },
        {
            "description": "All tests pass",
            "check_type": "command_succeeds",
            "params": {"command": "pytest"}
        }
    ]
)
```

When enabled, a validation agent checks these criteria before marking the task complete.

## Complete Example

Here's a real 3-phase bug fixing workflow:

```python
from src.sdk.models import Phase

BUG_FIX_PHASES = [
    Phase(
        id=1,
        name="reproduction",
        description="Reproduce the bug and capture evidence",
        done_definitions=[
            "Bug reproduced successfully",
            "Error logs and stack traces captured",
            "Reproduction steps documented in reproduction.md",
            "Phase 2 investigation task created with phase_id=2",
            "Task status updated to 'done'"
        ],
        working_directory=".",
        additional_notes="""
        🎯 REPRODUCE THE BUG

        STEP 1: Read the bug report in your task description
        STEP 2: Follow the exact reproduction steps
        STEP 3: Capture ALL error output (stderr, logs, stack traces)
        STEP 4: Document what happened in reproduction.md
        STEP 5: Create Phase 2 task: "Investigate root cause of [bug name]"
        STEP 6: Call update_task_status with status='done'

        REQUIREMENTS:
        - reproduction.md must include: steps taken, error messages, affected files
        - Screenshots if UI is involved
        - Environment details (OS, versions, etc.)

        CRITICAL: If you cannot reproduce the bug, document why and end the workflow.
        """,
        outputs=["reproduction.md", "error_logs.txt"],
        next_steps=["Phase 2 investigates root cause"]
    ),

    Phase(
        id=2,
        name="investigation",
        description="Find the root cause of the bug",
        done_definitions=[
            "Root cause identified with file and line number",
            "Logical error explained in analysis.md",
            "Fix approach proposed with specific changes",
            "Phase 3 implementation task created with phase_id=3",
            "Task status updated to 'done'"
        ],
        working_directory=".",
        additional_notes="""
        🎯 FIND THE ROOT CAUSE

        You have reproduction evidence from Phase 1. Now find WHY it happens.

        STEP 1: Read reproduction.md from Phase 1
        STEP 2: Examine the error logs and stack trace
        STEP 3: Navigate to the affected files
        STEP 4: Trace through the code logic
        STEP 5: Identify the exact line causing the issue
        STEP 6: Explain the logical error in analysis.md
        STEP 7: Propose a specific fix
        STEP 8: Create Phase 3 task: "Implement fix for [bug name]"
        STEP 9: Call update_task_status with status='done'

        YOUR ANALYSIS MUST INCLUDE:
        - Exact file path and line number
        - Current (broken) code
        - Explanation of the logical error
        - Proposed fix with new code
        - Why this fix solves the problem

        ❌ UNACCEPTABLE: "The auth system is broken"
        ✅ REQUIRED: "In auth.js:47, password is not URL-encoded before passing to API. This causes auth failures when password contains special characters like @. Fix: Add encodeURIComponent(password) before the fetch call."
        """,
        outputs=["analysis.md"],
        next_steps=["Phase 3 implements the proposed fix"]
    ),

    Phase(
        id=3,
        name="implementation",
        description="Implement the bug fix and verify it works",
        done_definitions=[
            "Proposed fix implemented in code",
            "Regression test added to prevent future occurrences",
            "All existing tests still pass",
            "New test passes (bug cannot be reproduced)",
            "Changes committed to git",
            "Task status updated to 'done'"
        ],
        working_directory=".",
        additional_notes="""
        🎯 IMPLEMENT THE FIX

        You have the root cause analysis from Phase 2. Now fix it.

        STEP 1: Read analysis.md from Phase 2
        STEP 2: Implement the proposed fix
        STEP 3: Add a regression test that would fail with the bug
        STEP 4: Run ALL tests: pytest
        STEP 5: Verify the new test passes
        STEP 6: Verify all existing tests still pass
        STEP 7: Commit changes: git add . && git commit -m "Fix: [bug description]"
        STEP 8: Call update_task_status with status='done'

        FIX REQUIREMENTS:
        - Only change what's necessary to fix the bug
        - Follow existing code style
        - Add comments explaining the fix
        - Test must reproduce the bug condition and verify it's fixed

        VERIFICATION:
        - Run the original reproduction steps from Phase 1
        - Confirm the bug no longer occurs
        - All tests must pass

        DO NOT:
        - Skip writing tests
        - Make unrelated changes
        - Break existing functionality
        """,
        outputs=["Fixed code", "test_bug_fix.py", "Git commit"],
        next_steps=["Workflow complete - bug is fixed and verified"]
    ),
]
```

## Importing from Example Workflows

The easiest way to use phases is to import existing ones:

```python
from example_workflows.prd_to_software.phases import PRD_PHASES
from src.sdk import HephaestusSDK

sdk = HephaestusSDK(phases=PRD_PHASES)
```

**Available workflows:**
- `example_workflows/prd_to_software/phases.py` - PRD to working software
- More in `example_workflows/` directory

## Programmatic Phase Generation

You can generate phases dynamically:

```python
def create_component_phases(components):
    """Generate Phase 2 tasks for each component."""
    phases = [
        Phase(
            id=1,
            name="planning",
            description="Analyze requirements and identify components",
            done_definitions=["All components identified", "Phase 2 tasks created"],
            working_directory="."
        )
    ]

    for i, component in enumerate(components, start=2):
        phases.append(Phase(
            id=i,
            name=f"build_{component}",
            description=f"Build the {component} component",
            done_definitions=[
                f"{component} code implemented",
                f"{component} tests pass",
                f"Phase {i+1} validation task created"
            ],
            working_directory=".",
            additional_notes=f"Focus ONLY on {component}. Do not modify other components."
        ))

    return phases

components = ["auth", "api", "database", "frontend"]
my_phases = create_component_phases(components)
```

## Best Practices

### 1. Write Crystal-Clear Done Definitions

Agents need to know when they're done. Be specific.

**Bad:**
```python
done_definitions=["Task complete"]
```

**Good:**
```python
done_definitions=[
    "plan.md created with problem analysis, approach, and implementation steps",
    "Minimum 5 sections in plan.md",
    "All requirements from PRD mentioned",
    "Phase 2 implementation task created with phase_id=2",
    "Task status set to 'done' via update_task_status"
]
```

### 2. Number Your Steps

Agents follow sequential instructions better:

```python
additional_notes="""
STEP 1: Read the requirements
STEP 2: Design the architecture
STEP 3: Create implementation.md
STEP 4: Spawn Phase 2 task
STEP 5: Mark done
"""
```

### 3. Show Examples

Include examples of good vs bad outcomes:

```python
additional_notes="""
✅ GOOD: "Fixed auth bug in login.js:47 by adding URL encoding. Tests pass."
❌ BAD: "Fixed the bug"

✅ GOOD: "Created 3 Phase 2 tasks: build_auth (phase_id=2), build_api (phase_id=2), build_db (phase_id=2)"
❌ BAD: "Made some tasks"
"""
```

### 4. Mandate Phase Transitions

Always tell agents to create the next phase task:

```python
done_definitions=[
    "...",
    "Phase 3 testing task created with phase_id=3",  # ← Mandatory
    "Task marked as done"
]

additional_notes="""
MANDATORY: Before marking done, create Phase 3 task using:
  create_task(
    description="Phase 3: Test the implementation",
    phase_id=3,
    priority="high"
  )
"""
```

### 5. Specify Artifacts

Tell agents exactly what to create:

```python
outputs=[
    "plan.md",           # What to create
    "requirements.txt",
    "architecture.svg"
]

done_definitions=[
    "plan.md exists with 5+ sections",  # How to verify it's done
    "..."
]
```

### 6. Use Working Directory Correctly

```python
# Same project, different phases
Phase(id=1, working_directory="/path/to/project")
Phase(id=2, working_directory="/path/to/project")

# Isolated workspaces
Phase(id=1, working_directory="/tmp/agent1_workspace")
Phase(id=2, working_directory="/tmp/agent2_workspace")
```

Git worktrees provide automatic isolation — you usually want all phases in the same working_directory.

## Common Patterns

### Pattern 1: Planning → Doing → Validating

```python
phases = [
    Phase(id=1, name="planning", description="Plan the work"),
    Phase(id=2, name="implementation", description="Do the work"),
    Phase(id=3, name="validation", description="Verify it works")
]
```

### Pattern 2: Analyze → Design → Build → Test → Document

For software development:

```python
phases = [
    Phase(id=1, name="requirements", description="Extract requirements"),
    Phase(id=2, name="design", description="Design architecture"),
    Phase(id=3, name="implementation", description="Build features"),
    Phase(id=4, name="testing", description="Test everything"),
    Phase(id=5, name="documentation", description="Write docs")
]
```

## What NOT to Do

### ❌ Vague Done Definitions
```python
done_definitions=["Task finished", "Work complete"]
```

### ❌ No Guidance in additional_notes
```python
additional_notes=""  # Agent has no idea what to do
```

### ❌ Missing Phase Transitions
```python
done_definitions=["Code written"]  # No mention of creating next phase task
```

### ❌ Overly Complex Single Phase
```python
# Don't pack everything into one phase
Phase(
    id=1,
    description="Do everything: plan, implement, test, deploy, document"
)
```

Break it into multiple phases instead.

## Next Steps

**See Real Examples**
- [SDK Examples](examples.md) - Breakdown of `run_prd_workflow.py`
- `example_workflows/prd_to_software/phases.py` - Production workflow phases

**Understand the System**
- [Phases System Guide](../guides/phases-system.md) - How workflows build themselves
- [Quick Start](../getting-started/quick-start.md) - Build your first workflow

**Advanced Topics**
- [Workflow Configuration](../guides/workflow-config.md) - Result handling and termination
- [Validation System](../features/validation-system.md) - Automated validation agents

## The Bottom Line

Phases are instruction sets for agents. The clearer your instructions, the better agents perform.

Write specific done definitions. Number your steps. Show examples. Mandate phase transitions.

Then let agents build your workflow.
