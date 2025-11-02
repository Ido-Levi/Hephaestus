# Fresh Start: New Project From a PRD (with Existing Code)

This guide shows how to start Hephaestus on a brand‑new project (or an existing repo with lots of code) using a clean database and clean/isolated memories — while keeping your frontend running on port `5173`.

Think of a “project” in Hephaestus as three things tied together:
- Working directory: the repo the agents operate on (your code + PRD)
- Database: a SQLite `*.db` holding tasks/tickets/agent state
- Memories: Qdrant collections used for RAG search and shared knowledge

If you point the system at a new working directory and start with a fresh DB and clean/isolated Qdrant collections, you have a clean slate.

---

## Prerequisites

- Hephaestus repo cloned and dependencies installed
- Qdrant running locally:

```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

- API keys exported in your shell or `.env` as needed (e.g., `OPENROUTER_API_KEY`, or `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` depending on your setup)
- Your target project directory exists, is accessible, and ideally is a git repo (agents commit on isolated worktrees)

---

## Two Ways To Kick Off A New Project

Pick the approach that fits how you like to run the system. Both keep the frontend on port `5173`.

### Option A: Use the PRD Workflow Runner (easy, self‑contained)

This script starts the backend + monitor for this session, auto‑finds your PRD, and creates the initial Phase 1 task for you.

1) Choose isolation values (recommended so projects don’t share state):

```bash
# Point Hephaestus at your existing project directory
export WORKING_DIRECTORY=/absolute/path/to/your_project

# Put the DB inside that project (or anywhere you prefer)
export DATABASE_PATH=/absolute/path/to/your_project/hephaestus_myproject.db

# Give memories a unique prefix so they don’t mix with old runs
export VECTOR_STORE_COLLECTION_PREFIX=hephaestus_myproject

# Optional: where agent worktrees are created so you can watch them
export WORKTREE_BASE=/absolute/path/to/heph-worktrees
```

2) Ensure your project is a git repo (agents use isolated worktree branches; your main branch stays clean):

```bash
cd /absolute/path/to/your_project
git init  # if not already a repo
```

3) Ensure a PRD file exists in the project root (e.g., `PRD.md`).

4) From the Hephaestus repo, start fresh and create the initial task:

```bash
cd /absolute/path/to/hephaestus
python run_prd_workflow.py --drop-db
# or explicitly: python run_prd_workflow.py --prd /absolute/path/to/your_project/PRD.md
```

5) Open the UI
- Frontend (already running): http://localhost:5173
- Backend tickets board: http://localhost:8000/tickets

The Phase 1 agent will parse your PRD, save key knowledge to memory, and spawn tickets with proper dependencies. Subsequent phases will design, implement, test, and document.

### Option B: Keep the Server Running and Create the Task via UI

If you prefer to run the backend directly (`python run_server.py`) and use the dashboard to create the first task:

1) Edit `hephaestus_config.yaml` to point at the new project:

```yaml
paths:
  project_root: /absolute/path/to/your_project
  worktree_base: /absolute/path/to/heph-worktrees   # optional but recommended

git:
  main_repo_path: /absolute/path/to/your_project

vector_store:
  collection_prefix: hephaestus_myproject            # isolate memories (recommended)
```

2) Restart backend and monitor in separate terminals:

```bash
python run_server.py
python run_monitor.py
```

3) In the UI:
- Go to Tasks → “New Task”
- Description: “Phase 1: Analyze PRD at /absolute/path/to/your_project/PRD.md …”
- Phase: `1`
- Priority: `high`
- Create. The Phase 1 agent will generate the tickets for you.

Note: Creating a ticket from the Tickets page only creates a ticket. To kick off the workflow, create a Phase 1 task (either via the runner in Option A or from the Tasks page here).

---

## Clean Start vs Shared Memories

- Clean/isolated (recommended):
  - Use a new `DATABASE_PATH` and a unique `VECTOR_STORE_COLLECTION_PREFIX` per project.
  - Optional: delete old Qdrant collections, then re‑init.

- Shared memories (advanced):
  - Keep the same Qdrant prefix so agents can reuse prior knowledge.
  - Still use a fresh DB for clean ticket/task state.

### Cleaning Qdrant (deletes all memories for the chosen prefix)

```bash
# DANGEROUS: wipes collections for the prefix used by the backend
python scripts/clean_qdrant.py --force
python scripts/init_qdrant.py
```

If you prefer not to delete old data, just pick a new `VECTOR_STORE_COLLECTION_PREFIX` and skip cleaning.

### Fresh DB

```bash
# If you are not using --drop-db with the runner
rm hephaestus.db
python scripts/init_db.py
```

---

## Where Things Are Written

- Worktrees (agent sandboxes):
  - Default: `/tmp/hephaestus_worktrees`
  - Change with `WORKTREE_BASE` or `paths.worktree_base` in `hephaestus_config.yaml`
  - Each agent uses its own branch (e.g., `agent-...`), so your main repo stays clean

- Logs:
  - `~/.hephaestus/logs/session-YYYYMMDD-HHMMSS/{backend.log,monitor.log}`
  - Startup prints the exact folder

- Database:
  - Whatever you set in `DATABASE_PATH` (default `./hephaestus.db` in repo root)

- Memories (Qdrant):
  - Collections named `<prefix>_agent_memories`, `<prefix>_project_context`, etc.
  - Prefix controlled by `VECTOR_STORE_COLLECTION_PREFIX` or `vector_store.collection_prefix`

---

## “Exact Recipe” For Your Case (existing repo + PRD + keep UI on 5173)

1) Keep your frontend on port `5173` — nothing changes there.
2) Choose clean isolation:

```bash
export WORKING_DIRECTORY=/absolute/path/to/your_project
export DATABASE_PATH=/absolute/path/to/your_project/hephaestus_myproject.db
export VECTOR_STORE_COLLECTION_PREFIX=hephaestus_myproject
export WORKTREE_BASE=/absolute/path/to/heph-worktrees
```

3) Ensure your repo has a `PRD.md` in its root, and is a git repo (`git init` if needed).
4) Start fresh and kick off Phase 1:

```bash
cd /absolute/path/to/hephaestus
python run_prd_workflow.py --drop-db
# or: python run_prd_workflow.py --prd /absolute/path/to/your_project/PRD.md
```

5) Watch it work:
- Tickets board: http://localhost:8000/tickets
- Frontend app:  http://localhost:5173

That’s it — you now have a clean project. Phase 1 reads your PRD, produces tickets with dependencies, and subsequent phases build, test, and document.

---

## Troubleshooting Tips

- Backend won’t start? Check Qdrant: `curl http://localhost:6333/collections`
- No PRD found? Pass `--prd /path/to/PRD.md` to the runner, or fix `WORKING_DIRECTORY`.
- Want to see what agents are doing? Tail logs in `~/.hephaestus/logs/session-*/`.
- Not seeing commits in your repo? Look in the `WORKTREE_BASE` location (agents work in isolated branches).

---

## References (in this repo)

- `run_prd_workflow.py` — PRD runner that starts services and seeds the first task
- `scripts/init_db.py` — (re)create database tables
- `scripts/clean_qdrant.py` — wipe Qdrant collections for a prefix (dangerous)
- `scripts/init_qdrant.py` — reinitialize Qdrant collections
- `hephaestus_config.yaml` — persistent config if you run `run_server.py` directly
- `src/sdk/config.py` — how env/config are passed through to the backend

