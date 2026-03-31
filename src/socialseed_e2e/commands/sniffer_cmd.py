"""
CLI Commands for Traffic Sniffer.

This module provides CLI commands for:
- Starting traffic sniffer
- Viewing captured traffic
- Managing storage
"""

import click
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()


@click.group(name="sniffer")
def sniffer_group():
    """Traffic Sniffer - Capture and analyze network traffic."""
    pass


@sniffer_group.command(name="start")
@click.option("--host", default="localhost", help="Target host")
@click.option("--port", default=8080, type=int, help="Target port")
@click.option("--mode", type=click.Choice(["reverse_proxy", "docker_sidecar"]), default="reverse_proxy")
@click.option("--output", "-o", type=click.Path(), help="Output file for captured traffic")
@click.option("--buffer-size", default=100, type=int, help="Buffer size")
def start_sniffer(host: str, port: int, mode: str, output: Optional[str], buffer_size: int):
    """Start the traffic sniffer."""
    from socialseed_e2e.traffic_sniffer import TrafficSnifferConfig
    from socialseed_e2e.traffic_sniffer.enhanced_sniffer import IsolatedTrafficSniffer, StorageType
    
    config = TrafficSnifferConfig(
        target_host=host,
        target_port=port,
        capture_mode=mode,
        output_file=Path(output) if output else None,
        buffer_size=buffer_size,
    )
    
    console.print(f"[cyan]Starting Traffic Sniffer:[/cyan]")
    console.print(f"  Mode: {mode}")
    console.print(f"  Target: {host}:{port}")
    console.print(f"  Buffer: {buffer_size}")
    
    sniffer = IsolatedTrafficSniffer(
        config=config,
        storage_type=StorageType.IN_MEMORY,
    )
    
    console.print("[green]Sniffer started. Press Ctrl+C to stop.[/green]")
    console.print(f"[yellow]Use 'e2e sniffer stats' to view captured traffic[/yellow]")
    
    try:
        sniffer.start()
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping sniffer...[/yellow]")
        sniffer.stop()


@sniffer_group.command(name="stats")
def show_stats():
    """Show traffic sniffer statistics."""
    from socialseed_e2e.traffic_sniffer.enhanced_sniffer import IsolatedTrafficSniffer
    
    # Note: In a real implementation, this would use a shared state
    # For now, show placeholder
    console.print("[yellow]Note: Start sniffer first to capture statistics[/yellow]")
    console.print("Use 'e2e sniffer start --host localhost --port 8085' to start")


@sniffer_group.command(name="capture")
@click.argument("output_file", type=click.Path())
@click.option("--count", default=10, type=int, help="Number of requests to capture")
@click.option("--timeout", default=30, type=int, help="Timeout in seconds")
def capture_traffic(output_file: str, count: int, timeout: int):
    """Capture traffic and save to file."""
    from socialseed_e2e.traffic_sniffer import TrafficSnifferConfig
    from socialseed_e2e.traffic_sniffer.enhanced_sniffer import IsolatedTrafficSniffer, StorageType
    
    config = TrafficSnifferConfig(
        target_host="localhost",
        target_port=8085,
        output_file=Path(output_file),
    )
    
    sniffer = IsolatedTrafficSniffer(
        config=config,
        storage_type=StorageType.IN_MEMORY,
    )
    
    captured = []
    
    def on_capture(traffic):
        captured.append(traffic)
        if len(captured) >= count:
            sniffer.stop()
    
    sniffer.on_traffic_captured = on_capture
    sniffer.start()
    
    import time
    start_time = time.time()
    while sniffer._running and len(captured) < count:
        if time.time() - start_time > timeout:
            break
        time.sleep(0.5)
    
    sniffer.stop()
    
    console.print(f"[green]Captured {len(captured)} requests[/green]")
    console.print(f"Saved to: {output_file}")


@sniffer_group.command(name="analyze")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
def analyze_traffic(input_file: str, format: str):
    """Analyze captured traffic from file."""
    traffic_data = []
    
    with open(input_file, 'r') as f:
        for line in f:
            traffic_data.append(json.loads(line))
    
    if format == "json":
        console.print(json.dumps(traffic_data, indent=2))
    else:
        table = Table(title=f"Traffic Analysis ({len(traffic_data)} requests)")
        table.add_column("Method", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Duration (ms)", style="magenta")
        
        for traffic in traffic_data:
            req = traffic.get("request", {})
            resp = traffic.get("response", {})
            table.add_row(
                req.get("method", ""),
                req.get("path", ""),
                str(resp.get("status_code", "")),
                f"{traffic.get('duration_ms', 0):.1f}"
            )
        
        console.print(table)


@sniffer_group.command(name="isolation-stats")
def isolation_stats():
    """Show testing traffic isolation statistics."""
    console.print("[cyan]Testing Traffic Isolation Configuration:[/cyan]")
    console.print("")
    console.print("Excluded Test Headers:")
    console.print("  - X-Test-Run")
    console.print("  - X-E2E-Test")
    console.print("  - X-Test-Id")
    console.print("")
    console.print("Excluded Test Paths:")
    console.print("  - /test/")
    console.print("  - /e2e/")
    console.print("  - /mock/")
    console.print("  - /health")
    console.print("")
    console.print("Enable isolation: Configurable via TestingIsolationConfig")


def get_sniffer_commands():
    """Return the sniffer command group for CLI registration."""
    return sniffer_group


if __name__ == "__main__":
    sniffer_group()