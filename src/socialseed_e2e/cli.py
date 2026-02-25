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
    "mock": {
        "packages": ["flask>=2.0.0"],
        "pip_extra": "mock",
        "description": "Mock Server",
    },
    "visual": {
        "packages": ["pillow>=10.0.0", "numpy>=1.24.0", "scipy>=1.11.0"],
        "pip_extra": "visual",
        "description": "Visual testing",
    },
    "dashboard": {
        "packages": ["fastapi>=0.104.0", "uvicorn[standard]>=0.24.0", "python-socketio[asyncio]>=5.10.0"],
        "pip_extra": "dashboard",
        "description": "Local Web Dashboard",
    },
    "secrets": {
        "packages": ["hvac>=1.0.0", "boto3>=1.26.0"],
        "pip_extra": "secrets",
        "description": "Secrets integration",
    },
    "full": {
        "packages": [],  # Special case - installs all extras
        "pip_extra": "full",
        "description": "All optional features",
    },
}

# Modules to import to check if an extra is installed
test_modules = {
    "tui": "textual",
    "rag": "sentence_transformers",
    "grpc": "grpc",
    "mock": "flask",
    "visual": "PIL",
    "dashboard": "fastapi",
    "secrets": "hvac",
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

    if extra_name in test_modules:
        try:
            __import__(test_modules[extra_name])
            return True
        except ImportError:
            pass
    elif extra_name == "full":
        # For full, check if all main extras are installed
        all_installed = all(
            check_and_install_extra(name) for name in ["tui", "rag", "grpc", "mock", "visual", "dashboard", "secrets"]
        )
        return all_installed

    if auto_install:
        console.print(f"[yellow]📦 Installing {extra_info['description']}...[/yellow]")
        pip_extra = extra_info["pip_extra"]
        # Use --break-system-packages if needed, but normally on venv it's fine.
        # We'll use sys.executable to ensure we use the same environment.
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
        console.print("[cyan]Install with:[/cyan]")
        console.print(f"   pip install socialseed-e2e[{pip_extra}]")
        console.print(f"\n[dim]Or run:[/dim] e2e install-extras {extra_name}")
        console.print()
        return False


def get_framework_root() -> Path:
    """Get the root directory of the framework installation."""
    import socialseed_e2e
    return Path(socialseed_e2e.__file__).parent.parent


@click.group()
@click.version_option(version=str(__version__), prog_name="socialseed-e2e")
def cli():
    """socialseed-e2e: E2E Framework for REST APIs.

    A service-agnostic framework for End-to-End testing of REST APIs,
    designed for developers and AI agents.
    """
    pass


def _register_modular_commands():
    """Register modular commands from commands/ directory."""
    from socialseed_e2e.commands import list_commands, get_command
    
    for cmd_name in list_commands():
        try:
            cmd = get_command(cmd_name)
            if cmd:
                # Add to CLI group directly
                cli.add_command(cmd, name=cmd_name)
        except Exception:
            # Silently skip if import fails
            pass


# Register modular commands on module import
_register_modular_commands()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    cli()
