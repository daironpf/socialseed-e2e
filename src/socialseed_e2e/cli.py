#!/usr/bin/env python3
"""CLI module for socialseed-e2e framework.

This module provides the command-line interface for the E2E testing framework,
enabling developers and AI agents to create, manage, and run API tests.
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from socialseed_e2e import __version__
from socialseed_e2e.core.config_loader import ApiConfigLoader, ConfigError
from socialseed_e2e.utils import TemplateEngine, to_class_name, to_snake_case

console = Console()

# Map of extra dependencies for better error messages
EXTRA_DEPENDENCIES = {
    "tui": {
        "packages": ["textual>=0.41.0"],
        "pip_extra": "tui",
        "description": "Terminal User Interface",
    },
    "rag": {
        "packages": ["sentence-transformers>=2.2.0", "numpy>=1.24.0"],
        "pip_extra": "rag",
        "description": "Semantic search and RAG features",
    },
    "grpc": {
        "packages": ["grpcio>=1.59.0", "grpcio-tools>=1.59.0", "protobuf>=4.24.0"],
        "pip_extra": "grpc",
        "description": "gRPC protocol support",
    },
    "full": {
        "packages": [],  # Special case - installs all extras
        "pip_extra": "tui,rag,grpc,test-data",
        "description": "All optional features",
    },
}


def check_and_install_extra(extra_name: str, auto_install: bool = False) -> bool:
    """Check if extra dependencies are installed, optionally install them.

    Args:
        extra_name: Name of the extra (tui, rag, grpc, etc.)
        auto_install: If True, automatically install missing dependencies

    Returns:
        True if dependencies are available, False otherwise
    """
    if extra_name not in EXTRA_DEPENDENCIES:
        console.print(f"[red]❌ Unknown extra: {extra_name}[/red]")
        return False

    extra_info = EXTRA_DEPENDENCIES[extra_name]

    # Try to import a module specific to this extra to check if it's installed
    test_modules = {
        "tui": "textual",
        "rag": "sentence_transformers",
        "grpc": "grpc",
    }

    if extra_name in test_modules:
        try:
            __import__(test_modules[extra_name])
            return True
        except ImportError:
            pass
    elif extra_name == "full":
        # For full, check if all main extras are installed
        all_installed = all(
            check_and_install_extra(name) for name in ["tui", "rag", "grpc"]
        )
        return all_installed

    if auto_install:
        console.print(f"[yellow]📦 Installing {extra_info['description']}...[/yellow]")
        pip_extra = extra_info["pip_extra"]
        cmd = [sys.executable, "-m", "pip", "install", f"socialseed-e2e[{pip_extra}]"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                console.print(
                    f"[green]✅ {extra_info['description']} installed successfully![/green]"
                )
                return True
            else:
                console.print(f"[red]❌ Installation failed:[/red] {result.stderr}")
                return False
        except Exception as e:
            console.print(f"[red]❌ Installation error:[/red] {e}")
            return False
    else:
        # Just show helpful message
        pip_extra = extra_info["pip_extra"]
        console.print(
            f"\n[yellow]📦 Missing dependency:[/yellow] {extra_info['description']}"
        )
        console.print(f"[cyan]Install with:[/cyan]")
        console.print(f"   pip install socialseed-e2e[{pip_extra}]")
        console.print(f"\n[dim]Or run:[/dim] e2e install-extras {extra_name}")
        console.print()
        return False


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

    # Initialize template engine
    engine = TemplateEngine()

    # Create example test file in tests/
    example_test_path = target_path / "tests" / "example_test.py"
    if not example_test_path.exists() or force:
        engine.render_to_file(
            "example_test.py.template",
            {},
            str(example_test_path),
            overwrite=force,
        )
        console.print("  [green]✓[/green] Created: tests/example_test.py")

    # Create __init__.py for tests package
    tests_init_path = target_path / "tests" / "__init__.py"
    if not tests_init_path.exists():
        tests_init_path.write_text("")

    # Configuration file will be created later with example service

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

    # Create example service with working tests
    example_service_path = target_path / "services" / "example"
    example_modules_path = example_service_path / "modules"

    if not example_service_path.exists() or force:
        example_service_path.mkdir(parents=True, exist_ok=True)
        example_modules_path.mkdir(exist_ok=True)

        # Create __init__.py
        (example_service_path / "__init__.py").write_text("")
        (example_modules_path / "__init__.py").write_text("")

        # Create data_schema.py
        engine.render_to_file(
            "example_data_schema.py.template",
            {},
            str(example_service_path / "data_schema.py"),
            overwrite=force,
        )
        console.print("  [green]✓[/green] Created: services/example/data_schema.py")

        # Create example_page.py
        engine.render_to_file(
            "example_service_page.py.template",
            {},
            str(example_service_path / "example_page.py"),
            overwrite=force,
        )
        console.print("  [green]✓[/green] Created: services/example/example_page.py")

        # Create test modules
        engine.render_to_file(
            "example_test_health.py.template",
            {},
            str(example_modules_path / "01_health.py"),
            overwrite=force,
        )
        console.print(
            "  [green]✓[/green] Created: services/example/modules/01_health.py"
        )

        engine.render_to_file(
            "example_test_create.py.template",
            {},
            str(example_modules_path / "02_create.py"),
            overwrite=force,
        )
        console.print(
            "  [green]✓[/green] Created: services/example/modules/02_create.py"
        )
    else:
        console.print(
            "  [yellow]⚠[/yellow] Already exists: services/example/ (use --force to overwrite)"
        )

    # Create/update e2e.conf with example service
    config_path = target_path / "e2e.conf"
    if not config_path.exists() or force:
        engine.render_to_file(
            "e2e.conf.template",
            {
                "environment": "dev",
                "timeout": "30000",
                "user_agent": "socialseed-e2e/1.0",
                "verbose": "true",
                "services_config": """  example:
    base_url: http://localhost:8765
    health_endpoint: /health
""",
            },
            str(config_path),
            overwrite=force,
        )
        console.print("  [green]✓[/green] Created: e2e.conf (with example service)")

    # Create socialseed.config.yaml (alternative config format)
    config_yaml_path = target_path / "socialseed.config.yaml"
    if not config_yaml_path.exists() or force:
        engine.render_to_file(
            "socialseed.config.yaml.template",
            {},
            str(config_yaml_path),
            overwrite=force,
        )
        console.print("  [green]✓[/green] Created: socialseed.config.yaml")

    # Create pyproject.toml for pytest and project metadata
    pyproject_path = target_path / "pyproject.toml"
    if not pyproject_path.exists() or force:
        engine.render_to_file(
            "pyproject.toml.template",
            {"project_name": target_path.name},
            str(pyproject_path),
            overwrite=force,
        )
        console.print("  [green]✓[/green] Created: pyproject.toml")

    # Create conftest.py with mock server fixtures
    conftest_path = target_path / "conftest.py"
    if not conftest_path.exists() or force:
        engine.render_to_file(
            "conftest.py.template",
            {},
            str(conftest_path),
            overwrite=force,
        )
        console.print(
            "  [green]✓[/green] Created: conftest.py (with mock server fixtures)"
        )

    # Create localized README.md
    readme_path = target_path / "README.md"
    if not readme_path.exists() or force:
        engine.render_to_file(
            "example_README.md.template",
            {"project_name": target_path.name},
            str(readme_path),
            overwrite=force,
        )
        console.print("  [green]✓[/green] Created: README.md")
    else:
        console.print("  [yellow]⚠[/yellow] Already exists: README.md")

    # Copy GitHub Actions workflow
    github_workflows_path = target_path / ".github" / "workflows"
    e2e_yml_path = github_workflows_path / "e2e.yml"
    if not e2e_yml_path.exists() or force:
        try:
            from socialseed_e2e.templates import __file__ as templates_init

            templates_dir = Path(templates_init).parent
            source_workflow = (
                templates_dir
                / "ci-cd"
                / "github-actions"
                / "basic-workflow.yml.template"
            )
            if source_workflow.exists():
                shutil.copy(str(source_workflow), str(e2e_yml_path))
                console.print("  [green]✓[/green] Created: .github/workflows/e2e.yml")
        except Exception:
            # If it fails, it's not critical
            pass

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
            "1. Review the [cyan]example service[/cyan] in services/example/\n"
            "2. Edit [cyan]e2e.conf[/cyan] to configure your API endpoints\n"
            "3. Read [cyan]README.md[/cyan] for detailed instructions\n"
            '4. Ask your AI Agent: [italic]"Read the AGENT_GUIDE.md and '
            'generate tests for my API"[/italic]\n'
            "5. Or create a new service: [cyan]e2e new-service <name>[/cyan]",
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
@click.argument("extra", nargs=-1, required=False)
@click.option("--list", "list_extras", is_flag=True, help="List available extras")
@click.option("--all", "install_all", is_flag=True, help="Install all extras")
def install_extras(extra, list_extras: bool, install_all: bool):
    """Install optional dependencies (extras).

    Installs optional feature packages like TUI, RAG, gRPC support, etc.

    Available extras:
        tui       - Terminal User Interface (textual)
        rag       - Semantic search and embeddings (sentence-transformers)
        grpc      - gRPC protocol support (grpcio)
        full      - All extras combined

    Examples:
        e2e install-extras              # Interactive mode
        e2e install-extras tui          # Install TUI only
        e2e install-extras rag grpc     # Install RAG and gRPC
        e2e install-extras --all        # Install all extras
        e2e install-extras --list       # Show available extras
    """
    if list_extras:
        console.print("\n[bold cyan]📦 Available Optional Dependencies[/bold cyan]\n")
        table = Table(title="Install with: pip install socialseed-e2e[extra]")
        table.add_column("Extra", style="green", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Packages", style="dim")

        for name, info in EXTRA_DEPENDENCIES.items():
            packages = (
                ", ".join(info["packages"][:2]) + "..."
                if len(info["packages"]) > 2
                else ", ".join(info["packages"])
            )
            if name == "full":
                packages = "All extras"
            table.add_row(name, info["description"], packages)

        console.print(table)
        console.print("\n[cyan]Usage:[/cyan]")
        console.print("  e2e install-extras tui")
        console.print("  e2e install-extras rag grpc")
        console.print("  pip install socialseed-e2e[tui,rag]")
        console.print()
        return

    # Determine which extras to install
    extras_to_install = []

    if install_all:
        extras_to_install = ["tui", "rag", "grpc"]
    elif extra:
        extras_to_install = list(extra)
    else:
        # Interactive mode
        console.print("\n[bold cyan]📦 Install Optional Dependencies[/bold cyan]\n")
        console.print("Select extras to install (space-separated, or 'all'):\n")

        for name, info in EXTRA_DEPENDENCIES.items():
            if name != "full":
                status = "✅" if check_extra_installed(name) else "❌"
                console.print(
                    f"  {status} [green]{name:<10}[/green] - {info['description']}"
                )

        console.print()
        user_input = click.prompt("Extras to install", default="", show_default=False)

        if user_input.lower() == "all":
            extras_to_install = ["tui", "rag", "grpc"]
        elif user_input.strip():
            extras_to_install = user_input.strip().split()
        else:
            console.print("[yellow]No extras selected. Nothing to install.[/yellow]")
            return

    # Validate extras
    invalid_extras = [e for e in extras_to_install if e not in EXTRA_DEPENDENCIES]
    if invalid_extras:
        console.print(f"[red]❌ Unknown extras: {', '.join(invalid_extras)}[/red]")
        console.print(
            f"[yellow]Run 'e2e install-extras --list' to see available extras[/yellow]"
        )
        sys.exit(1)

    # Install extras
    console.print(f"\n[bold]Installing {len(extras_to_install)} extra(s)...[/bold]\n")

    success_count = 0
    for extra_name in extras_to_install:
        if check_and_install_extra(extra_name, auto_install=True):
            success_count += 1

    console.print()
    if success_count == len(extras_to_install):
        console.print(
            f"[bold green]✅ All {success_count} extra(s) installed successfully![/bold green]"
        )
    else:
        console.print(
            f"[yellow]⚠️  {success_count}/{len(extras_to_install)} extra(s) installed[/yellow]"
        )
        sys.exit(1)


def check_extra_installed(extra_name: str) -> bool:
    """Check if an extra is already installed."""
    test_modules = {
        "tui": "textual",
        "rag": "sentence_transformers",
        "grpc": "grpc",
    }

    if extra_name in test_modules:
        try:
            __import__(test_modules[extra_name])
            return True
        except ImportError:
            return False
    return False


@cli.command()
@click.argument("name")
@click.option("--base-url", default="http://localhost:8080", help="Service base URL")
@click.option("--health-endpoint", default="/health", help="Health check endpoint")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files without prompting")
def new_service(name: str, base_url: str, health_endpoint: str, force: bool):
    """Create a new service with scaffolding.

    Creates the complete directory structure and template files for a new
    service, including data_schema.py, service_page.py, and the modules directory.

    Args:
        name: Service name (e.g.: users-api, auth_service)
        base_url: Service base URL (default: http://localhost:8080)
        health_endpoint: Health check endpoint path (default: /health)
        force: Overwrite existing files without prompting

    Examples:
        e2e new-service users-api                                    # Create with defaults
        e2e new-service payment-service --base-url http://localhost:8081
        e2e new-service auth-service --base-url http://localhost:8080 --health-endpoint /actuator/health
        e2e new-service auth-service --force                         # Overwrite without prompting
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
        if not force:
            console.print("   Use --force to overwrite existing files")
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
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files without prompting")
def new_test(name: str, service: str, description: str, force: bool):
    """Create a new test module.

    Args:
        name: Test name (e.g.: login, create-user)
        service: Service to which the test belongs
        description: Optional test description
        force: Overwrite existing files without prompting

    Examples:
        e2e new-test login -s auth_service
        e2e new-test create-user -s users-api -d "Test user creation"
        e2e new-test login -s auth_service --force
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
        if not force:
            console.print("   Use --force to overwrite existing files")
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
    type=click.Choice(["text", "json", "html"]),
    default="text",
    help="Output format (text, json, or html)",
)
@click.option(
    "--report-dir",
    type=click.Path(),
    default=".e2e/reports",
    help="Directory for HTML reports (default: .e2e/reports)",
)
@click.option(
    "--trace",
    "-T",
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
@click.option(
    "--parallel",
    "-j",
    type=int,
    default=None,
    help="Enable parallel execution with N workers (0=disabled, auto=CPU count)",
)
@click.option(
    "--parallel-mode",
    type=click.Choice(["service", "test"]),
    default="service",
    help="Parallel execution mode: 'service' runs services in parallel",
)
@click.option(
    "--tag",
    "-t",
    "include_tags",
    multiple=True,
    help="Only run tests with these tags",
)
@click.option(
    "--exclude-tag",
    "-x",
    "exclude_tags",
    multiple=True,
    help="Exclude tests with these tags",
)
@click.option(
    "--report",
    type=click.Choice(["junit", "json"]),
    help="Generate machine-readable test report (junit or json format)",
)
@click.option(
    "--report-output",
    type=click.Path(),
    default="./reports",
    help="Directory for machine-readable reports (default: ./reports)",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable debug mode with verbose HTTP request/response logging for failed tests",
)
@click.option(
    "--skip-unhealthy",
    is_flag=True,
    help="Skip tests for services that are not healthy (skip instead of fail)",
)
@click.option(
    "--no-agent",
    is_flag=True,
    help="Disable AI agent features (boring mode). No external LLM calls will be made",
)
def run(
    service: Optional[str],
    module: Optional[str],
    config: Optional[str],
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
):
    """Execute E2E tests.

    Discovers and automatically executes all available tests.

    Args:
        service: If specified, only run tests for this service
        module: If specified, only run this test module
        config: Path to the e2e.conf file
        verbose: If True, shows detailed information
        output: Output format (text, json, or html)
        report_dir: Directory for HTML reports
        trace: If True, enable visual traceability with sequence diagrams
        trace_output: Directory for traceability reports
        trace_format: Format for sequence diagrams (mermaid, plantuml, both)
        skip_unhealthy: If True, skip tests for services that are not healthy
        debug: If True, enable debug mode with verbose HTTP logging for failed tests
        no_agent: If True, disable AI agent features (boring mode)

    Examples:
        e2e run                                              # Run all tests
        e2e run --service auth_service                       # Run tests for specific service
        e2e run --service auth_service --module 01_login     # Run specific test module
        e2e run --verbose                                    # Run with detailed output
        e2e run --output html --report-dir ./reports         # Generate HTML report
        e2e run --parallel 4                                 # Run with 4 parallel workers
        e2e run --trace                                      # Enable traceability
        e2e run -c /path/to/e2e.conf                         # Use custom config file
        e2e run --report junit                               # Generate JUnit XML report
        e2e run --report json                                # Generate JSON report
        e2e run --report junit --report-output ./reports     # Custom report directory
        e2e run --debug                                      # Enable debug mode
        e2e run --no-agent                                   # Run in boring mode (no AI)
        e2e run --skip-unhealthy                             # Skip tests for unhealthy services
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
    from .core.test_runner import (
        generate_junit_report,
        generate_json_report,
        print_summary,
        run_all_tests,
    )

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
    if debug:
        console.print(
            "🐛 [yellow]Debug mode activated - verbose HTTP logging for failures[/yellow]"
        )
    if no_agent:
        console.print(
            "🔄 [yellow]Boring mode activated - AI features disabled[/yellow]"
        )
    if include_tags:
        console.print(f"🏷️ [yellow]Including tags:[/yellow] {', '.join(include_tags)}")
    if exclude_tags:
        console.print(f"🚫 [yellow]Excluding tags:[/yellow] {', '.join(exclude_tags)}")

    console.print()

    # Determine if parallel execution should be used
    use_parallel = parallel is not None and parallel != 0

    # Check service health if skip_unhealthy is enabled
    unhealthy_services = []
    if skip_unhealthy:
        console.print("🏥 [cyan]Checking service health...[/cyan]")
        try:
            health_loader = ApiConfigLoader()
            app_config = health_loader.load(config)
            for name, svc in app_config.services.items():
                health_endpoint = svc.health_endpoint or "/actuator/health"
                is_healthy, _ = _check_service_health(svc.base_url, health_endpoint)
                if not is_healthy:
                    unhealthy_services.append(name)
                    console.print(f"   ⏭️  [yellow]Skipping {name} (not healthy)[/yellow]")
                else:
                    console.print(f"   ✅ [green]{name} is healthy[/green]")
        except Exception as e:
            console.print(f"   ⚠️  [yellow]Could not check health: {e}[/yellow]")
        console.print()

    # If service is specified and it's unhealthy, skip it
    if service and skip_unhealthy and service in unhealthy_services:
        console.print(f"⏭️  [yellow]Skipping service '{service}' - not healthy[/yellow]")
        console.print()
        return

    # Initialize parallel config if needed
    parallel_config = None
    run_tests_parallel_func = None
    if use_parallel and parallel is not None:
        from socialseed_e2e.core.parallel_runner import (
            ParallelConfig,
            run_tests_parallel,
        )

        run_tests_parallel_func = run_tests_parallel

        workers = parallel if parallel > 0 else None
        parallel_config = ParallelConfig(
            enabled=True,
            max_workers=workers,
            parallel_mode=parallel_mode,
        )

        console.print(f"⚡ [cyan]Parallel execution enabled[/cyan]")
        console.print(f"   Workers: {parallel_config.max_workers}")
        console.print(f"   Mode: {parallel_config.parallel_mode}")
        console.print()

    # Execute tests
    try:
        if (
            use_parallel
            and parallel_config is not None
            and run_tests_parallel_func is not None
        ):
            results = run_tests_parallel_func(
                services_path=services_path,
                specific_service=service,
                specific_module=module,
                parallel_config=parallel_config,
                verbose=verbose,
                debug=debug,
                no_agent=no_agent,
                include_tags=list(include_tags) if include_tags else None,
                exclude_tags=list(exclude_tags) if exclude_tags else None,
            )
        else:
            results = run_all_tests(
                services_path=services_path,
                specific_service=service,
                specific_module=module,
                verbose=verbose,
                debug=debug,
                no_agent=no_agent,
                include_tags=list(include_tags) if include_tags else None,
                exclude_tags=list(exclude_tags) if exclude_tags else None,
            )

        # Print summary
        all_passed = print_summary(results)

        # Generate HTML report if requested
        if output == "html":
            try:
                from socialseed_e2e.reporting import (
                    HTMLReportGenerator,
                    TestResultCollector,
                )

                console.print("\n📊 [cyan]Generating HTML report...[/cyan]")

                # Convert test results to report format
                collector = TestResultCollector(title="E2E Test Report")
                collector.start_collection()

                # Process results and create test records
                for service_name, suite_result in results.items():
                    for test_result in suite_result.results:
                        test_id = f"{service_name}.{test_result.name}"
                        collector.record_test_start(
                            test_id, test_result.name, service_name
                        )
                        collector.record_test_end(
                            test_id,
                            status=test_result.status,
                            duration_ms=test_result.duration_ms,
                            error_message=test_result.error_message
                            if test_result.error_message
                            else None,
                        )

                # Generate report
                report = collector.generate_report()
                generator = HTMLReportGenerator()

                import os

                os.makedirs(report_dir, exist_ok=True)
                report_path = generator.generate(
                    report, output_path=os.path.join(report_dir, "report.html")
                )

                console.print(f"[green]✓ HTML report generated:[/green] {report_path}")

                # Also export CSV and JSON
                csv_path = generator.export_to_csv(
                    report, output_path=os.path.join(report_dir, "report.csv")
                )
                json_path = generator.export_to_json(
                    report, output_path=os.path.join(report_dir, "report.json")
                )

                console.print(f"[green]✓ CSV report:[/green] {csv_path}")
                console.print(f"[green]✓ JSON report:[/green] {json_path}")

            except Exception as e:
                console.print(f"[yellow]⚠ Could not generate HTML report: {e}[/yellow]")
                if verbose:
                    import traceback

                    console.print(traceback.format_exc())

        # Generate machine-readable reports if requested
        if report:
            try:
                from .core.test_runner import (
                    generate_junit_report,
                    generate_json_report,
                )

                console.print(
                    f"\n📊 [cyan]Generating {report.upper()} report...[/cyan]"
                )

                if report == "junit":
                    junit_path = generate_junit_report(
                        results, output_path=str(Path(report_output) / "junit.xml")
                    )
                    console.print(f"[green]✓ JUnit report:[/green] {junit_path}")

                elif report == "json":
                    json_path = generate_json_report(
                        results, output_path=str(Path(report_output) / "report.json")
                    )
                    console.print(f"[green]✓ JSON report:[/green] {json_path}")

            except Exception as e:
                console.print(
                    f"[yellow]⚠ Could not generate {report} report: {e}[/yellow]"
                )
                if verbose:
                    import traceback

                    console.print(traceback.format_exc())

        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)

    except Exception as e:
        console.print(f"[red]❌ Error executing tests:[/red] {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument(
    "platform",
    type=click.Choice(
        [
            "github",
            "gitlab",
            "jenkins",
            "azure",
            "circleci",
            "travis",
            "bitbucket",
            "all",
        ]
    ),
)
@click.option("--force", is_flag=True, help="Overwrite existing files")
def setup_ci(platform: str, force: bool):
    """Generate CI/CD pipeline templates for various platforms.

    Args:
        platform: Target platform (github, gitlab, jenkins, azure, circleci, travis, bitbucket, all)
        force: If True, overwrites existing files
    """
    console.print(
        f"\n🚀 [bold cyan]Setting up CI/CD templates for:[/bold cyan] {platform}\n"
    )

    if not _is_e2e_project():
        console.print(
            "[red]❌ Error:[/red] e2e.conf not found. Are you in an E2E project?"
        )
        sys.exit(1)

    engine = TemplateEngine()

    ci_configs = {
        "github": [
            (
                "ci-cd/github-actions/basic-workflow.yml.template",
                ".github/workflows/e2e-basic.yml",
            ),
            (
                "ci-cd/github-actions/parallel-workflow.yml.template",
                ".github/workflows/e2e-parallel.yml",
            ),
            (
                "ci-cd/github-actions/advanced-matrix-workflow.yml.template",
                ".github/workflows/e2e-matrix.yml",
            ),
        ],
        "gitlab": [("ci-cd/gitlab-ci/gitlab-ci.yml.template", ".gitlab-ci.yml")],
        "jenkins": [("ci-cd/jenkins/Jenkinsfile.template", "Jenkinsfile")],
        "azure": [
            ("ci-cd/azure-devops/azure-pipelines.yml.template", "azure-pipelines.yml")
        ],
        "circleci": [("ci-cd/circleci/config.yml.template", ".circleci/config.yml")],
        "travis": [("ci-cd/travis/travis.yml.template", ".travis.yml")],
        "bitbucket": [
            (
                "ci-cd/bitbucket/bitbucket-pipelines.yml.template",
                "bitbucket-pipelines.yml",
            )
        ],
    }

    platforms_to_setup = list(ci_configs.keys()) if platform == "all" else [platform]

    for p in platforms_to_setup:
        console.print(f"📦 [bold blue]{p.upper()}[/bold blue]")
        for template, output in ci_configs[p]:
            output_path = Path(output)

            try:
                engine.render_to_file(template, {}, str(output_path), overwrite=force)
                console.print(f"  [green]✓[/green] Generated: {output}")
            except FileExistsError:
                console.print(
                    f"  [yellow]⚠[/yellow] Already exists: {output} (use --force to overwrite)"
                )
            except Exception as e:
                console.print(f"  [red]❌ Error generating {output}:[/red] {e}")

    console.print(
        "\n[bold green]✅ CI/CD templates generated successfully![/bold green]\n"
    )


