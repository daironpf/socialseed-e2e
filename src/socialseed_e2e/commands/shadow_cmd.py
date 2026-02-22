"""Shadow commands for socialseed-e2e CLI.

This module provides the shadow commands (capture, generate, replay, analyze) using POO and SOLID principles.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


class ShadowCaptureAgent:
    """Handles traffic capture (Single Responsibility)."""

    def __init__(
        self,
        name: str,
        target_url: str,
        output: Optional[str] = None,
        filter_health: bool = False,
        filter_static: bool = False,
        sanitize: bool = False,
        duration: Optional[int] = None,
        max_requests: Optional[int] = None,
    ):
        self.name = name
        self.target_url = target_url
        self.output = output
        self.filter_health = filter_health
        self.filter_static = filter_static
        self.sanitize = sanitize
        self.duration = duration
        self.max_requests = max_requests

    def capture(self):
        """Capture API traffic."""
        from socialseed_e2e.shadow_runner import CaptureConfig, ShadowRunner

        output_path = (
            Path(self.output) if self.output else Path(f".e2e/shadow/{self.name}.json")
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        config = CaptureConfig(
            target_url=self.target_url,
            output_path=str(output_path),
            filter_health_checks=self.filter_health,
            filter_static_assets=self.filter_static,
            sanitize_pii=self.sanitize,
            max_requests=self.max_requests,
        )

        runner = ShadowRunner(output_dir=str(Path(config.output_path).parent))

        console.print(f"[yellow]Starting capture...[/yellow]")
        console.print(
            f"   Filter health checks: {'Yes' if self.filter_health else 'No'}"
        )
        console.print(
            f"   Filter static assets: {'Yes' if self.filter_static else 'No'}"
        )
        console.print(f"   Sanitize PII: {'Yes' if self.sanitize else 'No'}")
        console.print()


class ShadowGenerateAgent:
    """Handles test generation from captured traffic (Single Responsibility)."""

    def __init__(
        self,
        capture_file: str,
        service: Optional[str] = None,
        group_by: str = "service",
        include_auth: bool = False,
    ):
        self.capture_file = capture_file
        self.service = service
        self.group_by = group_by
        self.include_auth = include_auth

    def generate(self):
        """Generate tests from captured traffic."""
        from socialseed_e2e.shadow_runner import ShadowRunner, TestGenerationConfig


class ShadowReplayAgent:
    """Handles traffic replay (Single Responsibility)."""

    def __init__(
        self,
        capture_file: str,
        target_url: Optional[str] = None,
        speed: str = "realtime",
        stop_on_error: bool = False,
    ):
        self.capture_file = capture_file
        self.target_url = target_url
        self.speed = speed
        self.stop_on_error = stop_on_error

    def replay(self):
        """Replay captured traffic."""
        from socialseed_e2e.shadow_runner import ReplayConfig, ShadowRunner


class ShadowAnalyzeAgent:
    """Handles captured traffic analysis (Single Responsibility)."""

    def __init__(
        self, capture_file: str, format: str = "table", show_pii: bool = False
    ):
        self.capture_file = capture_file
        self.format = format
        self.show_pii = show_pii

    def analyze(self):
        """Analyze captured traffic."""
        from socialseed_e2e.shadow_runner import ShadowRunner

        if not Path(self.capture_file).exists():
            console.print(f"[red]❌ Error:[/red] File not found: {self.capture_file}")
            sys.exit(1)

        runner = ShadowRunner()
        analysis = runner.analyze_capture(self.capture_file)

        if self.format == "table":
            table = Table(title="Traffic Analysis")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green")

            table.add_row("Total Requests", str(analysis.get("total_requests", 0)))
            table.add_row("Unique Endpoints", str(analysis.get("unique_endpoints", 0)))
            table.add_row("Methods", str(analysis.get("methods", {})))
            table.add_row("Status Codes", str(analysis.get("status_codes", {})))

            console.print(table)


class ShadowFuzzAgent:
    """Handles semantic fuzzing on captured traffic (Issue #1)."""

    def __init__(
        self,
        capture_file: str,
        target_url: str,
        strategy: str = "intelligent",
        mutations: int = 5,
        output: Optional[str] = None,
    ):
        self.capture_file = capture_file
        self.target_url = target_url
        self.strategy = strategy
        self.mutations = mutations
        self.output = output

    def fuzz(self):
        """Run semantic fuzzing on captured traffic."""
        from socialseed_e2e.shadow_runner import (
            FuzzingConfig,
            FuzzingStrategy,
            SemanticShadowRunner,
        )

        if not Path(self.capture_file).exists():
            console.print(f"[red]❌ Error:[/red] File not found: {self.capture_file}")
            sys.exit(1)

        runner = SemanticShadowRunner()

        strategy_map = {
            "random": FuzzingStrategy.RANDOM,
            "intelligent": FuzzingStrategy.INTELLIGENT,
            "coverage_guided": FuzzingStrategy.COVERAGE_GUIDED,
            "ai_powered": FuzzingStrategy.AI_POWERED,
        }

        config = FuzzingConfig(
            strategy=strategy_map.get(self.strategy, FuzzingStrategy.INTELLIGENT),
            mutations_per_request=self.mutations,
        )

        console.print(f"[yellow]Starting semantic fuzzing...[/yellow]")
        console.print(f"   Capture: {self.capture_file}")
        console.print(f"   Target: {self.target_url}")
        console.print(f"   Strategy: {self.strategy}")
        console.print(f"   Mutations per request: {self.mutations}")
        console.print()

        campaign = runner.generate_fuzzing_campaign(
            self.capture_file,
            self.target_url,
            config,
        )

        console.print(f"[green]Fuzzing campaign created:[/green] {campaign.name}")
        console.print(f"   Campaign ID: {campaign.campaign_id}")

        if self.output:
            runner.export_fuzzing_report(campaign, self.output)
            console.print(f"   Report saved to: {self.output}")


@click.group(name="shadow")
def get_shadow_group():
    """Shadow Runner - Capture traffic and auto-generate tests (Issue #130)."""
    pass


@click.command(name="capture")
@click.argument("name")
@click.option(
    "--target-url", "-u", required=True, help="Target API URL to capture traffic from"
)
@click.option("--output", "-o", help="Output file for captured traffic")
@click.option("--filter-health", is_flag=True, help="Filter out health check requests")
@click.option("--filter-static", is_flag=True, help="Filter out static asset requests")
@click.option("--sanitize", is_flag=True, help="Sanitize PII from captured traffic")
@click.option("--duration", "-d", type=int, help="Capture duration in seconds")
@click.option("--max-requests", "-m", type=int, help="Maximum requests to capture")
def get_shadow_capture_command(
    name: str,
    target_url: str,
    output: Optional[str],
    filter_health: bool,
    filter_static: bool,
    sanitize: bool,
    duration: Optional[int],
    max_requests: Optional[int],
):
    """Capture real API traffic via middleware proxy."""
    try:
        agent = ShadowCaptureAgent(
            name,
            target_url,
            output,
            filter_health,
            filter_static,
            sanitize,
            duration,
            max_requests,
        )
        agent.capture()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command(name="generate")
@click.argument("capture_file")
@click.option("--service", "-s", help="Service name for generated tests")
@click.option(
    "--group-by", type=click.Choice(["service", "flow", "endpoint"]), default="service"
)
@click.option("--include-auth", is_flag=True, help="Include authentication in tests")
def get_shadow_generate_command(
    capture_file: str, service: Optional[str], group_by: str, include_auth: bool
):
    """Generate tests from captured traffic."""
    try:
        agent = ShadowGenerateAgent(capture_file, service, group_by, include_auth)
        agent.generate()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command(name="replay")
@click.argument("capture_file")
@click.option("--target-url", "-u", help="Override target URL")
@click.option(
    "--speed", type=click.Choice(["realtime", "fast", "slow"]), default="realtime"
)
@click.option("--stop-on-error", is_flag=True, help="Stop on first error")
def get_shadow_replay_command(
    capture_file: str, target_url: Optional[str], speed: str, stop_on_error: bool
):
    """Replay captured traffic."""
    try:
        agent = ShadowReplayAgent(capture_file, target_url, speed, stop_on_error)
        agent.replay()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command(name="analyze")
@click.argument("capture_file")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
@click.option("--show-pii", is_flag=True, help="Show PII in output")
def get_shadow_analyze_command(capture_file: str, format: str, show_pii: bool):
    """Analyze captured traffic."""
    try:
        agent = ShadowAnalyzeAgent(capture_file, format, show_pii)
        agent.analyze()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command(name="fuzz")
@click.argument("capture_file")
@click.argument("target_url")
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(["random", "intelligent", "coverage_guided", "ai_powered"]),
    default="intelligent",
    help="Fuzzing strategy to use",
)
@click.option(
    "--mutations", "-m", type=int, default=5, help="Number of mutations per request"
)
@click.option("--output", "-o", help="Output file for fuzzing report")
def get_shadow_fuzz_command(
    capture_file: str,
    target_url: str,
    strategy: str,
    mutations: int,
    output: Optional[str],
):
    """Run semantic fuzzing on captured traffic (Issue #1 - Fuzzing Semántico)."""
    try:
        agent = ShadowFuzzAgent(capture_file, target_url, strategy, mutations, output)
        agent.fuzz()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


shadow_group = get_shadow_group()
