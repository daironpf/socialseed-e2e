"""Test list component for TUI."""

from typing import Dict, List

from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable, Static


class TestList(Static):
    """Component displaying the list of tests."""

    tests = reactive([])
    selected_test_id = reactive(None)

    def compose(self):
        """Compose the component."""
        yield DataTable(id="test-table")

    def on_mount(self):
        """Called when component is mounted."""
        table = self.query_one(DataTable)
        table.add_columns("Status", "Service", "Test Name", "Duration")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def watch_tests(self, tests: List[Dict]):
        """Watch for test list changes."""
        table = self.query_one(DataTable)
        table.clear()

        for test in tests:
            status = self._format_status(test.get("status", "pending"))
            service = test.get("service", "")
            name = test.get("name", "")
            duration = self._format_duration(test.get("duration"))

            table.add_row(
                status,
                service,
                name,
                duration,
                key=test.get("id"),
            )

    def update_test(self, test: Dict):
        """Update a single test in the list."""
        table = self.query_one(DataTable)
        test_id = test.get("id")

        # Find and update the row
        status = self._format_status(test.get("status", "pending"))
        service = test.get("service", "")
        name = test.get("name", "")
        duration = self._format_duration(test.get("duration"))

        table.update_cell(test_id, 0, status)
        table.update_cell(test_id, 3, duration)

    def _format_status(self, status: str) -> str:
        """Format status with icons."""
        icons = {
            "passed": "✓",
            "failed": "✗",
            "running": "⟳",
            "pending": "○",
            "skipped": "⊘",
        }
        return f"{icons.get(status, '?')} {status.upper()}"

    def _format_duration(self, duration: float) -> str:
        """Format duration."""
        if duration is None:
            return "-"
        return f"{duration:.2f}s"

    def on_data_table_row_selected(self, event):
        """Handle row selection."""
        test_id = event.row_key.value
        self.selected_test_id = test_id

        # Find the test data
        for test in self.tests:
            if test.get("id") == test_id:
                # Post message to parent
                self.post_message(self.TestSelected(test))
                break

    class TestSelected(Message):
        """Message sent when a test is selected."""

        def __init__(self, test: Dict):
            super().__init__()
            self.test = test
