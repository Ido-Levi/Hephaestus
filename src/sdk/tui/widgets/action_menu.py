"""
Action menu widget with arrow key navigation
"""
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text


class ActionMenu(Widget):
    """Interactive action menu with arrow key navigation"""

    DEFAULT_CSS = """
    ActionMenu {
        width: 40%;
        height: 100%;
        border: solid green;
        background: $surface;
    }

    ActionMenu > VerticalScroll {
        height: 100%;
    }

    ActionMenu .menu-title {
        text-align: center;
        background: green;
        color: black;
        padding: 1;
        text-style: bold;
    }

    ActionMenu .menu-item {
        padding: 0 2;
        color: white;
    }

    ActionMenu .menu-item-selected {
        padding: 0 2;
        background: yellow;
        color: black;
        text-style: bold;
    }
    """

    selected_index: reactive[int] = reactive(0)

    ACTIONS = [
        ("📋 View Tasks", "tasks"),
        ("🤖 View Agents", "agents"),
        ("🧠 View Memories", "memories"),
        ("📊 View Metrics", "metrics"),
        ("➕ Create Task", "create_task"),
        ("💬 Send Message", "send_message"),
        ("📢 Broadcast Message", "broadcast"),
        ("📜 Backend Logs", "backend_logs"),
        ("🔍 Monitor Logs", "monitor_logs"),
        ("❤️  Health Check", "health_check"),
        ("🚪 Exit", "exit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with VerticalScroll():
            yield Static("🔥 FORGE ACTIONS 🔥", classes="menu-title")
            for idx, (label, _) in enumerate(self.ACTIONS):
                classes = "menu-item-selected" if idx == 0 else "menu-item"
                yield Static(label, classes=classes, id=f"action-{idx}")

    def on_mount(self) -> None:
        """Set up keyboard focus"""
        self.can_focus = True
        self.focus()

    def watch_selected_index(self, old_value: int, new_value: int) -> None:
        """Update visual selection when index changes"""
        # Deselect old item
        old_item = self.query_one(f"#action-{old_value}", Static)
        old_item.remove_class("menu-item-selected")
        old_item.add_class("menu-item")

        # Select new item
        new_item = self.query_one(f"#action-{new_value}", Static)
        new_item.remove_class("menu-item")
        new_item.add_class("menu-item-selected")

    def action_cursor_up(self) -> None:
        """Move selection up"""
        self.selected_index = max(0, self.selected_index - 1)

    def action_cursor_down(self) -> None:
        """Move selection down"""
        self.selected_index = min(len(self.ACTIONS) - 1, self.selected_index + 1)

    def key_up(self) -> None:
        """Handle up arrow key"""
        self.action_cursor_up()

    def key_down(self) -> None:
        """Handle down arrow key"""
        self.action_cursor_down()

    def key_enter(self) -> None:
        """Handle enter key - trigger selected action"""
        _, action_id = self.ACTIONS[self.selected_index]
        self.post_message(self.ActionSelected(action_id))

    class ActionSelected(Message):
        """Message sent when an action is selected"""

        def __init__(self, action_id: str) -> None:
            super().__init__()
            self.action_id = action_id
