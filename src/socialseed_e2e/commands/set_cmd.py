"""Set configuration commands for socialseed-e2e CLI.

This module provides the set command group using POO and SOLID principles.
"""

import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console


console = Console()


class ConfigManager:
    """Manages e2e.conf configuration (Single Responsibility)."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("e2e.conf")

    def load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            console.print(
                f"[red]❌ Error:[/red] Configuration file not found: {self.config_path}"
            )
            console.print(
                "[yellow]Tip:[/yellow] Run 'e2e init' to create a new configuration file."
            )
            sys.exit(1)

        try:
            with open(self.config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            console.print(f"[red]❌ Error parsing configuration file:[/red] {e}")
            sys.exit(1)

        return config_data

    def save_config(self, config_data: dict) -> None:
        """Save configuration to YAML file."""
        try:
            with open(self.config_path, "w") as f:
                yaml.safe_dump(
                    config_data, f, default_flow_style=False, sort_keys=False
                )
        except yaml.YAMLError as e:
            console.print(f"[red]❌ Error saving configuration file:[/red] {e}")
            sys.exit(1)

    def get_service(self, service_name: str) -> Optional[dict]:
        """Get a service configuration."""
        config_data = self.load_config()
        services = config_data.get("services", {}) or {}
        return services.get(service_name)

    def set_service_url(
        self, service_name: str, url: str, health_endpoint: Optional[str] = None
    ) -> None:
        """Set or update service URL."""
        config_data = self.load_config()

        # Ensure services section exists
        if "services" not in config_data or config_data.get("services") is None:
            config_data["services"] = {}

        # Update or add service
        if service_name in config_data["services"]:
            config_data["services"][service_name]["base_url"] = url
            if health_endpoint:
                config_data["services"][service_name]["health_endpoint"] = (
                    health_endpoint
                )
            console.print(f"[green]✓[/green] Updated base_url for '{service_name}'")
        else:
            config_data["services"][service_name] = {
                "base_url": url,
            }
            if health_endpoint:
                config_data["services"][service_name]["health_endpoint"] = (
                    health_endpoint
                )
            console.print(f"[green]✓[/green] Added service '{service_name}'")

        self.save_config(config_data)
        console.print(f"[green]✓[/green] Configuration saved to {self.config_path}")


class URLValidator:
    """Validates URLs (Single Responsibility)."""

    @staticmethod
    def validate(url: str) -> bool:
        """Validate URL format."""
        if not url.startswith(("http://", "https://")):
            console.print(
                f"[red]❌ Error:[/red] URL must start with http:// or https://"
            )
            console.print(f"[yellow]Example:[/yellow] https://api.example.com:443")
            return False
        return True


@click.group("set")
def set_group():
    """Configuration management commands.

    Examples:
        e2e set url <service> <url>     # Set service URL
        e2e set url auth_service https://api.example.com:443
    """
    pass


@set_group.command("url")
@click.argument("service_name")
@click.argument("url")
@click.option("--config", "-c", help="Path to configuration file (e2e.conf)")
@click.option("--health-endpoint", "-e", help="Health endpoint for the service")
def set_url_cmd(
    service_name: str,
    url: str,
    config: Optional[str],
    health_endpoint: Optional[str],
):
    """Set or update the URL for a service in e2e.conf.

    Examples:
        e2e set url auth_service https://my-api.azurewebsites.net
        e2e set url auth_service https://api.example.com:443
        e2e set url payment_service https://my-api.execute-api.us-east-1.amazonaws.com
        e2e set url auth_service http://localhost:8085 -c custom.conf
        e2e set url auth_service https://api.example.com --health-endpoint /health
    """
    config_path = Path(config) if config else None
    manager = ConfigManager(config_path)

    if not URLValidator.validate(url):
        sys.exit(1)

    manager.set_service_url(service_name, url, health_endpoint)


def get_set_group():
    """Get the set command group for lazy loading."""
    return set_group


__all__ = ["set_group", "get_set_group", "ConfigManager"]
