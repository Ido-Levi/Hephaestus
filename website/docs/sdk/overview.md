# The Hephaestus SDK

If you want to run Hephaestus workflows from Python — starting services, creating tasks, monitoring progress, and shutting everything down — you use the SDK.

It's the programmatic way to control Hephaestus.

## What the SDK Does

The SDK handles the operational complexity of running a multi-agent system:

**Process Management**
- Starts the FastAPI backend server
- Starts the Guardian monitoring process
- Manages log files
- Handles graceful shutdown

**Multi-Workflow Support**
- Register multiple workflow types (bug fix, PRD builder, security audit, etc.)
- Each workflow has its own phases and configuration
- Launch workflows from the UI with dynamic forms
- Run multiple workflow executions simultaneously

**Workflow Definition**
- Loads your phase definitions
- Validates configuration
- Makes phases available to agents via MCP

**Task Orchestration**
- Creates tasks programmatically
- Tracks task status
- Monitors agent health
- Retrieves results

**Optional TUI**
- Terminal-based visual interface
- Real-time task monitoring
- Agent status visualization
- Interactive controls

## When You'd Use It

**Automation Scripts**
You want to run workflows without manual intervention:
```python
sdk = HephaestusSDK(phases=MY_PHASES)
sdk.start()
sdk.create_task("Build feature X", phase_id=1)
sdk.wait_for_completion()
sdk.shutdown()
```

**CI/CD Integration**
Run Hephaestus as part of your deployment pipeline:
```python
# In your deploy script
sdk = HephaestusSDK(phases=REVIEW_PHASES)
sdk.start()
sdk.create_task("Review PR #123", phase_id=1)
result = sdk.wait_for_result()
if result.validated:
    print("✓ Review passed")
else:
    sys.exit(1)
```

**Research Experiments**
Run multiple workflow variations programmatically:
```python
for config in experiment_configs:
    sdk = HephaestusSDK(phases=config.phases, llm_model=config.model)
    sdk.start()
    sdk.create_task(config.task)
    results.append(sdk.wait_for_completion())
    sdk.shutdown()
```

**Production Deployments**
Long-running systems that spawn workflows on-demand:
```python
sdk = HephaestusSDK(phases=PROD_PHASES)
sdk.start()

# Keep running, create tasks as needed
while True:
    if new_issue_detected():
        sdk.create_task(f"Investigate issue {issue_id}", phase_id=1)
```

## Basic Example

Here's what SDK usage looks like. You define workflow types, start Hephaestus, and let users launch workflows from the UI:

```python
from src.sdk import HephaestusSDK
from src.sdk.models import WorkflowDefinition, Phase, WorkflowConfig, LaunchTemplate, LaunchParameter

# Define your workflow phases
bug_fix_phases = [
    Phase(
        id=1,
        name="analyze",
        description="Analyze and reproduce the bug",
        done_definitions=["Bug reproduced", "Root cause identified", "Phase 2 task created"],
        working_directory=".",
    ),
    Phase(
        id=2,
        name="fix",
        description="Implement the fix",
        done_definitions=["Fix implemented", "Tests pass"],
        working_directory=".",
    ),
]

# Configure result handling
bug_fix_config = WorkflowConfig(
    has_result=True,
    result_criteria="Bug is fixed and verified",
    on_result_found="complete"
)

# Create a launch template - this generates the UI form
bug_fix_template = LaunchTemplate(
    parameters=[
        LaunchParameter(
            name="bug_description",
            label="Bug Description",
            type="textarea",
            required=True,
            description="Describe the bug - what's happening vs what should happen"
        ),
        LaunchParameter(
            name="severity",
            label="Severity",
            type="dropdown",
            required=True,
            options=["Critical", "High", "Medium", "Low"],
            default="Medium"
        ),
    ],
    phase_1_task_prompt="""Phase 1: Analyze and Reproduce Bug

**Severity:** {severity}

**Bug Description:**
{bug_description}

Your task: Reproduce this bug, identify the root cause, and create a Phase 2 fix task.
"""
)

# Bundle everything into a WorkflowDefinition
bug_fix_workflow = WorkflowDefinition(
    id="bug-fix",
    name="Bug Fix",
    description="Analyze, fix, and verify bug fixes",
    phases=bug_fix_phases,
    config=bug_fix_config,
    launch_template=bug_fix_template,  # Enables UI launching
)

# Initialize SDK with your workflow definitions
sdk = HephaestusSDK(
    workflow_definitions=[bug_fix_workflow],  # Can register multiple!
    working_directory="/path/to/project",
    main_repo_path="/path/to/project",
)

# Start services
sdk.start()

# That's it! Users can now launch workflows from the UI at http://localhost:3000
print("Hephaestus running. Launch workflows from the UI.")
print("Press Ctrl+C to stop")

try:
    while True:
        import time
        time.sleep(10)
except KeyboardInterrupt:
    print("Shutting down...")
    sdk.shutdown(graceful=True)
```

When users click "Launch Workflow" in the UI, they see a form generated from your `LaunchTemplate`. Their inputs get substituted into `{placeholders}` in the phase prompt, and the workflow begins.

## What You Get

**Headless Mode (Default)**
- Services run in background
- Logs written to `~/.hephaestus/logs/session-{timestamp}/`
- Perfect for automation and scripts

**TUI Mode**
- Visual interface with forge ASCII art
- Real-time task updates
- Interactive controls
- Use with `sdk.start(enable_tui=True)`

**Process Isolation**
- Each agent runs in its own tmux session
- Git worktree isolation prevents conflicts
- Automatic cleanup on shutdown

**Health Monitoring**
- Guardian checks agent health every 60 seconds
- Automatic interventions for stuck agents
- Self-healing capabilities

## The Two Ways to Use It

