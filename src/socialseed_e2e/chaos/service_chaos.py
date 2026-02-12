"""Service failure simulation for Chaos Engineering."""

from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class ServiceChaos:
    """Simulates service-level failures, primarily using Docker."""

    def __init__(self):
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
            except Exception:
                self.client = None
                logger.warning("Docker client could not be initialized")
        else:
            self.client = None

    def stop_service(self, container_name: str):
        """Stop a specific container/service."""
        if not self.client:
            raise RuntimeError("Docker is not available to stop services")
        
        container = self.client.containers.get(container_name)
        container.stop()
        logger.info(f"Chaos: Stopped service {container_name}")

    def start_service(self, container_name: str):
        """Start a specific container/service."""
        if not self.client:
            raise RuntimeError("Docker is not available to start services")
        
        container = self.client.containers.get(container_name)
        container.start()
        logger.info(f"Chaos: Started service {container_name}")

    def restart_service(self, container_name: str):
        """Restart a specific container/service."""
        if not self.client:
            raise RuntimeError("Docker is not available to restart services")
        
        container = self.client.containers.get(container_name)
        container.restart()
        logger.info(f"Chaos: Restarted service {container_name}")

    def kill_service(self, container_name: str, signal: str = "SIGKILL"):
        """Kill a service immediately."""
        if not self.client:
            raise RuntimeError("Docker is not available to kill services")
        
        container = self.client.containers.get(container_name)
        container.kill(signal=signal)
        logger.info(f"Chaos: Killed service {container_name} with {signal}")
