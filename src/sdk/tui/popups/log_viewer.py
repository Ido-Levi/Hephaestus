"""Log viewer popup."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import RichLog, Button, Static
from textual.containers import Container, Horizontal
from pathlib import Path


class LogViewerPopup(ModalScreen):
    """Popup for viewing log files with live tail."""

    CSS = """
    LogViewerPopup {
        align: center middle;
    }

    #popup-container {
        width: 90%;
        height: 90%;
        border: thick blue;
        background: $panel;
        padding: 1;
    }

    #popup-title {
        text-align: center;
        background: blue;
        color: white;
        text-style: bold;
        padding: 1;
        margin-bottom: 1;
    }

    RichLog {
        height: 100%;
        border: solid white;
        background: black;
    }

    #button-row {
        dock: bottom;
        align: center middle;
        height: 3;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, log_file: str, title: str = "Log Viewer", **kwargs):
        super().__init__(**kwargs)
        self.log_file = Path(log_file)
        self.title = title
        self.last_position = 0

    def compose(self) -> ComposeResult:
        """Compose the log viewer popup."""
        with Container(id="popup-container"):
            yield Static(f"📜 {self.title}", id="popup-title")
            yield RichLog(id="log-content", highlight=True, markup=True)

            with Horizontal(id="button-row"):
                yield Button("Refresh", variant="primary", id="refresh-btn")
                yield Button("Clear", variant="warning", id="clear-btn")
                yield Button("Close", variant="error", id="close-btn")

    def on_mount(self) -> None:
        """Set up the log viewer after mounting."""
        self.load_log()
        # Auto-refresh every 2 seconds
        self.set_interval(2, self.load_log)

    def load_log(self) -> None:
        """Load and display log file content."""
        log_widget = self.query_one("#log-content", RichLog)

        try:
            if not self.log_file.exists():
                if self.last_position == 0:  # Only show once
                    log_widget.write(f"[dim]Log file not found: {self.log_file}[/]")
                    self.last_position = -1
                return

            with open(self.log_file, "r") as f:
                # Seek to last position
                f.seek(self.last_position)
                new_lines = f.readlines()

                if new_lines:
                    for line in new_lines:
                        line = line.rstrip()
                        if line:
                            # Color code log lines
                            if "ERROR" in line or "CRITICAL" in line:
                                log_widget.write(f"[red]{line}[/]")
                            elif "WARNING" in line:
                                log_widget.write(f"[yellow]{line}[/]")
                            elif "INFO" in line:
                                log_widget.write(f"[cyan]{line}[/]")
                            elif "DEBUG" in line:
                                log_widget.write(f"[dim]{line}[/]")
                            else:
                                log_widget.write(line)

                # Update position
                self.last_position = f.tell()

        except Exception as e:
            if self.last_position == 0:  # Only show error once
                log_widget.write(f"[red]Error reading log: {str(e)}[/]")
                self.last_position = -1

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-btn":
            self.app.pop_screen()
        elif event.button.id == "refresh-btn":
            self.load_log()
        elif event.button.id == "clear-btn":
            log_widget = self.query_one("#log-content", RichLog)
            log_widget.clear()

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.app.pop_screen()
