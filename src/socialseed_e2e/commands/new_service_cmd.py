"""New service command for socialseed-e2e CLI.

This module provides the new-service command using POO and SOLID principles.
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from socialseed_e2e.utils import TemplateEngine, to_snake_case, to_class_name


console = Console()


class ServiceCreator:
    """Handles the creation of new services (Single Responsibility)."""

    def __init__(self, force: bool = False):
        self.force = force

    def create(self, name: str, base_url: str, health_endpoint: str) -> None:
        """Create a new service with scaffolding."""
        service_path = Path("services") / name
        modules_path = service_path / "modules"

        self._create_directories(service_path, modules_path)
        self._create_init_files(service_path, modules_path, name)
        self._create_template_files(service_path, name)
        self._update_config(name, base_url, health_endpoint)

    def _create_directories(self, service_path: Path, modules_path: Path) -> None:
        """Create service directories."""
        try:
            service_path.mkdir(parents=True)
            modules_path.mkdir()
            console.print(f"  [green]✓[/green] Created: services/{service_path.name}/")
            console.print(
                f"  [green]✓[/green] Created: services/{service_path.name}/modules/"
            )
        except FileExistsError:
            console.print(
                f"  [yellow]⚠[/yellow] Service '{service_path.name}' already exists"
            )
            if not self.force:
                console.print("   Use --force to overwrite existing files")
                sys.exit(1)

    def _create_init_files(
        self, service_path: Path, modules_path: Path, name: str
    ) -> None:
        """Create __init__.py files."""
        self._write_file(service_path / "__init__.py", f'"""Service {name}."""\n')
        self._write_file(
            modules_path / "__init__.py", f'"""Test modules for {name}."""\n'
        )
        console.print(f"  [green]✓[/green] Created: services/{name}/__init__.py")
        console.print(
            f"  [green]✓[/green] Created: services/{name}/modules/__init__.py"
        )

    def _write_file(self, path: Path, content: str) -> None:
        """Write content to file."""
        path.write_text(content)

    def _create_template_files(self, service_path: Path, name: str) -> None:
        """Create service template files."""
        engine = TemplateEngine()
        class_name = _to_class_name(name)
        snake_name = to_snake_case(name)

        template_vars = {
            "service_name": name,
            "class_name": class_name,
            "snake_case_name": snake_name,
            "endpoint_prefix": "entities",
        }

        # Service page
        engine.render_to_file(
            "service_page.py.template",
            template_vars,
            str(service_path / f"{snake_name}_page.py"),
            overwrite=False,
        )
        console.print(
            f"  [green]✓[/green] Created: services/{name}/{snake_name}_page.py"
        )

        # Config
        engine.render_to_file(
            "config.py.template",
            template_vars,
            str(service_path / "config.py"),
            overwrite=False,
        )
        console.print(f"  [green]✓[/green] Created: services/{name}/config.py")

        # Data schema
        engine.render_to_file(
            "data_schema.py.template",
            template_vars,
            str(service_path / "data_schema.py"),
            overwrite=False,
        )
        console.print(f"  [green]✓[/green] Created: services/{name}/data_schema.py")

    def _update_config(self, name: str, base_url: str, health_endpoint: str) -> None:
        """Update e2e.conf with new service."""
        from socialseed_e2e.core.config_loader import ApiConfigLoader

        try:
            loader = ApiConfigLoader()
            config = loader.load()

            if config.services is None:
                config.services = {}

            from socialseed_e2e.core.config_loader import ServiceConfig

            config.services[name] = ServiceConfig(
                name=name,
                base_url=base_url,
                health_endpoint=health_endpoint,
            )

            loader.save(config)
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Could not update e2e.conf: {e}")


class ServiceCreatorValidator:
    """Validates service creation requirements (Single Responsibility)."""

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
@click.option(
    "--base-url",
    default="http://localhost:8080",
    help="Service base URL",
)
@click.option("--health-endpoint", default="/health", help="Health check endpoint")
@click.option(
    "--force", "-f", is_flag=True, help="Overwrite existing files without prompting"
)
def new_service_cmd(name: str, base_url: str, health_endpoint: str, force: bool):
    """Create a new service with scaffolding.

    Creates the complete directory structure and template files for a new
    service, including data_schema.py, service_page.py, and the modules directory.

    Examples:
        e2e new-service users-api                                    # Create with defaults
        e2e new-service payment-service --base-url http://localhost:8081
        e2e new-service auth-service --base-url http://localhost:8080 --health-endpoint /actuator/health
        e2e new-service auth-service --force                         # Overwrite without prompting
    """
    console.print(f"\n🔧 [bold blue]Creating service:[/bold blue] {name}\n")

    if not ServiceCreatorValidator.validate_project():
        sys.exit(1)

    creator = ServiceCreator(force=force)
    creator.create(name, base_url, health_endpoint)

    console.print(
        f"\n[bold green]✅ Service '{name}' created successfully![/bold green]\n"
    )

    console.print(
        Panel(
            f"[bold]Next steps:[/bold]\n\n"
            f"1. Edit [cyan]services/{name}/data_schema.py[/cyan] to define your DTOs\n"
            f"2. Run: [cyan]e2e new-test <name> --service {name}[/cyan]\n"
            f"3. Run: [cyan]e2e run --service {name}[/cyan]",
            title="🚀 Continue",
            border_style="blue",
        )
    )


def get_new_service_command():
    """Get the new-service command for lazy loading."""
    return new_service_cmd


__all__ = ["new_service_cmd", "get_new_service_command"]
