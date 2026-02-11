# Docker Compose Integration

This guide explains how to use the Docker Compose integration in socialseed-e2e for managing test environments.

## Overview

The Docker Compose integration provides:

- **Docker Compose Parser**: Parse and validate docker-compose.yml files
- **Service Orchestration**: Start, stop, and manage Docker Compose services
- **Health Check Integration**: Wait for services to be healthy before running tests
- **Automatic Startup/Shutdown**: Lifecycle management for test environments
- **Configuration Options**: Flexible options for different use cases

## Quick Start

### Basic Usage

```python
from socialseed_e2e.docker import DockerComposeManager

# Initialize manager
manager = DockerComposeManager("docker-compose.yml")

# Start all services
manager.up()

# Wait for services to be healthy
manager.wait_for_healthy()

# Run your tests
# ...

# Stop services
manager.down()
```

## DockerComposeManager

The `DockerComposeManager` is the main class for managing Docker Compose services.

### Initialization

```python
from socialseed_e2e.docker import DockerComposeManager, DockerComposeOptions

# Basic initialization
manager = DockerComposeManager("docker-compose.yml")

# With custom options
options = DockerComposeOptions(
    project_name="my-project",
    build=True,
    timeout=60,
)
manager = DockerComposeManager("docker-compose.yml", options)
```

### Starting Services

```python
# Start all services
manager.up()

# Start specific services
manager.up(services=["api", "database"])

# Start with build
manager.up(build=True)

# Start in foreground (not detached)
manager.up(detach=False)
```

### Stopping Services

```python
# Stop all services
manager.down()

# Stop and remove volumes
manager.down(volumes=True)

# Stop without removing orphans
manager.down(remove_orphans=False)
```

### Health Checks

```python
# Wait for all services with health checks
manager.wait_for_healthy()

# Wait for specific services
manager.wait_for_healthy(
    services=["api", "database"],
    timeout=120,
    interval=5,
)
```

### Checking Service Status

```python
# Get status of all services
status_list = manager.ps()
for status in status_list:
    print(f"{status.name}: {status.state} ({status.health})")

# Check if a service is running
if manager.is_running("api"):
    print("API is running")

# Check if a service is healthy
if manager.is_healthy("database"):
    print("Database is healthy")

# Get specific service status
try:
    status = manager.get_service_status("api")
    print(f"Ports: {status.ports}")
except ServiceNotFoundError:
    print("Service not found")
```

### Logs

```python
# Get all logs
logs = manager.logs()
print(logs)

# Get last 100 lines
logs = manager.logs(tail=100)

# Get logs for specific services
logs = manager.logs(services=["api", "database"])
```

### Building Services

```python
# Build all services
manager.build()

# Build specific services
manager.build(services=["api"])

# Build without cache
manager.build(no_cache=True)
```

## DockerComposeParser

Use the parser to inspect docker-compose.yml files without running Docker commands.

### Parsing Compose Files

```python
from socialseed_e2e.docker import DockerComposeParser

parser = DockerComposeParser()
config = parser.parse("docker-compose.yml")

# Get compose version
print(f"Version: {config.version}")

# List services
print(f"Services: {list(config.services.keys())}")

# Inspect a service
api = config.services["api"]
print(f"Image: {api.image}")
print(f"Ports: {api.ports}")
print(f"Environment: {api.environment}")
print(f"Health Check: {api.health_check}")
```

### Validating Compose Files

```python
parser = DockerComposeParser()
errors = parser.validate("docker-compose.yml")

if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✓ File is valid")
```

### Getting Service Information

```python
# Get specific service
try:
    service = parser.get_service("docker-compose.yml", "api")
    print(f"Service: {service.name}")
except ServiceNotFoundError:
    print("Service not found")

# List all services
services = parser.list_services("docker-compose.yml")
print(f"Services: {services}")
```

## Configuration Options

### DockerComposeOptions

```python
from socialseed_e2e.docker import DockerComposeOptions

options = DockerComposeOptions(
    # Compose file path
    file="docker-compose.yml",
    
    # Project name (prefix for containers)
    project_name="my-project",
    
    # Environment file
    env_file=".env",
    
    # Build images before starting
    build=True,
    
    # Run in detached mode
    detach=True,
    
    # Remove orphaned containers
    remove_orphans=True,
    
    # Force recreate containers
    force_recreate=False,
    
    # Shutdown timeout (seconds)
    timeout=30,
)
```

## Integration with Tests

### Using with pytest

```python
import pytest
from socialseed_e2e.docker import DockerComposeManager

@pytest.fixture(scope="session")
def docker_services():
    """Start Docker Compose services for tests."""
    manager = DockerComposeManager("docker-compose.yml")
    
    # Start services
    manager.up()
    
    # Wait for healthy
    manager.wait_for_healthy()
    
    yield manager
    
    # Cleanup after tests
    manager.down()

def test_api(docker_services):
    # Services are running and healthy
    assert docker_services.is_running("api")
    assert docker_services.is_healthy("api")
    
    # Run your test
    # ...
```

