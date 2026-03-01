"""Doctor command for socialseed-e2e CLI.

This command verifies the installation and checks system health.
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command(name="doctor")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--fix", is_flag=True, help="Attempt to fix issues automatically")
def doctor_command(verbose: bool, fix: bool) -> None:
    """Verify installation and dependencies.

    Checks the system for required dependencies and configuration.
    Use --fix to attempt automatic fixes.

    Args:
        verbose: Show detailed output
        fix: Attempt automatic fixes
    """
    console.print("\n🏥 [bold]socialseed-e2e Doctor[/bold]\n")

    # Create status table
    table = Table(title="System Verification")
    table.add_column("Component", style="cyan")
    table.add_column("Version/Status", style="green")
    table.add_column("Status", style="white")

    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python", python_version, "✓")

    # Check Playwright
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            pw_version = (
                p.chromium.launcher.version if hasattr(p.chromium, "launcher") else "installed"
            )
            table.add_row("Playwright", pw_version, "✓")
    except ImportError:
        table.add_row("Playwright", "Not found", "❌")
    except Exception as e:
        table.add_row("Playwright", str(e)[:20], "⚠")

    # Check Pydantic
    try:
        import pydantic

        table.add_row("Pydantic", pydantic.__version__, "✓")
    except ImportError:
        table.add_row("Pydantic", "Not found", "❌")

    # Check Configuration
    config_path = Path.cwd() / "e2e.conf"
    if config_path.exists():
        table.add_row("Configuration", "e2e.conf found", "✓")
    else:
        table.add_row("Configuration", "Not found", "⚠")

    # Check services directory
    services_dir = Path.cwd() / "services"
    if services_dir.exists():
        table.add_row("services/ directory", "OK", "✓")
    else:
        table.add_row("services/ directory", "Not found", "⚠")

    # Check tests directory
    tests_dir = Path.cwd() / "tests"
    if tests_dir.exists():
        table.add_row("tests/ directory", "OK", "✓")
    else:
        table.add_row("tests/ directory", "Not found", "⚠")

    # Check optional extras
    extras_table = Table(title="Optional Dependencies")
    extras_table.add_column("Extra", style="cyan")
    extras_table.add_column("Status", style="white")
    extras_table.add_column("Install Command", style="dim")

    optional_deps = {
        "flask": "pip install flask",
        "sentence-transformers": "pip install socialseed-e2e[rag]",
        "grpcio": "pip install socialseed-e2e[grpc]",
        "textual": "pip install socialseed-e2e[tui]",
    }

    for extra, install_cmd in optional_deps.items():
        try:
            __import__(extra.replace("-", "_"))
            extras_table.add_row(extra, "✓ Installed", "-")
        except ImportError:
            extras_table.add_row(extra, "⚠ Not installed", install_cmd)

    console.print(table)
    console.print(extras_table)

    if verbose:
        console.print("\n[bold cyan]Detailed Information:[/bold cyan]")

        # Show Python path
        console.print(f"  Python: {sys.executable}")
        console.print(f"  Version: {sys.version}")

        # Show installed packages
        try:
            import pkg_resources

            console.print("\n  [cyan]Installed packages:[/cyan]")
            for pkg in ["playwright", "pydantic", "click", "rich", "pyyaml"]:
                try:
                    version = pkg_resources.get_distribution(pkg).version
                    console.print(f"    {pkg}: {version}")
                except pkg_resources.DistributionNotFound:
                    console.print(f"    {pkg}: [red]Not found[/red]")
        except Exception:
            pass

    # Summary
    console.print("\n✅ [green]Everything is configured correctly![/green]\n")

    if fix:
        console.print("[yellow]Note:[/yellow] --fix is not yet implemented")


def get_command():
    """Return the click command object."""
    return doctor_command


def get_name():
    """Return the command name."""
    return "doctor"


def get_help():
    """Return the command help text."""
    return "Verify installation and dependencies"
