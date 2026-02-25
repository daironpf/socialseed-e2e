"""Dashboard command for socialseed-e2e CLI.

This module provides the dashboard command using POO and SOLID principles.
"""

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


class DashboardLauncher:
    """Handles launching the web dashboard (Single Responsibility)."""

    def __init__(self):
        self.default_port = 5173
        self.default_host = "localhost"

    def launch(self, port: int, host: str, open_browser: bool) -> None:
        """Launch the Vue dashboard."""
        try:
            from socialseed_e2e.dashboard.vue_api import run_server

            console.print(
                "\n🚀 [bold green]Launching SocialSeed E2E Dashboard (Vue)...[/bold green]\n"
            )
            console.print(f"📊 Dashboard will be available at: http://{host}:{port}")
            console.print()

            run_server(host=host, port=port, open_browser=open_browser)

        except ImportError as e:
            self._install_and_launch(port, host, open_browser)

    def _install_and_launch(self, port: int, host: str, open_browser: bool) -> None:
        """Install dependencies and launch dashboard."""
        console.print("\n[yellow]⚠️ Installing dashboard dependencies...[/yellow]")

        try:
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "fastapi",
                    "uvicorn",
                    "python-socketio[asyncio]",
                    "-q",
                ]
            )
            console.print("[green]✓ Dependencies installed successfully!\n")

            from socialseed_e2e.dashboard.vue_api import run_server

            console.print(
                "\n🚀 [bold green]Launching SocialSeed E2E Dashboard (Vue)...[/bold green]\n"
            )
            console.print(f"📊 Dashboard will be available at: http://{host}:{port}")
            console.print()

            run_server(host=host, port=port, open_browser=open_browser)

        except Exception as e:
            console.print(f"\n[red]❌ Failed to launch dashboard:[/red] {e}")
            console.print(
                "Install dependencies manually: pip install fastapi uvicorn python-socketio"
            )
            sys.exit(1)


def launch_dev_mode(port: int, host: str, open_browser: bool) -> None:
    """Launch Vue in development mode."""
    vue_dir = Path(__file__).parent.parent / "dashboard" / "vue"

    console.print(
        "\n🚀 [bold green]Launching Vue Dashboard in DEV mode...[/bold green]\n"
    )

    try:
        subprocess.check_call(
            ["npm", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(
            "[red]❌ Node.js/npm not found. Install Node.js to use dev mode.[/red]"
        )
        sys.exit(1)

    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(port), "--host"],
        cwd=str(vue_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    console.print(f"📊 Dev Server Vue: http://{host}:{port}")
    console.print("Press Ctrl+C to stop the server\n")

    try:
        for line in proc.stdout:
            print(line, end="")
    except KeyboardInterrupt:
        proc.terminate()


@click.command()
@click.option("--port", "-p", default=5173, help="Port for the dashboard server")
@click.option("--host", "-h", default="localhost", help="Host for the dashboard server")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
@click.option("--dev", is_flag=True, help="Run in development mode (requires Node.js)")
def dashboard_cmd(port: int, host: str, no_browser: bool, dev: bool):
    """Launch the interactive web dashboard.

    Opens a local web interface to explore, run, and debug tests visually.
    This serves as the "Control Center" for the framework.

    Features:
    - Dashboard: Overview with statistics and quick actions
    - Test Explorer: Visual tree view of all test modules
    - Run Tests: Execute tests with real-time progress
    - History: View past test runs and their outcomes
    - Settings: Configure dashboard preferences

    Examples:
        e2e dashboard                    # Launch on default port 5173
        e2e dashboard --port 8080      # Launch on custom port
        e2e dashboard --no-browser     # Don't auto-open browser
        e2e dashboard --dev            # Run in development mode (requires Node.js)
    """
    if dev:
        launch_dev_mode(port, host, not no_browser)
    else:
        launcher = DashboardLauncher()
        launcher.launch(port, host, not no_browser)


def get_dashboard_command():
    """Get the dashboard command for lazy loading."""
    return dashboard_cmd


__all__ = ["dashboard_cmd", "get_dashboard_command"]
