"""Docker integration for socialseed-e2e.

This module provides Docker and Docker Compose integration for managing
test environments.

Example:
    >>> from socialseed_e2e.docker import DockerComposeManager
    >>>
    >>> # Initialize with docker-compose.yml
    >>> manager = DockerComposeManager("docker-compose.yml")
    >>>
    >>> # Start all services
    >>> manager.up()
    >>>
    >>> # Wait for services to be healthy
    >>> manager.wait_for_healthy()
    >>>
    >>> # Run your tests
    >>> # ...
    >>>
    >>> # Shutdown services
    >>> manager.down()
"""

from socialseed_e2e.docker.manager import DockerComposeManager, DockerComposeOptions
from socialseed_e2e.docker.parser import (
    ComposeConfig,
    DockerComposeError,
    DockerComposeParser,
    HealthCheckError,
    ServiceConfig,
    ServiceNotFoundError,
    ServiceStatus,
)

__all__ = [
    "DockerComposeManager",
    "DockerComposeOptions",
    "DockerComposeParser",
    "ComposeConfig",
    "ServiceConfig",
    "ServiceStatus",
    "DockerComposeError",
    "ServiceNotFoundError",
    "HealthCheckError",
]
