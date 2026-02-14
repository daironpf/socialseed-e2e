"""Log view component for TUI."""

from textual.reactive import reactive
from textual.widgets import RichLog


class LogView(RichLog):
    """Component displaying execution logs."""

    max_lines = reactive(1000)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_scroll = True
        self.highlight = True
        self.markup = True

    def on_mount(self):
        """Called when component is mounted."""
        self.write("[dim]Logs will appear here when tests are executed...[/dim]")

    def add_log(self, message: str, level: str = "info"):
        """Add a log entry."""
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        level_styles = {
            "debug": "dim",
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "critical": "bold red",
        }

        style = level_styles.get(level, "")
        prefix = f"[{timestamp}]"

        if style:
            formatted = f"{prefix} [{style}]{message}[/{style}]"
        else:
            formatted = f"{prefix} {message}"

        self.write(formatted)

    def clear_logs(self):
        """Clear all logs."""
        self.clear()
        self.add_log("Logs cleared", level="info")
