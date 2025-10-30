"""Memories screen showing saved memories."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Static, Footer, Input
from textual.containers import Container, Vertical, Horizontal
import requests


class MemoriesScreen(Screen):
    """Screen showing all memories."""

    BINDINGS = [
        ("escape", "back", "Back to Forge"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    MemoriesScreen {
        background: black;
    }

    #header {
        dock: top;
        height: 3;
        background: $panel;
        text-align: center;
        content-align: center middle;
    }

    #search-bar {
        dock: top;
        height: 3;
        padding: 1;
    }

    #search-input {
        width: 100%;
    }

    #memories-container {
        height: 70%;
        border: solid magenta;
        margin: 1;
    }

    #details-container {
        height: 30%;
        border: solid yellow;
        margin: 1;
    }

    #details-content {
        padding: 1;
        color: white;
    }

    DataTable {
        height: 100%;
    }
    """

    def __init__(self, sdk_instance, **kwargs):
        super().__init__(**kwargs)
        self.sdk = sdk_instance
        self.memories_cache = {}  # Cache full memory data

    def compose(self) -> ComposeResult:
        """Compose the memories screen."""
        yield Static("🧠 MEMORIES", id="header")

        with Horizontal(id="search-bar"):
            yield Static("Search: ", classes="field-label")
            yield Input(placeholder="Search memories...", id="search-input")

        with Vertical():
            with Container(id="memories-container"):
                yield DataTable(id="memories-table", cursor_type="row")

            with Container(id="details-container"):
                yield Static("Select a memory to view details...", id="details-content")

        yield Footer()

    def on_mount(self) -> None:
        """Set up the screen after mounting."""
        table = self.query_one("#memories-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_columns("ID", "Type", "Agent", "Created", "Content Preview")

        # Load memories
        self.load_memories()

    def load_memories(self, search_query: str = "") -> None:
        """Load memories from the backend."""
        table = self.query_one("#memories-table", DataTable)
        table.clear()

        try:
            # Get memories via API
            api_url = self.sdk.config.api_base_url
            params = {}
            if search_query:
                params["search"] = search_query

            response = requests.get(
                f"{api_url}/api/memories",
                params=params,
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                memories = data.get("memories", [])

                # Cache full memory data
                self.memories_cache = {m.get("id"): m for m in memories}

                for memory in memories:
                    # Truncate content for preview
                    content = memory.get("content", "")[:50]
                    if len(memory.get("content", "")) > 50:
                        content += "..."

                    created = memory.get("created_at", "")[:19]  # Remove microseconds

                    table.add_row(
                        memory.get("id", "")[:8],
                        memory.get("memory_type", ""),
                        memory.get("agent_id", "")[:12] if memory.get("agent_id") else "-",
                        created,
                        content,
                        key=memory.get("id", ""),
                    )
            else:
                table.add_row("ERROR", "-", "-", "-", f"HTTP {response.status_code}")

        except Exception as e:
            table.add_row("ERROR", "-", "-", "-", f"Failed to load: {str(e)}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        if event.input.id == "search-input":
            self.load_memories(event.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection to show memory details."""
        memory_id = event.row_key.value

        # Get memory from cache
        memory = self.memories_cache.get(memory_id)
        if memory:
            self.show_memory_details(memory)
        else:
            self.show_error(f"Memory {memory_id} not found in cache")

    def show_memory_details(self, memory: dict) -> None:
        """Display memory details in the details panel."""
        details = self.query_one("#details-content", Static)

        text = f"""[bold yellow]Memory ID:[/] {memory.get('id', 'N/A')}
[bold yellow]Type:[/] {memory.get('memory_type', 'N/A')}
[bold yellow]Agent:[/] {memory.get('agent_id', 'N/A')}
[bold yellow]Created:[/] {memory.get('created_at', 'N/A')}

[bold yellow]Content:[/]
{memory.get('content', 'N/A')}
"""
        details.update(text)

    def show_error(self, message: str) -> None:
        """Show error message in details panel."""
        details = self.query_one("#details-content", Static)
        details.update(f"[red]Error:[/] {message}")

    def action_refresh(self) -> None:
        """Refresh memories table."""
        search_input = self.query_one("#search-input", Input)
        self.load_memories(search_input.value)

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
