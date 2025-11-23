# SDK Examples

The best way to learn the SDK is to see it in action. Let's break down `run_hephaestus_dev.py` — a complete, production-ready setup that registers multiple workflows and lets users launch them from the UI.

## The Complete Example

This is what a real SDK workflow looks like. We'll walk through each part.

### 1. The Setup

```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project to path so we can import from example_workflows
sys.path.insert(0, str(Path(__file__).parent))

# Import workflow definitions (phases + config + launch templates)
from example_workflows.prd_to_software.phases import PRD_PHASES, PRD_WORKFLOW_CONFIG, PRD_LAUNCH_TEMPLATE
from example_workflows.bug_fix.phases import BUG_FIX_PHASES, BUG_FIX_WORKFLOW_CONFIG, BUG_FIX_LAUNCH_TEMPLATE

# Import the SDK
from src.sdk import HephaestusSDK
from src.sdk.models import WorkflowDefinition

# Load environment variables from .env file
load_dotenv()
```

**What's happening:**
- Path manipulation lets us import from `example_workflows/`
- We import pre-defined phases, configs, AND launch templates
- Each workflow comes as a bundle: phases + config + launch template
- Load API keys and config from `.env`

### 2. Parse Command Line Arguments

```python
import argparse

parser = argparse.ArgumentParser(description="Build software from PRD using Hephaestus SDK")
parser.add_argument("--tui", action="store_true", help="Enable TUI mode")
parser.add_argument("--drop-db", action="store_true", help="Drop database before starting")
parser.add_argument("--prd", type=str, help="Path to PRD file (default: auto-detect)")
parser.add_argument("--resume", action="store_true", help="Resume existing workflow")
args = parser.parse_args()
```

**Options:**
- `--tui`: Show visual interface instead of headless mode
- `--drop-db`: Start fresh (deletes `hephaestus.db`)
- `--prd /path/to/PRD.md`: Specify PRD location
- `--resume`: Continue existing workflow without creating initial task

### 3. Cleanup (Optional)

```python
def kill_existing_services():
    """Kill any existing Hephaestus services on port 8000."""
    try:
        result = subprocess.run(["lsof", "-ti", ":8000"], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                os.kill(int(pid), signal.SIGKILL)
                print(f"  Killed process on port 8000 (PID: {pid})")
    except Exception as e:
        print(f"  Warning: Could not kill processes: {e}")

kill_existing_services()
```

This ensures a clean start by killing any lingering Hephaestus processes.

### 4. Load Configuration

```python
# These come from environment variables or defaults
db_path = os.getenv("DATABASE_PATH", "./hephaestus.db")
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
mcp_port = int(os.getenv("MCP_PORT", "8000"))
monitoring_interval = int(os.getenv("MONITORING_INTERVAL_SECONDS", "60"))
working_directory = os.getenv("WORKING_DIRECTORY", "/path/to/project")
```

**Key settings:**
- `DATABASE_PATH`: Where SQLite stores task/agent data
- `QDRANT_URL`: Vector store for memory/RAG
- `MCP_PORT`: Port for the FastAPI server
- `MONITORING_INTERVAL_SECONDS`: How often Guardian checks agents
- `WORKING_DIRECTORY`: Where agents work (must be a git repo)

### 5. Find the PRD File

```python
def find_prd_file(working_dir: str, specified_path: str = None) -> str:
    """Find the PRD file in the working directory."""
    if specified_path:
        return specified_path

    # Look for common names
    candidates = ["PRD.md", "prd.md", "REQUIREMENTS.md", "README.md"]

    for candidate in candidates:
        prd_path = Path(working_dir) / candidate
        if prd_path.exists():
            return str(prd_path.absolute())

    print("[Error] No PRD file found")
    sys.exit(1)

prd_file = find_prd_file(working_directory, args.prd)
```

The script automatically finds your PRD by looking for common filenames.

### 6. Create Workflow Definitions

Bundle your phases, config, and launch template into `WorkflowDefinition` objects:

```python
# Create workflow definitions
prd_definition = WorkflowDefinition(
    id="prd-to-software",
    name="PRD to Software Builder",
    phases=PRD_PHASES,
    config=PRD_WORKFLOW_CONFIG,
    description="Build working software from a Product Requirements Document",
    launch_template=PRD_LAUNCH_TEMPLATE,
)

bug_fix_definition = WorkflowDefinition(
    id="bug-fix",
    name="Bug Fix",
    phases=BUG_FIX_PHASES,
    config=BUG_FIX_WORKFLOW_CONFIG,
    description="Analyze, fix, and verify bug fixes",
    launch_template=BUG_FIX_LAUNCH_TEMPLATE,
)
```

