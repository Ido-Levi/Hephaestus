"""Main forge screen with action menu."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.containers import Horizontal, Container

from src.sdk.tui.widgets.animated_forge_art import AnimatedForgeArt
from src.sdk.tui.widgets.action_menu import ActionMenu


class ForgeMainScreen(Screen):
    """Main forge screen with art and action menu."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "toggle_animations", "Toggle Animations"),
    ]

    CSS = """
    ForgeMainScreen {
        background: black;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #forge-container {
        width: 60%;
        height: 100%;
        align: center middle;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self, sdk_instance, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk_instance

    def compose(self) -> ComposeResult:
        """Compose the main forge screen."""
        with Horizontal(id="main-container"):
            with Container(id="forge-container"):
                yield AnimatedForgeArt(
                    status_text="Use arrows ← ↑ ↓ → to navigate | Press ENTER to select | Press 'a' to toggle animations",
                    enable_animations=True,
                    id="forge-art",
                )
            yield ActionMenu(id="action-menu")

        # Status bar at bottom
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the screen after mounting."""
        self.update_status_bar()
        self.set_interval(5, self.update_status_bar)

    def update_status_bar(self) -> None:
        """Update the status bar with system health."""
        if self.sdk:
            health = self.sdk.is_healthy()
            backend_status = "✓" if health.get("backend_process") and health.get("backend_api") else "✗"
            monitor_status = "✓" if health.get("monitor_process") else "✗"
            qdrant_status = "✓" if health.get("qdrant") else "✗"
            status_text = f"Backend: {backend_status}  Monitor: {monitor_status}  Qdrant: {qdrant_status}  |  Logs: {self.sdk.log_dir}"
        else:
            status_text = "System starting..."

        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(status_text)

    def on_action_menu_action_selected(self, message: ActionMenu.ActionSelected) -> None:
        """Handle action selection from the menu."""
        action_id = message.action_id

        if action_id == "exit":
            self.action_quit()
        elif action_id == "health_check":
            self.show_health_check()
        elif action_id == "tasks":
            from src.sdk.tui.screens.tasks import TasksScreen
            self.app.push_screen(TasksScreen(self.sdk))
        elif action_id == "agents":
            from src.sdk.tui.screens.agents import AgentsScreen
            self.app.push_screen(AgentsScreen(self.sdk))
        elif action_id == "memories":
            from src.sdk.tui.screens.memories import MemoriesScreen
            self.app.push_screen(MemoriesScreen(self.sdk))
        elif action_id == "metrics":
            from src.sdk.tui.screens.metrics import MetricsScreen
            self.app.push_screen(MetricsScreen(self.sdk))
        elif action_id == "create_task":
            from src.sdk.tui.popups.create_task import CreateTaskPopup
            self.app.push_screen(CreateTaskPopup(self.sdk))
        elif action_id == "send_message":
            from src.sdk.tui.popups.send_message import SendMessagePopup
            self.app.push_screen(SendMessagePopup(self.sdk))
        elif action_id == "broadcast":
            from src.sdk.tui.popups.broadcast import BroadcastPopup
            self.app.push_screen(BroadcastPopup(self.sdk))
        elif action_id == "backend_logs":
            from src.sdk.tui.popups.log_viewer import LogViewerPopup
            log_file = f"{self.sdk.log_dir}/backend.log"
            self.app.push_screen(LogViewerPopup(log_file, "Backend Logs"))
        elif action_id == "monitor_logs":
            from src.sdk.tui.popups.log_viewer import LogViewerPopup
            log_file = f"{self.sdk.log_dir}/monitor.log"
            self.app.push_screen(LogViewerPopup(log_file, "Monitor Logs"))

    def show_health_check(self) -> None:
        """Show health check popup."""
        health = self.sdk.is_healthy()
        backend_process = "✓ Online" if health.get("backend_process") else "✗ Offline"
        backend_api = "✓ Online" if health.get("backend_api") else "✗ Offline"
        monitor = "✓ Online" if health.get("monitor_process") else "✗ Offline"
        qdrant = "✓ Online" if health.get("qdrant") else "✗ Offline"
        overall = "✓ Healthy" if health.get("overall") else "✗ Unhealthy"

        from src.sdk.tui.popups.info import InfoPopup
        self.app.push_screen(
            InfoPopup(
                title="System Health",
                message=f"""Overall: {overall}

Backend Process: {backend_process}
Backend API: {backend_api}
Monitor Process: {monitor}
Qdrant: {qdrant}""",
            )
        )

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

    def action_toggle_animations(self) -> None:
        """Toggle forge animations on/off."""
        forge_art = self.query_one("#forge-art", AnimatedForgeArt)
        forge_art.toggle_animations()

        status = "enabled" if forge_art.enable_animations else "disabled"
        forge_art.update_status(
            f"Animations {status} | Use arrows ← ↑ ↓ → to navigate | Press ENTER to select"
        )

    def action_back_to_forge(self) -> None:
        """Return to forge main screen (no-op on main screen)."""
        pass
