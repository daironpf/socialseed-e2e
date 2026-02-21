"""Watch command for socialseed-e2e.

This module provides the watch command functionality.
Auto-update manifest when project files change.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


class WatchService:
    """Service class for watch operations.

    Responsibilities:
    - Validate service and manifest existence
    - Initialize manifest generator
    - Manage file watcher
    """

    def __init__(self, service_name: str, project_root: Optional[Path] = None):
        """Initialize watch service.

        Args:
            service_name: Name of the service to watch
            project_root: Project root directory (optional)
        """
        self.service_name = service_name
        self.project_root = project_root or Path.cwd()
        self._resolve_project_root()
        self.manifest_path = self._find_manifest()
        self.generator = None

    def _resolve_project_root(self) -> None:
        """Resolve the project root by checking for e2e.conf."""
        config_path = self.project_root / "e2e.conf"
        if not config_path.exists():
            self.project_root = self.project_root.parent

    def _find_manifest(self) -> Path:
        """Find the manifest file path.

        Returns:
            Path to manifest file

        Raises:
            RuntimeError: If manifest not found
        """
        manifest_dir = self.project_root / ".e2e" / "manifests" / self.service_name
        manifest_path = manifest_dir / "project_knowledge.json"

        if not manifest_path.exists():
            raise RuntimeError(
                f"Manifest not found at {manifest_path}. "
                f"Run 'e2e manifest ../services/{self.service_name}' first."
            )

        return manifest_path

    def initialize_watcher(self) -> None:
        """Initialize the manifest generator for watching."""
        from socialseed_e2e.project_manifest import ManifestGenerator

        manifest_dir = self.manifest_path.parent
        self.generator = ManifestGenerator(
            project_root=manifest_dir, manifest_path=self.manifest_path
        )

    def start_watching(self, blocking: bool = True) -> None:
        """Start watching for file changes.

        Args:
            blocking: Whether to block the main thread

        Raises:
            RuntimeError: If watcher fails
        """
        from socialseed_e2e.project_manifest import SmartSyncManager

        if not self.generator:
            self.initialize_watcher()

        manager = SmartSyncManager(self.generator, debounce_seconds=2.0)

        if blocking:
            manager.start_watching(blocking=True)


class WatchPresenter:
    """Presenter class for watch command output formatting.

    Responsibilities:
    - Format watcher status messages
    - Format error messages
    """

    @staticmethod
    def display_start_message(service_name: str, manifest_path: Path) -> None:
        """Display watcher start message.

        Args:
            service_name: Service being watched
            manifest_path: Path to manifest
        """
        console.print("\n👁️  [bold cyan]Starting file watcher[/bold cyan]")
        console.print(f"   Service: {service_name}")
        console.print(f"   Manifest: {manifest_path}")
        console.print("   Press Ctrl+C to stop\n")

    @staticmethod
    def display_stop_message() -> None:
        """Display watcher stop message."""
        console.print("\n\n[yellow]👋 File watcher stopped by user[/yellow]")

    @staticmethod
    def display_error(message: str) -> None:
        """Display error message.

        Args:
            message: Error message
        """
        console.print(f"\n[red]❌ Error:[/red] {message}")

    @staticmethod
    def display_service_required() -> None:
        """Display service name required message."""
        console.print("[red]❌ Error:[/red] Service name is required")
        console.print("Usage: e2e watch <service_name>")
        console.print("Example: e2e watch auth-service")

    @staticmethod
    def display_manifest_not_found(manifest_path: Path, service_name: str) -> None:
        """Display manifest not found message.

        Args:
            manifest_path: Path to manifest
            service_name: Service name
        """
        console.print(f"[red]❌ Error:[/red] Manifest not found at {manifest_path}")
        console.print(
            f"Run 'e2e manifest ../services/{service_name}' first to generate."
        )


class WatchCommand:
    """Command class for watch CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute watch workflow
    """

    def __init__(self):
        """Initialize watch command."""
        self.service: Optional[WatchService] = None
        self.presenter = WatchPresenter()

    def execute(self, directory: str) -> int:
        """Execute watch command.

        Args:
            directory: Service name or directory path

        Returns:
            Exit code (0 for success, 1 for error)
        """
        service_name = directory if directory and directory != "." else None

        if not service_name:
            self.presenter.display_service_required()
            return 1

        try:
            # Initialize service
            self.service = WatchService(service_name)

            # Display start message
            self.presenter.display_start_message(
                service_name, self.service.manifest_path
            )

            # Start watching
            self.service.start_watching(blocking=True)

            return 0

        except KeyboardInterrupt:
            self.presenter.display_stop_message()
            return 0

        except RuntimeError as e:
            self.presenter.display_error(str(e))
            return 1

        except Exception as e:
            self.presenter.display_error(str(e))
            return 1


# CLI command definition
@click.command(name="watch")
@click.argument("directory", default=".", required=False)
def watch_command(directory: str) -> None:
    """Watch project files and auto-update manifest.

    Monitors source files for changes and automatically updates
    the manifest in the framework's manifests folder using smart sync.

    Examples:
        e2e watch auth-service         # Watch auth service for changes
        e2e watch user-service         # Watch user service for changes
    """
    command = WatchCommand()
    exit_code = command.execute(directory)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return watch_command


def get_name():
    """Return the command name."""
    return "watch"


def get_help():
    """Return the command help text."""
    return "Watch project files and auto-update manifest"
