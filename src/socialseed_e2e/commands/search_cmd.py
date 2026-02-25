"""Search command for socialseed-e2e.

This module provides the search command functionality.
Semantic search on project manifest using vector embeddings.
"""

import sys
from pathlib import Path
from typing import Any, List, Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


class SearchService:
    """Service class for search operations.

    Responsibilities:
    - Validate service and manifest
    - Build vector index
    - Perform semantic search
    """

    def __init__(self, service: str, project_root: Optional[Path] = None):
        """Initialize search service.

        Args:
            service: Service name to search in
            project_root: Project root directory
        """
        self.service = service
        self.project_root = project_root or Path.cwd()
        self._resolve_project_root()
        self.store = None

    def _resolve_project_root(self) -> None:
        """Resolve project root by checking for e2e.conf."""
        config_path = self.project_root / "e2e.conf"
        if not config_path.exists():
            self.project_root = self.project_root.parent

    def validate(self) -> None:
        """Validate service and manifest exist.

        Raises:
            RuntimeError: If validation fails
        """
        manifest_dir = self.project_root / ".e2e" / "manifests" / self.service

        if not manifest_dir.exists():
            raise RuntimeError(
                f"Manifest not found for service: {self.service}. "
                f"Run 'e2e manifest ../services/{self.service}' first."
            )

    def initialize_store(self) -> None:
        """Initialize the vector store."""
        from socialseed_e2e.project_manifest import ManifestVectorStore

        manifest_dir = self.project_root / ".e2e" / "manifests" / self.service
        self.store = ManifestVectorStore(manifest_dir)

    def search(
        self, query: str, top_k: int = 5, item_type: Optional[str] = None
    ) -> List[Any]:
        """Perform semantic search.

        Args:
            query: Search query
            top_k: Number of results
            item_type: Filter by type (endpoint, dto, service)

        Returns:
            List of search results

        Raises:
            RuntimeError: If search fails
        """
        if not self.store:
            self.initialize_store()

        if not self.store.is_index_valid():
            console.print("📊 Building vector index...")
            self.store.build_index()

        return self.store.search(query, top_k=top_k, item_type=item_type)


class SearchPresenter:
    """Presenter class for search output formatting.

    Responsibilities:
    - Format search results for display
    - Display error messages
    """

    @staticmethod
    def display_results(results: List[Any], query: str) -> None:
        """Display search results.

        Args:
            results: Search results
            query: Search query
        """
        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        table = Table(title=f"Search Results: '{query}'")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Score", style="yellow")
        table.add_column("Service", style="dim")

        for result in results:
            table.add_row(
                result.item_type,
                result.item_id,
                f"{result.score:.3f}",
                result.service_name or "-",
            )

        console.print(table)

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
        console.print("Usage: e2e search <query> -s <service_name>")
        console.print("Example: e2e search authentication -s auth-service")


class SearchCommand:
    """Command class for search CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute search workflow
    """

    def __init__(self):
        """Initialize search command."""
        self.service: Optional[SearchService] = None
        self.presenter = SearchPresenter()

    def execute(self, query: str, service: str, top_k: int, type: Optional[str]) -> int:
        """Execute search command.

        Args:
            query: Search query
            service: Service name
            top_k: Number of results
            type: Filter by type

        Returns:
            Exit code (0 for success, 1 for error)
        """
        if not service:
            self.presenter.display_service_required()
            return 1

        from socialseed_e2e.cli import check_and_install_extra
        if not check_and_install_extra("rag", auto_install=True):
            return 1

        try:
            # Initialize and validate
            self.service = SearchService(service)
            self.service.validate()

            # Perform search
            results = self.service.search(query, top_k=top_k, item_type=type)

            # Display results
            self.presenter.display_results(results, query)

            return 0

        except RuntimeError as e:
            self.presenter.display_error(str(e))
            return 1

        except Exception as e:
            self.presenter.display_error(str(e))
            return 1


# CLI command definition
@click.command(name="search")
@click.argument("query")
@click.option(
    "--service",
    "-s",
    required=True,
    help="Service name to search in",
)
@click.option(
    "--top-k",
    "-k",
    default=5,
    help="Number of results to return",
)
@click.option(
    "--type",
    "-t",
    default=None,
    help="Filter by type (endpoint, dto, service)",
)
def search_command(query: str, service: str, top_k: int, type: Optional[str]) -> None:
    """Semantic search on project manifest.

    Performs semantic search using vector embeddings to find
    relevant endpoints, DTOs, and services.

    Examples:
        e2e search "authentication endpoints" -s auth-service
        e2e search "user DTO" -s user-service --type dto
        e2e search "payment" -s payment-service --top-k 10
    """
    command = SearchCommand()
    exit_code = command.execute(query, service, top_k, type)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return search_command


def get_name():
    """Return the command name."""
    return "search"


def get_help():
    """Return the command help text."""
    return "Semantic search on project manifest"
