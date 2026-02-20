"""Config command for socialseed-e2e CLI.

This module provides the config command to show and validate configuration.
"""

import sys
from typing import Tuple

import click
from rich.console import Console
from rich.table import Table

from socialseed_e2e.core.config_loader import ApiConfigLoader, ConfigError

console = Console()


def _check_service_health(
    base_url: str, health_endpoint: str, timeout: int = 5
) -> Tuple[bool, str]:
    """Check if a service health endpoint is accessible.

    Args:
        base_url: Service base URL
        health_endpoint: Health check endpoint path
        timeout: Request timeout in seconds

    Returns:
        Tuple of (is_healthy, status_message)
    """
    import requests

    if not health_endpoint or health_endpoint == "N/A":
        return False, "⚫ Not configured"

    url = f"{base_url.rstrip('/')}/{health_endpoint.lstrip('/')}"
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, "🟢 Healthy"
        else:
            return False, f"🔴 Error ({response.status_code})"
    except requests.exceptions.Timeout:
        return False, "🔴 Timeout"
    except requests.exceptions.ConnectionError:
        return False, "🔴 Connection failed"
    except Exception as e:
        return False, f"🔴 {type(e).__name__}"


@click.command()
def config_cmd():
    """Show and validate current configuration.

    Shows the configuration loaded from e2e.conf and validates its syntax.
    """
    console.print("\n⚙️  [bold blue]E2E Configuration[/bold blue]\n")

    try:
        loader = ApiConfigLoader()
        config = loader.load()

        console.print(f"📋 [cyan]Configuration:[/cyan] {loader._config_path}")
        console.print(f"🌍 [cyan]Environment:[/cyan] {config.environment}")
        console.print(f"[cyan]Timeout:[/cyan] {config.timeout}ms")
        console.print(f"[cyan]Verbose:[/cyan] {config.verbose}")
        console.print()

        if config.services:
            table = Table(title="Configured Services")
            table.add_column("Name", style="cyan")
            table.add_column("Base URL", style="green")
            table.add_column("Health", style="yellow")
            table.add_column("Required", style="white")

            for name, svc in config.services.items():
                display_name = svc.name if svc.name else name
                table.add_row(
                    display_name,
                    svc.base_url,
                    svc.health_endpoint or "N/A",
                    "✓" if svc.required else "✗",
                )

            console.print(table)
        else:
            console.print("[yellow]⚠ No services configured[/yellow]")
            console.print("   Use: [cyan]e2e new-service <name>[/cyan]")

        if config.services:
            console.print()
            console.print("[bold cyan]🌐 Checking Service Health...[/bold cyan]")

            health_table = Table(title="Live Service Status")
            health_table.add_column("Service", style="cyan")
            health_table.add_column("Health Endpoint", style="yellow")
            health_table.add_column("Status", style="bold")

            healthy_count = 0
            for name, svc in config.services.items():
                health_url = svc.health_endpoint or "/actuator/health"
                is_healthy, status_msg = _check_service_health(svc.base_url, health_url)
                if is_healthy:
                    healthy_count += 1
                health_table.add_row(name, health_url, status_msg)

            console.print(health_table)
            console.print(
                f"\n[bold]{healthy_count}/{len(config.services)} services healthy[/bold]"
            )

        console.print()
        console.print("[bold green]✅ Valid configuration[/bold green]")

    except ConfigError as e:
        console.print(f"[red]❌ Configuration error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error:[/red] {e}")
        sys.exit(1)


def get_config_command():
    """Get the config command for lazy loading."""
    return config_cmd


__all__ = ["config_cmd", "get_config_command"]
