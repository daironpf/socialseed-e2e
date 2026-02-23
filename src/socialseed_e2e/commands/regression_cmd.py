"""Regression command for socialseed-e2e CLI.

This module provides the regression command using POO and SOLID principles.
"""

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


class RegressionAnalyzer:
    """Handles AI Regression Analysis (Single Responsibility)."""

    def __init__(self, target_path: Path, base_ref: str, target_ref: str):
        self.target_path = target_path
        self.base_ref = base_ref
        self.target_ref = target_ref

    def analyze(self):
        """Run regression analysis."""
        from socialseed_e2e.project_manifest import RegressionAgent

        agent = RegressionAgent(self.target_path, self.base_ref, self.target_ref)
        return agent.run_analysis()

    def display_results(self, impact, run_tests: bool = False) -> None:
        """Display analysis results."""
        if not impact.changed_files:
            console.print("[yellow]⚠ No changes detected between references[/yellow]")
            return

        console.print("📊 [bold]Analysis Complete[/bold]\n")
        console.print(f"   Files changed: {len(impact.changed_files)}")
        console.print(f"   Services affected: {len(impact.affected_services)}")
        console.print(f"   Endpoints affected: {len(impact.affected_endpoints)}")
        console.print(f"   Tests to run: {len(impact.affected_tests)}")
        console.print(f"   Risk level: {impact.risk_level.upper()}")

        if impact.changed_files:
            console.print("\n📝 [bold]Changed Files:[/bold]")
            for change in impact.changed_files:
                file_name = change.file_path.name
                change_emoji = {"added": "+", "modified": "~", "deleted": "-"}.get(
                    change.change_type, "?"
                )
                console.print(
                    f"   {change_emoji} {file_name} ({change.lines_added}+/{change.lines_deleted}-)"
                )

        if impact.affected_services:
            console.print("\n🎯 [bold]Affected Services:[/bold]")
            for service in impact.affected_services:
                console.print(f"   • {service}")

        if impact.affected_tests:
            console.print("\n🧪 [bold]Tests to Execute:[/bold]")
            from socialseed_e2e.project_manifest import RegressionAgent

            agent = RegressionAgent(self.target_path, self.base_ref, self.target_ref)
            tests_by_service = agent.get_tests_to_run(impact)
            for service, tests in tests_by_service.items():
                console.print(f"   {service}:")
                for test in tests[:5]:
                    console.print(f"     - {test}")


@click.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--base-ref",
    "-b",
    default="HEAD~1",
    help="Base git reference to compare from",
)
@click.option(
    "--target-ref",
    "-t",
    default="HEAD",
    help="Target git reference to compare to",
)
@click.option(
    "--run-tests",
    is_flag=True,
    help="Run the affected tests after analysis",
)
@click.option(
    "--output",
    "-o",
    default="REGRESSION_REPORT.md",
    help="Output report filename",
)
def get_regression_command(
    directory: str = ".",
    base_ref: str = "HEAD~1",
    target_ref: str = "HEAD",
    run_tests: bool = False,
    output: str = "REGRESSION_REPORT.md",
):
    """AI Regression Analysis for differential testing (Issue #84).

    Analyzes git diffs to identify modified functions, controllers, or models,
    determines which tests are affected by changes, and executes only related
    tests for instant feedback.

    Examples:
        e2e regression                        # Analyze last commit
        e2e regression --base-ref main        # Compare against main branch
        e2e regression --run-tests            # Analyze and run affected tests
        e2e regression -b v1.0 -t v2.0       # Compare tags
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🤖 [bold cyan]AI Regression Agent[/bold cyan]")
    console.print(f"   Project: {target_path}")
    console.print(f"   Comparing: {base_ref} → {target_ref}\n")

    try:
        analyzer = RegressionAnalyzer(target_path, base_ref, target_ref)
        impact = analyzer.analyze()
        analyzer.display_results(impact, run_tests)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


regression_command = get_regression_command()
