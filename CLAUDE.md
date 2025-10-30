# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Writing Phase YAML Files

### Critical YAML Formatting Rules

When creating phase definition YAML files for Hephaestus workflows, follow these guidelines to avoid parsing errors:

#### 1. **Quote Special Lines in Lists**
Any list item containing colons or starting with keywords needs quotes:
```yaml
# ❌ BAD - Will cause parsing errors:
Done_Definitions:
  - Task completed: All tests pass
  - If condition: Do something
  - CRITICAL: Important note

# ✅ GOOD - Properly quoted:
Done_Definitions:
  - "Task completed: All tests pass"
  - "If condition: Do something"
  - "CRITICAL: Important note"
```

#### 2. **File Naming Convention**
- Pattern: `XX_phase_name.yaml` (e.g., `01_planning.yaml`)
- Always use two-digit prefixes (01, 02, 03...)
- Use underscores, not hyphens

#### 3. **Be Concise but Clear**
- Keep descriptions focused and actionable
- Avoid lengthy philosophical explanations
- Use bullet points for clarity
- Each phase should have a single, clear purpose

#### 4. **Multi-line Text Formatting**
Use pipe (`|`) for multi-line content to preserve formatting:
```yaml
Additional_Notes: |
  First instruction here
  Second instruction here
  - Bullet points work too
  - Keep formatting intact
```

#### 5. **Required Fields**
Every phase YAML must include:
- `description`: Brief explanation of phase purpose
- `Done_Definitions`: Clear completion criteria
- `working_directory`: Where the agent operates
- `Additional_Notes`: Key instructions for the agent
- `Outputs`: What this phase produces
- `Next_Steps`: What should happen after

#### 6. **Writing Clear Instructions**
```yaml
# ❌ AVOID - Too vague:
Additional_Notes: |
  Do the task and create next tasks

# ✅ BETTER - Specific and actionable:
Additional_Notes: |
  MANDATORY: Create Phase 2 task with:
  - Description starting with "Phase 2:"
  - Include phase_id=2
  - Reference files created in this phase
```

#### 7. **Validation Sections**
During development, comment out validation if not ready:
```yaml
#validation:
#  enabled: true
#  criteria:
#    - description: "File exists"
#      check_type: "file_exists"
```

### Common Pitfalls to Avoid

- **Unquoted colons**: Always quote strings containing `:` in lists
- **Missing phase_id**: Every task creation must specify phase_id
- **Overly complex descriptions**: Keep it simple and direct
- **Forgetting pipes**: Use `|` for multi-line Additional_Notes
- **Inconsistent formatting**: Maintain consistent indentation

## Documentation Structure

**IMPORTANT: Before implementing any feature or making changes, check the relevant documentation:**

- `docs/` - All documentation (see `docs/README.md` for navigation guide)
  - `docs/core/` - Core system architecture
  - `docs/features/` - Advanced features
  - `docs/sdk/` - Python SDK documentation
  - `docs/workflows/` - Workflow guides
  - `docs/design/` - Future plans and design specs
- `design_docs/` - Original design specifications (being consolidated into docs/design/)

When working on the codebase:
1. **Before starting**: Check if documentation exists for the feature/system you're working on
2. **Use existing docs**: Follow the patterns and specifications outlined in the documentation
3. **After changes**: Update relevant documentation to reflect your modifications
4. **New features**: Create appropriate documentation following existing patterns

## System Overview

Hephaestus is an autonomous AI agent orchestration system that manages multiple AI agents for complex tasks. It uses:
- **FastAPI** server with MCP (Model Context Protocol) for agent communication
- **SQLite** for relational data, **Qdrant** for vector storage (RAG)
- **tmux** sessions for agent isolation
- **LLM providers** (OpenAI/Anthropic) for task enrichment and monitoring

## Architecture

The codebase follows this structure:
- `src/core/` - Core configuration and database models
- `src/agents/` - Agent management and lifecycle
- `src/memory/` - RAG system and vector store
- `src/mcp/` - MCP server implementation
- `src/monitoring/` - Agent monitoring and self-healing
- `frontend/` - React frontend with Vite

### Recent Architectural Enhancements

The system includes several advanced features (see documentation for details):

1. **Git Worktree Isolation** (`docs/core/worktree-isolation.md`)
   - Provides isolated workspace environments for agents
   - Enables parallel task execution without conflicts
   - Automatic branch management and commit isolation

2. **Validation Agent System** (`docs/core/validation-system.md`)
   - Quality control layer for task completion verification
   - Automated validation of agent outputs
   - Integration with task lifecycle management

3. **Results Reporting Systems**
   - Task Results (`docs/features/task-results.md`) - Task-level result reporting
   - Workflow Results (`docs/features/workflow-results.md`) - Workflow-level solution submission
   - Comprehensive reporting with validation integration

4. **Trajectory Monitoring** (`docs/core/monitoring-architecture.md` & `docs/features/trajectory-monitoring.md`)
   - Advanced agent behavior monitoring
   - Real-time trajectory analysis using Guardian and Conductor agents
   - Self-healing capabilities with LLM-powered interventions
   - Pattern detection and anomaly identification

