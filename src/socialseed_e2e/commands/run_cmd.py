"""Run command for socialseed-e2e.

This module provides the run command functionality.
Execute E2E tests with proper SOLID architecture.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console

console = Console()


class RunConfigValidator:
    """Handles configuration validation.

    Single Responsibility: Validate all configuration options.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path

    def load_config(self) -> Any:
        """Load and validate configuration.

        Returns:
            App configuration

        Raises:
            RuntimeError: If configuration is invalid
        """
        from socialseed_e2e.core.config_loader import ApiConfigLoader, ConfigError

        try:
            loader = ApiConfigLoader()
            return loader.load(self.config_path)
        except ConfigError as e:
            raise RuntimeError(f"Configuration error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")


class RunServiceHealthChecker:
    """Handles service health checking.

    Single Responsibility: Check health of services.
    """

    def check_services(self, app_config: Any) -> List[str]:
        """Check which services are unhealthy.

        Args:
            app_config: Application configuration

        Returns:
            List of unhealthy service names
        """
        unhealthy = []
        for name, svc in app_config.services.items():
            health_endpoint = svc.health_endpoint or "/actuator/health"
            is_healthy, _ = self._check_health(svc.base_url, health_endpoint)
            if not is_healthy:
                unhealthy.append(name)
                console.print(f"   ⏭️  [yellow]Skipping {name} (not healthy)[/yellow]")
            else:
                console.print(f"   ✅ [green]{name} is healthy[/green]")
        return unhealthy

    def _check_health(self, base_url: str, health_endpoint: str) -> Tuple[bool, Any]:
        """Check if a service is healthy.

        Args:
            base_url: Service base URL
            health_endpoint: Health check endpoint

        Returns:
            Tuple of (is_healthy, response)
        """
        from socialseed_e2e.core.base_page import BasePage

        try:
            page = BasePage(base_url=base_url)
            response = page.get(health_endpoint)
            return response.ok, response
        except Exception:
            return False, None


