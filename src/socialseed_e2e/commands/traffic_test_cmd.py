"""
CLI Commands for Traffic-based Test Generator.

This module provides:
- e2e traffic-test generate: Generate tests from captured traffic
- e2e traffic-test analyze-flow: Analyze traffic flows
"""

import click
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


@click.group(name="traffic-test")
def traffic_test_group():
    """Traffic-based test generation from captured traffic."""
    pass


@traffic_test_group.command(name="generate")
@click.argument("traffic_file", type=click.Path(exists=True))
@click.option("--service", "-s", required=True, help="Service name for generated tests")
@click.option("--output", "-o", type=click.Path(), default="services", help="Output directory")
@click.option("--module-count", "-m", default=1, type=int, help="Number of test modules to generate")
def generate_from_traffic(traffic_file: str, service: str, output: str, module_count: int):
    """Generate tests from captured traffic file.
    
    TRAFFIC_FILE: Path to captured traffic JSON file
    
    Example:
        e2e traffic-test generate captured_traffic.json --service auth-service
    """
    import json
    
    console.print(f"[cyan]Generating tests from: {traffic_file}[/cyan]")
    console.print(f"  Service: {service}")
    console.print(f"  Output: {output}")
    console.print(f"  Modules: {module_count}")
    
    # Load captured traffic
    interactions = []
    with open(traffic_file, 'r') as f:
        for line in f:
            interactions.append(json.loads(line))
    
    if not interactions:
        console.print("[yellow]No traffic data found![/yellow]")
        return
    
    console.print(f"[green]Loaded {len(interactions)} interactions[/green]")
    
    # Generate test modules
    from socialseed_e2e.traffic_test_generator import (
        ModularTestGenerator,
        TestIntegrator,
    )
    
    generator = ModularTestGenerator(service)
    integrator = TestIntegrator(Path(output))
    
    test_modules = []
    for i in range(module_count):
        module = generator.generate_test_module(interactions, i + 1)
        test_modules.append(module)
        console.print(f"  Generated: {module.filename}")
    
    # Integrate into service folder
    paths = integrator.integrate_multiple_modules(test_modules, service)
    
    console.print(f"\n[green]✓ Generated {len(paths)} test modules:[/green]")
    for path in paths:
        console.print(f"    - {path}")


@traffic_test_group.command(name="analyze-flow")
@click.argument("traffic_file", type=click.Path(exists=True))
def analyze_flow(traffic_file: str):
    """Analyze traffic flows and show session groupings.
    
    TRAFFIC_FILE: Path to captured traffic JSON file
    
    Example:
        e2e traffic-test analyze-flow captured_traffic.json
    """
    import json
    
    console.print(f"[cyan]Analyzing traffic flows from: {traffic_file}[/cyan]")
    
    # Load captured traffic
    interactions = []
    with open(traffic_file, 'r') as f:
        for line in f:
            interactions.append(json.loads(line))
    
    if not interactions:
        console.print("[yellow]No traffic data found![/yellow]")
        return
    
    # Analyze flows
    from socialseed_e2e.traffic_test_generator import TrafficFlowAnalyzer
    
    analyzer = TrafficFlowAnalyzer()
    flow_groups = analyzer.group_by_session(interactions)
    
    console.print(f"\n[green]Found {len(flow_groups)} flow groups:[/green]\n")
    
    for session_id, flow in flow_groups.items():
        console.print(f"[cyan]Session: {session_id[:30]}...[/cyan]")
        console.print(f"  Type: {flow.flow_type}")
        console.print(f"  Entry: {flow.entry_point}")
        console.print(f"  Requests: {len(flow.interactions)}")
        
        for i, req in enumerate(flow.interactions, 1):
            method = req.get('request', {}).get('method', 'GET')
            path = req.get('request', {}).get('path', '/')
            console.print(f"    {i}. {method} {path}")
        console.print()


@traffic_test_group.command(name="list-templates")
def list_templates():
    """List available test templates."""
    console.print("[cyan]Available Test Templates:[/cyan]\n")
    
    templates = [
        ("01_auth_flow.py", "Authentication flow (login -> profile)"),
        ("02_register_flow.py", "User registration flow"),
        ("03_crud_flow.py", "Create, Read, Update, Delete flow"),
        ("04_profile_flow.py", "Profile management flow"),
        ("05_refresh_flow.py", "Token refresh flow"),
        ("99_logout_flow.py", "Logout flow"),
    ]
    
    for filename, description in templates:
        console.print(f"  {filename}: {description}")


def get_traffic_test_commands():
    """Return the traffic-test command group for CLI registration."""
    return traffic_test_group


if __name__ == "__main__":
    traffic_test_group()