"""Install demo command for socialseed-e2e CLI.

This module provides the install-demo command using POO and SOLID principles.
"""

from pathlib import Path

import click
from rich.console import Console

from socialseed_e2e.templates import TemplateEngine


console = Console()


class DemoInstaller:
    """Handles installation of demo services (Single Responsibility)."""

    DEMO_SERVICES = [
        ("rest", "api-rest-demo.py", "demo_api_page.py"),
        ("grpc", "api-grpc-demo.py", None),
        ("websocket", "api-websocket-demo.py", None),
        ("auth", "api-auth-demo.py", None),
    ]

    def __init__(self, force: bool = False):
        self.force = force
        self.engine = TemplateEngine()

    def install(self) -> None:
        """Install all demo services."""
        target_path = Path.cwd()

        console.print(
            f"\n🎯 [bold green]Installing demo services to:[/bold green] {target_path}\n"
        )

        self._create_demo_directories(target_path)
        self._create_demo_apis(target_path)
        self._create_demo_service(target_path)
        self._update_e2e_conf()

    def _create_demo_directories(self, target_path: Path) -> None:
        """Create demo directory structure."""
        demos_path = target_path / "demos"

        for demo_type, _, _ in self.DEMO_SERVICES:
            demo_path = demos_path / demo_type
            demo_path.mkdir(parents=True, exist_ok=True)

    def _create_demo_apis(self, target_path: Path) -> None:
        """Create demo API files."""
        demos_path = target_path / "demos"

        for demo_type, api_file, _ in self.DEMO_SERVICES:
            demo_api_path = demos_path / demo_type / api_file

            if not demo_api_path.exists() or self.force:
                self.engine.render_to_file(
                    f"api_{demo_type}_demo.py.template",
                    {},
                    str(demo_api_path),
                    overwrite=self.force,
                )
                console.print(
                    f"  [green]✓[/green] Created: demos/{demo_type}/{api_file}"
                )

    def _create_demo_service(self, target_path: Path) -> None:
        """Create demo service files."""
        demo_service_path = target_path / "services" / "demo-api"
        demo_modules_path = demo_service_path / "modules"

        if not demo_service_path.exists() or self.force:
            demo_service_path.mkdir(parents=True, exist_ok=True)
            demo_modules_path.mkdir(exist_ok=True)

            # Create __init__ files
            (demo_service_path / "__init__.py").write_text("")
            (demo_modules_path / "__init__.py").write_text("")

            # Create service page
            self.engine.render_to_file(
                "demo_service_page.py.template",
                {},
                str(demo_service_path / "demo_api_page.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/demo-api/demo_api_page.py"
            )

            # Create data schema
            self.engine.render_to_file(
                "demo_data_schema.py.template",
                {},
                str(demo_service_path / "data_schema.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/demo-api/data_schema.py"
            )

            # Create config
            self.engine.render_to_file(
                "demo_config.py.template",
                {},
                str(demo_service_path / "config.py"),
                overwrite=self.force,
            )
            console.print("  [green]✓[/green] Created: services/demo-api/config.py")

            # Create test module
            self.engine.render_to_file(
                "demo_test_health.py.template",
                {},
                str(demo_modules_path / "01_health_check.py"),
                overwrite=self.force,
            )
            console.print(
                "  [green]✓[/green] Created: services/demo-api/modules/01_health_check.py"
            )

    def _update_e2e_conf(self) -> None:
        """Update e2e.conf with demo service."""
        from socialseed_e2e.core.config_loader import ApiConfigLoader, ServiceConfig

        try:
            loader = ApiConfigLoader()
            config = loader.load()

            if config.services is None:
                config.services = {}

            config.services["demo-api"] = ServiceConfig(
                name="demo-api",
                base_url="http://localhost:8765",
                health_endpoint="/health",
            )

            loader.save(config)
            console.print("  [green]✓[/green] Updated: e2e.conf")
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Could not update e2e.conf: {e}")


@click.command()
@click.option("--force", is_flag=True, help="Overwrite existing files")
def install_demo_cmd(force: bool):
    """Install demo APIs and example services to an existing project.

    This command adds multiple demo APIs covering different protocols:
    - REST API (basic CRUD) on port 5000
    - gRPC API (with proto definitions) on port 50051
    - WebSocket API (real-time) on port 50052
    - Auth API (JWT Bearer tokens) on port 5003

    Each demo includes a runnable server and corresponding test services.

    Example:
        e2e init my-project
        cd my-project
        e2e install-demo
    """
    installer = DemoInstaller(force=force)
    installer.install()

    console.print(
        "\n[bold green]✅ Demo services installed successfully![/bold green]\n"
    )
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Run demo API: [cyan]python demos/rest/api-rest-demo.py[/cyan]")
    console.print("  2. Run tests: [cyan]e2e run --service demo-api[/cyan]")


def get_install_demo_command():
    """Get the install-demo command for lazy loading."""
    return install_demo_cmd


__all__ = ["install_demo_cmd", "get_install_demo_command"]
