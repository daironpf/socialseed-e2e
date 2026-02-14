"""Base TUI application using Textual."""

import asyncio
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Header

from socialseed_e2e.tui.components.log_view import LogView
from socialseed_e2e.tui.components.status_bar import StatusBar
from socialseed_e2e.tui.components.test_detail import TestDetail
from socialseed_e2e.tui.components.test_list import TestList


class TuiApp(App):
    """Main TUI application for SocialSeed E2E."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 2fr;
        grid-rows: auto 1fr auto auto;
    }

    Header {
        dock: top;
        height: 3;
    }

    #test-list {
        width: 100%;
        height: 100%;
        border: solid $primary;
    }

    #detail-container {
        width: 100%;
        height: 100%;
        border: solid $primary;
    }

    #log-view {
        height: 10;
        border: solid $primary-darken-2;
    }

    StatusBar {
        dock: bottom;
        height: 1;
    }

    .passed {
        color: $success;
    }

    .failed {
        color: $error;
    }

    .running {
        color: $warning;
    }

    .pending {
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "run_test", "Run Test"),
        ("R", "run_all", "Run All"),
        ("s", "stop", "Stop"),
        ("f", "filter", "Filter"),
        ("e", "environment", "Environment"),
        ("?", "help", "Help"),
        ("ctrl+c", "quit", "Quit"),
    ]

    current_test = reactive(None)
    tests = reactive([])
    is_running = reactive(False)
    environment = reactive("dev")

    def __init__(self, config_path: Optional[Path] = None):
        super().__init__()
        self.config_path = config_path or Path("e2e.conf")
        self.test_results = {}
        self._discover_tests()

    def _discover_tests(self):
        """Discover all tests in the project."""
        # TODO: Integrate with actual test discovery
        self.tests = [
            {
                "id": "1",
                "name": "test_health_check",
                "service": "auth-service",
                "status": "pending",
                "duration": None,
                "description": "Check if auth service is healthy",
            },
            {
                "id": "2",
                "name": "test_login_success",
                "service": "auth-service",
                "status": "pending",
                "duration": None,
                "description": "Test successful login flow",
            },
            {
                "id": "3",
                "name": "test_login_invalid_credentials",
                "service": "auth-service",
                "status": "pending",
                "duration": None,
                "description": "Test login with invalid credentials",
            },
            {
                "id": "4",
                "name": "test_create_payment",
                "service": "payment-service",
                "status": "passed",
                "duration": 0.45,
                "description": "Create a new payment",
            },
            {
                "id": "5",
                "name": "test_refund_payment",
                "service": "payment-service",
                "status": "failed",
                "duration": 1.20,
                "description": "Refund an existing payment",
            },
        ]

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header(show_clock=True)

        with Horizontal():
            # Left panel: Test list
            yield TestList(id="test-list")

            # Right panel: Test details
            with Container(id="detail-container"):
                yield TestDetail()

        # Bottom panel: Logs
        yield LogView(id="log-view")

        # Status bar
        yield StatusBar()

        # Footer with key bindings
        yield Footer()

    def on_mount(self):
        """Called when app is mounted."""
        self.title = "SocialSeed E2E - Test Commander"
        self.sub_title = f"Environment: {self.environment}"

        # Populate test list
        test_list = self.query_one(TestList)
        test_list.tests = self.tests

        # Select first test
        if self.tests:
            self.current_test = self.tests[0]

    def watch_current_test(self, test):
        """Watch for test selection changes."""
        detail = self.query_one(TestDetail)
        detail.test = test

    def action_run_test(self):
        """Run the currently selected test."""
        if self.current_test and not self.is_running:
            self._run_test(self.current_test)

    def action_run_all(self):
        """Run all tests."""
        if not self.is_running:
            self._run_all_tests()

    def action_stop(self):
        """Stop current execution."""
        self.is_running = False
        log_view = self.query_one(LogView)
        log_view.add_log("Execution stopped by user", level="warning")

    def action_filter(self):
        """Open filter dialog."""
        # TODO: Implement filter overlay
        pass

    def action_environment(self):
        """Toggle environment."""
        environments = ["dev", "staging", "prod"]
        current_idx = (
            environments.index(self.environment) if self.environment in environments else 0
        )
        next_idx = (current_idx + 1) % len(environments)
        self.environment = environments[next_idx]
        self.sub_title = f"Environment: {self.environment}"

        log_view = self.query_one(LogView)
        log_view.add_log(f"Switched to environment: {self.environment}", level="info")

    def action_help(self):
        """Show help overlay."""
        # TODO: Implement help overlay
        pass

    async def _run_test(self, test: dict):
        """Execute a single test."""
        self.is_running = True
        test["status"] = "running"

        # Update UI
        test_list = self.query_one(TestList)
        test_list.update_test(test)

        log_view = self.query_one(LogView)
        log_view.add_log(f"Running test: {test['name']}", level="info")

        # Simulate test execution (replace with actual test runner)
        await asyncio.sleep(0.5)

        # Random result for demo (replace with actual result)
        import random

        test["status"] = random.choice(["passed", "failed"])
        test["duration"] = round(random.uniform(0.1, 2.0), 2)

        # Update UI
        test_list.update_test(test)
        log_view.add_log(
            f"Test {test['name']}: {test['status']} ({test['duration']}s)",
            level="success" if test["status"] == "passed" else "error",
        )

        self.is_running = False

    async def _run_all_tests(self):
        """Execute all tests sequentially."""
        log_view = self.query_one(LogView)
        log_view.add_log("Starting test suite execution...", level="info")

        for test in self.tests:
            if test["status"] != "running":
                await self._run_test(test)
                await asyncio.sleep(0.1)  # Small delay between tests

        log_view.add_log("Test suite execution completed", level="info")


def launch_tui(config_path: Optional[Path] = None):
    """Launch the TUI application."""
    app = TuiApp(config_path=config_path)
    app.run()
