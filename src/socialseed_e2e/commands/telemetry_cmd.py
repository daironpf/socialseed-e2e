"""Telemetry commands for socialseed-e2e CLI.

This module provides the telemetry command group using POO and SOLID principles.
"""

import time

import click
from rich.console import Console

console = Console()


class TelemetryManagerWrapper:
    """Wrapper for telemetry functionality (Single Responsibility)."""

    def __init__(self):
        pass

    def monitor(
        self,
        output: str,
        baseline: str,
        threshold: float,
        budget: float,
    ) -> None:
        """Start monitoring LLM calls."""
        from socialseed_e2e.telemetry import TelemetryManager, TokenMonitorConfig

        console.print("\n📊 [bold cyan]Token Telemetry Monitor[/bold cyan]")
        console.print("   Tracking LLM calls for cost optimization...\n")

        config = TokenMonitorConfig(
            report_output_dir=output,
            baseline_file=baseline,
            regression_threshold_percentage=threshold,
        )

        if budget:
            config.global_budget_enabled = True
            config.global_max_cost_usd = budget

        manager = TelemetryManager(config)
        manager.start_session()

        console.print("✅ Telemetry session started")
        console.print(f"   Output directory: {output}")
        if baseline:
            console.print(f"   Baseline: {baseline}")
        console.print(f"   Regression threshold: {threshold}%")
        if budget:
            console.print(f"   Budget: ${budget:.2f}")
        console.print("\n   Press Ctrl+C to stop and generate report\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n\n📊 Generating telemetry report...")
            report = manager.stop_session()
            console.print(f"✅ Report saved to: {output}")

    def budget(self) -> None:
        """Show budget information."""
        console.print("\n💰 [bold cyan]Token Budget Management[/bold cyan]\n")
        console.print("Configure budgets in e2e.conf or use environment variables:")
        console.print("  - E2E_MAX_TOKENS: Maximum tokens per request")
        console.print("  - E2E_BUDGET_USD: Monthly budget in USD")
        console.print("\nCurrent settings:")
        console.print(
            "  Use 'e2e telemetry monitor --budget 10.0' to set a session budget"
        )

    def show_stats(self) -> None:
        """Show telemetry statistics."""
        from socialseed_e2e.telemetry import load_telemetry_data

        console.print("\n📊 [bold cyan]Telemetry Statistics[/bold cyan]\n")

        data = load_telemetry_data()
        if not data:
            console.print("[yellow]No telemetry data found.[/yellow]")
            console.print("Run 'e2e telemetry monitor' to start collecting data.")
            return

        console.print(f"Total sessions: {len(data.get('sessions', []))}")
        console.print(f"Total tokens: {data.get('total_tokens', 0):,}")
        console.print(f"Total cost: ${data.get('total_cost', 0):.2f}")


@click.group()
def telemetry():
    """Commands for token-centric performance testing and cost optimization.

    Monitors LLM token usage, detects cost regressions, identifies
    reasoning loops, and provides optimization recommendations.
    """
    pass


@telemetry.command("monitor")
@click.option(
    "--output", "-o", default="telemetry", help="Output directory for reports"
)
@click.option(
    "--baseline", "-b", help="Path to baseline file for regression comparison"
)
@click.option(
    "--threshold", "-t", default=15.0, help="Cost regression threshold percentage"
)
@click.option("--budget", type=float, help="Max token budget in USD")
def telemetry_monitor_cmd(output: str, baseline: str, threshold: float, budget: float):
    """Start monitoring LLM calls for cost and performance.

    Examples:
        e2e telemetry monitor                    # Start monitoring
        e2e telemetry monitor -b baseline.json   # Compare with baseline
        e2e telemetry monitor --budget 10.0    # Set $10 budget
    """
    wrapper = TelemetryManagerWrapper()
    wrapper.monitor(output, baseline, threshold, budget)


@telemetry.command("budget")
def telemetry_budget_cmd():
    """Manage token budgets and view budget information."""
    wrapper = TelemetryManagerWrapper()
    wrapper.budget()


@telemetry.command("stats")
def telemetry_stats_cmd():
    """Show telemetry statistics."""
    wrapper = TelemetryManagerWrapper()
    wrapper.show_stats()


def get_telemetry_group():
    """Get the telemetry command group for lazy loading."""
    return telemetry


__all__ = ["telemetry", "get_telemetry_group"]
