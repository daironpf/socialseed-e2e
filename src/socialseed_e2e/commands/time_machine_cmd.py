"""
CLI Commands for Time-Machine Debugging.

This module provides:
- e2e time-machine listen: Start error listener
- e2e time-machine list: List recorded errors
- e2e time-machine replay <id>: Replay a recorded error
- e2e time-machine info <id>: Show error details
"""

import click
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


@click.group(name="time-machine")
def time_machine_group():
    """Time-Machine Debugging - Record and replay failed requests."""
    pass


@time_machine_group.command(name="listen")
@click.option("--port", default=8085, help="Target port to monitor")
@click.option("--storage", default=".e2e/time_machine/errors", help="Storage path")
@click.option("--watch-4xx/--no-watch-4xx", default=True, help="Watch for 4xx errors")
@click.option("--watch-5xx/--no-watch-5xx", default=True, help="Watch for 5xx errors")
def start_listener(port: int, storage: str, watch_4xx: bool, watch_5xx: bool):
    """Start the error listener to capture failed requests.
    
    Example:
        e2e time-machine listen --port 8085 --storage .e2e/errors
    """
    from socialseed_e2e.time_travel.error_listener import (
        ErrorListenerConfig,
        ErrorListener,
    )
    
    config = ErrorListenerConfig(
        storage_path=Path(storage),
        trigger_on_4xx=watch_4xx,
        trigger_on_5xx=watch_5xx,
    )
    
    console.print(f"[cyan]Starting Time-Machine Error Listener:[/cyan]")
    console.print(f"  Storage: {storage}")
    console.print(f"  Watch 4xx: {watch_4xx}")
    console.print(f"  Watch 5xx: {watch_5xx}")
    console.print()
    console.print("[yellow]Note: This is a demonstration. In production,")
    console.print("connect this to the Traffic Sniffer for real-time capture.[/yellow]")


@time_machine_group.command(name="list")
@click.option("--limit", default=10, type=int, help="Number of recent errors to show")
@click.option("--severity", type=click.Choice(["all", "info", "warning", "error", "critical"]), default="all")
def list_errors(limit: int, severity: str):
    """List recorded error snapshots.
    
    Example:
        e2e time-machine list --limit 20
    """
    from socialseed_e2e.time_travel.error_listener import (
        ErrorListener,
        ErrorSeverity,
    )
    
    storage_path = Path(".e2e/time_machine/errors")
    
    if not storage_path.exists():
        console.print("[yellow]No errors recorded yet. Run 'e2e time-machine listen' first.[/yellow]")
        return
    
    listener = ErrorListener()
    snapshots = listener.get_recent_snapshots(limit)
    
    if not snapshots:
        console.print("[yellow]No error snapshots found.[/yellow]")
        return
    
    # Filter by severity if needed
    if severity != "all":
        severity_enum = ErrorSeverity(severity)
        snapshots = [s for s in snapshots if s.severity == severity_enum]
    
    table = Table(title=f"Recorded Errors (Last {len(snapshots)})")
    table.add_column("Incident ID", style="cyan")
    table.add_column("Time", style="dim")
    table.add_column("Method", style="yellow")
    table.add_column("Path", style="green")
    table.add_column("Status", style="red")
    table.add_column("Severity", style="magenta")
    
    for snapshot in snapshots:
        table.add_row(
            snapshot.incident_id,
            snapshot.timestamp.strftime("%H:%M:%S"),
            snapshot.method,
            snapshot.path[:40],
            str(snapshot.status_code),
            snapshot.severity.value,
        )
    
    console.print(table)


@time_machine_group.command(name="info")
@click.argument("incident_id")
def show_error_info(incident_id: str):
    """Show detailed information about an error.
    
    Example:
        e2e time-machine info INC-abc123
    """
    from socialseed_e2e.time_travel.error_listener import ErrorListener
    
    listener = ErrorListener()
    snapshot = listener.get_snapshot_by_id(incident_id)
    
    if not snapshot:
        console.print(f"[red]Error: Incident {incident_id} not found[/red]")
        return
    
    console.print(f"[cyan]Incident: {snapshot.incident_id}[/cyan]")
    console.print(f"Time: {snapshot.timestamp.isoformat()}")
    console.print(f"Severity: {snapshot.severity.value}")
    console.print(f"Trigger: {snapshot.trigger_type.value}")
    console.print()
    
    console.print("[yellow]Request:[/yellow]")
    console.print(f"  Method: {snapshot.method}")
    console.print(f"  Path: {snapshot.path}")
    console.print(f"  Headers: {len(snapshot.headers)} items")
    
    console.print()
    console.print("[yellow]Response:[/yellow]")
    console.print(f"  Status: {snapshot.status_code}")
    if snapshot.error_message:
        console.print(f"  Error: {snapshot.error_message}")
    
    console.print()
    console.print("[yellow]Environment:[/yellow]")
    for key in list(snapshot.environment_variables.keys())[:5]:
        console.print(f"  {key}: {snapshot.environment_variables[key][:30]}...")


@time_machine_group.command(name="replay")
@click.argument("incident_id")
@click.option("--base-url", default="http://localhost:8085", help="Base URL to replay against")
@click.option("--mock/--no-mock", default=False, help="Use mock response instead of real request")
def replay_error(incident_id: str, base_url: str, mock: bool):
    """Replay a recorded error request.
    
    Example:
        e2e time-machine replay INC-abc123 --base-url http://localhost:8085
    """
    from socialseed_e2e.time_travel.error_listener import ErrorListener, ErrorReplay
    
    # Get snapshot
    listener = ErrorListener()
    snapshot = listener.get_snapshot_by_id(incident_id)
    
    if not snapshot:
        console.print(f"[red]Error: Incident {incident_id} not found[/red]")
        return
    
    console.print(f"[cyan]Replaying incident: {incident_id}[/cyan]")
    console.print(f"Original request: {snapshot.method} {snapshot.path}")
    console.print(f"Original status: {snapshot.status_code}")
    console.print(f"Base URL: {base_url}")
    console.print(f"Mock mode: {mock}")
    console.print()
    
    # Replay
    replay = ErrorReplay(base_url=base_url)
    result = replay.replay_snapshot(snapshot, mock_responses=mock)
    
    if result.get("success"):
        console.print("[green]✓ Request completed[/green]")
        console.print(f"  Status: {result.get('status_code', 'N/A')}")
        console.print(f"  Duration: {result.get('duration_ms', 0):.1f}ms")
    else:
        console.print("[red]✗ Request failed[/red]")
        console.print(f"  Error: {result.get('error', 'Unknown')}")


@time_machine_group.command(name="clear")
@click.confirmation_option(prompt="Are you sure you want to clear all recorded errors?")
def clear_errors():
    """Clear all recorded error snapshots."""
    from shutil import rmtree
    
    storage_path = Path(".e2e/time_machine/errors")
    
    if storage_path.exists():
        rmtree(storage_path)
        console.print("[green]Cleared all recorded errors[/green]")
    else:
        console.print("[yellow]No errors to clear[/yellow]")


def get_time_machine_commands():
    """Return the time-machine command group for CLI registration."""
    return time_machine_group


if __name__ == "__main__":
    time_machine_group()