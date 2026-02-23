"""Debug Execution command for socialseed-e2e.

This module provides the debug-execution command functionality.
Debug failed test executions with AI assistance.
"""

import sys
from typing import Any, Dict, Optional

import click
from rich.console import Console

console = Console()


class DebugExecutionService:
    """Service class for debug execution operations.

    Responsibilities:
    - Initialize AI debugger
    - Get debug reports
    - Apply fixes
    """

    def __init__(self, project: str):
        """Initialize debug execution service.

        Args:
            project: Project directory path
        """
        self.project = project
        self.debugger = None

    def initialize(self) -> None:
        """Initialize the AI debugger."""
        from socialseed_e2e.ai_orchestrator import AIDebugger

        self.debugger = AIDebugger(self.project)

    def get_debug_report(self, execution_id: str) -> Dict[str, Any]:
        """Get debug report for execution.

        Args:
            execution_id: Execution ID to debug

        Returns:
            Debug report dictionary

        Raises:
            RuntimeError: If debug fails
        """
        if not self.debugger:
            self.initialize()

        return self.debugger.get_debug_report(execution_id)


class DebugExecutionPresenter:
    """Presenter class for debug-execution output formatting.

    Responsibilities:
    - Format debug reports for display
    - Format failure analyses
    - Format suggested fixes
    """

    @staticmethod
    def display_header() -> None:
        """Display debug header."""
        console.print("\n🐛 [bold cyan]AI-Powered Debug Analysis[/bold cyan]\n")

    @staticmethod
    def display_report(report: Dict[str, Any], execution_id: str) -> None:
        """Display debug report.

        Args:
            report: Debug report dictionary
            execution_id: Execution ID
        """
        if "error" in report:
            console.print(f"[red]Error:[/red] {report['error']}")
            return

        console.print(f"[bold]Execution ID:[/bold] {execution_id}")
        console.print(f"[bold]Total Failures:[/bold] {report['total_failures']}")

        avg_confidence = report.get("average_confidence", 0)
        console.print(f"[bold]Avg Confidence:[/bold] {avg_confidence:.2%}")

        console.print(
            f"[bold]Need Review:[/bold] {report.get('requiring_human_review', 0)}"
        )
        console.print()

        DebugExecutionPresenter._display_failures_by_type(report)
        DebugExecutionPresenter._display_analyses(report)

    @staticmethod
    def _display_failures_by_type(report: Dict[str, Any]) -> None:
        """Display failures grouped by type.

        Args:
            report: Debug report dictionary
        """
        failures = report.get("failures_by_type", {})

        if failures:
            console.print("[bold]Failures by Type:[/bold]")
            for error_type, count in failures.items():
                console.print(f"  {error_type}: {count}")
            console.print()

    @staticmethod
    def _display_analyses(report: Dict[str, Any]) -> None:
        """Display detailed failure analyses.

        Args:
            report: Debug report dictionary
        """
        analyses = report.get("analyses", [])

        if not analyses:
            return

        for analysis in analyses:
            console.print("-" * 50)
            console.print(f"[bold]Test:[/bold] {analysis.get('test_id', 'unknown')}")
            console.print(
                f"[bold]Failure Type:[/bold] {analysis.get('failure_type', 'unknown')}"
            )

            confidence = analysis.get("confidence_score", 0)
            console.print(f"[bold]Confidence:[/bold] {confidence:.2%}")

            root_cause = analysis.get("root_cause", "Unknown")
            console.print(f"[bold]Root Cause:[/bold] {root_cause}")
            console.print()

            DebugExecutionPresenter._display_suggested_fixes(analysis)

        console.print("-" * 50)
        console.print()

    @staticmethod
    def _display_suggested_fixes(analysis: Dict[str, Any]) -> None:
        """Display suggested fixes for an analysis.

        Args:
            analysis: Analysis dictionary
        """
        fixes = analysis.get("suggested_fixes", [])

        if fixes:
            console.print("[bold]Suggested Fixes:[/bold]")
            for fix in fixes:
                risk = fix.get("risk_level", "unknown")
                score = fix.get("applicability_score", 0)
                description = fix.get("description", "No description")
                console.print(f"  - {description} (risk: {risk}, score: {score:.2f})")
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


class DebugExecutionCommand:
    """Command class for debug-execution CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute debug workflow
    """

    def __init__(self):
        """Initialize debug-execution command."""
        self.service: Optional[DebugExecutionService] = None
        self.presenter = DebugExecutionPresenter()

    def execute(self, project: str, execution_id: str, apply_fix: bool) -> int:
        """Execute debug-execution command.

        Args:
            project: Project directory path
            execution_id: Execution ID to debug
            apply_fix: Whether to apply fixes automatically

        Returns:
            Exit code (0 for success, 1 for error)
        """
        self.presenter.display_header()

        try:
            # Get debug report
            self.service = DebugExecutionService(project)
            report = self.service.get_debug_report(execution_id)

            # Display results
            self.presenter.display_report(report, execution_id)

            # TODO: Apply fix if requested
            if apply_fix:
                console.print("[yellow]Apply fix not yet implemented[/yellow]")

            return 0

        except Exception as e:
            import traceback

            self.presenter.display_error(str(e), traceback.format_exc())
            return 1


# CLI command definition
@click.command(name="debug-execution")
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--execution-id",
    "-e",
    required=True,
    help="Execution ID to debug",
)
@click.option(
    "--apply-fix",
    is_flag=True,
    help="Apply suggested fix automatically",
)
def debug_execution_command(project: str, execution_id: str, apply_fix: bool) -> None:
    """Debug a failed test execution with AI.

    Analyzes failed tests, identifies root causes, and suggests
    or applies fixes automatically.

    Prerequisites:
        - Run 'e2e run --report json' first to generate execution records
        - Execution IDs are stored in .e2e/reports/

    Examples:
        e2e debug-execution --execution-id exec_20240211_120000
        e2e debug-execution --execution-id exec_20240211_120000 --apply-fix
    """
    command = DebugExecutionCommand()
    exit_code = command.execute(project, execution_id, apply_fix)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return debug_execution_command


def get_name():
    """Return the command name."""
    return "debug-execution"


def get_help():
    """Return the command help text."""
    return "Debug failed test executions with AI assistance"
