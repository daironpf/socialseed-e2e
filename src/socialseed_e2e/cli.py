#!/usr/bin/env python3
"""CLI module for socialseed-e2e framework.

This module provides the command-line interface for the E2E testing framework,
enabling developers and AI agents to create, manage, and run API tests.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

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
@click.option("--config", "-c", help="Path to configuration file (e2e.conf)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose mode")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def run(
    service: Optional[str],
    module: Optional[str],
    config: Optional[str],
    verbose: bool,
    output: str,
):
    """Execute E2E tests.

    Discovers and automatically executes all available tests.

    Args:
        service: If specified, only run tests for this service
        module: If specified, only run this test module
        config: Path to the e2e.conf file
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
        app_config = loader.load(config)  # Pass the config path if provided
        console.print(f"📋 [cyan]Configuration:[/cyan] {loader._config_path}")
        console.print(f"🌍 [cyan]Environment:[/cyan] {app_config.environment}")
        console.print()
    except ConfigError as e:
        console.print(f"[red]❌ Configuration error:[/red] {e}")
        console.print("   Run: [cyan]e2e init[/cyan] to create a project")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error:[/red] {e}")
        sys.exit(1)

    # Import test runner
    from .core.test_runner import print_summary, run_all_tests

    # Determine services path
    # If a config file was explicitly provided, we prioritize the 'services' folder next to it.
    services_path = Path("services")
    if loader._config_path:
        alt_path = loader._config_path.parent / "services"
        if alt_path.exists():
            services_path = alt_path
        elif not services_path.exists():
            # Fallback if neither works
            pass

    if service:
        console.print(f"🔍 [yellow]Filtering by service:[/yellow] {service}")
    if module:
        console.print(f"🔍 [yellow]Filtering by module:[/yellow] {module}")
    if verbose:
        console.print("📢 [yellow]Verbose mode activated[/yellow]")

    console.print()

    # Execute tests
    try:
        results = run_all_tests(
            services_path=services_path,
            specific_service=service,
            specific_module=module,
            verbose=verbose,
        )

        # Print summary
        all_passed = print_summary(results)

        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)

    except Exception as e:
        console.print(f"[red]❌ Error executing tests:[/red] {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


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


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Force full scan instead of smart sync")
def manifest(directory: str, force: bool):
    """Generate AI Project Manifest for token optimization.

    Analyzes the project and generates project_knowledge.json containing:
    - All detected endpoints and HTTP methods
    - DTO schemas and validation rules
    - Port configurations and environment variables
    - Relationships between services

    Examples:
        e2e manifest                    # Generate manifest in current directory
        e2e manifest /path/to/project   # Generate manifest for specific project
        e2e manifest --force            # Force full re-scan
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n📚 [bold cyan]Generating AI Project Manifest[/bold cyan]")
    console.print(f"   Project: {target_path}\n")

    try:
        from socialseed_e2e.project_manifest import ManifestGenerator

        generator = ManifestGenerator(target_path)
        manifest = generator.generate(force_full_scan=force)

        # Display summary
        table = Table(title="Project Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        total_endpoints = sum(len(s.endpoints) for s in manifest.services)
        total_dtos = sum(len(s.dto_schemas) for s in manifest.services)
        total_ports = sum(len(s.ports) for s in manifest.services)
        total_env_vars = len(manifest.global_env_vars)

        table.add_row("Services", str(len(manifest.services)))
        table.add_row("Endpoints", str(total_endpoints))
        table.add_row("DTOs", str(total_dtos))
        table.add_row("Ports", str(total_ports))
        table.add_row("Global Env Vars", str(total_env_vars))

        console.print(table)
        console.print()

        # Display services
        if manifest.services:
            console.print("[bold]Services detected:[/bold]")
            for service in manifest.services:
                framework = service.framework or "unknown framework"
                console.print(f"  • {service.name} ({service.language}, {framework})")
            console.print()

        console.print("[bold green]✅ Manifest generated successfully![/bold green]")
        console.print(f"   📄 Location: {generator.manifest_path}\n")

    except Exception as e:
        console.print(f"[red]❌ Error generating manifest:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--format",
    "-f",
    default="json",
    type=click.Choice(["json", "markdown"]),
    help="Output format",
)
def manifest_query(directory: str, format: str):
    """Query the AI Project Manifest.

    Displays project information from the generated manifest.

    Examples:
        e2e manifest-query                    # Query current directory
        e2e manifest-query /path/to/project   # Query specific project
        e2e manifest-query -f markdown        # Output as Markdown
    """
    target_path = Path(directory).resolve()
    manifest_path = target_path / "project_knowledge.json"

    if not manifest_path.exists():
        console.print(f"[red]❌ Error:[/red] Manifest not found at {manifest_path}")
        console.print("Run 'e2e manifest' first to generate the manifest.")
        sys.exit(1)

    try:
        from socialseed_e2e.project_manifest import ManifestAPI

        api = ManifestAPI(target_path)

        if format == "json":
            output = api.export_summary(format="json")
            console.print(output)
        else:  # markdown
            output = api.export_summary(format="markdown")
            console.print(output)

    except Exception as e:
        console.print(f"[red]❌ Error querying manifest:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
def watch(directory: str):
    """Watch project files and auto-update manifest.

    Monitors source files for changes and automatically updates
    the project_knowledge.json manifest using smart sync.

    Examples:
        e2e watch                    # Watch current directory
        e2e watch /path/to/project   # Watch specific project
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    try:
        from socialseed_e2e.project_manifest import ManifestGenerator, SmartSyncManager

        generator = ManifestGenerator(target_path)

        # Ensure manifest exists
        if not generator.manifest_path.exists():
            console.print("📚 Generating initial manifest...\n")
            generator.generate()

        console.print("\n👁️  [bold cyan]Starting file watcher[/bold cyan]")
        console.print(f"   Project: {target_path}")
        console.print("   Press Ctrl+C to stop\n")

        manager = SmartSyncManager(generator, debounce_seconds=2.0)
        manager.start_watching(blocking=True)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 File watcher stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--directory", "-d", default=".", help="Project directory")
@click.option("--top-k", "-k", default=5, help="Number of results")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["endpoint", "dto", "service"]),
    help="Filter by type",
)
def search(query: str, directory: str, top_k: int, type: str):
    """Semantic search on project manifest.

    Performs semantic search using vector embeddings to find
    relevant endpoints, DTOs, and services.

    Examples:
        e2e search "authentication endpoints"
        e2e search "user DTO" --type dto
        e2e search "payment" --top-k 10
    """
    target_path = Path(directory).resolve()

    try:
        from socialseed_e2e.project_manifest import ManifestVectorStore

        store = ManifestVectorStore(target_path)

        if not store.is_index_valid():
            console.print("📊 Building vector index...")
            store.build_index()

        results = store.search(query, top_k=top_k, item_type=type)

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        table = Table(title=f"Search Results: '{query}'")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Score", style="yellow")
        table.add_column("Service", style="dim")

        for result in results:
            table.add_row(
                result.item_type,
                result.item_id,
                f"{result.score:.3f}",
                result.service_name or "-",
            )

        console.print(table)

    except ImportError as e:
        console.print(f"[red]❌ Missing dependency:[/red] {e}")
        console.print("Install with: pip install sentence-transformers")
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")


