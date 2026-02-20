"""Init command for socialseed-e2e.

This module provides the init command functionality.
"""

import click
from rich.console import Console

console = Console()


@click.command(name="init")
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--demo", is_flag=True, help="Include demo API and example services")
def init_command(directory: str, force: bool, demo: bool) -> None:
    """Initialize a new E2E project."""
    from pathlib import Path

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

    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            console.print(
                f"  [green]✓[/green] Created: {dir_path.relative_to(target_path)}"
            )
        else:
            console.print(
                f"  [yellow]⚠[/yellow] Already exists: {dir_path.relative_to(target_path)}"
            )

    console.print("\n[bold green]✅ Project initialized successfully![/bold green]\n")


# Registration function
def get_command():
    return init_command


def get_name():
    return "init"


def get_help():
    return "Initialize a new E2E project"
