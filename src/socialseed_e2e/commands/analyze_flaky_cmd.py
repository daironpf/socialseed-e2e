"""Analyze Flaky command for socialseed-e2e.

This module provides the analyze-flaky command functionality.
Analyze test files for flakiness patterns.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


class FlakyAnalyzerService:
    """Service class for analyzing test flakiness.

    Responsibilities:
    - Analyze test files for flaky patterns
    - Generate flakiness reports
    - Provide recommendations
    """

    def __init__(self, project: str):
        """Initialize flaky analyzer service.

        Args:
            project: Project directory path
        """
        self.project = project
        self.healer = None

    def initialize(self) -> None:
        """Initialize the self-healer for analysis."""
        from socialseed_e2e.ai_orchestrator import SelfHealer

        self.healer = SelfHealer(self.project)

    def analyze_test_file(self, test_file: str) -> Dict[str, Any]:
        """Analyze a test file for flakiness patterns.

        Args:
            test_file: Path to test file

        Returns:
            Analysis report dictionary
        """
        if not self.healer:
            self.initialize()

        return self.healer.analyze_test_file(test_file)


class FlakyAnalyzerPresenter:
    """Presenter class for analyze-flaky output formatting.

    Responsibilities:
    - Format analysis results for display
    - Format pattern detection tables
    - Format recommendations
    """

    SEVERITY_COLORS = {
        "high": "red",
        "medium": "yellow",
        "low": "blue",
    }

    @staticmethod
    def display_header() -> None:
        """Display analysis header."""
        console.print("\n🔍 [bold blue]Analyzing Test for Flakiness[/bold blue]\n")

    @staticmethod
    def display_results(report: Dict[str, Any]) -> None:
        """Display analysis results.

        Args:
            report: Analysis report dictionary
        """
        console.print(f"[bold]File:[/bold] {report['test_file']}")
        console.print()

        patterns = report.get("flakiness_patterns", [])

        if patterns:
            FlakyAnalyzerPresenter._display_patterns(patterns)
            FlakyAnalyzerPresenter._display_recommendations(report)
        else:
            FlakyAnalyzerPresenter._display_no_patterns()

    @staticmethod
    def _display_patterns(patterns: List[Dict[str, Any]]) -> None:
        """Display detected flakiness patterns.

        Args:
            patterns: List of detected patterns
        """
        console.print(f"[yellow]⚠ Found {len(patterns)} flakiness patterns:[/yellow]")
        console.print()

        table = Table(title="Detected Patterns")
        table.add_column("Pattern", style="bold")
        table.add_column("Severity")
        table.add_column("Line")
        table.add_column("Description")

        for pattern in patterns:
            severity = pattern.get("severity", "low")
            severity_color = FlakyAnalyzerPresenter.SEVERITY_COLORS.get(
                severity, "white"
            )

            table.add_row(
                pattern.get("pattern", "unknown"),
                f"[{severity_color}]{severity.upper()}[/{severity_color}]",
                str(pattern.get("line", "-")),
                pattern.get("description", ""),
            )

        console.print(table)
        console.print()

    @staticmethod
    def _display_recommendations(report: Dict[str, Any]) -> None:
        """Display recommendations.

        Args:
            report: Analysis report dictionary
        """
        recommendations = report.get("recommendations", [])

        if recommendations:
            console.print("[bold]Recommendations:[/bold]")
            for i, rec in enumerate(recommendations, 1):
                console.print(f"  {i}. {rec}")
            console.print()

    @staticmethod
    def _display_no_patterns() -> None:
        """Display no patterns found message."""
        console.print("[green]✓ No flakiness patterns detected[/green]")
        console.print()

    @staticmethod
    def display_error(message: str, traceback: Optional[str] = None) -> None:
        """Display error message.

        Args:
            message: Error message
            traceback: Optional traceback
        """
        console.print(f"\n[red]Error:[/red] {message}")

        if traceback:
            console.print(traceback)


class AnalyzeFlakyCommand:
    """Command class for analyze-flaky CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute analysis workflow
    """

    def __init__(self):
        """Initialize analyze-flaky command."""
        self.service: Optional[FlakyAnalyzerService] = None
        self.presenter = FlakyAnalyzerPresenter()

    def execute(self, project: str, test_file: str) -> int:
        """Execute analyze-flaky command.

        Args:
            project: Project directory path
            test_file: Path to test file

        Returns:
            Exit code (0 for success, 1 for error)
        """
        self.presenter.display_header()

        try:
            # Initialize and run analysis
            self.service = FlakyAnalyzerService(project)
            report = self.service.analyze_test_file(test_file)

            # Display results
            self.presenter.display_results(report)

            return 0

        except Exception as e:
            import traceback

            self.presenter.display_error(str(e), traceback.format_exc())
            return 1


# CLI command definition
@click.command(name="analyze-flaky")
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--test-file",
    "-f",
    required=True,
    help="Test file to analyze",
    type=click.Path(exists=True, dir_okay=False),
)
def analyze_flaky_command(project: str, test_file: str) -> None:
    """Analyze a test file for flakiness patterns.

    Scans the test code and identifies patterns that commonly
    cause flaky tests, providing recommendations for fixes.

    Examples:
        e2e analyze-flaky --test-file services/users/modules/test_login.py
    """
    command = AnalyzeFlakyCommand()
    exit_code = command.execute(project, test_file)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return analyze_flaky_command


def get_name():
    """Return the command name."""
    return "analyze-flaky"


def get_help():
    """Return the command help text."""
    return "Analyze test files for flakiness patterns"
