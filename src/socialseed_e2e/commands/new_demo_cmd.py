"""New demo command for socialseed-e2e CLI.

Creates a new demo API using the demo factory.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from socialseed_e2e.demo_factory import create_demo_factory, DemoConfig


console = Console()


class NewDemoCommand:
    """Handles creation of new demo APIs."""

    DEMO_PRESETS = {
        "crud": DemoConfig(
            name="crud",
            port=5016,
            title="CRUD Demo API",
            description="A simple CRUD API",
            entities=["item"],
            features=["Create", "Read", "Update", "Delete"],
        ),
        "blog": DemoConfig(
            name="blog",
            port=5017,
            title="Blog API",
            description="A blog API with posts and comments",
            entities=["post", "comment"],
            features=["Posts", "Comments", "Authors"],
        ),
        "task": DemoConfig(
            name="task",
            port=5018,
            title="Task Management API",
            description="Task management with boards and columns",
            entities=["task", "board", "column"],
            features=["Boards", "Tasks", "Assignees"],
        ),
    }

    def __init__(self, name: str, port: int, preset: str, force: bool):
        self.name = name
        self.port = port
        self.preset = preset
        self.force = force

    def execute(self):
        """Execute the demo creation."""
        target_path = Path.cwd()

        # Get config from preset or use defaults
        if self.preset and self.preset in self.DEMO_PRESETS:
            config = self.DEMO_PRESETS[self.preset]
            config.name = self.name
            config.port = self.port
        else:
            config = DemoConfig(
                name=self.name,
                port=self.port,
                title=f"{self.name.title()} Demo API",
                description=f"A {self.name} demo API",
                entities=[self.name],
                features=["CRUD"],
            )

        # Create factory and generate demo
        factory = create_demo_factory(self.name, self.port, target_path)

        console.print(f"\n🎯 [bold green]Creating demo:[/bold green] {self.name}")
        console.print(f"   Port: {self.port}")

        results = factory.create_all()

        # Show results
        table = Table(title="Created Files")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")

        for component, success in results.items():
            status = "✓" if success else "✗"
            table.add_row(component, status)

        console.print(table)
        console.print(
            f"\n[bold green]✅ Demo '{self.name}' created successfully![/bold green]\n"
        )
        console.print(
            f"Run with: [cyan]python demos/{self.name}/api_{self.name}_demo.py[/cyan]"
        )


@click.command()
@click.argument("name")
@click.option("--port", "-p", default=5016, help="Port for the demo API")
@click.option(
    "--preset",
    "-t",
    type=click.Choice(["crud", "blog", "task"]),
    help="Use a preset configuration",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
def new_demo(name: str, port: int, preset: str, force: bool):
    """Create a new demo API.

    Examples:
        e2e new-demo myapi --port 5016
        e2e new-demo blog --preset blog
        e2e new-demo tasks --preset task --force
    """
    command = NewDemoCommand(name, port, preset, force)
    command.execute()


def get_new_demo_command():
    """Get the new-demo command for lazy loading."""
    return new_demo
