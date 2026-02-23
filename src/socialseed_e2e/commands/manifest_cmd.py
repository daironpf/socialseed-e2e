"""Manifest commands for socialseed-e2e CLI.

This module provides the manifest, manifest-query, build-index, search, retrieve commands
using POO and SOLID principles.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


def get_service_name_from_path(target_path: Path) -> str:
    """Extract service name from path."""
    return target_path.name


class ManifestGenerator:
    """Handles manifest generation (Single Responsibility)."""

    def __init__(self, target_path: Path, project_root: Path, service_name: str):
        self.target_path = target_path
        self.project_root = project_root
        self.service_name = service_name

    def generate(self, force: bool = False):
        """Generate manifest."""
        from socialseed_e2e.project_manifest import ManifestGenerator as MG

        manifest_dir = self.project_root / ".e2e" / "manifests" / self.service_name
        manifest_path = manifest_dir / "project_knowledge.json"

        generator = MG(project_root=self.target_path, manifest_path=manifest_path)
        return generator.generate(force_full_scan=force)

    def display_summary(self, manifest) -> None:
        """Display manifest summary."""
        table = Table(title="Project Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        total_endpoints = sum(len(s.endpoints) for s in manifest.services)
        total_dtos = sum(len(s.dto_schemas) for s in manifest.services)
        total_ports = sum(len(s.ports) for s in manifest.services)

        table.add_row("Services", str(len(manifest.services)))
        table.add_row("Endpoints", str(total_endpoints))
        table.add_row("DTO Schemas", str(total_dtos))
        table.add_row("Ports", str(total_ports))

        console.print(table)


class ManifestQueryAgent:
    """Handles manifest queries (Single Responsibility)."""

    def __init__(self, service_name: str):
        self.service_name = service_name

    def query(self, query_type: Optional[str] = None):
        """Query the manifest."""
        from pathlib import Path as P

        from socialseed_e2e.project_manifest import ManifestAPI

        manifest_path = (
            P.cwd()
            / ".e2e"
            / "manifests"
            / self.service_name
            / "project_knowledge.json"
        )
        api = ManifestAPI(manifest_path)
        api._load_manifest()
        return api

    def display_endpoints(self, api) -> None:
        """Display endpoints."""
        endpoints = api.get_endpoints()
        if not endpoints:
            console.print("[yellow]No endpoints found[/yellow]")
            return

        table = Table(title="Endpoints")
        table.add_column("Method", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Auth", style="yellow")

        for ep in endpoints[:20]:
            table.add_row(
                ep.http_method, ep.path[:50], "Yes" if ep.auth_required else "No"
            )

        console.print(table)


class VectorIndexBuilder:
    """Handles vector index building (Single Responsibility)."""

    def __init__(self, service_name: Optional[str] = None):
        self.service_name = service_name

    def build(self):
        """Build vector index."""
        from pathlib import Path as P

        from socialseed_e2e.project_manifest import ManifestVectorStore

        if self.service_name:
            manifest_path = (
                P.cwd()
                / ".e2e"
                / "manifests"
                / self.service_name
                / "project_knowledge.json"
            )
            store = ManifestVectorStore(manifest_path)
        else:
            store = ManifestVectorStore(P.cwd())

        store.build_index()
        return store


class SemanticSearchAgent:
    """Handles semantic search (Single Responsibility)."""

    def __init__(self, query: str, service_name: Optional[str] = None, top_k: int = 5):
        self.query = query
        self.service_name = service_name
        self.top_k = top_k

    def search(self):
        """Perform semantic search."""
        from pathlib import Path as P

        from socialseed_e2e.project_manifest import ManifestVectorStore

        if self.service_name:
            manifest_path = (
                P.cwd()
                / ".e2e"
                / "manifests"
                / self.service_name
                / "project_knowledge.json"
            )
            store = ManifestVectorStore(manifest_path)
        else:
            store = ManifestVectorStore(P.cwd())

        return store.search(self.query, top_k=self.top_k)


class RetrievalAgent:
    """Handles retrieval for RAG (Single Responsibility)."""

    def __init__(
        self, task: str, service_name: Optional[str] = None, max_chunks: int = 5
    ):
        self.task = task
        self.service_name = service_name
        self.max_chunks = max_chunks

    def retrieve(self):
        """Retrieve context for task."""
        from pathlib import Path as P

        from socialseed_e2e.project_manifest import RAGRetrievalEngine

        if self.service_name:
            manifest_path = (
                P.cwd()
                / ".e2e"
                / "manifests"
                / self.service_name
                / "project_knowledge.json"
            )
            engine = RAGRetrievalEngine(manifest_path)
        else:
            engine = RAGRetrievalEngine(P.cwd())

        return engine.retrieve_for_task(self.task, max_chunks=self.max_chunks)


@click.command()
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Force full scan instead of smart sync")
def get_manifest_command(directory: str = ".", force: bool = False):
    """Generate AI Project Manifest for token optimization.

    Analyzes the microservice and generates project_knowledge.json in the
    project's .e2e/manifests/ directory.

    Examples:
        e2e manifest ../services/auth-service  # Generate manifest for auth service
        e2e manifest /path/to/microservice     # Generate manifest for any service
        e2e manifest --force                   # Force full re-scan
    """
    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    service_name = get_service_name_from_path(target_path)

    project_root = Path.cwd()
    config_path = project_root / "e2e.conf"
    if not config_path.exists():
        project_root = project_root.parent
        config_path = project_root / "e2e.conf"

    manifest_dir = project_root / ".e2e" / "manifests" / service_name
    manifest_path = manifest_dir / "project_knowledge.json"

    console.print("\n📚 [bold cyan]Generating AI Project Manifest[/bold cyan]")
    console.print(f"   Service: {service_name}")
    console.print(f"   Source: {target_path}")
    console.print(f"   Output: {manifest_path}\n")

    try:
        generator = ManifestGenerator(target_path, project_root, service_name)
        manifest = generator.generate(force)
        generator.display_summary(manifest)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.argument("service_name")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "markdown"]),
    default="table",
    help="Output format",
)
def get_manifest_query_command(service_name: str, format: str = "table"):
    """Query the project manifest for AI context.

    Examples:
        e2e manifest-query auth-service
        e2e manifest-query auth-service -f markdown
    """
    console.print(f"\n🔍 [bold cyan]Querying manifest: {service_name}[/bold cyan]\n")

    try:
        agent = ManifestQueryAgent(service_name)
        api = agent.query()
        agent.display_endpoints(api)
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.option(
    "--service",
    "-s",
    help="Service name to build index for",
)
def get_build_index_command(service: Optional[str] = None):
    """Build vector index for semantic search.

    Examples:
        e2e build-index
        e2e build-index -s auth-service
    """
    console.print("\n📦 [bold cyan]Building vector index...[/bold cyan]\n")

    try:
        builder = VectorIndexBuilder(service_name=service)
        builder.build()
        console.print("[green]✅ Vector index built successfully![/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.argument("query")
@click.option(
    "--service",
    "-s",
    help="Service name to search in",
)
@click.option(
    "--top-k",
    "-k",
    default=5,
    help="Number of results to return",
)
def get_search_command(query: str, service: Optional[str] = None, top_k: int = 5):
    """Semantic search over project manifest.

    Examples:
        e2e search "authentication endpoints"
        e2e search "user DTO" -s auth-service
    """
    console.print(f'\n🔎 [bold cyan]Searching: "{query}"[/bold cyan]\n')

    try:
        agent = SemanticSearchAgent(query, service, top_k)
        results = agent.search()

        for result in results:
            console.print(f"  {result.item_id} (score: {result.score:.3f})")
        console.print()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.argument("task")
@click.option(
    "--service",
    "-s",
    help="Service name to retrieve from",
)
@click.option(
    "--max-chunks",
    "-m",
    default=5,
    help="Maximum chunks to retrieve",
)
def get_retrieve_command(task: str, service: Optional[str] = None, max_chunks: int = 5):
    """Retrieve context for RAG.

    Examples:
        e2e retrieve "create auth tests" -s auth-service
        e2e retrieve "test payment flow" -m 3
    """
    console.print(f'\n📄 [bold cyan]Retrieving context for: "{task}"[/bold cyan]\n')

    try:
        agent = RetrievalAgent(task, service, max_chunks)
        chunks = agent.retrieve()

        for i, chunk in enumerate(chunks, 1):
            console.print(f"[bold]Chunk {i}:[/bold] {chunk.content[:200]}...")
        console.print()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)
