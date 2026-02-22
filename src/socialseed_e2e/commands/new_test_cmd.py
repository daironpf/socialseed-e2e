"""New test command for socialseed-e2e CLI.

This module provides the new-test command using POO and SOLID principles.
"""

import sys
from pathlib import Path

import click
from rich.console import Console

from socialseed_e2e.utils import TemplateEngine, to_snake_case, to_class_name


console = Console()


class TestCreator:
    """Handles the creation of new test modules (Single Responsibility)."""

    def __init__(self, force: bool = False):
        self.force = force

    def create(self, name: str, service: str, description: str) -> None:
        """Create a new test module."""
        service_path = Path("services") / service
        modules_path = service_path / "modules"

        self._validate_service_exists(service_path)
        self._ensure_modules_dir(modules_path)

        test_filename = self._generate_test_filename(modules_path, name)
        test_path = modules_path / test_filename

        self._check_overwrite(test_path)
        self._create_test_file(test_path, service, name, description)

    def _validate_service_exists(self, service_path: Path) -> None:
        """Validate that the service exists."""
        if not service_path.exists():
            console.print(
                f"[red]❌ Error:[/red] Service '{service_path.name}' does not exist."
            )
            console.print(
                f"   Create the service first: [cyan]e2e new-service {service_path.name}[/cyan]"
            )
            sys.exit(1)

    def _ensure_modules_dir(self, modules_path: Path) -> None:
        """Ensure modules directory exists."""
        if not modules_path.exists():
            modules_path.mkdir(parents=True)

    def _generate_test_filename(self, modules_path: Path, name: str) -> str:
        """Generate test filename with numeric prefix."""
        existing_tests = sorted(modules_path.glob("[0-9][0-9]_*.py"))

        if existing_tests:
            last_num = int(existing_tests[-1].name[:2])
            next_num = last_num + 1
        else:
            next_num = 1

        safe_name = to_snake_case(name)
        return f"{next_num:02d}_{safe_name}_flow.py"

    def _check_overwrite(self, test_path: Path) -> None:
        """Check if test already exists."""
        if test_path.exists():
            console.print(f"[yellow]⚠[/yellow] Test '{test_path.stem}' already exists.")
            if not self.force:
                console.print("   Use --force to overwrite existing files")
                sys.exit(1)

    def _create_test_file(
        self, test_path: Path, service: str, name: str, description: str
    ) -> None:
        """Create the test file from template."""
        engine = TemplateEngine()
        class_name = to_class_name(service)
        snake_name = to_snake_case(service)
        test_description = description or f"Test flow for {name}"

        template_vars = {
            "service_name": service,
            "class_name": class_name,
            "snake_case_name": snake_name,
            "test_name": name,
            "test_description": test_description,
        }

        engine.render_to_file(
            "test_module.py.template",
            template_vars,
            str(test_path),
            overwrite=False,
        )

        console.print(
            f"  [green]✓[/green] Created: services/{service}/modules/{test_path.name}"
        )


class TestCreatorValidator:
    """Validates test creation requirements (Single Responsibility)."""

    @staticmethod
    def validate_project() -> bool:
        """Check if we're in an E2E project."""
        if not Path("e2e.conf").exists():
            console.print(
                "[red]❌ Error:[/red] e2e.conf not found. Are you in an E2E project?"
            )
            console.print("   Run: [cyan]e2e init[/cyan] first")
            return False
        return True


@click.command()
@click.argument("name")
@click.option("--service", "-s", required=True, help="Service name")
@click.option("--description", "-d", default="", help="Test description")
@click.option(
    "--force", "-f", is_flag=True, help="Overwrite existing files without prompting"
)
def new_test_cmd(name: str, service: str, description: str, force: bool):
    """Create a new test module.

    Examples:
        e2e new-test login -s auth_service
        e2e new-test create-user -s users-api -d "Test user creation"
        e2e new-test login -s auth_service --force
    """
    console.print(f"\n📝 [bold cyan]Creating test:[/bold cyan] {name}\n")

    if not TestCreatorValidator.validate_project():
        sys.exit(1)

    creator = TestCreator(force=force)
    creator.create(name, service, description)

    console.print(
        f"\n[bold green]✅ Test '{name}' created successfully![/bold green]\n"
    )


def get_new_test_command():
    """Get the new-test command for lazy loading."""
    return new_test_cmd


__all__ = ["new_test_cmd", "get_new_test_command"]
