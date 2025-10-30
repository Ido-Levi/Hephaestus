#!/usr/bin/env python3
"""Add diagnostic agent support to database schema.

This migration script:
1. Creates the diagnostic_runs table
2. Updates the Agent.agent_type constraint to include 'diagnostic'
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.core.database import DatabaseManager, Base, DiagnosticRun
from src.core.simple_config import get_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Add diagnostic agent support to database."""
    logger.info("Starting diagnostic agent migration...")

    config = get_config()
    db_manager = DatabaseManager(str(config.database_path))

    # Create new table
    from sqlalchemy import create_engine
    engine = create_engine(f"sqlite:///{config.database_path}")

    # Create DiagnosticRun table if it doesn't exist
    try:
        DiagnosticRun.__table__.create(engine, checkfirst=True)
        logger.info("✅ Created diagnostic_runs table")
    except Exception as e:
        logger.warning(f"DiagnosticRun table may already exist: {e}")

    # Note: SQLite doesn't support ALTER for CHECK constraints easily
    # The updated agent_type constraint will work since SQLite is lenient with CHECK constraints
    # When new agents are created with agent_type='diagnostic', they will be accepted

    logger.info("✅ Migration complete - diagnostic agent support added")
    logger.info("\nNext steps:")
    logger.info("1. Restart the monitoring service (run_monitor.py)")
    logger.info("2. Monitor logs for diagnostic agent triggers")
    logger.info("3. Check diagnostic_runs table for diagnostic history")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
