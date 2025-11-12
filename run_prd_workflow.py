#!/usr/bin/env python3
"""
PRD to Software Builder Workflow Runner

This script automates the PRD to Software Builder workflow using the Hephaestus SDK.
It handles cleanup, initialization, and task creation without human intervention.

The workflow takes a PRD (Product Requirements Document) and builds working software.
It's fully generic and works for any type of software project: web apps, CLIs, libraries,
microservices, mobile backends, etc.

Usage:
    python run_prd_workflow.py [--tui] [--drop-db] [--prd PATH] [--resume]

Options:
    --tui         Enable TUI mode for interactive monitoring
    --drop-db     Drop the database before starting (removes hephaestus.db)
    --prd PATH    Path to PRD file (default: looks for PRD.md, REQUIREMENTS.md, README.md)
    --resume      Resume existing workflow (don't create initial task)
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Import from example_workflows
sys.path.insert(0, str(Path(__file__).parent))
from example_workflows.prd_to_software.phases import PRD_PHASES, PRD_WORKFLOW_CONFIG

from src.sdk import HephaestusSDK

# Load environment variables from .env file
load_dotenv()


def kill_existing_services():
    """Kill any existing Hephaestus services and processes on port 8000."""
    print("[Cleanup] Killing existing services...")

    # Kill processes on port 8000
    try:
        result = subprocess.run(
            ["lsof", "-ti", ":8000"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"  Killed process on port 8000 (PID: {pid})")
                except ProcessLookupError:
                    pass
    except Exception as e:
        print(f"  Warning: Could not kill processes on port 8000: {e}")

    # Kill guardian processes
    try:
        result = subprocess.run(
            ["pgrep", "-f", "run_monitor.py"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"  Killed guardian process (PID: {pid})")
                except ProcessLookupError:
                    pass
    except Exception as e:
        print(f"  Warning: Could not kill guardian processes: {e}")

    # Give processes time to die
    time.sleep(1)
    print("[Cleanup] ✓ Cleanup complete")


def drop_database(db_path: str):
    """Remove the database file if it exists."""
    db_file = Path(db_path)
    if db_file.exists():
        print(f"[Database] Dropping database: {db_path}")
        db_file.unlink()
        print("[Database] ✓ Database dropped")
    else:
        print(f"[Database] No database found at {db_path}")


def find_prd_file(working_dir: str, specified_path: str = None) -> str:
    """Find the PRD file in the working directory."""
    if specified_path:
        prd_path = Path(specified_path)
        if prd_path.exists():
            print(f"[PRD] Using specified PRD file: {specified_path}")
            return str(prd_path.absolute())
        else:
            print(f"[Error] Specified PRD file not found: {specified_path}")
            sys.exit(1)

    # Look for common PRD file names
    working_path = Path(working_dir)
    candidates = [
        "PRD.md",
        "prd.md",
        "REQUIREMENTS.md",
        "requirements.md",
        "SPEC.md",
        "spec.md",
        "README.md",
    ]

    for candidate in candidates:
        prd_path = working_path / candidate
        if prd_path.exists():
            print(f"[PRD] Found PRD file: {candidate}")
            return str(prd_path.absolute())

    print("[Error] No PRD file found. Looked for:")
    for candidate in candidates:
        print(f"  - {candidate}")
    print("\nSpecify PRD location with --prd flag")
    sys.exit(1)


def main():
    """Run the PRD to Software Builder workflow."""
    parser = argparse.ArgumentParser(
        description="Build software from PRD using Hephaestus SDK"
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Enable TUI mode for interactive monitoring",
    )
    parser.add_argument(
        "--drop-db",
        action="store_true",
        help="Drop the database before starting",
    )
    parser.add_argument(
        "--prd",
        type=str,
        help="Path to PRD file (default: auto-detect)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume existing workflow without creating initial task",
    )
    args = parser.parse_args()

    # Step 1: Kill existing services
    kill_existing_services()

    # Step 2: Drop database if requested
    db_path = os.getenv("DATABASE_PATH", "./hephaestus.db")
    if args.drop_db:
        drop_database(db_path)

    # Step 3: Load configuration from environment variables
    # Note: LLM_MODEL is deprecated - configuration now comes from hephaestus_config.yaml
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    mcp_port = int(os.getenv("MCP_PORT", "8000"))
    monitoring_interval = int(os.getenv("MONITORING_INTERVAL_SECONDS", "60"))
    working_directory = os.getenv(
        "WORKING_DIRECTORY",
        "/Users/idol/hephaestus_prd_tester/url_shortener_v2"  # Default to URL shortener project
    )

    # Step 4: Find PRD file (skip if resuming)
    if not args.resume:
        prd_file = find_prd_file(working_directory, args.prd)
    else:
        prd_file = None

    print("[Hephaestus] Initializing SDK with PRD to Software Builder phases...")
    print(f"[Config] Using LLM configuration from hephaestus_config.yaml")
    print(f"[Config] Working Directory: {working_directory}")
    if prd_file:
        print(f"[Config] PRD File: {prd_file}")
    if args.resume:
        print(f"[Config] Mode: Resume (no initial task will be created)")

    # Step 5: Initialize SDK with Python phase objects
    try:
        sdk = HephaestusSDK(
            phases=PRD_PHASES,  # Use Python objects
            workflow_config=PRD_WORKFLOW_CONFIG,  # Result handling config
            database_path=db_path,
            qdrant_url=qdrant_url,
            llm_provider="openai",
            llm_model="gpt-oss-120b",
            # LLM configuration now comes from hephaestus_config.yaml
            working_directory=working_directory,
            mcp_port=mcp_port,
            monitoring_interval=monitoring_interval,

            # Git Configuration
            main_repo_path=working_directory,
            project_root=working_directory,
            auto_commit=True,
            conflict_resolution="newest_file_wins",
            worktree_branch_prefix="prd-builder-",
        )
    except Exception as e:
        print(f"[Error] Failed to initialize SDK: {e}")
        sys.exit(1)

    # Step 6: Start services
    print("[Hephaestus] Starting services...")
    try:
        sdk.start(enable_tui=args.tui, timeout=30)
    except Exception as e:
        print(f"[Error] Failed to start services: {e}")
        sys.exit(1)

    # Step 7: Output log paths (only if not in TUI mode)
    if not args.tui:
        print("\n" + "=" * 60)
        print("LOG PATHS")
        print("=" * 60)
        print(f"Backend: {sdk.log_dir}/backend.log")
        print(f"Guardian: {sdk.log_dir}/monitor.log")
        print("=" * 60 + "\n")

    # Step 8: Verify phases loaded
    print(f"[Phases] Loaded {len(sdk.phases_map)} phases:")
    for phase_id, phase in sorted(sdk.phases_map.items()):
        print(f"  - Phase {phase_id}: {phase.name}")

    # Step 9: Create initial Phase 1 task (unless resuming)
    if not args.resume:
        print("\n[Task] Creating Phase 1 task...")
        print(f"[Task] PRD Location: {prd_file}")
        try:
            task_id = sdk.create_task(
                description=f"Analyze PRD at {prd_file}.",
                phase_id=1,
                priority="high",
                agent_id="main-session-agent",
            )
            print(f"[Task] ✓ Created task: {task_id}")
        except Exception as e:
            print(f"[Error] Failed to create task: {e}")
            print(f"[Error] Exception details: {type(e).__name__}: {str(e)}")
            sdk.shutdown()
            sys.exit(1)

        # Step 10: Verify task is in pending status
        print("[Task] Verifying task status...")
        time.sleep(2)

        try:
            task_status = sdk.get_task_status(task_id)
            print(f"[Task] Status: {task_status.status}")

            if task_status.status not in ["pending", "assigned", "in_progress"]:
                print(f"[Warning] Unexpected task status: {task_status.status}")
        except Exception as e:
            print(f"[Error] Failed to get task status: {e}")

        # Step 11: Wait for agent assignment
        print("[Agent] Waiting for agent assignment...")
        time.sleep(5)

        try:
            task_status = sdk.get_task_status(task_id)
            if task_status.agent_id:
                print(f"[Agent] ✓ Agent assigned: {task_status.agent_id}")
            else:
                print("[Agent] Waiting for agent assignment...")
        except Exception as e:
            print(f"[Error] Failed to check agent: {e}")
    else:
        print("\n[Resume] Skipping initial task creation")
        print("[Resume] Existing workflow will continue running")

    # Step 12: If not in TUI mode, keep running until interrupted
    if not args.tui:
        print("\n[Hephaestus] Workflow running. Press Ctrl+C to stop.\n")
        if not args.resume:
            print("[Info] The workflow will:")
            print("  1. Parse the PRD and identify components")
            print("  2. Create Kanban tickets for each component")
            print("  3. Design each component in parallel (Phase 2)")
            print("  4. Implement each component (Phase 3)")
            print("  5. Test each component (Phase 4)")
            print("  6. Document the system (Phase 5)")
            print("  7. Submit final result when complete")
            print("\n[Kanban Board] Track progress at http://localhost:8000/tickets or http://localhost:3001/")
            print("  - View components moving through: Backlog → Design → Implementation → Testing → Documentation → Done")
        else:
            print("[Info] Resuming existing workflow")
            print("  - No new initial task created")
            print("  - Existing agents will continue their work")
            print("  - New tasks can be created via MCP or existing agents")
        print("\nMonitor progress in the logs or use --tui for visual monitoring\n")

        try:
            while True:
                time.sleep(10)
                # Poll task status periodically
                try:
                    tasks = sdk.get_tasks(status="in_progress")
                    if tasks:
                        print(f"[Status] {len(tasks)} task(s) in progress...")
                except:
                    pass
        except KeyboardInterrupt:
            print("\n[Hephaestus] Received interrupt signal")

    # Shutdown
    print("\n[Hephaestus] Shutting down...")
    sdk.shutdown(graceful=True, timeout=10)
    print("[Hephaestus] ✓ Shutdown complete")


if __name__ == "__main__":
    main()
