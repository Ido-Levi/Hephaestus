# Quick Start Guide

Build your first Hephaestus workflow in 10 minutes.

## What You'll Build

A simple 3-phase bug fixing workflow:
1. **Phase 1**: Reproduce the bug
2. **Phase 2**: Find the root cause
3. **Phase 3**: Implement and verify the fix

## Prerequisites

- **Claude Code** installed (AI coding assistant that agents run in)
- **tmux** installed (terminal multiplexer for agent isolation)
- **Git** (for worktree isolation - your project directory must be a git repo)
- **Python 3.10+**
- **Node.js** and **npm** (for the frontend UI)
- **Docker** (for running Qdrant vector store)
- **API Keys**: OpenAI, OpenRouter (or Anthropic - see LLM Configuration below)

## LLM Configuration

Before running workflows, configure which LLMs to use in `hephaestus_config.yaml`.

### Recommended Setup (Default)

The pre-configured `hephaestus_config.yaml` uses:
- **OpenAI** for embeddings (`text-embedding-3-large`)
- **OpenRouter** with Cerebras provider for all tasks (`gpt-oss:120b`)

This is the **recommended setup** - OpenRouter with Cerebras is extremely fast (1000+ tokens/sec), cost-effective, and performs well on most tasks.

```yaml
llm:
  embedding_model: "text-embedding-3-large"
  default_provider: "openrouter"
  default_model: "openai/gpt-oss-120b"
  default_openrouter_provider: "cerebras"  # Cerebras infrastructure for speed
```

**Required API Keys**:
```bash
# .env file
OPENAI_API_KEY=sk-...        # For embeddings
OPENROUTER_API_KEY=sk-...    # For OpenRouter (Cerebras provider)
```

### Alternative: OpenAI Only

If you prefer a single provider:

```yaml
llm:
  default_provider: "openai"
  default_model: "gpt-5"      # Or "gpt-5-mini" for cheaper option
```

**Models we recommend**:
- `gpt-oss:120b` (OpenRouter with Cerebras) - Best performance/cost, extremely fast
- `gpt-5` (OpenAI) - Strong reasoning, higher cost
- `gpt-5-mini` (OpenAI) - Faster, cheaper alternative

### Agent CLI Configuration

Agents run inside **Claude Code**. Configure which Claude model to use:

**Using Claude Code (Default)**:
```yaml
agents:
  default_cli_tool: "claude"
  cli_model: "sonnet"  # or "opus", "haiku"
```

This uses your **Anthropic subscription** through Claude Code.

**Using GLM-4.6 (Cheaper Alternative)**:
```yaml
agents:
  default_cli_tool: "claude"
  cli_model: "GLM-4.6"
  glm_api_token_env: "GLM_API_TOKEN"
```

Then set your GLM API token:
```bash
# .env file
GLM_API_TOKEN=your-glm-token
```

GLM-4.6 is significantly cheaper than Claude models while maintaining good performance.

## MCP Server Setup

Before running workflows, you need to configure the MCP servers that agents use to interact with Hephaestus and Qdrant.

### 1. Qdrant MCP Server

This gives agents access to the vector store (memory/RAG system):

```bash
claude mcp add -s user qdrant python /path/to/qdrant_mcp_openai.py \
  -e QDRANT_URL=http://localhost:6333 \
  -e COLLECTION_NAME=hephaestus_agent_memories \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e EMBEDDING_MODEL=text-embedding-3-large
```

Replace `/path/to/qdrant_mcp_openai.py` with the actual path to the script in your Hephaestus installation.

### 2. Hephaestus MCP Server

This gives agents access to task management, phase information, and workflow coordination:

```bash
claude mcp add -s user hephaestus python /path/to/claude_mcp_client.py
```

Replace `/path/to/claude_mcp_client.py` with the actual path to the script in your Hephaestus installation.

**What these MCP servers provide:**

**Qdrant MCP** gives agents:
- `qdrant_find` - Search for relevant memories using semantic search
- `qdrant_store` - Save discoveries and learnings