**What each field does:**
- `id`: Unique identifier used in API calls (e.g., "bug-fix")
- `name`: Human-readable name shown in UI
- `phases`: List of Phase objects defining the workflow stages
- `config`: WorkflowConfig with result handling settings
- `description`: Shows in the workflow selector
- `launch_template`: Defines the UI form for launching (optional but recommended)

### 7. Initialize the SDK

Now pass your workflow definitions to the SDK:

```python
sdk = HephaestusSDK(
    # Multi-workflow mode - register all your workflow types
    workflow_definitions=[prd_definition, bug_fix_definition],

    # Database
    database_path=db_path,

    # Vector store
    qdrant_url=qdrant_url,

    # Note: LLM configuration comes from hephaestus_config.yaml
    # No need to specify llm_provider or llm_model here

    # Working directory
    working_directory=working_directory,

    # Agent CLI Tool (optional - overrides config file)
    default_cli_tool="claude",  # Options: "claude" (default), "opencode", "codex"

    # Server
    mcp_port=mcp_port,
    monitoring_interval=monitoring_interval,

    # Git Configuration (REQUIRED for worktree isolation)
    main_repo_path=working_directory,
    project_root=working_directory,
    auto_commit=True,
    conflict_resolution="newest_file_wins",
    worktree_branch_prefix="example-",
)
```

**Important notes:**
- `workflow_definitions=[...]`: Pass all your workflow types
- LLM configuration (provider, model) comes from `hephaestus_config.yaml`, not SDK params
- `default_cli_tool`: Optional parameter to override the CLI tool
- Git paths must match: `main_repo_path == project_root == working_directory`
- `auto_commit=True`: Agent changes are automatically committed

### 8. Start Services

```python
try:
    sdk.start(enable_tui=args.tui, timeout=30)
except Exception as e:
    print(f"[Error] Failed to start services: {e}")
    sys.exit(1)
```

This starts:
- FastAPI backend server (port 8000)
- Guardian monitoring process
- TUI interface (if `--tui` flag used)

Waits up to 30 seconds for health checks to pass.

### 9. Verify Workflow Definitions Loaded

```python
definitions = sdk.list_workflow_definitions()
print(f"[Workflows] Loaded {len(definitions)} workflow definitions:")
for defn in definitions:
    has_template = " (with launch template)" if defn.launch_template else ""
    print(f"  - {defn.name} ({defn.id}): {len(defn.phases)} phases{has_template}")
```

**Output:**
```
[Workflows] Loaded 2 workflow definitions:
  - PRD to Software Builder (prd-to-software): 3 phases (with launch template)
  - Bug Fix (bug-fix): 3 phases (with launch template)
```

### 10. Let Users Launch from UI

With multi-workflow mode, you don't create tasks programmatically. Users launch workflows from the UI:

```python
print("=" * 60)
print("HEPHAESTUS IS READY")
print("=" * 60)
print()
print("Open the frontend to launch workflows:")
print("  http://localhost:3000")
print()
print("To launch a workflow:")
print("  1. Go to 'Workflow Executions' page")
print("  2. Click 'Launch Workflow'")
print("  3. Select a workflow and fill in the form")
print("  4. Review and launch!")
print()
print("Press Ctrl+C to stop Hephaestus")
```

When users click "Launch Workflow", they see a form generated from your `LaunchTemplate`. Their inputs become the Phase 1 task prompt.

**Still want programmatic task creation?** You can do both:

```python
# Start a workflow programmatically (returns workflow_id)
workflow_id = sdk.start_workflow(
    definition_id="bug-fix",
    description="Fix login authentication bug",
    launch_params={
        "bug_description": "Login fails with special characters",
        "severity": "High"
    }
)

# Or create tasks in an existing workflow
task_id = sdk.create_task_in_workflow(
    workflow_id=workflow_id,
    description="Investigate the authentication issue",
    phase_id=1,
    priority="high",
    agent_id="main-session-agent",
)
```

### 11. Monitor Progress

```python
try:
    while True:
        time.sleep(10)
        # Optional: Poll task status
        tasks = sdk.get_tasks(status="in_progress")
        if tasks:
            print(f"[Status] {len(tasks)} task(s) in progress...")
except KeyboardInterrupt:
    print("\n[Hephaestus] Received interrupt signal")
```

In headless mode, the script keeps running and periodically reports progress. You can also monitor everything in the UI at `http://localhost:3000`.

### 12. Graceful Shutdown

```python
print("\n[Hephaestus] Shutting down...")
sdk.shutdown(graceful=True, timeout=10)
print("[Hephaestus] ✓ Shutdown complete")
```

Cleanly stops all services:
- Gives agents 10 seconds to finish current operations
- Stops the backend server
- Stops Guardian monitoring
- Cleans up tmux sessions

## The Launch Template

The magic of UI-based launching comes from `LaunchTemplate`. Here's what the PRD workflow's template looks like:

