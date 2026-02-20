"""Dashboard command for socialseed-e2e CLI.

This module provides the dashboard command using POO and SOLID principles.
"""

import subprocess
import sys

import click
from rich.console import Console


console = Console()


class DashboardLauncher:
    """Handles launching the web dashboard (Single Responsibility)."""

    def __init__(self):
        self.default_port = 8501
        self.default_host = "localhost"

    def launch(self, port: int, host: str, open_browser: bool) -> None:
        """Launch the dashboard."""
        try:
            from socialseed_e2e.dashboard.server import launch_dashboard

            console.print(
                "\n🚀 [bold green]Launching SocialSeed E2E Dashboard...[/bold green]\n"
            )
            console.print(f"📊 Dashboard will be available at: http://{host}:{port}")
            console.print()

            launch_dashboard(port=port, open_browser=open_browser)

        except ImportError:
            self._install_and_launch(port, host, open_browser)

    def _install_and_launch(self, port: int, host: str, open_browser: bool) -> None:
        """Install streamlit and launch dashboard."""
        console.print("\n[red]❌ Streamlit not found. Installing...[/red]")

        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "streamlit", "-q"]
            )
            console.print("[green]✓ Streamlit installed successfully!\n")

            from socialseed_e2e.dashboard.server import launch_dashboard

            console.print(
                "\n🚀 [bold green]Launching SocialSeed E2E Dashboard...[/bold green]\n"
            )
            console.print(f"📊 Dashboard will be available at: http://{host}:{port}")
            console.print()

            launch_dashboard(port=port, open_browser=open_browser)

        except Exception as e:
            console.print(f"\n[red]❌ Failed to launch dashboard:[/red] {e}")
            console.print("Install streamlit manually: pip install streamlit")
            sys.exit(1)


@click.command()
@click.option("--port", "-p", default=8501, help="Port for the dashboard server")
@click.option("--host", "-h", default="localhost", help="Host for the dashboard server")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def dashboard_cmd(port: int, host: str, no_browser: bool):
    """Launch the interactive web dashboard.

    Opens a local web interface to explore, run, and debug tests visually.
    This serves as the "Control Center" for the framework.

    Features:
    - Test Explorer: Visual tree view of all test modules
    - One-Click Run: Execute individual tests, suites, or folders
    - Rich Request/Response Viewer: Inspect headers, bodies, and status codes
    - Parameterization: UI inputs to override test variables at runtime
    - Live Logs: Real-time streaming of test execution logs
    - Run History: View past test runs and their outcomes

    Examples:
        e2e dashboard                    # Launch on default port 8501
        e2e dashboard --port 8080      # Launch on custom port
        e2e dashboard --no-browser      # Don't auto-open browser
    """
    launcher = DashboardLauncher()
    launcher.launch(port, host, not no_browser)


def get_dashboard_command():
    """Get the dashboard command for lazy loading."""
    return dashboard_cmd


__all__ = ["dashboard_cmd", "get_dashboard_command"]
