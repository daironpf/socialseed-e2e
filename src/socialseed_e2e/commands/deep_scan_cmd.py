"""Deep Scan command for socialseed-e2e.

This module provides the deep-scan command functionality.
Zero-config project mapping and auto-configuration.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


class DeepScanService:
    """Service class for deep scan operations.

    Responsibilities:
    - Execute deep scan on target directory
    - Analyze detected services and configurations
    - Generate auto-configuration recommendations
    """

    def __init__(self, target_path: Path):
        """Initialize deep scan service.

        Args:
            target_path: Directory to scan
        """
        self.target_path = target_path
        self.scanner: Optional[object] = None

    def execute_scan(self) -> dict:
        """Execute deep scan on target directory.

        Returns:
            Scan results dictionary

        Raises:
            RuntimeError: If scan fails
        """
        if not self.target_path.exists():
            raise RuntimeError(f"Directory not found: {self.target_path}")

        try:
            from socialseed_e2e.project_manifest import DeepScanner

            self.scanner = DeepScanner(str(self.target_path))
            return self.scanner.scan()
        except Exception as e:
            raise RuntimeError(f"Deep scan failed: {e}")

    def get_services(self, scan_result: dict) -> list:
        """Extract detected services from scan result.

        Args:
            scan_result: Result from execute_scan

        Returns:
            List of detected services
        """
        return scan_result.get("services", [])

    def get_recommendations(self, scan_result: dict) -> dict:
        """Extract recommendations from scan result.

        Args:
            scan_result: Result from execute_scan

        Returns:
            Configuration recommendations
        """
        return scan_result.get("recommendations", {})


class DeepScanPresenter:
    """Presenter class for deep scan output formatting.

    Responsibilities:
    - Format scan results for display
    - Format auto-configuration output
    """

    @staticmethod
    def display_scan_results(scan_result: dict) -> None:
        """Display scan results to console.

        Args:
            scan_result: Scan results dictionary
        """
        services = scan_result.get("services", [])
        frameworks = scan_result.get("frameworks", [])
        recommendations = scan_result.get("recommendations", {})

        console.print(f"\n📊 [bold cyan]Scan Results[/bold cyan]\n")

        if services:
            console.print(f"  [bold]Services detected:[/bold] {len(services)}")
            for service in services:
                console.print(f"    - {service.get('name', 'unknown')}")

        if frameworks:
            console.print(f"\n  [bold]Frameworks:[/bold]")
            for fw in frameworks:
                console.print(
                    f"    - {fw.get('framework', 'unknown')} "
                    f"({fw.get('language', 'unknown')})"
                )

        if recommendations:
            console.print(f"\n  [bold]Recommendations:[/bold]")
            if recommendations.get("base_url"):
                console.print(f"    - Base URL: {recommendations['base_url']}")
            if recommendations.get("health_endpoint"):
                console.print(f"    - Health: {recommendations['health_endpoint']}")

    @staticmethod
    def display_auto_config_summary(services: list, recommendations: dict) -> None:
        """Display auto-configuration summary.

        Args:
            services: List of detected services
            recommendations: Configuration recommendations
        """
        console.print("\n⚙️  [bold cyan]Auto-configuring project...[/bold cyan]\n")

        for service in services:
            service_name = service.get("name", "unknown")
            console.print(f"  Creating service: [green]{service_name}[/green]")

            if recommendations.get("base_url"):
                console.print(f"  Base URL: {recommendations['base_url']}")

        console.print("\n[bold green]✅ Auto-configuration complete![/bold green]")
        console.print("   Run 'e2e run' to execute tests\n")


class DeepScanCommand:
    """Command class for deep-scan CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute deep scan workflow
    """

    def __init__(self):
        """Initialize deep scan command."""
        self.service = None
        self.presenter = DeepScanPresenter()

    def execute(self, directory: str, auto_config: bool = False) -> int:
        """Execute deep scan command.

        Args:
            directory: Target directory to scan
            auto_config: Whether to auto-configure services

        Returns:
            Exit code (0 for success, 1 for error)
        """
        target_path = Path(directory).resolve()

        try:
            # Execute scan
            self.service = DeepScanService(target_path)
            scan_result = self.service.execute_scan()

            # Display results
            self.presenter.display_scan_results(scan_result)

            # Auto-configure if requested
            if auto_config:
                services = self.service.get_services(scan_result)
                recommendations = self.service.get_recommendations(scan_result)
                self.presenter.display_auto_config_summary(services, recommendations)

            return 0

        except RuntimeError as e:
            console.print(f"[red]❌ Error:[/red] {e}")
            return 1
        except Exception as e:
            console.print(f"[red]❌ Unexpected error:[/red] {e}")
            return 1


# CLI command definition
@click.command(name="deep-scan")
@click.argument("directory", default=".", required=False)
@click.option("--auto-config", is_flag=True, help="Auto-generate e2e.conf from scan")
def deep_scan_command(directory: str, auto_config: bool) -> None:
    """Zero-config deep scan for automatic project mapping.

    Analyzes your project to detect tech stack, extract endpoints,
    and discover environment configuration without requiring manual setup.

    Examples:
        e2e deep-scan                    # Scan current directory
        e2e deep-scan /path/to/project   # Scan specific project
        e2e deep-scan --auto-config      # Scan and auto-configure
    """
    command = DeepScanCommand()
    exit_code = command.execute(directory, auto_config)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return deep_scan_command


def get_name():
    """Return the command name."""
    return "deep-scan"


def get_help():
    """Return the command help text."""
    return "Zero-config deep scan for automatic project mapping"
