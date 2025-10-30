#!/usr/bin/env python3
"""
Open Source Bug Bounty Workflow Runner

This script automates the bug bounty hunting workflow for open source projects
using the Hephaestus SDK. It spawns multiple specialized vulnerability hunters
to comprehensively test an open source project for security vulnerabilities.

Usage:
    python run_opensource_bugbounty.py [--working-dir PATH] [--tui] [--drop-db] [--resume]

Options:
    --working-dir PATH   Path to open source project directory (overrides hardcoded default)
    --tui                Enable TUI mode for interactive monitoring
    --drop-db            Drop the database before starting (removes hephaestus.db)
    --resume             Resume existing workflow (don't create new Phase 1 task)

Setup:
    The script will automatically verify the project structure and begin hunting
    for security vulnerabilities in the target open source project.
"""

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION - Change this to your open source project directory
# ═══════════════════════════════════════════════════════════════════════
DEFAULT_WORKING_DIR = "/Users/idol/hackerone_root/httpd"
# ═══════════════════════════════════════════════════════════════════════

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
from example_workflows.open_source_bug_bounty.phases import BUGBOUNTY_PHASES, BUGBOUNTY_WORKFLOW_CONFIG

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


def verify_project_setup(working_dir: Path) -> tuple[bool, str]:
    """Verify that the target project is a valid open source project."""

    # Check if directory exists
    if not working_dir.exists():
        return False, f"❌ ERROR: Project directory does not exist: {working_dir}\n\nPlease clone the open source project to this directory."

    # Look for common project files
    project_files = [
        "README.md", "README.rst", "README.txt",
        "setup.py", "pyproject.toml", "requirements.txt", "Pipfile",
        "package.json", "package-lock.json", "yarn.lock",
        "Cargo.toml", "go.mod", "composer.json",
        ".gitignore", "LICENSE", "LICENSE.md"
    ]

    found_files = []
    for file in project_files:
        if (working_dir / file).exists():
            found_files.append(file)

    if not found_files:
        return False, f"❌ ERROR: No project files found in {working_dir}\n\nThis doesn't appear to be a valid open source project directory."

    # Detect project type
    project_type = detect_project_type(working_dir, found_files)

    # Count source code files
    source_count = count_source_files(working_dir)

    if source_count < 10:
        return False, f"❌ ERROR: Very few source files found ({source_count}) in {working_dir}\n\nThis doesn't appear to be a substantial open source project."

    return True, f"{project_type} project with {source_count} source files"


def detect_project_type(working_dir: Path, files: list) -> str:
    """Detect the type of project based on files present."""

    if any(f in files for f in ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"]):
        return "Python"
    elif any(f in files for f in ["package.json", "package-lock.json", "yarn.lock"]):
        return "Node.js/JavaScript"
    elif "Cargo.toml" in files:
        return "Rust"
    elif "go.mod" in files:
        return "Go"
    elif "composer.json" in files:
        return "PHP"
    else:
        return "Unknown"


def count_source_files(working_dir: Path) -> int:
    """Count source code files in the project."""

    # Common source file extensions
    source_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
        '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala', '.r', '.m',
        '.sh', '.bash', '.zsh', '.fish', '.pl', '.lua', '.dart', '.vb', '.scala'
    }

    count = 0
    try:
        for file_path in working_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in source_extensions:
                # Skip test files and common directories
                if not any(skip in str(file_path) for skip in ['test', 'spec', 'node_modules', '.git', '__pycache__', '.venv', 'venv']):
                    count += 1
    except PermissionError:
        pass  # Skip directories we can't read

    return count


