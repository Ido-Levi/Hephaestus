# Mike's Hephaestus Workspace

This folder contains personal project configurations, launch scripts, and notes that are specific to my local development work. **This folder is automatically excluded from pull requests.**

## Current Active Project

**coached-data-explore** - Multi-audience data discovery platform

- **Location**: `/Users/mike/www/ai/coached-data-explore`
- **PRD**: `/Users/mike/www/ai/coached-data-explore/docs/prds/phase7-multi-audience-discovery-prd.md`
- **Status**: Active development via Hephaestus agents
- **Launch Script**: `./coached/launch.sh`

### Quick Start

To resume work on coached-data-explore:

```bash
cd /Users/mike/www/ai/hephaestus
./Mike/coached/launch.sh
```

This will:
- Clean Qdrant collections
- Drop and reinitialize database
- Bootstrap the project with Phase 1 task
- Start backend, monitor, and agent workflow

### Project Context

The coached-data-explore project is building a data discovery platform that serves multiple audiences (executives, data scientists, business analysts). We're using Hephaestus to manage the PRD-to-software workflow with autonomous agents.

**Key Learning Points:**
- Guardian (LLM monitoring) requires OpenRouter + Cerebras + gpt-oss-120b
- Single database approach: `./hephaestus.db` (no per-project databases)
- Agents need 120-second grace period to register before monitor checks
- Bootstrap creates Phase 1 task, which spawns agents for analysis

See `./coached/notes.md` for detailed progress and discoveries.

## Folder Structure

```
Mike/
├── README.md                     # This file - overview of workspace
├── coached/
│   ├── launch.sh                 # Bootstrap script for coached-data-explore
│   └── notes.md                  # Progress, discoveries, agent insights
├── configs/
│   └── hephaestus_config.local.yaml  # Local config with actual paths/keys
└── .gitkeep
```

## Important Notes

- **This folder is gitignored** - Won't accidentally commit to PRs
- **PR commands auto-clean this** - `/pr-prep` removes Mike/ before creating PR branch
- **Safe for secrets** - Can store API keys, local paths here
- **Context for new chats** - Read this when starting a new session

## Related Files

- **Main config**: `../hephaestus_config.yaml` (generic paths for repo)
- **Bootstrap script**: `../scripts/bootstrap_project.py`
- **Workflow runner**: `../run_prd_workflow.py`
- **PR commands**: `../.claude/commands/`

## Upstream PRs

When contributing fixes back to Ido's repo, use the automated workflow:

```bash
# 1. Create clean PR branch (removes Mike/ automatically)
/pr-prep fix-something

# 2. Push and create PR
/pr-create
```

This ensures no personal paths or configs leak into PRs.