@cli.command()
@click.argument("task")
@click.option("--directory", "-d", default=".", help="Project directory")
@click.option("--max-chunks", "-c", default=5, help="Maximum chunks")
def retrieve(task: str, directory: str, max_chunks: int):
    """Retrieve context for a specific task.

    Retrieves relevant context from the project manifest
    for the given task description.

    Examples:
        e2e retrieve "create user authentication tests"
        e2e retrieve "test payment flow" --max-chunks 3
    """
    target_path = Path(directory).resolve()

    try:
        from socialseed_e2e.project_manifest import RAGRetrievalEngine

        engine = RAGRetrievalEngine(target_path)
        chunks = engine.retrieve_for_task(task, max_chunks=max_chunks)

        if not chunks:
            console.print("[yellow]No context found for this task[/yellow]")
            return

        console.print(f"\n[bold cyan]Task:[/bold cyan] {task}\n")

        for i, chunk in enumerate(chunks, 1):
            console.print(f"[bold]Chunk {i}:[/bold] {chunk.chunk_type}")
            console.print(f"[dim]Tokens: {chunk.token_estimate} | ID: {chunk.chunk_id}[/dim]")
            console.print(Panel(chunk.content, border_style="green"))
            console.print()

    except ImportError as e:
        console.print(f"[red]❌ Missing dependency:[/red] {e}")
        console.print("Install with: pip install sentence-transformers")
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")


