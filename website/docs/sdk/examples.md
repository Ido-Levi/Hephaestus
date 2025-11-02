# SDK Examples

The best way to learn the SDK is to see it in action. Let's break down `run_prd_workflow.py` — a complete, production-ready workflow that builds software from a Product Requirements Document.

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

# Import the phase definitions
from example_workflows.prd_to_software.phases import PRD_PHASES, PRD_WORKFLOW_CONFIG

# Import the SDK
from src.sdk import HephaestusSDK

# Load environment variables from .env file
load_dotenv()
```

**What's happening:**
- Path manipulation lets us import from `example_workflows/`
- We import pre-defined phases (someone already wrote them)
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

### 6. Initialize the SDK

This is the core of the SDK usage:

```python
sdk = HephaestusSDK(
    # Phase definitions (Python objects)
    phases=PRD_PHASES,

    # Workflow configuration (result handling)
    workflow_config=PRD_WORKFLOW_CONFIG,

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
    worktree_branch_prefix="prd-builder-",
)
```

**Important notes:**
- `phases=PRD_PHASES`: Pass the Python phase objects
- `workflow_config=PRD_WORKFLOW_CONFIG`: Configure result handling
- LLM configuration (provider, model) comes from `hephaestus_config.yaml`, not SDK params
- `default_cli_tool`: Optional parameter to override the CLI tool (defaults to config file setting)
- Git paths must match: `main_repo_path == project_root == working_directory`
- `auto_commit=True`: Agent changes are automatically committed

### 7. Start Services

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

### 8. Verify Phases Loaded

```python
print(f"[Phases] Loaded {len(sdk.phases_map)} phases:")
for phase_id, phase in sorted(sdk.phases_map.items()):
    print(f"  - Phase {phase_id}: {phase.name}")
```

**Output:**
```
[Phases] Loaded 3 phases:
  - Phase 1: requirements_analysis
  - Phase 2: plan_and_implementation
  - Phase 3: validate_and_document
```

### 9. Create the Initial Task

Unless using `--resume`, create the Phase 1 task that kicks everything off:

```python
if not args.resume:
    task_id = sdk.create_task(
        description=f"""
        Phase 1: Build LinkLite URL Shortener - Analyze PRD at {prd_file}.

        This is a production-ready URL shortening service with batch operations,
        rich analytics, QR codes, API, and custom domains.

        Extract all requirements, identify components (auth, links, analytics,
        API, frontend, workers, QR generation), and spawn MULTIPLE Phase 2
        design tasks (one per component).

        Read the entire PRD carefully - it has 10 sections with detailed specs.
        """,
        phase_id=1,
        priority="high",
        agent_id="main-session-agent",
    )
    print(f"[Task] ✓ Created task: {task_id}")
```

**Key points:**
- `description`: Tell the agent exactly what to do
- `phase_id=1`: This is a Phase 1 task
- `agent_id="main-session-agent"`: Identifies who created it (you, not another agent)
- The description references the PRD file location

### 10. Monitor Progress

```python
if not args.tui:
    print("[Hephaestus] Workflow running. Press Ctrl+C to stop.\n")
    print("[Info] The workflow will:")
    print("  1. Parse the PRD and identify components")
    print("  2. Create Kanban tickets for each component")
    print("  3. Design each component in parallel (Phase 2)")
    print("  4. Implement each component (Phase 3)")
    print("  5. Test and validate (Phase 4)")
    print("  6. Submit final result when complete")
    print("\n[Kanban Board] http://localhost:3001/")

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

In headless mode, the script keeps running and periodically reports progress.

### 11. Graceful Shutdown

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
python run_prd_workflow.py
```

**With TUI:**
```bash
python run_prd_workflow.py --tui
```

**Fresh start:**
```bash
python run_prd_workflow.py --drop-db
```

**Custom PRD:**
```bash
python run_prd_workflow.py --prd /path/to/my-prd.md
```

**Resume existing workflow:**
```bash
python run_prd_workflow.py --resume
```

## What Happens When It Runs

```
1. [SDK] Loads PRD_PHASES (3 phases)
2. [SDK] Starts backend server (port 8000)
3. [SDK] Starts Guardian monitoring (checks every 60s)
4. [SDK] Creates Phase 1 task: "Analyze PRD at /path/to/PRD.md"
5. [Agent 1] Spawns in tmux session
6. [Agent 1] Reads PRD, identifies 6 components
7. [Agent 1] Creates 6 Kanban tickets
8. [Agent 1] Creates 6 Phase 2 tasks (one per component)
9. [Agent 2-7] Six agents spawn, one per Phase 2 task
10. [Agents 2-7] Work in parallel, each building their component
11. [Agents 2-7] Each creates a Phase 3 validation task when done
12. [Agent 8-13] Six validation agents spawn
13. [Agents 8-13] Validate components, find bugs, create Phase 2 fix tasks
14. [More agents] Spawn to fix bugs discovered by validators
15. [Eventually] All components complete, an agent submits final result
16. [Guardian] Validates result against criteria
17. [SDK] Stops all agents (on_result_found="stop_all")
18. [Workflow] Complete!
```

The workflow **builds itself** based on what agents discover.

## Other Examples

### Simple 2-Phase Workflow

```python
from src.sdk import HephaestusSDK, Phase, WorkflowConfig

phases = [
    Phase(
        id=1,
        name="analysis",
        description="Analyze the problem",
        done_definitions=["Problem understood", "Phase 2 task created"],
        working_directory="."
    ),
    Phase(
        id=2,
        name="solution",
        description="Solve the problem",
        done_definitions=["Solution implemented", "Verified working"],
        working_directory="."
    ),
]

config = WorkflowConfig(
    has_result=True,
    result_criteria="Problem is solved",
    on_result_found="stop_all"
)

sdk = HephaestusSDK(phases=phases, workflow_config=config)
sdk.start()
sdk.create_task("Solve issue #123", phase_id=1, agent_id="main-session-agent")
```

## Key Takeaways

**The SDK pattern:**
1. Define phases (or import existing ones)
2. Configure workflow result handling
3. Initialize SDK with phases + config
4. Start services
5. Create initial task
6. Let it run
7. Shutdown gracefully

**Best practices:**
- Always use `try/except` around `sdk.start()`
- Use `graceful=True` when shutting down
- Set `agent_id="main-session-agent"` for tasks you create manually
- Put cleanup logic in `finally` blocks
- Use `--tui` mode during development for visibility

**Real workflows:**
- See `run_prd_workflow.py` for production example
- See `example_workflows/prd_to_software/phases.py` for phase definitions
- See `example_workflows/hackerone_bug_bounty/` for security testing
- All real workflows follow this pattern

## Next Steps

**Try the PRD Workflow:**
```bash
cd /path/to/Hephaestus
python run_prd_workflow.py --tui
```

**Read the Guides:**
- [SDK Overview](overview.md) - What the SDK does
- [Defining Phases](phases.md) - Complete phase guide
- [Quick Start](../getting-started/quick-start.md) - Step-by-step setup

**Explore Examples:**
- `example_workflows/prd_to_software/` - Complete software builder
- `run_prd_workflow.py` - The script we just examined
