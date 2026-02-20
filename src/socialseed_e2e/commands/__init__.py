"""CLI Commands package for socialseed-e2e.

This package contains modular CLI commands extracted from the main cli.py.
Each command is in its own file for better maintainability.

Usage:
    from socialseed_e2e.commands import get_command

    cmd = get_command("init")
    # Returns the click command for 'init'

Commands can be loaded dynamically for lazy loading to improve startup time.

Structure:
    commands/
    ├── __init__.py          # Command registry with lazy loading
    ├── template_cmd.py      # Template for new commands
    ├── init_cmd.py          # init command
    ├── doctor_cmd.py        # doctor command
    └── ...
"""

import importlib
import logging
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Command registry with lazy loading
_COMMAND_LOADERS: Dict[str, Callable[[], Callable]] = {}
_LOADED_COMMANDS: Dict[str, Callable] = {}


def register(name: str) -> Callable:
    """Decorator to register a command loader (lazy loading).

    Usage:
        @register("init")
        def load_init_command():
            from socialseed_e2e.commands.init_cmd import get_init_command
            return get_init_command()
    """

    def decorator(func: Callable[[], Callable]) -> Callable:
        _COMMAND_LOADERS[name] = func
        return func

    return decorator


def get_command(name: str) -> Optional[Callable]:
    """Get a command by name (lazy loading).

    Commands are only loaded when first accessed.

    Args:
        name: Command name

    Returns:
        Command function or None if not found
    """
    # Check if already loaded
    if name in _LOADED_COMMANDS:
        return _LOADED_COMMANDS[name]

    # Try to load from loaders
    if name in _COMMAND_LOADERS:
        try:
            loader = _COMMAND_LOADERS[name]
            command = loader()
            _LOADED_COMMANDS[name] = command
            return command
        except Exception as e:
            logger.warning(f"Failed to load command '{name}': {e}")
            return None

    # Try lazy import as fallback
    return _lazy_import_command(name)


def _lazy_import_command(name: str) -> Optional[Callable]:
    """Try to lazy import a command module.

    Args:
        name: Command name

    Returns:
        Command function or None if not found
    """
    module_name = f"{name}_cmd"

    try:
        # Try to import the command module
        module = importlib.import_module(f"socialseed_e2e.commands.{module_name}")

        # Look for get_<command>_command function
        func_name = f"get_{name}_command"
        if hasattr(module, func_name):
            loader = getattr(module, func_name)
            command = loader()
            _LOADED_COMMANDS[name] = command
            return command

        # Look for command directly
        if hasattr(module, "command"):
            _LOADED_COMMANDS[name] = module.command
            return module.command

    except ImportError:
        pass

    return None


def list_commands() -> list:
    """List all registered commands (including lazy-loaded)."""
    # Combine registered loaders with discovered commands
    commands = set(_COMMAND_LOADERS.keys())

    # Try to discover more commands
    common_commands = [
        "init",
        "doctor",
        "run",
        "new-service",
        "new-test",
        "config",
        "lint",
        "set",
        "install-demo",
        "install-extras",
        "setup-ci",
        "dashboard",
        "tui",
        "telemetry",
        "perf-profile",
        "perf-report",
        "generate-tests",
        "analyze-flaky",
        "autonomous-run",
        "debug-execution",
        "healing-stats",
        "semantic-analyze",
        "plan-strategy",
        "translate",
        "gherkin-translate",
        "deep-scan",
        "observe",
        "discover",
        "watch",
        "manifest",
        "manifest-query",
        "manifest-check",
        "build-index",
        "search",
        "retrieve",
        "mock-analyze",
        "mock-generate",
        "mock-run",
        "mock-validate",
        "security-test",
        "red-team",
        "recorder",
        "shadow",
        "community",
        "import-cmd",
        "regression",
        "ai-learning",
    ]

    for cmd in common_commands:
        if cmd not in _LOADED_COMMANDS:
            # Try lazy import
            if _lazy_import_command(cmd):
                commands.add(cmd)

    return sorted(commands)


def preload_commands(commands: Optional[list] = None) -> None:
    """Preload specified commands.

    Args:
        commands: List of command names to preload. If None, preload common commands.
    """
    if commands is None:
        commands = ["init", "doctor", "run", "config", "lint"]

    for name in commands:
        get_command(name)


def clear_cache() -> None:
    """Clear the loaded commands cache.

    Useful for testing or forcing reload of commands.
    """
    global _LOADED_COMMANDS
    _LOADED_COMMANDS.clear()


def get_command_count() -> int:
    """Get the number of registered/loaded commands."""
    return len(_COMMAND_LOADERS) + len(_LOADED_COMMANDS)


# Initialize with common command loaders
# These will be loaded on-demand
def _init_command_loaders():
    """Initialize command loaders for lazy loading."""
    global _COMMAND_LOADERS

    # Define loaders for available commands
    loaders = {
        "init": lambda: importlib.import_module("socialseed_e2e.commands.init_cmd"),
        "doctor": lambda: importlib.import_module("socialseed_e2e.commands.doctor_cmd"),
    }

    for name, loader in loaders.items():
        _COMMAND_LOADERS[name] = loader


# Initialize on import
_init_command_loaders()


__all__ = [
    "get_command",
    "list_commands",
    "register",
    "preload_commands",
    "clear_cache",
    "get_command_count",
]