```python
from src.sdk.models import LaunchTemplate, LaunchParameter

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
            options=["Web Application", "CLI Tool", "Library/SDK", "API/Microservice"],
            description="What type of software are you building?"
        ),
        LaunchParameter(
            name="prd_content",
            label="PRD Content",
            type="textarea",
            required=True,
            description="Paste the full PRD here"
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

## PRD Content
{prd_content}

Your task:
1. Read and understand the PRD above
2. Identify major components
3. Create Kanban tickets for each component
4. Create Phase 2 design & implementation tasks
"""
)
```

**How it works:**

1. **parameters**: Define form fields users fill out
2. **phase_1_task_prompt**: The template for the initial task
3. **{placeholders}**: Get replaced with user inputs when launched

**Available parameter types:**
- `text`: Single-line text input
- `textarea`: Multi-line text input
- `number`: Numeric input
- `boolean`: Checkbox
- `dropdown`: Select from options list

See [Launch Templates](../features/launch-templates.md) for the complete guide.

## The Phase Definitions

Let's look at what `PRD_PHASES` contains:

```python
# From example_workflows/prd_to_software/phases.py

from src.sdk.models import Phase

PHASE_1_REQUIREMENTS = Phase(
    id=1,
    name="requirements_analysis",
    description="Extract requirements from PRD and create component tickets",
    done_definitions=[
        "PRD fully analyzed",
        "All components identified",
        "Kanban tickets created for each component",
        "Phase 2 design tasks created for each component",
        "Task marked as done"
    ],
    working_directory=".",
    additional_notes="""
    🎯 YOUR MISSION: Break down the PRD into buildable components

    STEP 1: Read the entire PRD document
    STEP 2: Extract all functional requirements
    STEP 3: Identify system components (auth, API, frontend, database, etc.)
    STEP 4: Create a Kanban ticket for each component using create_ticket()
    STEP 5: Create Phase 2 design tasks (one per component) using create_task()
    STEP 6: Mark your task as done

    CRITICAL: Each component gets TWO things:
    1. A Kanban ticket (for tracking)
    2. A Phase 2 task (for actual work)
    """
)

PHASE_2_DESIGN = Phase(
    id=2,
    name="plan_and_implementation",
    description="Design and implement one component",
    done_definitions=[
        "Component design documented",
        "Implementation complete",
        "Tests pass",
        "Phase 3 validation task created",
        "Task marked as done"
    ],
    working_directory=".",
    additional_notes="""
    🎯 YOUR MISSION: Build ONE component completely

    You are assigned to ONE specific component. Do not work on other components.

    STEP 1: Design the component architecture
    STEP 2: Implement the code
    STEP 3: Write tests (minimum 3 test cases)
    STEP 4: Run tests and ensure they pass
    STEP 5: Create Phase 3 validation task
    STEP 6: Mark your task as done
    """
)

PHASE_3_VALIDATION = Phase(
    id=3,
    name="validate_and_document",
    description="Validate component and write documentation",
    done_definitions=[
        "Integration tests pass",
        "Component documentation written",
        "No regressions in other components",
        "Task marked as done"
    ],
    working_directory=".",
    additional_notes="""
    🎯 YOUR MISSION: Validate and document

    STEP 1: Run all tests (unit + integration)
    STEP 2: Verify no regressions
    STEP 3: Write component documentation
    STEP 4: If issues found: Create Phase 2 bug-fix task
    STEP 5: Mark your task as done
    """
)

PRD_PHASES = [
    PHASE_1_REQUIREMENTS,
    PHASE_2_DESIGN,
    PHASE_3_VALIDATION
]
```

## The Workflow Configuration

```python
# From example_workflows/prd_to_software/phases.py

from src.sdk.models import WorkflowConfig

PRD_WORKFLOW_CONFIG = WorkflowConfig(
    has_result=True,
    result_criteria="All components implemented, tested, and documented",
    on_result_found="stop_all"
)
```

**What this does:**
- `has_result=True`: Workflow has a definitive completion point
- `result_criteria`: What "done" means for the entire workflow
- `on_result_found="stop_all"`: Stop all agents when result is submitted

When an agent calls `submit_result()`, Guardian validates it against these criteria.

## Running the Example

**Basic usage:**
```bash
python run_hephaestus_dev.py
```

**Fresh start (drops database):**
```bash
python run_hephaestus_dev.py --drop-db
```

**Specify project path:**
```bash
python run_hephaestus_dev.py --path /path/to/my/project
```

The script will:
1. Set up a project directory with example PRD
2. Initialize git repository
3. Start Hephaestus with both workflows registered
4. Display instructions for launching from UI

## What Happens When You Launch a Workflow