**Hephaestus MCP** gives agents:
- `create_task` - Spawn new tasks for any phase
- `get_tasks` - Query task status and information
- `update_task_status` - Mark tasks as done/failed
- `save_memory` - Store learnings in the knowledge base
- `get_agent_status` - Check other agents' status
- And more...

These MCP servers are configured **once per user** and will be available to all agents running in Claude Code.

## Working Directory Setup

Hephaestus needs to know where your project is located. This is the directory where agents will read files, write code, and make changes.

### 1. Create or Choose Your Project Directory

```bash
# Create a new project directory
mkdir -p ~/my_project
cd ~/my_project

# Initialize as a git repository (REQUIRED)
git init
```

**Important**: The working directory **must be a git repository**. Hephaestus uses Git worktrees to isolate agent changes and prevent conflicts.

### 2. Configure the Path in `hephaestus_config.yaml`

Edit the paths in `hephaestus_config.yaml`:

```yaml
# Paths Configuration
paths:
  database: "./hephaestus.db"
  worktree_base: "/tmp/hephaestus_worktrees"
  project_root: "/Users/yourname/my_project"  # Change this to your project path

# Git Configuration
git:
  main_repo_path: "/Users/yourname/my_project"  # Change this to match project_root
  worktree_branch_prefix: "agent-"
  auto_commit: true
  conflict_resolution: "newest_file_wins"
```

**Both paths must point to the same directory** and it must be a git repository.

### 3. Add Your PRD (Product Requirements Document)

Create a `PRD.md` file in your project directory:

```bash
cd ~/my_project
touch PRD.md
# Edit PRD.md with your project requirements
```

Hephaestus will automatically find `PRD.md` in the project root - you don't need to specify the path when running workflows.

## Step 1: Define Your Phases

Create `my_workflow/phases.py`:

```python
from src.sdk.models import Phase

PHASE_1_REPRODUCTION = Phase(
    id=1,
    name="bug_reproduction",
    description="Reproduce the reported bug and capture evidence",
    done_definitions=[
        "Bug reproduced successfully",
        "Reproduction steps documented",
        "Error logs captured",
        "Phase 2 investigation task created",
        "Task marked as done"
    ],
    working_directory=".",
    additional_notes="""
    🎯 YOUR MISSION: Confirm the bug exists

    STEP 1: Read the bug report in your task description
    STEP 2: Follow the reproduction steps
    STEP 3: Capture error messages and logs
    STEP 4: If bug confirmed: Create Phase 2 task
    STEP 5: Mark your task as done

    ✅ GOOD: "Bug reproduced. Error: 'Cannot read property of undefined' at login.js:47"
    ❌ BAD: "It crashes sometimes"
    """
)

PHASE_2_INVESTIGATION = Phase(
    id=2,
    name="root_cause_analysis",
    description="Find the root cause of the bug",
    done_definitions=[
        "Root cause identified",
        "Affected code located",
        "Fix approach proposed",
        "Phase 3 implementation task created",
        "Task marked as done"
    ],
    working_directory=".",
    additional_notes="""
    🎯 YOUR MISSION: Find WHY the bug happens

    STEP 1: Review reproduction evidence from Phase 1
    STEP 2: Trace through the code
    STEP 3: Identify the faulty code
    STEP 4: Propose a fix
    STEP 5: Create Phase 3 task with fix details
    STEP 6: Mark done
    """
)

PHASE_3_FIX = Phase(
    id=3,
    name="fix_implementation",
    description="Implement the bug fix and verify it works",
    done_definitions=[
        "Bug fix implemented",
        "Tests added to prevent regression",
        "All tests pass",
        "Bug cannot be reproduced anymore",
        "Task marked as done"
    ],
    working_directory=".",
    additional_notes="""
    🎯 YOUR MISSION: Apply the fix and verify

    STEP 1: Implement the proposed fix
    STEP 2: Add regression test
    STEP 3: Run all tests
    STEP 4: Verify bug is fixed
    STEP 5: Mark done
    """
)

BUG_FIX_PHASES = [
    PHASE_1_REPRODUCTION,
    PHASE_2_INVESTIGATION,
    PHASE_3_FIX
]
```

