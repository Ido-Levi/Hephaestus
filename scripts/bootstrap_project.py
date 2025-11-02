#!/usr/bin/env python3
"""Bootstrap a fresh Hephaestus project and create the Phase 1 task.

What this script does:
- Optionally wipe Qdrant memories (for a truly clean slate)
- Reinitialize Qdrant collections
- Start backend + monitor via run_prd_workflow.py
- Poll backend health
- Programmatically create the Phase 1 task against your PRD

Usage example:

  .venv/bin/python scripts/bootstrap_project.py \
    --working-dir "/abs/path/to/project" \
    --worktrees "/tmp/hephaestus_worktrees" \
    --prd "/abs/path/to/project/PRD.md" \
    --drop-db --clean-qdrant

Requirements:
- Qdrant running on localhost:6333
- Run from the Hephaestus repo root
- Use the project virtualenv (e.g., .venv/bin/python)

Note: Uses default database (./hephaestus.db) for simplicity.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict

import requests


def run(cmd: list[str], env: Dict[str, str] | None = None) -> int:
    """Run a command to completion, return exit code."""
    print("$", " ".join(cmd))
    return subprocess.call(cmd, env=env)


def spawn(cmd: list[str], env: Dict[str, str] | None = None) -> subprocess.Popen:
    """Spawn a long-running process without waiting for completion."""
    print("$ (spawn)", " ".join(cmd))
    return subprocess.Popen(cmd, env=env)


def ensure_qdrant() -> None:
    """Check Qdrant health; raise if not reachable."""
    try:
        r = requests.get("http://127.0.0.1:6333/", timeout=3)
        if r.status_code != 200:
            raise RuntimeError(
                f"Qdrant returned status {r.status_code}. Start it with:\n"
                "  docker run -d -p 6333:6333 qdrant/qdrant"
            )
    except Exception as e:
        raise RuntimeError(
            "Qdrant is not reachable on http://127.0.0.1:6333.\n"
            "Start it with: docker run -d -p 6333:6333 qdrant/qdrant"
        ) from e


def poll_backend(timeout: int = 60, base_url: str = "http://127.0.0.1:8000") -> None:
    """Wait until backend /health is healthy or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{base_url}/health", timeout=2)
            if r.ok and r.json().get("status") == "healthy":
                print("[health] Backend is healthy ✓")
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("Backend did not become healthy within timeout")


def create_phase1_task(
    prd_path: str,
    project_name: str,
    base_url: str = "http://127.0.0.1:8000",
    agent_id: str = "main-session-agent",
) -> None:
    """Create the Phase 1 task programmatically."""
    description = (
        "Phase 1: Analyze PRD at "
        f"{prd_path} for {project_name}. "
        "Extract functional and non-functional requirements, identify components, "
        "map dependencies with proper blocking relationships, create infrastructure "
        "tickets first, save key decisions/warnings to memory, and create Phase 2 "
        "Plan & Implementation tasks (one per component)."
    )

    done_definition = "\n".join(
        [
            "- PRD document located and thoroughly analyzed",
            "- Functional requirements extracted and documented",
            "- Non-functional requirements identified (performance, security, etc.)",
            "- Infrastructure needs identified and infra tickets created first (no blockers)",
            "- Implementation order and dependencies determined",
            "- System components identified and categorized",
            "- Dependencies between components mapped with blocking relationships",
            "- Success criteria defined",
            "- ONE Phase 2 Plan & Implementation task created for EVERY ticket (1:1)",
            "- All key requirements/decisions saved to memory for the hive mind",
        ]
    )

    payload = {
        "task_description": description,
        "done_definition": done_definition,
        "ai_agent_id": agent_id,
        "phase_id": "1",
        "priority": "high",
    }
    headers = {"Content-Type": "application/json", "X-Agent-ID": agent_id}

    r = requests.post(f"{base_url}/create_task", json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    print("[task] Created Phase 1 task:")
    print("       id:", data.get("task_id"))
    print("       status:", data.get("status"))
    print("       agent:", data.get("assigned_agent_id"))
    print("→ View tasks:    ", f"{base_url}/api/tasks")
    print("→ Tickets board: ", f"{base_url}/tickets")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap a fresh project and seed Phase 1 task")
    parser.add_argument("--working-dir", required=True, help="Absolute path to project directory")
    parser.add_argument("--worktrees", required=True, help="Path for git worktrees (e.g., /tmp/hephaestus_worktrees)")
    parser.add_argument("--prd", required=True, help="Absolute path to PRD file")
    parser.add_argument("--clean-qdrant", action="store_true", help="Clean Qdrant collections before starting")
    parser.add_argument("--drop-db", action="store_true", help="Drop database before starting")
    parser.add_argument("--mcp-port", default="8000", help="MCP server port (default: 8000)")
    args = parser.parse_args()

    # Sanity checks
    prd_path = Path(args.prd)
    if not prd_path.exists():
        raise SystemExit(f"PRD not found: {prd_path}")

    Path(args.worktrees).mkdir(parents=True, exist_ok=True)

    # 1) Ensure Qdrant is reachable
    ensure_qdrant()

    # 2) Clean and reinit Qdrant collections (optional)
    if args.clean_qdrant:
        code = run([sys.executable, "scripts/clean_qdrant.py", "--force", "--prefix", "hephaestus"])
        if code != 0:
            raise SystemExit("Failed to clean Qdrant collections")
    code = run([sys.executable, "scripts/init_qdrant.py"])
    if code != 0:
        raise SystemExit("Failed to initialize Qdrant collections")

    # 3) Start services via run_prd_workflow.py in resume mode
    # Note: Uses default database (./hephaestus.db) for simplicity
    env = os.environ.copy()
    env.update(
        {
            "WORKING_DIRECTORY": args.working_dir,
            "WORKTREE_BASE": args.worktrees,
            "MCP_PORT": str(args.mcp_port),
        }
    )

    run_args = [sys.executable, "run_prd_workflow.py", "--resume"]
    if args.drop_db:
        run_args.append("--drop-db")
    # Start and wait for it to report healthy
    # Spawn in background (run_prd_workflow keeps the services running)
    proc = spawn(run_args, env=env)

    # 4) Poll backend health and create Phase 1 task
    base_url = f"http://127.0.0.1:{args.mcp_port}"
    poll_backend(timeout=60, base_url=base_url)

    project_name = Path(args.working_dir).name.replace("-", "_")
    create_phase1_task(str(prd_path), project_name, base_url=base_url)

    print("\n[ok] Services are running in the spawned process.")
    print("     To stop them, Ctrl+C in that terminal, or kill the PID:")
    print(f"     PID: {proc.pid}")


if __name__ == "__main__":
    main()
