"""CLI Commands package for socialseed-e2e.

This package contains modular CLI commands extracted from the main cli.py.
Each command is in its own file for better maintainability.

Usage:
    from socialseed_e2e.commands import get_command

    cmd = get_command("init")
    # Returns the click command for 'init'

Commands can be loaded dynamically for lazy loading to improve startup time.
The lazy loading system auto-discovers commands from the commands directory.
"""

import importlib
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Command registry with lazy loading
_COMMAND_LOADERS: Dict[str, Callable[[], Callable]] = {}
_LOADED_COMMANDS: Dict[str, Callable] = {}
_DISCOVERED_COMMANDS: Optional[List[str]] = None


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
    # Skip commands that might trigger execution on import
    skip_on_import = [
        "discover",
        "deep-scan",
        "regression",
        "manifest",
        "build-index",
        "generate-tests",
    ]
    if name in skip_on_import:
        # Just return None - these commands need special handling
        return None

    # Handle command groups (e.g., "mock-analyze" -> "mock_cmd")
    module_name = name.replace("-", "_") + "_cmd"

    # Map command names to module names for special cases
    command_to_module = {
        "mock-analyze": "mock_cmd",
        "mock-generate": "mock_cmd",
        "mock-run": "mock_cmd",
        "mock-validate": "mock_cmd",
        "deep-scan": "discover_cmd",
        "new-service": "new_service_cmd",
        "new-test": "new_test_cmd",
        "install-demo": "install_demo_cmd",
        "install-extras": "install_extras_cmd",
        "setup-ci": "setup_ci_cmd",
        "plan-strategy": "ai_commands",
        "generate-tests": "ai_commands",
        "autonomous-run": "ai_commands",
        "translate": "ai_commands",
        "gherkin-translate": "ai_commands",
        "perf-profile": "perf_cmd",
        "perf-report": "perf_cmd",
        "ai-learning": "learning_cmd",
        "import-cmd": "import_cmd",
    }

    if name in command_to_module:
        module_name = command_to_module[name]

    try:
        # Import the module
        module = importlib.import_module(f"socialseed_e2e.commands.{module_name}")

        # For commands in ai_commands module, the function IS the Click command
        # Don't call it, just return it
        ai_commands = {
            "generate-tests": "get_generate_tests_command",
            "plan-strategy": "get_plan_strategy_command",
            "autonomous-run": "get_autonomous_run_command",
            "translate": "get_translate_command",
            "gherkin-translate": "get_gherkin_translate_command",
        }

        if name in ai_commands:
            func_name = ai_commands[name]
            if hasattr(module, func_name):
                cmd_func = getattr(module, func_name)
                # Don't call it - the decorated function IS the command
                _LOADED_COMMANDS[name] = cmd_func
                return cmd_func

        # Look for get_<command>_command function - this returns a Click command
        func_name = f"get_{name.replace('-', '_')}_command"

        # Handle group commands (like recorder, shadow, community)
        group_func_name = f"get_{name.replace('-', '_')}_group"

        for try_func in [func_name, group_func_name]:
            if hasattr(module, try_func):
                loader = getattr(module, try_func)
                # Call it to get the Click command
                command = loader()
                _LOADED_COMMANDS[name] = command
                return command

        # Handle telemetry group special case
        if name == "telemetry":
            if hasattr(module, "get_telemetry_group"):
                command = getattr(module, "get_telemetry_group")()
                _LOADED_COMMANDS[name] = command
                return command

        # Look for command directly in module (like init_cmd.init_command)
        if hasattr(module, "command"):
            _LOADED_COMMANDS[name] = module.command
            return module.command

        # Look for <name>_command in module (like init_cmd.init_command)
        direct_name = name.replace("-", "_") + "_command"
        if hasattr(module, direct_name):
            _LOADED_COMMANDS[name] = getattr(module, direct_name)
            return getattr(module, direct_name)

    except ImportError:
        pass

    return None


def discover_commands() -> List[str]:
    """Return list of known commands.

    This uses pre-registered commands to avoid importing modules
    that have side-effects when loaded.

    Returns:
        List of known command names
    """
    global _DISCOVERED_COMMANDS

    if _DISCOVERED_COMMANDS is not None:
        return _DISCOVERED_COMMANDS

    # Pre-registered commands via @register decorator
    commands = list(_COMMAND_LOADERS.keys())

    # Add known working commands
    known_commands = [
        "init",
        "doctor",
        "config",
        "lint",
        "run",
        "new-service",
        "new-test",
        "install-demo",
        "install-extras",
        "setup-ci",
        "dashboard",
        "tui",
        "observe",
        "perf-profile",
        "perf-report",
        "security-test",
    ]

    for cmd in known_commands:
        if cmd not in commands:
            commands.append(cmd)

    _DISCOVERED_COMMANDS = commands
    return commands


def list_commands() -> list:
    """List all registered commands (including lazy-loaded)."""
    # Use auto-discovery
    return discover_commands()


def preload_commands(commands: Optional[list] = None) -> None:
    """Preload specified commands.

    Args:
        commands: List of command names to preload. If None, preload common commands.
    """
    if commands is None:
        # Preload most commonly used commands
        commands = [
            "init",
            "doctor",
            "run",
            "config",
            "lint",
            "new-service",
            "new-test",
        ]

    for name in commands:
        get_command(name)


def clear_cache() -> None:
    """Clear the loaded commands cache.

    Useful for testing or forcing reload of commands.
    """
    global _LOADED_COMMANDS, _DISCOVERED_COMMANDS
    _LOADED_COMMANDS.clear()
    _DISCOVERED_COMMANDS = None


def get_command_count() -> int:
    """Get the number of registered/loaded commands."""
    return len(_COMMAND_LOADERS) + len(_LOADED_COMMANDS)


# Initialize with common command loaders using the @register decorator
# These will be loaded on-demand
@register("init")
def _load_init():
    from socialseed_e2e.commands.init_cmd import init_command

    return init_command


@register("doctor")
def _load_doctor():
    from socialseed_e2e.commands.doctor_cmd import doctor_command

    return doctor_command


@register("config")
def _load_config():
    from socialseed_e2e.commands.config_cmd import get_config_command

    return get_config_command()


@register("lint")
def _load_lint():
    from socialseed_e2e.commands.lint_cmd import get_lint_command

    return get_lint_command()


__all__ = [
    "get_command",
    "list_commands",
    "register",
    "preload_commands",
    "clear_cache",
    "get_command_count",
    "discover_commands",
]
