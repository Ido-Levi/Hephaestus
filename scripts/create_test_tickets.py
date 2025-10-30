#!/usr/bin/env python3
"""Create test tickets for E2E testing of the ticket UI."""

import json
import uuid
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import DatabaseManager
from src.core.database import Workflow, BoardConfig, Ticket

# Initialize database
db_path = Path("./hephaestus.db")
db_manager = DatabaseManager(str(db_path))
session = db_manager.get_session()

print("Creating test data for ticket E2E test...")

try:
    # 1. Create workflow
    workflow_id = "workflow-e2e-test"
    workflow = session.query(Workflow).filter_by(id=workflow_id).first()
    if not workflow:
        workflow = Workflow(
            id=workflow_id,
            name="E2E Test Workflow",
            phases_folder_path="/tmp/phases",
            status="active",
            created_at=datetime.utcnow(),
        )
        session.add(workflow)
        print(f"✓ Created workflow: {workflow_id}")
    else:
        print(f"✓ Workflow already exists: {workflow_id}")

    # 2. Create board config
    board_config = session.query(BoardConfig).filter_by(workflow_id=workflow_id).first()
    if not board_config:
        board_config = BoardConfig(
            id=f"board-{uuid.uuid4()}",
            workflow_id=workflow_id,
            name="E2E Test Board",
            columns=[
                {"id": "backlog", "name": "Backlog", "color": "#6B7280", "order": 0},
                {"id": "todo", "name": "To Do", "color": "#3B82F6", "order": 1},
                {"id": "in_progress", "name": "In Progress", "color": "#F59E0B", "order": 2},
                {"id": "review", "name": "Review", "color": "#8B5CF6", "order": 3},
                {"id": "done", "name": "Done", "color": "#10B981", "order": 4},
            ],
            ticket_types=[
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
            ],
            default_ticket_type="task",
            initial_status="backlog",
            created_at=datetime.utcnow(),
        )
        session.add(board_config)
        print("✓ Created board config")
    else:
        print("✓ Board config already exists")

    # 3. Create test tickets
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
        # Check if ticket already exists with this title
        existing = session.query(Ticket).filter_by(
            workflow_id=workflow_id,
            title=ticket_data["title"]
        ).first()

        if not existing:
            # Need to create dummy task and agent first
            from src.core.database import Agent, Task

            # Create ui-task if it doesn't exist
            ui_task = session.query(Task).filter_by(id="ui-task").first()
            if not ui_task:
                ui_task = Task(
                    id="ui-task",
                    description="UI user task",
                    status="in_progress",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(ui_task)

            # Check if ui-user agent exists
            ui_agent = session.query(Agent).filter_by(id="ui-user").first()
            if not ui_agent:
                ui_agent = Agent(
                    id="ui-user",
                    task_id="ui-task",
                    tmux_session="ui-session",
                    status="active",
                    created_at=datetime.utcnow(),
                    last_active=datetime.utcnow(),
                )
                session.add(ui_agent)

            session.flush()  # Ensure task and agent are created before tickets

            ticket = Ticket(
                id=f"ticket-{uuid.uuid4()}",
                workflow_id=workflow_id,
                title=ticket_data["title"],
                description=ticket_data["description"],
                ticket_type=ticket_data["ticket_type"],
                status=ticket_data["status"],
                priority=ticket_data["priority"],
                created_by_agent_id="ui-user",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(ticket)
            print(f"✓ Created ticket: {ticket_data['title']}")
        else:
            print(f"✓ Ticket already exists: {ticket_data['title']}")

    # Commit all changes
    session.commit()
    print("\n✅ Test data created successfully!")
    print(f"\nView the board at: http://localhost:8000/tickets")

except Exception as e:
    session.rollback()
    print(f"\n❌ Error creating test data: {e}")
    raise
finally:
    session.close()
