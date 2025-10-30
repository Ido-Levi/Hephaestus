#!/usr/bin/env python3
"""Initialize the Hephaestus database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import DatabaseManager


def main():
    """Initialize the database with all tables."""
    print("Initializing Hephaestus database...")

    db_manager = DatabaseManager("hephaestus.db")

    # Create all tables
    db_manager.create_tables()

    print("Database initialized successfully!")
    print("Tables created:")
    print("  - agents")
    print("  - tasks (with ticket_id field)")
    print("  - memories")
    print("  - agent_logs")
    print("  - project_context")
    print("  - workflows")
    print("  - phases")
    print("  - phase_executions")
    print("  - agent_worktrees")
    print("  - worktree_commits")
    print("  - validation_reviews")
    print("  - merge_conflict_resolutions")
    print("  - agent_results")
    print("  - workflow_results")
    print("  - guardian_analyses")
    print("  - conductor_analyses")
    print("  - detected_duplicates")
    print("  - steering_interventions")
    print("  - diagnostic_runs")
    print("  - tickets")
    print("  - ticket_comments")
    print("  - ticket_history")
    print("  - ticket_commits")
    print("  - board_configs")
    print("  - ticket_fts (FTS5 virtual table for search)")


if __name__ == "__main__":
    main()