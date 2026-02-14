"""Status bar component for TUI."""

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing hotkeys and current state."""

    is_running = reactive(False)
    environment = reactive("dev")
    selected_count = reactive(0)
    total_count = reactive(0)

    def compose(self):
        """Compose the component."""
        yield Static(id="status-content")

    def watch_is_running(self, is_running: bool):
        """Watch for running state changes."""
        self._update_status()

    def watch_environment(self, environment: str):
        """Watch for environment changes."""
        self._update_status()

    def watch_selected_count(self, count: int):
        """Watch for selection changes."""
        self._update_status()

    def watch_total_count(self, count: int):
        """Watch for total count changes."""
        self._update_status()

    def _update_status(self):
        """Update the status display."""
        content = self.query_one("#status-content", Static)

        # Build status line
        parts = []

        # Running indicator
        if self.is_running:
            parts.append("[bold yellow]⟳ RUNNING[/bold yellow]")
        else:
            parts.append("[green]⏹ READY[/green]")

        # Environment
        env_colors = {
            "dev": "blue",
            "staging": "yellow",
            "prod": "red",
        }
        env_color = env_colors.get(self.environment, "white")
        parts.append(f"[{env_color}]🌍 {self.environment.upper()}[/{env_color}]")

        # Selection count
        parts.append(f"📋 {self.selected_count}/{self.total_count} tests")

        # Hotkeys
        parts.append("[dim]Press '?' for help[/dim]")

        status = " | ".join(parts)
        content.update(status)

    def on_mount(self):
        """Called when component is mounted."""
        self._update_status()
