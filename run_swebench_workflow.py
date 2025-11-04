#!/usr/bin/env python3
"""
SWEBench Solver Workflow Runner

This script automates the SWEBench solver workflow using the Hephaestus SDK.
It sets up the repository, problem statement, and launches the exploration-based workflow.

The workflow solves SWEBench issues through systematic exploration, validation,
implementation, and testing of different solution approaches.

Usage:
    # Using SWE-bench dataset instance ID:
    python run_swebench_workflow.py --path /path/to/workspace --instance-id astropy__astropy-14365 [--tui] [--drop-db] [--resume]

    # Using manual repository details:
    python run_swebench_workflow.py --path /path/to/workspace --repo https://github.com/org/repo.git --commit abc123 --problem-statement ./problem.md [--tui] [--drop-db] [--resume]

Options:
    --path PATH                 Path to workspace directory (will be created if doesn't exist)
    --instance-id ID            SWE-bench instance ID (e.g., astropy__astropy-14365)
    --repo REPO                 Git repository URL to clone (required if not using --instance-id)
    --commit COMMIT             Git commit SHA to checkout (required if not using --instance-id)
    --problem-statement FILE    Path to problem statement markdown file (required if not using --instance-id)
    --tui                       Enable TUI mode for interactive monitoring
    --drop-db                   Drop the database before starting (removes hephaestus.db)
    --resume                    Resume existing workflow (don't create initial task)

Note: Either --instance-id OR (--repo + --commit + --problem-statement) must be provided.
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from datasets import load_dataset

# Import from example_workflows
sys.path.insert(0, str(Path(__file__).parent))
from example_workflows.swebench_solver.phases import SWEBENCH_PHASES, SWEBENCH_WORKFLOW_CONFIG

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


def setup_swebench_repo(path: str, repo: str, commit: str, problem_statement: str) -> str:
    """
    Set up the SWEBench repository with problem statement.

    Args:
        path: Path to workspace directory
        repo: Git repository URL
        commit: Git commit SHA to checkout
        problem_statement: Path to problem statement markdown file

    Returns:
        Path to the cloned repository
    """
    workspace = Path(path)

    # Step 1: Create workspace directory if it doesn't exist
    print(f"[Setup] Creating workspace directory: {path}")
    workspace.mkdir(parents=True, exist_ok=True)
    print(f"[Setup] ✓ Workspace directory ready")

    # Step 2: Extract repo name from URL
    repo_name = repo.rstrip('/').split('/')[-1].replace('.git', '')
    repo_path = workspace / repo_name

    # Step 3: Clone repository if it doesn't exist
    if repo_path.exists():
        print(f"[Setup] Repository already exists at {repo_path}")
        print(f"[Setup] Cleaning up existing repository...")
        # Clean any uncommitted changes
        try:
            subprocess.run(
                ["git", "reset", "--hard"],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "clean", "-fdx"],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(f"[Warning] Could not clean repository: {e}")
    else:
        print(f"[Setup] Cloning repository: {repo}")
        try:
            subprocess.run(
                ["git", "clone", repo, str(repo_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"[Setup] ✓ Repository cloned to {repo_path}")
        except subprocess.CalledProcessError as e:
            print(f"[Error] Failed to clone repository: {e.stderr}")
            sys.exit(1)

    # Step 4: Checkout specific commit
    print(f"[Setup] Checking out commit: {commit}")
    try:
        subprocess.run(
            ["git", "checkout", commit],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"[Setup] ✓ Checked out commit {commit}")
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to checkout commit: {e.stderr}")
        sys.exit(1)

    # Step 5: Copy problem statement file
    problem_statement_path = Path(problem_statement)
    if not problem_statement_path.exists():
        print(f"[Error] Problem statement file not found: {problem_statement}")
        sys.exit(1)

    print(f"[Setup] Copying problem statement to repository...")
    target_path = repo_path / "PROBLEM_STATEMENT.md"
    shutil.copy2(problem_statement_path, target_path)
    print(f"[Setup] ✓ Problem statement copied to {target_path}")

    # Step 6: Commit problem statement
    print(f"[Setup] Committing PROBLEM_STATEMENT.md...")
    try:
        subprocess.run(
            ["git", "add", "PROBLEM_STATEMENT.md"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Add PROBLEM_STATEMENT.md for SWEBench workflow"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        print(f"[Setup] ✓ PROBLEM_STATEMENT.md committed")
    except subprocess.CalledProcessError as e:
        # It's ok if commit fails (might already exist)
        print(f"[Setup] Note: {e.stderr if e.stderr else 'PROBLEM_STATEMENT.md may already exist'}")

    print(f"[Setup] ✓ Repository setup complete at {repo_path}")
    return str(repo_path.absolute())


def load_swebench_instance(instance_id: str) -> dict:
    """
    Load instance data from SWE-bench Verified dataset.

    Args:
        instance_id: SWE-bench instance ID (e.g., "astropy__astropy-14365")

    Returns:
        Dictionary with keys: repo, commit, problem_text, instance_id
    """
    print(f"[SWE-bench] Loading dataset for instance: {instance_id}")

    try:
        ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    except Exception as e:
        print(f"[Error] Failed to load SWE-bench dataset: {e}")
        sys.exit(1)

    # Find the instance
    instance = None
    for item in ds:
        if item['instance_id'] == instance_id:
            instance = item
            break

    if instance is None:
        print(f"[Error] Instance '{instance_id}' not found in SWE-bench Verified dataset")
        print(f"[Error] Make sure the instance ID is correct (e.g., astropy__astropy-14365)")
        sys.exit(1)

    print(f"[SWE-bench] ✓ Found instance: {instance_id}")

    # Extract repository URL
    repo_url = instance.get('repo')
    if not repo_url.startswith('http'):
        # Convert github short format to full URL
        repo_url = f"https://github.com/{repo_url}"

    return {
        'repo': repo_url,
        'commit': instance.get('base_commit'),
        'problem_text': instance.get('problem_statement'),
        'instance_id': instance_id,
    }


def extract_instance_id(repo: str, commit: str) -> str:
    """Extract a reasonable instance ID from repo and commit."""
    repo_name = repo.rstrip('/').split('/')[-1].replace('.git', '')
    short_commit = commit[:7]
    return f"{repo_name}-{short_commit}"


def main():
    """Run the SWEBench Solver workflow."""
    parser = argparse.ArgumentParser(
        description="Solve SWEBench issues using Hephaestus SDK"
    )
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Path to workspace directory (will be created if doesn't exist)",
    )

    # SWE-bench dataset option
    parser.add_argument(
        "--instance-id",
        type=str,
        help="SWE-bench instance ID (e.g., astropy__astropy-14365)",
    )

    # Manual repository option
    parser.add_argument(
        "--repo",
        type=str,
        help="Git repository URL to clone (required if not using --instance-id)",
    )
    parser.add_argument(
        "--commit",
        type=str,
        help="Git commit SHA to checkout (required if not using --instance-id)",
    )
    parser.add_argument(
        "--problem-statement",
        type=str,
        help="Path to problem statement markdown file (required if not using --instance-id)",
    )

    # Other options
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
        help="Resume existing workflow without creating initial task",
    )
    args = parser.parse_args()

    # Validate arguments: either instance-id OR manual parameters
    if args.instance_id:
        if args.repo or args.commit or args.problem_statement:
            parser.error("--instance-id cannot be used with --repo, --commit, or --problem-statement")
    else:
        if not (args.repo and args.commit and args.problem_statement):
            parser.error("Either --instance-id OR all of (--repo, --commit, --problem-statement) must be provided")

    # Step 1: Kill existing services
    kill_existing_services()

    # Step 2: Drop database if requested
    db_path = os.getenv("DATABASE_PATH", "./hephaestus.db")
    if args.drop_db:
        drop_database(db_path)

    # Step 3: Load instance data (either from dataset or manual args)
    if args.instance_id:
        # Load from SWE-bench dataset
        swebench_data = load_swebench_instance(args.instance_id)
        repo = swebench_data['repo']
        commit = swebench_data['commit']
        instance_id = swebench_data['instance_id']

        # Create problem statement file from dataset
        workspace = Path(args.path)
        workspace.mkdir(parents=True, exist_ok=True)
        problem_statement_path = workspace / f"{instance_id}.md"

        print(f"[SWE-bench] Writing problem statement to {problem_statement_path}")
        with open(problem_statement_path, 'w') as f:
            f.write(swebench_data['problem_text'])

        problem_statement = str(problem_statement_path)
        print(f"[SWE-bench] ✓ Problem statement created")
    else:
        # Use manual parameters
        repo = args.repo
        commit = args.commit
        problem_statement = args.problem_statement
        instance_id = extract_instance_id(repo, commit)

    # Step 4: Set up SWEBench repository (skip if resuming)
    if not args.resume:
        repo_path = setup_swebench_repo(
            args.path,
            repo,
            commit,
            problem_statement
        )
    else:
        # If resuming, reconstruct repo path
        repo_name = repo.rstrip('/').split('/')[-1].replace('.git', '')
        repo_path = str(Path(args.path) / repo_name)
        print(f"[Resume] Using existing repository at {repo_path}")

    # Step 5: Load configuration from environment variables
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    mcp_port = int(os.getenv("MCP_PORT", "8000"))
    monitoring_interval = int(os.getenv("MONITORING_INTERVAL_SECONDS", "60"))

    print("\n[Hephaestus] Initializing SDK with SWEBench Solver phases...")
    print(f"[Config] Using LLM configuration from hephaestus_config.yaml")
    print(f"[Config] Instance ID: {instance_id}")
    print(f"[Config] Repository: {repo_path}")
    print(f"[Config] Commit: {commit}")
    if args.instance_id:
        print(f"[Config] Source: SWE-bench Verified dataset")
    if not args.resume:
        print(f"[Config] Problem Statement: {problem_statement}")
    if args.resume:
        print(f"[Config] Mode: Resume (no initial task will be created)")

    # Step 6: Prepare workflow config with placeholder replacements
    # Load problem statement text for placeholder replacement
    print("[Config] Preparing validation criteria with SWEBench instance details...")
    with open(problem_statement, 'r') as f:
        problem_text = f.read()

    # Create a copy of the workflow config and replace placeholders in result_criteria
    import copy
    from src.sdk.models import WorkflowConfig

    swebench_config = WorkflowConfig(
        has_result=SWEBENCH_WORKFLOW_CONFIG.has_result,
        enable_tickets=SWEBENCH_WORKFLOW_CONFIG.enable_tickets,
        board_config=SWEBENCH_WORKFLOW_CONFIG.board_config,
        result_criteria=SWEBENCH_WORKFLOW_CONFIG.result_criteria
            .replace("{REPO_URL}", repo)
            .replace("{COMMIT_SHA}", commit)
            .replace("{PROBLEM_STATEMENT}", problem_text),
        on_result_found=SWEBENCH_WORKFLOW_CONFIG.on_result_found,
    )
    print("[Config] ✓ Validation criteria configured with repo, commit, and problem statement")

    # Step 7: Initialize SDK with Python phase objects
    try:
        sdk = HephaestusSDK(
            phases=SWEBENCH_PHASES,  # Use Python objects
            workflow_config=swebench_config,  # Modified config with placeholder replacements
            database_path=db_path,
            qdrant_url=qdrant_url,
            # LLM configuration now comes from hephaestus_config.yaml
            working_directory=repo_path,
            mcp_port=mcp_port,
            monitoring_interval=monitoring_interval,

            # Git Configuration
            main_repo_path=repo_path,
            project_root=repo_path,
            base_branch=commit,  # Use the commit SHA as the base for merging
            auto_commit=True,
            conflict_resolution="newest_file_wins",
            worktree_branch_prefix="swebench-solver-",
        )
    except Exception as e:
        print(f"[Error] Failed to initialize SDK: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 8: Start services
    print("[Hephaestus] Starting services...")
    try:
        sdk.start(enable_tui=args.tui, timeout=30)
    except Exception as e:
        print(f"[Error] Failed to start services: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 9: Output log paths (only if not in TUI mode)
    if not args.tui:
        print("\n" + "=" * 60)
        print("LOG PATHS")
        print("=" * 60)
        print(f"Backend: {sdk.log_dir}/backend.log")
        print(f"Guardian: {sdk.log_dir}/monitor.log")
        print("=" * 60 + "\n")

    # Step 10: Verify phases loaded
    print(f"[Phases] Loaded {len(sdk.phases_map)} phases:")
    for phase_id, phase in sorted(sdk.phases_map.items()):
        print(f"  - Phase {phase_id}: {phase.name}")

    # Step 11: Create initial Phase 1 task (unless resuming)
    if not args.resume:
        print("\n[Task] Creating Phase 1 task...")
        print(f"[Task] Instance ID: {instance_id}")
        try:
            task_id = sdk.create_task(
                description=f"Phase 1: Analyze and reproduce the issue described in PROBLEM_STATEMENT.md at {repo_path}/PROBLEM_STATEMENT.md. Create reproduction.md with clear steps, create main issue ticket, and spawn MULTIPLE approach tickets + Phase 2 tasks for different solution strategies. The workflow uses ticket tracking - create issue ticket, then 2-3 approach tickets exploring different fix strategies.",
                phase_id=1,
                priority="high",
                agent_id="main-session-agent",
            )
            print(f"[Task] ✓ Created task: {task_id}")
        except Exception as e:
            print(f"[Error] Failed to create task: {e}")
            print(f"[Error] Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            sdk.shutdown()
            sys.exit(1)

        # Step 12: Verify task is in pending status
        print("[Task] Verifying task status...")
        time.sleep(2)

        try:
            task_status = sdk.get_task_status(task_id)
            print(f"[Task] Status: {task_status.status}")

            if task_status.status not in ["pending", "assigned", "in_progress"]:
                print(f"[Warning] Unexpected task status: {task_status.status}")
        except Exception as e:
            print(f"[Error] Failed to get task status: {e}")

        # Step 13: Wait for agent assignment
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

    # Step 14: If not in TUI mode, keep running until interrupted
    if not args.tui:
        print("\n[Hephaestus] Workflow running. Press Ctrl+C to stop.\n")
        if not args.resume:
            print("[Info] The SWEBench solver workflow will:")
            print("  1. Phase 1: Reproduce the issue and create tickets")
            print("     - Main issue ticket (represents the SWEBench problem)")
            print("     - Multiple approach tickets (different solution strategies)")
            print("  2. Phase 2: Explore and implement each approach in parallel")
            print("     - Investigate approach → implement fix → test immediately")
            print("     - If works → create Phase 3 task for full testing")
            print("     - If fails → mark approach as failed + create new approach")
            print("  3. Phase 3: Comprehensive testing")
            print("     - Run full test suite on working implementation")
            print("     - If all pass → Resolve tickets + Submit result ✅")
            print("     - If any fail → Mark approach as failed + create new approach")
            print("\n[Kanban Board] Track exploration at http://localhost:8000/tickets or http://localhost:3001/")
            print("  - Watch approaches move through: Exploration → Exploring & Implementing → Testing → Solved")
            print("  - Failed approaches remain visible with detailed reasoning for learning")
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