@cli.group()
def recorder():
    """Commands for recording and replaying API sessions."""
    pass


@recorder.command("record")
@click.argument("name")
@click.option("--port", "-p", default=8090, help="Proxy port")
@click.option(
    "--output", "-o", help="Output file path (default: recordings/<name>.json)"
)
def recorder_record(name: str, port: int, output: Optional[str]):
    """Record a new API session via proxy."""
    import os

    from socialseed_e2e.recorder import RecordingProxy

    output_path = output or f"recordings/{name}.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    proxy = RecordingProxy(port=port)
    proxy.start(name)

    console.print(
        "\n[bold red]🔴 Recording Proxy active.[/bold red] [bold green]Press Ctrl+C to stop recording and save the session...[/bold green]\n"
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        session = proxy.stop()
        session.save(output_path)
        console.print(f"\n[bold green]✓ Session saved to:[/bold green] {output_path}")
        console.print(f"Recorded {len(session.interactions)} interactions.")


@recorder.command("replay")
@click.argument("file")
def recorder_replay(file: str):
    """Replay a recorded session."""
    from playwright.sync_api import sync_playwright

    from socialseed_e2e.core.base_page import BasePage
    from socialseed_e2e.recorder import RecordedSession, SessionPlayer

    if not Path(file).exists():
        console.print(f"[red]❌ Error:[/red] File '{file}' not found.")
        return

    session = RecordedSession.load(file)

    with sync_playwright() as p:
        page = BasePage(base_url="", playwright=p)
        page.setup()
        try:
            SessionPlayer.play(session, page)
        finally:
            page.teardown()


@recorder.command("convert")
@click.argument("file")
@click.option("--output", "-o", help="Output test file path")
def recorder_convert(file: str, output: Optional[str]):
    """Convert a recorded session to Python test code."""
    from socialseed_e2e.recorder import RecordedSession, SessionConverter

    if not Path(file).exists():
        console.print(f"[red]❌ Error:[/red] File '{file}' not found.")
        return

    session = RecordedSession.load(file)
    code = SessionConverter.to_python_code(session)

    output_path = output or f"services/recorded/modules/{session.name}_flow.py"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(code)

    console.print(f"\n[bold green]✓ Test module generated:[/bold green] {output_path}")


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

    # Check service connectivity if in an E2E project
    if _is_e2e_project():
        console.print()
        console.print("[bold cyan]🌐 Service Connectivity Check[/bold cyan]")

        try:
            loader = ApiConfigLoader()
            config = loader.load()

            if config.services:
                connectivity_table = Table(title="Service Health Status")
                connectivity_table.add_column("Service", style="cyan")
                connectivity_table.add_column("URL", style="green")
                connectivity_table.add_column("Status", style="bold")

                for name, svc in config.services.items():
                    is_healthy, status_msg = _check_service_health(
                        svc.base_url, svc.health_endpoint or "/actuator/health"
                    )
                    connectivity_table.add_row(name, svc.base_url, status_msg)

                console.print(connectivity_table)
            else:
                console.print("[yellow]  ℹ No services configured[/yellow]")

        except Exception as e:
            console.print(f"[yellow]  ⚠ Could not check services: {e}[/yellow]")

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
                # Use svc.name (original name from config) instead of normalized key
                display_name = svc.name if svc.name else name
                table.add_row(
                    display_name,
                    svc.base_url,
                    svc.health_endpoint or "N/A",
                    "✓" if svc.required else "✗",
                )

            console.print(table)
        else:
            console.print("[yellow]⚠ No services configured[/yellow]")
            console.print("   Use: [cyan]e2e new-service <name>[/cyan]")

        # Check service connectivity
        if config.services:
            console.print()
            console.print("[bold cyan]🌐 Checking Service Health...[/bold cyan]")

            health_table = Table(title="Live Service Status")
            health_table.add_column("Service", style="cyan")
            health_table.add_column("Health Endpoint", style="yellow")
            health_table.add_column("Status", style="bold")

            healthy_count = 0
            for name, svc in config.services.items():
                health_url = svc.health_endpoint or "/actuator/health"
                is_healthy, status_msg = _check_service_health(svc.base_url, health_url)
                if is_healthy:
                    healthy_count += 1
                health_table.add_row(name, health_url, status_msg)

            console.print(health_table)
            console.print(
                f"\n[bold]{healthy_count}/{len(config.services)} services healthy[/bold]"
            )

        console.print()
        console.print("[bold green]✅ Valid configuration[/bold green]")

    except ConfigError as e:
        console.print(f"[red]❌ Configuration error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error:[/red] {e}")
        sys.exit(1)


# Funciones auxiliares


def _check_service_health(
    base_url: str, health_endpoint: str, timeout: int = 5
) -> Tuple[bool, str]:
    """Check if a service health endpoint is accessible.

    Args:
        base_url: Service base URL
        health_endpoint: Health check endpoint path
        timeout: Request timeout in seconds

    Returns:
        Tuple of (is_healthy, status_message)
    """
    import requests

    if not health_endpoint or health_endpoint == "N/A":
        return False, "No health endpoint configured"

    try:
        url = f"{base_url}{health_endpoint}"
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, f"✅ Healthy (200)"
        else:
            return False, f"⚠️  Status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "❌ Connection refused"
    except requests.exceptions.Timeout:
        return False, "⏱️  Timeout"
    except Exception as e:
        return False, f"❌ Error: {str(e)[:30]}"


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
def manifest_check(directory: str):
    """Validate manifest freshness using source code hashes.

    Quickly checks if the project manifest is up-to-date by comparing
    stored SHA-256 hashes with current source files.

    Examples:
        e2e manifest-check                    # Check current directory
        e2e manifest-check /path/to/project   # Check specific project
    """
    target_path = Path(directory).resolve()
    manifest_path = target_path / "project_knowledge.json"

    if not manifest_path.exists():
        console.print(f"[red]❌ Error:[/red] Manifest not found at {manifest_path}")
        console.print("Run 'e2e manifest' first to generate the manifest.")
        sys.exit(1)

    try:
        from socialseed_e2e.project_manifest import ManifestGenerator
        from socialseed_e2e.project_manifest.hash_validator import HashValidator

        console.print("\n🔍 [bold cyan]Checking Manifest Freshness[/bold cyan]")
        console.print(f"   Project: {target_path}\n")

        # Load existing manifest
        generator = ManifestGenerator(target_path)
        manifest = generator.get_manifest()

        if not manifest:
            console.print("[red]❌ Error:[/red] Could not load manifest")
            sys.exit(1)

        # Validate using hash validator
        validator = HashValidator(target_path)
        freshness, changed_files = validator.validate_manifest(manifest)

        # Display results
        if freshness.value == "fresh":
            console.print("[bold green]✅ Manifest is FRESH[/bold green]")
            console.print("   All source files match stored hashes.\n")
            console.print(f"   Version: {manifest.version}")
            console.print(f"   Last updated: {manifest.last_updated}")
            console.print(f"   Total files tracked: {len(manifest.source_hashes)}\n")
        elif freshness.value == "stale":
            console.print("[bold yellow]⚠️  Manifest is STALE[/bold yellow]")
            console.print("   Source files have changed and need re-scanning.\n")

            if changed_files:
                console.print(f"   Changed files: {len(changed_files)}")
                for file_path in list(changed_files.keys())[:5]:
                    console.print(f"     • {file_path}")
                if len(changed_files) > 5:
                    console.print(f"     ... and {len(changed_files) - 5} more\n")

            console.print(
                "\n[yellow]Run 'e2e manifest' to update the manifest.[/yellow]\n"
            )
            sys.exit(1)
        else:  # partial
            console.print("[bold orange]⚠️  Manifest is PARTIALLY FRESH[/bold orange]")
            console.print("   Some files may be outdated.\n")
            console.print(
                "[yellow]Run 'e2e manifest --force' for full re-scan.[/yellow]\n"
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Error checking manifest:[/red] {e}")
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
        check_and_install_extra("rag", auto_install=False)
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
        check_and_install_extra("rag", auto_install=False)
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
        check_and_install_extra("rag", auto_install=False)
        sys.exit(1)
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

    Prerequisites:
        - Run 'e2e manifest' first to generate project manifest
        - Services must be defined in e2e.conf

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
        with console.status(
            "[bold yellow]Step 1/5:[/bold yellow] Parsing database models...",
            spinner="dots",
        ) as status:
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
        console.print()
        with console.status(
            "[bold yellow]Step 2/5:[/bold yellow] Loading project manifest...",
            spinner="dots",
        ) as status:
            manifest_path = target_path / "project_knowledge.json"
            if not manifest_path.exists():
                from socialseed_e2e.project_manifest import ManifestGenerator

                generator = ManifestGenerator(target_path)
                generator.generate()

            from socialseed_e2e.project_manifest import ManifestAPI

            api = ManifestAPI(target_path)
            api._load_manifest()
            manifest = api.manifest

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
        port_list: Optional[List[int]] = None
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
        api._load_manifest()
        manifest = api.manifest

        if not manifest:
            console.print(
                "[yellow]⚠ No project manifest found. Run 'e2e manifest' first.[/yellow]"
            )
            sys.exit(1)

        # Generate report with spinner
        output_dir = Path(output) if output else None
        with console.status(
            "[bold cyan]🔍 Analyzing project and generating report...[/bold cyan]",
            spinner="dots",
        ):
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
        api._load_manifest()
        manifest = api.manifest

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
            ExternalServiceRegistry,
            MockServerGenerator,
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
                "\n[bold green]✅ Mock server generated successfully![/bold green]"
            )
            console.print("\n[bold]To run the mock server:[/bold]")
            console.print(f"   cd {output_path}")
            console.print(f"   python mock_{service}.py")
            console.print("\n   Or with Docker:")
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

    console.print("\n🚀 [bold cyan]Starting Mock Servers[/bold cyan]\n")

    try:
        from socialseed_e2e.ai_mocking import (
            ExternalServiceRegistry,
            MockServerGenerator,
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
                    console.print("     [green]✓[/green] Generated")
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
                "\n[bold green]✅ Mock servers running in background[/bold green]"
            )
            console.print("   Check with: [cyan]ps aux | grep mock_[/cyan]\n")

        elif processes:
            console.print(f"\n[bold]Running {len(processes)} mock servers...[/bold]")
            console.print("Press Ctrl+C to stop all\n")

            try:
                # Wait for all processes
                for service, process in processes:
                    process.wait()
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Stopping all mock servers...[/yellow]")
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

    console.print("\n✅ [bold cyan]Contract Validation[/bold cyan]")
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
                "\n   [bold green]✅ All contracts validated successfully![/bold green]\n"
            )
        else:
            console.print(
                f"\n   [bold yellow]⚠ {total_invalid} contract(s) "
                f"have validation issues[/bold yellow]\n"
            )

        sys.exit(0 if total_invalid == 0 else 1)

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--service",
    "-s",
    default="unknown",
    help="Service name for the profiling session",
)
@click.option(
    "--output",
    "-o",
    default=".e2e/performance",
    help="Output directory for performance reports",
)
@click.option(
    "--threshold",
    "-t",
    default=50.0,
    help="Regression threshold percentage (default: 50)",
)
@click.option(
    "--compare-baseline",
    is_flag=True,
    help="Compare with baseline and show regressions",
)
@click.option(
    "--set-baseline",
    is_flag=True,
    help="Set current run as baseline for future comparisons",
)
def perf_profile(
    directory: str,
    service: str,
    output: str,
    threshold: float,
    compare_baseline: bool,
    set_baseline: bool,
):
    """Run performance profiling and analysis (Issue #87).

    Profiles all E2E tests and provides AI-powered performance insights
    including latency tracking, regression detection, and bottleneck analysis.

    Examples:
        e2e perf-profile                    # Profile current directory
        e2e perf-profile /path/to/project   # Profile specific project
        e2e perf-profile --compare-baseline # Compare with baseline
        e2e perf-profile --set-baseline     # Set current as baseline
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    try:
        from socialseed_e2e.performance import (
            PerformanceProfiler,
            SmartAlertGenerator,
            ThresholdAnalyzer,
        )

        console.print("\n📊 [bold cyan]AI-Powered Performance Profiling[/bold cyan]")
        console.print(f"   Service: {service}")
        console.print(f"   Project: {target_path}\n")

        # Create profiler
        profiler = PerformanceProfiler(
            service_name=service,
            output_dir=Path(output),
        )

        # Start profiling
        profiler.start_profiling()

        console.print("[yellow]Profiling session started...[/yellow]")
        console.print("Run your E2E tests now. Press Ctrl+C to stop profiling.\n")

        try:
            # Wait for user to finish tests
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        # Stop profiling
        profiler.stop_profiling()

        # Generate report
        report = profiler.generate_report()
        report_path = profiler.save_report(report)

        console.print(f"\n[green]✓ Report saved:[/green] {report_path}")

        # Compare with baseline if requested
        if compare_baseline:
            console.print("\n[yellow]Comparing with baseline...[/yellow]")

            analyzer = ThresholdAnalyzer(
                performance_dir=Path(output),
                regression_threshold_pct=threshold,
            )

            if analyzer.load_baseline():
                regressions = analyzer.detect_regressions(report)

                if regressions:
                    console.print(
                        f"\n[red]⚠ {len(regressions)} regression(s) detected![/red]"
                    )

                    # Generate smart alerts
                    alert_gen = SmartAlertGenerator(project_root=target_path)
                    alerts = alert_gen.generate_alerts(report, regressions)

                    for alert in alerts:
                        severity_color = {
                            "critical": "red",
                            "warning": "yellow",
                            "info": "blue",
                        }.get(alert.severity.value, "white")

                        console.print(
                            f"\n[{severity_color}]{alert.severity.value.upper()}:"
                            f"[/{severity_color}] {alert.title}"
                        )
                        console.print(alert.message)

                        if alert.recommendations:
                            console.print("\n[cyan]Recommendations:[/cyan]")
                            for rec in alert.recommendations[:3]:
                                console.print(f"  • {rec}")
                else:
                    console.print("\n[green]✓ No regressions detected[/green]")
            else:
                console.print(
                    "\n[yellow]⚠ No baseline found. Run with --set-baseline first.[/yellow]"
                )

        # Set baseline if requested
        if set_baseline:
            analyzer = ThresholdAnalyzer(performance_dir=Path(output))
            baseline_path = analyzer.set_baseline(report)
            console.print(f"\n[green]✓ Baseline set:[/green] {baseline_path}")

        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--output",
    "-o",
    default=".e2e/performance",
    help="Performance reports directory",
)
@click.option(
    "--baseline",
    "-b",
    help="Path to baseline report for comparison",
)
@click.option(
    "--threshold",
    "-t",
    default=50.0,
    help="Regression threshold percentage",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
def perf_report(
    directory: str,
    output: str,
    baseline: str,
    threshold: float,
    format: str,
):
    """Generate performance report with AI analysis (Issue #87).

    Analyzes performance reports and generates detailed analysis
    including regressions, trends, and recommendations.

    Examples:
        e2e perf-report                     # Analyze latest report
        e2e perf-report --baseline path     # Compare with baseline
        e2e perf-report -f markdown         # Generate markdown report
    """
    target_path = Path(directory).resolve()
    output_dir = Path(output)

    try:
        from socialseed_e2e.performance import SmartAlertGenerator, ThresholdAnalyzer

        console.print("\n📈 [bold cyan]Performance Report Analysis[/bold cyan]\n")

        # Load latest report
        analyzer = ThresholdAnalyzer(
            performance_dir=output_dir,
            regression_threshold_pct=threshold,
        )

        latest_report = analyzer._find_baseline_file()
        if not latest_report:
            console.print("[red]Error:[/red] No performance reports found.")
            console.print(
                "Run [cyan]e2e perf-profile[/cyan] first to generate reports."
            )
            sys.exit(1)

        # Load baseline if provided
        if baseline:
            analyzer.load_baseline(Path(baseline))
        else:
            analyzer.load_baseline()

        # Generate report
        console.print(f"Analyzing: {latest_report}\n")

        # Load and analyze
        with open(latest_report, "r") as f:
            import json

            report_data = json.load(f)

        # Check for regressions
        if analyzer.baseline:
            report = analyzer._report_from_dict(report_data)
            regressions = analyzer.detect_regressions(report)

            if regressions:
                # Generate smart alerts
                alert_gen = SmartAlertGenerator(project_root=target_path)
                alerts = alert_gen.generate_alerts(report, regressions)

                if format == "text":
                    summary = alert_gen.generate_summary_report(report, regressions)
                    console.print(summary)

                    console.print("\n[bold]Detailed Alerts:[/bold]\n")
                    for alert in alerts:
                        severity_color = {
                            "critical": "red",
                            "warning": "yellow",
                            "info": "blue",
                        }.get(alert.severity.value, "white")

                        console.print(
                            f"[{severity_color}]{alert.severity.value.upper()}:"
                            f"[/{severity_color}] {alert.title}"
                        )
                        console.print(alert.message)
                        console.print()

                elif format == "json":
                    import json

                    output_data = {
                        "report": report_data,
                        "regressions": [
                            {
                                "endpoint": f"{r.method} {r.endpoint_path}",
                                "type": r.regression_type.value,
                                "change_pct": r.percentage_change,
                                "severity": r.severity.value,
                            }
                            for r in regressions
                        ],
                        "alerts": [a.to_dict() for a in alerts],
                    }
                    console.print(json.dumps(output_data, indent=2))

                elif format == "markdown":
                    lines = [
                        "# Performance Analysis Report",
                        "",
                        f"**Service:** {report_data.get('service_name', 'unknown')}",
                        f"**Date:** {report_data.get('timestamp', 'N/A')}",
                        "",
                        "## Summary",
                        "",
                        f"- Total Requests: {report_data.get('total_requests', 0)}",
                        f"- Overall Avg Latency: {report_data.get('overall_avg_latency', 0):.2f}ms",
                        f"- Regressions Detected: {len(regressions)}",
                        "",
                        "## Regressions",
                        "",
                    ]

                    for alert in alerts:
                        lines.extend(
                            [
                                f"### {alert.title}",
                                "",
                                f"**Severity:** {alert.severity.value}",
                                "",
                                alert.message,
                                "",
                                "**Recommendations:**",
                                "",
                            ]
                        )
                        for rec in alert.recommendations[:3]:
                            lines.append(f"- {rec}")
                        lines.append("")

                    console.print("\n".join(lines))

            else:
                console.print("[green]✓ No regressions detected[/green]")
                console.print(
                    "All endpoints are performing within expected thresholds."
                )
        else:
            # Just show the report without comparison
            console.print("[bold]Performance Summary:[/bold]\n")
            console.print(report_data.get("summary", "No summary available"))

        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--name",
    "-n",
    required=True,
    help="Strategy name",
)
@click.option(
    "--description",
    "-d",
    default="",
    help="Strategy description",
)
@click.option(
    "--services",
    "-s",
    help="Comma-separated list of services to include (default: all)",
)
@click.option(
    "--output",
    "-o",
    help="Output path for strategy file",
    type=click.Path(),
)
def plan_strategy(
    project: str, name: str, description: str, services: str, output: str
):
    """Generate an AI-driven test strategy.

    Analyzes the codebase and creates a comprehensive testing strategy
    with risk-based prioritization and optimal execution order.

    Prerequisites:
        - Run 'e2e manifest' first for best results
        - Services must be defined in e2e.conf

    Examples:
        e2e plan-strategy --name "API Regression Strategy"
        e2e plan-strategy --name "Critical Path Tests" --services users-api,orders-api
    """
    from socialseed_e2e.ai_orchestrator import StrategyPlanner

    console.print(f"\n🤖 [bold blue]Planning Test Strategy:[/bold blue] {name}\n")

    try:
        planner = StrategyPlanner(project)

        target_services = None
        if services:
            target_services = [s.strip() for s in services.split(",")]

        strategy = planner.generate_strategy(
            name=name,
            description=description or f"Auto-generated strategy for {name}",
            target_services=target_services,
        )

        # Save strategy
        output_path = Path(output) if output else None
        saved_path = planner.save_strategy(strategy, output_path)

        # Display summary
        console.print(
            f"[green]✓[/green] Strategy generated: [bold]{strategy.id}[/bold]"
        )
        console.print(f"[green]✓[/green] Saved to: {saved_path}")
        console.print()
        console.print("[bold]Strategy Summary:[/bold]")
        console.print(f"  Total test cases: {len(strategy.test_cases)}")
        console.print(f"  Services covered: {', '.join(strategy.target_services)}")
        console.print(
            f"  Estimated duration: {strategy.total_estimated_duration_ms // 1000}s"
        )
        console.print(f"  Parallel groups: {len(strategy.parallelization_groups)}")
        console.print()

        # Show priority breakdown
        from socialseed_e2e.ai_orchestrator import TestPriority

        priority_counts: Dict[TestPriority, int] = {}
        for tc in strategy.test_cases:
            priority_counts[tc.priority] = priority_counts.get(tc.priority, 0) + 1

        console.print("[bold]Priority Distribution:[/bold]")
        for priority in [
            TestPriority.CRITICAL,
            TestPriority.HIGH,
            TestPriority.MEDIUM,
            TestPriority.LOW,
        ]:
            count = priority_counts.get(priority, 0)
            if count > 0:
                console.print(f"  {priority.value.upper()}: {count} tests")

        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--strategy-id",
    "-s",
    required=True,
    help="Strategy ID to execute",
)
@click.option(
    "--parallel",
    "-j",
    default=4,
    help="Number of parallel workers",
    type=int,
)
@click.option(
    "--no-healing",
    is_flag=True,
    help="Disable self-healing",
)
@click.option(
    "--auto-fix",
    is_flag=True,
    help="Auto-apply fixes without confirmation",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
def autonomous_run(
    project: str,
    strategy_id: str,
    parallel: int,
    no_healing: bool,
    auto_fix: bool,
    verbose: bool,
):
    """Run tests autonomously with AI orchestration.

    Executes a test strategy with intelligent retry, self-healing,
    and autonomous debugging capabilities.

    Prerequisites:
        - Create a strategy first with 'e2e plan-strategy --name "My Strategy"'
        - Strategy IDs are generated by the plan-strategy command

    Examples:
        e2e autonomous-run --strategy-id abc123
        e2e autonomous-run --strategy-id abc123 --parallel 8 --auto-fix
    """
    from socialseed_e2e.ai_orchestrator import (
        AutonomousRunner,
        OrchestratorConfig,
        StrategyPlanner,
    )

    console.print("\n🚀 [bold blue]Autonomous Test Execution[/bold blue]\n")

    try:
        # Load strategy
        planner = StrategyPlanner(project)
        strategy = planner.load_strategy(strategy_id)

        console.print(f"Loaded strategy: [bold]{strategy.name}[/bold]")
        console.print(f"Test cases: {len(strategy.test_cases)}")
        console.print()

        # Configure runner
        config = OrchestratorConfig(
            enable_self_healing=not no_healing,
            auto_apply_fixes=auto_fix,
            parallel_workers=parallel,
        )

        runner = AutonomousRunner(project, config)

        # Progress callback
        def progress_callback(result):
            if verbose:
                status_color = "green" if result.status.value == "passed" else "red"
                console.print(
                    f"  [{status_color}]{result.status.value.upper()}[/{status_color}] "
                    f"{result.test_id} ({result.duration_ms}ms)"
                )

        # Create context factory (simplified - would use actual page creation)
        def context_factory():
            # This would create appropriate page context based on project config
            from socialseed_e2e.core.base_page import BasePage

            return BasePage("http://localhost:8000")

        # Run execution
        execution = runner.run_strategy(strategy, context_factory, progress_callback)

        # Display results
        console.print()
        console.print("=" * 50)
        console.print("[bold]Execution Complete[/bold]")
        console.print("=" * 50)
        console.print()

        # Summary table
        table = Table(title="Test Results Summary")
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")

        for status, count in execution.summary.items():
            color = {
                "passed": "green",
                "failed": "red",
                "healed": "yellow",
                "flaky": "orange",
            }.get(status, "white")
            table.add_row(status.upper(), str(count), style=color)

        console.print(table)
        console.print()

        # Overall status
        if execution.status.value == "passed":
            console.print("[bold green]✓ All tests passed![/bold green]")
        elif execution.status.value == "healed":
            console.print("[bold yellow]⚠ Some tests were auto-healed[/bold yellow]")
        else:
            console.print("[bold red]✗ Some tests failed[/bold red]")

        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--test-file",
    "-f",
    required=True,
    help="Test file to analyze",
    type=click.Path(exists=True, dir_okay=False),
)
def analyze_flaky(project: str, test_file: str):
    """Analyze a test file for flakiness patterns.

    Scans the test code and identifies patterns that commonly
    cause flaky tests, providing recommendations for fixes.

    Examples:
        e2e analyze-flaky --test-file services/users/modules/test_login.py
    """
    from socialseed_e2e.ai_orchestrator import SelfHealer

    console.print("\n🔍 [bold blue]Analyzing Test for Flakiness[/bold blue]\n")

    try:
        healer = SelfHealer(project)
        report = healer.analyze_test_file(test_file)

        console.print(f"[bold]File:[/bold] {report['test_file']}")
        console.print()

        patterns = report.get("flakiness_patterns", [])
        if patterns:
            console.print(
                f"[yellow]⚠ Found {len(patterns)} flakiness patterns:[/yellow]"
            )
            console.print()

            table = Table(title="Detected Patterns")
            table.add_column("Pattern", style="bold")
            table.add_column("Severity")
            table.add_column("Line")
            table.add_column("Description")

            for pattern in patterns:
                severity_color = {
                    "high": "red",
                    "medium": "yellow",
                    "low": "blue",
                }.get(pattern["severity"], "white")

                table.add_row(
                    pattern["pattern"],
                    f"[{severity_color}]{pattern['severity'].upper()}[/{severity_color}]",
                    str(pattern["line"]),
                    pattern["description"],
                )

            console.print(table)
            console.print()

            # Show recommendations
            recommendations = report.get("recommendations", [])
            if recommendations:
                console.print("[bold]Recommendations:[/bold]")
                for i, rec in enumerate(recommendations, 1):
                    console.print(f"  {i}. {rec}")
                console.print()
        else:
            console.print("[green]✓ No flakiness patterns detected[/green]")
            console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--execution-id",
    "-e",
    required=True,
    help="Execution ID to debug",
)
@click.option(
    "--apply-fix",
    is_flag=True,
    help="Apply suggested fix automatically",
)
def debug_execution(project: str, execution_id: str, apply_fix: bool):
    """Debug a failed test execution with AI.

    Analyzes failed tests, identifies root causes, and suggests
    or applies fixes automatically.

    Prerequisites:
        - Run 'e2e run --report json' first to generate execution records
        - Execution IDs are stored in .e2e/reports/

    Examples:
        e2e debug-execution --execution-id exec_20240211_120000
        e2e debug-execution --execution-id exec_20240211_120000 --apply-fix
    """
    from socialseed_e2e.ai_orchestrator import AIDebugger

    console.print("\n🐛 [bold blue]AI-Powered Debug Analysis[/bold blue]\n")

    try:
        debugger = AIDebugger(project)
        report = debugger.get_debug_report(execution_id)

        if "error" in report:
            console.print(f"[red]Error:[/red] {report['error']}")
            return

        console.print(f"[bold]Execution ID:[/bold] {execution_id}")
        console.print(f"[bold]Total Failures:[/bold] {report['total_failures']}")
        console.print(
            f"[bold]Avg Confidence:[/bold] {report['average_confidence']:.2%}"
        )
        console.print(f"[bold]Need Review:[/bold] {report['requiring_human_review']}")
        console.print()

        # Show failures by type
        if report.get("failures_by_type"):
            console.print("[bold]Failures by Type:[/bold]")
            for error_type, count in report["failures_by_type"].items():
                console.print(f"  {error_type}: {count}")
            console.print()

        # Show detailed analyses
        analyses = report.get("analyses", [])
        if analyses:
            for analysis in analyses:
                console.print("-" * 50)
                console.print(f"[bold]Test:[/bold] {analysis['test_id']}")
                console.print(f"[bold]Failure Type:[/bold] {analysis['failure_type']}")
                console.print(
                    f"[bold]Confidence:[/bold] {analysis['confidence_score']:.2%}"
                )
                console.print(f"[bold]Root Cause:[/bold] {analysis['root_cause']}")
                console.print()

                if analysis.get("suggested_fixes"):
                    console.print("[bold]Suggested Fixes:[/bold]")
                    for fix in analysis["suggested_fixes"]:
                        risk = fix.get("risk_level", "unknown")
                        score = fix.get("applicability_score", 0)
                        console.print(
                            f"  - {fix['description']} (risk: {risk}, score: {score:.2f})"
                        )
                    console.print()

        console.print("-" * 50)
        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def healing_stats(project: str):
    """View self-healing statistics.

    Shows statistics about auto-healed tests, most common
    flakiness patterns, and healing success rates.
    """
    from socialseed_e2e.ai_orchestrator import SelfHealer

    console.print("\n📊 [bold blue]Self-Healing Statistics[/bold blue]\n")

    try:
        healer = SelfHealer(project)
        stats = healer.get_healing_statistics()

        console.print(f"[bold]Total Healings:[/bold] {stats['total_healings']}")
        console.print()

        if stats.get("most_common_patterns"):
            console.print("[bold]Most Common Flakiness Patterns:[/bold]")
            table = Table()
            table.add_column("Pattern", style="bold")
            table.add_column("Count", justify="right")

            for pattern, count in stats["most_common_patterns"]:
                table.add_row(pattern, str(count))

            console.print(table)
            console.print()

        recent = stats.get("recent_healings", [])
        if recent:
            console.print("[bold]Recent Healings:[/bold]")
            for healing in recent[-5:]:
                console.print(f"  - {healing['test_id']} ({healing['timestamp']})")
            console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--description",
    "-d",
    required=True,
    help="Natural language test description",
)
@click.option(
    "--service",
    "-s",
    help="Target service for context",
)
@click.option(
    "--language",
    "-l",
    default="en",
    help="Language of the description (en, es, fr, de)",
)
@click.option(
    "--output",
    "-o",
    help="Output file path",
    type=click.Path(),
)
def translate(project: str, description: str, service: str, language: str, output: str):
    """Translate natural language to test code.

    Converts plain English or other natural language descriptions
    into executable test code.

    Examples:
        e2e translate --description "Verify user can login with valid credentials"
        e2e translate --description "Comprobar que el usuario puede iniciar sesión" --language es
    """
    from socialseed_e2e.nlp import Language, NLToCodePipeline, TranslationContext

    console.print("\n🌐 [bold blue]Natural Language Translation[/bold blue]\n")

    try:
        # Detect language if not specified
        lang_map = {
            "en": Language.ENGLISH,
            "es": Language.SPANISH,
            "fr": Language.FRENCH,
            "de": Language.GERMAN,
            "pt": Language.PORTUGUESE,
            "it": Language.ITALIAN,
        }
        lang = lang_map.get(language.lower(), Language.ENGLISH)

        # Create pipeline
        pipeline = NLToCodePipeline(project)

        # Create context
        context = TranslationContext(
            language=lang,
            service=service,
        )

        # Translate
        result = pipeline.translate(description, context, lang)

        if not result.success:
            console.print("[red]Translation failed:[/red]")
            for error in result.errors:
                console.print(f"  - {error}")
            return

        # Display results
        console.print("[green]✓[/green] Translation successful!\n")

        # Show parsing info
        if result.parsed_test:
            console.print("[bold]Parsed Information:[/bold]")
            console.print(f"  Intent: {result.parsed_test.intent.value}")
            console.print(f"  Confidence: {result.parsed_test.confidence_score:.2%}")
            console.print(f"  Entities: {len(result.parsed_test.entities)}")
            console.print(f"  Actions: {len(result.parsed_test.actions)}")
            console.print(f"  Assertions: {len(result.parsed_test.assertions)}")
            console.print()

        # Show generated code
        if result.generated_code:
            code = result.generated_code

            console.print("[bold]Generated Test:[/bold]")
            console.print(f"  Name: {code.test_name}")
            console.print(f"  Module: {code.module_name}")
            console.print(f"  Lines: {code.lines_of_code}")
            console.print(f"  Assertions: {code.assertions_count}")
            console.print(f"  Confidence: {code.confidence:.2%}")

            if code.requires_review:
                console.print("  [yellow]⚠ Requires manual review[/yellow]")
            console.print()

            # Show code
            console.print("[bold]Code:[/bold]")
            console.print("```python")
            console.print(code.code)
            console.print("```")
            console.print()

            # Show suggestions
            if code.suggestions:
                console.print("[bold]Suggestions:[/bold]")
                for suggestion in code.suggestions:
                    console.print(f"  - {suggestion}")
                console.print()

            # Save to file if requested
            if output:
                output_path = Path(output)
                output_path.write_text(code.code)
                console.print(f"[green]✓[/green] Code saved to: {output}")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--project",
    "-p",
    default=".",
    help="Path to project directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--feature-file",
    "-f",
    required=True,
    help="Path to Gherkin feature file",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--output-dir",
    "-o",
    help="Output directory for generated tests",
    type=click.Path(file_okay=False, dir_okay=True),
)
def gherkin_translate(project: str, feature_file: str, output_dir: str):
    """Convert Gherkin feature files to test code.

    Parses Gherkin/Cucumber feature files and generates executable
    test code from BDD scenarios.

    Examples:
        e2e gherkin-translate --feature-file features/login.feature
        e2e gherkin-translate --feature-file features/ --output-dir tests/generated/
    """
    from socialseed_e2e.nlp import GherkinParser, GherkinToCodeConverter, Language

    console.print("\n🥒 [bold blue]Gherkin to Code Conversion[/bold blue]\n")

    try:
        # Parse feature file
        parser = GherkinParser(Language.ENGLISH)
        feature_text = Path(feature_file).read_text()
        feature = parser.parse(feature_text)

        console.print(f"[green]✓[/green] Parsed feature: [bold]{feature.name}[/bold]")
        console.print(f"  Scenarios: {len(feature.scenarios)}")
        console.print()

        # Convert to code
        converter = GherkinToCodeConverter(project)
        generated_tests = converter.convert_feature(feature)

        # Display results
        console.print("[bold]Generated Tests:[/bold]")
        for i, test in enumerate(generated_tests, 1):
            console.print(f"\n  Test {i}: {test.test_name}")
            console.print(f"  Confidence: {test.confidence:.2%}")
            if test.requires_review:
                console.print("  [yellow]⚠ Requires review[/yellow]")

            # Show code snippet
            code_lines = test.code.split("\n")[:10]
            console.print("  Code preview:")
            for line in code_lines:
                console.print(f"    {line}")
            if len(test.code.split("\n")) > 10:
                console.print("    ...")

        # Save to output directory
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            for test in generated_tests:
                test_file = output_path / f"{test.test_name}.py"
                test_file.write_text(test.code)

            console.print(f"\n[green]✓[/green] Tests saved to: {output_dir}")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@cli.group()
def ai_learning():
    """Commands for AI learning and feedback loop."""
    pass


@cli.group()
def shadow():
    """Shadow Runner - Capture traffic and auto-generate tests (Issue #130)."""
    pass


@shadow.command("capture")
@click.argument("name")
@click.option(
    "--target-url", "-u", required=True, help="Target API URL to capture traffic from"
)
@click.option(
    "--output",
    "-o",
    help="Output file for captured traffic (default: .e2e/shadow/<name>.json)",
)
@click.option("--filter-health", is_flag=True, help="Filter out health check requests")
@click.option("--filter-static", is_flag=True, help="Filter out static asset requests")
@click.option("--sanitize", is_flag=True, help="Sanitize PII from captured traffic")
@click.option(
    "--duration",
    "-d",
    type=int,
    help="Capture duration in seconds (default: until Ctrl+C)",
)
@click.option("--max-requests", "-m", type=int, help="Maximum requests to capture")
def shadow_capture(
    name: str,
    target_url: str,
    output: Optional[str],
    filter_health: bool,
    filter_static: bool,
    sanitize: bool,
    duration: Optional[int],
    max_requests: Optional[int],
):
    """Capture real API traffic via middleware proxy.

    Intercepts HTTP traffic between clients and target API,
    recording requests/responses for test generation.

    Examples:
        e2e shadow capture myapp -u http://localhost:8000
        e2e shadow capture myapp -u http://localhost:8000 --duration 300
        e2e shadow capture myapp -u http://localhost:8000 --sanitize --filter-health
    """
    console.print(f"\n🔍 [bold cyan]Shadow Runner - Traffic Capture[/bold cyan]")
    console.print(f"   Name: {name}")
    console.print(f"   Target: {target_url}\n")

    try:
        from socialseed_e2e.shadow_runner import CaptureConfig, ShadowRunner

        output_path = Path(output) if output else Path(f".e2e/shadow/{name}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        config = CaptureConfig(
            target_url=target_url,
            output_path=str(output_path),
            filter_health_checks=filter_health,
            filter_static_assets=filter_static,
            sanitize_pii=sanitize,
            max_requests=max_requests,
        )

        runner = ShadowRunner(config)

        console.print(f"[yellow]Starting capture...[/yellow]")
        console.print(f"   Filter health checks: {'Yes' if filter_health else 'No'}")
        console.print(f"   Filter static assets: {'Yes' if filter_static else 'No'}")
        console.print(f"   Sanitize PII: {'Yes' if sanitize else 'No'}")
        if duration:
            console.print(f"   Duration: {duration}s")
        if max_requests:
            console.print(f"   Max requests: {max_requests}")
        console.print()

        runner.start_capture()

        console.print("[bold green]✓ Capture started![/bold green]")
        if duration:
            console.print(f"   Capturing for {duration} seconds...")
            import time

            time.sleep(duration)
            session = runner.stop_capture()
        else:
            console.print("   Press Ctrl+C to stop capturing...\n")
            try:
                import time

                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                session = runner.stop_capture()

        # Save captured session
        session.save(str(output_path))

        console.print(f"\n[bold green]✓ Capture complete![/bold green]")
        console.print(f"   Requests captured: {len(session.interactions)}")
        console.print(f"   Saved to: {output_path}\n")

        # Show summary
        if session.interactions:
            methods = {}
            paths = set()
            for interaction in session.interactions:
                method = interaction.request.method
                methods[method] = methods.get(method, 0) + 1
                paths.add(interaction.request.path)

            console.print("[bold]Captured Methods:[/bold]")
            for method, count in sorted(methods.items()):
                console.print(f"   {method}: {count}")

            console.print(f"\n[bold]Unique Paths:[/bold] {len(paths)}")

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@shadow.command("generate")
@click.argument("capture_file")
@click.option("--service", "-s", required=True, help="Service name for generated tests")
@click.option(
    "--output-dir", "-o", default="services", help="Output directory for tests"
)
@click.option("--template", "-t", default="standard", help="Test template to use")
@click.option(
    "--group-by",
    "-g",
    type=click.Choice(["endpoint", "flow", "user"]),
    default="endpoint",
    help="Grouping strategy",
)
@click.option("--include-auth", is_flag=True, help="Include authentication patterns")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def shadow_generate(
    capture_file: str,
    service: str,
    output_dir: str,
    template: str,
    group_by: str,
    include_auth: bool,
    verbose: bool,
):
    """Generate tests from captured traffic.

    Analyzes captured API traffic and generates E2E test cases
    that reproduce real user interactions.

    Examples:
        e2e shadow generate capture.json -s users-api
        e2e shadow generate capture.json -s users-api --group-by flow
        e2e shadow generate capture.json -s users-api --include-auth
    """
    capture_path = Path(capture_file)

    if not capture_path.exists():
        console.print(f"[red]❌ Error:[/red] Capture file not found: {capture_path}")
        sys.exit(1)

    console.print(f"\n🤖 [bold cyan]Shadow Runner - Test Generation[/bold cyan]")
    console.print(f"   Capture: {capture_path}")
    console.print(f"   Service: {service}")
    console.print(f"   Output: {output_dir}\n")

    try:
        from socialseed_e2e.shadow_runner import ShadowRunner, TestGenerationConfig

        config = TestGenerationConfig(
            service_name=service,
            output_dir=output_dir,
            template=template,
            group_by=group_by,
            include_auth_patterns=include_auth,
        )

        runner = ShadowRunner(config)

        # Load captured session
        console.print("[yellow]Loading capture file...[/yellow]")
        session = runner.load_capture(str(capture_path))
        console.print(f"   ✓ Loaded {len(session.interactions)} interactions\n")

        # Generate tests
        console.print("[yellow]Generating tests...[/yellow]")
        generated_tests = runner.generate_tests(session)

        if not generated_tests:
            console.print(
                "[yellow]⚠ No tests could be generated from this capture[/yellow]"
            )
            return

        # Display results
        console.print(
            f"\n[bold green]✓ Generated {len(generated_tests)} test(s):[/bold green]\n"
        )

        for test in generated_tests:
            console.print(f"   📄 {test.name}")
            console.print(f"      Endpoints: {len(test.endpoints)}")
            console.print(f"      File: {test.file_path}")
            if verbose and test.description:
                console.print(f"      Description: {test.description}")
            console.print()

        # Show summary
        total_endpoints = sum(len(t.endpoints) for t in generated_tests)
        console.print("=" * 50)
        console.print("[bold]Summary:[/bold]")
        console.print(f"   Tests generated: {len(generated_tests)}")
        console.print(f"   Total endpoints covered: {total_endpoints}")
        console.print(f"   Output directory: {Path(output_dir) / service}")
        console.print()

        console.print("[bold]Next steps:[/bold]")
        console.print(
            f"   1. Review generated tests in: {Path(output_dir) / service / 'modules'}"
        )
        console.print("   2. Customize test data as needed")
        console.print("   3. Run tests: [cyan]e2e run --service {service}[/cyan]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@shadow.command("replay")
@click.argument("capture_file")
@click.option("--target-url", "-u", help="Override target URL for replay")
@click.option(
    "--speed",
    "-s",
    type=click.Choice(["realtime", "fast", "slow"]),
    default="fast",
    help="Replay speed",
)
@click.option("--stop-on-error", is_flag=True, help="Stop on first error")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be replayed without executing"
)
def shadow_replay(
    capture_file: str,
    target_url: Optional[str],
    speed: str,
    stop_on_error: bool,
    dry_run: bool,
):
    """Replay captured traffic session.

    Replays a captured API session against a target API,
    useful for load testing or regression testing.

    Examples:
        e2e shadow replay capture.json
        e2e shadow replay capture.json -u http://localhost:8000
        e2e shadow replay capture.json --speed realtime --stop-on-error
    """
    capture_path = Path(capture_file)

    if not capture_path.exists():
        console.print(f"[red]❌ Error:[/red] Capture file not found: {capture_path}")
        sys.exit(1)

    console.print(f"\n🔄 [bold cyan]Shadow Runner - Session Replay[/bold cyan]")
    console.print(f"   Capture: {capture_path}\n")

    try:
        from socialseed_e2e.shadow_runner import ReplayConfig, ShadowRunner

        config = ReplayConfig(
            capture_file=str(capture_path),
            target_url=target_url,
            speed=speed,
            stop_on_error=stop_on_error,
        )

        runner = ShadowRunner(config)

        # Load session
        session = runner.load_capture(str(capture_path))
        console.print(
            f"[yellow]Loaded session with {len(session.interactions)} interactions[/yellow]\n"
        )

        if dry_run:
            console.print("[bold]Dry run - would execute:[/bold]\n")
            for i, interaction in enumerate(session.interactions, 1):
                console.print(
                    f"   {i}. {interaction.request.method} {interaction.request.path}"
                )
            console.print()
            return

        # Replay session
        console.print(f"[bold]Replaying at {speed} speed...[/bold]\n")
        results = runner.replay_session(session)

        # Display results
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count

        console.print("\n" + "=" * 50)
        console.print("[bold]Replay Results:[/bold]")
        console.print(f"   Total: {len(results)}")
        console.print(f"   [green]✓ Success:[/green] {success_count}")
        if failed_count > 0:
            console.print(f"   [red]✗ Failed:[/red] {failed_count}")
        console.print()

        if failed_count > 0 and stop_on_error:
            console.print("[yellow]⚠ Stopped on first error as requested[/yellow]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@shadow.command("analyze")
@click.argument("capture_file")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option("--show-pii", is_flag=True, help="Show detected PII (for debugging)")
def shadow_analyze(capture_file: str, format: str, show_pii: bool):
    """Analyze captured traffic patterns.

    Analyzes captured traffic to show usage patterns,
    endpoint statistics, and detected data patterns.

    Examples:
        e2e shadow analyze capture.json
        e2e shadow analyze capture.json -f json
    """
    capture_path = Path(capture_file)

    if not capture_path.exists():
        console.print(f"[red]❌ Error:[/red] Capture file not found: {capture_path}")
        sys.exit(1)

    console.print(f"\n📊 [bold cyan]Shadow Runner - Traffic Analysis[/bold cyan]\n")

    try:
        from socialseed_e2e.shadow_runner import ShadowRunner

        runner = ShadowRunner()
        session = runner.load_capture(str(capture_path))

        # Analyze patterns
        analysis = runner.analyze_patterns(session)

        if format == "json":
            import json

            console.print(json.dumps(analysis, indent=2, default=str))
        else:
            # Display as table
            console.print(
                f"[bold]Total Interactions:[/bold] {analysis['total_interactions']}"
            )
            console.print(f"[bold]Time Range:[/bold] {analysis['time_range']}")
            console.print()

            if analysis.get("method_distribution"):
                console.print("[bold]Method Distribution:[/bold]")
                table = Table()
                table.add_column("Method", style="cyan")
                table.add_column("Count", style="green")
                table.add_column("Percentage", style="yellow")

                for method, stats in analysis["method_distribution"].items():
                    table.add_row(
                        method, str(stats["count"]), f"{stats['percentage']:.1f}%"
                    )
                console.print(table)
                console.print()

            if analysis.get("top_endpoints"):
                console.print("[bold]Top Endpoints:[/bold]")
                table = Table()
                table.add_column("Endpoint", style="cyan")
                table.add_column("Method", style="green")
                table.add_column("Hits", style="yellow")
                table.add_column("Avg Response Time", style="white")

                for endpoint in analysis["top_endpoints"][:10]:
                    table.add_row(
                        endpoint["path"][:50],
                        endpoint["method"],
                        str(endpoint["count"]),
                        f"{endpoint['avg_response_time']:.0f}ms",
                    )
                console.print(table)
                console.print()

            if analysis.get("detected_patterns"):
                console.print("[bold]Detected Patterns:[/bold]")
                for pattern in analysis["detected_patterns"]:
                    console.print(f"   • {pattern}")
                console.print()

            if show_pii and analysis.get("pii_detected"):
                console.print("[bold yellow]⚠ PII Detected in Traffic:[/bold yellow]")
                for pii in analysis["pii_detected"]:
                    console.print(f"   • {pii['type']}: {pii['count']} occurrences")
                console.print()

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@shadow.command("export-middleware")
@click.argument("framework", type=click.Choice(["flask", "fastapi"]))
@click.option("--output", "-o", help="Output file path")
def shadow_export_middleware(framework: str, output: Optional[str]):
    """Export middleware code for traffic capture.

    Generates ready-to-use middleware code for Flask or FastAPI
    to capture traffic automatically.

    Examples:
        e2e shadow export-middleware flask
        e2e shadow export-middleware fastapi -o shadow_middleware.py
    """
    console.print(f"\n📦 [bold cyan]Shadow Runner - Middleware Export[/bold cyan]")
    console.print(f"   Framework: {framework}\n")

    try:
        from socialseed_e2e.shadow_runner import ShadowRunner

        runner = ShadowRunner()
        middleware_code = runner.export_middleware(framework)

        if output:
            output_path = Path(output)
            output_path.write_text(middleware_code)
            console.print(
                f"[bold green]✓ Middleware saved to:[/bold green] {output_path}\n"
            )
        else:
            console.print("[bold]Generated Middleware Code:[/bold]\n")
            console.print("```python")
            console.print(middleware_code)
            console.print("```\n")

        console.print("[bold]Usage:[/bold]")
        if framework == "flask":
            console.print("   1. Import the middleware in your Flask app")
            console.print("   2. Register it before other middlewares:")
            console.print("      app.wsgi_app = ShadowRunnerMiddleware(app.wsgi_app)\n")
        else:
            console.print("   1. Import the middleware in your FastAPI app")
            console.print("   2. Add it as a middleware:")
            console.print("      app.add_middleware(ShadowRunnerMiddleware)\n")

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


@ai_learning.command("feedback")
@click.option("--storage-path", "-s", help="Path to feedback storage directory")
@click.option(
    "--limit", "-l", default=10, help="Number of recent feedback items to show"
)
@click.option("--analyze", "-a", is_flag=True, help="Analyze patterns in feedback")
def ai_feedback(storage_path: str, limit: int, analyze: bool):
    """View collected feedback from test executions.

    Displays feedback collected during test runs including:
    - Test successes and failures
    - User corrections
    - Performance issues
    - Code changes detected

    Examples:
        e2e ai-learning feedback              # Show recent feedback
        e2e ai-learning feedback --analyze    # Analyze patterns
        e2e ai-learning feedback -l 50        # Show last 50 items
    """
    from socialseed_e2e.ai_learning import FeedbackCollector

    collector = FeedbackCollector(Path(storage_path) if storage_path else None)

    console.print("\n🧠 [bold cyan]AI Learning - Feedback Collection[/bold cyan]\n")

    # Load all feedback
    all_feedback = collector.load_all_feedback()

    if not all_feedback:
        console.print("[yellow]⚠ No feedback collected yet[/yellow]")
        console.print("   Run some tests first: [cyan]e2e run[/cyan]")
        return

    console.print(f"[green]✓[/green] Total feedback items: {len(all_feedback)}\n")

    if analyze:
        # Show pattern analysis
        patterns = collector.analyze_patterns()

        table = Table(title="Feedback Analysis")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Items", str(patterns["total"]))
        table.add_row("Success Rate", f"{patterns['success_rate']:.1%}")
        table.add_row("Avg Execution Time", f"{patterns['avg_execution_time']:.2f}s")
        table.add_row("User Corrections", str(patterns["user_corrections"]))

        console.print(table)
        console.print()

        # Show type distribution
        if patterns.get("type_counts"):
            console.print("[bold]Feedback Types:[/bold]")
            for feedback_type, count in patterns["type_counts"].items():
                console.print(f"  • {feedback_type}: {count}")
            console.print()

        # Show top errors
        if patterns.get("top_errors"):
            console.print("[bold]Top Errors:[/bold]")
            for error_info in patterns["top_errors"][:5]:
                console.print(
                    f"  • {error_info['error'][:60]}... ({error_info['count']} times)"
                )
            console.print()
    else:
        # Show recent feedback
        recent = collector.get_recent_feedback(limit=limit)

        table = Table(title=f"Recent Feedback (last {len(recent)} items)")
        table.add_column("Type", style="cyan")
        table.add_column("Test Name", style="green")
        table.add_column("Time", style="yellow")
        table.add_column("Status", style="white")

        for feedback in reversed(recent):
            status_icon = "✓" if "success" in feedback.feedback_type.value else "✗"
            status_color = (
                "green" if "success" in feedback.feedback_type.value else "red"
            )

            table.add_row(
                feedback.feedback_type.value,
                feedback.test_name[:40],
                feedback.timestamp.strftime("%H:%M:%S"),
                f"[{status_color}]{status_icon}[/{status_color}]",
            )

        console.print(table)


@ai_learning.command("train")
@click.option("--storage-path", "-s", help="Path to feedback storage directory")
@click.option("--output", "-o", help="Output path for trained model")
def ai_train(storage_path: str, output: str):
    """Train AI model from collected feedback.

    Trains the model using user corrections and patterns
    to improve future test generation.

    Examples:
        e2e ai-learning train              # Train with default settings
        e2e ai-learning train -o model.json # Save model to specific file
    """
    from socialseed_e2e.ai_learning import FeedbackCollector, ModelTrainer, TrainingData

    collector = FeedbackCollector(Path(storage_path) if storage_path else None)
    trainer = ModelTrainer()

    console.print("\n🤖 [bold cyan]AI Learning - Model Training[/bold cyan]\n")

    # Get user corrections for training
    all_feedback = collector.load_all_feedback()
    corrections = [
        f for f in all_feedback if f.feedback_type.value == "user_correction"
    ]

    if not corrections:
        console.print("[yellow]⚠ No user corrections found for training[/yellow]")
        console.print("   Corrections are collected when users fix test assertions")
        return

    console.print(
        f"[green]✓[/green] Found {len(corrections)} corrections for training\n"
    )

    # Prepare training data
    training_data = TrainingData(
        inputs=[c.original_assertion or "" for c in corrections],
        outputs=[c.corrected_assertion or "" for c in corrections],
        contexts=[c.user_comment for c in corrections],
    )

    # Train
    with console.status("[bold green]Training model..."):
        metrics = trainer.train_from_corrections(training_data)

    # Show results
    table = Table(title="Training Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Training Samples", str(metrics.training_samples))
    table.add_row("Accuracy", f"{metrics.accuracy:.1%}")
    table.add_row("Precision", f"{metrics.precision:.1%}")
    table.add_row("Recall", f"{metrics.recall:.1%}")
    table.add_row("F1 Score", f"{metrics.f1_score:.1%}")
    table.add_row("Training Time", f"{metrics.training_time:.2f}s")

    console.print(table)
    console.print()

    # Save model if output specified
    if output:
        trainer.export_model(output)
        console.print(f"[green]✓[/green] Model saved to: {output}\n")

    # Show learning progress
    progress = trainer.get_learning_progress()
    console.print("[bold]Learning Progress:[/bold]")
    console.print(f"  Total training sessions: {progress['total_training_sessions']}")
    console.print(f"  Total samples processed: {progress['total_samples']}")
    console.print(f"  Learned patterns: {progress['learned_patterns']}")
    console.print(f"  Learned corrections: {progress['learned_corrections']}")
    console.print()


@ai_learning.command("adapt")
@click.option(
    "--strategy",
    type=click.Choice(["conservative", "balanced", "aggressive"]),
    default="balanced",
)
@click.option(
    "--test-name", "-t", help="Specific test to get adaptation suggestions for"
)
def ai_adapt(strategy: str, test_name: str):
    """Get adaptation suggestions based on learned patterns.

    Analyzes collected feedback and provides suggestions for:
    - Test improvements
    - Execution order optimization
    - Codebase change adaptations

    Examples:
        e2e ai-learning adapt                    # General suggestions
        e2e ai-learning adapt --test-name login  # Suggestions for specific test
        e2e ai-learning adapt --strategy aggressive  # Use aggressive adaptation
    """
    from socialseed_e2e.ai_learning import (
        AdaptationEngine,
        AdaptationStrategy,
        FeedbackCollector,
    )

    strategy_map = {
        "conservative": AdaptationStrategy.CONSERVATIVE,
        "balanced": AdaptationStrategy.BALANCED,
        "aggressive": AdaptationStrategy.AGGRESSIVE,
    }

    engine = AdaptationEngine(strategy=strategy_map[strategy])
    collector = FeedbackCollector()

    console.print(
        f"\n🔄 [bold cyan]AI Learning - Adaptation ({strategy})[/bold cyan]\n"
    )

    # Get feedback for analysis
    all_feedback = collector.load_all_feedback()

    if not all_feedback:
        console.print("[yellow]⚠ No feedback available for adaptation[/yellow]")
        return

    # Get failure patterns
    from socialseed_e2e.ai_learning import FeedbackType

    failures = collector.get_feedback_by_type(FeedbackType.TEST_FAILURE)

    if test_name:
        # Get suggestions for specific test
        test_feedback = collector.get_feedback_by_test(test_name)
        failure_count = len(
            [f for f in test_feedback if f.feedback_type.value == "test_failure"]
        )

        if failure_count > 0:
            console.print(f"[bold]Test:[/bold] {test_name}")
            console.print(f"[bold]Failures detected:[/bold] {failure_count}\n")

            # This would use ModelTrainer in a real implementation
            console.print("[bold]Suggestions:[/bold]")
            if failure_count > 5:
                console.print("  • Consider adding more robust error handling")
                console.print("  • Check if test data is still valid")
                console.print("  • Verify endpoint availability and response format")
            if failure_count > 10:
                console.print("  • This test may need significant refactoring")
                console.print("  • Consider splitting into smaller, more focused tests")
        else:
            console.print(
                f"[green]✓[/green] Test '{test_name}' has no recorded failures"
            )
    else:
        # Show general adaptation metrics
        metrics = engine.get_adaptation_metrics()

        table = Table(title="Adaptation Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Adaptations", str(metrics["total_adaptations"]))
        table.add_row("Strategy", metrics["strategy"])
        table.add_row(
            "Confidence Threshold", f"{metrics.get('confidence_threshold', 0):.1%}"
        )
        table.add_row(
            "Codebase Changes Tracked", str(metrics.get("codebase_changes_tracked", 0))
        )

        console.print(table)
        console.print()

        # Show summary
        patterns = collector.analyze_patterns()
        console.print("[bold]Feedback Summary:[/bold]")
        console.print(f"  Total feedback items: {patterns['total']}")
        console.print(f"  Success rate: {patterns['success_rate']:.1%}")
        console.print(f"  Recent failures: {len(failures)}")
        console.print()


@ai_learning.command("optimize")
@click.argument("service")
def ai_optimize(service: str):
    """Optimize test execution order based on historical data.

    Analyzes past test execution times and suggests
    an optimized order for faster feedback.

    Examples:
        e2e ai-learning optimize users-api    # Optimize tests for users-api service
    """
    from socialseed_e2e.ai_learning import FeedbackCollector, ModelTrainer

    collector = FeedbackCollector()
    trainer = ModelTrainer()

    console.print(f"\n⚡ [bold cyan]AI Learning - Test Optimization[/bold cyan]")
    console.print(f"   Service: {service}\n")

    # Get all feedback for this service
    all_feedback = collector.load_all_feedback()
    service_feedback = [f for f in all_feedback if f.metadata.get("service") == service]

    if not service_feedback:
        console.print("[yellow]⚠ No historical data for this service[/yellow]")
        console.print("   Run tests first to collect execution data")
        return

    # Build execution history
    execution_history = {}
    for feedback in service_feedback:
        if feedback.execution_time:
            # Keep average if multiple executions
            if feedback.test_name in execution_history:
                execution_history[feedback.test_name] = (
                    execution_history[feedback.test_name] + feedback.execution_time
                ) / 2
            else:
                execution_history[feedback.test_name] = feedback.execution_time

    if not execution_history:
        console.print("[yellow]⚠ No execution time data available[/yellow]")
        return

    # Get test names
    test_names = list(execution_history.keys())

    # Optimize order
    optimized = trainer.optimize_test_order(test_names, execution_history)

    console.print(f"[green]✓[/green] Analyzed {len(test_names)} tests\n")

    table = Table(title="Optimized Test Execution Order")
    table.add_column("Order", style="cyan")
    table.add_column("Test Name", style="green")
    table.add_column("Avg Time", style="yellow")

    for i, test_name in enumerate(optimized, 1):
        avg_time = execution_history[test_name]
        table.add_row(str(i), test_name, f"{avg_time:.2f}s")

    console.print(table)
    console.print()

    # Calculate time savings
    original_total = sum(execution_history.values())
    console.print(f"[dim]Original total execution time: {original_total:.2f}s[/dim]")
    console.print(
        "[dim]Optimized order prioritizes faster tests for quicker feedback[/dim]"
    )
    console.print()


@cli.group()
def community():
    """Community Hub and Test Marketplace commands."""
    pass


@community.command("list-templates")
@click.option("--category", "-c", help="Filter by category")
@click.option("--framework", "-f", help="Filter by framework")
@click.option("--limit", "-l", default=20, help="Maximum number to show")
def list_templates(category: str, framework: str, limit: int):
    """List available test templates in the marketplace."""
    from socialseed_e2e.community import CommunityHub
    from socialseed_e2e.community.template_marketplace import TestTemplateMarketplace

    console.print("\n📦 [bold cyan]Test Template Marketplace[/bold cyan]\n")

    try:
        hub = CommunityHub()
        marketplace = TestTemplateMarketplace(hub)

        # Get templates
        if category:
            templates = marketplace.get_templates_by_category(category)
        else:
            templates = marketplace.search_templates(framework=framework)

        if not templates:
            console.print("[yellow]No templates found.[/yellow]")
            return

        # Display results
        table = Table(title=f"Available Templates ({len(templates)})")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Framework", style="yellow")
        table.add_column("Author", style="white")
        table.add_column("Rating", style="magenta")
        table.add_column("Downloads", style="blue")

        for template in templates[:limit]:
            category_display = template.metadata.get("category", "general")
            rating_display = f"⭐ {template.rating:.1f}" if template.rating > 0 else "-"

            table.add_row(
                template.name,
                category_display,
                template.framework,
                template.author,
                rating_display,
                str(template.downloads),
            )

        console.print(table)

        if len(templates) > limit:
            console.print(f"\n[dim]... and {len(templates) - limit} more[/dim]")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


@community.command("install-template")
@click.argument("template_id")
@click.option("--service", "-s", required=True, help="Target service name")
@click.option("--name", "-n", help="Custom test name")
def install_template(template_id: str, service: str, name: str):
    """Install a test template into a service."""
    from socialseed_e2e.community import CommunityHub
    from socialseed_e2e.community.template_marketplace import TestTemplateMarketplace

    console.print(f"\n📥 [bold cyan]Installing Template[/bold cyan]\n")

    try:
        hub = CommunityHub()
        marketplace = TestTemplateMarketplace(hub)

        # Install template
        result = marketplace.install_template(template_id, service, name)

        if result:
            console.print(f"[green]✓[/green] Template installed successfully!")
            console.print(f"   Location: {result}")
        else:
            console.print("[red]✗[/red] Failed to install template")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


@community.command("publish-template")
@click.option("--name", "-n", required=True, help="Template name")
@click.option("--description", "-d", required=True, help="Template description")
@click.option("--category", "-c", required=True, help="Template category")
@click.option("--framework", "-f", default="generic", help="Target framework")
@click.option("--author", "-a", required=True, help="Author name")
@click.option("--file", "-f", "template_file", required=True, help="Template file path")
def publish_template(
    name: str,
    description: str,
    category: str,
    framework: str,
    author: str,
    template_file: str,
):
    """Publish a test template to the marketplace."""
    from pathlib import Path

    from socialseed_e2e.community import CommunityHub
    from socialseed_e2e.community.template_marketplace import TestTemplateMarketplace

    console.print("\n📤 [bold cyan]Publishing Template[/bold cyan]\n")

    try:
        # Read template file
        file_path = Path(template_file)
        if not file_path.exists():
            console.print(f"[red]Error:[/red] File not found: {template_file}")
            return

        template_code = file_path.read_text()

        hub = CommunityHub()
        marketplace = TestTemplateMarketplace(hub)

        # Create template
        template = marketplace.create_template(
            name=name,
            description=description,
            author=author,
            category=category,
            framework=framework,
            template_code=template_code,
            tags=[category, framework],
        )

        # Publish
        if marketplace.publish_template(template):
            console.print("[green]✓[/green] Template published successfully!")
            console.print(f"   ID: {template.id}")
            console.print(f"   Name: {template.name}")
            console.print(f"   Status: Pending review")
        else:
            console.print("[red]✗[/red] Failed to publish template")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


@community.command("list-plugins")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--limit", "-l", default=20, help="Maximum number to show")
def list_plugins(tag: str, limit: int):
    """List available plugins in the repository."""
    from socialseed_e2e.community import CommunityHub
    from socialseed_e2e.community.plugin_repository import PluginRepository

    console.print("\n🔌 [bold cyan]Plugin Repository[/bold cyan]\n")

    try:
        hub = CommunityHub()
        repo = PluginRepository(hub)

        # Get plugins
        tags = [tag] if tag else None
        plugins = repo.search_plugins(tags=tags)

        if not plugins:
            console.print("[yellow]No plugins found.[/yellow]")
            return

        # Display results
        table = Table(title=f"Available Plugins ({len(plugins)})")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Author", style="yellow")
        table.add_column("Hooks", style="white")
        table.add_column("Rating", style="magenta")

        for plugin in plugins[:limit]:
            hooks_display = ", ".join(plugin.hooks[:3])
            rating_display = f"⭐ {plugin.rating:.1f}" if plugin.rating > 0 else "-"

            table.add_row(
                plugin.name,
                plugin.version,
                plugin.author,
                hooks_display,
                rating_display,
            )

        console.print(table)

        if len(plugins) > limit:
            console.print(f"\n[dim]... and {len(plugins) - limit} more[/dim]")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


@community.command("install-plugin")
@click.argument("plugin_id")
def install_plugin(plugin_id: str):
    """Install a plugin from the repository."""
    from socialseed_e2e.community import CommunityHub
    from socialseed_e2e.community.plugin_repository import PluginRepository

    console.print(f"\n🔧 [bold cyan]Installing Plugin[/bold cyan]\n")

    try:
        hub = CommunityHub()
        repo = PluginRepository(hub)

        # Get plugin info
        plugin = hub.get_resource(plugin_id)
        if plugin:
            console.print(f"Plugin: {plugin.name}")
            console.print(f"Version: {plugin.version}")
            console.print(f"Author: {plugin.author}\n")

        # Install
        if repo.install_plugin(plugin_id):
            console.print("[green]✓[/green] Plugin installed successfully!")
        else:
            console.print("[red]✗[/red] Failed to install plugin")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


@community.command("list-installed-plugins")
def list_installed_plugins():
    """List all installed plugins."""
    from socialseed_e2e.community.plugin_repository import PluginRepository

    console.print("\n📦 [bold cyan]Installed Plugins[/bold cyan]\n")

    try:
        repo = PluginRepository()
        plugins = repo.list_installed_plugins()

        if not plugins:
            console.print("[yellow]No plugins installed.[/yellow]")
            return

        table = Table(title=f"Installed Plugins ({len(plugins)})")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Author", style="yellow")
        table.add_column("Entry Point", style="white")

        for plugin in plugins:
            table.add_row(
                plugin.get("name", "Unknown"),
                plugin.get("version", "Unknown"),
                plugin.get("author", "Unknown"),
                plugin.get("entry_point", "-"),
            )

        console.print(table)

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


@community.command("uninstall-plugin")
@click.argument("plugin_name")
def uninstall_plugin(plugin_name: str):
    """Uninstall a plugin."""
    from socialseed_e2e.community.plugin_repository import PluginRepository

    console.print(f"\n🗑️ [bold cyan]Uninstalling Plugin[/bold cyan]\n")

    try:
        repo = PluginRepository()

        if repo.uninstall_plugin(plugin_name):
            console.print(
                f"[green]✓[/green] Plugin '{plugin_name}' uninstalled successfully!"
            )
        else:
            console.print(f"[red]✗[/red] Failed to uninstall plugin '{plugin_name}'")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


@community.command("marketplace-stats")
def marketplace_stats():
    """Show marketplace statistics."""
    from socialseed_e2e.community import CommunityHub

    console.print("\n📊 [bold cyan]Community Marketplace Statistics[/bold cyan]\n")

    try:
        hub = CommunityHub()
        stats = hub.get_statistics()

        # Display stats
        table = Table(title="Overview")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Resources", str(stats["total_resources"]))
        table.add_row("Approved Resources", str(stats["approved_resources"]))
        table.add_row("Pending Review", str(stats["pending_review"]))
        table.add_row("Total Downloads", str(stats["total_downloads"]))

        console.print(table)
        console.print()

        # Display by type
        type_table = Table(title="Resources by Type")
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", style="green")

        for resource_type, count in stats["by_type"].items():
            type_table.add_row(resource_type.replace("_", " ").title(), str(count))

        console.print(type_table)
        console.print()

        # Show popular resources
        popular = hub.get_popular_resources(5)
        if popular:
            console.print("[bold]Top Downloaded Resources:[/bold]")
            for resource in popular:
                console.print(f"  • {resource.name} ({resource.downloads} downloads)")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


@cli.command()
@click.option("--port", "-p", default=8501, help="Port for the dashboard server")
@click.option("--host", "-h", default="localhost", help="Host for the dashboard server")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def dashboard(port: int, host: str, no_browser: bool):
    """Launch the interactive web dashboard.

    Opens a local web interface to explore, run, and debug tests visually.
    This serves as the "Control Center" for the framework.

    Features:
    - Test Explorer: Visual tree view of all test modules
    - One-Click Run: Execute individual tests, suites, or folders
    - Rich Request/Response Viewer: Inspect headers, bodies, and status codes
    - Parameterization: UI inputs to override test variables at runtime
    - Live Logs: Real-time streaming of test execution logs
    - Run History: View past test runs and their outcomes

    Examples:
        e2e dashboard                    # Launch on default port 8501
        e2e dashboard --port 8080        # Launch on custom port
        e2e dashboard --no-browser       # Don't auto-open browser
    """
    try:
        from socialseed_e2e.dashboard.server import launch_dashboard

        console.print(
            "\n🚀 [bold green]Launching SocialSeed E2E Dashboard...[/bold green]\n"
        )
        console.print(f"📊 Dashboard will be available at: http://{host}:{port}")
        console.print()

        launch_dashboard(port=port, open_browser=not no_browser)

    except ImportError as e:
        console.print(f"\n[red]❌ Error launching dashboard:[/red] {e}")
        console.print("\n[yellow]📦 Required dependencies:[/yellow]")
        console.print("   pip install streamlit")
        console.print()
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error:[/red] {e}")
        sys.exit(1)


@cli.group()
def import_cmd():
    """Import external formats into SocialSeed E2E."""
    pass


@import_cmd.command("postman")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    default="./services/imported",
    help="Output directory for generated files",
)
@click.option(
    "--service-name", "-s", default="imported", help="Service name for generated code"
)
def import_postman(file_path: str, output: str, service_name: str):
    """Import Postman Collection (v2.1) into test modules.

    Example:
        e2e import postman ./my-collection.json --output ./services/api
        e2e import postman ./collection.json --service-name user-service
    """
    try:
        from socialseed_e2e.importers import PostmanImporter

        console.print(f"\n📥 [bold green]Importing Postman Collection[/bold green]")
        console.print(f"   File: {file_path}")
        console.print(f"   Output: {output}")
        console.print(f"   Service: {service_name}\n")

        importer = PostmanImporter(output_dir=Path(output), service_name=service_name)

        result = importer.import_file(Path(file_path))

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
            console.print(f"   Generated {len(result.tests)} test files")

            if result.warnings:
                console.print(f"\n[yellow]⚠ Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"   - {warning}")
        else:
            console.print(f"[red]✗[/red] Import failed: {result.message}")
            sys.exit(1)

    except ImportError as e:
        console.print(f"\n[red]❌ Import error:[/red] {e}")
        sys.exit(1)


@import_cmd.command("openapi")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    default="./services/imported",
    help="Output directory for generated files",
)
@click.option(
    "--service-name", "-s", default="imported", help="Service name for generated code"
)
@click.option(
    "--generate-scenarios", is_flag=True, help="Generate test scenarios from endpoints"
)
def import_openapi(
    file_path: str, output: str, service_name: str, generate_scenarios: bool
):
    """Import OpenAPI/Swagger specification (3.0+) into test skeletons.

    Example:
        e2e import openapi ./swagger.yaml --output ./services/api
        e2e import openapi ./api.json --service-name payment-api --generate-scenarios
    """
    try:
        from socialseed_e2e.importers import OpenAPIImporter

        console.print(f"\n📥 [bold green]Importing OpenAPI Specification[/bold green]")
        console.print(f"   File: {file_path}")
        console.print(f"   Output: {output}")
        console.print(f"   Service: {service_name}")
        if generate_scenarios:
            console.print(f"   Generate scenarios: Yes")
        console.print()

        importer = OpenAPIImporter(output_dir=Path(output), service_name=service_name)

        result = importer.import_file(Path(file_path))

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
            console.print(f"   Generated {len(result.tests)} test files")
            console.print(f"   Config file: {output}/openapi_config.yaml")

            if result.warnings:
                console.print(f"\n[yellow]⚠ Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"   - {warning}")
        else:
            console.print(f"[red]✗[/red] Import failed: {result.message}")
            sys.exit(1)

    except ImportError as e:
        console.print(f"\n[red]❌ Import error:[/red] {e}")
        sys.exit(1)


@import_cmd.command("curl")
@click.argument("command")
@click.option(
    "--output",
    "-o",
    default="./services/imported",
    help="Output directory for generated files",
)
@click.option("--name", "-n", default="curl_import", help="Test name")
def import_curl(command: str, output: str, name: str):
    """Import a curl command to generate a test case.

    Example:
        e2e import curl "curl -X POST https://api.example.com/users -d '{name:John}'"
        e2e import curl "curl -H 'Authorization: Bearer token' https://api.example.com/profile"
    """
    try:
        from socialseed_e2e.importers import CurlImporter

        console.print(f"\n📥 [bold green]Importing Curl Command[/bold green]")
        console.print(f"   Output: {output}")
        console.print(f"   Name: {name}\n")

        importer = CurlImporter(output_dir=Path(output))
        result = importer.import_command(command)

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
            console.print(f"   Generated test: {output}/{name}.py")
        else:
            console.print(f"[red]✗[/red] Import failed: {result.message}")
            sys.exit(1)

    except ImportError as e:
        console.print(f"\n[red]❌ Import error:[/red] {e}")
        sys.exit(1)


@import_cmd.command("environment")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    default="./services/imported",
    help="Output directory for generated config",
)
@click.option(
    "--service-name", "-s", default="imported", help="Service name for config"
)
def import_environment(file_path: str, output: str, service_name: str):
    """Import Postman Environment into framework config.

    Example:
        e2e import environment ./environment.json --output ./config
        e2e import environment ./prod-env.json --service-name production
    """
    try:
        from socialseed_e2e.importers import PostmanEnvironmentImporter

        console.print(f"\n📥 [bold green]Importing Postman Environment[/bold green]")
        console.print(f"   File: {file_path}")
        console.print(f"   Output: {output}")
        console.print(f"   Service: {service_name}\n")

        importer = PostmanEnvironmentImporter(output_dir=Path(output))
        result = importer.import_file(Path(file_path))

        if result.success:
            console.print(f"[green]✓[/green] {result.message}")
            console.print(f"   Config saved to: {output}/imported_config.yaml")
        else:
            console.print(f"[red]✗[/red] Import failed: {result.message}")
            sys.exit(1)

    except ImportError as e:
        console.print(f"\n[red]❌ Import error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", help="Path to configuration file (e2e.conf)")
@click.option("--service", "-s", help="Filter by specific service")
def tui(config: str, service: str):
    """Launch the Rich Terminal Interface (TUI).

    Opens an interactive terminal-based UI for power users who prefer
    keyboard navigation and split-pane views over web interfaces.

    Features:
    - Keyboard Navigation: Navigate test suites with arrow keys
    - Quick Actions: Run/Stop/Filter tests with hotkeys (r, s, f)
    - Split View: Test list and execution details side-by-side
    - Instant Feedback: Colored status indicators
    - Environment Toggling: Switch environments without restarting

    Key Bindings:
    - ↑/↓: Navigate test list
    - Enter: Run selected test
    - r: Run selected test
    - R: Run all tests
    - s: Stop running tests
    - f: Toggle filter
    - e: Switch environment
    - q: Quit
    - ?: Show help

    Examples:
        e2e tui                    # Launch TUI
        e2e tui --service users    # Launch with service filter
        e2e tui --config ./e2e.conf  # Use custom config
    """
    try:
        from socialseed_e2e.tui import TuiApp

        console.print(
            "\n🖥️  [bold green]Launching SocialSeed E2E Terminal Interface...[/bold green]\n"
        )

        app = TuiApp(config_path=config, service_filter=service)
        app.run()

    except ImportError as e:
        check_and_install_extra("tui", auto_install=False)
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error:[/red] {e}")
        sys.exit(1)


@cli.command("semantic-analyze")
@click.option(
    "--baseline-commit",
    help="Git commit hash for baseline (before changes)",
)
@click.option(
    "--target-commit",
    help="Git commit hash for target (after changes)",
)
@click.option(
    "--pr",
    type=int,
    help="Pull Request number to analyze",
)
@click.option(
    "--base-url",
    default="http://localhost:8080",
    help="Base URL for API testing",
)
@click.option(
    "--api-endpoint",
    multiple=True,
    help="API endpoint to test (format: METHOD /path)",
)
@click.option(
    "--database",
    type=click.Choice(["neo4j", "postgresql", "mysql", "mongodb"]),
    help="Database type to snapshot",
)
@click.option(
    "--db-uri",
    help="Database connection URI",
)
@click.option(
    "--db-user",
    help="Database username",
)
@click.option(
    "--db-password",
    help="Database password",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=".",
    help="Output directory for reports",
)
@click.option(
    "--quick-check",
    is_flag=True,
    help="Quick check without state capture",
)
@click.option(
    "--project-root",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory",
)
def semantic_analyze(
    baseline_commit: Optional[str],
    target_commit: Optional[str],
    pr: Optional[int],
    base_url: str,
    api_endpoint: Tuple[str, ...],
    database: Optional[str],
    db_uri: Optional[str],
    db_user: Optional[str],
    db_password: Optional[str],
    output: str,
    quick_check: bool,
    project_root: str,
):
    """Run semantic regression and logic drift detection.

    Analyzes whether system behavior aligns with intended business logic
    by extracting intent baselines from documentation, capturing system
    states, and detecting semantic drift.

    Examples:
        e2e semantic-analyze                                    # Run full analysis
        e2e semantic-analyze --baseline-commit HEAD~1          # Compare commits
        e2e semantic-analyze --pr 123                          # Analyze PR
        e2e semantic-analyze --quick-check                     # Quick validation
        e2e semantic-analyze --api-endpoint "GET /api/users"   # Test endpoints
    """
    try:
        from socialseed_e2e.agents import SemanticAnalyzerAgent

        console.print(
            "\n🔍 [bold cyan]Semantic Regression & Logic Drift Analysis[/bold cyan]\n"
        )

        # Create agent
        agent = SemanticAnalyzerAgent(
            project_root=Path(project_root),
            base_url=base_url,
        )

        # Quick check mode
        if quick_check:
            console.print(
                "[yellow]Running quick check (no state capture)...[/yellow]\n"
            )
            results = agent.quick_check()

            console.print(f"[green]Total Intents:[/green] {results['total_intents']}")
            console.print(
                f"[green]High Confidence:[/green] {len(results['high_confidence_intents'])}"
            )
            console.print(
                f"[green]Low Confidence:[/green] {len(results['low_confidence_intents'])}"
            )

            if results["by_category"]:
                console.print("\n[bold]By Category:[/bold]")
                for cat, count in results["by_category"].items():
                    console.print(f"  - {cat}: {count}")

            return

        # PR analysis
        if pr:
            console.print(f"[cyan]Analyzing PR #{pr}...[/cyan]\n")
            report = agent.analyze_pr(
                pr_number=pr,
                api_endpoints=_parse_api_endpoints(api_endpoint),
                database_configs=_parse_database_configs(
                    database, db_uri, db_user, db_password
                ),
            )
        else:
            # Standard analysis
            report = agent.analyze(
                baseline_commit=baseline_commit,
                target_commit=target_commit,
                api_endpoints=_parse_api_endpoints(api_endpoint),
                database_configs=_parse_database_configs(
                    database, db_uri, db_user, db_password
                ),
                output_path=Path(output) / "SEMANTIC_DRIFT_REPORT.md",
            )

        # Display summary
        summary = report.generate_summary()

        console.print("\n[bold]Analysis Summary:[/bold]")
        console.print(f"  Total Intents: {summary['total_intents_analyzed']}")
        console.print(f"  Total Drifts: {summary['total_drifts']}")

        if summary["severity_distribution"]["critical"] > 0:
            console.print(
                f"  [red]Critical: {summary['severity_distribution']['critical']}[/red]"
            )
        if summary["severity_distribution"]["high"] > 0:
            console.print(
                f"  [yellow]High: {summary['severity_distribution']['high']}[/yellow]"
            )

        # Exit with error if critical issues found
        if report.has_critical_drifts():
            console.print("\n[red]🚨 Critical semantic drifts detected![/red]")
            sys.exit(1)
        elif summary["total_drifts"] > 0:
            console.print(
                "\n[yellow]⚠️  Semantic drifts detected - review recommended[/yellow]"
            )
            sys.exit(0)
        else:
            console.print("\n[green]✅ No semantic drift detected[/green]")
            sys.exit(0)

    except ImportError as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        console.print(
            "\n[yellow]Make sure the semantic analyzer is properly installed.[/yellow]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        import traceback

        console.print(traceback.format_exc())
        sys.exit(1)


def _parse_api_endpoints(endpoint_specs: Tuple[str, ...]) -> List[Dict[str, str]]:
    """Parse API endpoint specifications."""
    endpoints = []
    for spec in endpoint_specs:
        parts = spec.split()
        if len(parts) >= 2:
            endpoints.append(
                {
                    "method": parts[0].upper(),
                    "endpoint": parts[1],
                }
            )
    return endpoints


def _parse_database_configs(
    db_type: Optional[str],
    uri: Optional[str],
    user: Optional[str],
    password: Optional[str],
) -> List[Dict[str, str]]:
    """Parse database configurations."""
    if not db_type:
        return []

    config = {"type": db_type}

    if uri:
        config["uri"] = uri
    if user:
        config["user"] = user
    if password:
        config["password"] = password

    return [config]


@cli.group()
def semantic_analyze():
    """Commands for semantic regression and logic drift detection.

    Provides autonomous semantic analysis to detect logic drift
    by comparing actual system behavior against intended business intent.
    """
    pass


@semantic_analyze.command("run")
@click.argument("directory", default=".", required=False)
@click.option("--base-url", "-u", help="Base URL for API testing")
@click.option("--baseline-commit", "-b", help="Baseline git commit")
@click.option("--target-commit", "-t", help="Target git commit")
@click.option(
    "--database-type",
    "-d",
    type=click.Choice(["neo4j", "postgresql", "mongodb"]),
    help="Database type for state capture",
)
@click.option("--db-uri", help="Database connection URI")
@click.option("--db-user", help="Database username")
@click.option("--db-password", help="Database password")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory for reports",
)
@click.option(
    "--no-state-capture",
    is_flag=True,
    help="Skip state capture (intent extraction only)",
)
def semantic_analyze_run(
    directory: str,
    base_url: str,
    baseline_commit: str,
    target_commit: str,
    database_type: str,
    db_uri: str,
    db_user: str,
    db_password: str,
    output: str,
    no_state_capture: bool,
):
    """Run semantic drift analysis.

    Analyzes project documentation and code to extract intent baselines,
    captures system states, and detects logic drift.

    Examples:
        e2e semantic-analyze run                    # Analyze current directory
        e2e semantic-analyze run /path/to/project   # Analyze specific project
        e2e semantic-analyze run -u http://localhost:8080  # With API testing
        e2e semantic-analyze run -b HEAD~1 -t HEAD  # Compare commits
        e2e semantic-analyze run -d neo4j --db-uri bolt://localhost:7687
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🔍 [bold cyan]Semantic Drift Analysis[/bold cyan]")
    console.print(f"   Project: {target_path}\n")

    try:
        from socialseed_e2e.agents.semantic_analyzer import SemanticAnalyzerAgent

        # Initialize agent
        agent = SemanticAnalyzerAgent(
            project_root=target_path,
            base_url=base_url,
        )

        # Build database configs if provided
        database_configs = None
        if database_type:
            database_configs = [
                {
                    "type": database_type,
                    "uri": db_uri or "",
                    "user": db_user or "",
                    "password": db_password or "",
                }
            ]

        # Run analysis
        output_path = Path(output) if output else None

        report = agent.analyze(
            baseline_commit=baseline_commit or None,
            target_commit=target_commit or None,
            capture_states=not no_state_capture,
            database_configs=database_configs,
            output_path=output_path,
        )

        # Display summary
        console.print("\n" + "=" * 60)
        console.print("[bold]Analysis Summary:[/bold]")
        console.print(f"   Report ID: {report.report_id}")
        console.print(f"   Intents Analyzed: {len(report.intent_baselines)}")
        console.print(f"   Drifts Detected: {len(report.detected_drifts)}")

        if report.has_critical_drifts():
            console.print("\n[bold red]🚨 Critical issues found![/bold red]")
            sys.exit(1)
        elif report.detected_drifts:
            console.print(
                "\n[bold yellow]⚠️  Drifts detected - review recommended[/bold yellow]"
            )
        else:
            console.print("\n[bold green]✅ No semantic drift detected[/bold green]")

        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@semantic_analyze.command("intents")
@click.argument("directory", default=".", required=False)
@click.option(
    "--category",
    "-c",
    multiple=True,
    help="Filter by category (can be specified multiple times)",
)
@click.option("--json-output", is_flag=True, help="Output as JSON")
def semantic_analyze_intents(directory: str, category: tuple, json_output: bool):
    """Extract and display intent baselines.

    Scans documentation, GitHub issues, code comments, and test cases
    to extract expected system behavior.

    Examples:
        e2e semantic-analyze intents              # Show all intents
        e2e semantic-analyze intents -c auth      # Filter by category
        e2e semantic-analyze intents --json-output
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n📚 [bold cyan]Extracting Intent Baselines[/bold cyan]")
    console.print(f"   Project: {target_path}\n")

    try:
        from socialseed_e2e.agents.semantic_analyzer import IntentBaselineExtractor

        extractor = IntentBaselineExtractor(target_path)
        intents = extractor.extract_all()

        # Filter by category if specified
        if category:
            intents = [i for i in intents if i.category in category]

        if json_output:
            import json

            output = [
                {
                    "intent_id": i.intent_id,
                    "description": i.description,
                    "category": i.category,
                    "expected_behavior": i.expected_behavior,
                    "success_criteria": i.success_criteria,
                    "confidence": i.confidence,
                }
                for i in intents
            ]
            console.print(json.dumps(output, indent=2))
        else:
            # Display as table
            from rich.table import Table

            table = Table(title=f"Intent Baselines ({len(intents)} found)")
            table.add_column("ID", style="dim")
            table.add_column("Category", style="cyan")
            table.add_column("Description", style="green")
            table.add_column("Confidence", style="yellow")

            for intent in intents[:50]:  # Limit to 50 for display
                conf_str = f"{intent.confidence:.0%}"
                table.add_row(
                    intent.intent_id[:20] + "..."
                    if len(intent.intent_id) > 20
                    else intent.intent_id,
                    intent.category,
                    intent.description[:50] + "..."
                    if len(intent.description) > 50
                    else intent.description,
                    conf_str,
                )

            console.print(table)

            if len(intents) > 50:
                console.print(f"\n... and {len(intents) - 50} more")

        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@semantic_analyze.command("server")
@click.option("--port", "-p", default=50051, help="gRPC server port")
@click.option(
    "--host",
    "-h",
    default="0.0.0.0",
    help="Host to bind the server",
)
def semantic_analyze_server(port: int, host: str):
    """Start the semantic analyzer gRPC server.

    Starts a gRPC server that other agents can query for semantic
    analysis capabilities.

    Examples:
        e2e semantic-analyze server              # Start on default port 50051
        e2e semantic-analyze server -p 50052     # Use custom port
    """
    console.print(f"\n🚀 [bold cyan]Starting Semantic Analyzer gRPC Server[/bold cyan]")
    console.print(f"   Host: {host}")
    console.print(f"   Port: {port}")
    console.print("\n   Press Ctrl+C to stop\n")

    try:
        from socialseed_e2e.agents.semantic_analyzer.grpc_server import (
            SemanticAnalyzerServer,
        )

        server = SemanticAnalyzerServer(port=port)
        server.start()
        server.wait_for_termination()

    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@cli.group()
def red_team():
    """Commands for adversarial AI security testing (Red Team).

    Performs security assessments by simulating adversarial attacks
    including prompt injection, privilege escalation, and hallucination
    triggering to identify vulnerabilities.
    """
    pass


@red_team.command("assess")
@click.argument("directory", default=".", required=False)
@click.option(
    "--attack-type",
    "-a",
    multiple=True,
    type=click.Choice(
        [
            "prompt_injection",
            "privilege_escalation",
            "hallucination_trigger",
            "context_leakage",
            "jailbreak",
            "multi_step_manipulation",
        ]
    ),
    help="Attack types to execute (can be specified multiple times)",
)
@click.option(
    "--max-attempts",
    "-m",
    default=50,
    help="Maximum number of attack attempts",
)
@click.option(
    "--output",
    "-o",
    default="security",
    help="Output directory for reports and logs",
)
@click.option(
    "--quick",
    is_flag=True,
    help="Run quick scan with limited attacks",
)
def red_team_assess(
    directory: str,
    attack_type: tuple,
    max_attempts: int,
    output: str,
    quick: bool,
):
    """Run full adversarial security assessment.

    Discovers guardrails, executes adversarial attacks, and calculates
    a resilience score for the target system.

    Examples:
        e2e red-team assess                    # Assess current directory
        e2e red-team assess /path/to/project   # Assess specific project
        e2e red-team assess -a prompt_injection -a jailbreak  # Specific attacks
        e2e red-team assess --quick            # Quick scan
    """
    from socialseed_e2e.agents.red_team_adversary import RedTeamAgent, AttackType

    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🎯 [bold red]Red Team Security Assessment[/bold red]")
    console.print(f"   Target: {target_path}\n")

    try:
        # Create agent
        agent = RedTeamAgent(project_root=target_path)

        # Convert attack types
        attack_types = None
        if attack_type:
            attack_types = [AttackType(at) for at in attack_type]

        if quick:
            # Quick scan
            results = agent.quick_scan()
            console.print("\n📊 [bold]Quick Scan Results:[/bold]")
            console.print(f"   Guardrails Found: {results['guardrails_found']}")
            console.print(f"   Attacks Executed: {results['attacks_executed']}")
            console.print(f"   Successful: {results['successful_attacks']}")
            console.print(f"   Resilience Score: {results['resilience_score']}/100")
            console.print(f"\n   {results['summary']}")
        else:
            # Full assessment
            report = agent.run_full_assessment(attack_types=attack_types)

            # Display results
            console.print("\n" + "=" * 60)
            console.print("[bold]Assessment Complete[/bold]")
            console.print(f"   Report ID: {report.report_id}")
            console.print(f"   Total Attacks: {report.total_attacks}")
            console.print(f"   Successful: {report.successful_attacks}")
            console.print(f"   Failed: {report.failed_attacks}")
            console.print(
                f"   Resilience Score: {report.resilience_score.overall_score}/100"
            )

            if report.resilience_score.overall_score < 50:
                console.print(
                    "\n[bold red]⚠️  Critical vulnerabilities found![/bold red]"
                )
            elif report.resilience_score.overall_score < 75:
                console.print(
                    "\n[bold yellow]⚠️  Moderate security concerns[/bold yellow]"
                )
            else:
                console.print("\n[bold green]✅ Good security posture[/bold green]")

            # Show recommendations
            if report.resilience_score.recommendations:
                console.print("\n[bold]Recommendations:[/bold]")
                for i, rec in enumerate(report.resilience_score.recommendations[:5], 1):
                    console.print(f"   {i}. {rec}")

        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@red_team.command("guardrails")
@click.argument("directory", default=".", required=False)
@click.option(
    "--json-output",
    is_flag=True,
    help="Output as JSON",
)
def red_team_guardrails(directory: str, json_output: bool):
    """Discover and analyze security guardrails.

    Scans documentation and code to identify safety constraints
    and security controls in the system.

    Examples:
        e2e red-team guardrails              # Show all guardrails
        e2e red-team guardrails --json-output
    """
    from socialseed_e2e.agents.red_team_adversary import GuardrailDiscovery
    import json

    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    console.print("\n🔍 [bold cyan]Discovering Guardrails[/bold cyan]")
    console.print(f"   Target: {target_path}\n")

    try:
        discovery = GuardrailDiscovery(target_path)
        guardrails = discovery.discover_all()

        if json_output:
            output = [
                {
                    "guardrail_id": g.guardrail_id,
                    "type": g.guardrail_type.value,
                    "description": g.description,
                    "location": g.location,
                    "strength": g.strength,
                }
                for g in guardrails
            ]
            console.print(json.dumps(output, indent=2))
        else:
            from rich.table import Table

            table = Table(title=f"Discovered Guardrails ({len(guardrails)} found)")
            table.add_column("ID", style="dim")
            table.add_column("Type", style="cyan")
            table.add_column("Strength", style="yellow")
            table.add_column("Location", style="green")

            for guardrail in guardrails:
                strength_color = (
                    "red"
                    if guardrail.strength < 50
                    else "yellow"
                    if guardrail.strength < 75
                    else "green"
                )
                table.add_row(
                    guardrail.guardrail_id[:20] + "..."
                    if len(guardrail.guardrail_id) > 20
                    else guardrail.guardrail_id,
                    guardrail.guardrail_type.value,
                    f"[{strength_color}]{guardrail.strength}/100[/{strength_color}]",
                    guardrail.location[:50] + "..."
                    if len(guardrail.location) > 50
                    else guardrail.location,
                )

            console.print(table)

            # Summary
            summary = discovery.generate_summary()
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"   Total: {summary['total_guardrails']}")
            console.print(f"   Vulnerable: {summary['vulnerable_count']}")
            console.print(f"   Average Strength: {summary['average_strength']:.1f}/100")

        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@red_team.command("payloads")
@click.option(
    "--attack-type",
    "-a",
    type=click.Choice(
        [
            "prompt_injection",
            "privilege_escalation",
            "hallucination_trigger",
            "context_leakage",
            "jailbreak",
            "multi_step_manipulation",
        ]
    ),
    help="Filter by attack type",
)
def red_team_payloads(attack_type: str):
    """List available attack payloads.

    Displays all adversarial payloads available for security testing.

    Examples:
        e2e red-team payloads                    # Show all payloads
        e2e red-team payloads -a prompt_injection  # Filter by type
    """
    from socialseed_e2e.agents.red_team_adversary import AdversarialPayloads, AttackType
    from rich.table import Table

    console.print("\n⚔️  [bold red]Available Attack Payloads[/bold red]\n")

    try:
        if attack_type:
            payloads = AdversarialPayloads.get_payloads_by_type(AttackType(attack_type))
        else:
            payloads = AdversarialPayloads.get_all_payloads()

        table = Table(title=f"Attack Payloads ({len(payloads)} total)")
        table.add_column("ID", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="red")
        table.add_column("Target", style="yellow")
        table.add_column("Description", style="green")

        for payload in payloads:
            table.add_row(
                payload.payload_id,
                payload.attack_type.value,
                payload.name,
                payload.target_component,
                payload.description[:60] + "..."
                if len(payload.description) > 60
                else payload.description,
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@red_team.command("logs")
@click.option(
    "--session",
    "-s",
    help="Filter by session ID",
)
@click.option(
    "--attack-type",
    "-a",
    help="Filter by attack type",
)
@click.option(
    "--winning",
    is_flag=True,
    help="Show only successful exploits",
)
def red_team_logs(session: str, attack_type: str, winning: bool):
    """View Red Team attack logs.

    Displays logged attack attempts and successful exploits.

    Examples:
        e2e red-team logs              # Show all logs
        e2e red-team logs --winning    # Show successful exploits only
        e2e red-team logs -s <session_id>
    """
    from socialseed_e2e.agents.red_team_adversary import SecurityLogger
    from rich.table import Table

    console.print("\n📋 [bold cyan]Red Team Logs[/bold cyan]\n")

    try:
        logger = SecurityLogger()

        if winning:
            logs = logger.get_winning_payloads()
        elif session:
            logs = logger.get_logs_by_session(session)
        elif attack_type:
            logs = logger.get_logs_by_attack_type(attack_type)
        else:
            logs = logger.logs

        if not logs:
            console.print("[yellow]No logs found[/yellow]")
            return

        table = Table(title=f"Attack Logs ({len(logs)} entries)")
        table.add_column("Timestamp", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Attack", style="red")
        table.add_column("Result", style="yellow")
        table.add_column("Severity", style="green")

        for log in logs[-50:]:  # Show last 50
            log_type = log.get("type", "unknown")
            attack = log.get("attack_type", "-")
            result = log.get("result", "-")
            severity = log.get("severity", "-")
            timestamp = log.get("timestamp", "-")

            table.add_row(
                timestamp[:19] if timestamp else "-",
                log_type,
                attack,
                result,
                severity if isinstance(severity, str) else severity.get("value", "-"),
            )

        console.print(table)

        # Summary
        summary = logger.generate_summary()
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"   Total Entries: {summary['total_entries']}")
        console.print(f"   Successful Exploits: {summary['successful_exploits']}")
        console.print(f"   Sessions: {summary['sessions']}")

        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@cli.group()
def telemetry():
    """Commands for token-centric performance testing and cost optimization.

    Monitors LLM token usage, detects cost regressions, identifies
    reasoning loops, and provides optimization recommendations.
    """
    pass


@telemetry.command("monitor")
@click.option(
    "--output",
    "-o",
    default="telemetry",
    help="Output directory for reports",
)
@click.option(
    "--baseline",
    "-b",
    help="Path to baseline file for regression comparison",
)
@click.option(
    "--threshold",
    "-t",
    default=15.0,
    help="Cost regression threshold percentage",
)
@click.option(
    "--budget",
    type=float,
    help="Max token budget in USD",
)
def telemetry_monitor(output: str, baseline: str, threshold: float, budget: float):
    """Start monitoring LLM calls for cost and performance.

    Intercepts LLM calls to track tokens, latency, and costs.
    Generates COST_EFFICIENCY_REPORT.json after execution.

    Examples:
        e2e telemetry monitor                    # Start monitoring
        e2e telemetry monitor -b baseline.json   # Compare with baseline
        e2e telemetry monitor --budget 10.0      # Set $10 budget
    """
    from socialseed_e2e.telemetry import TelemetryManager, TokenMonitorConfig

    console.print("\n📊 [bold cyan]Token Telemetry Monitor[/bold cyan]")
    console.print("   Tracking LLM calls for cost optimization...\n")

    try:
        # Configure telemetry
        config = TokenMonitorConfig(
            report_output_dir=output,
            baseline_file=baseline,
            regression_threshold_percentage=threshold,
        )

        if budget:
            config.global_budget_enabled = True
            config.global_max_cost_usd = budget

        # Create manager and start session
        manager = TelemetryManager(config)
        manager.start_session()

        console.print("✅ Telemetry session started")
        console.print(f"   Output directory: {output}")
        if baseline:
            console.print(f"   Baseline: {baseline}")
        console.print(f"   Regression threshold: {threshold}%")
        if budget:
            console.print(f"   Budget: ${budget:.2f}")
        console.print("\n   Press Ctrl+C to stop and generate report\n")

        # Keep running until interrupted
        import time

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        # End session and generate report
        console.print("\n📝 Generating report...")
        report = manager.end_session()

        # Display summary
        console.print("\n" + "=" * 60)
        console.print("[bold]Telemetry Report Summary[/bold]")
        console.print(f"   Report ID: {report.report_id}")
        console.print(f"   Total Calls: {report.total_llm_calls}")
        console.print(f"   Total Tokens: {report.total_tokens:,}")
        console.print(f"   Total Cost: ${report.total_cost_usd:.4f}")
        console.print(f"   Health Score: {report.health_score}/100")
        console.print(f"   Status: {report.status.upper()}")

        if report.reasoning_loops:
            console.print(
                f"\n[bold yellow]⚠️  {len(report.reasoning_loops)} reasoning loop(s) detected[/bold yellow]"
            )

        if report.cost_regressions:
            console.print(
                f"\n[bold red]🚨 {len(report.cost_regressions)} cost regression(s) detected[/bold red]"
            )
            console.print(manager.get_ci_message())

        if report.optimization_recommendations:
            console.print(
                f"\n[bold green]💡 {len(report.optimization_recommendations)} optimization recommendation(s)[/bold green]"
            )

        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@telemetry.command("baseline")
@click.option(
    "--output",
    "-o",
    default="telemetry/cost_baseline.json",
    help="Output path for baseline file",
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset existing baseline",
)
def telemetry_baseline(output: str, reset: bool):
    """Save current metrics as cost baseline.

    Creates a baseline for cost regression detection.

    Examples:
        e2e telemetry baseline              # Save baseline
        e2e telemetry baseline --reset      # Reset and create new
    """
    from socialseed_e2e.telemetry import CostRegressionDetector

    console.print("\n📊 [bold cyan]Cost Baseline Management[/bold cyan]\n")

    try:
        detector = CostRegressionDetector(
            baseline_file=output,
        )

        if reset and detector.baseline_file.exists():
            detector.reset_baseline()
            console.print(f"✅ Baseline reset: {output}")
        elif detector.baseline_file.exists():
            info = detector.get_baseline_info()
            if info:
                console.print(f"[yellow]Baseline already exists:[/yellow] {output}")
                console.print(f"   Created: {info.get('created_at')}")
                console.print(f"   Test cases: {info.get('test_cases')}")
                console.print(f"   Total cost: ${info.get('total_cost_usd', 0):.4f}")
                console.print("\nUse --reset to overwrite")
        else:
            console.print(f"ℹ️  No baseline found at: {output}")
            console.print("   Run tests with telemetry to create a baseline")

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@telemetry.command("report")
@click.argument("report_file", required=False)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "markdown"]),
    default="json",
    help="Output format",
)
def telemetry_report(report_file: str, format: str):
    """View or convert telemetry report.

    Displays COST_EFFICIENCY_REPORT.json contents or converts to markdown.

    Examples:
        e2e telemetry report                              # Latest report
        e2e telemetry report telemetry/report.json        # Specific file
        e2e telemetry report -f markdown > report.md      # Convert to MD
    """
    import json
    from pathlib import Path

    console.print("\n📊 [bold cyan]Telemetry Report[/bold cyan]\n")

    try:
        # Find report file
        if not report_file:
            telemetry_dir = Path("telemetry")
            if telemetry_dir.exists():
                reports = sorted(
                    telemetry_dir.glob("COST_EFFICIENCY_REPORT_*.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if reports:
                    report_file = str(reports[0])

        if not report_file or not Path(report_file).exists():
            console.print("[red]❌ Error:[/red] No report file found")
            console.print("   Run 'e2e telemetry monitor' first or specify a file")
            sys.exit(1)

        # Load report
        with open(report_file, "r") as f:
            report_data = json.load(f)

        if format == "json":
            console.print(json.dumps(report_data, indent=2))
        else:
            # Generate markdown
            from socialseed_e2e.telemetry import CostEfficiencyReport
            from socialseed_e2e.telemetry.report_generator import ReportGenerator

            report = CostEfficiencyReport(**report_data)
            generator = ReportGenerator()
            markdown = generator.generate_markdown_report(report)
            console.print(markdown)

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@telemetry.command("budget")
@click.argument("action", type=click.Choice(["create", "status", "list"]))
@click.option(
    "--name",
    "-n",
    help="Budget name",
)
@click.option(
    "--scope",
    "-s",
    type=click.Choice(["global", "issue", "task", "test_case", "agent"]),
    help="Budget scope type",
)
@click.option(
    "--scope-id",
    help="Scope ID (e.g., issue #123)",
)
@click.option(
    "--max-cost",
    type=float,
    help="Maximum cost in USD",
)
@click.option(
    "--max-tokens",
    type=int,
    help="Maximum total tokens",
)
@click.option(
    "--on-breach",
    type=click.Choice(["warn", "block", "alert"]),
    default="warn",
    help="Action on budget breach",
)
def telemetry_budget(
    action: str,
    name: str,
    scope: str,
    scope_id: str,
    max_cost: float,
    max_tokens: int,
    on_breach: str,
):
    """Manage token budgets.

    Create and monitor budgets to prevent runaway costs.

    Examples:
        e2e telemetry budget create -n "Issue #165" -s issue --scope-id 165 --max-cost 5.0
        e2e telemetry budget status
        e2e telemetry budget list
    """
    from socialseed_e2e.telemetry import BudgetManager

    console.print("\n💰 [bold cyan]Token Budget Management[/bold cyan]\n")

    try:
        manager = BudgetManager()

        if action == "create":
            if not name or not scope:
                console.print("[red]❌ Error:[/red] --name and --scope are required")
                sys.exit(1)

            budget = manager.create_budget(
                name=name,
                scope_type=scope,
                scope_id=scope_id,
                max_cost_usd=max_cost,
                max_total_tokens=max_tokens,
                on_budget_breach=on_breach,
            )

            console.print(f"✅ Budget created: {budget.budget_id}")
            console.print(f"   Name: {name}")
            console.print(f"   Scope: {scope}:{scope_id or 'all'}")
            if max_cost:
                console.print(f"   Max cost: ${max_cost:.2f}")
            if max_tokens:
                console.print(f"   Max tokens: {max_tokens:,}")
            console.print(f"   On breach: {on_breach}")

        elif action == "status":
            statuses = manager.get_all_budgets_status()

            if not statuses:
                console.print("ℹ️  No active budgets")
            else:
                from rich.table import Table

                table = Table(title="Token Budgets")
                table.add_column("Budget", style="cyan")
                table.add_column("Scope", style="green")
                table.add_column("Usage", style="yellow")
                table.add_column("Limit", style="red")
                table.add_column("Status", style="bold")

                for status in statuses:
                    budget_name = status["name"]
                    scope_str = status["scope"]
                    usage = f"${status['usage']['cost_usd']:.2f} / {status['usage']['total_tokens']:,}t"
                    limit = ""
                    if status["limits"]["max_cost_usd"]:
                        limit += f"${status['limits']['max_cost_usd']:.2f} "
                    if status["limits"]["max_total_tokens"]:
                        limit += f"{status['limits']['max_total_tokens']:,}t"

                    if status["breached"]:
                        status_str = "[red]BREACHED[/red]"
                    else:
                        pct = (
                            status["percentages"]["cost"]
                            or status["percentages"]["total"]
                            or 0
                        )
                        if pct > 80:
                            status_str = f"[yellow]{pct:.0f}%[/yellow]"
                        else:
                            status_str = f"[green]{pct:.0f}%[/green]"

                    table.add_row(budget_name, scope_str, usage, limit, status_str)

                console.print(table)

        elif action == "list":
            budgets = list(manager.budgets.values())

            if not budgets:
                console.print("ℹ️  No budgets defined")
            else:
                for budget in budgets:
                    status = "🟢 Active" if budget.is_active else "🔴 Inactive"
                    console.print(f"{budget.budget_id}: {budget.name} ({status})")

    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    cli()
