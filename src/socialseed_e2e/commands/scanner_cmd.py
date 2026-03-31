"""
Scanner Commands - CLI commands for source code scanning and traffic generation.

This module provides commands for:
- Scanning endpoints from source code
- Scanning DTOs/schemas from source code
- Generating traffic to APIs
- Scheduling traffic generation

Usage:
    e2e scan-endpoints /path/to/project
    e2e scan-schemas /path/to/project
    e2e traffic-bot http://localhost:8085 /path/to/project --rpm 100
"""

import click
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()


@click.group(name="scanner")
def scanner_group():
    """Source code scanning and traffic generation tools."""
    pass


@scanner_group.command(name="scan-endpoints")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["table", "json", "markdown"]), default="table")
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
def scan_endpoints(project_path: str, format: str, output: Optional[str]):
    """Scan project for REST endpoints.
    
    PROJECT_PATH: Path to the project root directory
    
    Examples:
        e2e scanner scan-endpoints ../services/auth-service
        e2e scanner scan-endpoints /path/to/project --format json
    """
    from socialseed_e2e.scanner.endpoint_scanner import EndpointScanner
    
    console.print(f"[cyan]Scanning endpoints in: {project_path}[/cyan]")
    
    scanner = EndpointScanner(project_path)
    endpoints = scanner.scan()
    
    if format == "json":
        # Convert Endpoint dataclasses to dicts
        result = json.dumps([{
            "path": ep.path,
            "method": ep.method,
            "function_name": ep.function_name,
            "class_name": ep.class_name,
            "file_path": ep.file_path,
            "auth_required": ep.auth_required,
            "params": ep.params,
            "description": ep.description
        } for ep in endpoints], indent=2, default=str)
        
        if output:
            Path(output).write_text(result)
            console.print(f"[green]Saved to {output}[/green]")
        else:
            console.print(result)
    elif format == "markdown":
        md = _endpoints_to_markdown(endpoints)
        if output:
            Path(output).write_text(md)
            console.print(f"[green]Saved to {output}[/green]")
        else:
            console.print(md)
    else:
        _display_endpoints_table(endpoints)
    
    console.print(f"\n[green]Found {len(endpoints)} endpoints[/green]")


@scanner_group.command(name="scan-schemas")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["table", "json", "markdown"]), default="table")
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
def scan_schemas(project_path: str, format: str, output: Optional[str]):
    """Scan project for DTOs/Schemas.
    
    PROJECT_PATH: Path to the project root directory
    
    Examples:
        e2e scanner scan-schemas ../services/auth-service
        e2e scanner scan-schemas /path/to/project --format json
    """
    from socialseed_e2e.scanner.schema_scanner import SchemaScanner
    
    console.print(f"[cyan]Scanning schemas in: {project_path}[/cyan]")
    
    scanner = SchemaScanner(project_path)
    schemas = scanner.scan()
    
    if format == "json":
        result = json.dumps([{
            "name": s.name,
            "fields": [{"name": f.name, "field_type": f.field_type, "required": f.required} for f in s.fields],
            "file_path": s.file_path,
            "extends": s.extends,
            "implements": s.implements
        } for s in schemas], indent=2, default=str)
        
        if output:
            Path(output).write_text(result)
            console.print(f"[green]Saved to {output}[/green]")
        else:
            console.print(result)
    else:
        _display_schemas_table(schemas)
    
    console.print(f"\n[green]Found {len(schemas)} DTOs/Schemas[/green]")


@scanner_group.command(name="traffic-bot")
@click.argument("base_url")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--rpm", "-r", default=100, help="Requests per minute")
@click.option("--duration", "-d", default=60, help="Duration in seconds")
@click.option("--concurrent", "-c", default=1, help="Concurrent workers")
def traffic_bot(base_url: str, project_path: str, rpm: int, duration: int, concurrent: int):
    """Start traffic generation bot.
    
    BASE_URL: Base URL for the API (e.g., http://localhost:8085)
    PROJECT_PATH: Path to the project with source code
    
    Examples:
        e2e scanner traffic-bot http://localhost:8085 ../services/auth-service
        e2e scanner traffic-bot https://api.example.com /path/to/project --rpm 200
    """
    from socialseed_e2e.scanner.endpoint_scanner import EndpointScanner
    from socialseed_e2e.scanner.schema_scanner import SchemaScanner
    
    console.print(f"[cyan]Starting traffic bot:[/cyan]")
    console.print(f"  Base URL: {base_url}")
    console.print(f"  Project: {project_path}")
    console.print(f"  Rate: {rpm} req/min")
    console.print(f"  Duration: {duration}s")
    console.print(f"  Concurrent: {concurrent}")
    console.print()
    
    try:
        # Scan endpoints and schemas
        endpoint_scanner = EndpointScanner(project_path)
        endpoints = endpoint_scanner.scan()
        
        schema_scanner = SchemaScanner(project_path)
        schemas = schema_scanner.scan()
        
        console.print(f"[green]Found {len(endpoints)} endpoints and {len(schemas)} schemas[/green]")
        console.print("[yellow]Note: Full traffic bot requires additional setup. Use scan commands first.[/yellow]")
        
    except ImportError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Install playwright: pip install playwright && playwright install[/yellow]")


