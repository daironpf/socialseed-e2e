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
@click.option(
    "--to-manifest",
    "-m",
    is_flag=True,
    help="Generate project_knowledge.json from the collection",
)
def import_postman_cmd(file: str, to_manifest: bool):
    """Import a Postman collection.

    Examples:
        e2e import postman collection.json
        e2e import postman collection.json --to-manifest
    """
    console.print("\n📦 [bold cyan]Importing Postman Collection[/bold cyan]\n")
    importer = PostmanImporter()
    data = importer.import_collection(file)
    
    if to_manifest:
        _generate_manifest_from_import(data, "postman", file)


@import_cmd.command("openapi")
@click.argument("file")
@click.option(
    "--to-manifest",
    "-m",
    is_flag=True,
    help="Generate project_knowledge.json from the spec",
)
def import_openapi_cmd(file: str, to_manifest: bool):
    """Import an OpenAPI specification.

    Examples:
        e2e import openapi api-spec.yaml
        e2e import openapi api-spec.yaml --to-manifest
    """
    console.print("\n📦 [bold cyan]Importing OpenAPI Specification[/bold cyan]\n")
    importer = OpenAPIImporter()
    data = importer.import_spec(file)
    
    if to_manifest:
        _generate_manifest_from_import(data, "openapi", file)


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


def _generate_manifest_from_import(
    data: Dict[str, Any], import_type: str, source_file: str
) -> None:
    """Generate project_knowledge.json from imported data.
    
    Args:
        data: Parsed import data
        import_type: Type of import ('postman' or 'openapi')
        source_file: Source file path
    """
    manifest = {
        "service_name": Path(source_file).stem,
        "source": import_type,
        "version": "1.0.0",
        "base_url": "",
        "endpoints": [],
        "schemas": {},
    }
    
    if import_type == "openapi":
        info = data.get("info", {})
        manifest["service_name"] = info.get("title", Path(source_file).stem)
        manifest["base_url"] = data.get("servers", [{}])[0].get("url", "")
        
        for path, methods in data.get("paths", {}).items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "operationId": details.get("operationId", ""),
                    }
                    
                    params = details.get("parameters", [])
                    if params:
                        endpoint["parameters"] = [
                            {
                                "name": p.get("name"),
                                "in": p.get("in"),
                                "required": p.get("required", False),
                                "schema": p.get("schema", {}),
                            }
                            for p in params
                        ]
                    
                    request_body = details.get("requestBody", {})
                    if request_body:
                        endpoint["request_body"] = {
                            "content": request_body.get("content", {}),
                            "required": request_body.get("required", False),
                        }
                    
                    responses = details.get("responses", {})
                    if responses:
                        endpoint["responses"] = {
                            code: resp.get("description", "")
                            for code, resp in responses.items()
                        }
                    
                    manifest["endpoints"].append(endpoint)
                    
                    for code, resp in responses.items():
                        content = resp.get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            schema_name = details.get("operationId", f"Response{code}")
                            manifest["schemas"][schema_name] = schema
    
    elif import_type == "postman":
        info = data.get("info", {})
        manifest["service_name"] = info.get("name", Path(source_file).stem)
        manifest["description"] = info.get("description", "")
        
        for item in data.get("item", []):
            _extract_postman_item(item, manifest["endpoints"])
    
    output_path = Path.cwd() / ".e2e" / "manifests" / manifest["service_name"]
    output_path.mkdir(parents=True, exist_ok=True)
    
    manifest_file = output_path / "project_knowledge.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    console.print(f"   [green]✓[/green] Generated manifest: {manifest_file}")


def _extract_postman_item(item: Dict[str, Any], endpoints: list) -> None:
    """Recursively extract endpoints from Postman collection items."""
    if "request" in item:
        request = item["request"]
        method = request.get("method", "GET")
        url = request.get("url", {})
        
        if isinstance(url, dict):
            path = url.get("path", [])
            path = "/" + "/".join(path) if path else "/"
        else:
            path = url
        
        endpoint = {
            "path": path,
            "method": method.upper(),
            "name": item.get("name", ""),
        }
        
        headers = request.get("header", [])
        if headers:
            endpoint["headers"] = [
                {"key": h.get("key"), "value": h.get("value")}
                for h in headers
            ]
        
        body = request.get("body", {})
        if body:
            endpoint["body"] = body
        
        endpoints.append(endpoint)
    
    if "item" in item:
        for sub_item in item["item"]:
            _extract_postman_item(sub_item, endpoints)


def get_import_group():
    """Get the import command group for lazy loading."""
    return import_cmd


__all__ = ["import_cmd", "get_import_group"]
