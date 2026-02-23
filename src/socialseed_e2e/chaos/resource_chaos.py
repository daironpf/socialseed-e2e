"""Resource exhaustion tools for Chaos Engineering."""

import logging

logger = logging.getLogger(__name__)

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class ResourceChaos:
    """Simulates resource pressure (CPU, memory) on services."""

    def __init__(self):
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
            except Exception:
                self.client = None
        else:
            self.client = None

    def limit_memory(self, container_name: str, limit: str):
        """Limit memory for a container (e.g., '128m', '1g')."""
        if not self.client:
            raise RuntimeError("Docker is not available to limit memory")

        container = self.client.containers.get(container_name)
        container.update(mem_limit=limit, memswap_limit=limit)
        logger.info(f"Chaos: Limited memory of {container_name} to {limit}")

    def limit_cpu(self, container_name: str, quota_percent: int):
        """Limit CPU usage for a container.

        Args:
            quota_percent: Percentage of a single CPU core (e.g., 50 for 0.5 core).
        """
        if not self.client:
            raise RuntimeError("Docker is not available to limit CPU")

        # 100000 is the default period
        quota = quota_percent * 1000
        container = self.client.containers.get(container_name)
        container.update(cpu_quota=quota, cpu_period=100000)
        logger.info(f"Chaos: Limited CPU of {container_name} to {quota_percent}%")

    def reset_limits(self, container_name: str):
        """Reset all resource limits for a container."""
        if not self.client:
            raise RuntimeError("Docker is not available to reset limits")

        container = self.client.containers.get(container_name)
        # Setting to -1 or 0 usually resets in Docker API
        container.update(mem_limit=0, cpu_quota=-1)
        logger.info(f"Chaos: Reset limits for {container_name}")
