"""Docker Compose manager for service orchestration.

This module provides the DockerComposeManager class for managing
Docker Compose services, including startup, shutdown, health checks,
and service orchestration.
"""

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from socialseed_e2e.docker.parser import (
    ComposeConfig,
    DockerComposeError,
    DockerComposeParser,
    HealthCheckError,
    ServiceNotFoundError,
    ServiceStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class DockerComposeOptions:
    """Options for Docker Compose operations."""

    file: Union[str, Path] = "docker-compose.yml"
    project_name: Optional[str] = None
    env_file: Optional[Union[str, Path]] = None
    build: bool = False
    detach: bool = True
    remove_orphans: bool = True
    force_recreate: bool = False
    timeout: int = 30


class DockerComposeManager:
    """Manager for Docker Compose operations."""

    def __init__(
        self,
        compose_file: Union[str, Path] = "docker-compose.yml",
        options: Optional[DockerComposeOptions] = None,
    ):
        self.compose_file = Path(compose_file)
        self.options = options or DockerComposeOptions(file=compose_file)
        self.parser = DockerComposeParser()
        self._config: Optional[ComposeConfig] = None
        self._started_services: List[str] = []

    def _get_config(self) -> ComposeConfig:
        if self._config is None:
            self._config = self.parser.parse(self.compose_file)
        return self._config

    def _run_command(
        self,
        command: List[str],
        capture_output: bool = True,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        base_cmd = ["docker-compose", "-f", str(self.compose_file)]

        if self.options.project_name:
            base_cmd.extend(["-p", self.options.project_name])

        if self.options.env_file:
            base_cmd.extend(["--env-file", str(self.options.env_file)])

        full_cmd = base_cmd + command
        logger.debug(f"Running command: {' '.join(full_cmd)}")

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=capture_output,
                text=True,
                check=check,
            )
            return result
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else e.stdout
            raise DockerComposeError(f"Command failed: {error_msg}") from e
        except FileNotFoundError:
            raise DockerComposeError(
                "docker-compose not found. Is Docker Compose installed?"
            )

    def up(
        self,
        services: Optional[List[str]] = None,
        build: bool = False,
        detach: bool = True,
    ) -> None:
        cmd = ["up"]

        if detach:
            cmd.append("-d")

        if build or self.options.build:
            cmd.append("--build")

        if self.options.force_recreate:
            cmd.append("--force-recreate")

        if self.options.remove_orphans:
            cmd.append("--remove-orphans")

        if services:
            cmd.extend(services)
            self._started_services = services
        else:
            self._started_services = list(self._get_config().services.keys())

        logger.info(f"Starting services: {self._started_services}")
        self._run_command(cmd)
        logger.info("Services started successfully")

    def down(self, volumes: bool = False, remove_orphans: bool = True) -> None:
        cmd = ["down"]

        if volumes:
            cmd.append("-v")

        if remove_orphans:
            cmd.append("--remove-orphans")

        cmd.extend(["-t", str(self.options.timeout)])

        logger.info("Stopping services")
        self._run_command(cmd)
        self._started_services = []
        logger.info("Services stopped successfully")

    def ps(self) -> List[ServiceStatus]:
        cmd = ["ps", "--format", "json"]

        try:
            result = self._run_command(cmd)
            containers = json.loads(result.stdout) if result.stdout else []
        except (json.JSONDecodeError, DockerComposeError):
            return self._ps_fallback()

        services = []
        for container in containers:
            services.append(
                ServiceStatus(
                    name=container.get("Service", ""),
                    state=container.get("State", ""),
                    health=container.get("Health", ""),
                    ports=self._parse_ports(container.get("Publishers", [])),
                    uptime=container.get("Status", ""),
                )
            )

        return services

    def _ps_fallback(self) -> List[ServiceStatus]:
        cmd = ["ps"]
        result = self._run_command(cmd, check=False)

        services = []
        lines = result.stdout.strip().split("\n") if result.stdout else []

        for line in lines[2:]:
            parts = line.split()
            if len(parts) >= 4:
                services.append(
                    ServiceStatus(
                        name=parts[0],
                        state=parts[3] if len(parts) > 3 else "unknown",
                    )
                )

        return services

    def _parse_ports(self, publishers: List[Dict]) -> Dict[str, str]:
        ports = {}
        for pub in publishers:
            target = pub.get("TargetPort", "")
            published = pub.get("PublishedPort", "")
            if target and published:
                ports[str(target)] = str(published)
        return ports

    def is_running(self, service_name: str) -> bool:
        try:
            status = self.get_service_status(service_name)
            return status.state.lower() == "running"
        except ServiceNotFoundError:
            return False

    def is_healthy(self, service_name: str) -> bool:
        try:
            status = self.get_service_status(service_name)
            return status.health and status.health.lower() == "healthy"
        except ServiceNotFoundError:
            return False

    def get_service_status(self, service_name: str) -> ServiceStatus:
        all_status = self.ps()

        for status in all_status:
            if status.name == service_name:
                return status

        raise ServiceNotFoundError(f"Service '{service_name}' not found")

    def wait_for_healthy(
        self,
        services: Optional[List[str]] = None,
        timeout: int = 60,
        interval: int = 2,
    ) -> bool:
        if services is None:
            config = self._get_config()
            services = [
                name for name, svc in config.services.items() if svc.health_check
            ]

        if not services:
            logger.info("No services with health checks")
            return True

        logger.info(f"Waiting for services to be healthy: {services}")

        start_time = time.time()
        healthy_services = set()

        while time.time() - start_time < timeout:
            for service in services:
                if service in healthy_services:
                    continue

                if self.is_healthy(service):
                    logger.info(f"Service '{service}' is healthy")
                    healthy_services.add(service)
                elif not self.is_running(service):
                    raise HealthCheckError(f"Service '{service}' is not running")

            if len(healthy_services) == len(services):
                logger.info("All services are healthy")
                return True

            time.sleep(interval)

        unhealthy = set(services) - healthy_services
        raise HealthCheckError(
            f"Services did not become healthy in {timeout}s: {unhealthy}"
        )

    def logs(
        self,
        services: Optional[List[str]] = None,
        tail: Optional[int] = None,
        follow: bool = False,
    ) -> str:
        cmd = ["logs"]

        if tail:
            cmd.extend(["--tail", str(tail)])

        if follow:
            cmd.append("-f")

        if services:
            cmd.extend(services)

        result = self._run_command(cmd, check=False)
        return result.stdout

    def build(
        self,
        services: Optional[List[str]] = None,
        no_cache: bool = False,
    ) -> None:
        cmd = ["build"]

        if no_cache:
            cmd.append("--no-cache")

        if services:
            cmd.extend(services)

        logger.info(f"Building services: {services or 'all'}")
        self._run_command(cmd)
        logger.info("Build completed")

    def list_services(self) -> List[str]:
        return list(self._get_config().services.keys())