```
1. [User] Clicks "Launch Workflow" in UI
2. [User] Selects "PRD to Software Builder"
3. [User] Fills in form: PRD location, project type, preferences
4. [User] Reviews and clicks "Launch"
5. [SDK] Creates workflow execution
6. [SDK] Substitutes form values into phase_1_task_prompt
7. [SDK] Creates Phase 1 task with populated prompt
8. [Agent 1] Spawns in tmux session
9. [Agent 1] Reads PRD, identifies 6 components
10. [Agent 1] Creates 6 Kanban tickets
11. [Agent 1] Creates 6 Phase 2 tasks (one per component)
12. [Agent 2-7] Six agents spawn, one per Phase 2 task
13. [Agents 2-7] Work in parallel, each building their component
14. [Agents 2-7] Each creates a Phase 3 validation task when done
15. [Agent 8-13] Six validation agents spawn
16. [Agents 8-13] Validate components, find bugs, create Phase 2 fix tasks
17. [More agents] Spawn to fix bugs discovered by validators
18. [Eventually] All components complete, an agent submits final result
19. [Guardian] Validates result against criteria
20. [SDK] Marks workflow complete (on_result_found="complete")
21. [Workflow] Complete!
```

The workflow **builds itself** based on what agents discover.

## Other Examples

### Bug Fix Workflow

The bug fix workflow is simpler — it fixes bugs in 3 phases:

```python
from example_workflows.bug_fix.phases import BUG_FIX_PHASES, BUG_FIX_WORKFLOW_CONFIG, BUG_FIX_LAUNCH_TEMPLATE
from src.sdk.models import WorkflowDefinition

bug_fix_workflow = WorkflowDefinition(
    id="bug-fix",
    name="Bug Fix",
    phases=BUG_FIX_PHASES,
    config=BUG_FIX_WORKFLOW_CONFIG,
    description="Analyze, fix, and verify bug fixes",
    launch_template=BUG_FIX_LAUNCH_TEMPLATE,
)
```

The launch template asks for:
- Bug description (textarea)
- Bug type (dropdown: UI, Backend, Database, etc.)
- Severity (dropdown: Critical, High, Medium, Low)
- Steps to reproduce (optional textarea)

### Adding Your Own Workflow

Create a new workflow by defining phases, config, and launch template:

```python
from src.sdk.models import Phase, WorkflowConfig, LaunchTemplate, LaunchParameter, WorkflowDefinition

# 1. Define phases
my_phases = [
    Phase(id=1, name="research", description="Research the topic", ...),
    Phase(id=2, name="execute", description="Execute the plan", ...),
    Phase(id=3, name="verify", description="Verify results", ...),
]

# 2. Configure result handling
my_config = WorkflowConfig(
    has_result=True,
    result_criteria="Task completed successfully",
    on_result_found="complete"
)

# 3. Create launch template
my_template = LaunchTemplate(
    parameters=[
        LaunchParameter(name="topic", label="Topic", type="text", required=True),
        LaunchParameter(name="depth", label="Research Depth", type="dropdown",
                       options=["Quick", "Standard", "Deep"], default="Standard"),
    ],
    phase_1_task_prompt="Research {topic} with {depth} analysis..."
)

# 4. Bundle into WorkflowDefinition
my_workflow = WorkflowDefinition(
    id="my-research",
    name="Research Workflow",
    phases=my_phases,
    config=my_config,
    description="Research any topic systematically",
    launch_template=my_template,
)
```

## Key Takeaways

**The multi-workflow SDK pattern:**
1. Define phases for each workflow type
2. Create launch templates for UI forms
3. Bundle into WorkflowDefinition objects
4. Initialize SDK with all workflow definitions
5. Start services
6. Let users launch from UI (or programmatically)
7. Shutdown gracefully

**Best practices:**
- Always use `try/except` around `sdk.start()`
- Use `graceful=True` when shutting down
- Create meaningful launch template parameters
- Use descriptive workflow IDs and names
- Put cleanup logic in `finally` blocks

**Available workflows:**
- `example_workflows/prd_to_software/` - PRD to software builder
- `example_workflows/bug_fix/` - Bug fixing workflow
- `run_hephaestus_dev.py` - Multi-workflow setup example

## Next Steps

**Try it out:**
```bash
cd /path/to/Hephaestus
python run_hephaestus_dev.py
# Then open http://localhost:3000 and launch a workflow!
```

**Read the Guides:**
- [SDK Overview](overview.md) - What the SDK does
- [Defining Phases](phases.md) - Complete phase guide
- [Launch Templates](../features/launch-templates.md) - UI form configuration
- [Quick Start](../getting-started/quick-start.md) - Step-by-step setup

**Explore Examples:**
- `example_workflows/prd_to_software/phases.py` - Complete PRD workflow with launch template
- `example_workflows/bug_fix/phases.py` - Bug fix workflow with launch template