## Step 2: Configure the Workflow

Create `my_workflow/config.py`:

```python
from src.sdk.models import WorkflowConfig

BUG_FIX_CONFIG = WorkflowConfig(
    has_result=True,
    result_criteria="Bug is fixed and verified: cannot be reproduced, tests pass",
    on_result_found="stop_all"
)
```

## Step 3: Create the Runner Script

Create `run_bug_fix.py`:

```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import phases
from my_workflow.phases import BUG_FIX_PHASES
from my_workflow.config import BUG_FIX_CONFIG

from src.sdk import HephaestusSDK

# Load environment
load_dotenv()

def main():
    # Initialize SDK
    sdk = HephaestusSDK(
        phases=BUG_FIX_PHASES,
        workflow_config=BUG_FIX_CONFIG,
        database_path="./hephaestus.db",
        qdrant_url="http://localhost:6333",
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        working_directory=".",
        mcp_port=8000,
        monitoring_interval=60
    )

    # Start services
    print("[Hephaestus] Starting services...")
    sdk.start()

    print("[Hephaestus] Loaded phases:")
    for phase_id, phase in sorted(sdk.phases_map.items()):
        print(f"  - Phase {phase_id}: {phase.name}")

    # Create initial task
    print("\n[Task] Creating Phase 1 bug reproduction task...")
    task_id = sdk.create_task(
        description="""
        Phase 1: Reproduce Bug - "Login fails with special characters"

        Bug Report:
        - User enters password with @ symbol
        - Login button becomes unresponsive
        - Error in console: "Invalid character in auth string"

        Reproduce this bug and capture evidence.
        """,
        phase_id=1,
        priority="high",
        agent_id="main-session-agent"
    )
    print(f"[Task] Created task: {task_id}")

    # Keep running
    print("\n[Hephaestus] Workflow running. Press Ctrl+C to stop.\n")
    try:
        while True:
            import time
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[Hephaestus] Shutting down...")
        sdk.shutdown(graceful=True, timeout=10)
        print("[Hephaestus] Shutdown complete")

if __name__ == "__main__":
    main()
```

## Step 4: Run the Workflow

**Before running**, ensure you've completed the setup:
- ✅ Working directory configured in `hephaestus_config.yaml`
- ✅ Directory initialized as git repository (`git init`)
- ✅ MCP servers configured (`claude mcp list` to verify)
- ✅ API keys set in `.env` file

Start the required services:

```bash
# Terminal 1: Start Qdrant (vector store)
docker run -d -p 6333:6333 qdrant/qdrant

# Terminal 2: Start the frontend UI
cd frontend
npm install  # First time only
npm run dev

# Terminal 3: Run your workflow
python run_bug_fix.py
```

**Note**: The SDK automatically starts the Hephaestus server - you don't need to run `run_server.py` separately!

**View the workflow in action:**
Open your browser to `http://localhost:3000`. You'll see:
- **Phases Overview** - Task counts and active agents per phase
- **Task List** - Real-time updates as agents work
- **Workflow Graph** - Visual representation of task creation and dependencies
- **Trajectory Analysis** - Agent alignment scores and Guardian interventions

## Using Example Workflows

Instead of building your own workflow from scratch, you can use pre-built workflows in `example_workflows/`:

**PRD to Software Builder** (complete working example):
```bash
# Terminal 1: Start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant

# Terminal 2: Start frontend
cd frontend && npm run dev

# Terminal 3: Run the PRD workflow
python run_prd_workflow.py
```

**Note**: Make sure you have:
1. Set up your working directory path in `hephaestus_config.yaml` (see Working Directory Setup above)
2. Created a `PRD.md` file in your project directory
3. Initialized the directory as a git repository (`git init`)

The workflow will automatically find the `PRD.md` in your configured working directory.

