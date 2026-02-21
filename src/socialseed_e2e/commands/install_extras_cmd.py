"""Install extras command for socialseed-e2e CLI.

This module provides the install-extras command using POO and SOLID principles.
"""

import subprocess
import sys
from typing import List

import click
from rich.console import Console
from rich.table import Table


console = Console()


EXTRA_DEPENDENCIES = {
    "tui": {
        "description": "Terminal User Interface",
        "packages": ["textual>=0.41.0"],
    },
    "rag": {
        "description": "Semantic search and embeddings",
        "packages": ["sentence-transformers>=2.2.0", "numpy>=1.24.0"],
    },
    "grpc": {
        "description": "gRPC protocol support",
        "packages": ["grpcio>=1.59.0", "grpcio-tools>=1.59.0", "protobuf>=4.24.0"],
    },
    "secrets": {
        "description": "Secret scanning and management",
        "packages": ["hvac>=1.0.0", "boto3>=1.26.0"],
    },
    "dashboard": {
        "description": "Web dashboard (Vue.js + FastAPI)",
        "packages": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "python-socketio[asyncio]>=5.10.0",
        ],
    },
    "full": {
        "description": "All extras combined",
        "packages": [],
    },
}


class ExtraInstaller:
    """Handles installation of optional extras (Single Responsibility)."""

    def __init__(self):
        self.extras = EXTRA_DEPENDENCIES

    def list_extras(self) -> None:
        """Display available extras."""
        console.print("\n[bold cyan]📦 Available Optional Dependencies[/bold cyan]\n")
        table = Table(title="Install with: pip install socialseed-e2e[extra]")
        table.add_column("Extra", style="green", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Packages", style="dim")

        for name, info in self.extras.items():
            packages = (
                ", ".join(info["packages"][:2]) + "..."
                if len(info["packages"]) > 2
                else ", ".join(info["packages"])
            )
            if name == "full":
                packages = "All extras"
            table.add_row(name, info["description"], packages)

        console.print(table)
        console.print("\n[cyan]Usage:[/cyan]")
        console.print("  e2e install-extras tui")
        console.print("  e2e install-extras rag grpc")
        console.print("  pip install socialseed-e2e[tui,rag]")
        console.print()

    def install(self, extras_to_install: List[str]) -> None:
        """Install selected extras."""
        for extra in extras_to_install:
            if extra not in self.extras:
                console.print(f"[red]❌ Unknown extra:[/red] {extra}")
                console.print(f"Available: {', '.join(self.extras.keys())}")
                sys.exit(1)

            if extra == "full":
                extras_to_install = ["tui", "rag", "grpc", "secrets", "dashboard"]
                break

        console.print(
            f"\n[bold cyan]Installing extras:[/bold cyan] {', '.join(extras_to_install)}\n"
        )

        for extra in extras_to_install:
            packages = self.extras.get(extra, {}).get("packages", [])
            if not packages:
                continue

            package_str = " ".join(packages)
            console.print(f"Installing {extra}...")

            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        f"socialseed-e2e[{extra}]",
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    console.print(f"  [green]✓[/green] {extra} installed successfully")
                else:
                    console.print(f"  [yellow]⚠[/red] {extra}: {result.stderr}")
            except Exception as e:
                console.print(f"  [red]✗[/red] Failed to install {extra}: {e}")

        console.print("\n[bold green]✅ Installation complete![/bold green]\n")


@click.command()
@click.argument("extra", nargs=-1, required=False)
@click.option("--list", "list_extras", is_flag=True, help="List available extras")
@click.option("--all", "install_all", is_flag=True, help="Install all extras")
def install_extras_cmd(extra, list_extras: bool, install_all: bool):
    """Install optional dependencies (extras).

    Available extras:
        tui       - Terminal User Interface (textual)
        rag       - Semantic search and embeddings (sentence-transformers)
        grpc      - gRPC protocol support (grpcio)
        secrets   - Secret scanning and management
        dashboard - Web dashboard (Vue.js + FastAPI)
        full      - All extras combined

    Examples:
        e2e install-extras              # Interactive mode
        e2e install-extras dashboard   # Install dashboard only
        e2e install-extras rag grpc     # Install RAG and gRPC
        e2e install-extras --all        # Install all extras
        e2e install-extras --list       # Show available extras
    """
    installer = ExtraInstaller()

    if list_extras:
        installer.list_extras()
        return

    extras_to_install = []

    if install_all:
        extras_to_install = ["tui", "rag", "grpc", "secrets", "dashboard"]
    elif extra:
        extras_to_install = list(extra)
    else:
        console.print("\n[bold cyan]📦 Install Optional Dependencies[/bold cyan]\n")
        console.print(
            "Use --list to see available extras or specify extras to install."
        )
        console.print("Example: e2e install-extras tui rag")
        return

    installer.install(extras_to_install)


def get_install_extras_command():
    """Get the install-extras command for lazy loading."""
    return install_extras_cmd


__all__ = ["install_extras_cmd", "get_install_extras_command"]
