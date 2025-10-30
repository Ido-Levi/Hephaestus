"""Agents screen showing all agents with live output."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Static, Footer, RichLog
from textual.containers import Container, Vertical
import requests


class AgentsScreen(Screen):
    """Screen showing all agents and their output."""

    BINDINGS = [
        ("escape", "back", "Back to Forge"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    AgentsScreen {
        background: black;
    }

    #header {
        dock: top;
        height: 3;
        background: $panel;
        text-align: center;
        content-align: center middle;
    }

    #agents-container {
        height: 40%;
        border: solid green;
        margin: 1;
    }

    #output-container {
        height: 60%;
        border: solid cyan;
        margin: 1;
    }

    DataTable {
        height: 100%;
    }

    RichLog {
        height: 100%;
        padding: 1;
    }
    """

    def __init__(self, sdk_instance, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk_instance
        self.selected_agent = None

    def compose(self) -> ComposeResult:
        """Compose the agents screen."""
        yield Static("🤖 AGENTS", id="header")

        with Vertical():
            with Container(id="agents-container"):
                yield DataTable(id="agents-table", cursor_type="row")

            with Container(id="output-container"):
                yield RichLog(id="output-log", highlight=True, markup=True)

        yield Footer()

    def on_mount(self) -> None:
        """Set up the screen after mounting."""
        table = self.query_one("#agents-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_columns("Agent ID", "Status", "Task ID", "Current Task", "Health")

        # Load agents
        self.load_agents()

        # Set up auto-refresh
        self.set_interval(3, self.load_agents)

    def load_agents(self) -> None:
        """Load agents from the backend."""
        table = self.query_one("#agents-table", DataTable)
        current_rows = {row_key.value for row_key in table.rows}

        try:
            api_url = self.sdk.config.api_base_url
            response = requests.get(f"{api_url}/api/agents", timeout=5)
            if response.status_code == 200:
                agents = response.json()  # Response is array directly

                new_rows = set()
                for agent in agents:
                    agent_id = agent.get("id", "")
                    new_rows.add(agent_id)

                    # Get current task description
                    current_task = agent.get("current_task", {})
                    task_desc = current_task.get("description", "")[:30] if current_task else ""
                    if current_task and len(current_task.get("description", "")) > 30:
                        task_desc += "..."

                    health_icon = "✓" if agent.get("health_check_failures", 0) == 0 else "✗"

                    row_data = [
                        agent_id[:12],
                        agent.get("status", ""),
                        agent.get("current_task_id", "")[:8] if agent.get("current_task_id") else "-",
                        task_desc if task_desc else "-",
                        health_icon,
                    ]

                    # Update existing row or add new one
                    if agent_id in current_rows:
                        table.update_cell(agent_id, "Agent ID", row_data[0])
                        table.update_cell(agent_id, "Status", row_data[1])
                        table.update_cell(agent_id, "Task ID", row_data[2])
                        table.update_cell(agent_id, "Current Task", row_data[3])
                        table.update_cell(agent_id, "Health", row_data[4])
                    else:
                        table.add_row(*row_data, key=agent_id)

                # Remove rows that no longer exist
                for row_key in current_rows - new_rows:
                    table.remove_row(row_key)

        except Exception as e:
            if not current_rows:  # Only add error row if table is empty
                table.add_row("ERROR", "-", "-", f"Failed to load: {str(e)}", "-")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection to show agent output."""
        agent_id = event.row_key.value
        self.selected_agent = agent_id
        self.load_agent_output(agent_id)

    def load_agent_output(self, agent_id: str) -> None:
        """Load and display agent details (description and prompt)."""
        output_log = self.query_one("#output-log", RichLog)
        output_log.clear()

        try:
            api_url = self.sdk.config.api_base_url
            response = requests.get(f"{api_url}/api/agents", timeout=5)

            if response.status_code == 200:
                agents = response.json()
                agent = next((a for a in agents if a.get("id") == agent_id), None)

                if agent:
                    output_log.write(f"[bold cyan]Agent ID:[/] {agent_id[:12]}...\n")
                    output_log.write(f"[bold cyan]Status:[/] {agent.get('status', 'unknown')}\n")
                    output_log.write(f"[bold cyan]CLI Type:[/] {agent.get('cli_type', 'unknown')}\n")
                    output_log.write(f"[bold cyan]Health:[/] {'✓ Healthy' if agent.get('health_check_failures', 0) == 0 else '✗ Unhealthy'}\n")
                    output_log.write(f"[bold cyan]Created:[/] {agent.get('created_at', 'unknown')}\n")
                    output_log.write(f"[bold cyan]Last Activity:[/] {agent.get('last_activity', 'unknown')}\n\n")

                    current_task = agent.get("current_task", {})
                    if current_task:
                        output_log.write("[bold yellow]Current Task:[/]\n")
                        output_log.write(f"[bold yellow]Task ID:[/] {current_task.get('id', 'N/A')}\n")
                        output_log.write(f"[bold yellow]Status:[/] {current_task.get('status', 'N/A')}\n")
                        output_log.write(f"[bold yellow]Priority:[/] {current_task.get('priority', 'N/A')}\n\n")
                        output_log.write(f"[bold yellow]Description:[/]\n{current_task.get('description', 'N/A')}\n")
                    else:
                        output_log.write("[dim]No current task[/]\n")
                else:
                    output_log.write(f"[red]Agent {agent_id} not found[/]")
            else:
                output_log.write(f"[red]Failed to load agent: HTTP {response.status_code}[/]")
        except Exception as e:
            output_log.write(f"[red]Error loading agent: {str(e)}[/]")

    def action_refresh(self) -> None:
        """Refresh agents table."""
        self.load_agents()
        if self.selected_agent:
            self.load_agent_output(self.selected_agent)

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
