#!/usr/bin/env python3
"""Add CLI configuration columns to phases table for per-phase agent configuration."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from src.core.simple_config import get_config


def add_phase_cli_columns():
    """Add cli_tool, cli_model, and glm_api_token_env columns to phases table."""
    config = get_config()
    engine = create_engine(f'sqlite:///{config.database_path}')

    columns_to_add = [
        ("cli_tool", "VARCHAR"),
        ("cli_model", "VARCHAR"),
        ("glm_api_token_env", "VARCHAR"),
    ]

    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            try:
                conn.execute(text(f"""
                    ALTER TABLE phases
                    ADD COLUMN {column_name} {column_type};
                """))
                print(f"✅ Added {column_name} column to phases table")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"⚠️  Column {column_name} already exists")
                else:
                    print(f"❌ Error adding {column_name}: {e}")
                    raise

        conn.commit()
        print(f"\n✅ Migration completed successfully!")


if __name__ == "__main__":
    try:
        add_phase_cli_columns()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
