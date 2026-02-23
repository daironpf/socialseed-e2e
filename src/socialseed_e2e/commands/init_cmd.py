"""Init command for socialseed-e2e.

This module provides the init command functionality.
"""

from pathlib import Path

import click
from rich.console import Console

console = Console()


class InitManager:
    """Handles project initialization (Single Responsibility)."""

    DEFAULT_IGNORE = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.e2e/

# OS
.DS_Store
Thumbs.db

# socialseed-e2e
e2e_reports/
"""

    DEFAULT_REQUIREMENTS = """# socialseed-e2e requirements
socialseed-e2e>=0.1.0
playwright>=1.40.0
pydantic>=2.0.0
email-validator>=2.0.0
pyyaml>=6.0
rich>=13.0.0
jinja2>=3.1.0
click>=8.0.0

# Optional: Flask for demo APIs
flask>=2.0.0

# Optional: For vector embeddings and RAG
numpy>=1.21.0
scikit-learn>=1.0.0
sentence-transformers>=2.2.0
"""

    AGENT_DOCS = """# AI Agent Documentation

This directory contains context for AI agents working on this project.

## Project Structure

```
project/
├── services/       # Service pages and tests
├── tests/          # Test files
├── demos/          # Demo APIs
├── .e2e/          # E2E framework data
└── e2e.conf       # E2E configuration
```

## Key Commands

- `e2e run` - Run all tests
- `e2e run --service <name>` - Run specific service tests
- `e2e manifest <path>` - Generate project manifest
- `e2e discover` - Generate discovery report

## Configuration

Edit `e2e.conf` to configure services and endpoints.
"""

    def __init__(self, target_path: Path, force: bool = False, demo: bool = False):
        self.target_path = target_path
        self.force = force
        self.demo = demo

    def initialize(self) -> None:
        """Initialize the project."""
        self._create_directories()
        self._create_e2e_conf()
        self._create_gitignore()
        self._create_requirements()
        self._create_agent_docs()

    def _create_directories(self) -> None:
        """Create directory structure."""
        dirs = [
            self.target_path / "services",
            self.target_path / "tests",
            self.target_path / ".github" / "workflows",
        ]

        for dir_path in dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                console.print(
                    f"  [green]✓[/green] Created: {dir_path.relative_to(self.target_path)}"
                )
            else:
                console.print(
                    f"  [yellow]⚠[/yellow] Already exists: {dir_path.relative_to(self.target_path)}"
                )

    def _create_e2e_conf(self) -> None:
        """Create e2e.conf file."""
        config_path = self.target_path / "e2e.conf"

        if config_path.exists() and not self.force:
            console.print("  [yellow]⚠[/yellow] Already exists: e2e.conf")
            return

        config_content = """# SocialSeed E2E Configuration
# Documentation: https://github.com/daironpf/socialseed-e2e

general:
  environment: dev
  timeout: 30000
  verbose: true
  user_agent: socialseed-e2e/1.0
  project_name: my-project

services: {}
"""
        config_path.write_text(config_content)
        console.print("  [green]✓[/green] Created: e2e.conf")

    def _create_gitignore(self) -> None:
        """Create .gitignore file."""
        gitignore_path = self.target_path / ".gitignore"

        if gitignore_path.exists() and not self.force:
            console.print("  [yellow]⚠[/yellow] Already exists: .gitignore")
            return

        gitignore_path.write_text(self.DEFAULT_IGNORE)
        console.print("  [green]✓[/green] Created: .gitignore")

    def _create_requirements(self) -> None:
        """Create requirements.txt file."""
        req_path = self.target_path / "requirements.txt"

        if req_path.exists() and not self.force:
            console.print("  [yellow]⚠[/yellow] Already exists: requirements.txt")
            return

        req_path.write_text(self.DEFAULT_REQUIREMENTS)
        console.print("  [green]✓[/green] Created: requirements.txt")

    def _create_agent_docs(self) -> None:
        """Create .agent directory with AI documentation."""
        agent_dir = self.target_path / ".agent"

        if not agent_dir.exists():
            agent_dir.mkdir(parents=True, exist_ok=True)
            console.print("  [green]✓[/green] Created: .agent/")

        readme_path = agent_dir / "README.md"
        if not readme_path.exists() or self.force:
            readme_path.write_text(self.AGENT_DOCS)
            console.print("  [green]✓[/green] Created: .agent/README.md")


@click.command(name="init")
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--demo", is_flag=True, help="Include demo API and example services")
def init_command(directory: str, force: bool, demo: bool) -> None:
    """Initialize a new E2E project."""
    target_path = Path(directory).resolve()

    console.print(
        f"\n🌱 [bold green]Initializing E2E project at:[/bold green] {target_path}\n"
    )

    manager = InitManager(target_path, force, demo)
    manager.initialize()

    console.print("\n[bold green]✅ Project initialized successfully![/bold green]\n")
    console.print("[bold]Next steps:[/bold]")
    console.print(
        "  1. Install dependencies: [cyan]pip install -r requirements.txt[/cyan]"
    )
    console.print("  2. Install demo: [cyan]e2e install-demo[/cyan]")
    console.print("  3. Run tests: [cyan]e2e run[/cyan]\n")


# Registration function
def get_command():
    return init_command


def get_name():
    return "init"


def get_help():
    return "Initialize a new E2E project"
