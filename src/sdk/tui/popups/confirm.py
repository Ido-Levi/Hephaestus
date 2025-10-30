"""Confirmation popup."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Container, Horizontal


class ConfirmPopup(ModalScreen):
    """Confirmation popup for destructive actions."""

    CSS = """
    ConfirmPopup {
        align: center middle;
    }

    #popup-container {
        width: 60;
        height: 15;
        border: thick red;
        background: $panel;
        padding: 2;
    }

    #popup-title {
        text-align: center;
        background: red;
        color: white;
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
        margin-top: 2;
    }

    Button {
        margin: 0 2;
        min-width: 12;
    }
    """

    def __init__(self, title: str, message: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.message = message
        self.confirmed = False

    def compose(self) -> ComposeResult:
        """Compose the confirmation popup."""
        with Container(id="popup-container"):
            yield Static(self.title, id="popup-title")
            yield Static(self.message, id="message-content")

            with Horizontal(id="button-row"):
                yield Button("Yes", variant="error", id="yes-btn")
                yield Button("No", variant="primary", id="no-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "yes-btn":
            self.confirmed = True
            self.dismiss(True)
        else:
            self.dismiss(False)

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss(False)