The `run_prd_workflow.py` script shows how to:
- Initialize the SDK with pre-configured phases
- Set up Git worktree isolation
- Create the initial task
- Handle workflow lifecycle

Other example workflows:
- `example_workflows/prd_to_software/` - Full software development pipeline
- `example_workflows/crackme_solving/` - Reverse engineering workflow

See `run_prd_workflow.py` for a complete example of workflow configuration and execution.

## What Happens

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1 Agent (Reproduction)                                │
│ - Reads bug report                                          │
│ - Attempts to reproduce                                     │
│ - Captures error: "Invalid character at auth.js:47"        │
│ - Creates Phase 2 investigation task                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2 Agent (Investigation)                               │
│ - Reviews reproduction evidence                             │
│ - Traces through auth.js                                    │
│ - Finds issue: password not URL-encoded                     │
│ - Creates Phase 3 fix task                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3 Agent (Fix)                                         │
│ - Implements fix: encodeURIComponent(password)             │
│ - Adds regression test                                      │
│ - Runs tests: ALL PASS ✓                                   │
│ - Verifies bug is fixed                                     │
└─────────────────────────────────────────────────────────────┘
```

**Throughout this process:**
- **Guardian monitors** every 60 seconds
- **Steers agents** if they drift from phase instructions
- **Validates** that each phase follows its mandatory steps

## Monitoring Progress

### View Logs
```bash
tail -f logs/backend.log   # Server logs
tail -f logs/monitor.log   # Guardian logs
```

### Check Task Status
```python
# In Python console or script
from src.sdk import HephaestusSDK
sdk = HephaestusSDK(...)
tasks = sdk.get_tasks(status="in_progress")
for task in tasks:
    print(f"{task.id}: {task.description[:50]}... - {task.status}")
```

### View Agent Status
```bash
# Check active agents
curl http://localhost:8000/api/agents/status
```

## Next Steps

Now that you've built a basic workflow, try:

1. **Add Ticket Tracking**: Enable Kanban board coordination
   ```python
   config = WorkflowConfig(
       enable_tickets=True,
       board_config={...}
   )
   ```

2. **Add More Phases**: Extend to 4-5 phases for complex workflows

3. **Enable Validation**: Add automated validation criteria
   ```python
   phase = Phase(
       ...,
       validation={
           "enabled": True,
           "criteria": [...]
       }
   )
   ```

4. **Study Examples**: Explore `example_workflows/` for real-world workflow patterns

5. **Learn Best Practices**: Read [Best Practices Guide](best-practices.md) for workflow design patterns

## Troubleshooting

**Problem: Agents not spawning**
- Check logs: `tail -f logs/backend.log`
- Verify Qdrant running: `curl http://localhost:6333/health`
- Check API key in `.env`

**Problem: Guardian not steering**
- Verify monitoring interval in config
- Check `logs/monitor.log` for Guardian analysis
- Ensure phase instructions are clear and specific

**Problem: Tasks stuck**
- Check agent tmux sessions: `tmux ls`
- View agent output: `tmux attach -t agent-xxx`
- Check for errors in `logs/backend.log`

**Problem: LLM errors**
- Verify API keys in `.env` file
- Check `hephaestus_config.yaml` has correct provider/model configuration
- Review logs for authentication errors

**Problem: Agents can't access MCP tools**
- Verify MCP servers are configured: `claude mcp list`
- Check that both `hephaestus` and `qdrant` MCP servers are listed
- Re-run the MCP server setup commands if missing
- Restart Claude Code after adding MCP servers

**Problem: Git worktree errors**
- Ensure your working directory is initialized as a git repository: `git init`
- Verify paths in `hephaestus_config.yaml` point to the correct directory
- Check that `project_root` and `main_repo_path` match
- The directory must have at least one commit: `git commit --allow-empty -m "Initial commit"`

---

**Congratulations!** You've built your first Hephaestus workflow.

**Next:** Learn about [Guardian Monitoring](guardian-monitoring.md) to see how Guardian keeps workflows on track.