class RunTestExecutor:
    """Handles test execution.

    Single Responsibility: Execute tests (sequential or parallel).
    """

    def __init__(self, services_path: Path):
        self.services_path = services_path

    def execute(
        self,
        specific_service: Optional[str] = None,
        specific_module: Optional[str] = None,
        parallel: Optional[int] = None,
        parallel_mode: str = "service",
        verbose: bool = False,
        debug: bool = False,
        no_agent: bool = False,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute tests.

        Args:
            specific_service: Run tests for specific service
            specific_module: Run specific test module
            parallel: Number of parallel workers
            parallel_mode: Parallel execution mode
            verbose: Verbose output
            debug: Debug mode
            no_agent: Disable AI features
            include_tags: Tags to include
            exclude_tags: Tags to exclude

        Returns:
            Test results dictionary
        """
        use_parallel = parallel is not None and parallel != 0

        if use_parallel:
            return self._execute_parallel(
                specific_service,
                specific_module,
                parallel,
                parallel_mode,
                verbose,
                debug,
                no_agent,
                include_tags,
                exclude_tags,
            )
        else:
            return self._execute_sequential(
                specific_service,
                specific_module,
                verbose,
                debug,
                no_agent,
                include_tags,
                exclude_tags,
            )

    def _execute_sequential(
        self,
        specific_service: Optional[str],
        specific_module: Optional[str],
        verbose: bool,
        debug: bool,
        no_agent: bool,
        include_tags: Optional[List[str]],
        exclude_tags: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Execute tests sequentially."""
        from socialseed_e2e.core.test_runner import run_all_tests

        return run_all_tests(
            services_path=self.services_path,
            specific_service=specific_service,
            specific_module=specific_module,
            verbose=verbose,
            debug=debug,
            no_agent=no_agent,
            include_tags=include_tags,
            exclude_tags=exclude_tags,
        )

    def _execute_parallel(
        self,
        specific_service: Optional[str],
        specific_module: Optional[str],
        parallel: Optional[int],
        parallel_mode: str,
        verbose: bool,
        debug: bool,
        no_agent: bool,
        include_tags: Optional[List[str]],
        exclude_tags: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Execute tests in parallel."""
        from socialseed_e2e.core.parallel_runner import (
            ParallelConfig,
            run_tests_parallel,
        )

        workers = parallel if parallel and parallel > 0 else None
        parallel_config = ParallelConfig(
            enabled=True,
            max_workers=workers,
            parallel_mode=parallel_mode,
        )

        return run_tests_parallel(
            services_path=self.services_path,
            specific_service=specific_service,
            specific_module=specific_module,
            parallel_config=parallel_config,
            verbose=verbose,
            debug=debug,
            no_agent=no_agent,
            include_tags=include_tags,
            exclude_tags=exclude_tags,
        )


class RunReportGenerator:
    """Handles report generation.

    Single Responsibility: Generate various report formats.
    """

    def __init__(
        self, output: str, report_dir: str, report: Optional[str], report_output: str
    ):
        self.output = output
        self.report_dir = report_dir
        self.report = report
        self.report_output = report_output

    def generate_reports(self, results: Dict[str, Any], verbose: bool = False) -> None:
        """Generate all requested reports.

        Args:
            results: Test results
            verbose: Verbose output
        """
        if self.output == "html":
            self._generate_html_report(results, verbose)

        if self.report:
            self._generate_machine_readable_report(results, verbose)

    def _generate_html_report(self, results: Dict[str, Any], verbose: bool) -> None:
        """Generate HTML report."""
        try:
            from socialseed_e2e.reporting import (
                HTMLReportGenerator,
                TestResultCollector,
                TestSuiteReport,
            )

            console.print("\n📊 [cyan]Generating HTML report...[/cyan]")

            collector = TestResultCollector(title="E2E Test Report")
            collector.start_collection()

            for service_name, suite_result in results.items():
                for test_result in suite_result.results:
                    test_id = f"{service_name}.{test_result.name}"
                    collector.record_test_start(test_id, test_result.name, service_name)
                    collector.record_test_end(
                        test_id,
                        status=test_result.status,
                        duration_ms=test_result.duration_ms,
                        error_message=test_result.error_message
                        if test_result.error_message
                        else None,
                    )

            test_suite_report: TestSuiteReport = collector.generate_report()
            generator = HTMLReportGenerator()

            import os

            os.makedirs(self.report_dir, exist_ok=True)
            report_path = generator.generate(
                test_suite_report,
                output_path=os.path.join(self.report_dir, "report.html"),
            )

            console.print(f"[green]✓ HTML report generated:[/green] {report_path}")

            csv_path = generator.export_to_csv(
                test_suite_report,
                output_path=os.path.join(self.report_dir, "report.csv"),
            )
            json_path = generator.export_to_json(
                test_suite_report,
                output_path=os.path.join(self.report_dir, "report.json"),
            )

            console.print(f"[green]✓ CSV report:[/green] {csv_path}")
            console.print(f"[green]✓ JSON report:[/green] {json_path}")

        except Exception as e:
            console.print(f"[yellow]⚠ Could not generate HTML report: {e}[/yellow]")
            if verbose:
                import traceback

                console.print(traceback.format_exc())

    def _generate_machine_readable_report(
        self, results: Dict[str, Any], verbose: bool
    ) -> None:
        """Generate machine-readable reports (JUnit, JSON)."""
        try:
            from socialseed_e2e.core.test_runner import (
                generate_json_report,
                generate_junit_report,
            )

            console.print(
                f"\n📊 [cyan]Generating {self.report.upper()} report...[/cyan]"
            )

            if self.report == "junit":
                junit_path = generate_junit_report(
                    results, output_path=str(Path(self.report_output) / "junit.xml")
                )
                console.print(f"[green]✓ JUnit report:[/green] {junit_path}")

            elif self.report == "json":
                json_path = generate_json_report(
                    results, output_path=str(Path(self.report_output) / "report.json")
                )
                console.print(f"[green]✓ JSON report:[/green] {json_path}")

        except Exception as e:
            console.print(
                f"[yellow]⚠ Could not generate {self.report} report: {e}[/yellow]"
            )
            if verbose:
                import traceback

                console.print(traceback.format_exc())


class RunPresenter:
    """Handles output display.

    Single Responsibility: Display run command output.
    """

    @staticmethod
    def display_header(version: str) -> None:
        """Display command header."""
        console.print(f"\n🚀 [bold green]socialseed-e2e v{version}[/green]")
        console.print("═" * 50)
        console.print()

    @staticmethod
    def display_config_info(config_path: str, environment: str) -> None:
        """Display configuration info."""
        console.print(f"📋 [cyan]Configuration:[/cyan] {config_path}")
        console.print(f"🌍 [cyan]Environment:[/cyan] {environment}")
        console.print()

    @staticmethod
    def display_filters(
        service: Optional[str],
        module: Optional[str],
        verbose: bool,
        debug: bool,
        no_agent: bool,
        include_tags: Tuple[str, ...],
        exclude_tags: Tuple[str, ...],
    ) -> None:
        """Display active filters."""
        if service:
            console.print(f"🔍 [yellow]Filtering by service:[/yellow] {service}")
        if module:
            console.print(f"🔍 [yellow]Filtering by module:[/yellow] {module}")
        if verbose:
            console.print("📢 [yellow]Verbose mode activated[/yellow]")
        if debug:
            console.print(
                "🐛 [yellow]Debug mode activated - verbose HTTP logging for failures[/yellow]"
            )
        if no_agent:
            console.print(
                "🔄 [yellow]Boring mode activated - AI features disabled[/yellow]"
            )
        if include_tags:
            console.print(
                f"🏷️ [yellow]Including tags:[/yellow] {', '.join(include_tags)}"
            )
        if exclude_tags:
            console.print(
                f"🚫 [yellow]Excluding tags:[/yellow] {', '.join(exclude_tags)}"
            )
        console.print()

    @staticmethod
    def display_error(message: str, suggestion: str = "") -> None:
        """Display error message."""
        console.print(f"[red]❌ Error:[/red] {message}")
        if suggestion:
            console.print(f"   {suggestion}")
        sys.exit(1)


class RunCommand:
    """Main command coordinator.

    Single Responsibility: Coordinate run command workflow.

    Following SOLID principles:
    - S: Each class has single responsibility
    - O: Open for extension, closed for modification
    - L: Each class has clear interface
    - I: Small, focused interfaces
    - D: Dependencies injected, not hardcoded
    """

    def __init__(self):
        self.validator = RunConfigValidator()
        self.health_checker = RunServiceHealthChecker()
        self.presenter = RunPresenter()

    def execute(
        self,
        service: Optional[str],
        module: Optional[str],
        config: Optional[str],
        verbose: bool,
        output: str,
        report_dir: str,
        trace: bool,
        parallel: Optional[int],
        parallel_mode: str,
        include_tags: Tuple[str, ...],
        exclude_tags: Tuple[str, ...],
        report: Optional[str],
        report_output: str,
        debug: bool,
        skip_unhealthy: bool,
        no_agent: bool,
        watch: bool,
        isolate: bool = False,
        pii_check: bool = False,
        enable_xai: bool = False,
    ) -> int:
        """Execute run command.

        Returns:
            Exit code
        """
        from socialseed_e2e import __version__

        # Display header
        self.presenter.display_header(__version__)

        # Load and validate config
        try:
            self.validator.config_path = config
            app_config = self.validator.load_config()
            self.presenter.display_config_info(
                str(self.validator.config_path or "default"), app_config.environment
            )
        except RuntimeError as e:
            self.presenter.display_error(str(e), "Run: e2e init to create a project")

        # Determine services path
        services_path = self._resolve_services_path(config)

        # Display filters
        self.presenter.display_filters(
            service, module, verbose, debug, no_agent, include_tags, exclude_tags
        )

        # Check service health if requested
        unhealthy_services = []
        if skip_unhealthy:
            console.print("🏥 [cyan]Checking service health...[/cyan]")
            unhealthy_services = self.health_checker.check_services(app_config)
            console.print()

        # Skip unhealthy services
        if service and skip_unhealthy and service in unhealthy_services:
            console.print(
                f"⏭️  [yellow]Skipping service '{service}' - not healthy[/yellow]"
            )
            console.print()
            return 0

        # Setup smart mocking if isolate flag is set
        mock_isolation_manager = None
        if isolate:
            from socialseed_e2e.ai_mocking import (
                MockIsolationManager,
                SmartMockOrchestrator,
            )

            console.print("🔒 [cyan]Starting smart mock isolation mode...[/cyan]")
            orchestrator = SmartMockOrchestrator()
            mock_isolation_manager = MockIsolationManager(orchestrator)
            if service:
                mock_isolation_manager.start_isolation(service)
            console.print()

        # Setup PII detection if enabled
        pii_service = None
        if pii_check:
            from socialseed_e2e.pii_masking import PIIMaskingConfig, PIIMaskingService

            def on_pii_detected(masked_values):
                console.print(
                    f"🔒 [red]PII detected: {len(masked_values)} instances[/red]"
                )
                for mv in masked_values:
                    console.print(f"   - {mv.pii_type.value}: {mv.masked}")

            pii_service = PIIMaskingService(
                PIIMaskingConfig(), on_pii_detected=on_pii_detected
            )
            console.print("🔍 [cyan]PII detection enabled[/cyan]")

        # Setup XAI if enabled
        xai_reporter = None
        if enable_xai:
            from socialseed_e2e.agents.xai import ExplainableAIReporter

            xai_reporter = ExplainableAIReporter()
            console.print("🧠 [cyan]Explainable AI reports enabled[/cyan]")

        # Execute tests
        executor = RunTestExecutor(services_path)
        results = executor.execute(
            specific_service=service,
            specific_module=module,
            parallel=parallel,
            parallel_mode=parallel_mode,
            verbose=verbose,
            debug=debug,
            no_agent=no_agent,
            include_tags=list(include_tags) if include_tags else None,
            exclude_tags=list(exclude_tags) if exclude_tags else None,
        )

        # Print summary
        from socialseed_e2e.core.test_runner import print_summary

        all_passed = print_summary(results)

        # Generate reports
        report_gen = RunReportGenerator(output, report_dir, report, report_output)
        report_gen.generate_reports(results, verbose)

        # Generate XAI report if enabled
        if enable_xai and xai_reporter:
            from pathlib import Path

            xai_report_dir = Path(report_output) / "xai"
            xai_report_dir.mkdir(parents=True, exist_ok=True)

            for service_name, _service_results in results.items():
                report = xai_reporter.generate_report(
                    test_name=service_name, test_file=str(services_path / service_name)
                )
                html_report = xai_reporter.generate_html_report(report)
                report_file = xai_report_dir / f"{service_name}_xai.html"
                report_file.write_text(html_report)
                console.print(f"📊 [green]XAI report saved: {report_file}[/green]")

        # Cleanup mock isolation if enabled
        if mock_isolation_manager:
            mock_isolation_manager.stop_isolation()
            console.print("🔒 [green]Mock isolation stopped[/green]")

        return 0 if all_passed else 1

    def _resolve_services_path(self, config: Optional[str]) -> Path:
        """Resolve services directory path."""
        from socialseed_e2e.core.config_loader import ApiConfigLoader

        services_path = Path("services")

        if config:
            loader = ApiConfigLoader()
            alt_path = loader._config_path.parent / "services"
            if alt_path.exists():
                services_path = alt_path

        return services_path


# CLI command definition
@click.command(name="run")
@click.option("--service", "-s", help="Run tests for specific service")
@click.option("--module", "-m", help="Run specific test module")
@click.option("--config", "-c", help="Path to e2e.conf")
@click.option("--url", "override_url", help="Override service URL")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--output",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    help="Output format",
)
@click.option("--report-dir", default=".e2e/reports", help="HTML report directory")
@click.option("--trace", is_flag=True, help="Enable visual traceability")
@click.option("--trace-output", help="Directory for traceability reports")
@click.option(
    "--trace-format",
    type=click.Choice(["mermaid", "plantuml", "both"]),
    default="mermaid",
    help="Trace format",
)
@click.option("--parallel", type=int, help="Parallel workers")
@click.option(
    "--parallel-mode",
    type=click.Choice(["service", "module"]),
    default="service",
    help="Parallel mode",
)
@click.option("--include-tags", multiple=True, help="Include tags")
@click.option("--exclude-tags", multiple=True, help="Exclude tags")
@click.option("--report", type=click.Choice(["junit", "json"]), help="Generate report")
@click.option("--report-output", default=".e2e/reports", help="Report output directory")
@click.option("--debug", is_flag=True, help="Debug mode")
@click.option("--skip-unhealthy", is_flag=True, help="Skip unhealthy services")
@click.option("--no-agent", "no_agent", is_flag=True, help="Disable AI features")
@click.option("-w", "--watch", is_flag=True, help="Watch for file changes")
@click.option("--isolate", is_flag=True, help="Run with smart dependency mocking")
@click.option("--pii-check", "pii_check", is_flag=True, help="Enable PII detection")
@click.option("--xai", "enable_xai", is_flag=True, help="Enable explainable AI reports")
def run_command(
    service: Optional[str],
    module: Optional[str],
    config: Optional[str],
    override_url: Optional[str],
    verbose: bool,
    output: str,
    report_dir: str,
    trace: bool,
    trace_output: Optional[str],
    trace_format: str,
    parallel: Optional[int],
    parallel_mode: str,
    include_tags: Tuple[str, ...],
    exclude_tags: Tuple[str, ...],
    report: Optional[str],
    report_output: str,
    debug: bool,
    skip_unhealthy: bool,
    no_agent: bool,
    watch: bool,
    isolate: bool,
    pii_check: bool,
    enable_xai: bool,
) -> None:
    """Execute E2E tests.

    Discovers and automatically executes all available tests.

    Examples:
        e2e run
        e2e run --service auth_service
        e2e run --service auth_service --module 01_login
        e2e run --verbose
        e2e run --parallel 4
        e2e run --report junit
        e2e run --isolate --service my_service
    """
    command = RunCommand()
    exit_code = command.execute(
        service=service,
        module=module,
        config=config,
        verbose=verbose,
        output=output,
        report_dir=report_dir,
        trace=trace,
        parallel=parallel,
        parallel_mode=parallel_mode,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
        report=report,
        report_output=report_output,
        debug=debug,
        skip_unhealthy=skip_unhealthy,
        no_agent=no_agent,
        watch=watch,
        isolate=isolate,
        pii_check=pii_check,
        enable_xai=enable_xai,
    )
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return run_command


def get_name():
    """Return the command name."""
    return "run"


def get_help():
    """Return the command help text."""
    return "Execute E2E tests"
