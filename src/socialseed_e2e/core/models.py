from typing import Any, Dict, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ServiceConfig(BaseModel):
    """Configuration for a specific service."""

    name: str
    base_url: str
    default_headers: Dict[str, str] = Field(default_factory=dict)
    timeout: int = 30000
    extra: Dict[str, Any] = Field(default_factory=dict)


class TestContext(BaseModel):
    """Generic context for test execution."""

    env: str = "dev"
    services: Dict[str, ServiceConfig] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_service(self, name: str) -> Optional[ServiceConfig]:
        return self.services.get(name)
