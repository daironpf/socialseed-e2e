#!/usr/bin/env python3
"""CLI module for socialseed-e2e framework.

This module provides the command-line interface for the E2E testing framework,
enabling developers and AI agents to create, manage, and run API tests.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from socialseed_e2e import __version__
from socialseed_e2e.core.config_loader import ApiConfigLoader, ConfigError
from socialseed_e2e.utils import TemplateEngine, to_class_name, to_snake_case

console = Console()


@click.group()
@click.version_option(version=str(__version__), prog_name="socialseed-e2e")
def cli():
    """socialseed-e2e: E2E Framework for REST APIs.

    A service-agnostic framework for End-to-End testing of REST APIs,
    designed for developers and AI agents.
    """
    pass


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Overwrite existing files")
def init(directory: str, force: bool):
    """Initialize a new E2E project.

    Creates the initial directory structure and configuration files.

    Args:
        directory: Directory to create the project (default: current directory)
        force: If True, overwrites existing files
    """
    target_path = Path(directory).resolve()

    console.print(f"\n🌱 [bold green]Initializing E2E project at:[/bold green] {target_path}\n")

    # Create directory structure
    dirs_to_create = [
        target_path / "services",
        target_path / "tests",
        target_path / ".github" / "workflows",
    ]

    created_dirs = []
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            created_dirs.append(
                dir_path.name
                if dir_path.parent == target_path
                else str(dir_path.relative_to(target_path))
            )
            console.print(f"  [green]✓[/green] Created: {dir_path.relative_to(target_path)}")
        else:
            console.print(
                f"  [yellow]⚠[/yellow] Already exists: {dir_path.relative_to(target_path)}"
            )

    # Create configuration file
    config_path = target_path / "e2e.conf"
    if not config_path.exists() or force:
        engine = TemplateEngine()
        engine.render_to_file(
            "e2e.conf.template",
            {
                "environment": "dev",
                "timeout": "30000",
                "user_agent": "socialseed-e2e/1.0",
                "verbose": "true",
                "services_config": "",
            },
            str(config_path),
            overwrite=force,
        )
        console.print("  [green]✓[/green] Created: e2e.conf")
    else:
        console.print("  [yellow]⚠[/yellow] Already exists: e2e.conf (use --force to overwrite)")

    # Create .gitignore
    gitignore_path = target_path / ".gitignore"
    if not gitignore_path.exists() or force:
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# E2E Framework
test-results/
.coverage
htmlcov/
"""
        gitignore_path.write_text(gitignore_content)
        console.print("  [green]✓[/green] Created: .gitignore")
    else:
        console.print("  [yellow]⚠[/yellow] Already exists: .gitignore")

    # Create requirements.txt
    requirements_path = target_path / "requirements.txt"
    if not requirements_path.exists() or force:
        requirements_content = """pydantic>=2.0.0
email-validator>=2.0.0
"""
        requirements_path.write_text(requirements_content)
        console.print("  [green]✓[/green] Created: requirements.txt")
    else:
        console.print("  [yellow]⚠[/yellow] Already exists: requirements.txt")

    # Show success message
    console.print("\n[bold green]✅ Project initialized successfully![/bold green]\n")

    # Create .agent folder for AI documentation
    agent_docs_path = target_path / ".agent"
    if not agent_docs_path.exists() or force:
        if not agent_docs_path.exists():
            agent_docs_path.mkdir()

        # Instantiate engine if it doesn't exist
        engine = TemplateEngine()

        # List of documentation templates for the agent
        agent_templates = [
            ("agent_docs/FRAMEWORK_CONTEXT.md.template", "FRAMEWORK_CONTEXT.md"),
            ("agent_docs/WORKFLOW_GENERATION.md.template", "WORKFLOW_GENERATION.md"),
            ("agent_docs/EXAMPLE_TEST.md.template", "EXAMPLE_TEST.md"),
            ("agent_docs/AGENT_GUIDE.md.template", "AGENT_GUIDE.md"),
        ]

        for template_name, output_name in agent_templates:
            engine.render_to_file(
                template_name,
                {},  # No variables to replace in these MD
                str(agent_docs_path / output_name),
                overwrite=force,
            )

        console.print("  [green]✓[/green] Created: .agent/ (AI Documentation)")

    # Copy verification script
    verify_script_path = target_path / "verify_installation.py"
    if not verify_script_path.exists() or force:
        try:
            import shutil

            from socialseed_e2e.templates import __file__ as templates_init

            templates_dir = Path(templates_init).parent
            source_script = templates_dir / "verify_installation.py"
            if source_script.exists():
                shutil.copy(str(source_script), str(verify_script_path))
                console.print("  [green]✓[/green] Created: verify_installation.py")
        except Exception:
            # If it fails, it's not critical
            pass

    console.print(
        Panel(
            "[bold]Next steps:[/bold]\n\n"
            "1. Edit [cyan]e2e.conf[/cyan] to configure your API\n"
            '2. Ask your AI Agent: [italic]"Read the AGENT_GUIDE.md and '
            'generate tests for my API"[/italic]\n'
            "3. Or do it manually: [cyan]e2e new-service <name>[/cyan]",
            title="🚀 Getting Started",
            border_style="green",
        )
    )

    console.print(
        Panel(
            "[bold]⚠️  Important for AI Agents:[/bold]\n\n"
            "• Use [cyan]absolute imports[/cyan] (not relative) in tests\n"
            "• Remember to use [cyan]model_dump(by_alias=True)[/cyan] to serialize DTOs\n"
            "• Review [cyan]AGENT_GUIDE.md[/cyan] for correct patterns and conventions",
            title="🤖 Development Guide",
            border_style="yellow",
        )
    )

    # 1. Auto-install dependencies (if requirements.txt was created or force=True)
    console.print("\n📦 Installing dependencies...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=str(target_path),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            console.print("  [green]✓[/green] Dependencies installed")
        else:
            console.print("  [yellow]⚠ Warning:[/yellow] Some dependencies could not be installed")
            if result.stderr:
                console.print(f"  [dim]{result.stderr[:200]}...[/dim]")
    except subprocess.TimeoutExpired:
        console.print("  [yellow]⚠ Warning:[/yellow] Installation took too long")
    except Exception as e:
        console.print(f"  [yellow]⚠ Warning:[/yellow] Could not install dependencies: {e}")

    # 2. Run verification (always)
    console.print("\n🔍 Verifying installation...")
    all_checks_passed = False
    try:
        # Try to import and run verification
        import importlib.util

        verify_script_path = target_path / "verify_installation.py"
        if verify_script_path.exists():
            spec = importlib.util.spec_from_file_location(
                "verify_installation", str(verify_script_path)
            )
            verify_module = None
            if spec and spec.loader:
                verify_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(verify_module)

            # Run the verification function if it exists
            if verify_module and hasattr(verify_module, "run_verification"):
                all_checks_passed = verify_module.run_verification(str(target_path))
            else:
                # Fallback: run via subprocess
                result = subprocess.run(
                    [sys.executable, str(verify_script_path), str(target_path)],
                    cwd=str(target_path),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                all_checks_passed = result.returncode == 0
                if result.stdout:
                    console.print(result.stdout)
        else:
            console.print("  [yellow]⚠[/yellow] Verification script not found")
    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] Could not run verification: {e}")
        all_checks_passed = True  # Consider successful if verification couldn't run

    # 3. Final success panel (if all checks pass)
    if all_checks_passed:
        console.print(
            Panel(
                "[bold green]✅ ALL READY![/bold green] Your project is configured and verified.\n\n"
                "🤖 You can ask your AI Agent to read [cyan].agent/AGENT_GUIDE.md[/cyan]\n"
                "🚀 And generate E2E tests automatically",
                title="🎉 Success",
                border_style="green",
            )
        )


@cli.command()
@click.argument("name")
@click.option("--base-url", default="http://localhost:8080", help="Service base URL")
@click.option("--health-endpoint", default="/health", help="Health check endpoint")
def new_service(name: str, base_url: str, health_endpoint: str):
    """Create a new service with scaffolding.

    Args:
        name: Service name (e.g.: users-api)
        base_url: Service base URL
        health_endpoint: Health check endpoint
    """
    console.print(f"\n🔧 [bold blue]Creating service:[/bold blue] {name}\n")

    # Verify we are in an E2E project
    if not _is_e2e_project():
        console.print("[red]❌ Error:[/red] e2e.conf not found. Are you in an E2E project?")
        console.print("   Run: [cyan]e2e init[/cyan] first")
        sys.exit(1)

    # Create service structure
    service_path = Path("services") / name
    modules_path = service_path / "modules"

    try:
        service_path.mkdir(parents=True)
        modules_path.mkdir()
        console.print(f"  [green]✓[/green] Created: services/{name}/")
        console.print(f"  [green]✓[/green] Created: services/{name}/modules/")
    except FileExistsError:
        console.print(f"  [yellow]⚠[/yellow] Service '{name}' already exists")
        if not click.confirm("Do you want to continue and overwrite files?"):
            return

    # Create __init__.py
    _create_file(service_path / "__init__.py", f'"""Service {name}."""\n')
    _create_file(modules_path / "__init__.py", f'"""Test modules for {name}."""\n')
    console.print(f"  [green]✓[/green] Created: services/{name}/__init__.py")
    console.print(f"  [green]✓[/green] Created: services/{name}/modules/__init__.py")

    # Initialize TemplateEngine
    engine = TemplateEngine()

    # Variables for templates
    class_name = _to_class_name(name)
    snake_case_name = to_snake_case(name)
    template_vars = {
        "service_name": name,
        "class_name": class_name,
        "snake_case_name": snake_case_name,
        "endpoint_prefix": "entities",
    }

    # Create service page
    engine.render_to_file(
        "service_page.py.template",
        template_vars,
        str(service_path / f"{snake_case_name}_page.py"),
        overwrite=False,
    )
    console.print(f"  [green]✓[/green] Created: services/{name}/{snake_case_name}_page.py")

    # Create configuration file
    engine.render_to_file(
        "config.py.template",
        template_vars,
        str(service_path / "config.py"),
        overwrite=False,
    )
    console.print(f"  [green]✓[/green] Created: services/{name}/config.py")

    # Create data_schema.py
    engine.render_to_file(
        "data_schema.py.template",
        template_vars,
        str(service_path / "data_schema.py"),
        overwrite=False,
    )
    console.print(f"  [green]✓[/green] Created: services/{name}/data_schema.py")

    # Update e2e.conf
    _update_e2e_conf(name, base_url, health_endpoint)

    console.print(f"\n[bold green]✅ Service '{name}' created successfully![/bold green]\n")

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


@cli.command()
@click.argument("name")
@click.option("--service", "-s", required=True, help="Service name")
@click.option("--description", "-d", default="", help="Test description")
def new_test(name: str, service: str, description: str):
    """Create a new test module.

    Args:
        name: Test name (e.g.: login, create-user)
        service: Service to which the test belongs
        description: Optional test description
    """
    console.print(f"\n📝 [bold cyan]Creating test:[/bold cyan] {name}\n")

    # Verify we are in an E2E project
    if not _is_e2e_project():
        console.print("[red]❌ Error:[/red] e2e.conf not found. Are you in an E2E project?")
        sys.exit(1)

    # Verify that the service exists
    service_path = Path("services") / service
    modules_path = service_path / "modules"

    if not service_path.exists():
        console.print(f"[red]❌ Error:[/red] Service '{service}' does not exist.")
        console.print(f"   Create the service first: [cyan]e2e new-service {service}[/cyan]")
        sys.exit(1)

    if not modules_path.exists():
        modules_path.mkdir(parents=True)

    # Find next available number
    existing_tests = sorted(modules_path.glob("[0-9][0-9]_*.py"))
    if existing_tests:
        last_num = int(existing_tests[-1].name[:2])
        next_num = last_num + 1
    else:
        next_num = 1

    test_filename = f"{next_num:02d}_{name}_flow.py"
    test_path = modules_path / test_filename

    # Check if it already exists
    if test_path.exists():
        console.print(f"[yellow]⚠[/yellow] Test '{name}' already exists.")
        if not click.confirm("Do you want to overwrite it?"):
            return

    # Initialize TemplateEngine
    engine = TemplateEngine()

    # Variables for template
    class_name = _to_class_name(service)
    snake_case_name = to_snake_case(service)
    test_description = description or f"Test flow for {name}"

    template_vars = {
        "service_name": service,
        "class_name": class_name,
        "snake_case_name": snake_case_name,
        "test_name": name,
        "test_description": test_description,
    }

    # Create test using template
    engine.render_to_file("test_module.py.template", template_vars, str(test_path), overwrite=False)
    console.print(f"  [green]✓[/green] Created: services/{service}/modules/{test_filename}")

    console.print(f"\n[bold green]✅ Test '{name}' created successfully![/bold green]\n")

    console.print(
        Panel(
            f"[bold]Next steps:[/bold]\n\n"
            f"1. Edit [cyan]services/{service}/modules/{test_filename}[/cyan]\n"
            f"2. Implement the test logic\n"
            f"3. Run: [cyan]e2e run --service {service}[/cyan]",
            title="🚀 Implement",
            border_style="cyan",
        )
    )


@cli.command()
@click.option("--service", "-s", help="Filter by specific service")
@click.option("--module", "-m", help="Filter by specific module")
@click.option("--verbose", "-v", is_flag=True, help="Verbose mode")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def run(service: Optional[str], module: Optional[str], verbose: bool, output: str):
    """Execute E2E tests.

    Discovers and automatically executes all available tests.

    Args:
        service: If specified, only run tests for this service
        module: If specified, only run this test module
        verbose: If True, shows detailed information
        output: Output format (text or json)
    """
    # from .core.test_orchestrator import TestOrchestrator

    console.print(f"\n🚀 [bold green]socialseed-e2e v{__version__}[/bold green]")
    console.print("═" * 50)
    console.print()

    # Verify configuration
    try:
        loader = ApiConfigLoader()
        config = loader.load()
        console.print(f"📋 [cyan]Configuration:[/cyan] {loader._config_path}")
        console.print(f"🌍 [cyan]Environment:[/cyan] {config.environment}")
        console.print()
    except ConfigError as e:
        console.print(f"[red]❌ Configuration error:[/red] {e}")
        console.print("   Run: [cyan]e2e init[/cyan] to create a project")
        sys.exit(1)

    # TODO: Implement real test execution
    # For now, show discovery information

    if service:
        console.print(f"🔍 [yellow]Filtering by service:[/yellow] {service}")
    if module:
        console.print(f"🔍 [yellow]Filtering by module:[/yellow] {module}")
    if verbose:
        console.print("📢 [yellow]Verbose mode activated[/yellow]")

    console.print()
    console.print("[yellow]⚠ Note:[/yellow] Test execution is not yet implemented")
    console.print("   This is a placeholder for version 0.1.0")
    console.print()

    # Show table of found services
    services_path = Path("services")
    if services_path.exists():
        services = [
            d.name for d in services_path.iterdir() if d.is_dir() and not d.name.startswith("__")
        ]

        if services:
            table = Table(title="Found Services")
            table.add_column("Service", style="cyan")
            table.add_column("Tests", style="green")
            table.add_column("Status", style="yellow")

            for svc in services:
                modules_path = services_path / svc / "modules"
                if modules_path.exists():
                    test_count = len(list(modules_path.glob("[0-9][0-9]_*.py")))
                    table.add_row(svc, str(test_count), "Ready" if test_count > 0 else "Empty")
                else:
                    table.add_row(svc, "0", "No modules")

            console.print(table)
        else:
            console.print("[yellow]⚠ No services found[/yellow]")
            console.print("   Create one with: [cyan]e2e new-service <name>[/cyan]")
    else:
        console.print("[red]❌ 'services/' directory not found[/red]")

    console.print()
    console.print("═" * 50)
    console.print("[bold]To implement real execution, contribute at:[/bold]")
    console.print("[cyan]https://github.com/daironpf/socialseed-e2e[/cyan]")


@cli.command()
def doctor():
    """Verify installation and dependencies.

    Checks that everything is properly configured to use the framework.
    """
    console.print("\n🏥 [bold green]socialseed-e2e Doctor[/bold green]\n")

    checks = []

    # Check Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(("Python", python_version, sys.version_info >= (3, 9)))

    # Check Playwright
    try:
        from importlib.metadata import version

        pw_version = version("playwright")
        checks.append(("Playwright", pw_version, True))
    except Exception:
        checks.append(("Playwright", "Not installed", False))

    # Check Playwright browsers
    try:
        result = subprocess.run(
            ["playwright", "install", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        browsers_installed = result.returncode == 0
        checks.append(("Playwright CLI", "Available", browsers_installed))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        checks.append(("Playwright CLI", "Not available", False))

    # Check Pydantic
    try:
        import pydantic

        checks.append(("Pydantic", pydantic.__version__, True))
    except ImportError:
        checks.append(("Pydantic", "Not installed", False))

    # Check e2e.conf
    if _is_e2e_project():
        checks.append(("Configuration", "e2e.conf found", True))
    else:
        checks.append(("Configuration", "e2e.conf not found", False))

    # Check directory structure
    services_exists = Path("services").exists()
    tests_exists = Path("tests").exists()
    checks.append(
        (
            "services/ directory",
            "OK" if services_exists else "Not found",
            services_exists,
        )
    )
    checks.append(("tests/ directory", "OK" if tests_exists else "Not found", tests_exists))

    # Show results
    table = Table(title="System Verification")
    table.add_column("Component", style="cyan")
    table.add_column("Version/Status", style="white")
    table.add_column("Status", style="bold")

    all_ok = True
    for name, value, ok in checks:
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        table.add_row(name, value, status)
        if not ok:
            all_ok = False

    console.print(table)

    console.print()
    if all_ok:
        console.print("[bold green]✅ Everything is configured correctly![/bold green]")
    else:
        console.print("[bold yellow]⚠ Some issues were found[/bold yellow]")
        console.print()
        console.print("[cyan]Suggested solutions:[/cyan]")

        if not any(name == "Playwright" and ok for name, _, ok in checks):
            console.print("  • Install Playwright: [white]pip install playwright[/white]")
        if not any(name == "Playwright CLI" and ok for name, _, ok in checks):
            console.print("  • Install browsers: [white]playwright install chromium[/white]")
        if not any(name == "Pydantic" and ok for name, _, ok in checks):
            console.print("  • Install dependencies: [white]pip install socialseed-e2e[/white]")
        if not _is_e2e_project():
            console.print("  • Initialize project: [white]e2e init[/white]")

    console.print()


@cli.command()
def config():
    """Show and validate current configuration.

    Shows the configuration loaded from e2e.conf and validates its syntax.
    """
    console.print("\n⚙️  [bold blue]E2E Configuration[/bold blue]\n")

    try:
        loader = ApiConfigLoader()
        config = loader.load()

        console.print(f"📋 [cyan]Configuration:[/cyan] {loader._config_path}")
        console.print(f"🌍 [cyan]Environment:[/cyan] {config.environment}")
        console.print(f"[cyan]Timeout:[/cyan] {config.timeout}ms")
        console.print(f"[cyan]Verbose:[/cyan] {config.verbose}")
        console.print()

        if config.services:
            table = Table(title="Configured Services")
            table.add_column("Name", style="cyan")
            table.add_column("Base URL", style="green")
            table.add_column("Health", style="yellow")
            table.add_column("Required", style="white")

            for name, svc in config.services.items():
                table.add_row(
                    name,
                    svc.base_url,
                    svc.health_endpoint or "N/A",
                    "✓" if svc.required else "✗",
                )

            console.print(table)
        else:
            console.print("[yellow]⚠ No services configured[/yellow]")
            console.print("   Use: [cyan]e2e new-service <name>[/cyan]")

        console.print()
        console.print("[bold green]✅ Valid configuration[/bold green]")

    except ConfigError as e:
        console.print(f"[red]❌ Configuration error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error:[/red] {e}")
        sys.exit(1)


# Funciones auxiliares


def _is_e2e_project() -> bool:
    """Verifica si el directorio actual es un proyecto E2E."""
    return Path("e2e.conf").exists()


def _to_class_name(name: str) -> str:
    """Convierte un nombre de servicio a nombre de clase.

    Args:
        name: Nombre del servicio (ej: users-api)

    Returns:
        str: Nombre de clase (ej: UsersApi)
    """
    return to_class_name(name)


def _create_file(path: Path, content: str) -> None:
    """Crea un archivo con el contenido especificado.

    Args:
        path: Ruta del archivo
        content: Contenido a escribir
    """
    path.write_text(content)


def _update_e2e_conf(service_name: str, base_url: str, health_endpoint: str) -> None:
    """Actualiza e2e.conf para incluir el nuevo servicio.

    Args:
        service_name: Nombre del servicio
        base_url: URL base
        health_endpoint: Endpoint de health check
    """
    config_path = Path("e2e.conf")

    if not config_path.exists():
        return

    content = config_path.read_text()

    # Check if services section already exists
    if "services:" not in content:
        content += "\nservices:\n"

    # Add service configuration
    service_config = f"""  {service_name}:
    name: {service_name}-service
    base_url: {base_url}
    health_endpoint: {health_endpoint}
    timeout: 5000
    auto_start: false
    required: true
"""

    content += service_config
    config_path.write_text(content)
    console.print("  [green]✓[/green] Updated: e2e.conf")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
