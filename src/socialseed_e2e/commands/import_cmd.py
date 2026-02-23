"""Import commands for socialseed-e2e CLI.

This module provides the import command group using POO and SOLID principles.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

import click
import yaml
from rich.console import Console

console = Console()


class PostmanImporter:
    """Handles importing Postman collections (Single Responsibility)."""

    def import_collection(self, file_path: str) -> Dict[str, Any]:
        """Import a Postman collection."""
        path = Path(file_path)

        if not path.exists():
            console.print(f"[red]File not found:[/red] {file_path}")
            sys.exit(1)

        try:
            with open(path) as f:
                data = json.load(f)

            console.print(f"[green]✓[/green] Imported Postman collection: {path.name}")
            console.print(f"   Requests: {len(data.get('item', []))}")

            return data
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)


class OpenAPIImporter:
    """Handles importing OpenAPI specs (Single Responsibility)."""

    def import_spec(self, file_path: str) -> Dict[str, Any]:
        """Import an OpenAPI specification."""
        path = Path(file_path)

        if not path.exists():
            console.print(f"[red]File not found:[/red] {file_path}")
            sys.exit(1)

        try:
            with open(path) as f:
                if path.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            info = data.get("info", {})
            console.print(
                f"[green]✓[/green] Imported OpenAPI spec: {info.get('title', path.name)}"
            )
            console.print(f"   Version: {info.get('version', 'unknown')}")
            console.print(f"   Endpoints: {len(data.get('paths', {}))}")

            return data
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)


class CurlImporter:
    """Handles importing curl commands (Single Responsibility)."""

    def import_command(self, command: str) -> Dict[str, Any]:
        """Import a curl command."""
        # Simple curl parser
        result = {
            "method": "GET",
            "url": "",
            "headers": {},
            "data": None,
        }

        parts = command.split()
        i = 0
        while i < len(parts):
            if parts[i] == "curl":
                i += 1
                continue
            elif parts[i] in ["-X", "--request"]:
                result["method"] = parts[i + 1].upper()
                i += 2
            elif parts[i] in ["-H", "--header"]:
                header = parts[i + 1]
                if ":" in header:
                    key, value = header.split(":", 1)
                    result["headers"][key.strip()] = value.strip()
                i += 2
            elif parts[i] in ["-d", "--data", "--data-raw"]:
                result["data"] = parts[i + 1]
                result["method"] = "POST"
                i += 2
            elif not parts[i].startswith("-"):
                result["url"] = parts[i]
                i += 1
            else:
                i += 1

        console.print("[green]✓[/green] Imported curl command")
        console.print(f"   Method: {result['method']}")
        console.print(f"   URL: {result['url']}")

        return result


@click.group()
def import_cmd():
    """Import external formats into SocialSeed E2E."""
    pass


@import_cmd.command("postman")
@click.argument("file")
def import_postman_cmd(file: str):
    """Import a Postman collection.

    Examples:
        e2e import postman collection.json
    """
    console.print("\n📦 [bold cyan]Importing Postman Collection[/bold cyan]\n")
    importer = PostmanImporter()
    importer.import_collection(file)


@import_cmd.command("openapi")
@click.argument("file")
def import_openapi_cmd(file: str):
    """Import an OpenAPI specification.

    Examples:
        e2e import openapi api-spec.yaml
        e2e import openapi api-spec.json
    """
    console.print("\n📦 [bold cyan]Importing OpenAPI Specification[/bold cyan]\n")
    importer = OpenAPIImporter()
    importer.import_spec(file)


@import_cmd.command("curl")
@click.argument("command")
def import_curl_cmd(command: str):
    """Import a curl command.

    Examples:
        e2e import curl "curl -X POST https://api.example.com -d '{}'"
    """
    console.print("\n📦 [bold cyan]Importing curl Command[/bold cyan]\n")
    importer = CurlImporter()
    importer.import_command(command)


@import_cmd.command("environment")
@click.argument("file")
def import_environment_cmd(file: str):
    """Import a Postman environment file.

    Examples:
        e2e import environment dev-env.json
    """
    console.print("\n📦 [bold cyan]Importing Environment[/bold cyan]\n")
    path = Path(file)

    if not path.exists():
        console.print(f"[red]File not found:[/red] {file}")
        sys.exit(1)

    try:
        with open(path) as f:
            data = json.load(f)

        console.print(f"[green]✓[/green] Imported environment: {path.name}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def get_import_group():
    """Get the import command group for lazy loading."""
    return import_cmd


__all__ = ["import_cmd", "get_import_group"]
