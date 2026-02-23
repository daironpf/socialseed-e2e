"""Security Test command for socialseed-e2e.

This module provides the security-test command functionality.
AI-driven security fuzzing tests.
"""

import sys
from pathlib import Path
from typing import Any, List, Optional

import click
from rich.console import Console

console = Console()


class SecurityTestService:
    """Service class for security test operations.

    Responsibilities:
    - Validate project and manifest
    - Run security fuzzing tests
    - Process test results
    """

    def __init__(self, target_path: Path, service: Optional[str] = None):
        """Initialize security test service.

        Args:
            target_path: Project directory path
            service: Optional specific service to test
        """
        self.target_path = target_path
        self.service = service
        self.api = None
        self.manifest = None

    def validate(self) -> None:
        """Validate project and load manifest.

        Raises:
            RuntimeError: If validation fails
        """
        if not self.target_path.exists():
            raise RuntimeError(f"Directory not found: {self.target_path}")

        from socialseed_e2e.project_manifest import ManifestAPI

        self.api = ManifestAPI(self.target_path)
        self.api._load_manifest()
        self.manifest = self.api.manifest

        if not self.manifest:
            raise RuntimeError("No project manifest found. Run 'e2e manifest' first.")

    def get_services_to_test(self) -> List[Any]:
        """Get list of services to test.

        Returns:
            List of services to fuzz

        Raises:
            RuntimeError: If specified service not found
        """
        services = self.manifest.services

        if self.service:
            services = [s for s in services if s.name == self.service]
            if not services:
                raise RuntimeError(f"Service '{self.service}' not found")

        return services

    def run_fuzzing(self, services: List[Any], max_payloads: int) -> List[Any]:
        """Run security fuzzing tests.

        Args:
            services: List of services to test
            max_payloads: Maximum payloads per field

        Returns:
            List of test sessions
        """
        from socialseed_e2e import BasePage
        from socialseed_e2e.project_manifest import run_security_fuzzing

        all_sessions = []

        for svc in services:
            console.print(f"\n🎯 Testing service: [cyan]{svc.name}[/cyan]")

            page = BasePage(base_url="http://localhost:8080")

            session = run_security_fuzzing(
                service_page=page, service_info=svc, max_payloads_per_field=max_payloads
            )

            all_sessions.append(session)

        return all_sessions


class SecurityTestPresenter:
    """Presenter class for security-test output formatting.

    Responsibilities:
    - Format security test output
    - Display test results and reports
    """

    @staticmethod
    def display_header(target_path: Path) -> None:
        """Display security test header.

        Args:
            target_path: Project directory
        """
        console.print("\n🔒 [bold red]AI Security Fuzzing[/bold red]")
        console.print(f"   Project: {target_path}\n")

    @staticmethod
    def display_results(
        sessions: List[Any], report_path: Path, output_filename: str
    ) -> None:
        """Display security test results.

        Args:
            sessions: Test sessions
            report_path: Path to report
            output_filename: Output filename
        """
        console.print("\n✅ [bold green]Security Testing Complete![/bold green]")
        console.print(f"   📄 Report: {report_path}\n")

    @staticmethod
    def display_error(message: str) -> None:
        """Display error message.

        Args:
            message: Error message
        """
        console.print(f"\n[red]❌ Error:[/red] {message}")


class SecurityTestCommand:
    """Command class for security-test CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute security testing workflow
    """

    def __init__(self):
        """Initialize security-test command."""
        self.service: Optional[SecurityTestService] = None
        self.presenter = SecurityTestPresenter()

    def execute(
        self,
        directory: str,
        service: Optional[str],
        max_payloads: int,
        output: str,
        attack_types: Optional[str],
    ) -> int:
        """Execute security-test command.

        Args:
            directory: Project directory path
            service: Optional specific service to test
            max_payloads: Maximum payloads per field
            output: Output report filename
            attack_types: Comma-separated attack types

        Returns:
            Exit code (0 for success, 1 for error)
        """
        target_path = Path(directory).resolve()

        self.presenter.display_header(target_path)

        try:
            # Initialize and validate
            self.service = SecurityTestService(target_path, service)
            self.service.validate()

            # Get services to test
            services = self.service.get_services_to_test()

            # Run fuzzing
            sessions = self.service.run_fuzzing(services, max_payloads)

            # Display results
            report_path = target_path / output
            self.presenter.display_results(sessions, report_path, output)

            return 0

        except RuntimeError as e:
            self.presenter.display_error(str(e))
            return 1

        except Exception as e:
            self.presenter.display_error(str(e))
            return 1


# CLI command definition
@click.command(name="security-test")
@click.argument("directory", default=".", required=False)
@click.option(
    "--service",
    "-s",
    help="Service to fuzz (default: all services)",
)
@click.option(
    "--max-payloads",
    "-m",
    default=10,
    help="Maximum payloads per field (default: 10)",
)
@click.option(
    "--output",
    "-o",
    default="SECURITY_REPORT.md",
    help="Output report filename (default: SECURITY_REPORT.md)",
)
@click.option(
    "--attack-types",
    "-a",
    help="Comma-separated attack types (sql,nosql,xss,buffer,all)",
)
def security_test_command(
    directory: str,
    service: Optional[str],
    max_payloads: int,
    output: str,
    attack_types: Optional[str],
) -> None:
    """Run AI-driven security fuzzing tests.

    Performs intelligent security testing including:
    - SQL Injection and NoSQL Injection detection
    - Buffer overflow and large blob attacks
    - Type manipulation and logic bypass attempts
    - XSS and Command Injection testing

    Monitors backend resilience and generates security report.

    Examples:
        e2e security-test                    # Test all services
        e2e security-test --service users    # Test specific service
        e2e security-test --max-payloads 20  # More thorough testing
        e2e security-test --attack-types sql,nosql  # Specific attacks
    """
    command = SecurityTestCommand()
    exit_code = command.execute(directory, service, max_payloads, output, attack_types)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return security_test_command


def get_name():
    """Return the command name."""
    return "security-test"


def get_help():
    """Return the command help text."""
    return "Run AI-driven security fuzzing tests"
