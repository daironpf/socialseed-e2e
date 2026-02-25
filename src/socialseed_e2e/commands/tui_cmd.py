"""TUI command for socialseed-e2e CLI.

This module provides the tui command using POO and SOLID principles.
"""

import sys

import click
from rich.console import Console

console = Console()


class TULauncher:
    """Handles launching the terminal UI (Single Responsibility)."""

    def launch(self, config: str, service: str, auto_install: bool) -> None:
        """Launch the TUI."""
        from socialseed_e2e.cli import check_and_install_extra
        
        # Determine whether to auto install based on the command line flag,
        # but the request asks to auto install by default.
        # We enforce auto_install=True here for explicit lazy loading
        if not check_and_install_extra("tui", auto_install=True):
            sys.exit(1)

        self._run_tui(config, service)

    def _run_tui(self, config: str, service: str) -> None:
        """Run the TUI application."""
        from socialseed_e2e.tui.app import launch_tui

        console.print("\n🚀 [bold green]Launching TUI...[/bold green]\n")
        launch_tui(config_path=config, service_filter=service)


@click.command()
@click.option("--config", "-c", default="e2e.conf", help="Path to configuration file")
@click.option("--service", "-s", default=None, help="Service to filter")
@click.option(
    "--yes", "-y", is_flag=True, help="Auto-install dependencies without prompting"
)
def tui_cmd(config: str, service: str, yes: bool):
    """Launch the Rich Terminal Interface (TUI).

    Opens an interactive terminal-based UI for power users who prefer
    keyboard navigation and split-pane views over web interfaces.

    Features:
    - Keyboard Navigation: Navigate test suites with arrow keys
    - Quick Actions: Run/Stop/Filter tests with hotkeys (r, s, f)
    - Split View: Test list and execution details side-by-side
    - Instant Feedback: Colored status indicators
    - Environment Toggling: Switch environments without restarting

    Key Bindings:
    - ↑/↓: Navigate test list
    - Enter: Run selected test
    - r: Run selected test
    - R: Run all tests
    - s: Stop running tests
    - f: Toggle filter
    - e: Switch environment
    - q: Quit
    - ?: Show help

    Examples:
        e2e tui                    # Launch TUI
        e2e tui --service users    # Launch with service filter
        e2e tui --config ./e2e.conf  # Use custom config
    """
    launcher = TULauncher()
    launcher.launch(config, service, yes)


def get_tui_command():
    """Get the tui command for lazy loading."""
    return tui_cmd


__all__ = ["tui_cmd", "get_tui_command"]
