"""Observe command for socialseed-e2e CLI.

This module provides the observe command using POO and SOLID principles.
"""

import socket
from dataclasses import dataclass
from typing import Dict, List, Optional

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
        8000: "FastAPI",
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
@click.option(
    "--ports", default="8000-9000", help="Port range to scan (e.g., 8000-9000)"
)
@click.option("--docker", is_flag=True, help="Scan common Docker ports")
def observe_cmd(host: str, ports: str, docker: bool):
    """Auto-detect services and ports in the network.

    Scans the specified port range to detect running services.

    Examples:
        e2e observe                           # Scan default range
        e2e observe --host 192.168.1.1     # Scan specific host
        e2e observe --ports 3000-4000      # Custom port range
        e2e observe --docker                 # Scan Docker ports
    """
    console.print("\n🔍 [bold cyan]Service Discovery[/bold blue]\n")

    # Parse port range
    if docker:
        start_port, end_port = 7000, 9100
    elif "-" in ports:
        start_port, end_port = map(int, ports.split("-"))
    else:
        start_port, end_port = 8000, 9000

    discoverer = ServiceDiscoverer(host)
    results = discoverer.discover(start_port, end_port)
    discoverer.display_results(results)


def get_observe_command():
    """Get the observe command for lazy loading."""
    return observe_cmd


__all__ = ["observe_cmd", "get_observe_command"]
