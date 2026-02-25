"""Mock commands for socialseed-e2e CLI.

This module provides the mock commands using POO and SOLID principles.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


class MockAnalyzer:
    """Handles analysis of external API dependencies (Single Responsibility)."""

    def __init__(self, target_path: Path):
        self.target_path = target_path

    def analyze(self) -> dict:
        """Run the analysis."""
        from socialseed_e2e.ai_mocking import ExternalAPIAnalyzer

        analyzer = ExternalAPIAnalyzer(self.target_path)
        return analyzer.analyze_project()

    def display_results(self, detected_apis: dict, format: str = "table") -> None:
        """Display analysis results."""
        if not detected_apis:
            console.print("[yellow]⚠ No external APIs detected[/yellow]")
            console.print("   Your project might not have third-party integrations.\n")
            return

        if format == "table":
            table = Table(title="Detected External APIs")
            table.add_column("Service", style="cyan")
            table.add_column("Base URL", style="green")
            table.add_column("Calls", style="yellow")
            table.add_column("Auth Detected", style="white")
            table.add_column("Env Vars", style="dim")

            for service_name, dependency in detected_apis.items():
                table.add_row(
                    service_name,
                    dependency.base_url[:50] + "..."
                    if len(dependency.base_url) > 50
                    else dependency.base_url,
                    str(len(dependency.detected_calls)),
                    "✓" if dependency.auth_header_detected else "✗",
                    ", ".join(dependency.env_var_keys[:2])
                    + ("..." if len(dependency.env_var_keys) > 2 else ""),
                )

            console.print(table)

            console.print("\n[bold]Details:[/bold]\n")
            for service_name, dependency in detected_apis.items():
                console.print(f"[cyan]{service_name}:[/cyan]")
                console.print(f"   Base URL: {dependency.base_url}")
                console.print(f"   Detected calls: {len(dependency.detected_calls)}")

                if dependency.detected_calls:
                    console.print("   Files:")
                    for call in dependency.detected_calls[:3]:
                        console.print(
                            f"     • {call.file_path}:{call.line_number} ({call.method})"
                        )
                    if len(dependency.detected_calls) > 3:
                        console.print(
                            f"     ... and {len(dependency.detected_calls) - 3} more"
                        )

                if dependency.env_var_keys:
                    console.print(
                        f"   Environment variables: {', '.join(dependency.env_var_keys)}"
                    )


class MockValidator:
    """Handles API contract validation (Single Responsibility)."""

    def validate(self, contract_path: Path, verbose: bool = False) -> dict:
        """Validate contract file."""
        from socialseed_e2e.ai_mocking import ContractValidator

        validator = ContractValidator()
        return validator.validate_contract_file(contract_path)

    def display_results(self, results: dict, verbose: bool = False) -> None:
        """Display validation results."""
        if not results:
            console.print("[yellow]⚠ No tests found in contract file[/yellow]\n")
            return

        total_valid = 0
        total_invalid = 0

        for test_name, result in results.items():
            if result.is_valid:
                console.print(f"  [green]✓[/green] {test_name}")
                total_valid += 1
            else:
                console.print(f"  [red]✗[/red] {test_name}")
                total_invalid += 1

                if verbose:
                    for error in result.errors:
                        console.print(
                            f"     [red]Error:[/red] {error.field} - {error.message}"
                        )
                        if error.expected is not None:
                            console.print(f"       Expected: {error.expected}")
                        if error.actual is not None:
                            console.print(f"       Actual: {error.actual}")

                    for warning in result.warnings:
                        console.print(
                            f"     [yellow]Warning:[/yellow] {warning.field} - {warning.message}"
                        )

        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Valid: [green]{total_valid}[/green]")
        console.print(f"  Invalid: [red]{total_invalid}[/red]\n")


@click.command(name="mock-analyze")
@click.argument("directory", default=".", required=False)
@click.option(
    "--output",
    "-o",
    default="external_apis.json",
    help="Output file for results",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def get_mock_analyze_command(
    directory: str = ".", output: str = "external_apis.json", format: str = "table"
):
    """Analyze project for external API dependencies (Issue #191).

    Scans codebase to detect calls to third-party APIs like Stripe,
    Google Maps, AWS, SendGrid, and other external services.

    Examples:
        e2e mock-analyze                    # Analyze current directory
        e2e mock-analyze /path/to/project   # Analyze specific project
        e2e mock-analyze -f json            # Output as JSON
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🔍 [bold cyan]External API Analysis[/bold cyan]")
    console.print(f"   Project: {target_path}\n")

    try:
        analyzer = MockAnalyzer(target_path)
        detected_apis = analyzer.analyze()
        analyzer.display_results(detected_apis, format)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command(name="mock-analyze")
@click.argument("contract_file")
@click.option(
    "--service",
    "-s",
    help="Specify service to validate",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation output",
)
def get_mock_validate_command(
    contract_file: str, service: Optional[str] = None, verbose: bool = False
):
    """Validate API contract against mock schema (Issue #191).

    Validates that requests and responses conform to the expected
    contract for external APIs, ensuring consistent mocking.

    Examples:
        e2e mock-validate contracts/stripe.json     # Validate contract
        e2e mock-validate contracts.json -s stripe  # Specify service
        e2e mock-validate contracts.json -v          # Verbose output
    """
    contract_path = Path(contract_file)

    if not contract_path.exists():
        console.print(f"[red]❌ Error:[/red] Contract file not found: {contract_path}")
        sys.exit(1)

    console.print("\n✅ [bold cyan]Contract Validation[/bold cyan]")
    console.print(f"   File: {contract_path}\n")

    try:
        validator = MockValidator()
        results = validator.validate(contract_path)
        validator.display_results(results, verbose)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


def get_mock_command():
    """Return mock command group."""
    return get_mock_analyze_command()


def get_mock_validate():
    """Return mock-validate command."""
    return get_mock_validate_command()
