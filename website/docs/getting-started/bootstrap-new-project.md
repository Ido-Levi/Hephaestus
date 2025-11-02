# Bootstrapping a New Project

Learn how to initialize Hephaestus for a new project with a single command.

## Prerequisites

- Qdrant running locally (port 6333)
- Target project is a git repository
- PRD document exists in your project

## Quick Start

```bash
cd /path/to/hephaestus

python scripts/bootstrap_project.py \
  --working-dir "./your_project" \
  --worktrees "/tmp/hephaestus_worktrees" \
  --prd "./your_project/PRD.md" \
  --drop-db
```

## What It Does

1. Initializes SQLite database
2. Sets up Qdrant collections
3. Creates git worktree structure
4. Starts backend and monitor services
5. Creates initial Phase 1 analysis task
6. Performs health checks

## Parameters

- `--working-dir`: Path to your project directory (must be git repo)
- `--worktrees`: Where to create isolated agent worktrees
- `--prd`: Path to your PRD document
- `--drop-db`: (Optional) Drop existing database for fresh start

## After Bootstrap

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Tickets board: http://localhost:8000/tickets

The Phase 1 agent will automatically analyze your PRD and create tickets with proper dependencies.
