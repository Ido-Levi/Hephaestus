#!/usr/bin/env python3
"""
HackerOne Bug Bounty Hunter - Quick Start Script

This script starts the Hephaestus bug bounty workflow for discovering
and reporting security vulnerabilities through HackerOne programs.

SETUP REQUIRED:
1. Create a directory for your bug bounty work
2. Create OVERVIEW.md with the program policy from HackerOne
3. Create allowed_domain.txt with ONE domain to focus on
4. Run this script

Example:
    python run_bug_bounty.py /path/to/bug_bounty_work
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sdk import HephaestusSDK


def main():
    # Get working directory from args or use default
    if len(sys.argv) > 1:
        working_dir = sys.argv[1]
    else:
        working_dir = os.path.expanduser("~/bug_bounty_work")
        print(f"No working directory specified, using: {working_dir}")

    working_dir = os.path.abspath(working_dir)

    # Verify required files exist
    overview_path = os.path.join(working_dir, "OVERVIEW.md")
    domain_path = os.path.join(working_dir, "allowed_domain.txt")

    if not os.path.exists(overview_path):
        print(f"❌ ERROR: OVERVIEW.md not found in {working_dir}")
        print("\nPlease create OVERVIEW.md with the bug bounty program policy.")
        print("Copy the entire program overview from HackerOne.")
        sys.exit(1)

    if not os.path.exists(domain_path):
        print(f"❌ ERROR: allowed_domain.txt not found in {working_dir}")
        print("\nPlease create allowed_domain.txt with ONE domain to focus on.")
        print("Example content: example.com")
        sys.exit(1)

    # Read allowed domain
    with open(domain_path, 'r') as f:
        allowed_domain = f.read().strip()

    print("\n" + "="*70)
    print("🔍 HACKERONE BUG BOUNTY HUNTER")
    print("="*70)
    print(f"\nWorking Directory: {working_dir}")
    print(f"Target Domain: {allowed_domain}")
    print("\nThis workflow will:")
    print("  1. Parse the bug bounty program scope and rules")
    print("  2. Spawn 10-15+ vulnerability hunters (one per vuln type)")
    print("  3. Extensively explore the target domain")
    print("  4. Investigate and validate any findings")
    print("  5. Submit professional reports to HackerOne")
    print("\n⚠️  REMINDER: Only test on authorized programs with in-scope assets!")
    print("="*70 + "\n")

    # Initialize SDK
    # Note: LLM configuration now comes from hephaestus_config.yaml
    sdk = HephaestusSDK(
        phases_dir=str(Path(__file__).parent),
        # LLM provider and model now configured in hephaestus_config.yaml
        working_directory=working_dir,
        database_path=os.path.join(working_dir, "bug_bounty.db"),
        monitoring_interval=60,
        max_concurrent_agents=20,  # Allow many parallel hunters
        task_deduplication_enabled=True,
        similarity_threshold=0.85,
    )

    print("🚀 Starting Hephaestus SDK...")
    sdk.start()

    print("\n✅ SDK started successfully!")
    print(f"📊 TUI available at: http://localhost:8000")
    print(f"📁 Database: {working_dir}/bug_bounty.db\n")

    # Create initial Phase 1 task
    print("📋 Creating Phase 1 task: Program Analysis & Strategic Planning")
    task_id = sdk.create_task(
        description="Phase 1: Analyze bug bounty program and spawn vulnerability hunters",
        phase_id=1,
        priority="high",
    )

    print(f"✅ Phase 1 task created! Task ID: {task_id}\n")
    print("="*70)
    print("🎯 WORKFLOW STARTED!")
    print("="*70)
    print("\nPhase 1 will now:")
    print("  • Parse OVERVIEW.md for scope and rules")
    print("  • Extract in-scope vulnerability types")
    print("  • Create test accounts")
    print("  • Spawn 10-15+ Phase 2 vulnerability hunters")
    print("\nMonitor progress:")
    print(f"  • Web UI: http://localhost:8000")
    print(f"  • Tasks: curl http://localhost:8000/api/tasks")
    print(f"  • Results: curl http://localhost:8000/api/results")
    print("\n⏸️  Press Ctrl+C to stop (agents will finish current tasks)")
    print("="*70 + "\n")

    # Keep running until interrupted
    try:
        import time
        while True:
            time.sleep(60)
            # Could add periodic status updates here
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping workflow...")
        print("Agents will complete their current tasks and shut down.")
        print("Your progress is saved in the database.")
        print("\nTo resume later, run this script again.")


if __name__ == "__main__":
    main()
