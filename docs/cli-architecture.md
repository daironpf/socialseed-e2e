# CLI Architecture Guide

This document describes the CLI architecture of socialseed-e2e and how to extend it.

---

## Overview

The CLI is built with Click and provides 47+ commands for managing E2E tests. The architecture supports both:
- **Monolithic mode**: All commands in `cli.py` (current default)
- **Modular mode**: Commands in separate files (future)

---

## Directory Structure

```
src/socialseed_e2e/
├── cli.py                    # Main CLI entry point (8245 lines)
├── __main__.py              # Package entry point
├── commands/                # Modular commands package (NEW)
│   ├── __init__.py         # Command registry
│   ├── init_cmd.py         # Example: init command
│   └── template_cmd.py     # Template for new commands
└── commands/                # More command modules...
```

---

## Command Structure

### Option 1: Monolithic (Current)

All commands are defined directly in `cli.py`:

```python
# cli.py
@click.command()
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Overwrite existing files")
def init(directory: str, force: bool):
    """Initialize a new E2E project."""
    # Implementation here
    pass
```

**Pros:**
- Simple to understand
- All commands in one place
- No import overhead

**Cons:**
- Hard to maintain (8245 lines)
- Slow to test
- Difficult to collaborate

### Option 2: Modular (Recommended for New Commands)

Each command in its own file:

```python
# commands/init_cmd.py
import click
from rich.console import Console

console = Console()


@click.command(name="init")
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Overwrite existing files")
def init_command(directory: str, force: bool) -> None:
    """Initialize a new E2E project."""
    # Implementation here
    pass


def get_command():
    """Return the click command object."""
    return init_command


def get_name():
    """Return the command name."""
    return "init"


def get_help():
    """Return the command help text."""
    return "Initialize a new E2E project"
```

**Pros:**
- Easy to maintain
- Easy to test
- Better collaboration
- Lazy loading possible

**Cons:**
- More files to manage
- Need to register commands

---

## Command Registration

### In cli.py (Monolithic)

Commands are automatically registered with Click:

```python
@click.group()
def cli():
    pass

@cli.command()  # Auto-registered with Click
def init():
    pass
```

### In commands/ (Modular)

Commands need to be registered:

```python
# Option 1: Direct import in cli.py
from socialseed_e2e.commands import init_cmd
cli.add_command(init_cmd.get_command())

# Option 2: Auto-discovery (future)
from socialseed_e2e.commands import get_command
for cmd_name in ["init", "run", "config"]:
    cmd = get_command(cmd_name)
    if cmd:
        cli.add_command(cmd)
```

---

## Creating a New Command

### Step 1: Create the Command File

Create `commands/<command_name>_cmd.py`:

```python
"""Command description for socialseed-e2e CLI.

Brief description of what this command does.
"""

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command(name="command-name")
@click.argument("argument", required=False)
@click.option("--option", "-o", help="Option description")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def command_name(argument: str, option: str, verbose: bool) -> None:
    """Short command description.
    
    Longer description if needed.
    """
    if verbose:
        console.print("[cyan]Running in verbose mode[/cyan]")
    
    # Implementation
    console.print(f"[green]Done![/green]")


def get_command():
    """Return the click command object."""
    return command_name


def get_name():
    """Return the command name."""
    return "command-name"


def get_help():
    """Return the command help text."""
    return "Short command description"
```

### Step 2: Register the Command

Add to `cli.py`:

```python
# Import the command
from socialseed_e2e.commands.command_name_cmd import get_command

# Add to CLI group
cli.add_command(get_command(), name="command-name")
```

Or use auto-discovery (future):

```python
# In cli.py - auto-discover all commands
from socialseed_e2e.commands import discover_commands
discover_commands(cli)
```

---

## Best Practices

### 1. Use Rich for Output

```python
from rich.console import Console
from rich.table import Table

console = Console()

# Good: Rich formatting
table = Table(title="Results")
table.add_column("Name", style="cyan")
table.add_row("Value")
console.print(table)

# Avoid: Plain print
print("Results:")  # Less informative
```

