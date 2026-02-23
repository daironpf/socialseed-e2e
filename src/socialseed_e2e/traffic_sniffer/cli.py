import argparse
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from . import CapturedTraffic, TrafficSniffer, TrafficSnifferConfig

console = Console()


def create_sniffer(
    docker_network_id: Optional[str] = None,
    target_port: int = 8080,
    target_host: str = "localhost",
    output_file: Optional[Path] = None,
    mode: str = "reverse_proxy",
) -> TrafficSniffer:
    config = TrafficSnifferConfig(
        docker_network_id=docker_network_id,
        target_port=target_port,
        target_host=target_host,
        output_file=output_file,
        capture_mode=mode,
    )
    return TrafficSniffer(config)


def cmd_sniffer_start(args: argparse.Namespace) -> int:
    sniffer = create_sniffer(
        docker_network_id=args.network,
        target_port=args.port,
        target_host=args.host,
        output_file=Path(args.output) if args.output else None,
        mode=args.mode,
    )

    console.print(f"[green]Starting traffic sniffer on {args.host}:{args.port}[/green]")
    console.print(f"[dim]Mode: {args.mode}[/dim]")

    def on_traffic(traffic: CapturedTraffic):
        console.print(
            f"[cyan]{traffic.request.method}[/cyan] "
            f"[yellow]{traffic.request.path}[/yellow] "
            f"[blue]{traffic.response.status_code}[/blue] "
            f"[dim]{traffic.duration_ms:.2f}ms[/dim]"
        )

    sniffer.on_traffic_captured = on_traffic
    sniffer.start()

    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping sniffer...[/yellow]")
        sniffer.stop()

    return 0


def cmd_sniffer_docker(args: argparse.Namespace) -> int:
    console.print("[green]Starting Docker sidecar sniffer[/green]")
    console.print(f"[dim]Network: {args.network}[/dim]")
    console.print(f"[dim]Target Port: {args.port}[/dim]")

    sniffer = create_sniffer(
        docker_network_id=args.network,
        target_port=args.port,
        target_host="127.0.0.1",
        mode="docker_sidecar",
    )
    sniffer.start()

    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sniffer.stop()

    return 0


def cmd_sniffer_list(args: argparse.Namespace) -> int:
    table = Table(title="Traffic Sniffer Status")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Mode", args.mode or "reverse_proxy")
    table.add_row("Port", str(args.port))
    table.add_row("Host", args.host)

    console.print(table)
    return 0


def add_sniffer_commands(subparsers) -> None:
    parser = subparsers.add_parser("sniffer", help="Traffic Sniffer commands")
    sub = parser.add_subparsers(dest="sniffer_cmd", help="Sniffer subcommands")

    start_parser = sub.add_parser("start", help="Start traffic sniffer")
    start_parser.add_argument("--host", default="localhost", help="Target host")
    start_parser.add_argument("--port", type=int, default=8080, help="Target port")
    start_parser.add_argument("--network", help="Docker network ID")
    start_parser.add_argument("--output", "-o", help="Output file for captured traffic")
    start_parser.add_argument(
        "--mode", choices=["reverse_proxy", "docker_sidecar"], default="reverse_proxy"
    )
    start_parser.set_defaults(func=cmd_sniffer_start)

    docker_parser = sub.add_parser("docker", help="Run as Docker sidecar")
    docker_parser.add_argument("--network", required=True, help="Docker network ID")
    docker_parser.add_argument("--port", type=int, default=8080, help="Target port")
    docker_parser.set_defaults(func=cmd_sniffer_docker)

    list_parser = sub.add_parser("status", help="Show sniffer status")
    list_parser.add_argument("--host", default="localhost")
    list_parser.add_argument("--port", type=int, default=8080)
    list_parser.add_argument("--mode")
    list_parser.set_defaults(func=cmd_sniffer_list)
