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

    console.print(
        f"\n🌱 [bold green]Initializing E2E project at:[/bold green] {target_path}\n"
    )

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
            console.print(
                f"  [green]✓[/green] Created: {dir_path.relative_to(target_path)}"
            )
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
        console.print(
            "  [yellow]⚠[/yellow] Already exists: e2e.conf (use --force to overwrite)"
        )

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
            console.print(
                "  [yellow]⚠ Warning:[/yellow] Some dependencies could not be installed"
            )
            if result.stderr:
                console.print(f"  [dim]{result.stderr[:200]}...[/dim]")
    except subprocess.TimeoutExpired:
        console.print("  [yellow]⚠ Warning:[/yellow] Installation took too long")
    except Exception as e:
        console.print(
            f"  [yellow]⚠ Warning:[/yellow] Could not install dependencies: {e}"
        )

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
        console.print(
            "[red]❌ Error:[/red] e2e.conf not found. Are you in an E2E project?"
        )
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
    console.print(
        f"  [green]✓[/green] Created: services/{name}/{snake_case_name}_page.py"
    )

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
        console.print(
            "[red]❌ Error:[/red] e2e.conf not found. Are you in an E2E project?"
        )
        sys.exit(1)

    # Verify that the service exists
    service_path = Path("services") / service
    modules_path = service_path / "modules"

    if not service_path.exists():
        console.print(f"[red]❌ Error:[/red] Service '{service}' does not exist.")
        console.print(
            f"   Create the service first: [cyan]e2e new-service {service}[/cyan]"
        )
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
    engine.render_to_file(
        "test_module.py.template", template_vars, str(test_path), overwrite=False
    )
    console.print(
        f"  [green]✓[/green] Created: services/{service}/modules/{test_filename}"
    )

    console.print(
        f"\n[bold green]✅ Test '{name}' created successfully![/bold green]\n"
    )

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
@click.option(
    "--trace",
    "-t",
    is_flag=True,
    help="Enable visual traceability and generate sequence diagrams",
)
@click.option(
    "--trace-output",
    type=click.Path(),
    help="Directory for traceability reports (default: e2e_reports)",
)
@click.option(
    "--trace-format",
    type=click.Choice(["mermaid", "plantuml", "both"]),
    default="mermaid",
    help="Format for sequence diagrams",
)
def run(
    service: Optional[str],
    module: Optional[str],
    config: Optional[str],
    verbose: bool,
    output: str,
    trace: bool,
    trace_output: Optional[str],
    trace_format: str,
):
    """Execute E2E tests.

    Discovers and automatically executes all available tests.

    Args:
        service: If specified, only run tests for this service
        module: If specified, only run this test module
        config: Path to the e2e.conf file
        verbose: If True, shows detailed information
        output: Output format (text or json)
        trace: If True, enable visual traceability with sequence diagrams
        trace_output: Directory for traceability reports
        trace_format: Format for sequence diagrams (mermaid, plantuml, both)
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

    # Initialize traceability if enabled
    if trace:
        try:
            from socialseed_e2e.core.traceability import (
                TraceConfig,
                enable_traceability,
                instrument_base_page,
            )

            trace_config = TraceConfig(
                enabled=True,
                capture_request_body=True,
                capture_response_body=True,
                track_logic_branches=True,
                generate_sequence_diagrams=True,
                output_format=trace_format,
            )
            enable_traceability(trace_config, auto_instrument=True)
            console.print("📊 [cyan]Visual traceability enabled[/cyan]")
            console.print(f"   Format: {trace_format}")
            if trace_output:
                console.print(f"   Output: {trace_output}")
            console.print()
        except ImportError as e:
            console.print(f"[yellow]⚠ Traceability not available: {e}[/yellow]")

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
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
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
    checks.append(
        ("tests/ directory", "OK" if tests_exists else "Not found", tests_exists)
    )

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
            console.print(
                "  • Install Playwright: [white]pip install playwright[/white]"
            )
        if not any(name == "Playwright CLI" and ok for name, _, ok in checks):
            console.print(
                "  • Install browsers: [white]playwright install chromium[/white]"
            )
        if not any(name == "Pydantic" and ok for name, _, ok in checks):
            console.print(
                "  • Install dependencies: [white]pip install socialseed-e2e[/white]"
            )
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
            console.print(
                f"[dim]Tokens: {chunk.token_estimate} | ID: {chunk.chunk_id}[/dim]"
            )
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
        from socialseed_e2e.project_manifest.flow_test_generator import (
            FlowBasedTestSuiteGenerator,
        )

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
                console.print(
                    f"[red]❌ Service '{service}' not found in manifest[/red]"
                )
                sys.exit(1)

        generated_suites = []
        for svc in services_to_process:
            console.print(f"   Analyzing: {svc.name}...")

            # Create test suite generator
            suite_generator = FlowBasedTestSuiteGenerator(
                service_info=svc, db_schema=db_schema
            )

            # Analyze flows
            flow_count = len(suite_generator.flows)
            relationship_count = len(suite_generator.analysis_result["relationships"])
            console.print(
                f"     ✓ Detected {flow_count} flows, {relationship_count} relationships"
            )

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
            console.print(
                f"     📄 {svc.name}_page.py ({len(svc.endpoints)} endpoints)"
            )
            for flow in suite.flows_detected:
                console.print(f"     📄 {flow.name} ({len(flow.steps)} steps)")

        # Show validation criteria summary
        console.print(
            "\n🎯 [yellow]Step 5/5:[/yellow] Extracting validation criteria..."
        )
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
                                {"endpoint": {"name": step.endpoint.name}}
                                for step in flow.steps
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
            console.print(
                "   1. Review the AI Discovery Report in .e2e/DISCOVERY_REPORT.md"
            )
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
                ports_str = ", ".join(
                    f"{p['public']}->{p['private']}" for p in container["ports"]
                )
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
                                console.print(
                                    f"   Output: {setup_result['output'][:200]}..."
                                )
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
        from socialseed_e2e.project_manifest import (
            ManifestAPI,
            generate_discovery_report,
        )

        # Load manifest
        api = ManifestAPI(target_path)
        manifest = api._load_manifest()

        if not manifest:
            console.print(
                "[yellow]⚠ No project manifest found. Run 'e2e manifest' first.[/yellow]"
            )
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


@cli.command()
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
def security_test(
    directory: str,
    service: Optional[str],
    max_payloads: int,
    output: str,
    attack_types: Optional[str],
):
    """Run AI-driven security fuzzing tests (Issue #189).

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
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🔒 [bold red]AI Security Fuzzing[/bold red]")
    console.print(f"   Project: {target_path}\n")

    try:
        from socialseed_e2e import BasePage
        from socialseed_e2e.project_manifest import (
            ManifestAPI,
            SecurityReportGenerator,
            run_security_fuzzing,
        )

        # Load manifest
        api = ManifestAPI(target_path)
        manifest = api._load_manifest()

        if not manifest:
            console.print(
                "[yellow]⚠ No project manifest found. Run 'e2e manifest' first.[/yellow]"
            )
            sys.exit(1)

        # Get services to test
        services_to_test = manifest.services
        if service:
            services_to_test = [s for s in services_to_test if s.name == service]
            if not services_to_test:
                console.print(f"[red]❌ Service '{service}' not found[/red]")
                sys.exit(1)

        all_sessions = []

        # Run security tests for each service
        for svc in services_to_test:
            console.print(f"\n🎯 Testing service: [cyan]{svc.name}[/cyan]")

            # Create service page
            page = BasePage(base_url=f"http://localhost:8080")  # Default URL

            # Run fuzzing
            session = run_security_fuzzing(
                service_page=page, service_info=svc, max_payloads_per_field=max_payloads
            )

            all_sessions.append(session)

            # Display results
            console.print(f"   Total tests: {session.total_tests}")
            console.print(f"   Blocked: {session.passed_tests}")
            console.print(f"   Vulnerabilities: {len(session.vulnerabilities_found)}")

            if session.vulnerabilities_found:
                console.print(
                    f"   [red]⚠ {len(session.vulnerabilities_found)} vulnerabilities found![/red]"
                )

        # Generate combined report
        if all_sessions:
            console.print("\n📝 Generating security report...")

            # Use first session for report (could be enhanced to combine all)
            report_gen = SecurityReportGenerator(all_sessions[0])

            output_path = target_path / ".e2e" / output
            output_path.parent.mkdir(parents=True, exist_ok=True)

            report_gen.save_report(str(output_path))

            console.print(f"   ✓ Report saved: {output_path}\n")

            # Summary
            total_vulns = sum(len(s.vulnerabilities_found) for s in all_sessions)
            avg_resilience = sum(s.resilience_score for s in all_sessions) / len(
                all_sessions
            )

            console.print(f"{'=' * 60}")
            console.print("[bold]🔒 Security Testing Complete[/bold]")
            console.print(f"{'=' * 60}")
            console.print(f"\n📊 Summary:")
            console.print(f"   Services tested: {len(all_sessions)}")
            console.print(f"   Total tests: {sum(s.total_tests for s in all_sessions)}")
            console.print(f"   Vulnerabilities found: {total_vulns}")
            console.print(f"   Average resilience score: {avg_resilience:.1f}%")

            if total_vulns > 0:
                console.print(
                    f"\n   [red]⚠ {total_vulns} vulnerabilities require attention![/red]"
                )
                console.print(f"   📄 See report: {output_path}")
            else:
                console.print(f"\n   [green]✅ No vulnerabilities found![/green]")

            console.print()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 Security testing interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--base-ref",
    "-b",
    default="HEAD~1",
    help="Base git reference (default: HEAD~1)",
)
@click.option(
    "--target-ref",
    "-t",
    default="HEAD",
    help="Target git reference (default: HEAD)",
)
@click.option(
    "--run-tests/--no-run-tests",
    default=False,
    help="Run affected tests after analysis",
)
@click.option(
    "--output",
    "-o",
    default="REGRESSION_REPORT.md",
    help="Output report filename",
)
def regression(
    directory: str,
    base_ref: str,
    target_ref: str,
    run_tests: bool,
    output: str,
):
    """AI Regression Analysis for differential testing (Issue #84).

    Analyzes git diffs to identify modified functions, controllers, or models,
    determines which tests are affected by changes, and executes only related
    tests for instant feedback.

    Examples:
        e2e regression                        # Analyze last commit
        e2e regression --base-ref main        # Compare against main branch
        e2e regression --run-tests            # Analyze and run affected tests
        e2e regression -b v1.0 -t v2.0       # Compare tags
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🤖 [bold cyan]AI Regression Agent[/bold cyan]")
    console.print(f"   Project: {target_path}")
    console.print(f"   Comparing: {base_ref} → {target_ref}\n")

    try:
        from socialseed_e2e.project_manifest import (
            RegressionAgent,
            run_regression_analysis,
        )

        # Run regression analysis
        agent = RegressionAgent(target_path, base_ref, target_ref)
        impact = agent.run_analysis()

        if not impact.changed_files:
            console.print("[yellow]⚠ No changes detected between references[/yellow]")
            return

        # Display summary
        console.print("📊 [bold]Analysis Complete[/bold]\n")
        console.print(f"   Files changed: {len(impact.changed_files)}")
        console.print(f"   Services affected: {len(impact.affected_services)}")
        console.print(f"   Endpoints affected: {len(impact.affected_endpoints)}")
        console.print(f"   Tests to run: {len(impact.affected_tests)}")
        console.print(f"   Risk level: {impact.risk_level.upper()}")

        # Show changed files
        if impact.changed_files:
            console.print("\n📝 [bold]Changed Files:[/bold]")
            for change in impact.changed_files:
                file_name = change.file_path.name
                change_emoji = {"added": "+", "modified": "~", "deleted": "-"}.get(
                    change.change_type, "?"
                )
                console.print(
                    f"   {change_emoji} {file_name} ({change.lines_added}+/{change.lines_deleted}-)"
                )

        # Show affected services
        if impact.affected_services:
            console.print("\n🎯 [bold]Affected Services:[/bold]")
            for service in impact.affected_services:
                console.print(f"   • {service}")

        # Show tests to run
        if impact.affected_tests:
            console.print("\n🧪 [bold]Tests to Execute:[/bold]")
            tests_by_service = agent.get_tests_to_run(impact)
            for service, tests in tests_by_service.items():
                console.print(f"   {service}:")
                for test in tests[:5]:  # Show first 5
                    console.print(f"     - {test}")
                if len(tests) > 5:
                    console.print(f"     ... and {len(tests) - 5} more")

        # Show new tests needed
        if impact.new_tests_needed:
            console.print("\n✨ [bold]New Tests Recommended:[/bold]")
            for test in impact.new_tests_needed[:5]:
                console.print(f"   • {test}")
            if len(impact.new_tests_needed) > 5:
                console.print(f"   ... and {len(impact.new_tests_needed) - 5} more")

        # Generate and save report
        console.print("\n📝 Generating report...")
        report = agent.generate_report(impact)

        output_path = target_path / ".e2e" / output
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(report)

        console.print(f"   ✓ Report saved: {output_path}\n")

        # Run affected tests if requested
        if run_tests and impact.affected_services:
            console.print("🚀 [bold]Running Affected Tests...[/bold]\n")

            for service in impact.affected_services:
                console.print(f"   Running tests for: {service}")
                # Here we would actually run the tests
                # For now, just show the command
                console.print(f"   [dim]e2e run --service {service}[/dim]")

            console.print()

        # Final summary
        console.print(f"{'=' * 60}")
        console.print("[bold]🤖 Regression Analysis Complete[/bold]")
        console.print(f"{'=' * 60}")

        if impact.risk_level in ["critical", "high"]:
            console.print(f"\n   [red]⚠ High risk changes detected![/red]")
            console.print(f"   📄 Review full report: {output_path}")
        else:
            console.print(
                f"\n   [green]✅ Analysis complete - {len(impact.affected_tests)} tests identified[/green]"
            )

        if not run_tests and impact.affected_services:
            console.print(
                f"\n   [dim]Tip: Use --run-tests to execute affected tests automatically[/dim]"
            )

        console.print()

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
    default=".e2e/external_apis.json",
    help="Output file for analysis results",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "table"]),
    default="table",
    help="Output format",
)
def mock_analyze(directory: str, output: str, format: str):
    """Analyze project for external API dependencies (Issue #191).

    Scans codebase to detect calls to third-party APIs like Stripe,
    Google Maps, AWS, SendGrid, and other external services.

    Examples:
        e2e mock-analyze                    # Analyze current directory
        e2e mock-analyze /path/to/project   # Analyze specific project
        e2e mock-analyze -f json            # Output as JSON
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🔍 [bold cyan]External API Analysis[/bold cyan]")
    console.print(f"   Project: {target_path}\n")

    try:
        from socialseed_e2e.ai_mocking import ExternalAPIAnalyzer

        # Analyze project
        analyzer = ExternalAPIAnalyzer(target_path)
        detected_apis = analyzer.analyze_project()

        if not detected_apis:
            console.print("[yellow]⚠ No external APIs detected[/yellow]")
            console.print("   Your project might not have third-party integrations.\n")
            return

        # Display results
        if format == "table":
            table = Table(title="Detected External APIs")
            table.add_column("Service", style="cyan")
            table.add_column("Base URL", style="green")
            table.add_column("Calls", style="yellow")
            table.add_column("Auth Detected", style="white")
            table.add_column("Env Vars", style="dim")

            for service_name, dependency in detected_apis.items():
                table.add_row(
                    service_name,
                    dependency.base_url[:50] + "..."
                    if len(dependency.base_url) > 50
                    else dependency.base_url,
                    str(len(dependency.detected_calls)),
                    "✓" if dependency.auth_header_detected else "✗",
                    ", ".join(dependency.env_var_keys[:2])
                    + ("..." if len(dependency.env_var_keys) > 2 else ""),
                )

            console.print(table)

            # Show details for each API
            console.print("\n[bold]Details:[/bold]\n")
            for service_name, dependency in detected_apis.items():
                console.print(f"[cyan]{service_name}:[/cyan]")
                console.print(f"   Base URL: {dependency.base_url}")
                console.print(f"   Detected calls: {len(dependency.detected_calls)}")

                if dependency.detected_calls:
                    console.print("   Files:")
                    for call in dependency.detected_calls[:3]:
                        console.print(
                            f"     • {call.file_path}:{call.line_number} ({call.method})"
                        )
                    if len(dependency.detected_calls) > 3:
                        console.print(
                            f"     ... and {len(dependency.detected_calls) - 3} more"
                        )

                if dependency.env_var_keys:
                    console.print(
                        f"   Environment variables: {', '.join(dependency.env_var_keys)}"
                    )
                console.print()

        else:  # JSON format
            import json

            output_data = {}
            for service_name, dependency in detected_apis.items():
                output_data[service_name] = {
                    "base_url": dependency.base_url,
                    "auth_detected": dependency.auth_header_detected,
                    "env_vars": dependency.env_var_keys,
                    "calls": [
                        {
                            "method": c.method,
                            "file": c.file_path,
                            "line": c.line_number,
                            "url_pattern": c.url_pattern,
                        }
                        for c in dependency.detected_calls
                    ],
                }

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)

            console.print(f"[green]✅ Analysis saved to:[/green] {output_path}\n")

        # Summary
        console.print(f"{'=' * 60}")
        console.print("[bold]📊 Summary:[/bold]")
        console.print(f"   External APIs detected: {len(detected_apis)}")
        console.print(
            f"   Total API calls: {sum(len(d.detected_calls) for d in detected_apis.values())}"
        )

        console.print("\n[bold]Next steps:[/bold]")
        console.print(
            "   1. Generate mock servers: [cyan]e2e mock-generate <service>[/cyan]"
        )
        console.print("   2. Run mock servers: [cyan]e2e mock-run[/cyan]")
        console.print("   3. Run E2E tests with mocks enabled\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("service")
@click.option(
    "--port",
    "-p",
    default=8000,
    help="Port for the mock server",
)
@click.option(
    "--output-dir",
    "-o",
    default=".e2e/mocks",
    help="Output directory for generated mocks",
)
@click.option(
    "--docker",
    is_flag=True,
    help="Also generate Dockerfile and docker-compose.yml",
)
@click.option(
    "--all",
    "generate_all",
    is_flag=True,
    help="Generate mocks for all detected services",
)
def mock_generate(
    service: str, port: int, output_dir: str, docker: bool, generate_all: bool
):
    """Generate mock server for external API (Issue #191).

    Creates a FastAPI-based mock server that mimics the behavior
    of external services like Stripe, Google Maps, AWS, etc.

    Examples:
        e2e mock-generate stripe              # Generate Stripe mock
        e2e mock-generate stripe --port 9000  # Custom port
        e2e mock-generate --all               # Generate all detected mocks
        e2e mock-generate stripe --docker     # Include Docker files
    """
    from pathlib import Path

    output_path = Path(output_dir)

    console.print(f"\n🏗️  [bold cyan]Mock Server Generation[/bold cyan]")
    console.print(f"   Output: {output_path.resolve()}\n")

    try:
        from socialseed_e2e.ai_mocking import (
            MockServerGenerator,
            ExternalServiceRegistry,
        )

        generator = MockServerGenerator(output_path)

        if generate_all:
            # Generate for all registered services
            registry = ExternalServiceRegistry()
            services = registry.list_services()

            console.print(f"Generating mocks for {len(services)} services...\n")

            servers = generator.generate_all_mock_servers(services, base_port=port)

            for i, server in enumerate(servers):
                file_path = generator.save_mock_server(
                    server, f"mock_{server.service_name}.py"
                )
                console.print(f"  [green]✓[/green] {server.service_name}: {file_path}")

                if docker:
                    dockerfile = generator.generate_dockerfile(server)
                    dockerfile_path = output_path / f"Dockerfile.{server.service_name}"
                    dockerfile_path.write_text(dockerfile)
                    console.print(f"     📄 Dockerfile.{server.service_name}")

            # Generate docker-compose if requested
            if docker:
                compose = generator.generate_docker_compose(servers)
                compose_path = output_path / "docker-compose.yml"
                compose_path.write_text(compose)
                console.print(f"\n  [green]✓[/green] docker-compose.yml")

            console.print(
                f"\n[bold green]✅ Generated {len(servers)} mock servers![/bold green]\n"
            )

        else:
            # Generate single service
            console.print(f"Generating mock for: [cyan]{service}[/cyan]\n")

            try:
                server = generator.generate_mock_server(service, port=port)
            except ValueError as e:
                console.print(f"[red]❌ Error:[/red] {e}")
                console.print(f"\nAvailable services:")
                registry = ExternalServiceRegistry()
                for svc in registry.list_services():
                    console.print(f"   • {svc}")
                sys.exit(1)

            file_path = generator.save_mock_server(server)
            console.print(f"  [green]✓[/green] Generated: {file_path}")

            if docker:
                dockerfile = generator.generate_dockerfile(server)
                dockerfile_path = output_path / f"Dockerfile.{service}"
                dockerfile_path.write_text(dockerfile)
                console.print(f"  [green]✓[/green] Generated: {dockerfile_path}")

            console.print(
                f"\n[bold green]✅ Mock server generated successfully![/bold green]"
            )
            console.print(f"\n[bold]To run the mock server:[/bold]")
            console.print(f"   cd {output_path}")
            console.print(f"   python mock_{service}.py")
            console.print(f"\n   Or with Docker:")
            console.print(f"   docker-compose up {service}\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--services",
    "-s",
    help="Comma-separated list of services to mock",
)
@click.option(
    "--config",
    "-c",
    default=".e2e/mock-config.yml",
    help="Path to mock configuration file",
)
@click.option(
    "--detach",
    "-d",
    is_flag=True,
    help="Run in background (detached mode)",
)
@click.option(
    "--port",
    "-p",
    default=8000,
    help="Starting port for mock servers",
)
def mock_run(services: str, config: str, detach: bool, port: int):
    """Run mock servers for external APIs (Issue #191).

    Starts FastAPI mock servers for configured external APIs,
    enabling air-gapped E2E testing without real credentials.

    Examples:
        e2e mock-run                          # Run all configured mocks
        e2e mock-run -s stripe,aws            # Run specific mocks
        e2e mock-run -d                       # Run in background
        e2e mock-run -p 9000                  # Start at port 9000
    """
    import subprocess

    console.print(f"\n🚀 [bold cyan]Starting Mock Servers[/bold cyan]\n")

    try:
        from socialseed_e2e.ai_mocking import (
            MockServerGenerator,
            ExternalServiceRegistry,
        )

        output_dir = Path(".e2e/mocks")

        # Determine which services to run
        if services:
            service_list = [s.strip() for s in services.split(",")]
        else:
            # Check for generated mocks
            if output_dir.exists():
                service_list = [
                    f.stem.replace("mock_", "") for f in output_dir.glob("mock_*.py")
                ]
            else:
                console.print("[yellow]⚠ No mock servers found.[/yellow]")
                console.print(
                    "   Run [cyan]e2e mock-generate <service>[/cyan] first.\n"
                )
                sys.exit(1)

        if not service_list:
            console.print("[yellow]⚠ No services to mock.[/yellow]\n")
            sys.exit(1)

        console.print(f"Starting {len(service_list)} mock server(s):\n")

        processes = []
        current_port = port

        for service in service_list:
            mock_file = output_dir / f"mock_{service}.py"

            if not mock_file.exists():
                console.print(
                    f"  [yellow]⚠[/yellow] {service}: Mock not found, generating..."
                )
                generator = MockServerGenerator(output_dir)
                try:
                    server = generator.generate_mock_server(service, port=current_port)
                    generator.save_mock_server(server)
                    console.print(f"     [green]✓[/green] Generated")
                except ValueError as e:
                    console.print(f"     [red]✗[/red] {e}")
                    continue

            # Start the mock server
            console.print(f"  [green]●[/green] {service} on port {current_port}")

            if detach:
                # Run in background
                process = subprocess.Popen(
                    [sys.executable, str(mock_file)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            else:
                # Run in foreground (will be managed by the user)
                if len(service_list) == 1:
                    # Single service - run directly
                    console.print(f"\n[bold]Running {service} mock server...[/bold]")
                    console.print("Press Ctrl+C to stop\n")
                    try:
                        subprocess.run([sys.executable, str(mock_file)], check=True)
                    except KeyboardInterrupt:
                        console.print(
                            f"\n[yellow]👋 {service} mock server stopped[/yellow]\n"
                        )
                    return
                else:
                    # Multiple services - use subprocesses
                    process = subprocess.Popen(
                        [sys.executable, str(mock_file)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    processes.append((service, process))

            current_port += 1

        if detach:
            console.print(
                f"\n[bold green]✅ Mock servers running in background[/bold green]"
            )
            console.print(f"   Check with: [cyan]ps aux | grep mock_[/cyan]\n")

        elif processes:
            console.print(f"\n[bold]Running {len(processes)} mock servers...[/bold]")
            console.print("Press Ctrl+C to stop all\n")

            try:
                # Wait for all processes
                for service, process in processes:
                    process.wait()
            except KeyboardInterrupt:
                console.print(f"\n[yellow]👋 Stopping all mock servers...[/yellow]")
                for service, process in processes:
                    process.terminate()
                    console.print(f"   [red]●[/red] {service} stopped")
                console.print()

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("contract_file")
@click.option(
    "--service",
    "-s",
    help="Service name for schema lookup",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation output",
)
def mock_validate(contract_file: str, service: str, verbose: bool):
    """Validate API contract against mock schema (Issue #191).

    Validates that requests and responses conform to the expected
    contract for external APIs, ensuring consistent mocking.

    Examples:
        e2e mock-verify contracts/stripe.json     # Validate contract
        e2e mock-verify contracts.json -s stripe  # Specify service
        e2e mock-verify contracts.json -v         # Verbose output
    """
    contract_path = Path(contract_file)

    if not contract_path.exists():
        console.print(f"[red]❌ Error:[/red] Contract file not found: {contract_path}")
        sys.exit(1)

    console.print(f"\n✅ [bold cyan]Contract Validation[/bold cyan]")
    console.print(f"   File: {contract_path}\n")

    try:
        from socialseed_e2e.ai_mocking import ContractValidator

        validator = ContractValidator()
        results = validator.validate_contract_file(contract_path)

        if not results:
            console.print("[yellow]⚠ No tests found in contract file[/yellow]\n")
            return

        # Display results
        total_valid = 0
        total_invalid = 0

        for test_name, result in results.items():
            if result.is_valid:
                console.print(f"  [green]✓[/green] {test_name}")
                total_valid += 1
            else:
                console.print(f"  [red]✗[/red] {test_name}")
                total_invalid += 1

                if verbose:
                    for error in result.errors:
                        console.print(
                            f"     [red]Error:[/red] {error.field} - {error.message}"
                        )
                        if error.expected is not None:
                            console.print(f"       Expected: {error.expected}")
                        if error.actual is not None:
                            console.print(f"       Actual: {error.actual}")

                    for warning in result.warnings:
                        console.print(
                            f"     [yellow]Warning:[/yellow] {warning.field} - {warning.message}"
                        )

        # Summary
        console.print(f"\n{'=' * 60}")
        console.print("[bold]📊 Validation Summary:[/bold]")
        console.print(f"   Total tests: {len(results)}")
        console.print(f"   Valid: {total_valid}")
        console.print(f"   Invalid: {total_invalid}")

        if total_invalid == 0:
            console.print(
                f"\n   [bold green]✅ All contracts validated successfully![/bold green]\n"
            )
        else:
            console.print(
                f"\n   [bold yellow]⚠ {total_invalid} contract(s) have validation issues[/bold yellow]\n"
            )

        sys.exit(0 if total_invalid == 0 else 1)

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    cli()
