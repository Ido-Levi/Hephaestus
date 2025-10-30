"""Redesigned create task popup with better UX."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Static, Label
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
import requests


class CreateTaskPopup(ModalScreen):
    """Popup for creating a new task with improved UX."""

    CSS = """
    CreateTaskPopup {
        align: center middle;
    }

    #popup-container {
        width: 90;
        height: 35;
        border: thick green;
        background: $panel;
    }

    #popup-header {
        dock: top;
        height: 3;
        background: green;
        color: black;
        text-align: center;
        content-align: center middle;
        text-style: bold;
    }

    #form-container {
        padding: 2;
        height: 100%;
    }

    .field-group {
        height: auto;
        margin-bottom: 1;
    }

    .field-label {
        color: yellow;
        text-style: bold;
        margin-bottom: 0;
        height: 1;
    }

    .field-help {
        color: #888;
        margin-bottom: 1;
        height: 1;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
    }

    TextArea {
        width: 100%;
        height: 10;
        margin-bottom: 1;
    }

    #button-container {
        dock: bottom;
        height: 5;
        background: $panel;
        align: center middle;
    }

    #button-row {
        align: center middle;
        width: 100%;
    }

    Button {
        margin: 0 2;
        min-width: 16;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        text-align: center;
    }
    """

    def __init__(self, sdk_instance, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk_instance

    def compose(self) -> ComposeResult:
        """Compose the create task popup."""
        with Container(id="popup-container"):
            yield Static("➕ CREATE NEW TASK", id="popup-header")

            with VerticalScroll(id="form-container"):
                with Vertical(classes="field-group"):
                    yield Label("Phase ID", classes="field-label")
                    yield Label("Which phase does this task belong to? (e.g., 1, 2, 3)", classes="field-help")
                    yield Input(placeholder="1", value="1", id="phase-input")

                with Vertical(classes="field-group"):
                    yield Label("Priority", classes="field-label")
                    yield Label("Task priority: low, medium, or high", classes="field-help")
                    yield Input(placeholder="medium", value="medium", id="priority-input")

                with Vertical(classes="field-group"):
                    yield Label("Task Description", classes="field-label")
                    yield Label("Detailed description of what needs to be done", classes="field-help")
                    yield TextArea(id="description-input")

            with Container(id="button-container"):
                with Horizontal(id="button-row"):
                    yield Button("Create Task", variant="success", id="create-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")

            yield Static("", id="status-bar")

    def on_mount(self) -> None:
        """Focus on description field."""
        self.query_one("#description-input", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.app.pop_screen()
        elif event.button.id == "create-btn":
            self.create_task()

    def create_task(self) -> None:
        """Create the task via API."""
        phase_input = self.query_one("#phase-input", Input)
        priority_input = self.query_one("#priority-input", Input)
        description_input = self.query_one("#description-input", TextArea)
        status_bar = self.query_one("#status-bar", Static)

        # Validate inputs
        try:
            phase_id = int(phase_input.value)
        except ValueError:
            status_bar.update("[red]✗ Phase ID must be a number[/]")
            return

        description = description_input.text.strip()
        if not description:
            status_bar.update("[red]✗ Description is required[/]")
            return

        priority = priority_input.value.strip().lower()
        if priority not in ["low", "medium", "high"]:
            status_bar.update("[red]✗ Priority must be: low, medium, or high[/]")
            return

        # Create task via API
        try:
            api_url = self.sdk.config.api_base_url
            response = requests.post(
                f"{api_url}/create_task",
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": "Hephaestus-User",
                },
                json={
                    "task_description": description,
                    "done_definition": "Task completed successfully",
                    "ai_agent_id": "Hephaestus-User",
                    "phase_id": str(phase_id),
                    "priority": priority,
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id", "unknown")
                status_bar.update(f"[green]✓ Task created: {task_id[:16]}...[/]")
                # Close popup after 1.5 seconds
                self.set_timer(1.5, self.app.pop_screen)
            else:
                error_msg = response.text[:100] if response.text else f"HTTP {response.status_code}"
                status_bar.update(f"[red]✗ Error: {error_msg}[/]")
        except Exception as e:
            status_bar.update(f"[red]✗ Error: {str(e)[:100]}[/]")

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.app.pop_screen()
