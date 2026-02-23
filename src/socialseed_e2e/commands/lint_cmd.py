"""Lint command for socialseed-e2e CLI.

This module provides the lint command to validate test files.
"""

import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.command()
@click.option(
    "--project",
    "-p",
    default=".",
    help="Project directory to lint",
)
@click.option(
    "--service",
    "-s",
    default=None,
    help="Specific service to lint",
)
@click.option(
    "--fix",
    is_flag=True,
    help="Attempt to fix automatically (not implemented yet)",
)
def lint_cmd(project: str, service: str, fix: bool):
    """Validate test files for common issues.

    Checks that tests follow framework standards:
    - No relative imports (must use absolute imports)
    - Proper module structure
    - Correct import paths

    Examples:
        e2e lint                                    # Validate all services
        e2e lint --service auth_service            # Validate specific service
        e2e lint --project /path/to/project      # Custom project path
    """
    from socialseed_e2e.core.test_runner import validate_service_tests

    console.print("\n🔍 [bold cyan]Validating Test Files[/bold cyan]\n")

    project_path = Path(project).resolve()
    services_path = project_path / "services"

    if not services_path.exists():
        console.print("[red]❌ Error:[/red] services/ directory not found")
        sys.exit(1)

    services_to_check = [service] if service else None

    total_issues = 0
    services_with_issues = 0

    for service_dir in sorted(services_path.iterdir()):
        if not service_dir.is_dir() or service_dir.name.startswith("__"):
            continue

        if services_to_check and service_dir.name not in services_to_check:
            continue

        console.print(f"[cyan]Checking:[/cyan] {service_dir.name}")

        issues = validate_service_tests(service_dir)

        if issues:
            services_with_issues += 1
            for module_path, module_issues in issues.items():
                module_name = Path(module_path).name
                console.print(f"  [yellow]⚠[/yellow] {module_name}")
                for issue in module_issues:
                    total_issues += 1
                    console.print(f"      Line {issue['line']}: {issue['message']}")
                    console.print(f"      → {issue['suggestion']}")
        else:
            console.print("  [green]✓[/green] No issues found")

    console.print()
    if total_issues > 0:
        console.print(
            f"[red]✗ Found {total_issues} issues in {services_with_issues} services[/red]"
        )
        console.print()
        console.print("[cyan]Note:[/cyan] Use absolute imports in tests:")
        console.print(
            "  ✅ CORRECT: from services.auth_service.data_schema import RegisterRequest"
        )
        console.print("  ❌ WRONG:   from ..data_schema import RegisterRequest")
        sys.exit(1)
    else:
        console.print("[green]✓ All tests passed validation![/green]")


def get_lint_command():
    """Get the lint command for lazy loading."""
    return lint_cmd


__all__ = ["lint_cmd", "get_lint_command"]
