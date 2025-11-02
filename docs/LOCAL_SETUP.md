## Local Setup and Update Workflow

This document captures the minimal, repeatable steps to maintain your local customizations while tracking upstream updates.

### Branch and Remote Model
- `main`: pristine, tracks `upstream/main` (original repo).
- `local/customizations`: your long‑lived branch with local changes.
- Remotes:
  - `origin`: your fork (optional).
  - `upstream`: original repository.

### Update Flow (safe and repeatable)
1) Create backups (safety tag + bundle).
2) Ensure `upstream` is configured; fetch.
3) Reset `main` to `upstream/main`.
4) Rebase `local/customizations` on top of `main`.

Use the helper script below.

```bash
# From repo root
scripts/dev/update_from_upstream.sh
```

### Rollback Options
- Switch back to safety tag: `git switch local/customizations && git reset --hard <created-tag>`
- Or restore from bundle: `git clone hephaestus-backup-<timestamp>.bundle restored && cd restored`

### Config Policy
- Track `hephaestus_config.yaml` in `local/customizations` so changes are versioned.
- Keep secrets/keys in `.env` (gitignored). The app reads API keys from env.
- Expect occasional YAML merge conflicts when upstream adds/changes keys; prefer keeping your values while adopting new upstream keys.

### Service Commands (local dev)
Use the helper to start all services for this repo:

```bash
# Starts Qdrant (via docker compose if needed), initializes DB/Qdrant, 
# launches backend server, monitor, and frontend (Vite on :5173)
scripts/dev/start_all.sh
```

Health checks:
- Backend: `curl http://localhost:8000/health`
- Qdrant: `curl http://localhost:6333/health`
- Frontend: open `http://localhost:5173/`

### Notes
- Scripts are idempotent where practical and avoid reinstalling dependencies unless missing.
- Logs are written under `logs/` (e.g., `server.out`, `monitor.out`, `frontend.out`).
