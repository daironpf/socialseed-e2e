"""AI commands for socialseed-e2e CLI.

This module provides the AI-related commands (generate-tests, plan-strategy, autonomous-run, translate, gherkin-translate) using POO and SOLID principles.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


class TestGenerator:
    """Handles autonomous test suite generation (Single Responsibility)."""

    def __init__(
        self,
        directory: str,
        output: str,
        service: Optional[str],
        strategy: str,
        use_manifest: bool = False,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        self.directory = Path(directory).resolve()
        self.output = Path(output).resolve()
        self.service = service
        self.strategy = strategy
        self.use_manifest = use_manifest
        self.dry_run = dry_run
        self.verbose = verbose

    def _get_manifest_context(self) -> Optional[dict]:
        """Get context from project manifest using RAG."""
        from socialseed_e2e.project_manifest import RAGRetrievalEngine

        if not self.service:
            return None

        project_root = self.directory
        manifest_dir = project_root / ".e2e" / "manifests" / self.service

        if not manifest_dir.exists():
            console.print(
                f"[yellow]⚠ Manifest not found:[/yellow] {manifest_dir}. "
                "Run 'e2e manifest' first."
            )
            return None

        try:
            engine = RAGRetrievalEngine(manifest_dir)
            task = f"generate {self.strategy} tests for {self.service}"
            chunks = engine.retrieve_for_task(task, max_chunks=5)
            return {"chunks": chunks, "service": self.service}
        except Exception as e:
            if self.verbose:
                console.print(f"[yellow]⚠ RAG Error:[/yellow] {e}")
            return None

    def generate(self):
        """Generate test suite."""
        from socialseed_e2e.project_manifest import db_parser_registry

        console.print("\n🧪 [bold cyan]Autonomous Test Suite Generation[/bold cyan]")
        console.print(f"   Project: {self.directory}")
        console.print(f"   Output: {self.output}")
        if self.strategy != "all":
            console.print(f"   Strategy: {self.strategy}")
        if self.use_manifest:
            console.print(f"   Using: Project Manifest (RAG)")
        console.print()

        manifest_context = None
        if self.use_manifest:
            with console.status(
                "[bold yellow]Retrieving manifest context...",
                spinner="dots",
            ) as status:
                manifest_context = self._get_manifest_context()

        with console.status(
            "[bold yellow]Parsing database models...",
            spinner="dots",
        ) as status:
            db_schema = db_parser_registry.parse_project(self.directory)


class StrategyPlannerAgent:
    """Handles test strategy planning (Single Responsibility)."""

    def __init__(
        self,
        project: str,
        name: str,
        description: str,
        services: Optional[str],
        output: str,
    ):
        self.project = project
        self.name = name
        self.description = description
        self.services = services
        self.output = output

    def plan(self):
        """Generate test strategy."""
        from socialseed_e2e.ai_orchestrator import StrategyPlanner

        console.print(
            f"\n🤖 [bold cyan]Planning Test Strategy:[/bold cyan] {self.name}\n"
        )

        planner = StrategyPlanner(self.project)

        target_services = None
        if self.services:
            target_services = [s.strip() for s in self.services.split(",")]

        strategy = planner.generate_strategy(
            name=self.name,
            description=self.description or f"Auto-generated strategy for {self.name}",
            target_services=target_services,
        )

        output_path = Path(self.output) if self.output else None
        saved_path = planner.save_strategy(strategy, output_path)

        console.print(
            f"[green]✓[/green] Strategy generated: [bold]{strategy.id}[/bold]"
        )
        console.print(f"[green]✓[/green] Saved to: {saved_path}")
        console.print()


class AutonomousRunnerAgent:
    """Handles autonomous test execution (Single Responsibility)."""

    def __init__(
        self, services: Optional[str], parallel: bool, strategy_file: Optional[str]
    ):
        self.services = services
        self.parallel = parallel
        self.strategy_file = strategy_file

    def run(self):
        """Run autonomous tests."""
        from socialseed_e2e.ai_orchestrator import (
            AutonomousTestOrchestrator,
        )

        console.print("\n🚀 [bold cyan]Autonomous Test Runner[/bold cyan]\n")

        orchestrator = AutonomousTestOrchestrator()


class TranslateAgent:
    """Handles natural language to test translation (Single Responsibility)."""

    def __init__(
        self, project: str, description: str, service: str, language: str, output: str
    ):
        self.project = project
        self.description = description
        self.service = service
        self.language = language
        self.output = output

    def translate(self):
        """Translate description to test code."""
        from socialseed_e2e.ai_nlp import NLToTestTranslator

        console.print("\n🔄 [bold cyan]NLP Translation[/bold cyan]")
        console.print(f"   Description: {self.description}")
        console.print(f"   Language: {self.language}")
        console.print()

        translator = NLToTestTranslator()
        test_code = translator.translate(self.description, self.service)


class GherkinTranslator:
    """Handles Gherkin to test code translation (Single Responsibility)."""

    def __init__(self, project: str, feature_file: str, output_dir: str):
        self.project = project
        self.feature_file = feature_file
        self.output_dir = output_dir

    def translate(self):
        """Translate Gherkin to test code."""
        from socialseed_e2e.ai_nlp import GherkinToTestConverter

        console.print("\n🥒 [bold cyan]Gherkin Translation[/bold cyan]")
        console.print(f"   Feature file: {self.feature_file}")
        console.print(f"   Output: {self.output_dir}")
        console.print()

        converter = GherkinToTestConverter()


@click.command()
@click.argument("directory", default=".", required=False)
@click.option(
    "--output", "-o", default="services", help="Output directory for generated tests"
)
@click.option("--service", "-s", help="Generate tests for specific service only")
@click.option(
    "--strategy",
    type=click.Choice(["all", "flow", "crud", "validation", "chaos"]),
    default="all",
    help="Test generation strategy",
)
@click.option(
    "--use-manifest",
    is_flag=True,
    help="Use project manifest (RAG) for context-aware test generation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without creating files",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def get_generate_tests_command(
    directory: str = ".",
    output: str = "services",
    service: Optional[str] = None,
    strategy: str = "all",
    use_manifest: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
):
    """Autonomous test suite generation based on code intent (Issue #185)."""
    target_path = Path(directory).resolve()
    output_path = Path(output).resolve()

    if not target_path.exists():
        console.print(f"[red]❌ Error:[/red] Directory not found: {target_path}")
        sys.exit(1)

    if use_manifest and not service:
        console.print("[yellow]⚠ Warning:[/yellow] --use-manifest requires --service. Using default manifest search.")
        use_manifest = False

    try:
        generator = TestGenerator(
            target_path, output_path, service, strategy, use_manifest, dry_run, verbose
        )
        generator.generate()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.option("--project", "-p", default=".", help="Project directory")
@click.option("--name", "-n", required=True, help="Strategy name")
@click.option("--description", "-d", help="Strategy description")
@click.option("--services", help="Comma-separated list of services")
@click.option("--output", "-o", help="Output path for strategy file")
def get_plan_strategy_command(
    project: str = ".",
    name: str = "",
    description: Optional[str] = None,
    services: Optional[str] = None,
    output: Optional[str] = None,
):
    """Generate an AI-driven test strategy."""
    try:
        agent = StrategyPlannerAgent(
            project, name, description, services, output or "strategy.json"
        )
        agent.plan()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.option("--services", "-s", help="Comma-separated list of services to test")
@click.option("--parallel", is_flag=True, help="Run tests in parallel")
@click.option("--strategy-file", "-f", help="Path to strategy file")
def get_autonomous_run_command(
    services: Optional[str] = None,
    parallel: bool = False,
    strategy_file: Optional[str] = None,
):
    """Run tests autonomously with AI orchestration."""
    try:
        agent = AutonomousRunnerAgent(services, parallel, strategy_file)
        agent.run()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.option("--project", "-p", default=".", help="Project directory")
@click.option(
    "--description", "-d", required=True, help="Test description in natural language"
)
@click.option("--service", "-s", help="Target service name")
@click.option("--language", "-l", default="python", help="Output language")
@click.option("--output", "-o", help="Output file path")
def get_translate_command(
    project: str = ".",
    description: str = "",
    service: Optional[str] = None,
    language: str = "python",
    output: Optional[str] = None,
):
    """Translate natural language to test code."""
    try:
        agent = TranslateAgent(
            project, description, service, language, output or "test_generated.py"
        )
        agent.translate()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command()
@click.option("--project", "-p", default=".", help="Project directory")
@click.option("--feature-file", "-f", required=True, help="Gherkin feature file path")
@click.option(
    "--output-dir", "-o", default="tests", help="Output directory for generated tests"
)
def get_gherkin_translate_command(
    project: str = ".",
    feature_file: str = "",
    output_dir: str = "tests",
):
    """Convert Gherkin feature files to test code."""
    try:
        agent = GherkinTranslator(project, feature_file, output_dir)
        agent.translate()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)
