#!/usr/bin/env python3
"""
Hephaestus Quick Example Runner

This script sets up a quick example project and runs the PRD to Software Builder workflow.
It creates a project directory, copies the example PRD, initializes git, and starts Hephaestus.

Usage:
    python run_example.py [--drop-db] [--path PATH]

Options:
    --drop-db     Drop the database before starting (removes hephaestus.db)
    --path PATH   Path where to create the example project (prompts if not provided)
"""

import argparse
import os
import signal
import subprocess
import sys
import time
import yaml
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


def get_project_path(specified_path: str = None) -> str:
    """Get the project path from user input or argument."""
    if specified_path:
        project_path = Path(specified_path)
        return str(project_path.absolute())

    # Get current working directory as default
    default_path = str(Path.cwd() / "hephaestus-example")

    while True:
        user_input = input(f"[Setup] Enter project path (default: {default_path}): ").strip()

        if not user_input:
            project_path = Path(default_path)
        else:
            project_path = Path(user_input)

        # Check if directory exists and has content
        if project_path.exists() and any(project_path.iterdir()):
            print(f"[Warning] Directory '{project_path}' exists and is not empty.")
            choice = input("[Setup] Continue anyway? (y/N): ").strip().lower()
            if choice in ['y', 'yes']:
                break
            continue

        break

    return str(project_path.absolute())


