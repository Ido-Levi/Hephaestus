# Launch Templates

Launch templates turn your workflow definitions into interactive forms. Instead of writing code to start workflows, users fill out a form in the UI, and Hephaestus creates the initial task automatically.

## Why Launch Templates?

Before launch templates, starting a workflow looked like this:

```python
sdk.create_task(
    description="Phase 1: Analyze PRD at /path/to/PRD.md for Web Application...",
    phase_id=1,
    priority="high",
    agent_id="main-session-agent"
)
```

You had to write code every time. And you had to hardcode paths, configurations, and context into task descriptions.

With launch templates, you define a form once:

```python
LaunchTemplate(
    parameters=[
        LaunchParameter(name="prd_location", label="PRD File", type="text", default="./PRD.md"),
        LaunchParameter(name="project_type", label="Project Type", type="dropdown",
                       options=["Web App", "CLI", "Library"]),
    ],
    phase_1_task_prompt="Analyze PRD at {prd_location} for {project_type}..."
)
```

Users fill out the form, click "Launch", and the workflow starts with their inputs automatically substituted.

## The LaunchTemplate Object

A launch template has two parts:

```python
from src.sdk.models import LaunchTemplate, LaunchParameter

template = LaunchTemplate(
    parameters=[...],           # Form fields
    phase_1_task_prompt="..."   # Task template with {placeholders}
)
```

### parameters

A list of `LaunchParameter` objects defining the form fields.

### phase_1_task_prompt

A string template for the Phase 1 task. Use `{parameter_name}` placeholders that match your parameter names.

## The LaunchParameter Object

Each parameter defines one form field:

```python
LaunchParameter(
    name="bug_description",              # Internal name (used in placeholders)
    label="Bug Description",             # Label shown in UI
    type="textarea",                     # Input type
    required=True,                       # Is this field required?
    default="",                          # Default value (optional)
    description="Describe the bug...",   # Help text (optional)
    options=["A", "B", "C"],             # Options for dropdown type (optional)
)
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Internal identifier. Used in `{placeholders}`. Use snake_case. |
| `label` | str | Human-readable label shown above the field in UI. |
| `type` | str | Input type: `text`, `textarea`, `number`, `boolean`, `dropdown` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `required` | bool | Whether the field must be filled. Default: `True` |
| `default` | any | Pre-filled value. Type should match the field type. |
| `description` | str | Help text shown below the field. |
| `options` | list | Required for `dropdown` type. List of string options. |

## Parameter Types

### text

Single-line text input. Good for short values like file paths, names, or IDs.

```python
LaunchParameter(
    name="file_path",
    label="File Path",
    type="text",
    default="./PRD.md",
    description="Path to the requirements document"
)
```

### textarea

Multi-line text input. Good for descriptions, bug reports, or any longer text.

```python
LaunchParameter(
    name="bug_description",
    label="Bug Description",
    type="textarea",
    required=True,
    description="Describe what's happening vs what should happen"
)
```

### number

Numeric input. Good for counts, limits, or numeric configuration.

```python
LaunchParameter(
    name="max_retries",
    label="Maximum Retries",
    type="number",
    default=3,
    description="How many times to retry on failure"
)
```

### boolean

Checkbox input. Good for yes/no options or feature flags.

```python
LaunchParameter(
    name="include_tests",
    label="Include Tests",
    type="boolean",
    default=True,
    description="Generate test files for each component"
)
```

### dropdown

Select from a list of options. Good for categories, priorities, or predefined choices.

```python
LaunchParameter(
    name="severity",
    label="Severity",
    type="dropdown",
    required=True,
    options=["Critical", "High", "Medium", "Low"],
    default="Medium",
    description="How urgent is this bug?"
)
```

## Placeholder Substitution

When a user launches a workflow, their form inputs replace `{placeholders}` in the `phase_1_task_prompt`:

**Template:**
```python
phase_1_task_prompt="""Phase 1: Fix Bug

**Severity:** {severity}
**Component:** {component}

**Description:**
{bug_description}

Your task: Reproduce this bug and create a Phase 2 fix task.
"""
```

**User fills out form:**
- severity: "High"
- component: "Authentication"
- bug_description: "Login fails when password contains @ symbol"

**Resulting Phase 1 task:**
```
Phase 1: Fix Bug

**Severity:** High
**Component:** Authentication

**Description:**
Login fails when password contains @ symbol

Your task: Reproduce this bug and create a Phase 2 fix task.
```

### Substitution Rules

- `{parameter_name}` is replaced with the user's input
- If a parameter is optional and not filled, `{placeholder}` becomes empty string
- Parameter names are case-sensitive
- Placeholders can appear multiple times
- Unknown placeholders remain unchanged

## Complete Examples

### Bug Fix Workflow

```python
from src.sdk.models import LaunchTemplate, LaunchParameter

