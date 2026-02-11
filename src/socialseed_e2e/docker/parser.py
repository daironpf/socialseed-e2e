"""Docker Compose integration for socialseed-e2e.

This module provides integration with Docker Compose for managing
test environments, including service orchestration, health checks,
and automatic startup/shutdown.

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
    >>> manager.wait_for_healthy(timeout=60)
    >>>
    >>> # Run your tests
    >>> # ...
    >>>
    >>> # Shutdown services
    >>> manager.down()
"""

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class DockerComposeError(Exception):
    """Exception raised for Docker Compose errors."""

    pass


class ServiceNotFoundError(DockerComposeError):
    """Exception raised when a service is not found."""

    pass


class HealthCheckError(DockerComposeError):
    """Exception raised when health checks fail."""

    pass


@dataclass
class ServiceConfig:
    """Configuration for a Docker Compose service.

    Attributes:
        name: Service name
        image: Docker image
        ports: Exposed ports
        environment: Environment variables
        depends_on: Services this service depends on
        health_check: Health check configuration
        volumes: Volume mounts
        networks: Networks to join
    """

    name: str
    image: Optional[str] = None
    ports: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    health_check: Optional[Dict[str, Any]] = None
    volumes: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    build: Optional[Union[str, Dict[str, Any]]] = None
    command: Optional[Union[str, List[str]]] = None


@dataclass
class ComposeConfig:
    """Parsed Docker Compose configuration.

    Attributes:
        version: Compose file version
        services: Dictionary of service configurations
        networks: Network definitions
        volumes: Volume definitions
        file_path: Path to the compose file
    """

    version: str
    services: Dict[str, ServiceConfig]
    networks: Dict[str, Any] = field(default_factory=dict)
    volumes: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[Path] = None


@dataclass
class ServiceStatus:
    """Status of a Docker Compose service.

    Attributes:
        name: Service name
        state: Current state (running, exited, etc.)
        health: Health status (healthy, unhealthy, starting)
        ports: Mapped ports
        uptime: Container uptime
    """

    name: str
    state: str
    health: Optional[str] = None
    ports: Dict[str, str] = field(default_factory=dict)
    uptime: Optional[str] = None


class DockerComposeParser:
    """Parser for Docker Compose files.

    Parses docker-compose.yml files and extracts service configurations.

    Example:
        >>> parser = DockerComposeParser()
        >>> config = parser.parse("docker-compose.yml")
        >>> print(f"Services: {list(config.services.keys())}")
    """

    def parse(self, compose_file: Union[str, Path]) -> ComposeConfig:
        """Parse a Docker Compose file.

        Args:
            compose_file: Path to docker-compose.yml

        Returns:
            Parsed ComposeConfig

        Raises:
            DockerComposeError: If file cannot be parsed
        """
        file_path = Path(compose_file)

        if not file_path.exists():
            raise DockerComposeError(f"Compose file not found: {file_path}")

        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise DockerComposeError(f"Failed to parse YAML: {e}") from e

        if not data:
            raise DockerComposeError("Compose file is empty")

        # Extract version
        version = data.get("version", "3")

        # Parse services
        services = {}
        services_data = data.get("services", {})

        for name, service_data in services_data.items():
            services[name] = self._parse_service(name, service_data)

        # Parse networks and volumes
        networks = data.get("networks", {})
        volumes = data.get("volumes", {})

        return ComposeConfig(
            version=version,
            services=services,
            networks=networks,
            volumes=volumes,
            file_path=file_path,
        )

    def _parse_service(self, name: str, data: Dict[str, Any]) -> ServiceConfig:
        """Parse a single service definition.

        Args:
            name: Service name
            data: Service configuration dict

        Returns:
            ServiceConfig
        """
        return ServiceConfig(
            name=name,
            image=data.get("image"),
            ports=data.get("ports", []),
            environment=self._parse_environment(data.get("environment", {})),
            depends_on=data.get("depends_on", []),
            health_check=data.get("healthcheck"),
            volumes=data.get("volumes", []),
            networks=data.get("networks", []),
            build=data.get("build"),
            command=data.get("command"),
        )

    def _parse_environment(
        self, env_data: Union[Dict[str, str], List[str]]
    ) -> Dict[str, str]:
        """Parse environment variables.

        Args:
            env_data: Environment variables (dict or list format)

        Returns:
            Dictionary of environment variables
        """
        if isinstance(env_data, dict):
            return env_data

        # Parse list format ["KEY=value", "KEY2=value2"]
        result = {}
        for item in env_data:
            if "=" in item:
                key, value = item.split("=", 1)
                result[key] = value
            else:
                result[item] = ""
        return result

    def get_service(
        self, compose_file: Union[str, Path], service_name: str
    ) -> ServiceConfig:
        """Get configuration for a specific service.

        Args:
            compose_file: Path to docker-compose.yml
            service_name: Name of the service

        Returns:
            ServiceConfig

        Raises:
            ServiceNotFoundError: If service not found
        """
        config = self.parse(compose_file)

        if service_name not in config.services:
            raise ServiceNotFoundError(
                f"Service '{service_name}' not found in compose file"
            )

        return config.services[service_name]

    def list_services(self, compose_file: Union[str, Path]) -> List[str]:
        """List all services in a compose file.

        Args:
            compose_file: Path to docker-compose.yml

        Returns:
            List of service names
        """
        config = self.parse(compose_file)
        return list(config.services.keys())

    def validate(self, compose_file: Union[str, Path]) -> List[str]:
        """Validate a Docker Compose file.

        Args:
            compose_file: Path to docker-compose.yml

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        file_path = Path(compose_file)

        if not file_path.exists():
            return [f"File not found: {file_path}"]

        try:
            config = self.parse(compose_file)

            # Validate services
            if not config.services:
                errors.append("No services defined")

            for name, service in config.services.items():
                if not service.image and not service.build:
                    errors.append(f"Service '{name}' has no image or build context")

        except Exception as e:
            errors.append(str(e))

        return errors


__all__ = [
    "DockerComposeParser",
    "ComposeConfig",
    "ServiceConfig",
    "ServiceStatus",
    "DockerComposeError",
    "ServiceNotFoundError",
    "HealthCheckError",
]
