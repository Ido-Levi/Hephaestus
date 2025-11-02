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

Here's what SDK usage looks like:

```python
from src.sdk import HephaestusSDK, Phase, WorkflowConfig

# Define your workflow phases
phases = [
    Phase(
        id=1,
        name="analysis",
        description="Analyze the problem",
        done_definitions=["Problem understood", "Phase 2 task created"],
        working_directory=".",
    ),
    Phase(
        id=2,
        name="implementation",
        description="Implement the solution",
        done_definitions=["Solution implemented", "Tests pass"],
        working_directory=".",
    ),
]

# Configure result handling
workflow_config = WorkflowConfig(
    has_result=True,
    result_criteria="Problem is solved and verified",
    on_result_found="stop_all"
)

# Initialize SDK
sdk = HephaestusSDK(
    phases=phases,
    workflow_config=workflow_config,
    working_directory="/path/to/project",
    main_repo_path="/path/to/project",
)

# Start services
sdk.start()

# Create initial task
task_id = sdk.create_task(
    description="Fix authentication bug in login.js",
    phase_id=1,
    priority="high",
    agent_id="main-session-agent"
)

# Monitor progress
print(f"Task created: {task_id}")
print("Workflow running... Press Ctrl+C to stop")

try:
    while True:
        import time
        time.sleep(10)
except KeyboardInterrupt:
    print("Shutting down...")
    sdk.shutdown(graceful=True)
```

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

### 1. Import Existing Workflows

Use pre-built workflows from `example_workflows/`:

```python
from example_workflows.prd_to_software.phases import PRD_PHASES, PRD_WORKFLOW_CONFIG
from src.sdk import HephaestusSDK

sdk = HephaestusSDK(
    phases=PRD_PHASES,
    workflow_config=PRD_WORKFLOW_CONFIG,
    working_directory="/path/to/project",
    main_repo_path="/path/to/project",
)
```

See: `run_prd_workflow.py` for a complete example.

### 2. Define Custom Workflows

Create your own phase definitions:

```python
from src.sdk import Phase

my_phases = [
    Phase(id=1, name="recon", description="..."),
    Phase(id=2, name="exploit", description="..."),
    Phase(id=3, name="report", description="..."),
]

sdk = HephaestusSDK(phases=my_phases)
```

See: [Defining Phases](phases.md) for the complete guide.

## Configuration

The SDK accepts any configuration from `hephaestus_config.yaml` as parameters:

```python
sdk = HephaestusSDK(
    phases=phases,

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

**See Real Examples**
- [PRD to Software Workflow](examples.md) - Breakdown of run_prd_workflow.py
- `example_workflows/prd_to_software/` - Production workflow
- `example_workflows/hackerone_bug_bounty/` - Security testing workflow

**Understand the System**
- [Phases System Guide](../guides/phases-system.md) - How workflows build themselves
- [Task Deduplication](../features/task-deduplication.md) - Preventing duplicate work

## The Bottom Line

The SDK is how you programmatically control Hephaestus. You define phases, start services, create tasks, and let autonomous agents build your workflow.

Everything else — agent spawning, monitoring, Git isolation, task coordination — is handled automatically.