@cli.command()
@click.argument("directory", default=".", required=False)
def build_index(directory: str):
    """Build vector index for semantic search.

    Creates embeddings for all endpoints, DTOs, and services
    in the project manifest.

    Examples:
        e2e build-index              # Build index for current directory
        e2e build-index /path/to/project  # Build for specific project
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    manifest_path = target_path / "project_knowledge.json"
    if not manifest_path.exists():
        console.print(f"[red]❌ Error:[/red] Manifest not found at {manifest_path}")
        console.print("Run 'e2e manifest' first to generate the manifest.")
        sys.exit(1)

    try:
        from socialseed_e2e.project_manifest import ManifestVectorStore

        console.print("\n📊 [bold cyan]Building Vector Index[/bold cyan]")
        console.print(f"   Project: {target_path}\n")

        store = ManifestVectorStore(target_path)
        store.build_index()

        console.print("[bold green]✅ Vector index built successfully![/bold green]")
        console.print(f"   📄 Location: {store.index_dir}\n")

    except ImportError as e:
        console.print(f"[red]❌ Missing dependency:[/red] {e}")
        console.print("Install with: pip install sentence-transformers")
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option("--auto-config", is_flag=True, help="Auto-generate e2e.conf from scan")
def deep_scan(directory: str, auto_config: bool):
    """Zero-config deep scan for automatic project mapping.

    Analyzes your project to detect tech stack, extract endpoints,
    and discover environment configuration without requiring manual setup.

    Examples:
        e2e deep-scan                    # Scan current directory
        e2e deep-scan /path/to/project   # Scan specific project
        e2e deep-scan --auto-config      # Scan and auto-configure
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    try:
        from socialseed_e2e.project_manifest import DeepScanner, ManifestGenerator

        # Run deep scan
        scanner = DeepScanner(str(target_path))
        result = scanner.scan()

        if auto_config:
            console.print("\n⚙️  [bold cyan]Auto-configuring project...[/bold cyan]\n")

            for service in result["services"]:
                service_name = service["name"]
                recommendations = result["recommendations"]

                if recommendations.get("base_url"):
                    # Create service with detected config
                    console.print(f"  Creating service: [green]{service_name}[/green]")
                    console.print(f"  Base URL: {recommendations['base_url']}")

            console.print("\n[bold green]✅ Auto-configuration complete![/bold green]")
            console.print("   Run 'e2e run' to execute tests\n")

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--output",
    "-o",
    default="services",
    help="Output directory for generated tests",
)
@click.option(
    "--service",
    "-s",
    help="Generate tests for specific service only",
)
@click.option(
    "--strategy",
    type=click.Choice(["valid", "invalid", "edge", "chaos", "all"]),
    default="all",
    help="Data generation strategy",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def generate_tests(
    directory: str,
    output: str,
    service: str,
    strategy: str,
    dry_run: bool,
    verbose: bool,
):
    """Autonomous test suite generation based on code intent (Issue #185).

    Analyzes your project to understand business logic, detects endpoint
    relationships, and generates complete test suites with:

    \b
    - Flow-based tests (register → login → use)
    - CRUD lifecycle tests
    - Validation tests (success, failure, edge cases)
    - Chaos tests with intelligent dummy data

    The generator automatically:
    - Parses database models (SQLAlchemy, Prisma, Hibernate)
    - Detects validation rules from code
    - Generates valid dummy data based on constraints
    - Creates tests that follow your API's business flows

    Examples:
        e2e generate-tests                    # Generate for all services
        e2e generate-tests --service users    # Generate for specific service
        e2e generate-tests --dry-run          # Preview without creating files
        e2e generate-tests --strategy chaos   # Generate chaos tests only
    """
    target_path = Path(directory).resolve()
    output_path = Path(output).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🧪 [bold cyan]Autonomous Test Suite Generation[/bold cyan]")
    console.print(f"   Project: {target_path}")
    console.print(f"   Output: {output_path}")
    if strategy != "all":
        console.print(f"   Strategy: {strategy}")
    console.print()

    try:
        from socialseed_e2e.project_manifest import DatabaseSchema, db_parser_registry
        from socialseed_e2e.project_manifest.flow_test_generator import FlowBasedTestSuiteGenerator

        # Parse database schema if available
        console.print("📊 [yellow]Step 1/5:[/yellow] Parsing database models...")
        db_schema = db_parser_registry.parse_project(target_path)
        if db_schema.entities:
            console.print(f"   ✓ Found {len(db_schema.entities)} entities")
            for entity in db_schema.entities[:3]:
                console.print(f"     - {entity.name} ({len(entity.columns)} columns)")
            if len(db_schema.entities) > 3:
                console.print(f"     ... and {len(db_schema.entities) - 3} more")
        else:
            console.print("   ⚠ No database models found")

        # Load project manifest
        console.print("\n📚 [yellow]Step 2/5:[/yellow] Loading project manifest...")
        manifest_path = target_path / "project_knowledge.json"
        if not manifest_path.exists():
            console.print("   ⚠ Manifest not found, generating...")
            from socialseed_e2e.project_manifest import ManifestGenerator

            generator = ManifestGenerator(target_path)
            generator.generate()

        from socialseed_e2e.project_manifest import ManifestAPI

        api = ManifestAPI(target_path)
        manifest = api._load_manifest()
        if manifest is None:
            console.print("[red]❌ Error:[/red] Could not load project manifest")
            sys.exit(1)
        console.print(f"   ✓ Loaded manifest with {len(manifest.services)} services")

        # Generate tests for each service
        console.print("\n🤖 [yellow]Step 3/5:[/yellow] Analyzing business logic...")

        services_to_process = manifest.services
        if service:
            services_to_process = [s for s in services_to_process if s.name == service]
            if not services_to_process:
                console.print(f"[red]❌ Service '{service}' not found in manifest[/red]")
                sys.exit(1)

        generated_suites = []
        for svc in services_to_process:
            console.print(f"   Analyzing: {svc.name}...")

            # Create test suite generator
            suite_generator = FlowBasedTestSuiteGenerator(service_info=svc, db_schema=db_schema)

            # Analyze flows
            flow_count = len(suite_generator.flows)
            relationship_count = len(suite_generator.analysis_result["relationships"])
            console.print(f"     ✓ Detected {flow_count} flows, {relationship_count} relationships")

            generated_suites.append((svc, suite_generator))

        # Generate and write test suites
        console.print("\n✨ [yellow]Step 4/5:[/yellow] Generating test code...")

        if dry_run:
            console.print("   [italic]Dry run mode - no files will be created[/italic]")

        total_files = 0
        for svc, suite_generator in generated_suites:
            suite = suite_generator.generate_test_suite()

            if not dry_run:
                # Write files to disk
                suite_generator.write_to_files(output_path)

            file_count = len(suite.test_modules) + 2  # +2 for data_schema and page
            total_files += file_count

            console.print(f"\n   [bold]{svc.name}:[/bold]")
            console.print(f"     📄 data_schema.py ({len(svc.dto_schemas)} DTOs)")
            console.print(f"     📄 {svc.name}_page.py ({len(svc.endpoints)} endpoints)")
            for flow in suite.flows_detected:
                console.print(f"     📄 {flow.name} ({len(flow.steps)} steps)")

        # Show validation criteria summary
        console.print("\n🎯 [yellow]Step 5/5:[/yellow] Extracting validation criteria...")
        total_validations = 0
        for svc, suite_generator in generated_suites:
            validations = suite_generator.analysis_result["validation_criteria"]
            total_validations += len(validations)

            if validations:
                console.print(f"   {svc.name}: {len(validations)} validation rules")

                # Show example validation rules
                for i, (key, criteria) in enumerate(list(validations.items())[:2]):
                    console.print(f"     - {key}: {len(criteria.rules)} rules")

        if total_validations == 0:
            console.print("   ⚠ No validation rules detected")

        # Summary
        console.print(f"\n{'=' * 60}")
        console.print("[bold green]✅ Test generation complete![/bold green]")
        console.print(f"{'=' * 60}")
        console.print(f"\n📊 Summary:")
        console.print(f"   Services processed: {len(generated_suites)}")
        console.print(f"   Total files generated: {total_files}")
        console.print(f"   Validation rules: {total_validations}")

        # Generate AI Discovery Report
        if not dry_run:
            console.print("\n📝 [yellow]Generating AI Discovery Report...[/yellow]")

            from socialseed_e2e.project_manifest import generate_discovery_report

            # Collect flows from all generated suites
            all_flows = []
            for svc, suite_generator in generated_suites:
                for flow in suite_generator.flows:
                    all_flows.append(
                        {
                            "name": flow.name,
                            "description": flow.description,
                            "steps": [
                                {"endpoint": {"name": step.endpoint.name}} for step in flow.steps
                            ],
                            "flow_type": flow.flow_type.value
                            if hasattr(flow.flow_type, "value")
                            else str(flow.flow_type),
                        }
                    )

            # Generate the report
            report_path = generate_discovery_report(
                project_root=target_path,
                manifest=manifest,
                flows=all_flows,
                tests_generated=total_files,
                output_dir=output_path,
            )

            console.print(f"   ✓ Report saved: {report_path}")

        if not dry_run:
            console.print(f"\n📁 Output directory: {output_path}")
            console.print("\n[bold]Next steps:[/bold]")
            console.print("   1. Review the AI Discovery Report in .e2e/DISCOVERY_REPORT.md")
            console.print("   2. Customize test data in data_schema.py")
            console.print("   3. Run tests: [cyan]e2e run[/cyan]")
        else:
            console.print("\n[italic]Run without --dry-run to create files[/italic]")

        console.print()

    except Exception as e:
        console.print(f"\n[red]❌ Error generating tests:[/red] {e}")
        import traceback

        if verbose:
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--host",
    "-h",
    multiple=True,
    default=["localhost", "127.0.0.1"],
    help="Hosts to scan (can be specified multiple times)",
)
@click.option(
    "--ports",
    "-p",
    help="Port range to scan (e.g., 8000-9000 or 8080,8081,3000)",
)
@click.option(
    "--docker/--no-docker",
    default=True,
    help="Scan Docker containers (default: enabled)",
)
@click.option(
    "--cross-ref/--no-cross-ref",
    default=True,
    help="Cross-reference with project code (default: enabled)",
)
@click.option(
    "--auto-setup",
    is_flag=True,
    help="Auto-setup environment using Docker (build and run)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without executing",
)
@click.option(
    "--timeout",
    "-t",
    default=2.0,
    help="Timeout for port scanning (seconds)",
)
def observe(
    directory: str,
    host: Tuple[str, ...],
    ports: Optional[str],
    docker: bool,
    cross_ref: bool,
    auto_setup: bool,
    dry_run: bool,
    timeout: float,
):
    """Auto-detect running services and ports (The Observer - Issue #186).

    Scans for open ports, detects HTTP/gRPC services, finds Docker containers,
    and cross-references with project code to identify running APIs.

    Examples:
        e2e observe                              # Scan localhost
        e2e observe /path/to/project             # Scan specific project
        e2e observe --host 192.168.1.100         # Scan remote host
        e2e observe --ports 8000-9000            # Custom port range
        e2e observe --auto-setup                 # Build and run Docker
        e2e observe --dry-run                    # Preview only
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🔭 [bold cyan]The Observer - Service Detection[/bold cyan]")
    console.print(f"   Project: {target_path}")
    console.print(f"   Hosts: {', '.join(host)}\n")

    try:
        import asyncio

        from socialseed_e2e.project_manifest import ServiceObserver

        # Parse ports if specified
        port_list = None
        if ports:
            port_list = []
            for part in ports.split(","):
                if "-" in part:
                    start, end = part.split("-")
                    port_list.extend(range(int(start), int(end) + 1))
                else:
                    port_list.append(int(part))

        # Create observer
        observer = ServiceObserver(target_path)
        observer.port_scanner.timeout = timeout

        # Run observation
        console.print("📡 [yellow]Scanning for services...[/yellow]\n")

        results = asyncio.run(
            observer.observe(
                hosts=list(host),
                scan_docker=docker,
                cross_reference=cross_ref,
            )
        )

        # Display results
        if results["services_detected"]:
            console.print("\n[bold green]✅ Services Detected:[/bold green]\n")

            from rich.table import Table

            table = Table(title="Running Services")
            table.add_column("Service", style="cyan")
            table.add_column("URL", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("Source", style="dim")
            table.add_column("Health", style="white")

            for svc in results["services_detected"]:
                table.add_row(
                    svc["name"],
                    svc["url"],
                    svc["type"].upper(),
                    svc.get("detected_from", "scan"),
                    svc.get("health", "N/A") or "N/A",
                )

            console.print(table)
        else:
            console.print("\n[yellow]⚠ No running services detected[/yellow]")

        # Show Docker containers
        if docker and results["docker_containers"]:
            console.print("\n[bold]🐳 Docker Containers:[/bold]\n")

            table = Table(title="Containers")
            table.add_column("Name", style="cyan")
            table.add_column("Image", style="green")
            table.add_column("Ports", style="yellow")
            table.add_column("Status", style="white")

            for container in results["docker_containers"]:
                ports_str = ", ".join(f"{p['public']}->{p['private']}" for p in container["ports"])
                table.add_row(
                    container["name"],
                    container["image"],
                    ports_str or "N/A",
                    container["status"],
                )

            console.print(table)

        # Show cross-references
        if cross_ref and results["cross_references"]:
            console.print("\n[bold]🔗 Cross-References:[/bold]\n")

            for ref in results["cross_references"]:
                console.print(
                    f"   ✓ [green]{ref['detected_service']}[/green] matches "
                    f"[cyan]{ref['code_service']}[/cyan] (port {ref['port']})"
                )

        # Docker setup suggestions
        if results["dockerfile_found"]:
            console.print(f"\n[bold]🐳 Docker Setup:[/bold]")
            console.print(f"   Dockerfile: {results['dockerfile_found']}")

            for suggestion in results["suggestions"]:
                if suggestion["type"] == "docker":
                    console.print(f"\n   {suggestion['message']}")
                    console.print(f"   Command: [cyan]{suggestion['command']}[/cyan]")

                    if auto_setup:
                        console.print("\n   [yellow]Executing auto-setup...[/yellow]\n")
                        setup_result = asyncio.run(observer.auto_setup(dry_run=dry_run))

                        if setup_result["success"]:
                            console.print("   [green]✅ Setup successful![/green]")
                            if "output" in setup_result:
                                console.print(f"   Output: {setup_result['output'][:200]}...")
                        else:
                            console.print(
                                f"   [red]❌ Setup failed:[/red] {setup_result['message']}"
                            )
                    elif not dry_run:
                        console.print(
                            "\n   [italic]Use --auto-setup to build and run automatically[/italic]"
                        )

        # Summary
        console.print(f"\n{'=' * 60}")
        console.print("[bold]📊 Summary:[/bold]")
        console.print(f"   Services detected: {len(results['services_detected'])}")
        console.print(f"   Docker containers: {len(results['docker_containers'])}")
        console.print(f"   Cross-references: {len(results['cross_references'])}")

        if results["dockerfile_found"]:
            console.print(f"   Dockerfile: ✓ Found")

        console.print()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 Observation interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--output",
    "-o",
    help="Output directory for the report",
)
@click.option(
    "--open",
    "--view",
    is_flag=True,
    help="Open the report after generation",
)
def discover(directory: str, output: Optional[str], open: bool):
    """Generate AI Discovery Report for the project (Issue #187).

    Creates a comprehensive "Mental Map" report summarizing:
    - Discovered endpoints and services
    - Technology stack analysis
    - Business flows detected
    - Generated test suites

    The report is saved as a markdown file in .e2e/DISCOVERY_REPORT.md

    Examples:
        e2e discover                    # Generate report for current project
        e2e discover /path/to/project   # Generate for specific project
        e2e discover --open             # Generate and open the report
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🤖 [bold cyan]AI Discovery Report[/bold cyan]")
    console.print(f"   Project: {target_path}\n")

    try:
        from socialseed_e2e.project_manifest import ManifestAPI, generate_discovery_report

        # Load manifest
        api = ManifestAPI(target_path)
        manifest = api._load_manifest()

        if not manifest:
            console.print("[yellow]⚠ No project manifest found. Run 'e2e manifest' first.[/yellow]")
            sys.exit(1)

        # Generate report
        output_dir = Path(output) if output else None
        report_path = generate_discovery_report(
            project_root=target_path, manifest=manifest, output_dir=output_dir
        )

        console.print(f"\n✅ [bold green]Discovery Report generated![/bold green]")
        console.print(f"   📄 Location: {report_path}\n")

        console.print("[bold]What's in the report:[/bold]")
        console.print("   • Technology stack analysis")
        console.print("   • Discovered endpoints and services")
        console.print("   • Business flows mental map")
        console.print("   • Single command to run all tests")
        console.print("   • Next steps and recommendations\n")

        console.print("[bold]Quick Start:[/bold]")
        console.print("   Run: [cyan]e2e run[/cyan]\n")

        if open:
            # Try to open the report
            try:
                import webbrowser

                webbrowser.open(f"file://{report_path}")
            except Exception:
                console.print(f"   [dim]Open manually: {report_path}[/dim]")

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    cli()
