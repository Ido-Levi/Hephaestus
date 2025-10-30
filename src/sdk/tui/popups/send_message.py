"""Redesigned send message popup with better UX."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Static, Label
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
import requests


class SendMessagePopup(ModalScreen):
    """Popup for sending a direct message to an agent."""

    CSS = """
    SendMessagePopup {
        align: center middle;
    }

    #popup-container {
        width: 90;
        height: 30;
        border: thick cyan;
        background: $panel;
    }

    #popup-header {
        dock: top;
        height: 3;
        background: cyan;
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
        """Compose the send message popup."""
        with Container(id="popup-container"):
            yield Static("💬 SEND MESSAGE TO AGENT", id="popup-header")

            with VerticalScroll(id="form-container"):
                with Vertical(classes="field-group"):
                    yield Label("Recipient Agent ID", classes="field-label")
                    yield Label("The agent ID to send the message to (e.g., agent-xxx)", classes="field-help")
                    yield Input(placeholder="agent-xxx", id="recipient-input")

                with Vertical(classes="field-group"):
                    yield Label("Message", classes="field-label")
                    yield Label("Your message to the agent", classes="field-help")
                    yield TextArea(id="message-input")

            with Container(id="button-container"):
                with Horizontal(id="button-row"):
                    yield Button("Send Message", variant="success", id="send-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")

            yield Static("", id="status-bar")

    def on_mount(self) -> None:
        """Focus on recipient field."""
        self.query_one("#recipient-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.app.pop_screen()
        elif event.button.id == "send-btn":
            self.send_message()

    def send_message(self) -> None:
        """Send the message via API."""
        recipient_input = self.query_one("#recipient-input", Input)
        message_input = self.query_one("#message-input", TextArea)
        status_bar = self.query_one("#status-bar", Static)

        recipient = recipient_input.value.strip()
        message = message_input.text.strip()

        # Validate inputs
        if not recipient:
            status_bar.update("[red]✗ Recipient agent ID is required[/]")
            return

        if not message:
            status_bar.update("[red]✗ Message is required[/]")
            return

        # Send message via API
        try:
            api_url = self.sdk.config.api_base_url
            response = requests.post(
                f"{api_url}/api/send_message",
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": "Hephaestus-User",
                },
                json={
                    "message": message,
                    "sender_agent_id": "Hephaestus-User",
                    "recipient_agent_id": recipient,
                },
                timeout=10,
            )

            if response.status_code == 200:
                status_bar.update("[green]✓ Message sent successfully[/]")
                # Close popup after 1 second
                self.set_timer(1.0, self.app.pop_screen)
            else:
                error_msg = response.text[:100] if response.text else f"HTTP {response.status_code}"
                status_bar.update(f"[red]✗ Error: {error_msg}[/]")
        except Exception as e:
            status_bar.update(f"[red]✗ Error: {str(e)[:100]}[/]")

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.app.pop_screen()
