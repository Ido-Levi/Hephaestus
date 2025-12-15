#!/usr/bin/env python3
"""
Hephaestus Project Runner - For Real Projects

Use this script to run Hephaestus on YOUR ACTUAL PROJECT (not examples).
Unlike run_hephaestus_dev.py, this script:
  - Uses your EXISTING project directory (doesn't create a new one)
  - Doesn't copy example PRD (uses your actual project files)
  - Doesn't modify hephaestus_config.yaml (reads from it)
  - Validates your project is a proper git repository

Usage:
    python run_hephaestus_project.py [--drop-db] [--project PATH]

Options:
    --drop-db           Drop the database before starting (removes hephaestus.db)
    --project PATH      Path to your existing project (defaults to config file)
    --no-frontend       Don't remind about starting frontend (assumes it's running)

Prerequisites:
    1. Your project directory must exist and be a git repository
    2. hephaestus_config.yaml must have correct paths.project_root set
    3. Qdrant must be running (docker run -p 6333:6333 qdrant/qdrant)
    4. Frontend should be running (cd frontend && npm run dev)
    5. Sub-agents should be in ~/.claude/agents/ (script will check)
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
from example_workflows.prd_to_software.phases import PRD_PHASES, PRD_WORKFLOW_CONFIG, PRD_LAUNCH_TEMPLATE
from example_workflows.bug_fix.phases import BUG_FIX_PHASES, BUG_FIX_WORKFLOW_CONFIG, BUG_FIX_LAUNCH_TEMPLATE
from example_workflows.index_repo.phases import INDEX_REPO_PHASES, INDEX_REPO_CONFIG, INDEX_REPO_LAUNCH_TEMPLATE
from example_workflows.feature_development.phases import FEATURE_DEV_PHASES, FEATURE_DEV_CONFIG, \
    FEATURE_DEV_LAUNCH_TEMPLATE
from example_workflows.documentation_generation.phases import DOC_GEN_PHASES, DOC_GEN_CONFIG, DOC_GEN_LAUNCH_TEMPLATE

from src.sdk import HephaestusSDK
from src.sdk.models import WorkflowDefinition

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


def load_config(config_path: Path) -> dict:
    """Load hephaestus_config.yaml."""
    if not config_path.exists():
        print(f"[Error] Config file not found: {config_path}")
        print("[Error] Please create hephaestus_config.yaml or run from Hephaestus root directory")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def validate_project_directory(project_path: Path) -> bool:
    """Validate that the project directory exists and is a git repository."""
    print(f"[Validation] Checking project directory: {project_path}")
    
    # Check if directory exists
    if not project_path.exists():
        print(f"[Error] Project directory does not exist: {project_path}")
        print("[Error] Please create the directory or update paths.project_root in hephaestus_config.yaml")
        return False
    
    if not project_path.is_dir():
        print(f"[Error] Project path is not a directory: {project_path}")
        return False
    
    # Check if it's a git repository
    git_dir = project_path / ".git"
    if not git_dir.exists():
        print(f"[Error] Project directory is not a git repository: {project_path}")
        print("[Error] Run: cd {project_path} && git init")
        return False
    
    # Check if there's at least one commit
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[Validation] ✓ Git repository is valid (HEAD: {result.stdout.strip()[:8]})")
    except subprocess.CalledProcessError:
        print(f"[Error] Git repository has no commits yet")
        print(f"[Error] Run: cd {project_path} && git commit --allow-empty -m 'Initial commit'")
        return False
    
    # Check directory has some content (files)
    has_files = False
    for item in project_path.iterdir():
        if item.is_file() and item.name != ".gitignore":
            has_files = True
            break
    
    if not has_files:
        print(f"[Warning] Project directory appears to be empty (only has .git)")
        choice = input("[Warning] Continue anyway? (y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            return False
    
    print(f"[Validation] ✓ Project directory is valid")
    return True


def check_qdrant_connection(qdrant_url: str) -> bool:
    """Check if Qdrant is accessible."""
    try:
        import requests
        # Qdrant's root endpoint returns version info
        response = requests.get(f"{qdrant_url}/", timeout=2)
        if response.status_code == 200 and "qdrant" in response.text.lower():
            version = response.json().get("version", "unknown")
            print(f"[Qdrant] ✓ Connected to Qdrant v{version} at {qdrant_url}")
            return True
        else:
            print(f"[Qdrant] ✗ Unexpected response from {qdrant_url}")
            print(f"[Qdrant] Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[Qdrant] ✗ Cannot connect to Qdrant at {qdrant_url}")
        print(f"[Qdrant] Error: {e}")
        print("[Qdrant] Please start Qdrant: docker run -d -p 6333:6333 qdrant/qdrant")
        return False


def check_sub_agents() -> bool:
    """Check if sub-agents are available in ~/.claude/agents/."""
    agents_dir = Path.home() / ".claude" / "agents"
    
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
    
    if not agents_dir.exists():
        print(f"[Sub-Agents] ✗ Agents directory not found: {agents_dir}")
        print("[Sub-Agents] Please create it or copy from examples/sub_agents/")
        return False
    
    missing_agents = []
    for agent_file in required_agents:
        if not (agents_dir / agent_file).exists():
            missing_agents.append(agent_file)
    
    if missing_agents:
        print(f"[Sub-Agents] ✗ Missing {len(missing_agents)}/{len(required_agents)} required agents:")
        for agent in missing_agents:
            print(f"  - {agent}")
        print(f"\n[Sub-Agents] Copy from: {Path(__file__).parent}/examples/sub_agents/")
        print(f"[Sub-Agents] To: {agents_dir}")
        return False
    
    print(f"[Sub-Agents] ✓ All {len(required_agents)} agents found")
    return True


def show_project_info(project_path: Path):
    """Display information about the project directory."""
    print("\n" + "=" * 60)
    print("PROJECT INFORMATION")
    print("=" * 60)
    
    # Count files by type
    file_types = {}
    total_files = 0
    
    for item in project_path.rglob("*"):
        if item.is_file() and not any(part.startswith('.') for part in item.parts):
            total_files += 1
            ext = item.suffix or "no extension"
            file_types[ext] = file_types.get(ext, 0) + 1
    
    print(f"Path: {project_path}")
    print(f"Total files: {total_files}")
    
    if file_types:
        print("\nFile types:")
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ext}: {count}")
    
    # Check for common project files
    markers = {
        "PRD.md": "Product Requirements Document",
        "README.md": "Readme file",
        "package.json": "Node.js project",
        "requirements.txt": "Python requirements",
        "pyproject.toml": "Python project (Poetry)",
        "Cargo.toml": "Rust project",
        "go.mod": "Go project",
    }
    
    found_markers = []
    for marker, description in markers.items():
        if (project_path / marker).exists():
            found_markers.append(f"{marker} ({description})")
    
    if found_markers:
        print("\nProject markers found:")
        for marker in found_markers:
            print(f"  - {marker}")
    
    print("=" * 60 + "\n")


def main():
    """Run Hephaestus on an existing project."""
    parser = argparse.ArgumentParser(
        description="Run Hephaestus on your existing project (not examples)"
    )
    parser.add_argument(
        "--drop-db",
        action="store_true",
        help="Drop the database before starting (removes hephaestus.db)",
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Path to your existing project (overrides config file)",
    )
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Don't show frontend reminder (assumes it's already running)",
    )
    args = parser.parse_args()

    print("🔥 Hephaestus Project Runner 🔥")
    print("=" * 50)
    print("Running Hephaestus on YOUR ACTUAL PROJECT")
    print("(Not the example workflow)")
    print("=" * 50 + "\n")

    # Step 1: Load config file
    config_path = Path(__file__).parent / "hephaestus_config.yaml"
    config = load_config(config_path)
    
    # Step 2: Determine project path
    if args.project:
        project_path = Path(args.project).absolute()
        print(f"[Config] Using project path from --project argument: {project_path}")
    else:
        project_path = Path(config['paths']['project_root']).absolute()
        print(f"[Config] Using project path from hephaestus_config.yaml: {project_path}")
    
    # Step 3: Validate project directory
    if not validate_project_directory(project_path):
        sys.exit(1)
    
    # Step 4: Show project info
    show_project_info(project_path)
    
    # Step 5: Check prerequisites
    print("[Prerequisites] Checking system requirements...")
    
    all_ok = True
    
    # Check Qdrant
    qdrant_url = os.getenv("QDRANT_URL", config.get('memory', {}).get('qdrant_url', 'http://localhost:6333'))
    if not check_qdrant_connection(qdrant_url):
        all_ok = False
    
    # Check sub-agents
    if not check_sub_agents():
        all_ok = False
    
    if not all_ok:
        print("\n[Error] Prerequisites not met. Please fix the issues above.")
        sys.exit(1)
    
    print("[Prerequisites] ✓ All checks passed\n")
    
    # Step 6: Reminder about frontend
    if not args.no_frontend:
        print("=" * 60)
        print("REMINDER: Start the frontend in a separate terminal:")
        print("  cd frontend && npm run dev")
        print("  Then open: http://localhost:3000")
        print("=" * 60 + "\n")
        
        response = input("Press Enter to continue (or Ctrl+C to abort)...")
    
    # Step 7: Kill existing services
    kill_existing_services()

    # Step 8: Drop database if requested
    db_path = os.getenv("DATABASE_PATH", "./hephaestus.db")
    if args.drop_db:
        drop_database(db_path)

    # Step 9: Load configuration
    mcp_port = int(os.getenv("MCP_PORT", "8000"))
    monitoring_interval = int(os.getenv("MONITORING_INTERVAL_SECONDS", "60"))

    print(f"[Hephaestus] Initializing SDK with 5 production workflows...")
    print(f"[Config] Using LLM configuration from hephaestus_config.yaml")
    print(f"[Config] Working Directory: {project_path}")
    print(f"[Config] Database: {db_path}")
    print(f"[Config] Qdrant: {qdrant_url}")
    print(f"[Config] MCP Port: {mcp_port}\n")

    # Step 10: Initialize SDK with workflow definitions
    try:
        # Create workflow definitions
        prd_definition = WorkflowDefinition(
            id="prd-to-software",
            name="PRD to Software Builder",
            phases=PRD_PHASES,
            config=PRD_WORKFLOW_CONFIG,
            description="Build working software from a Product Requirements Document",
            launch_template=PRD_LAUNCH_TEMPLATE,
        )

        bug_fix_definition = WorkflowDefinition(
            id="bug-fix",
            name="Bug Fix",
            phases=BUG_FIX_PHASES,
            config=BUG_FIX_WORKFLOW_CONFIG,
            description="Analyze, fix, and verify bug fixes",
            launch_template=BUG_FIX_LAUNCH_TEMPLATE,
        )

        index_repo_definition = WorkflowDefinition(
            id="index-repo",
            name="Index Repository",
            phases=INDEX_REPO_PHASES,
            config=INDEX_REPO_CONFIG,
            description="Scan and index a repository to build codebase knowledge in memory",
            launch_template=INDEX_REPO_LAUNCH_TEMPLATE,
        )

        feature_dev_definition = WorkflowDefinition(
            id="feature-dev",
            name="Feature Development",
            phases=FEATURE_DEV_PHASES,
            config=FEATURE_DEV_CONFIG,
            description="Add features to existing codebases following existing patterns",
            launch_template=FEATURE_DEV_LAUNCH_TEMPLATE,
        )

        doc_gen_definition = WorkflowDefinition(
            id="doc-gen",
            name="Documentation Generation",
            phases=DOC_GEN_PHASES,
            config=DOC_GEN_CONFIG,
            description="Generate comprehensive documentation for existing codebases",
            launch_template=DOC_GEN_LAUNCH_TEMPLATE,
        )

        sdk = HephaestusSDK(
            workflow_definitions=[
                index_repo_definition,
                bug_fix_definition,
                feature_dev_definition,
                doc_gen_definition,
                prd_definition
            ],
            database_path=db_path,
            qdrant_url=qdrant_url,
            # LLM configuration comes from hephaestus_config.yaml
            working_directory=str(project_path),
            mcp_port=mcp_port,
            monitoring_interval=monitoring_interval,

            # Agent Configuration
            default_cli_tool=config.get('agents', {}).get('default_cli_tool', 'claude'),

            # Git Configuration
            main_repo_path=str(project_path),
            project_root=str(project_path),
            auto_commit=config.get('git', {}).get('auto_commit', True),
            conflict_resolution=config.get('git', {}).get('conflict_resolution', 'newest_file_wins'),
            worktree_branch_prefix=config.get('git', {}).get('worktree_branch_prefix', 'agent-'),
        )
    except Exception as e:
        print(f"[Error] Failed to initialize SDK: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 11: Start services
    print("[Hephaestus] Starting services...")
    try:
        sdk.start(enable_tui=False, timeout=30)
    except Exception as e:
        print(f"[Error] Failed to start services: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 12: Output log paths
    print("\n" + "=" * 60)
    print("LOG PATHS")
    print("=" * 60)
    print(f"Backend: {sdk.log_dir}/backend.log")
    print(f"Guardian: {sdk.log_dir}/monitor.log")
    print("\nTail logs:")
    print(f"  tail -f {sdk.log_dir}/backend.log")
    print(f"  tail -f {sdk.log_dir}/monitor.log")
    print("=" * 60 + "\n")

    # Step 13: Verify workflow definitions loaded
    definitions = sdk.list_workflow_definitions()
    print(f"[Workflows] Loaded {len(definitions)} workflow definitions:")
    for defn in definitions:
        has_template = " (UI-launchable)" if defn.launch_template else ""
        print(f"  - {defn.name} ({defn.id}): {len(defn.phases)} phases{has_template}")

    # Step 14: Ready for UI-based workflow launch
    print("\n" + "=" * 60)
    print("🚀 HEPHAESTUS IS READY 🚀")
    print("=" * 60)
    print()
    print("Frontend UI: http://localhost:3000")
    print()
    print("Available workflows:")
    print("  1. Index Repository     - Scan your codebase to build knowledge")
    print("  2. Bug Fix              - Reproduce, analyze, and fix bugs")
    print("  3. Feature Development  - Add features following existing patterns")
    print("  4. Documentation Gen    - Generate comprehensive docs")
    print("  5. PRD to Software      - Build new software from PRD")
    print()
    print("To launch a workflow:")
    print("  1. Open http://localhost:3000")
    print("  2. Go to 'Workflow Executions' page")
    print("  3. Click 'Launch Workflow'")
    print("  4. Select a workflow and fill in the form")
    print("  5. Review and launch!")
    print()
    print("💡 TIP: Start with 'Index Repository' to build knowledge of your codebase")
    print("        This helps other workflows understand your project better.")
    print()
    print(f"📁 Project Directory: {project_path}")
    print()
    print("Press Ctrl+C to stop Hephaestus")
    print("=" * 60 + "\n")

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
