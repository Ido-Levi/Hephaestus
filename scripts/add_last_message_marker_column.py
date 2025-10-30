#!/usr/bin/env python3
"""Add last_claude_message_marker column to guardian_analyses table."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from src.core.simple_config import get_config


def add_column():
    """Add the last_claude_message_marker column to guardian_analyses table."""
    config = get_config()
    engine = create_engine(f'sqlite:///{config.database_path}')

    # SQLite ALTER TABLE to add new column
    with engine.connect() as conn:
        try:
            # Add the new column
            conn.execute("""
                ALTER TABLE guardian_analyses
                ADD COLUMN last_claude_message_marker VARCHAR(100);
            """)
            conn.commit()
            print(f"✅ Successfully added last_claude_message_marker column to guardian_analyses table")
            print(f"   Database: {config.database_path}")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print(f"⚠️  Column last_claude_message_marker already exists in guardian_analyses table")
            else:
                print(f"❌ Error adding column: {e}")
                raise


if __name__ == "__main__":
    add_column()