### 2. Add Proper Error Handling

```python
@click.command()
def command():
    try:
        # Main logic
        result = do_something()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise
```

### 3. Use Type Hints

```python
# Good
def command(name: str, count: int = 10) -> None:
    pass

# Avoid
def command(name, count=10):
    pass
```

### 4. Document Options

```python
@click.option(
    "--output", 
    "-o", 
    type=click.Path(),
    help="Output file path"
)
def command(output: str):
    """Description."""
    pass
```

### 5. Follow Naming Conventions

- File: `<command_name>_cmd.py`
- Function: `<command_name>_command()`
- Class (if needed): `<CommandName>Command`

---

## Common Patterns

### Option with Choices

```python
@click.option("--format", type=click.Choice(["json", "yaml", "csv"]))
def export(format: str):
    pass
```

### Option with Default Value

```python
@click.option("--timeout", default=30, help="Timeout in seconds")
def run(timeout: int):
    pass
```

### Flag Option

```python
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(verbose: bool):
    pass
```

### Multiple Options

```python
@click.option("--tag", multiple=True, help="Tags to include")
def run(tag: tuple):
    for t in tag:
        console.print(f"Tag: {t}")
```

### Confirmation Prompt

```python
@click.command()
@click.confirmation_option(prompt="Are you sure?")
def delete():
    # Destructive action
    pass
```

### Progress Indicator

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
) as progress:
    task = progress.add_task("Working...", total=100)
    # Do work
    progress.update(task, advance=10)
```

---

## Testing Commands

### Unit Test Example

```python
# tests/test_commands.py
from click.testing import CliRunner
from socialseed_e2e.cli import cli

def test_init_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init", "my-project"])
        assert result.exit_code == 0
        assert "Project initialized" in result.output
```

### Integration Test

```python
def test_init_with_demo():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init", "--demo"])
        assert result.exit_code == 0
        # Verify demo files created
```

---

## Migration Guide

### From Monolithic to Modular

1. **Copy** the command function from `cli.py` to `commands/<cmd>_cmd.py`

2. **Add** the registration functions:
   ```python
   def get_command():
       return command_name
   ```

3. **Import** in `cli.py`:
   ```python
   from socialseed_e2e.commands.init_cmd import get_command
   ```

4. **Register** the command:
   ```python
   cli.add_command(get_command(), name="init")
   ```

5. **Test** the command works

6. **Remove** from `cli.py` (when all commands migrated)

---

## Future Enhancements

### Lazy Loading

Load commands only when needed:

```python
# cli.py
def get_command(name: str):
    if name == "init":
        from socialseed_e2e.commands.init_cmd import get_command
        return get_command()
    # ...
```

### Auto-Discovery

```python
# commands/__init__.py
import importlib
from pathlib import Path

def discover_commands():
    commands_dir = Path(__file__).parent
    for file in commands_dir.glob("*_cmd.py"):
        module = importlib.import_module(f"socialseed_e2e.commands.{file.stem}")
        yield module.get_command()
```

### Command Groups

Organize related commands:

```python
# commands/project/
#   ├── __init__.py
#   ├── init_cmd.py
#   ├── new_service_cmd.py
#   └── new_test_cmd.py

@cli.group()
def project():
    """Project management commands."""
    pass

project.add_command(init)
project.add_command(new_service)
```

---

## Quick Reference

| Task | File | Function |
|------|------|----------|
| Add new command | `commands/<name>_cmd.py` | `@click.command()` |
| Register command | `cli.py` | `cli.add_command()` |
| Add option | Command file | `@click.option()` |
| Add argument | Command file | `@click.argument()` |
| Output formatting | Command file | `console.print()` |
| Error handling | Command file | `try/except` |

---

## See Also

- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [CLI Reference](../cli-reference.md)
- [AGENT_GUIDE.md](../AGENT_GUIDE.md)
