"""Build Index command for socialseed-e2e.

This module provides the build-index command functionality.
Build vector index for semantic search.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


class BuildIndexService:
    """Service class for build-index operations.

    Responsibilities:
    - Validate service and manifest
    - Build vector index
    """

    def __init__(self, service_name: str, project_root: Optional[Path] = None):
        """Initialize build index service.

        Args:
            service_name: Service name
            project_root: Project root directory
        """
        self.service_name = service_name
        self.project_root = project_root or Path.cwd()
        self._resolve_project_root()

    def _resolve_project_root(self) -> None:
        """Resolve project root by checking for e2e.conf."""
        config_path = self.project_root / "e2e.conf"
        if not config_path.exists():
            self.project_root = self.project_root.parent

    def validate(self) -> Path:
        """Validate service and manifest exist.

        Returns:
            Path to manifest file

        Raises:
            RuntimeError: If validation fails
        """
        manifest_dir = self.project_root / ".e2e" / "manifests" / self.service_name
        manifest_path = manifest_dir / "project_knowledge.json"

        if not manifest_path.exists():
            raise RuntimeError(
                f"Manifest not found at {manifest_path}. "
                f"Run 'e2e manifest ../services/{self.service_name}' first."
            )

        return manifest_path

    def build_index(self, manifest_dir: Path) -> None:
        """Build vector index.

        Args:
            manifest_dir: Path to manifest directory

        Raises:
            RuntimeError: If build fails
        """
        from socialseed_e2e.project_manifest import ManifestVectorStore

        store = ManifestVectorStore(manifest_dir)
        store.build_index()

        self.index_dir = store.index_dir


class BuildIndexPresenter:
    """Presenter class for build-index output formatting.

    Responsibilities:
    - Format build index output
    - Display error messages
    """

    @staticmethod
    def display_header(service_name: str) -> None:
        """Display build index header.

        Args:
            service_name: Service name
        """
        console.print("\n📊 [bold cyan]Building Vector Index[/bold cyan]")
        console.print(f"   Service: {service_name}\n")

    @staticmethod
    def display_success(index_dir: Path) -> None:
        """Display success message.

        Args:
            index_dir: Path to index directory
        """
        console.print("[bold green]✅ Vector index built successfully![/bold green]")
        console.print(f"   📄 Location: {index_dir}\n")

    @staticmethod
    def display_error(message: str) -> None:
        """Display error message.

        Args:
            message: Error message
        """
        console.print(f"[red]❌ Error:[/red] {message}")

    @staticmethod
    def display_service_required() -> None:
        """Display service required message."""
        console.print("[red]❌ Error:[/red] Service name is required")
        console.print("Usage: e2e build-index <service_name>")
        console.print("Example: e2e build-index auth-service")


class BuildIndexCommand:
    """Command class for build-index CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute build index workflow
    """

    def __init__(self):
        """Initialize build-index command."""
        self.service: Optional[BuildIndexService] = None
        self.presenter = BuildIndexPresenter()

    def execute(self, directory: str) -> int:
        """Execute build-index command.

        Args:
            directory: Service name or directory path

        Returns:
            Exit code (0 for success, 1 for error)
        """
        service_name = directory if directory and directory != "." else None

        if not service_name:
            self.presenter.display_service_required()
            return 1

        from socialseed_e2e.cli import check_and_install_extra
        if not check_and_install_extra("rag", auto_install=True):
            return 1

        try:
            # Initialize and validate
            self.service = BuildIndexService(service_name)
            manifest_path = self.service.validate()

            # Display header
            self.presenter.display_header(service_name)

            # Build index
            manifest_dir = manifest_path.parent
            self.service.build_index(manifest_dir)

            # Display success
            self.presenter.display_success(self.service.index_dir)

            return 0

        except RuntimeError as e:
            self.presenter.display_error(str(e))
            return 1

        except Exception as e:
            self.presenter.display_error(str(e))
            return 1


# CLI command definition
@click.command(name="build-index")
@click.argument("directory", default=".", required=False)
def build_index_command(directory: str) -> None:
    """Build vector index for semantic search.

    Creates embeddings for all endpoints, DTOs, and services
    in the project manifest.

    Examples:
        e2e build-index auth-service         # Build index for auth service
        e2e build-index user-service         # Build index for user service
    """
    command = BuildIndexCommand()
    exit_code = command.execute(directory)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return build_index_command


def get_name():
    """Return the command name."""
    return "build-index"


def get_help():
    """Return the command help text."""
    return "Build vector index for semantic search"