### 1. Multi-Workflow Mode (Recommended)

Register multiple workflow types and let users launch them from the UI:

```python
from example_workflows.prd_to_software.phases import PRD_PHASES, PRD_WORKFLOW_CONFIG, PRD_LAUNCH_TEMPLATE
from example_workflows.bug_fix.phases import BUG_FIX_PHASES, BUG_FIX_WORKFLOW_CONFIG, BUG_FIX_LAUNCH_TEMPLATE
from src.sdk import HephaestusSDK
from src.sdk.models import WorkflowDefinition

# Create workflow definitions
prd_workflow = WorkflowDefinition(
    id="prd-to-software",
    name="PRD to Software Builder",
    description="Build working software from a Product Requirements Document",
    phases=PRD_PHASES,
    config=PRD_WORKFLOW_CONFIG,
    launch_template=PRD_LAUNCH_TEMPLATE,
)

bug_fix_workflow = WorkflowDefinition(
    id="bug-fix",
    name="Bug Fix",
    description="Analyze, fix, and verify bugs",
    phases=BUG_FIX_PHASES,
    config=BUG_FIX_WORKFLOW_CONFIG,
    launch_template=BUG_FIX_LAUNCH_TEMPLATE,
)

# Register all workflows
sdk = HephaestusSDK(
    workflow_definitions=[prd_workflow, bug_fix_workflow],
    working_directory="/path/to/project",
    main_repo_path="/path/to/project",
)

sdk.start()
# Users launch workflows from http://localhost:3000 → Workflow Executions
```

See: `run_hephaestus_dev.py` for a complete multi-workflow setup.

### 2. Single-Workflow Mode (Legacy)

For simpler use cases or backward compatibility, you can still pass phases directly:

```python
from src.sdk import HephaestusSDK, Phase, WorkflowConfig

my_phases = [
    Phase(id=1, name="recon", description="..."),
    Phase(id=2, name="exploit", description="..."),
    Phase(id=3, name="report", description="..."),
]

my_config = WorkflowConfig(has_result=True, on_result_found="stop_all")

sdk = HephaestusSDK(
    phases=my_phases,
    workflow_config=my_config,
    working_directory="/path/to/project",
)

sdk.start()
# Create tasks programmatically
sdk.create_task("Do the thing", phase_id=1, agent_id="main-session-agent")
```

This mode doesn't support UI launching — you create tasks from code.

See: [Defining Phases](phases.md) for the complete guide.

## Configuration

The SDK accepts any configuration from `hephaestus_config.yaml` as parameters:

```python
sdk = HephaestusSDK(
    # Multi-workflow mode (recommended)
    workflow_definitions=[prd_workflow, bug_fix_workflow],

    # Or single-workflow mode (legacy)
    # phases=phases,
    # workflow_config=workflow_config,

    # LLM Configuration
    # Note: These are deprecated - use hephaestus_config.yaml instead
    # The SDK now reads LLM config from the YAML file

    # Paths
    database_path="./custom.db",
    working_directory="/path/to/project",
    project_root="/path/to/project",

    # Agent CLI Tool (optional - overrides config file)
    default_cli_tool="claude",  # Options: "claude", "opencode", "droid", "codex"

    # Git Configuration (REQUIRED for worktree isolation)
    main_repo_path="/path/to/project",
    auto_commit=True,
    conflict_resolution="newest_file_wins",

    # Server
    mcp_port=8000,
    monitoring_interval=60,

    # Task Deduplication
    task_deduplication_enabled=True,
    similarity_threshold=0.92,
)
```

**Important**: LLM configuration (provider, model, API keys) is now set in `hephaestus_config.yaml`, not via SDK parameters.

## Requirements

Before using the SDK:

**1. Configure Working Directory**
Edit `hephaestus_config.yaml`:
```yaml
paths:
  project_root: "/path/to/your/project"

git:
  main_repo_path: "/path/to/your/project"  # Must be same as project_root
```

**2. Initialize Git Repository**
```bash
cd /path/to/your/project
git init
git commit --allow-empty -m "Initial commit"
```

**3. Set Up MCP Servers**
```bash
# Qdrant MCP (for memory/RAG)
claude mcp add -s user qdrant python /path/to/qdrant_mcp_openai.py \
  -e QDRANT_URL=http://localhost:6333 \
  -e COLLECTION_NAME=hephaestus_agent_memories \
  -e OPENAI_API_KEY=$OPENAI_API_KEY

# Hephaestus MCP (for task management)
claude mcp add -s user hephaestus python /path/to/claude_mcp_client.py
```

**4. Start Required Services**
```bash
# Terminal 1: Qdrant vector store
docker run -d -p 6333:6333 qdrant/qdrant

# Terminal 2: Frontend (optional)
cd frontend && npm run dev
```

See: [Quick Start Guide](../getting-started/quick-start.md) for complete setup instructions.

## Next Steps

**Get Started**
- [Quick Start Guide](../getting-started/quick-start.md) - Build your first workflow

**Learn Phase Definition**
- [Defining Phases](phases.md) - Complete guide to Phase objects
- [Launch Templates](../features/launch-templates.md) - UI forms for workflow launching

**See Real Examples**
- [SDK Examples](examples.md) - Complete workflow setup walkthrough
- `example_workflows/prd_to_software/` - PRD to software workflow
- `example_workflows/bug_fix/` - Bug fixing workflow

**Understand the System**
- [Phases System Guide](../guides/phases-system.md) - How workflows build themselves
- [Task Deduplication](../features/task-deduplication.md) - Preventing duplicate work

## The Bottom Line

The SDK is how you programmatically control Hephaestus. You define workflow types with phases and launch templates, start services, and let users launch workflows from the UI.

Everything else — agent spawning, monitoring, Git isolation, task coordination — is handled automatically.
