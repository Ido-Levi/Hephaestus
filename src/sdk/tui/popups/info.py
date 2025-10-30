"""Info popup for displaying simple messages."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Container, Horizontal


class InfoPopup(ModalScreen):
    """Simple info popup for displaying messages."""

    CSS = """
    InfoPopup {
        align: center middle;
    }

    #popup-container {
        width: 60;
        height: 15;
        border: thick yellow;
        background: $panel;
        padding: 1;
    }

    #popup-title {
        text-align: center;
        background: yellow;
        color: black;
        text-style: bold;
        padding: 1;
        margin-bottom: 1;
    }

    #message-content {
        padding: 2;
        text-align: center;
        color: white;
    }

    #button-row {
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, message: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.message = message

    def compose(self) -> ComposeResult:
        """Compose the info popup."""
        with Container(id="popup-container"):
            yield Static(self.title, id="popup-title")
            yield Static(self.message, id="message-content")

            with Horizontal(id="button-row"):
                yield Button("OK", variant="primary", id="ok-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        self.app.pop_screen()

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key in ("escape", "enter"):
            self.app.pop_screen()
