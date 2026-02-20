"""CLI Commands package for socialseed-e2e.

This package contains modular CLI commands extracted from the main cli.py.
Each command is in its own file for better maintainability.

Usage:
    from socialseed_e2e.commands import get_command

    cmd = get_command("init")
    # Returns the click command for 'init'

Commands can be loaded dynamically for lazy loading.

Structure:
    commands/
    ├── __init__.py          # Command registry
    ├── template_cmd.py      # Template for new commands
    ├── init_cmd.py          # init command
    ├── doctor_cmd.py        # doctor command
    └── ...
"""

from typing import Callable, Dict, Optional

# Command registry
_COMMANDS: Dict[str, Callable] = {}


def register(name: str) -> Callable:
    """Decorator to register a command.

    Usage:
        @register("init")
        def get_init_command():
            return init_command
    """

    def decorator(func: Callable) -> Callable:
        _COMMANDS[name] = func
        return func

    return decorator


def get_command(name: str) -> Optional[Callable]:
    """Get a command by name.

    Args:
        name: Command name

    Returns:
        Command function or None if not found
    """
    return _COMMANDS.get(name)


def list_commands() -> list:
    """List all registered commands."""
    return list(_COMMANDS.keys())


# Import all commands to register them
# These will register themselves via the get_command() function
# Note: This is for future use when commands are migrated
def _load_commands():
    """Load all commands from submodules."""
    global _COMMANDS

    # Import available commands
    # Each module should define get_command() function
    try:
        from socialseed_e2e.commands import init_cmd

        _COMMANDS["init"] = init_cmd.get_command
    except ImportError:
        pass

    try:
        from socialseed_e2e.commands import doctor_cmd

        _COMMANDS["doctor"] = doctor_cmd.get_command
    except ImportError:
        pass


# Load commands on first access
_load_commands()


def discover_commands():
    """Manually discover all available commands.

    Returns:
        Dict of command name to command function
    """
    return dict(_COMMANDS)


__all__ = [
    "get_command",
    "list_commands",
    "register",
    "discover_commands",
]
