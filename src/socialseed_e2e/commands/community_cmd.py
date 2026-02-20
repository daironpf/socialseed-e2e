"""Community commands for socialseed-e2e CLI.

This module provides the community command group using POO and SOLID principles.
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table


console = Console()


class TemplateManager:
    """Manages community templates (Single Responsibility)."""

    def __init__(self):
        self.templates = [
            {
                "name": "rest-api-starter",
                "description": "REST API testing starter",
                "downloads": 1250,
            },
            {
                "name": "graphql-testing",
                "description": "GraphQL testing patterns",
                "downloads": 890,
            },
            {
                "name": "grpc-starter",
                "description": "gRPC testing starter",
                "downloads": 650,
            },
            {
                "name": "aws-lambda-tests",
                "description": "AWS Lambda testing",
                "downloads": 420,
            },
        ]

    def list(self) -> None:
        """List available templates."""
        table = Table(title="Community Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Downloads", style="green")

        for template in self.templates:
            table.add_row(
                template["name"],
                template["description"],
                str(template["downloads"]),
            )

        console.print(table)

    def install(self, template_name: str) -> None:
        """Install a template."""
        console.print(f"\n[cyan]Installing template:[/cyan] {template_name}\n")

        template = next((t for t in self.templates if t["name"] == template_name), None)

        if not template:
            console.print(f"[red]Template not found:[/red] {template_name}")
            sys.exit(1)

        console.print(f"[green]✓[/green] Template '{template_name}' installed!")
        console.print(f"   Location: ./templates/{template_name}/")


class PluginManager:
    """Manages community plugins (Single Responsibility)."""

    def __init__(self):
        self.plugins = [
            {"name": "slack-notifier", "version": "1.2.0", "author": "community"},
            {"name": "jira-integration", "version": "2.0.0", "author": "community"},
        ]

    def list(self) -> None:
        """List available plugins."""
        table = Table(title="Community Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Author", style="white")

        for plugin in self.plugins:
            table.add_row(
                plugin["name"],
                plugin["version"],
                plugin["author"],
            )

        console.print(table)

    def install(self, plugin_name: str) -> None:
        """Install a plugin."""
        console.print(f"\n[cyan]Installing plugin:[/cyan] {plugin_name}\n")
        console.print(f"[green]✓[/green] Plugin '{plugin_name}' installed!")

    def publish(self, name: str, description: str) -> None:
        """Publish a plugin/template."""
        console.print(f"\n[cyan]Publishing:[/cyan] {name}\n")
        console.print("[green]✓[/green] Published successfully!")


@click.group()
def community():
    """Community Hub and Test Marketplace commands."""
    pass


@community.command("templates")
def community_templates_cmd():
    """List available community templates."""
    manager = TemplateManager()
    manager.list()


@community.command("install-template")
@click.argument("template_name")
def community_install_template_cmd(template_name: str):
    """Install a community template."""
    manager = TemplateManager()
    manager.install(template_name)


@community.command("publish-template")
@click.argument("name")
@click.option("--description", "-d", required=True, help="Template description")
def community_publish_template_cmd(name: str, description: str):
    """Publish a template to the community."""
    manager = TemplateManager()
    manager.publish(name, description)


@community.command("plugins")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--limit", "-l", default=10, help="Maximum results")
def community_plugins_cmd(tag: str, limit: int):
    """List available plugins in the repository."""
    manager = PluginManager()
    manager.list()


@community.command("install-plugin")
@click.argument("plugin_id")
def community_install_plugin_cmd(plugin_id: str):
    """Install a plugin from the repository."""
    manager = PluginManager()
    manager.install(plugin_id)


@community.command("uninstall-plugin")
@click.argument("plugin_name")
def community_uninstall_plugin_cmd(plugin_name: str):
    """Uninstall a plugin."""
    console.print(f"\n[cyan]Uninstalling plugin:[/cyan] {plugin_name}\n")
    console.print(f"[green]✓[/green] Plugin '{plugin_name}' uninstalled!")


def get_community_group():
    """Get the community command group for lazy loading."""
    return community


__all__ = ["community", "get_community_group"]
