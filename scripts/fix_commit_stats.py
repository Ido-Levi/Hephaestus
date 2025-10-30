#!/usr/bin/env python3
"""Fix commit stats in database by fetching real values from git."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import get_db, TicketCommit
from src.core.simple_config import get_config
from src.services.ticket_service import TicketService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_commit_stats():
    """Update all ticket commits with real git stats."""
    config = get_config()
    main_repo_path = str(config.main_repo_path)

    with get_db() as db:
        # Get all commits with 0 files_changed (likely need updating)
        commits = db.query(TicketCommit).filter(
            TicketCommit.files_changed == 0
        ).all()

        logger.info(f"Found {len(commits)} commits to update")

        updated_count = 0
        failed_count = 0

        for commit in commits:
            try:
                logger.info(f"Updating commit {commit.commit_sha} for ticket {commit.ticket_id}")

                # Get real stats from git
                stats = TicketService._get_commit_stats(commit.commit_sha, main_repo_path)

                # Update the commit record
                commit.files_changed = stats["files_changed"]
                commit.insertions = stats["insertions"]
                commit.deletions = stats["deletions"]
                commit.files_list = stats["files_list"]

                if stats["files_changed"] > 0:
                    logger.info(
                        f"  ✓ Updated: {stats['files_changed']} files, "
                        f"+{stats['insertions']} -{stats['deletions']}"
                    )
                    updated_count += 1
                else:
                    logger.warning(f"  ⚠ No changes found for commit {commit.commit_sha}")

            except Exception as e:
                logger.error(f"  ✗ Failed to update commit {commit.commit_sha}: {e}")
                failed_count += 1

        # Commit all changes
        if updated_count > 0:
            db.commit()
            logger.info(f"\n✓ Updated {updated_count} commits successfully")

        if failed_count > 0:
            logger.warning(f"⚠ Failed to update {failed_count} commits")

        if updated_count == 0 and failed_count == 0:
            logger.info("No commits needed updating")


if __name__ == "__main__":
    logger.info("Starting commit stats fix...")
    fix_commit_stats()
    logger.info("Done!")