## Development Commands

### Backend (Python)

```bash
# Install dependencies (using Poetry or pip)
poetry install  # If Poetry is installed
pip install -r requirements.txt  # Alternative

# Start services
docker run -p 6333:6333 qdrant/qdrant  # Start Qdrant
python scripts/init_db.py  # Initialize SQLite database
python scripts/init_qdrant.py  # Initialize vector store
python run_server.py  # Start MCP server (port 8000)
python run_monitor.py  # Start monitoring loop (separate terminal)

# Testing
pytest  # Run all tests
pytest tests/test_mcp_server.py  # Run specific test
pytest --cov=src  # Run with coverage

# Code quality
black src/  # Format code
flake8 src/  # Lint code
mypy src/  # Type checking
```

### Frontend (React)

```bash
cd frontend
npm install  # Install dependencies
npm run dev  # Start development server
npm run build  # Build for production
npm run type-check  # TypeScript checking
```

### Docker

```bash
docker-compose up -d  # Start all services
docker-compose logs -f  # View logs
docker-compose down  # Stop services
```

## Key Implementation Details

### Task Creation Flow
1. Agent calls `/create_task` endpoint with description
2. System retrieves relevant memories from Qdrant using RAG
3. LLM enriches task with specifications based on context
4. New agent spawned in tmux session with task assignment
5. Task and agent IDs returned to caller

### Agent Lifecycle
- Agents are created per task and terminated on completion
- Health monitored every 60 seconds via monitoring loop
- Stuck agents receive LLM-powered interventions (nudge/restart/recreate)
- All agent output logged to database

### Monitoring System
The monitoring architecture includes two specialized AI agents:
- **Guardian Agent**: Monitors individual agent health and behavior
  - Analyzes agent trajectories and output patterns
  - Provides targeted interventions for stuck agents
  - Uses LLM to craft context-aware nudges
- **Conductor Agent**: Oversees system-wide coordination
  - Detects and eliminates duplicate work between agents
  - Assesses overall system coherence
  - Makes termination decisions for duplicate agents
  - Note: The coordination_needs feature is currently disabled in prompts but all handling logic remains intact in the codebase for future activation

### Memory System
- Uses Qdrant vector database with multiple collections
- Memory types: `error_fix`, `discovery`, `decision`, `learning`, `warning`, `codebase_knowledge`
- Semantic search provides context for new tasks
- Automatic deduplication prevents redundant memories

### MCP Integration
The server implements MCP protocol for Claude Code integration:
- Health check: `mcp__hephaestus__health_check`
- Create task: `mcp__hephaestus__create_task`
- Get tasks: `mcp__hephaestus__get_tasks`
- Save memory: `mcp__hephaestus__save_memory`
- Update task status: `mcp__hephaestus__update_task_status`
- Get agent status: `mcp__hephaestus__get_agent_status`
- Validation review: `mcp__hephaestus__give_validation_review` (for validator agents)

## Configuration

Set these environment variables in `.env`:
```bash
LLM_PROVIDER=openai  # or "anthropic"
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=gpt-4-turbo-preview
DATABASE_PATH=./hephaestus.db
QDRANT_URL=http://localhost:6333
MCP_PORT=8000
MONITORING_INTERVAL_SECONDS=60
```

## Testing Approach

The project uses pytest with async support. Test files are in `tests/` directory:
- Unit tests for individual components
- Integration tests for MCP flow (`tests/mcp_integration/`)
- Use `pytest-asyncio` for async testing
- Mock external services (LLM, Qdrant) in tests

## Important Patterns

### Database Sessions
Uses SQLAlchemy with session management:
```python
from src.core.database import get_db
with get_db() as db:
    # Database operations
```

### Async Operations
Most server endpoints are async:
```python
async def endpoint():
    # Use await for async calls
```

### Error Handling
Consistent error handling with try/except blocks and proper logging using `structlog`.

### LLM Provider Interface
Abstract interface allows swapping between OpenAI/Anthropic:
```python
from src.interfaces.llm_provider import get_llm_provider
provider = get_llm_provider()
```

## Available Documentation

### Design Documents (`design_docs/`)
- `00_implementation_roadmap.md` - Overall implementation strategy and phases
- `01_git_worktree_isolation.md` - Git worktree system design
- `02_validation_agent_system.md` - Validation agent architecture
- `03_results_reporting_system.md` - Results reporting design
- `agent_trajectory_monitoring_system.md` - Trajectory monitoring design

### Implementation Documentation (`docs/`)
- `MONITORING_ARCHITECTURE.md` - Complete monitoring system architecture
- `TRAJECTORY_MONITORING_SYSTEM.md` - Trajectory monitoring specifications
- `TRAJECTORY_MONITORING_IMPLEMENTATION.md` - Implementation details
- `worktree-isolation-system.md` - Worktree isolation implementation
- `validation-system.md` - Validation system implementation
- `results-reporting-system.md` - Results reporting implementation