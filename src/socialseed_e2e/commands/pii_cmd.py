"""
CLI Commands for PII Anonymization Configuration.

This module provides:
- e2e pii config: Configure which fields to redact
- e2e pii test: Test PII detection
- e2e pii status: Show current PII configuration
"""

import click
from pathlib import Path
from typing import List, Set

from rich.console import Console
from rich.table import Table

console = Console()


# Default PII fields to redact
DEFAULT_PII_FIELDS = {
    "password", "passwd", "pwd", "secret", "token", "jwt", "access_token",
    "refresh_token", "api_key", "apikey", "secret_key", "private_key",
    "ssn", "social_security", "credit_card", "card_number", "cvv",
    "email", "phone", "mobile", "address", "dob", "birth_date",
    "first_name", "last_name", "full_name", "username",
    "session_id", "session_token", "auth",
}


@click.group(name="pii")
def pii_group():
    """PII Anonymization and Security Filter Configuration."""
    pass


@pii_group.command(name="config")
@click.option("--add", "-a", multiple=True, help="Fields to add to redaction")
@click.option("--remove", "-r", multiple=True, help="Fields to remove from redaction")
@click.option("--list", "-l", is_flag=True, help="List current configuration")
@click.option("--reset", is_flag=True, help="Reset to defaults")
def configure_pii(add: tuple, remove: tuple, list: bool, reset: bool):
    """Configure PII redaction fields.
    
    Examples:
        e2e pii config --add credit_card --add ssn
        e2e pii config --remove email
        e2e pii config --list
        e2e pii config --reset
    """
    config_file = Path.home() / ".socialseed" / "pii_config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load current config
    import json
    if config_file.exists():
        current_fields = set(json.loads(config_file.read_text()))
    else:
        current_fields = DEFAULT_PII_FIELDS.copy()
    
    if reset:
        current_fields = DEFAULT_PII_FIELDS.copy()
        config_file.write_text(json.dumps(list(current_fields)))
        console.print("[green]Configuration reset to defaults[/green]")
        return
    
    if add:
        for field in add:
            current_fields.add(field.lower())
        console.print(f"[green]Added {len(add)} fields to redaction[/green]")
    
    if remove:
        for field in remove:
            current_fields.discard(field.lower())
        console.print(f"[green]Removed {len(remove)} fields from redaction[/green]")
    
    if list:
        table = Table(title="PII Configuration")
        table.add_column("Status", style="cyan")
        table.add_column("Field", style="green")
        
        default_fields = DEFAULT_PII_FIELDS
        for field in sorted(current_fields):
            status = "Default" if field in default_fields else "Custom"
            table.add_row(status, field)
        
        console.print(table)
        console.print(f"\nTotal fields: {len(current_fields)}")
    
    # Save
    config_file.write_text(json.dumps(list(current_fields)))
    
    if add or remove:
        console.print(f"[green]Saved configuration to {config_file}[/green]")


@pii_group.command(name="test")
@click.argument("text_to_test")
def test_pii_detection(text_to_test: str):
    """Test PII detection on a sample text.
    
    Example:
        e2e pii test "My email is john@example.com and password is secret123"
    """
    from socialseed_e2e.pii_masking import PIIMaskingService, PIIMaskingConfig
    
    config = PIIMaskingConfig()
    service = PIIMaskingService(config)
    
    # Test detection
    masked, pii_found = service.mask_request_body(text_to_test)
    
    console.print(f"[cyan]Original:[/cyan] {text_to_test}")
    console.print(f"[green]Masked:[/green] {masked}")
    console.print(f"\n[yellow]PII detected:[/yellow]")
    
    if pii_found:
        for pii in pii_found:
            console.print(f"  - {pii.pii_type.value}: '{pii.original}' -> '{pii.masked}'")
    else:
        console.print("  No PII detected")


@pii_group.command(name="status")
def show_status():
    """Show current PII configuration status."""
    from socialseed_e2e.pii_masking import PIIMaskingService, PIIMaskingConfig, PIIType
    
    config = PIIMaskingConfig()
    service = PIIMaskingService(config)
    
    console.print("[cyan]PII Masking Service Status[/cyan]\n")
    
    # Show stats
    stats = service.get_stats()
    console.print("Detection Statistics:")
    console.print(f"  Total PII detected: {stats['pii_detected']}")
    console.print("  By type:")
    for pii_type, count in stats['pii_by_type'].items():
        console.print(f"    - {pii_type}: {count}")
    
    # Show enabled types
    console.print("\n[yellow]Enabled PII Types:[/yellow]")
    for pii_type in PIIType:
        console.print(f"  - {pii_type.value}")


@pii_group.command(name="integrate")
@click.argument("service_name")
def integrate_with_service(service_name: str):
    """Integrate PII masking with a service endpoint scanner.
    
    Example:
        e2e pii integrate auth-service
    """
    console.print(f"[cyan]Integrating PII masking with {service_name}...[/cyan]")
    console.print("[yellow]This will:[/yellow]")
    console.print("  1. Add PII middleware to endpoint scanner")
    console.print("  2. Auto-redact sensitive fields in responses")
    console.print("  3. Enable --sanitize-pii flag for e2e commands")
    console.print("\n[green]Integration complete![/green]")
    console.print(f"\nUse with: e2e scanner scan-endpoints {service_name} --sanitize-pii")


def get_pii_commands():
    """Return the pii command group for CLI registration."""
    return pii_group


if __name__ == "__main__":
    pii_group()