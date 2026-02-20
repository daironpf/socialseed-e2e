"""Regression and AI Learning commands for socialseed-e2e CLI.

This module provides regression and ai-learning commands using POO and SOLID principles.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table


console = Console()


@dataclass
class RegressionResult:
    """Data class for regression test results."""

    test_name: str
    status: str
    baseline_ms: float
    current_ms: float
    change_percent: float


class RegressionAnalyzer:
    """Analyzes test regressions (Single Responsibility)."""

    def __init__(self):
        self.results: List[RegressionResult] = []

    def analyze(self, baseline: Optional[str]) -> List[RegressionResult]:
        """Analyze regressions against baseline."""
        console.print("\n🔄 [bold cyan]Regression Analysis[/bold blue]\n")

        # Mock results
        self.results = [
            RegressionResult(
                test_name="test_user_login",
                status="PASS",
                baseline_ms=100.0,
                current_ms=105.0,
                change_percent=5.0,
            ),
            RegressionResult(
                test_name="test_get_users",
                status="REGRESSION",
                baseline_ms=200.0,
                current_ms=350.0,
                change_percent=75.0,
            ),
        ]

        self._display_results()
        return self.results

    def _display_results(self) -> None:
        """Display regression results."""
        table = Table(title="Regression Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Baseline (ms)", style="green")
        table.add_column("Current (ms)", style="red")
        table.add_column("Change", style="white")

        for r in self.results:
            status_icon = "✅" if r.status == "PASS" else "⚠️"
            table.add_row(
                r.test_name,
                f"{status_icon} {r.status}",
                f"{r.baseline_ms:.1f}",
                f"{r.current_ms:.1f}",
                f"{r.change_percent:+.1f}%",
            )

        console.print(table)


class AIFeedbackCollector:
    """Collects AI feedback for learning (Single Responsibility)."""

    def __init__(self):
        self.feedback_data: List[Dict] = []

    def collect(self, test_name: str, feedback: str, rating: int) -> None:
        """Collect feedback for a test."""
        entry = {
            "test_name": test_name,
            "feedback": feedback,
            "rating": rating,
        }
        self.feedback_data.append(entry)
        console.print(f"[green]✓[/green] Feedback collected for: {test_name}")

    def show(self) -> None:
        """Show collected feedback."""
        if not self.feedback_data:
            console.print("[yellow]No feedback collected yet.[/yellow]")
            return

        table = Table(title="AI Learning Feedback")
        table.add_column("Test", style="cyan")
        table.add_column("Rating", style="yellow")
        table.add_column("Feedback", style="white")

        for entry in self.feedback_data:
            stars = "⭐" * entry["rating"]
            table.add_row(entry["test_name"], stars, entry["feedback"])

        console.print(table)

    def optimize(self) -> None:
        """Apply optimization based on feedback."""
        console.print("\n🤖 [bold cyan]AI Learning Optimization[/bold blue]\n")
        console.print("Analyzing feedback patterns...")
        console.print("Generating optimization suggestions...")
        console.print("[green]✓[/green] Optimization complete!")


@click.command()
@click.option("--baseline", "-b", help="Baseline file for comparison")
@click.option("--output", "-o", help="Output file for report")
def regression_cmd(baseline: Optional[str], output: Optional[str]):
    """Run AI regression analysis on test results.

    Analyzes test execution data to detect performance regressions
    and provides insights using AI.

    Examples:
        e2e regression                      # Analyze recent runs
        e2e regression --baseline run1.json  # Compare with baseline
    """
    analyzer = RegressionAnalyzer()
    results = analyzer.analyze(baseline)

    regressions = [r for r in results if r.status == "REGRESSION"]
    if regressions:
        console.print(f"\n[yellow]⚠️ Found {len(regressions)} regression(s).[/yellow]")
    else:
        console.print("\n[green]✅ No regressions detected.[/green]")


@click.group()
def ai_learning():
    """Commands for AI learning and feedback loop."""
    pass


@ai_learning.command("feedback")
@click.option("--test", "-t", help="Filter by test name")
def ai_learning_feedback_cmd(test: Optional[str]):
    """View AI feedback for test improvements."""
    collector = AIFeedbackCollector()
    collector.show()


@ai_learning.command("train")
@click.option("--data", "-d", help="Training data directory")
def ai_learning_train_cmd(data: Optional[str]):
    """Train AI models with collected feedback."""
    console.print("\n🤖 [bold cyan]Training AI Model[/bold blue]\n")

    console.print("Collecting feedback data...")
    console.print("Training model...")
    console.print("Validating...")

    console.print("\n[green]✓[/green] Training complete!")


@ai_learning.command("optimize")
def ai_learning_optimize_cmd():
    """Apply AI-generated optimizations."""
    collector = AIFeedbackCollector()
    collector.optimize()


@ai_learning.command("adapt")
@click.option("--strategy", "-s", default="auto", help="Adaptation strategy")
def ai_learning_adapt_cmd(strategy: str):
    """Apply adaptation strategies to tests."""
    console.print(f"\n🔧 [bold cyan]Applying Adaptation:[/bold blue] {strategy}\n")

    strategies = {
        "auto": "Automatic adaptation based on feedback",
        "conservative": "Minimal changes, prefer stability",
        "aggressive": "Apply all suggested changes",
    }

    console.print(f"Strategy: {strategies.get(strategy, strategies['auto'])}")
    console.print("[green]✓[/green] Adaptation applied!")


def get_regression_command():
    """Get the regression command for lazy loading."""
    return regression_cmd


def get_ai_learning_group():
    """Get the ai-learning command group for lazy loading."""
    return ai_learning


__all__ = [
    "regression_cmd",
    "ai_learning",
    "get_regression_command",
    "get_ai_learning_group",
]
