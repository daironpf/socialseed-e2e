"""Template command for socialseed-e2e CLI.

This is a template file for creating new CLI commands.
Copy this file and modify it to create new commands.

Usage:
    1. Copy this file to commands/<your_command>_cmd.py
    2. Replace "template" with your command name
    3. Implement the command logic
    4. Register in cli.py
"""

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command(name="template")
@click.argument("argument", required=False)
@click.option("--option", "-o", help="Description of the option")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--count", "-c", default=10, type=int, help="Number of items (default: 10)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
def template_command(
    argument: str, option: str, verbose: bool, count: int, format: str
) -> None:
    """Short description of what the command does.

    Longer description if needed. This can span multiple
    paragraphs and provide detailed information about
    the command's functionality.

    Args:
        argument: Description of the argument
        option: Description of the option
        verbose: Enable verbose output
        count: Number of items to process
        format: Output format (json, yaml, table)
    """
    if verbose:
        console.print("[cyan]Running in verbose mode[/cyan]")
        console.print(f"  Argument: {argument}")
        console.print(f"  Option: {option}")
        console.print(f"  Count: {count}")
        console.print(f"  Format: {format}")

    # Your command logic here
    console.print("[green]Command executed successfully![/green]")

    # Example: Create a table
    if format == "table":
        table = Table(title="Results")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")

        for i in range(count):
            table.add_row(
                str(i + 1), f"Item {i + 1}", "Active" if i % 2 == 0 else "Pending"
            )

        console.print(table)

    # Example: JSON output
    elif format == "json":
        import json

        data = {
            "argument": argument,
            "option": option,
            "count": count,
            "items": [{"id": i, "name": f"Item {i}"} for i in range(count)],
        }
        console.print(json.dumps(data, indent=2))


def get_command():
    """Return the click command object.

    This function is used by the command loader to
    dynamically load commands.

    Returns:
        click.Command: The Click command object
    """
    return template_command


def get_name() -> str:
    """Return the command name.

    This should match the command name in @click.command(name="...")

    Returns:
        str: The command name
    """
    return "template"


def get_help() -> str:
    """Return the command help text.

    This is shown when running --help for the command.

    Returns:
        str: The help text
    """
    return "Short description of what the command does"


# --- Registration Examples ---

# Option 1: Direct import in cli.py
# from socialseed_e2e.commands.template_cmd import get_command
# cli.add_command(get_command(), name="template")

# Option 2: Using the command registry (future)
# from socialseed_e2e.commands import get_command
# cli.add_command(get_command("template"), name="template")
