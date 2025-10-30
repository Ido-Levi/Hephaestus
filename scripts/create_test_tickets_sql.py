#!/usr/bin/env python3
"""Create test tickets for E2E testing using raw SQL."""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

db_path = Path("./hephaestus.db")

print("Creating test data for ticket E2E test...")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # 1. Create workflow
    workflow_id = "workflow-e2e-test"
    cursor.execute("SELECT id FROM workflows WHERE id = ?", (workflow_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO workflows (id, name, phases_folder_path, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (workflow_id, "E2E Test Workflow", "/tmp/phases", "active", datetime.utcnow().isoformat()),
        )
        print(f"✓ Created workflow: {workflow_id}")
    else:
        print(f"✓ Workflow already exists: {workflow_id}")

    # 2. Create board config
    cursor.execute("SELECT id FROM board_configs WHERE workflow_id = ?", (workflow_id,))
    if not cursor.fetchone():
        board_id = f"board-{uuid.uuid4()}"
        columns = json.dumps([
            {"id": "backlog", "name": "Backlog", "color": "#6B7280", "order": 0},
            {"id": "todo", "name": "To Do", "color": "#3B82F6", "order": 1},
            {"id": "in_progress", "name": "In Progress", "color": "#F59E0B", "order": 2},
            {"id": "review", "name": "Review", "color": "#8B5CF6", "order": 3},
            {"id": "done", "name": "Done", "color": "#10B981", "order": 4},
        ])
        ticket_types = json.dumps([
            {
                "id": "bug",
                "name": "Bug",
                "icon": "🐛",
                "color": "#EF4444",
                "description": "Something isn't working",
            },
            {
                "id": "feature",
                "name": "Feature",
                "icon": "✨",
                "color": "#3B82F6",
                "description": "New feature or request",
            },
            {
                "id": "task",
                "name": "Task",
                "icon": "📋",
                "color": "#6B7280",
                "description": "General task",
            },
        ])
        cursor.execute(
            "INSERT INTO board_configs (id, workflow_id, name, columns, ticket_types, default_ticket_type, initial_status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (board_id, workflow_id, "E2E Test Board", columns, ticket_types, "task", "backlog", datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        print("✓ Created board config")
    else:
        print("✓ Board config already exists")

    # 3. Create dummy agent
    cursor.execute("SELECT id FROM agents WHERE id = ?", ("ui-user",))
    if not cursor.fetchone():
        cursor.execute(
            """INSERT INTO agents
            (id, created_at, system_prompt, status, cli_type, tmux_session_name, agent_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("ui-user", datetime.utcnow().isoformat(), "UI user", "idle", "claude-code", "ui-session", "phase"),
        )

    # 5. Create test tickets
    tickets_data = [
        {
            "title": "Fix authentication timeout issue",
            "description": "Users are experiencing timeout errors during login. Need to investigate session management and fix the underlying cause.",
            "ticket_type": "bug",
            "priority": "high",
            "status": "in_progress",
        },
        {
            "title": "Add dark mode support",
            "description": "Implement dark mode theme for better user experience in low-light environments. Should include toggle in settings.",
            "ticket_type": "feature",
            "priority": "medium",
            "status": "todo",
        },
        {
            "title": "Update documentation",
            "description": "Refresh README and add deployment guide. Include setup instructions and troubleshooting section.",
            "ticket_type": "task",
            "priority": "low",
            "status": "backlog",
        },
    ]

    for ticket_data in tickets_data:
        cursor.execute(
            "SELECT id FROM tickets WHERE workflow_id = ? AND title = ?",
            (workflow_id, ticket_data["title"]),
        )
        if not cursor.fetchone():
            ticket_id = f"ticket-{uuid.uuid4()}"
            cursor.execute(
                """INSERT INTO tickets
                (id, workflow_id, created_by_agent_id, title, description, ticket_type, priority, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ticket_id,
                    workflow_id,
                    "ui-user",
                    ticket_data["title"],
                    ticket_data["description"],
                    ticket_data["ticket_type"],
                    ticket_data["priority"],
                    ticket_data["status"],
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )
            print(f"✓ Created ticket: {ticket_data['title']}")
        else:
            print(f"✓ Ticket already exists: {ticket_data['title']}")

    conn.commit()
    print("\n✅ Test data created successfully!")
    print(f"\nView the board at: http://localhost:8000/tickets")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error creating test data: {e}")
    raise
finally:
    conn.close()
