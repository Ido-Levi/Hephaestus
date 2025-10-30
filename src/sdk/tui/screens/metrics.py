"""Metrics screen showing system statistics."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, DataTable
from textual.containers import Container, Vertical, Horizontal
import requests


class MetricsScreen(Screen):
    """Screen showing system metrics and statistics."""

    BINDINGS = [
        ("escape", "back", "Back to Forge"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    MetricsScreen {
        background: black;
    }

    #header {
        dock: top;
        height: 3;
        background: $panel;
        text-align: center;
        content-align: center middle;
    }

    .metric-container {
        height: 50%;
        border: solid cyan;
        margin: 1;
        padding: 1;
    }

    .metric-title {
        text-style: bold;
        color: yellow;
        margin-bottom: 1;
    }

    .metric-row {
        padding: 0 2;
        margin: 0 0 1 0;
    }

    .metric-label {
        width: 30;
        color: white;
    }

    .metric-value {
        color: green;
        text-style: bold;
    }

    DataTable {
        height: 100%;
    }
    """

    def __init__(self, sdk_instance, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk_instance

    def compose(self) -> ComposeResult:
        """Compose the metrics screen."""
        yield Static("📊 SYSTEM METRICS", id="header")

        with Vertical():
            with Container(classes="metric-container"):
                yield Static("System Overview", classes="metric-title")
                yield Static("Loading metrics...", id="system-metrics")

            with Container(classes="metric-container"):
                yield Static("Task Statistics", classes="metric-title")
                yield DataTable(id="task-stats-table")

        yield Footer()

    def on_mount(self) -> None:
        """Set up the screen after mounting."""
        # Set up task stats table
        table = self.query_one("#task-stats-table", DataTable)
        table.add_columns("Status", "Count", "Percentage")

        # Load initial metrics
        self.load_metrics()

        # Auto-refresh every 5 seconds
        self.set_interval(5, self.load_metrics)

    def load_metrics(self) -> None:
        """Load system metrics from the backend."""
        self.load_system_metrics()
        self.load_task_stats()

    def load_system_metrics(self) -> None:
        """Load general system metrics."""
        metrics_widget = self.query_one("#system-metrics", Static)

        try:
            # Get agent status
            api_url = self.sdk.config.api_base_url
            agent_response = requests.get(f"{api_url}/api/agents", timeout=5)
            tasks_response = requests.get(f"{api_url}/api/tasks", timeout=5)

            if agent_response.status_code == 200 and tasks_response.status_code == 200:
                agents = agent_response.json()  # Array directly
                tasks = tasks_response.json()  # Array directly

                active_agents = len([a for a in agents if a.get("status") == "working"])
                total_agents = len(agents)
                total_tasks = len(tasks)
                healthy_agents = len([a for a in agents if a.get("health_check_failures", 0) == 0])

                # Check backend/monitor health
                health = self.sdk.is_healthy()
                backend_health = "✓ Online" if health.get("backend_process") and health.get("backend_api") else "✗ Offline"
                monitor_health = "✓ Online" if health.get("monitor_process") else "✗ Offline"
                qdrant_health = "✓ Online" if health.get("qdrant") else "✗ Offline"

                text = f"""[bold cyan]Backend:[/] {backend_health}
[bold cyan]Monitor:[/] {monitor_health}
[bold cyan]Qdrant:[/] {qdrant_health}

[bold cyan]Total Agents:[/] {total_agents}
[bold cyan]Active Agents:[/] {active_agents}
[bold cyan]Healthy Agents:[/] {healthy_agents}

[bold cyan]Total Tasks:[/] {total_tasks}

[bold cyan]Log Directory:[/] {self.sdk.log_dir}
"""
                metrics_widget.update(text)
            else:
                metrics_widget.update("[red]Failed to load metrics[/]")

        except Exception as e:
            metrics_widget.update(f"[red]Error loading metrics: {str(e)}[/]")

    def load_task_stats(self) -> None:
        """Load task statistics."""
        table = self.query_one("#task-stats-table", DataTable)
        table.clear()

        try:
            api_url = self.sdk.config.api_base_url
            response = requests.get(f"{api_url}/api/tasks", timeout=5)

            if response.status_code == 200:
                tasks = response.json()
                total = len(tasks)

                if total == 0:
                    table.add_row("No tasks yet", "0", "0%")
                    return

                # Count by status
                status_counts = {}
                for task in tasks:
                    status = task.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1

                # Add rows for each status
                for status, count in sorted(status_counts.items()):
                    percentage = (count / total) * 100
                    table.add_row(
                        status.upper(),
                        str(count),
                        f"{percentage:.1f}%",
                    )

        except Exception as e:
            table.add_row("ERROR", "-", str(e))

    def action_refresh(self) -> None:
        """Refresh metrics."""
        self.load_metrics()

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
