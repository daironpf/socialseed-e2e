"""Retrieve command for socialseed-e2e.

This module provides the retrieve command functionality.
Retrieve context from project manifest for specific tasks.
"""

import sys
from pathlib import Path
from typing import Any, List, Optional

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


class RetrieveService:
    """Service class for retrieve operations.

    Responsibilities:
    - Validate service and manifest
    - Initialize RAG retrieval engine
    - Retrieve context for tasks
    """

    def __init__(self, service: str, project_root: Optional[Path] = None):
        """Initialize retrieve service.

        Args:
            service: Service name
            project_root: Project root directory
        """
        self.service = service
        self.project_root = project_root or Path.cwd()
        self._resolve_project_root()
        self.engine = None

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

    def initialize_engine(self) -> None:
        """Initialize the RAG retrieval engine."""
        from socialseed_e2e.project_manifest import RAGRetrievalEngine

        manifest_dir = self.project_root / ".e2e" / "manifests" / self.service
        self.engine = RAGRetrievalEngine(manifest_dir)

    def retrieve_context(self, task: str, max_chunks: int = 5) -> List[Any]:
        """Retrieve context for a task.

        Args:
            task: Task description
            max_chunks: Maximum number of chunks

        Returns:
            List of context chunks

        Raises:
            RuntimeError: If retrieval fails
        """
        if not self.engine:
            self.initialize_engine()

        return self.engine.retrieve_for_task(task, max_chunks=max_chunks)


class RetrievePresenter:
    """Presenter class for retrieve output formatting.

    Responsibilities:
    - Format retrieved context for display
    - Display error messages
    """

    @staticmethod
    def display_results(chunks: List[Any], task: str) -> None:
        """Display retrieved context.

        Args:
            chunks: Retrieved context chunks
            task: Task description
        """
        if not chunks:
            console.print("[yellow]No context found for this task[/yellow]")
            return

        console.print(f"\n[bold cyan]Task:[/bold cyan] {task}\n")

        for i, chunk in enumerate(chunks, 1):
            chunk_type = chunk.chunk_type
            token_estimate = chunk.token_estimate
            chunk_id = chunk.chunk_id
            content = chunk.content

            console.print(f"[bold]Chunk {i}:[/bold] {chunk_type}")
            console.print(f"[dim]Tokens: {token_estimate} | ID: {chunk_id}[/dim]")
            console.print(Panel(content, border_style="green"))
            console.print()

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
        console.print("Usage: e2e retrieve <task> -s <service_name>")
        console.print("Example: e2e retrieve 'create auth tests' -s auth-service")


class RetrieveCommand:
    """Command class for retrieve CLI command.

    Responsibilities:
    - Handle CLI argument parsing
    - Coordinate service and presenter
    - Execute retrieval workflow
    """

    def __init__(self):
        """Initialize retrieve command."""
        self.service: Optional[RetrieveService] = None
        self.presenter = RetrievePresenter()

    def execute(self, task: str, service: str, max_chunks: int) -> int:
        """Execute retrieve command.

        Args:
            task: Task description
            service: Service name
            max_chunks: Maximum number of chunks

        Returns:
            Exit code (0 for success, 1 for error)
        """
        if not service:
            self.presenter.display_service_required()
            return 1

        try:
            # Initialize and validate
            self.service = RetrieveService(service)
            self.service.validate()

            # Retrieve context
            chunks = self.service.retrieve_context(task, max_chunks)

            # Display results
            self.presenter.display_results(chunks, task)

            return 0

        except RuntimeError as e:
            self.presenter.display_error(str(e))
            return 1

        except ImportError:
            from socialseed_e2e.cli import check_and_install_extra

            check_and_install_extra("rag", auto_install=False)
            return 1

        except Exception as e:
            self.presenter.display_error(str(e))
            return 1


# CLI command definition
@click.command(name="retrieve")
@click.argument("task")
@click.option(
    "--service",
    "-s",
    default=None,
    help="Service name",
)
@click.option(
    "--max-chunks",
    "-c",
    default=5,
    help="Maximum chunks",
)
def retrieve_command(task: str, service: str, max_chunks: int) -> None:
    """Retrieve context for a specific task.

    Retrieves relevant context from the project manifest
    for the given task description.

    Examples:
        e2e retrieve "create user authentication tests" -s auth-service
        e2e retrieve "test payment flow" -s payment-service --max-chunks 3
    """
    command = RetrieveCommand()
    exit_code = command.execute(task, service, max_chunks)
    sys.exit(exit_code)


# Registration functions
def get_command():
    """Return the click command for registration."""
    return retrieve_command


def get_name():
    """Return the command name."""
    return "retrieve"


def get_help():
    """Return the command help text."""
    return "Retrieve context from project manifest for specific tasks"
