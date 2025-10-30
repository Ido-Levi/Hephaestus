"""Splash screen with forge art and startup progress."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container

from src.sdk.tui.widgets.forge_art import ForgeArt


class SplashScreen(Screen):
    """Splash screen shown during startup."""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    CSS = """
    SplashScreen {
        align: center middle;
        background: black;
    }

    #forge-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #log-path {
        dock: bottom;
        height: 3;
        text-align: center;
        color: #888;
    }
    """

    def __init__(self, log_dir: str = "", ready: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.log_dir = log_dir
        self.ready = ready

    def compose(self) -> ComposeResult:
        """Compose the splash screen."""
        with Container(id="forge-container"):
            if self.ready:
                yield ForgeArt(
                    status_text="✓ All systems ready\n\nPress any key to enter forge...",
                    id="forge-art",
                )
            else:
                yield ForgeArt(status_text="Starting services...", id="forge-art")

        if self.log_dir:
            log_text = f"Logs: {self.log_dir}/\n  → backend.log  → monitor.log"
            yield Static(log_text, id="log-path")

    def update_status(self, status: str):
        """Update startup status."""
        forge = self.query_one("#forge-art", ForgeArt)
        forge.update_status(status)

    def on_key(self, event):
        """Handle any key press to transition to dashboard."""
        if self.ready:
            # Switch to dashboard
            from src.sdk.tui.screens.dashboard import DashboardScreen

            self.app.pop_screen()
            self.app.push_screen(DashboardScreen())

    def action_quit(self):
        """Quit the application."""
        self.app.exit()
