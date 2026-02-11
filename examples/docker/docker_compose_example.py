"""Example: Docker Compose Integration.

This example demonstrates how to use the Docker Compose integration
to manage test environments.

Prerequisites:
    - Docker and Docker Compose installed
    - A docker-compose.yml file

Usage:
    python docker_compose_example.py
"""

import tempfile
from pathlib import Path


def create_sample_compose_file():
    """Create a sample docker-compose.yml for testing."""
    content = """
version: '3.8'

services:
  api:
    image: nginx:alpine
    ports:
      - "8080:80"
    environment:
      - NGINX_HOST=localhost
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/"]
      interval: 5s
      timeout: 3s
      retries: 3
      start_period: 5s

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(content)
        return Path(f.name)


def example_parse_compose():
    """Example: Parse a docker-compose.yml file."""
    print("\n" + "=" * 60)
    print("Example 1: Parse docker-compose.yml")
    print("=" * 60)

    from socialseed_e2e.docker import DockerComposeParser

    compose_file = create_sample_compose_file()
    parser = DockerComposeParser()

    # Parse the compose file
    config = parser.parse(compose_file)

    print(f"\nCompose version: {config.version}")
    print(f"Services found: {list(config.services.keys())}")

    # Inspect a specific service
    api_service = config.services["api"]
    print(f"\nAPI Service:")
    print(f"  Image: {api_service.image}")
    print(f"  Ports: {api_service.ports}")
    print(f"  Environment: {api_service.environment}")
    print(f"  Has health check: {api_service.health_check is not None}")

    # Clean up
    compose_file.unlink()
    print("\n✓ Parsing completed")


def example_validate_compose():
    """Example: Validate a docker-compose.yml file."""
    print("\n" + "=" * 60)
    print("Example 2: Validate docker-compose.yml")
    print("=" * 60)

    from socialseed_e2e.docker import DockerComposeParser

    # Create a valid compose file
    valid_compose = create_sample_compose_file()
    parser = DockerComposeParser()

    errors = parser.validate(valid_compose)
    print(f"\nValidation errors in valid file: {len(errors)}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    else:
        print("  ✓ File is valid")

    # Create an invalid compose file (no image or build)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("""
version: '3'
services:
  bad_service:
    ports:
      - "80:80"
""")
        invalid_compose = Path(f.name)

    errors = parser.validate(invalid_compose)
    print(f"\nValidation errors in invalid file: {len(errors)}")
    for error in errors:
        print(f"  - {error}")

    # Clean up
    valid_compose.unlink()
    invalid_compose.unlink()
    print("\n✓ Validation completed")


def example_manager_workflow():
    """Example: Complete workflow with DockerComposeManager.

    Note: This example demonstrates the API usage but won't actually
    run Docker commands unless you have Docker installed and running.
    """
    print("\n" + "=" * 60)
    print("Example 3: Docker Compose Manager Workflow")
    print("=" * 60)

    from socialseed_e2e.docker import DockerComposeManager, DockerComposeOptions

    compose_file = create_sample_compose_file()

    # Initialize manager with options
    options = DockerComposeOptions(
        build=True,
        detach=True,
        timeout=30,
    )
    manager = DockerComposeManager(compose_file, options)

    print(f"\nManager initialized with compose file: {manager.compose_file}")
    print(f"Options:")
    print(f"  Build: {manager.options.build}")
    print(f"  Detach: {manager.options.detach}")
    print(f"  Timeout: {manager.options.timeout}s")

    # List services
    services = manager.list_services()
    print(f"\nServices in compose file: {services}")

    # Note: Actual Docker operations would be done here
    # manager.up()  # Start services
    # manager.wait_for_healthy()  # Wait for health checks
    # manager.ps()  # Check status
    # manager.down()  # Stop services

    print("\n✓ Manager workflow example completed")
    print("  (Note: Docker commands were not executed in this example)")

    # Clean up
    compose_file.unlink()


def example_configuration():
    """Example: Working with Docker Compose configuration."""
    print("\n" + "=" * 60)
    print("Example 4: Working with Configuration")
    print("=" * 60)

    from socialseed_e2e.docker import (
        DockerComposeParser,
        ServiceConfig,
        ComposeConfig,
    )

    compose_file = create_sample_compose_file()
    parser = DockerComposeParser()
    config = parser.parse(compose_file)

    print(f"\nCompose Configuration:")
    print(f"  Version: {config.version}")
    print(f"  Total services: {len(config.services)}")
    print(f"  Networks: {list(config.networks.keys())}")
    print(f"  Volumes: {list(config.volumes.keys())}")

    print(f"\nService Details:")
    for name, service in config.services.items():
        print(f"\n  {name}:")
        print(f"    Image: {service.image}")
        print(f"    Ports: {service.ports}")
        print(f"    Environment vars: {list(service.environment.keys())}")
        print(f"    Depends on: {service.depends_on}")
        print(f"    Volumes: {service.volumes}")

    # Clean up
    compose_file.unlink()
    print("\n✓ Configuration example completed")


def example_error_handling():
    """Example: Error handling."""
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)

    from socialseed_e2e.docker import (
        DockerComposeParser,
        DockerComposeError,
        ServiceNotFoundError,
    )

    parser = DockerComposeParser()

    # Try to parse non-existent file
    print("\nTrying to parse non-existent file...")
    try:
        parser.parse("/nonexistent/docker-compose.yml")
    except DockerComposeError as e:
        print(f"  ✓ Caught error: {e}")

    # Create a valid file and try to get non-existent service
    compose_file = create_sample_compose_file()
    print("\nTrying to get non-existent service...")
    try:
        parser.get_service(compose_file, "nonexistent")
    except ServiceNotFoundError as e:
        print(f"  ✓ Caught error: {e}")

    # Clean up
    compose_file.unlink()
    print("\n✓ Error handling example completed")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Docker Compose Integration Examples")
    print("=" * 60)
    print("\nThese examples demonstrate the Docker Compose integration.")
    print("Note: Examples 1, 2, 4, and 5 work without Docker installed.")
    print("Example 3 demonstrates the API but doesn't run Docker commands.")

    try:
        example_parse_compose()
        example_validate_compose()
        example_manager_workflow()
        example_configuration()
        example_error_handling()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback

        traceback.print_exc()
