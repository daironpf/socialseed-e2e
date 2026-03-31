"""Observe command for socialseed-e2e CLI.

This module provides the observe command using POO and SOLID principles.
"""

import socket
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class PortResult:
    """Represents a port scan result."""

    port: int
    service: str
    status: str


class PortScanner:
    """Handles port scanning for service discovery (Single Responsibility)."""

    COMMON_PORTS = {
        3000: "Node.js",
        5000: "REST Demo",
        5003: "Auth Demo",
        5173: "Vite",
        8000: "Python/Django",
        8080: "Spring Boot/Java",
        8081: "Alt HTTP",
        8085: "Java App",
        8765: "Mock API",
        3001: "React",
        4000: "GraphQL",
        5001: "HTTPS",
        50051: "gRPC",
        50052: "WebSocket",
        9000: "PHP-FPM",
    }

    def __init__(self, host: str = "localhost"):
        self.host = host

    def scan_port(self, port: int, timeout: float = 1.0) -> Optional[PortResult]:
        """Scan a single port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            result = sock.connect_ex((self.host, port))
            sock.close()

            if result == 0:
                return PortResult(
                    port=port,
                    service=self.COMMON_PORTS.get(port, "Unknown"),
                    status="Open",
                )
        except Exception:
            pass

        return None

    def scan_range(self, start_port: int, end_port: int) -> List[PortResult]:
        """Scan a range of ports."""
        results = []

        console.print(f"Scanning {self.host}:{start_port}-{end_port}...")

        for port in range(start_port, end_port + 1):
            result = self.scan_port(port)
            if result:
                results.append(result)
                console.print(f"  Found: {port} ({result.service})")

        return results


class ServiceDiscoverer:
    """Discovers services in the network (Single Responsibility)."""

    def __init__(self, host: str = "localhost"):
        self.scanner = PortScanner(host)

    def discover(self, start_port: int, end_port: int) -> List[PortResult]:
        """Discover services in the given port range."""
        return self.scanner.scan_range(start_port, end_port)

    def display_results(self, results: List[PortResult]) -> None:
        """Display discovery results."""
        if not results:
            console.print("[yellow]No services found.[/yellow]")
            return

        table = Table(title="Discovered Services")
        table.add_column("Port", style="cyan")
        table.add_column("Service", style="green")
        table.add_column("Status", style="yellow")

        for result in results:
            table.add_row(str(result.port), result.service, result.status)

        console.print(table)
        console.print(f"\n[green]Found {len(results)} service(s).[/green]")


@click.command()
@click.option("--host", default="localhost", help="Host to scan")
@click.option("--ports", default="8000-9000", help="Port range to scan (e.g., 8000-9000)")
@click.option("--docker", is_flag=True, help="Scan Docker containers")
@click.option("--auto-config", is_flag=True, help="Automatically generate e2e.conf")
def observe_cmd(host: str, ports: str, docker: bool, auto_config: bool):
    """Auto-detect services and ports in the network.
    
    Scans the specified port range to detect running services.
    
    Examples:
        e2e observe                           # Scan default range
        e2e observe --host 192.168.1.1     # Scan specific host
        e2e observe --ports 3000-4000      # Custom port range
        e2e observe --docker                 # Scan Docker containers
        e2e observe --auto-config            # Generate e2e.conf automatically
    """
    console.print("\n🔍 [bold cyan]Service Discovery[/bold cyan]\n")
    
    from socialseed_e2e.scanner.port_detector import PortScanner, ServiceConfigGenerator
    
    detector = PortScanner()
    generator = ServiceConfigGenerator()
    
    if docker:
        console.print("🐳 Detecting Docker containers...")
        docker_services = detector.detect_docker_services()
        
        if docker_services:
            table = Table(title="Docker Services")
            table.add_column("Name", style="cyan")
            table.add_column("Port", style="green")
            table.add_column("Container ID", style="yellow")
            
            for s in docker_services:
                table.add_row(s.name, str(s.port), s.container_id[:12] if s.container_id else "N/A")
            
            console.print(table)
        else:
            console.print("[yellow]No Docker containers found.[/yellow]")
    
    # Parse port range
    if "-" in ports:
        start_port, end_port = map(int, ports.split("-"))
    else:
        start_port, end_port = 8000, 9000
    
    console.print(f"\n🔍 Scanning {host}:{start_port}-{end_port}...")
    
    services = detector.scan_ports(start_port, end_port, [host])
    
    if not services:
        console.print("[yellow]No services found.[/yellow]")
        return
    
    # Check health endpoints
    for service in services:
        detector.check_health(service)
    
    table = Table(title="Discovered Services")
    table.add_column("Port", style="cyan")
    table.add_column("Service", style="green")
    table.add_column("Health", style="yellow")
    table.add_column("Response", style="magenta")
    
    for s in services:
        health = "✓" if s.health_endpoint else "✗"
        response = f"{s.response_time_ms:.0f}ms" if s.response_time_ms > 0 else "-"
        table.add_row(str(s.port), s.name, health, response)
    
    console.print(table)
    console.print(f"\n[green]Found {len(services)} service(s).[/green]")
    
    # Auto-config generation
    if auto_config:
        console.print("\n⚙️  Generating e2e.conf...")
        config = generator.generate_config(services)
        
        import json
        config_json = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "services": config,
        }
        
        with open("e2e.conf", "w") as f:
            json.dump(config_json, f, indent=2)
        
        console.print("[green]✓ Configuration saved to e2e.conf[/green]")


def get_observe_command():
    """Get the observe command for lazy loading."""
    return observe_cmd


__all__ = ["observe_cmd", "get_observe_command"]
