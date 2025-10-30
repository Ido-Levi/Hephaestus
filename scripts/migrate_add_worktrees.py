#!/usr/bin/env python3
"""Database migration to add worktree tables for agent isolation."""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import DatabaseManager, Base


def migrate_add_worktrees():
    """Add worktree tables to the database."""
    print("Starting migration: Adding worktree tables...")

    # Initialize database manager
    db_manager = DatabaseManager()

    # Create all tables (safe - only creates if not exists)
    try:
        # This will create the new worktree tables
        # AgentWorktree, WorktreeCommit, MergeConflictResolution
        Base.metadata.create_all(bind=db_manager.engine)

        print("✅ Successfully created worktree tables:")
        print("  - agent_worktrees")
        print("  - worktree_commits")
        print("  - merge_conflict_resolutions")

        # Verify tables were created
        session = db_manager.get_session()
        try:
            # Check if tables exist by querying them
            from src.core.database import AgentWorktree, WorktreeCommit, MergeConflictResolution

            # These queries will fail if tables don't exist
            session.query(AgentWorktree).count()
            session.query(WorktreeCommit).count()
            session.query(MergeConflictResolution).count()

            print("\n✅ Tables verified successfully!")

        except Exception as e:
            print(f"\n❌ Error verifying tables: {e}")
            return False
        finally:
            session.close()

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

    print("\n✅ Migration completed successfully!")
    return True


if __name__ == "__main__":
    success = migrate_add_worktrees()
    sys.exit(0 if success else 1)