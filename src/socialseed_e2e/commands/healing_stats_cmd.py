"""Healing Stats command for socialseed-e2e.

This module provides the healing-stats command functionality.
View self-healing statistics for tests.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


class HealingStatsService:
    """Service class for healing statistics operations.

    Responsibilities:
    - Initialize self-healer
    - Retrieve healing statistics
    - Process statistics data
    """

    def __init__(self, project: str):
        """Initialize healing stats service.

        Args:
            project: Project directory path
        """
        self.project = project
        self.healer = None

    def initialize(self) -> None:
        """Initialize the self-healer."""
        from socialseed_e2e.ai_orchestrator import SelfHealer

        self.healer = SelfHealer(self.project)

    def get_statistics(self) -> Dict[str, Any]:
        """Get healing statistics.

        Returns:
            Statistics dictionary

        Raises:
            RuntimeError: If retrieval fails
        """
        if not self.healer:
            self.initialize()

        return self.healer.get_healing_statistics()


class HealingStatsPresenter:
    """Presenter class for healing-stats output formatting.

    Responsibilities:
    - Format statistics for display
    - Format tables for patterns and recent healings
    """

    @staticmethod
    def display_header() -> None:
        """Display statistics header."""
        console.print("\n📊 [bold cyan]Self-Healing Statistics[/bold cyan]\n")

    @staticmethod
    def display_statistics(stats: Dict[str, Any]) -> None:
        """Display healing statistics.

        Args:
            stats: Statistics dictionary
        """
        console.print(f"[bold]Total Healings:[/bold] {stats['total_healings']}")
        console.print()

        HealingStatsPresenter._display_patterns(stats)
        HealingStatsPresenter._display_recent_healings(stats)

    @staticmethod
    def _display_patterns(stats: Dict[str, Any]) -> None:
        """Display most common flakiness patterns.

        Args:
            stats: Statistics dictionary
        """
        patterns = stats.get("most_common_patterns", [])

        if patterns:
            console.print("[bold]Most Common Flakiness Patterns:[/bold]")

            table = Table()
            table.add_column("Pattern", style="bold")
            table.add_column("Count", justify="right")

            for pattern, count in patterns:
                table.add_row(pattern, str(count))

            console.print(table)
            console.print()

    @staticmethod
    def _display_recent_healings(stats: Dict[str, Any]) -> None:
        """Display recent healings.

        Args:
            stats: Statistics dictionary
        """
        recent = stats.get("recent_healings", [])

        if recent:
            console.print("[bold]Recent Healings:[/bold]")
            for healing in recent[-5:]:
                test_id = healing.get("test_id", "unknown")
                timestamp = healing.get("timestamp", "unknown")
                console.print(f"  - {test_id} ({timestamp})")
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


class HealingStatsCommand:
    """Command class for healing-stats CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute stats retrieval workflow
    """

    def __init__(self):
        """Initialize healing-stats command."""
        self.service: Optional[HealingStatsService] = None
        self.presenter = HealingStatsPresenter()

    def execute(self, project: str) -> int:
        """Execute healing-stats command.

        Args:
            project: Project directory path

        Returns:
            Exit code (0 for success, 1 for error)
        """
        self.presenter.display_header()

        try:
            # Get statistics
            self.service = HealingStatsService(project)
            stats = self.service.get_statistics()

            # Display results
            self.presenter.display_statistics(stats)

            return 0

        except Exception as e:
            import traceback

            self.presenter.display_error(str(e), traceback.format_exc())
            return 1


# CLI command definition
@click.command(name="healing-stats")
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def healing_stats_command(project: str) -> None:
    """View self-healing statistics.

    Shows statistics about auto-healed tests, most common
    flakiness patterns, and healing success rates.
    """
    command = HealingStatsCommand()
    exit_code = command.execute(project)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return healing_stats_command


def get_name():
    """Return the command name."""
    return "healing-stats"


def get_help():
    """Return the command help text."""
    return "View self-healing statistics for tests"