def setup_project(project_path: str):
    """Set up the project directory with PRD and git."""
    print(f"[Setup] Creating example project at: {project_path}")

    project_dir = Path(project_path)

    # Create directory
    project_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Setup] ✓ Created directory: {project_path}")

    # Copy PRD.md
    prd_source = Path(__file__).parent / "examples" / "PRD.md"
    prd_dest = project_dir / "PRD.md"

    if prd_source.exists():
        import shutil
        shutil.copy2(prd_source, prd_dest)
        print("[Setup] ✓ Copied PRD.md")
    else:
        print("[Error] PRD.md not found in examples/")
        sys.exit(1)

    # Copy .gitignore
    gitignore_source = Path(__file__).parent / "examples" / ".gitignore_template"
    gitignore_dest = project_dir / ".gitignore"

    if gitignore_source.exists():
        import shutil
        shutil.copy2(gitignore_source, gitignore_dest)
        print("[Setup] ✓ Copied .gitignore")

    # Initialize git if not already a git repo
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        print("[Setup] Initializing git repository...")
        subprocess.run(
            ["git", "init"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )

        # Configure git user if not set
        try:
            subprocess.run(
                ["git", "config", "user.name", "Hephaestus Example"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "example@hephaestus.local"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError:
            print("[Warning] Git configuration may be incomplete")

        print("[Setup] ✓ Git repository initialized")

        # Add files and make initial commit
        subprocess.run(
            ["git", "add", "."],
            cwd=project_dir,
            capture_output=True,
            text=True
        )

        subprocess.run(
            ["git", "commit", "-m", "Initial commit: Add PRD and .gitignore"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        print("[Setup] ✓ Initial commit created")
    else:
        print("[Setup] Git repository already exists")

    print("[Setup] ✓ Project setup complete")
    return str(prd_dest)


def update_config_with_project_path(config_path: str, project_path: str):
    """Update hephaestus_config.yaml with the selected project path."""
    try:
        # Read existing config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Update project paths
        config['paths']['project_root'] = project_path
        config['git']['main_repo_path'] = project_path

        # Write back to config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"[Config] ✓ Updated project paths in {config_path}")
        return True

    except Exception as e:
        print(f"[Error] Failed to update config file: {e}")
        return False


def check_and_setup_sub_agents():
    """Check if sub-agents are available in ~/.claude/agents/ and offer to copy them if needed."""
    agents_dir = Path.home() / ".claude" / "agents"
    examples_agents_dir = Path(__file__).parent / "examples" / "sub_agents"

    # Create target directory if it doesn't exist
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Check what sub-agents we have in examples
    if not examples_agents_dir.exists():
        print(f"[Warning] Examples sub-agents directory not found: {examples_agents_dir}")
        return

    # List required agents
    required_agents = [
        "api-integration-engineer.md",
        "database-architect.md",
        "debug-troubleshoot-expert.md",
        "devops-engineer.md",
        "senior-code-reviewer.md",
        "senior-fastapi-engineer.md",
        "senior-frontend-engineer.md",
        "technical-documentation-writer.md",
        "test-automation-engineer.md"
    ]

    missing_agents = []
    existing_agents = []

    for agent_file in required_agents:
        target_path = agents_dir / agent_file
        source_path = examples_agents_dir / agent_file

        if target_path.exists():
            existing_agents.append(agent_file)
        else:
            missing_agents.append((source_path, target_path, agent_file))

    print(f"[Sub-Agents] Found {len(existing_agents)} agents in ~/.claude/agents/")

    if missing_agents:
        print(f"[Sub-Agents] Missing {len(missing_agents)} agents in ~/.claude/agents/")
        print("\nMissing agents:")
        for _, _, agent_file in missing_agents:
            print(f"  - {agent_file}")

        # Ask user if they want to copy the agents
        response = input("\n[Sub-Agents] You need 9 sub agents. Do you want to copy them to ~/.claude/agents? (y/N): ").strip().lower()

        if response in ['y', 'yes']:
            print("[Sub-Agents] Copying agents...")
            for source_path, target_path, agent_file in missing_agents:
                try:
                    import shutil
                    shutil.copy2(source_path, target_path)
                    print(f"  ✓ Copied {agent_file}")
                except Exception as e:
                    print(f"  ✗ Failed to copy {agent_file}: {e}")
                    return False

            print(f"[Sub-Agents] ✓ Successfully copied {len(missing_agents)} agents")
        else:
            print("[Sub-Agents] Skipping agent copy. Workflow may not work properly without all sub-agents.")

    return True


def main():
    """Run the Hephaestus example."""
    parser = argparse.ArgumentParser(
        description="Run Hephaestus example project"
    )
    parser.add_argument(
        "--drop-db",
        action="store_true",
        help="Drop the database before starting",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path where to create the example project",
    )
    args = parser.parse_args()

    print("🔥 Hephaestus Quick Example Runner 🔥")
    print("=" * 50)

    # Step 0: Check and setup sub-agents
    if not check_and_setup_sub_agents():
        print("[Error] Failed to setup sub-agents. Workflow cannot proceed.")
        sys.exit(1)

    # Step 1: Get and setup project path
    project_path = get_project_path(args.path)
    prd_file = setup_project(project_path)

    # Step 2: Update config file with project path
    config_path = Path(__file__).parent / "hephaestus_config.yaml"
    if not update_config_with_project_path(str(config_path), project_path):
        sys.exit(1)

    # Step 3: Kill existing services
    kill_existing_services()

    # Step 4: Drop database if requested
    db_path = os.getenv("DATABASE_PATH", "./hephaestus.db")
    if args.drop_db:
        drop_database(db_path)

    # Step 5: Load configuration from environment variables
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    mcp_port = int(os.getenv("MCP_PORT", "8000"))
    monitoring_interval = int(os.getenv("MONITORING_INTERVAL_SECONDS", "60"))

    print(f"[Hephaestus] Initializing SDK with PRD to Software Builder phases...")
    print(f"[Config] Using LLM configuration from hephaestus_config.yaml")
    print(f"[Config] Working Directory: {project_path}")
    print(f"[Config] PRD File: {prd_file}")

    # Step 6: Initialize SDK with Python phase objects
    try:
        sdk = HephaestusSDK(
            phases=PRD_PHASES,  # Use Python objects
            workflow_config=PRD_WORKFLOW_CONFIG,  # Result handling config
            database_path=db_path,
            qdrant_url=qdrant_url,
            # LLM configuration now comes from hephaestus_config.yaml
            working_directory=project_path,
            mcp_port=mcp_port,
            monitoring_interval=monitoring_interval,

            # Agent Configuration
            default_cli_tool="claude",  # Options: "claude", "opencode", "codex", "droid"

            # Git Configuration
            main_repo_path=project_path,
            project_root=project_path,
            auto_commit=True,
            conflict_resolution="newest_file_wins",
            worktree_branch_prefix="example-",
        )
    except Exception as e:
        print(f"[Error] Failed to initialize SDK: {e}")
        sys.exit(1)

    # Step 7: Start services
    print("[Hephaestus] Starting services...")
    try:
        sdk.start(enable_tui=False, timeout=30)
    except Exception as e:
        print(f"[Error] Failed to start services: {e}")
        sys.exit(1)

    # Step 8: Output log paths
    print("\n" + "=" * 60)
    print("LOG PATHS")
    print("=" * 60)
    print(f"Backend: {sdk.log_dir}/backend.log")
    print(f"Guardian: {sdk.log_dir}/monitor.log")
    print("=" * 60 + "\n")

    # Step 9: Verify phases loaded
    print(f"[Phases] Loaded {len(sdk.phases_map)} phases:")
    for phase_id, phase in sorted(sdk.phases_map.items()):
        print(f"  - Phase {phase_id}: {phase.name}")

    # Step 10: Create initial Phase 1 task
    print("\n[Task] Creating Phase 1 task...")
    print(f"[Task] PRD Location: {prd_file}")
    try:
        task_id = sdk.create_task(
            description=f"Phase 1: Build Personal Task Manager - Analyze PRD at {prd_file}. This is a simple task management application with FastAPI backend, React frontend, and SQLite database. Extract all requirements, identify components (backend API, frontend UI, database), and spawn MULTIPLE Phase 2 design tasks (one per component). Read the entire PRD carefully.",
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

    # Step 11: Verify task is in pending status
    print("[Task] Verifying task status...")
    time.sleep(2)

    try:
        task_status = sdk.get_task_status(task_id)
        print(f"[Task] Status: {task_status.status}")

        if task_status.status not in ["pending", "assigned", "in_progress"]:
            print(f"[Warning] Unexpected task status: {task_status.status}")
    except Exception as e:
        print(f"[Error] Failed to get task status: {e}")

    # Step 12: Wait for agent assignment
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

    # Step 13: Keep running until interrupted
    print("\n[Hephaestus] Example workflow running. Press Ctrl+C to stop.\n")
    print("=" * 60)
    print("⚠️  HUMAN APPROVAL ENABLED")
    print("=" * 60)
    print("📋 Tickets require YOUR approval before agents can work on them!")
    print("   When Phase 1 creates component tickets, you'll see:")
    print("   • Orange pulsing badge: 'N tickets pending review'")
    print("   • Click ticket → see approval banner → Approve/Reject")
    print("   • Agent waits up to 10 minutes for your decision")
    print()
    print("🔗 Go to: http://localhost:3000/tickets (or port 5173)")
    print("=" * 60)
    print()
    print("[Info] The workflow will:")
    print("  1. Parse the PRD and identify components")
    print("  2. Create Kanban tickets for each component ⏸️  WAITS FOR YOUR APPROVAL")
    print("  3. Design each component in parallel (Phase 2)")
    print("  4. Implement each component (Phase 3)")
    print("  5. Test each component (Phase 4)")
    print("  6. Document the system (Phase 5)")
    print("  7. Submit final result when complete")
    print("\n[Kanban Board] Track progress at http://localhost:3000/tickets")
    print("  - View components moving through: Backlog → Building → Validating → Done")
    print("\n[Project] Your Personal Task Manager will be built in:")
    print(f"  {project_path}")
    print("\nMonitor progress in the logs\n")

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
