"""Auto-install dependencies module for socialseed-e2e.

This module provides automatic dependency installation for commands that need them.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable

from rich.console import Console
from rich.prompt import Confirm

console = Console()

DEPENDENCY_TRACKER_FILE = Path.home() / ".socialseed-e2e" / "installed_extras"


class DependencyManager:
    """Manages automatic installation of dependencies per command."""

    COMMAND_DEPENDENCIES: Dict[str, Dict] = {
        "tui": {
            "packages": ["textual>=0.41.0"],
            "pip_extra": "tui",
            "description": "Terminal User Interface (TUI)",
            "test_module": "textual",
        },
        "dashboard": {
            "packages": ["fastapi>=0.100.0", "uvicorn>=0.23.0"],
            "pip_extra": "dashboard",
            "description": "Web Dashboard",
            "test_module": "fastapi",
        },
        "rag": {
            "packages": ["sentence-transformers>=2.2.0", "numpy>=1.24.0", "scikit-learn>=1.0.0"],
            "pip_extra": "rag",
            "description": "Semantic search and RAG features",
            "test_module": "sentence_transformers",
        },
        "grpc": {
            "packages": ["grpcio>=1.59.0", "grpcio-tools>=1.59.0", "protobuf>=4.24.0"],
            "pip_extra": "grpc",
            "description": "gRPC protocol support",
            "test_module": "grpc",
        },
        "mock": {
            "packages": ["flask>=2.0.0"],
            "pip_extra": "mock",
            "description": "Mock Server",
            "test_module": "flask",
        },
        "visual": {
            "packages": ["pillow>=10.0.0", "numpy>=1.24.0", "scipy>=1.11.0"],
            "pip_extra": "visual",
            "description": "Visual testing",
            "test_module": "PIL",
        },
        "secrets": {
            "packages": ["python-dotenv>=1.0.0"],
            "pip_extra": "secrets",
            "description": "Secrets management",
            "test_module": "dotenv",
        },
        "test-data": {
            "packages": ["faker>=19.0.0"],
            "pip_extra": "test-data",
            "description": "Test data generation",
            "test_module": "faker",
        },
    }

    def __init__(self):
        self._ensure_tracker_file()

    def _ensure_tracker_file(self) -> None:
        """Ensure the tracker file exists."""
        DEPENDENCY_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not DEPENDENCY_TRACKER_FILE.exists():
            DEPENDENCY_TRACKER_FILE.write_text("")

    def is_installed(self, extra_name: str) -> bool:
        """Check if an extra dependency is already installed.

        Args:
            extra_name: Name of the extra

        Returns:
            True if installed, False otherwise
        """
        if extra_name not in self.COMMAND_DEPENDENCIES:
            return True

        extra_info = self.COMMAND_DEPENDENCIES[extra_name]
        test_module = extra_info.get("test_module")

        if not test_module:
            return True

        try:
            __import__(test_module)
            return True
        except ImportError:
            return False

    def is_already_asked(self, extra_name: str) -> bool:
        """Check if user has already been asked about this extra.

        Args:
            extra_name: Name of the extra

        Returns:
            True if already asked, False otherwise
        """
        if not DEPENDENCY_TRACKER_FILE.exists():
            return False

        installed = DEPENDENCY_TRACKER_FILE.read_text()
        return extra_name in installed

    def mark_as_asked(self, extra_name: str) -> None:
        """Mark that user has been asked about this extra.

        Args:
            extra_name: Name of the extra
        """
        self._ensure_tracker_file()
        installed = DEPENDENCY_TRACKER_FILE.read_text()

        if extra_name not in installed:
            with open(DEPENDENCY_TRACKER_FILE, "a") as f:
                f.write(f"{extra_name}\n")

    def install(self, extra_name: str) -> bool:
        """Install an extra dependency.

        Args:
            extra_name: Name of the extra to install

        Returns:
            True if successful, False otherwise
        """
        if extra_name not in self.COMMAND_DEPENDENCIES:
            console.print(f"[yellow]⚠ Unknown extra: {extra_name}[/yellow]")
            return False

        extra_info = self.COMMAND_DEPENDENCIES[extra_name]
        description = extra_info["description"]

        console.print(f"\n[cyan]📦 Installing {description}...[/cyan]")

        cmd = [sys.executable, "-m", "pip", "install", f"socialseed-e2e[{extra_info['pip_extra']}]"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            console.print(f"[green]✅ {description} installed successfully![/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Installation failed:[/red] {e.stderr}")
            return False

    def check_and_prompt(self, extra_name: str) -> bool:
        """Check if extra is installed, prompt user if not.

        Args:
            extra_name: Name of the extra to check

        Returns:
            True if extra is available (installed or user agreed to install)
        """
        if self.is_installed(extra_name):
            return True

        if self.is_already_asked(extra_name):
            console.print(
                f"[dim]Note: {extra_name} not installed. "
                f"Run 'e2e install-extras {extra_name}' to install.[/dim]"
            )
            return False

        extra_info = self.COMMAND_DEPENDENCIES.get(extra_name, {})
        description = extra_info.get("description", extra_name)

        console.print()
        should_install = Confirm.ask(
            f"⚠️ {description} is required but not installed.\nWould you like to install it now?",
            default=True,
        )

        self.mark_as_asked(extra_name)

        if should_install:
            return self.install(extra_name)

        return False


_dependency_manager: Optional[DependencyManager] = None


def get_dependency_manager() -> DependencyManager:
    """Get the singleton dependency manager instance."""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


def require_extra(extra_name: str) -> Callable:
    """Decorator to require an extra dependency before command execution.

    Usage:
        @require_extra("tui")
        @click.command()
        def my_command():
            ...
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            manager = get_dependency_manager()
            if not manager.check_and_prompt(extra_name):
                console.print(
                    f"[yellow]⚠ Command '{func.__name__}' requires {extra_name}.[/yellow]"
                )
                console.print(
                    f"[dim]Run 'e2e install-extras {extra_name}' to install it manually.[/dim]"
                )
                return
            return func(*args, **kwargs)

        return wrapper

    return decorator
