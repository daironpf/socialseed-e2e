"""Cloud platform integrations for socialseed-e2e.

This module provides native support for testing applications deployed on
major cloud platforms like AWS, GCP, and Azure.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CloudProvider(ABC):
    """Base class for cloud provider integrations."""

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the cloud provider integration is working."""
        pass


class CloudFunction(ABC):
    """Interface for Cloud Functions (Lambda, Cloud Functions, Azure Functions)."""

    @abstractmethod
    def invoke(self, payload: Dict[str, Any]) -> Any:
        """Invoke a cloud function."""
        pass

    @abstractmethod
    def get_logs(self, limit: int = 10) -> List[str]:
        """Get the latest logs for the function."""
        pass


class CloudService(ABC):
    """Interface for Containerized Services (ECS, Cloud Run, Container Instances)."""

    @abstractmethod
    def get_status(self) -> str:
        """Get the current status of the service."""
        pass

    @abstractmethod
    def restart(self) -> bool:
        """Restart the service."""
        pass


class CloudDatabase(ABC):
    """Interface for Managed Databases (RDS, Cloud SQL, Azure SQL)."""

    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query against the database."""
        pass