### Context Manager Pattern

```python
from contextlib import contextmanager
from socialseed_e2e.docker import DockerComposeManager

@contextmanager
def docker_environment(compose_file="docker-compose.yml"):
    """Context manager for Docker Compose environment."""
    manager = DockerComposeManager(compose_file)
    
    try:
        print("Starting services...")
        manager.up()
        manager.wait_for_healthy()
        yield manager
    finally:
        print("Stopping services...")
        manager.down()

# Usage
with docker_environment() as manager:
    # Run tests with services running
    assert manager.is_healthy("api")
    # ...
```

## Error Handling

The Docker integration provides specific exceptions:

```python
from socialseed_e2e.docker import (
    DockerComposeError,
    ServiceNotFoundError,
    HealthCheckError,
)

try:
    manager.up()
    manager.wait_for_healthy(timeout=60)
except DockerComposeError as e:
    print(f"Docker Compose error: {e}")
except ServiceNotFoundError as e:
    print(f"Service not found: {e}")
except HealthCheckError as e:
    print(f"Health check failed: {e}")
```

## Advanced Usage

### Custom Health Checks

```python
import time

def wait_for_service_ready(manager, service, max_attempts=10):
    """Custom wait logic for service readiness."""
    for i in range(max_attempts):
        if manager.is_healthy(service):
            return True
        
        # Check if service is running but not healthy yet
        if manager.is_running(service):
            print(f"Waiting for {service}... ({i+1}/{max_attempts})")
            time.sleep(2)
        else:
            raise Exception(f"Service {service} is not running")
    
    raise HealthCheckError(f"Service {service} did not become healthy")
```

### Working with Multiple Compose Files

```python
# Test with different environments
dev_manager = DockerComposeManager("docker-compose.yml")
test_manager = DockerComposeManager("docker-compose.test.yml")

# Start test environment
test_manager.up()
test_manager.wait_for_healthy()

# Run tests
# ...

# Cleanup
test_manager.down()
```

### Inspecting Service Configuration

```python
from socialseed_e2e.docker import DockerComposeParser

parser = DockerComposeParser()
config = parser.parse("docker-compose.yml")

# Check service dependencies
for name, service in config.services.items():
    print(f"\nService: {name}")
    print(f"  Depends on: {service.depends_on}")
    print(f"  Ports: {service.ports}")
    print(f"  Has health check: {service.health_check is not None}")
```

## Best Practices

1. **Always wait for health checks**: Use `wait_for_healthy()` before running tests
2. **Clean up resources**: Call `down()` in cleanup/finally blocks
3. **Use project names**: Isolate different test runs with project names
4. **Validate compose files**: Use `parser.validate()` to catch errors early
5. **Handle timeouts**: Set appropriate timeouts based on your services
6. **Check service status**: Verify services are running before using them

## Troubleshooting

### Docker Compose Not Found

```
DockerComposeError: docker-compose not found. Is Docker Compose installed?
```

**Solution**: Install Docker Compose:
```bash
# On macOS/Windows (Docker Desktop)
# Docker Compose is included

# On Linux
pip install docker-compose
# or
apt-get install docker-compose-plugin
```

### Services Not Becoming Healthy

```python
# Increase timeout
manager.wait_for_healthy(timeout=120)

# Check logs
print(manager.logs())

# Check specific service logs
print(manager.logs(services=["api"]))
```

### Port Conflicts

```python
# Use different ports in your compose file
# or specify environment-specific compose files
manager = DockerComposeManager("docker-compose.test.yml")
```

## API Reference

### DockerComposeManager

| Method | Description |
|--------|-------------|
| `up(services, build, detach)` | Start services |
| `down(volumes, remove_orphans)` | Stop and remove services |
| `ps()` | Get service status |
| `wait_for_healthy(services, timeout, interval)` | Wait for health checks |
| `is_running(service)` | Check if service is running |
| `is_healthy(service)` | Check if service is healthy |
| `logs(services, tail, follow)` | Get service logs |
| `build(services, no_cache)` | Build services |
| `list_services()` | List all services |

### DockerComposeParser

| Method | Description |
|--------|-------------|
| `parse(file)` | Parse compose file |
| `validate(file)` | Validate compose file |
| `get_service(file, name)` | Get service config |
| `list_services(file)` | List all services |

## Examples

See the `examples/docker/` directory for complete examples:

- `docker_compose_example.py` - Complete usage examples

## Further Reading

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Health Checks in Docker](https://docs.docker.com/engine/reference/builder/#healthcheck)
