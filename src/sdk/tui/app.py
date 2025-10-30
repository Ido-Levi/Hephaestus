"""Main Textual TUI application for Hephaestus."""

from textual.app import App
from textual.screen import Screen

from src.sdk.tui.screens.forge_main import ForgeMainScreen


class HephaestusTUI(App):
    """
    Hephaestus Terminal User Interface.

    Provides an interactive interface for managing Hephaestus agents and tasks.
    """

    CSS = """
    Screen {
        background: black;
    }
    """

    TITLE = "Hephaestus Forge"

    def __init__(self, sdk_instance, log_dir: str = "", **kwargs):
        """
        Initialize the TUI.

        Args:
            sdk_instance: The HephaestusSDK instance to control
            log_dir: Path to log directory
        """
        super().__init__(**kwargs)
        self.sdk = sdk_instance
        self.log_dir = log_dir

    def on_mount(self):
        """Called when app starts."""
        # Show main forge screen
        self.push_screen(ForgeMainScreen(self.sdk))

    def get_system_health(self):
        """Get system health from SDK."""
        if self.sdk:
            return self.sdk.is_healthy()
        return {
            "backend": False,
            "monitor": False,
        }