def main():
    """Run the open source bug bounty workflow."""
    parser = argparse.ArgumentParser(
        description="Run open source bug bounty workflow using Hephaestus SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    # First time setup
    git clone https://github.com/netflix/atlas.git ~/hackerone_root/atlas
    cd ~/hackerone_root/atlas

    # Run the workflow
    python run_opensource_bugbounty.py --working-dir ~/hackerone_root/atlas
        """
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        default=DEFAULT_WORKING_DIR,
        help=f"Path to open source project directory (default: {DEFAULT_WORKING_DIR})",
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
        "--resume",
        action="store_true",
        help="Resume existing workflow (don't create new Phase 1 task)",
    )
    args = parser.parse_args()

    working_dir = Path(args.working_dir).resolve()

    # Verify working directory exists
    if not working_dir.exists():
        print(f"❌ ERROR: Project directory does not exist: {working_dir}")
        print(f"\nClone the project with: git clone <repository_url> {working_dir}")
        sys.exit(1)

    # Verify project setup
    setup_ok, message = verify_project_setup(working_dir)
    if not setup_ok:
        print(message)
        sys.exit(1)

    project_info = message  # message contains project info if setup_ok

    # Print banner
    print("\n" + "=" * 70)
    print("🔍 OPEN SOURCE BUG BOUNTY HUNTER")
    print("=" * 70)
    print(f"\nWorking Directory: {working_dir}")
    print(f"Project Type: {project_info}")
    print("\nThis workflow will:")
    print("  1. Analyze the open source project structure and dependencies")
    print("  2. Identify security-critical code domains (auth, crypto, input handling, etc.)")
    print("  3. Spawn 4-6 specialized hunters for different vulnerability types")
    print("  4. Systematically discover, investigate, and exploit vulnerabilities")
    print("  5. Create professional HackerOne reports with working exploits")
    print("\n⚠️  REMINDER: Only test on authorized open source programs!")
    print("=" * 70 + "\n")

    # Step 1: Kill existing services
    kill_existing_services()

    # Step 2: Setup database path (in repo root, not working dir)
    db_path = os.getenv("DATABASE_PATH", "./hephaestus.db")
    if args.drop_db:
        drop_database(db_path)

    # Step 3: Load configuration from environment variables
    # Note: LLM_MODEL is deprecated - configuration now comes from hephaestus_config.yaml
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    mcp_port = int(os.getenv("MCP_PORT", "8000"))
    monitoring_interval = int(os.getenv("MONITORING_INTERVAL_SECONDS", "60"))

    print("[Hephaestus] Initializing SDK with open source bug bounty phases...")
    print(f"[Config] Using LLM configuration from hephaestus_config.yaml")
    print(f"[Config] Working Directory: {working_dir}")
    print(f"[Config] Database: {db_path}")

    # Step 4: Initialize SDK with Python phase objects
    try:
        sdk = HephaestusSDK(
            phases=BUGBOUNTY_PHASES,  # Use Python objects, not YAML directory
            workflow_config=BUGBOUNTY_WORKFLOW_CONFIG,  # Result handling config
            database_path=db_path,
            qdrant_url=qdrant_url,
            # LLM configuration now comes from hephaestus_config.yaml
            working_directory=str(working_dir),
            mcp_port=mcp_port,
            monitoring_interval=monitoring_interval,

            # Task deduplication to avoid duplicate work
            task_deduplication_enabled=True,
            similarity_threshold=0.89,

            # Git Configuration
            main_repo_path=str(working_dir),
            project_root=str(working_dir),
            auto_commit=True,
            conflict_resolution="newest_file_wins",
            worktree_branch_prefix="bugbounty-agent-",
        )
    except Exception as e:
        print(f"[Error] Failed to initialize SDK: {e}")
        sys.exit(1)

    # Step 4.5: If we dropped the DB, ensure schema is initialized before starting monitor
    if args.drop_db:
        print("[Database] Initializing database schema...")
        time.sleep(1)  # Give DB time to initialize schema

    # Step 5: Start services
    print("\n[Hephaestus] Starting services...")
    try:
        sdk.start(enable_tui=args.tui, timeout=30)
    except Exception as e:
        print(f"[Error] Failed to start services: {e}")
        sys.exit(1)

    # Step 6: Output log paths (only if not in TUI mode)
    if not args.tui:
        print("\n" + "=" * 60)
        print("LOG PATHS")
        print("=" * 60)
        print(f"Backend: {sdk.log_dir}/backend.log")
        print(f"Guardian: {sdk.log_dir}/monitor.log")
        print("=" * 60 + "\n")

    # Step 7: Verify phases loaded
    print(f"[Phases] Loaded {len(sdk.phases_map)} phases:")
    for phase_id, phase in sorted(sdk.phases_map.items()):
        print(f"  - Phase {phase_id}: {phase.name}")

    # Step 8: Create initial Phase 1 task (unless resuming)
    if not args.resume:
        print("\n[Task] Creating Phase 1 task...")
        try:
            task_id = sdk.create_task(
                description=f"Phase 1: Analyze the open source project structure and security domains. Map the codebase, identify security-critical components (authentication, input validation, cryptography, file operations, etc.), understand the tech stack and dependencies, and strategically spawn 4-6 Phase 2 domain specialists to systematically hunt for vulnerabilities across different code areas.",
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

        # Step 9: Verify task is in pending status
        print("[Task] Verifying task status...")
        time.sleep(2)

        try:
            task_status = sdk.get_task_status(task_id)
            print(f"[Task] Status: {task_status.status}")

            if task_status.status not in ["pending", "assigned", "in_progress"]:
                print(f"[Warning] Unexpected task status: {task_status.status}")
        except Exception as e:
            print(f"[Error] Failed to get task status: {e}")

        # Step 10: Wait for agent assignment
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
        print("\n[Resume] Resuming existing workflow (no new task created)")
        print("[Resume] Existing agents will continue working...")

    # Step 11: Print helpful information
    print("\n" + "=" * 70)
    if args.resume:
        print("🔄 WORKFLOW RESUMED!")
    else:
        print("🎯 WORKFLOW STARTED!")
    print("=" * 70)

    if not args.resume:
        print("\nPhase 1 will now:")
        print("  • Analyze project structure and dependencies")
        print("  • Identify security-critical code domains")
        print("  • Map high-risk components (auth, crypto, input handling, etc.)")
        print("  • Strategically select 4-6 security domains")
        print("  • Spawn 4-6 Phase 2 domain specialists")
    else:
        print("\nExisting agents will continue:")
        print("  • Ongoing Phase 2/3/4 tasks will proceed")
        print("  • New vulnerabilities will be investigated")
        print("  • Exploits will be developed and submitted")

    print("\nMonitor progress:")
    print(f"  • Web UI: http://localhost:{mcp_port}")
    print(f"  • Tasks: curl http://localhost:{mcp_port}/api/tasks")
    print(f"  • Results: curl http://localhost:{mcp_port}/api/results")
    print(f"  • Agents: curl http://localhost:{mcp_port}/api/agents")

    if not args.resume:
        print("\nExpected timeline:")
        print("  • Phase 2 domain specialists: 2-5 minutes")
        print("  • First vulnerability findings: 15-30 minutes")
        print("  • First exploits: 30-60 minutes (if vulnerabilities exist)")
        print("  • First HackerOne submission: 45-90 minutes")

    print("=" * 70 + "\n")

    # Step 12: If not in TUI mode, keep running until interrupted
    if not args.tui:
        print("⏸️  Press Ctrl+C to stop (agents will finish current tasks)\n")
        try:
            while True:
                time.sleep(30)
                # Poll task status periodically
                try:
                    tasks = sdk.get_tasks(status="in_progress")
                    results = sdk.get_results()
                    if tasks:
                        print(f"[Status] {len(tasks)} task(s) in progress, {len(results)} bug(s) submitted")
                except:
                    pass
        except KeyboardInterrupt:
            print("\n[Hephaestus] Received interrupt signal")

    # Shutdown
    print("\n[Hephaestus] Shutting down...")
    sdk.shutdown(graceful=True, timeout=10)
    print("[Hephaestus] ✓ Shutdown complete")

    # Print summary
    try:
        results = sdk.get_results()
        if results:
            print(f"\n🎉 Found and submitted {len(results)} bug(s) during this session!")
            print("\nCheck the results with:")
            print(f"  curl http://localhost:{mcp_port}/api/results | jq")
    except:
        pass


if __name__ == "__main__":
    main()