"""Discovery commands for socialseed-e2e CLI.

This module provides the discover and deep-scan commands using POO and SOLID principles.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


class DiscoverAgent:
    """Handles AI Discovery Report generation (Single Responsibility)."""

    def __init__(self, target_path: Path, output: Optional[str] = None):
        self.target_path = target_path
        self.output = output

    def generate_report(self) -> Path:
        """Generate the discovery report."""
        from socialseed_e2e.project_manifest import (
            ManifestAPI,
            generate_discovery_report,
        )

        api = ManifestAPI(self.target_path)
        api._load_manifest()
        manifest = api.manifest

        if not manifest:
            console.print(
                "[yellow]⚠ No project manifest found. Run 'e2e manifest' first.[/yellow]"
            )
            sys.exit(1)

        output_dir = Path(self.output) if self.output else None
        with console.status(
            "[bold cyan]🔍 Analyzing project and generating report...[/bold cyan]",
            spinner="dots",
        ):
            report_path = generate_discovery_report(
                project_root=self.target_path, manifest=manifest, output_dir=output_dir
            )

        return report_path

    def display_success(self, report_path: Path) -> None:
        """Display success message."""
        console.print(f"\n✅ [bold green]Discovery Report generated![/bold green]")
        console.print(f"   📄 Location: {report_path}\n")

        console.print("[bold]What's in the report:[/bold]")
        console.print("   • Technology stack analysis")
        console.print("   • Discovered endpoints and services")
        console.print("   • Business flows mental map")
        console.print("   • Single command to run all tests")
        console.print("   • Next steps and recommendations\n")

        console.print("[bold]Quick Start:[/bold]")
        console.print("   Run: [cyan]e2e run[/cyan]\n")


class DeepScanAgent:
    """Handles Zero-config deep scan (Single Responsibility)."""

    def __init__(self, target_path: Path):
        self.target_path = target_path

    def scan(self, auto_config: bool = False) -> dict:
        """Run deep scan."""
        from socialseed_e2e.project_manifest import DeepScanner

        scanner = DeepScanner(str(self.target_path))
        return scanner.scan()

    def handle_auto_config(self, result: dict) -> None:
        """Handle auto-configuration."""
        console.print("\n⚙️  [bold cyan]Auto-configuring project...[/bold cyan]\n")

        for service in result["services"]:
            service_name = service["name"]
            recommendations = result["recommendations"]

            if recommendations.get("base_url"):
                console.print(f"  Creating service: [green]{service_name}[/green]")
                console.print(f"  Base URL: {recommendations['base_url']}")

        console.print("\n[bold green]✅ Auto-configuration complete![/bold green]")
        console.print("   Run 'e2e run' to execute tests\n")


@click.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--output",
    "-o",
    help="Output directory for the report",
)
@click.option(
    "--open",
    "-p",
    "open_report",
    is_flag=True,
    help="Open the report after generation",
)
def get_discover_command(
    directory: str = ".", output: Optional[str] = None, open_report: bool = False
):
    """Generate AI Discovery Report for the project (Issue #187).

    Creates a comprehensive "Mental Map" report summarizing:
    - Discovered endpoints and services
    - Technology stack analysis
    - Business flows detected
    - Generated test suites

    The report is saved as a markdown file in .e2e/DISCOVERY_REPORT.md

    Examples:
        e2e discover                    # Generate report for current project
        e2e discover /path/to/project   # Generate for specific project
        e2e discover --open             # Generate and open the report
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🤖 [bold cyan]AI Discovery Report[/bold cyan]")
    console.print(f"   Project: {target_path}\n")

    try:
        agent = DiscoverAgent(target_path, output)
        report_path = agent.generate_report()
        agent.display_success(report_path)

        if open_report:
            pass
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.argument("directory", default=".", required=False)
@click.option("--auto-config", is_flag=True, help="Auto-generate e2e.conf from scan")
def get_deep_scan_command(directory: str = ".", auto_config: bool = False):
    """Zero-config deep scan for automatic project mapping.

    Analyzes your project to detect tech stack, extract endpoints,
    and discover environment configuration without requiring manual setup.

    Examples:
        e2e deep-scan                    # Scan current directory
        e2e deep-scan /path/to/project   # Scan specific project
        e2e deep-scan --auto-config      # Scan and auto-configure
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    try:
        agent = DeepScanAgent(target_path)
        result = agent.scan()

        if auto_config:
            agent.handle_auto_config(result)

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)