@scanner_group.command(name="traffic-scheduler")
@click.argument("base_url")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--rpm", "-r", default=100, help="Requests per minute")
@click.option("--duration", "-d", default=60, help="Duration in seconds")
@click.option("--schedule", "-s", type=click.Choice(["fixed", "interval", "random", "burst"]), default="fixed")
@click.option("--workers", "-w", default=5, help="Number of workers")
def traffic_scheduler(base_url: str, project_path: str, rpm: int, duration: int, schedule: str, workers: int):
    """Start advanced traffic scheduler.
    
    BASE_URL: Base URL for the API
    PROJECT_PATH: Path to the project with source code
    
    Examples:
        e2e scanner traffic-scheduler http://localhost:8085 /path --schedule burst
    """
    from socialseed_e2e.scanner.endpoint_scanner import EndpointScanner
    
    console.print(f"[cyan]Starting traffic scheduler:[/cyan]")
    console.print(f"  Base URL: {base_url}")
    console.print(f"  Schedule: {schedule}")
    console.print(f"  Rate: {rpm} req/min")
    console.print(f"  Workers: {workers}")
    console.print()
    
    # Scan endpoints
    scanner = EndpointScanner(project_path)
    endpoints = scanner.scan()
    
    if not endpoints:
        console.print("[yellow]No endpoints found![/yellow]")
        return
    
    # Convert to dict format for compatibility
    endpoint_dicts = [{"path": ep.path, "method": ep.method} for ep in endpoints]
    
    from socialseed_e2e.scanner.traffic_scheduler import create_scheduler, ScheduleType
    
    schedule_type = {
        "fixed": ScheduleType.FIXED_RATE,
        "interval": ScheduleType.INTERVAL,
        "random": ScheduleType.RANDOM,
        "burst": ScheduleType.BURST,
    }[schedule]
    
    scheduler = create_scheduler(
        base_url=base_url,
        endpoints=endpoint_dicts,
        schedule_type=schedule_type,
        requests_per_minute=rpm,
        concurrent_workers=workers
    )
    
    console.print(f"[green]Found {len(endpoints)} endpoints[/green]")
    console.print("[yellow]Note: Full execution requires Playwright. Use scan commands first.[/yellow]")
    console.print(scheduler.get_stats())


def _display_endpoints_table(endpoints):
    """Display endpoints in a table."""
    table = Table(title="Discovered Endpoints")
    table.add_column("Method", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Class", style="yellow")
    table.add_column("File", style="dim")
    
    for ep in endpoints:
        table.add_row(
            ep.method,
            ep.path,
            ep.class_name or "",
            (ep.file_path or "")[:50]
        )
    
    console.print(table)


def _display_schemas_table(schemas):
    """Display schemas in a table."""
    table = Table(title="Discovered DTOs/Schemas")
    table.add_column("Name", style="cyan")
    table.add_column("Extends", style="yellow")
    table.add_column("Fields", style="green")
    table.add_column("File", style="dim")
    
    for schema in schemas:
        table.add_row(
            schema.name,
            schema.extends or "",
            str(len(schema.fields)),
            (schema.file_path or "")[:50]
        )
    
    console.print(table)


def _endpoints_to_markdown(endpoints) -> str:
    """Convert endpoints to markdown format."""
    md = "# Endpoints\n\n"
    md += "| Method | Path | Class | File |\n"
    md += "|--------|------|-------|------|\n"
    
    for ep in endpoints:
        md += f"| {ep.method} | {ep.path} | {ep.class_name or ''} | {ep.file_path or ''} |\n"
    
    return md


def get_scanner_commands():
    """Return the scanner command group for CLI registration."""
    return scanner_group


if __name__ == "__main__":
    scanner_group()