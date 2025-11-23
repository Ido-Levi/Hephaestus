# Hephaestus Dev

Hephaestus Dev is a ready-to-use development tool that comes with 5 pre-built workflows for common software development tasks. It's the fastest way to start using Hephaestus productively.

## Prerequisites

Before running Hephaestus Dev, complete the setup in the [Quick Start Guide](./quick-start.md):

- API keys configured in `.env`
- MCP servers set up (Hephaestus + Qdrant)
- Docker running with Qdrant container
- Frontend dependencies installed

## Running Hephaestus Dev

Start with a single command:

```bash
python run_hephaestus_dev.py --path /path/to/project
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--path PATH` | Project directory path (prompts if not provided) |
| `--drop-db` | Drop the database before starting (fresh start) |

### What Happens

1. **Checks sub-agents** - Copies required agents to `~/.claude/agents/` if missing
2. **Prompts for project path** - Where to create/use your project
3. **Sets up project** - Creates directory, copies example PRD, initializes git
4. **Starts Hephaestus** - Backend server, Guardian monitor, and registers all workflows
5. **Ready for UI** - Open http://localhost:3000 to launch workflows

## Available Workflows

| Workflow | Description | Use When |
|----------|-------------|----------|
| **PRD to Software Builder** | Build complete software from a Product Requirements Document | Starting a new project from requirements |
| **Bug Fix** | Analyze, fix, and verify bugs systematically | You have a bug to fix with clear reproduction steps |
| **Index Repository** | Scan and index a codebase to build knowledge in memory | Before other workflows, to give agents context |
| **Feature Development** | Add features to existing codebases following patterns | Adding functionality to an existing project |
| **Documentation Generation** | Generate comprehensive docs for existing codebases | Creating or updating project documentation |

## Launching a Workflow

1. Open **http://localhost:3000**
2. Navigate to **Workflow Executions**
3. Click **Launch Workflow**
4. Select a workflow from the dropdown
5. Fill in the form fields
6. Click **Launch**

The workflow starts immediately with agents working in parallel where possible.

## Recommended Workflow Order

:::tip Start with Index Repository
We recommend running **Index Repository** at least once for any existing project. This builds codebase knowledge in Qdrant that all other workflows can leverage, giving agents rich context about your code's structure, patterns, and conventions.
:::

For best results on an existing codebase:

```
1. Index Repository    → Builds codebase knowledge (run this first!)
2. Feature Development → Uses indexed knowledge for context
3. Documentation Gen   → Documents what was built
```

For a brand new project:

```
1. PRD to Software     → Builds from requirements
2. Index Repository    → Index what was built for future workflows
3. Bug Fix             → Fix issues as they arise
4. Documentation Gen   → Document the final product
```

## Monitoring Progress

- **Dashboard**: http://localhost:3000 - Overview of all activity
- **Workflow Executions**: Track running workflows
- **Tickets**: Kanban board showing work items
- **Agents**: See active agents and their status
- **Observability**: Watch agents work in real-time

## Next Steps

- [Quick Start Guide](./quick-start.md) - Full setup instructions
- [SDK Overview](../sdk/overview.md) - Create custom workflows
- [Launch Templates](../features/launch-templates.md) - Customize workflow forms
