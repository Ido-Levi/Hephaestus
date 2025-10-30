"""Tasks screen showing all tasks with details."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Static, Footer
from textual.containers import Container, Vertical
from typing import Any
import requests


class TasksScreen(Screen):
    """Screen showing all tasks in a table."""

    BINDINGS = [
        ("escape", "back", "Back to Forge"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    TasksScreen {
        background: black;
    }

    #header {
        dock: top;
        height: 3;
        background: $panel;
        text-align: center;
        content-align: center middle;
    }

    #tasks-container {
        height: 70%;
        border: solid green;
        margin: 1;
    }

    #details-container {
        height: 30%;
        border: solid yellow;
        margin: 1;
    }

    #details-content {
        padding: 1;
        color: white;
    }

    DataTable {
        height: 100%;
    }
    """

    def __init__(self, sdk_instance, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk_instance
        self.selected_task = None

    def compose(self) -> ComposeResult:
        """Compose the tasks screen."""
        yield Static("📋 TASKS", id="header")

        with Vertical():
            with Container(id="tasks-container"):
                yield DataTable(id="tasks-table", cursor_type="row")

            with Container(id="details-container"):
                yield Static("Select a task to view details...", id="details-content")

        yield Footer()

    def on_mount(self) -> None:
        """Set up the screen after mounting."""
        table = self.query_one("#tasks-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_columns("ID", "Phase", "Status", "Priority", "Agent", "Description")

        # Load tasks
        self.load_tasks()

    def load_tasks(self) -> None:
        """Load tasks from the backend."""
        table = self.query_one("#tasks-table", DataTable)
        table.clear()

        try:
            # Get tasks via SDK
            api_url = self.sdk.config.api_base_url
            response = requests.get(f"{api_url}/api/tasks", timeout=5)
            if response.status_code == 200:
                tasks = response.json()
                for task in tasks:
                    # Truncate description for table
                    desc = task.get("description", "")[:40]
                    if len(task.get("description", "")) > 40:
                        desc += "..."

                    table.add_row(
                        task.get("id", "")[:8],
                        str(task.get("phase_id", "")),
                        task.get("status", ""),
                        task.get("priority", ""),
                        task.get("agent_id", "")[:12] if task.get("agent_id") else "-",
                        desc,
                        key=task.get("id", ""),
                    )
        except Exception as e:
            table.add_row("ERROR", "-", "-", "-", "-", f"Failed to load tasks: {str(e)}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection to show task details."""
        task_id = event.row_key.value

        try:
            api_url = self.sdk.config.api_base_url
            response = requests.get(f"{api_url}/api/tasks/{task_id}", timeout=5)
            if response.status_code == 200:
                task = response.json()
                self.show_task_details(task)
        except Exception as e:
            self.show_error(f"Failed to load task details: {str(e)}")

    def show_task_details(self, task: dict[str, Any]) -> None:
        """Display task details in the details panel."""
        details = self.query_one("#details-content", Static)

        text = f"""[bold yellow]Task ID:[/] {task.get('id', 'N/A')}
[bold yellow]Phase:[/] {task.get('phase_id', 'N/A')}
[bold yellow]Status:[/] {task.get('status', 'N/A')}
[bold yellow]Priority:[/] {task.get('priority', 'N/A')}
[bold yellow]Agent:[/] {task.get('agent_id', 'N/A')}
[bold yellow]Created:[/] {task.get('created_at', 'N/A')}

[bold yellow]Description:[/]
{task.get('description', 'N/A')}

[bold yellow]Done Definition:[/]
{task.get('done_definition', 'N/A')}
"""
        details.update(text)

    def show_error(self, message: str) -> None:
        """Show error message in details panel."""
        details = self.query_one("#details-content", Static)
        details.update(f"[red]Error:[/] {message}")

    def action_refresh(self) -> None:
        """Refresh tasks table."""
        self.load_tasks()

    def action_back(self) -> None:
        """Return to forge main screen."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application with confirmation."""
        from src.sdk.tui.popups.confirm import ConfirmPopup

        def check_quit(confirmed: bool) -> None:
            if confirmed:
                self.app.exit()

        self.app.push_screen(
            ConfirmPopup(
                title="⚠️  EXIT HEPHAESTUS",
                message="Are you sure you want to exit?\nAll running agents will continue in the background.",
            ),
            check_quit
        )
