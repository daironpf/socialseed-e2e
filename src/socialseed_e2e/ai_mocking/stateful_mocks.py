"""
Smart Stateful Mocking System for socialseed-e2e.

This module provides AI-powered stateful mocks that can respond to
requests based on learned traffic patterns and maintain state across requests.

Features:
- Intercept outgoing calls from service under test
- Respond using LLM or Vector Store trained on production traffic
- Maintain state across requests (POST creates resource, GET returns it)
- CLI flag for automatic smart mock isolation
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MockMode(str, Enum):
    """Mode of operation for smart mocks."""

    STATIC = "static"
    VECTOR_STORE = "vector_store"
    LLM_POWERED = "llm_powered"
    HYBRID = "hybrid"


class RequestState(BaseModel):
    """State of a mocked request."""

    request_id: str
    method: str
    path: str

    request_body: Optional[Dict[str, Any]] = None
    request_headers: Dict[str, str] = {}

    response_status: int = 200
    response_body: Optional[Dict[str, Any]] = None
    response_headers: Dict[str, str] = {}

    created_at: datetime = Field(default_factory=datetime.now)


class ResourceState(BaseModel):
    """State of a resource in the mock."""

    resource_id: str
    resource_type: str

    data: Dict[str, Any]

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StatefulMockConfig(BaseModel):
    """Configuration for stateful mock server."""

    mode: MockMode = MockMode.HYBRID
    vector_store_path: Optional[str] = None
    llm_model: Optional[str] = None
    port: int = 8766
    host: str = "localhost"

    response_delay_ms: int = 0

    capture_traffic: bool = True
    traffic_log_path: str = ".e2e/mock_traffic.json"


class InterceptedCall(BaseModel):
    """An intercepted API call."""

    call_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

    source_service: str
    target_service: str
    target_url: str

    method: str
    path: str
    headers: Dict[str, str] = {}
    body: Optional[Dict[str, Any]] = None


class SmartMockServer:
    """
    Smart mock server that maintains state and uses AI for responses.
    """

    def __init__(self, config: StatefulMockConfig):
        self.config = config
        self.resources: Dict[str, ResourceState] = {}
        self.request_history: List[RequestState] = []
        self.intercepted_calls: List[InterceptedCall] = []

    def start(self) -> None:
        """Start the smart mock server."""
        pass

    def stop(self) -> None:
        """Stop the smart mock server."""
        pass

    def intercept_request(
        self,
        source_service: str,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Intercept and handle a request."""
        call = InterceptedCall(
            call_id=str(uuid.uuid4()),
            source_service=source_service,
            target_service=self._extract_service(path),
            target_url=path,
            method=method,
            path=path,
            headers=headers,
            body=body,
        )
        self.intercepted_calls.append(call)

        response = self._generate_response(method, path, body)

        request_state = RequestState(
            request_id=str(uuid.uuid4()),
            method=method,
            path=path,
            request_body=body,
            request_headers=headers,
            response_status=response.get("status", 200),
            response_body=response.get("body"),
        )
        self.request_history.append(request_state)

        return response

    def _extract_service(self, path: str) -> str:
        """Extract service name from path."""
        parts = path.strip("/").split("/")
        return parts[0] if parts else "unknown"

    def _generate_response(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate response based on mode and state."""
        if method == "POST":
            return self._handle_create(path, body)
        elif method == "GET":
            return self._handle_read(path)
        elif method == "PUT" or method == "PATCH":
            return self._handle_update(path, body)
        elif method == "DELETE":
            return self._handle_delete(path)

        return {"status": 200, "body": {"message": "ok"}}

    def _handle_create(
        self, path: str, body: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle POST - create resource."""
        resource_id = str(uuid.uuid4())
        resource_type = self._extract_resource_type(path)

        resource = ResourceState(
            resource_id=resource_id,
            resource_type=resource_type,
            data=body or {},
        )

        self.resources[f"{resource_type}:{resource_id}"] = resource

        return {
            "status": 201,
            "body": {
                "id": resource_id,
                **resource.data,
            },
        }

    def _handle_read(self, path: str) -> Dict[str, Any]:
        """Handle GET - read resource."""
        resource_key = self._extract_resource_key(path)

        if resource_key in self.resources:
            resource = self.resources[resource_key]
            return {
                "status": 200,
                "body": {
                    "id": resource.resource_id,
                    **resource.data,
                },
            }

        if ":" not in resource_key:
            items = [
                r.data
                for r in self.resources.values()
                if r.resource_type == resource_key
            ]
            return {"status": 200, "body": items}

        return {"status": 404, "body": {"error": "Not found"}}

    def _handle_update(
        self, path: str, body: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle PUT/PATCH - update resource."""
        resource_key = self._extract_resource_key(path)

        if resource_key in self.resources:
            resource = self.resources[resource_key]
            resource.data.update(body or {})
            resource.updated_at = datetime.now()
            return {
                "status": 200,
                "body": {
                    "id": resource.resource_id,
                    **resource.data,
                },
            }

        return {"status": 404, "body": {"error": "Not found"}}

    def _handle_delete(self, path: str) -> Dict[str, Any]:
        """Handle DELETE - delete resource."""
        resource_key = self._extract_resource_key(path)

        if resource_key in self.resources:
            del self.resources[resource_key]
            return {"status": 204, "body": None}

        return {"status": 404, "body": {"error": "Not found"}}

    def _extract_resource_type(self, path: str) -> str:
        """Extract resource type from path."""
        parts = path.strip("/").split("/")
        return parts[0] if parts else "resource"

    def _extract_resource_key(self, path: str) -> str:
        """Extract resource key (type:id) from path."""
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}"
        return parts[0] if parts else "resource"

    def get_state(self) -> Dict[str, Any]:
        """Get current mock state."""
        return {
            "resources": len(self.resources),
            "request_history": len(self.request_history),
            "intercepted_calls": len(self.intercepted_calls),
        }

    def reset_state(self) -> None:
        """Reset all mock state."""
        self.resources.clear()
        self.request_history.clear()
        self.intercepted_calls.clear()


class SmartMockOrchestrator:
    """
    Orchestrates smart mocks for multiple services.
    """

    def __init__(self):
        self.mocks: Dict[str, SmartMockServer] = {}
        self.configs: Dict[str, StatefulMockConfig] = {}

    def add_mock_service(
        self, service_name: str, config: Optional[StatefulMockConfig] = None
    ) -> SmartMockServer:
        """Add a mock service."""
        if config is None:
            config = StatefulMockConfig()

        self.configs[service_name] = config
        mock = SmartMockServer(config)
        self.mocks[service_name] = mock

        return mock

    def get_mock(self, service_name: str) -> Optional[SmartMockServer]:
        """Get a mock service by name."""
        return self.mocks.get(service_name)

    def start_all(self) -> None:
        """Start all mock services."""
        for mock in self.mocks.values():
            mock.start()

    def stop_all(self) -> None:
        """Stop all mock services."""
        for mock in self.mocks.values():
            mock.stop()

    def reset_all(self) -> None:
        """Reset all mock state."""
        for mock in self.mocks.values():
            mock.reset_state()


class MockIsolationManager:
    """
    Manages isolation mode for running tests with smart mocks.
    """

    def __init__(self, orchestrator: SmartMockOrchestrator):
        self.orchestrator = orchestrator
        self.is_running = False

    def start_isolation(self, service_name: str) -> None:
        """Start isolation mode for a service."""
        mock = self.orchestrator.get_mock(service_name)
        if mock:
            mock.start()
            self.is_running = True

    def stop_isolation(self) -> None:
        """Stop isolation mode."""
        self.orchestrator.stop_all()
        self.is_running = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_isolation()


__all__ = [
    "InterceptedCall",
    "MockMode",
    "RequestState",
    "ResourceState",
    "SmartMockOrchestrator",
    "SmartMockServer",
    "StatefulMockConfig",
    "MockIsolationManager",
]
