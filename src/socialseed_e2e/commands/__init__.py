"""CLI Commands package for socialseed-e2e.

This package contains modular CLI commands extracted from the main cli.py.
Each command is in its own file for better maintainability.
"""

import importlib
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

import click

logger = logging.getLogger(__name__)

# Command registry with lazy loading
_COMMAND_LOADERS: Dict[str, Callable[[], Callable]] = {}
_LOADED_COMMANDS: Dict[str, Callable] = {}
_DISCOVERED_COMMANDS: Optional[List[str]] = None


def register(name: str) -> Callable:
    """Decorator to register a command loader (lazy loading)."""
    def decorator(func: Callable[[], Callable]) -> Callable:
        _COMMAND_LOADERS[name] = func
        return func
    return decorator


def get_command(name: str) -> Optional[click.Command]:
    """Get a command by name (lazy loading)."""
    # Check if already loaded
    if name in _LOADED_COMMANDS:
        return _LOADED_COMMANDS[name]

    # Try to load from loaders
    if name in _COMMAND_LOADERS:
        try:
            loader = _COMMAND_LOADERS[name]
            # CRITICAL: Check if already a Click object before calling
            if isinstance(loader, click.BaseCommand):
                command = loader
            else:
                command = loader()
            _LOADED_COMMANDS[name] = command
            return command
        except Exception as e:
            logger.warning(f"Failed to load command '{name}': {e}")
            return None

    # Try lazy import as fallback
    return _lazy_import_command(name)


def _lazy_import_command(name: str) -> Optional[click.Command]:
    """Try to lazy import a command module."""
    # Handle command groups and special names
    module_name = name.replace("-", "_") + "_cmd"

    # Map command names to module names for special cases
    command_to_module = {
        "mock-analyze": "mock_cmd",
        "mock-generate": "mock_cmd",
        "mock-run": "mock_cmd",
        "mock-validate": "mock_cmd",
        "deep-scan": "deep_scan_cmd",
        "watch": "watch_cmd",
        "analyze-flaky": "analyze_flaky_cmd",
        "healing-stats": "healing_stats_cmd",
        "debug-execution": "debug_execution_cmd",
        "security-test": "security_test_cmd",
        "search": "search_cmd",
        "retrieve": "retrieve_cmd",
        "build-index": "build_index_cmd",
        "run": "run_cmd",
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
        "recorder": "recorder_cmd",
        "shadow": "shadow_cmd",
        "community": "community_cmd",
        "telemetry": "telemetry_cmd",
    }

    if name in command_to_module:
        module_name = command_to_module[name]

    try:
        # Import the module
        module = importlib.import_module(f"socialseed_e2e.commands.{module_name}")

        # AI Commands special handling
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
                # Check for click command
                if isinstance(cmd_func, click.BaseCommand):
                    _LOADED_COMMANDS[name] = cmd_func
                    return cmd_func
                else:
                    cmd = cmd_func()
                    _LOADED_COMMANDS[name] = cmd
                    return cmd

        # Look for getter functions
        loaders = [
            f"get_{name.replace('-', '_')}_command",
            f"get_{name.replace('-', '_')}_group",
            "get_command",
            "get_group"
        ]

        for func_name in loaders:
            if hasattr(module, func_name):
                loader = getattr(module, func_name)
                # CRITICAL: If the loader is already a Click command, DON'T call it!
                if isinstance(loader, click.BaseCommand):
                    command = loader
                else:
                    command = loader()
                _LOADED_COMMANDS[name] = command
                return command

        # Look for direct command objects
        direct_names = [
            "command",
            "group",
            f"{name.replace('-', '_')}_command",
            f"{name.replace('-', '_')}_group"
        ]
        
        for attr_name in direct_names:
            if hasattr(module, attr_name):
                cmd = getattr(module, attr_name)
                if isinstance(cmd, click.BaseCommand):
                    _LOADED_COMMANDS[name] = cmd
                    return cmd

    except Exception:
        pass

    return None


def discover_commands() -> List[str]:
    """Return list of known and auto-discovered commands."""
    global _DISCOVERED_COMMANDS

    if _DISCOVERED_COMMANDS is not None:
        return _DISCOVERED_COMMANDS

    commands = list(_COMMAND_LOADERS.keys())
    
    # Auto-discovery by file scanning
    try:
        commands_dir = Path(__file__).parent
        for file in commands_dir.glob("*.py"):
            if file.name.startswith("__"):
                continue
            
            # Basic name from filename
            name = file.stem.replace("_cmd", "").replace("_commands", "").replace("_", "-")
            if name and name not in commands:
                commands.append(name)
    except Exception:
        pass
            
    # Add special cases/groups
    special_cases = [
        "mock-analyze", "mock-validate", "mock-generate", "mock-run",
        "recorder", "shadow", "community", "telemetry", "observe",
        "generate-tests", "plan-strategy", "deep-scan", "discover"
    ]
    for sc in special_cases:
        if sc not in commands:
            commands.append(sc)

    _DISCOVERED_COMMANDS = sorted(list(set(commands)))
    return _DISCOVERED_COMMANDS


def list_commands() -> list:
    """List all registered commands."""
    return discover_commands()


# Register common commands explicitly for speed
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
