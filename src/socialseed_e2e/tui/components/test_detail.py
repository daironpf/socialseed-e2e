"""Test detail component for TUI."""

from typing import Dict, Optional

from rich.panel import Panel
from rich.text import Text
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label, Static


class TestDetail(Static):
    """Component displaying test details."""

    test = reactive(None)

    def compose(self):
        """Compose the component."""
        with Vertical():
            yield Label(id="test-name", classes="title")
            yield Label(id="test-service")
            yield Label(id="test-status")
            yield Label(id="test-duration")
            yield Static(id="test-description")
            yield Static(id="test-result")

    def watch_test(self, test: Optional[Dict]):
        """Watch for test selection changes."""
        if test is None:
            self._show_empty()
            return

        # Update all fields
        name_label = self.query_one("#test-name", Label)
        name_label.update(f"📋 {test.get('name', 'Unnamed Test')}")

        service_label = self.query_one("#test-service", Label)
        service_label.update(f"🔧 Service: {test.get('service', 'Unknown')}")

        status_label = self.query_one("#test-status", Label)
        status = test.get("status", "pending")
        status_text = self._get_status_rich(status)
        status_label.update(status_text)

        duration_label = self.query_one("#test-duration", Label)
        duration = test.get("duration")
        if duration:
            duration_label.update(f"⏱ Duration: {duration:.2f}s")
        else:
            duration_label.update("⏱ Duration: Not run")

        desc_static = self.query_one("#test-description", Static)
        description = test.get("description", "No description available")
        desc_static.update(Panel(description, title="Description"))

        result_static = self.query_one("#test-result", Static)
        if status == "passed":
            result_static.update(
                Panel(
                    "✓ Test passed successfully\n\n" + "All assertions were satisfied.",
                    title="Result",
                    border_style="green",
                )
            )
        elif status == "failed":
            result_static.update(
                Panel(
                    "✗ Test failed\n\n" + "Check the logs for details on the failure.",
                    title="Result",
                    border_style="red",
                )
            )
        elif status == "running":
            result_static.update(
                Panel(
                    "⟳ Test is currently running...",
                    title="Result",
                    border_style="yellow",
                )
            )
        else:
            result_static.update(
                Panel(
                    "○ Test has not been run yet\n\n" + "Press 'r' to run this test.",
                    title="Result",
                    border_style="dim",
                )
            )

    def _show_empty(self):
        """Show empty state."""
        name_label = self.query_one("#test-name", Label)
        name_label.update("No test selected")

        for widget_id in ["#test-service", "#test-status", "#test-duration"]:
            label = self.query_one(widget_id, Label)
            label.update("")

        desc_static = self.query_one("#test-description", Static)
        desc_static.update("Select a test from the list to view details")

    def _get_status_rich(self, status: str) -> Text:
        """Get rich text for status."""
        styles = {
            "passed": ("✓ PASSED", "bold green"),
            "failed": ("✗ FAILED", "bold red"),
            "running": ("⟳ RUNNING", "bold yellow"),
            "pending": ("○ PENDING", "dim"),
            "skipped": ("⊘ SKIPPED", "dim"),
        }
        text, style = styles.get(status, (f"? {status.upper()}", ""))
        return Text(text, style=style)