BUG_FIX_LAUNCH_TEMPLATE = LaunchTemplate(
    parameters=[
        LaunchParameter(
            name="bug_description",
            label="Bug Description",
            type="textarea",
            required=True,
            description="Describe the bug - what's happening vs what should happen"
        ),
        LaunchParameter(
            name="bug_type",
            label="Bug Type",
            type="dropdown",
            required=True,
            options=["UI/Frontend", "Backend/API", "Database", "Performance", "Security", "Other"],
            description="Category of the bug"
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
            name="steps_to_reproduce",
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
    ],
    phase_1_task_prompt="""Phase 1: Analyze and Reproduce Bug

**Bug Type:** {bug_type}
**Severity:** {severity}

**Bug Description:**
{bug_description}

**Steps to Reproduce (if provided):**
{steps_to_reproduce}

**Expected Behavior:**
{expected_behavior}

---

Your task:
1. Read and understand the bug description above
2. If reproduction steps are provided, verify them. If not, create your own
3. Document the reproduction in reproduction.md
4. Form a hypothesis about the root cause
5. Create a Phase 2 task to fix this bug
"""
)
```

### PRD to Software Workflow

```python
PRD_LAUNCH_TEMPLATE = LaunchTemplate(
    parameters=[
        LaunchParameter(
            name="project_name",
            label="Project Name",
            type="text",
            required=True,
            description="Name of the project you're building"
        ),
        LaunchParameter(
            name="project_type",
            label="Project Type",
            type="dropdown",
            required=True,
            options=["Web Application", "CLI Tool", "Library/SDK", "API/Microservice", "Mobile Backend", "Other"],
            description="What type of software are you building?"
        ),
        LaunchParameter(
            name="prd_content",
            label="PRD Content",
            type="textarea",
            required=True,
            description="Paste the full Product Requirements Document here"
        ),
        LaunchParameter(
            name="tech_preferences",
            label="Technology Preferences",
            type="text",
            required=False,
            description="Optional: Preferred tech stack (e.g., 'FastAPI, React, SQLite')"
        ),
    ],
    phase_1_task_prompt="""Phase 1: Requirements Analysis - {project_name}

**Project Type:** {project_type}
**Technology Preferences:** {tech_preferences}

---

## Product Requirements Document

{prd_content}

---

## Your Task

You are analyzing the PRD above for "{project_name}".

1. Carefully read and understand all requirements in the PRD
2. Identify ALL major components/modules needed
3. Create a Kanban ticket for EACH component
4. Create Phase 2 design & implementation tasks for each component
5. Mark your task as done

IMPORTANT: The PRD content above is the COMPLETE requirements document.
"""
)
```

## Attaching to Workflow Definitions

Once you have a launch template, attach it to a `WorkflowDefinition`:

```python
from src.sdk.models import WorkflowDefinition

my_workflow = WorkflowDefinition(
    id="bug-fix",
    name="Bug Fix",
    description="Analyze, fix, and verify bug fixes",
    phases=BUG_FIX_PHASES,
    config=BUG_FIX_WORKFLOW_CONFIG,
    launch_template=BUG_FIX_LAUNCH_TEMPLATE,  # Attach here
)
```

Then register with the SDK:

```python
sdk = HephaestusSDK(
    workflow_definitions=[my_workflow, other_workflow],
    ...
)
```

Workflows with launch templates appear in the UI's "Launch Workflow" modal with their generated forms.

## The Launch Flow

Here's what happens when a user launches a workflow from the UI:

1. **User clicks "Launch Workflow"** in the Workflow Executions page
2. **Modal shows available workflows** (filtered to those with launch templates)
3. **User selects a workflow** (e.g., "Bug Fix")
4. **Form appears** generated from `parameters`
5. **User fills in the form** and clicks "Next"
6. **Preview shows** the Phase 1 task with substituted values
7. **User clicks "Launch"**
8. **Backend creates workflow execution** and initial Phase 1 task
9. **Agent spawns** and starts working on the task

## Best Practices

### Use Descriptive Labels

```python
# Good
LaunchParameter(name="bug_description", label="Bug Description", ...)

# Bad
LaunchParameter(name="desc", label="desc", ...)
```

### Provide Helpful Descriptions

```python
LaunchParameter(
    name="severity",
    label="Severity",
    type="dropdown",
    description="Critical = production down, High = major feature broken, Medium = workaround exists, Low = cosmetic"
)
```

### Set Sensible Defaults

```python
LaunchParameter(
    name="prd_location",
    type="text",
    default="./PRD.md",  # Most common location
)
```

### Make Optional Fields Optional

```python
# Good - steps are helpful but not always known
LaunchParameter(
    name="steps_to_reproduce",
    type="textarea",
    required=False,
    description="Optional: Steps to reproduce (if known)"
)

# Bad - requiring steps blocks users who don't know them
LaunchParameter(
    name="steps_to_reproduce",
    type="textarea",
    required=True,  # Users can't launch without this!
)
```

### Structure Your Task Prompt

Make the Phase 1 task prompt clear and actionable:

```python
phase_1_task_prompt="""Phase 1: [Action]

**Key Info:**
{param1}

**Context:**
{param2}

---

Your task:
1. First step
2. Second step
3. Create Phase 2 task
"""
```

## Workflows Without Launch Templates

Launch templates are optional. If you don't provide one:

- The workflow won't appear in the "Launch Workflow" modal
- You can still start it programmatically:

```python
workflow_id = sdk.start_workflow(
    definition_id="my-workflow",
    description="Manual workflow execution"
)

sdk.create_task_in_workflow(
    workflow_id=workflow_id,
    description="Phase 1: Do the thing",
    phase_id=1,
    agent_id="main-session-agent"
)
```

This is useful for workflows triggered by automation, CI/CD, or API calls rather than human interaction.

## Next Steps

- [SDK Examples](../sdk/examples.md) - See launch templates in action
- [Defining Phases](../sdk/phases.md) - Create phases for your workflow
- [Quick Start](../getting-started/quick-start.md) - Build your first workflow
