"""Dashboard server module.

Handles the local web server setup and Streamlit process management.
"""

import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Optional

import click


class DashboardServer:
    """Manages the local dashboard server."""

    DEFAULT_PORT = 8501
    DEFAULT_HOST = "localhost"

    def __init__(self, port: int = DEFAULT_PORT, host: str = DEFAULT_HOST):
        self.port = port
        self.host = host
        self.app_path = Path(__file__).parent / "app.py"
        self.process: Optional[subprocess.Popen] = None

    def start(self, open_browser: bool = True) -> None:
        """Start the dashboard server."""
        # Check if streamlit is installed
        try:
            import streamlit
        except ImportError:
            click.echo("❌ Streamlit not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            click.echo("✅ Streamlit installed successfully")

        # Prepare command
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(self.app_path),
            "--server.port",
            str(self.port),
            "--server.address",
            self.host,
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ]

        click.echo("🚀 Starting SocialSeed E2E Dashboard...")
        click.echo(f"   URL: http://{self.host}:{self.port}")
        click.echo("   Press Ctrl+C to stop")
        click.echo()

        # Open browser if requested
        if open_browser:
            url = f"http://{self.host}:{self.port}"
            webbrowser.open(url)

        # Start Streamlit process
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            # Stream output
            for line in self.process.stdout:
                # Filter out some noisy Streamlit logs
                if "Watching" not in line and "%" not in line:
                    click.echo(line.rstrip())

        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping dashboard...")
            self.stop()
        except Exception as e:
            click.echo(f"❌ Error starting dashboard: {e}")
            sys.exit(1)

    def stop(self) -> None:
        """Stop the dashboard server."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            click.echo("✅ Dashboard stopped")

    def is_running(self) -> bool:
        """Check if the dashboard is running."""
        if self.process is None:
            return False
        return self.process.poll() is None


def launch_dashboard(port: int = 8501, open_browser: bool = True) -> None:
    """Launch the dashboard.

    Args:
        port: Port number for the dashboard
        open_browser: Whether to automatically open the browser
    """
    server = DashboardServer(port=port)
    server.start(open_browser=open_browser)
