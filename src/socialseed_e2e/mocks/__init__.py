"""Advanced API Simulation & Mocking Engine Module.

This module provides advanced API mocking capabilities:
- Dynamic mocking based on request content
- Scenario simulation (errors, latency, rate limiting)
- Contract-based mocking from OpenAPI specs
- Distributed mocking for microservices

Usage:
    from socialseed_e2e.mocks import (
        MockServer,
        DynamicMock,
        ScenarioSimulator,
    )
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse


class MockType(str, Enum):
    """Types of mocks."""

    DYNAMIC = "dynamic"
    STATIC = "static"
    SCENARIO = "scenario"
    CONTRACT = "contract"


class ResponseMode(str, Enum):
    """Response generation modes."""

    SEQUENTIAL = "sequential"
    RANDOM = "random"
    CONDITIONAL = "conditional"


@dataclass
class MockResponse:
    """Mock HTTP response."""

    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    delay_ms: float = 0.0
    scenario: Optional[str] = None


@dataclass
class MockRule:
    """Rule for matching requests."""

    path: Optional[str] = None
    method: Optional[str] = None
    query_params: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    body_contains: Optional[str] = None
    custom_match: Optional[Callable] = None


@dataclass
class DynamicMock:
    """Dynamic mock configuration."""

    rule: MockRule
    response: MockResponse
    response_mode: ResponseMode = ResponseMode.SEQUENTIAL
    responses: List[MockResponse] = field(default_factory=list)
    call_count: int = 0


class MockServer:
    """Advanced mock server for API testing.

    Example:
        server = MockServer(port=8080)

        # Add dynamic mock
        server.add_mock(
            path="/api/users",
            method="GET",
            response={"users": [{"id": "1", "name": "John"}]}
        )

        # Add conditional mock
        server.add_conditional_mock(
            path="/api/users/{id}",
            response={"id": "{{path.id}}", "name": "John"}
        )

        server.start()
    """

    def __init__(self, port: int = 8080, host: str = "localhost"):
        """Initialize mock server.

        Args:
            port: Server port
            host: Server host
        """
        self.port = port
        self.host = host
        self.mocks: Dict[str, DynamicMock] = {}
        self.scenarios: Dict[str, List[MockResponse]] = {}
        self.current_scenario: Optional[str] = None
        self.request_log: List[Dict[str, Any]] = []
        self._running = False

    def add_mock(
        self,
        path: str,
        method: str,
        response: Any,
        status_code: int = 200,
        delay_ms: float = 0.0,
    ) -> None:
        """Add a static mock.

        Args:
            path: URL path to match
            method: HTTP method
            response: Response body
            status_code: HTTP status code
            delay_ms: Response delay
        """
        rule = MockRule(path=path, method=method.upper())
        mock_response = MockResponse(
            status_code=status_code,
            body=response,
            delay_ms=delay_ms,
        )

        key = f"{method.upper()}:{path}"
        self.mocks[key] = DynamicMock(
            rule=rule,
            response=mock_response,
        )

    def add_conditional_mock(
        self,
        path: str,
        method: str,
        response_template: str,
        status_code: int = 200,
    ) -> None:
        """Add a conditional mock with template.

        Args:
            path: URL path with parameters
            method: HTTP method
            response_template: Response template with placeholders
            status_code: HTTP status code
        """
        rule = MockRule(path=path, method=method.upper())
        mock_response = MockResponse(
            status_code=status_code,
            body=response_template,
        )

        key = f"{method.upper()}:{path}"
        self.mocks[key] = DynamicMock(
            rule=rule,
            response=mock_response,
            response_mode=ResponseMode.CONDITIONAL,
        )

    def add_scenario(
        self,
        name: str,
        responses: List[Dict[str, Any]],
    ) -> None:
        """Add a scenario with multiple responses.

        Args:
            name: Scenario name
            responses: List of response definitions
        """
        mock_responses = []
        for resp in responses:
            mock_responses.append(
                MockResponse(
                    status_code=resp.get("status_code", 200),
                    body=resp.get("body"),
                    delay_ms=resp.get("delay_ms", 0.0),
                    scenario=name,
                )
            )

        self.scenarios[name] = mock_responses

    def set_scenario(self, name: str) -> None:
        """Set active scenario.

        Args:
            name: Scenario name
        """
        if name not in self.scenarios:
            raise ValueError(f"Scenario '{name}' not found")
        self.current_scenario = name

    def get_mock(self, method: str, path: str) -> Optional[MockResponse]:
        """Get mock response for request.

        Args:
            method: HTTP method
            path: Request path

        Returns:
            MockResponse or None
        """
        key = f"{method.upper()}:{path}"
        mock = self.mocks.get(key)

        if not mock:
            # Try pattern matching
            for _mock_key, mock_obj in self.mocks.items():
                if self._match_path(path, mock_obj.rule.path):
                    mock = mock_obj
                    break

        if not mock:
            return None

        # Apply response mode
        if mock.response_mode == ResponseMode.SEQUENTIAL:
            if mock.responses:
                mock.call_count += 1
                idx = mock.call_count % len(mock.responses)
                return mock.responses[idx]
        elif mock.response_mode == ResponseMode.RANDOM:
            import random

            if mock.responses:
                return random.choice(mock.responses)

        # Check scenario
        if self.current_scenario and self.current_scenario in self.scenarios:
            scenario_responses = self.scenarios[self.current_scenario]
            if scenario_responses:
                idx = mock.call_count % len(scenario_responses)
                mock.call_count += 1
                return scenario_responses[idx]

        mock.call_count += 1
        return mock.response

    def _match_path(self, path: str, pattern: Optional[str]) -> bool:
        """Match path against pattern."""
        if not pattern:
            return False

        # Simple pattern matching with {param}
        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")

        if len(pattern_parts) != len(path_parts):
            return False

        for pp, p in zip(pattern_parts, path_parts):
            if pp.startswith("{") and pp.endswith("}"):
                continue
            if pp != p:
                return False

        return True

    def log_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Any,
    ) -> None:
        """Log incoming request.

        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            body: Request body
        """
        self.request_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "path": path,
                "headers": headers,
                "body": body,
            }
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get mock server statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_mocks": len(self.mocks),
            "total_scenarios": len(self.scenarios),
            "current_scenario": self.current_scenario,
            "requests_logged": len(self.request_log),
        }

    def reset(self) -> None:
        """Reset mock server state."""
        self.current_scenario = None
        self.request_log.clear()
        for mock in self.mocks.values():
            mock.call_count = 0


class ScenarioSimulator:
    """Simulates various API scenarios.

    Example:
        simulator = ScenarioSimulator()

        # Simulate error scenario
        simulator.add_error_scenario("server_error", 500, "Internal Server Error")

        # Simulate latency
        simulator.add_latency_scenario("slow_response", 5000)

        # Simulate rate limiting
        simulator.add_rate_limit_scenario("rate_limited", 429, 60)
    """

    def __init__(self):
        """Initialize scenario simulator."""
        self.scenarios: Dict[str, MockResponse] = {}

    def add_error_scenario(
        self,
        name: str,
        status_code: int,
        error_message: str,
    ) -> None:
        """Add error scenario.

        Args:
            name: Scenario name
            status_code: Error status code
            error_message: Error message
        """
        self.scenarios[name] = MockResponse(
            status_code=status_code,
            body={"error": error_message},
            scenario=name,
        )

    def add_latency_scenario(
        self,
        name: str,
        delay_ms: float,
    ) -> None:
        """Add latency scenario.

        Args:
            name: Scenario name
            delay_ms: Delay in milliseconds
        """
        self.scenarios[name] = MockResponse(
            status_code=200,
            body={"message": "Success"},
            delay_ms=delay_ms,
            scenario=name,
        )

    def add_rate_limit_scenario(
        self,
        name: str,
        status_code: int = 429,
        retry_after: int = 60,
    ) -> None:
        """Add rate limiting scenario.

        Args:
            name: Scenario name
            status_code: Rate limit status code
            retry_after: Retry after seconds
        """
        self.scenarios[name] = MockResponse(
            status_code=status_code,
            headers={"Retry-After": str(retry_after)},
            body={"error": "Rate limit exceeded", "retry_after": retry_after},
            scenario=name,
        )

    def add_data_scenario(
        self,
        name: str,
        data: List[Dict[str, Any]],
    ) -> None:
        """Add data scenario.

        Args:
            name: Scenario name
            data: Data to return
        """
        self.scenarios[name] = MockResponse(
            status_code=200,
            body={"data": data},
            scenario=name,
        )

    def get_scenario(self, name: str) -> Optional[MockResponse]:
        """Get scenario by name.

        Args:
            name: Scenario name

        Returns:
            MockResponse or None
        """
        return self.scenarios.get(name)

    def list_scenarios(self) -> List[str]:
        """List all scenario names.

        Returns:
            List of scenario names
        """
        return list(self.scenarios.keys())


class ContractMockGenerator:
    """Generates mocks from API contracts.

    Example:
        generator = ContractMockGenerator()

        # Generate from OpenAPI
        generator.generate_from_openapi(openapi_spec)

        # Get mock endpoints
        mocks = generator.get_mocks()
    """

    def __init__(self):
        """Initialize contract mock generator."""
        self.endpoints: Dict[str, Dict[str, Any]] = {}

    def generate_from_openapi(self, spec: Dict[str, Any]) -> None:
        """Generate mocks from OpenAPI spec.

        Args:
            spec: OpenAPI specification
        """
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    self.endpoints[f"{method.upper()}:{path}"] = {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "parameters": details.get("parameters", []),
                        "responses": details.get("responses", {}),
                    }

    def generate_from_graphql(self, schema: Dict[str, Any]) -> None:
        """Generate mocks from GraphQL schema.

        Args:
            schema: GraphQL schema
        """
        # Simplified - would parse GraphQL schema
        self.endpoints["POST:/graphql"] = {
            "path": "/graphql",
            "method": "POST",
            "schema": schema,
        }

    def get_mocks(self) -> List[Dict[str, Any]]:
        """Get generated mocks.

        Returns:
            List of mock configurations
        """
        return [
            {
                "path": details["path"],
                "method": details["method"],
                "summary": details.get("summary", ""),
            }
            for details in self.endpoints.values()
        ]

    def get_mock_for_endpoint(
        self,
        method: str,
        path: str,
    ) -> Optional[Dict[str, Any]]:
        """Get mock configuration for endpoint.

        Args:
            method: HTTP method
            path: Request path

        Returns:
            Mock configuration or None
        """
        key = f"{method.upper()}:{path}"
        return self.endpoints.get(key)


class MockSuite:
    """Comprehensive mock testing suite.

    Example:
        suite = MockSuite()

        # Create mock server
        server = suite.create_server(port=8080)

        # Add mocks
        suite.add_get_mock(server, "/api/users", [{"id": "1", "name": "John"}])

        # Start server
        suite.start_server(server)
    """

    def __init__(self):
        """Initialize mock suite."""
        self.servers: List[MockServer] = []
        self.simulators: List[ScenarioSimulator] = []

    def create_server(
        self,
        port: int = 8080,
        host: str = "localhost",
    ) -> MockServer:
        """Create a mock server.

        Args:
            port: Server port
            host: Server host

        Returns:
            MockServer instance
        """
        server = MockServer(port=port, host=host)
        self.servers.append(server)
        return server

    def create_simulator(self) -> ScenarioSimulator:
        """Create a scenario simulator.

        Returns:
            ScenarioSimulator instance
        """
        simulator = ScenarioSimulator()
        self.simulators.append(simulator)
        return simulator

    def create_contract_generator(self) -> ContractMockGenerator:
        """Create a contract mock generator.

        Returns:
            ContractMockGenerator instance
        """
        return ContractMockGenerator()

    def add_get_mock(
        self,
        server: MockServer,
        path: str,
        response: Any,
    ) -> None:
        """Add GET mock to server.

        Args:
            server: Mock server
            path: URL path
            response: Response body
        """
        server.add_mock(path=path, method="GET", response=response)

    def add_post_mock(
        self,
        server: MockServer,
        path: str,
        response: Any,
        status_code: int = 201,
    ) -> None:
        """Add POST mock to server.

        Args:
            server: Mock server
            path: URL path
            response: Response body
            status_code: Status code
        """
        server.add_mock(
            path=path, method="POST", response=response, status_code=status_code
        )

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all servers.

        Returns:
            Statistics dictionary
        """
        return {
            f"server_{i}": server.get_stats() for i, server in enumerate(self.servers)
        }

    def reset_all(self) -> None:
        """Reset all servers."""
        for server in self.servers:
            server.reset()
