"""Mock Server Generator for creating FastAPI-based mock servers.

This module generates fully functional FastAPI applications that mock
external third-party APIs based on service definitions.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.ai_mocking.external_service_registry import (
    ExternalServiceDefinition,
    ExternalServiceRegistry,
    MockEndpoint,
)


@dataclass
class GeneratedMockServer:
    """Result of mock server generation."""

    service_name: str
    code: str
    file_path: Optional[Path] = None
    port: int = 8000


class MockServerGenerator:
    """Generates FastAPI mock servers for external APIs."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the generator.

        Args:
            output_dir: Directory where mock servers will be saved
        """
        self.output_dir = output_dir or Path(".e2e/mocks")
        self.registry = ExternalServiceRegistry()

    def generate_mock_server(
        self,
        service_name: str,
        port: int = 8000,
        custom_responses: Optional[Dict[str, Any]] = None,
    ) -> GeneratedMockServer:
        """Generate a FastAPI mock server for a service.

        Args:
            service_name: Name of the registered service
            port: Port for the mock server
            custom_responses: Optional custom response overrides

        Returns:
            GeneratedMockServer with code and metadata

        Raises:
            ValueError: If service is not found in registry
        """
        service = self.registry.get_service(service_name)
        if not service:
            raise ValueError(f"Service '{service_name}' not found in registry")

        code = self._generate_fastapi_code(service, port, custom_responses or {})

        return GeneratedMockServer(
            service_name=service_name,
            code=code,
            port=port,
        )

    def generate_all_mock_servers(
        self,
        services: List[str],
        base_port: int = 8001,
    ) -> List[GeneratedMockServer]:
        """Generate mock servers for multiple services.

        Args:
            services: List of service names
            base_port: Starting port number

        Returns:
            List of GeneratedMockServer
        """
        generated = []
        for i, service_name in enumerate(services):
            try:
                server = self.generate_mock_server(
                    service_name=service_name,
                    port=base_port + i,
                )
                generated.append(server)
            except ValueError as e:
                print(f"Warning: Could not generate mock for {service_name}: {e}")

        return generated

    def save_mock_server(
        self,
        server: GeneratedMockServer,
        filename: Optional[str] = None,
    ) -> Path:
        """Save a generated mock server to file.

        Args:
            server: Generated mock server
            filename: Optional filename override

        Returns:
            Path to saved file
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            filename = f"mock_{server.service_name}.py"

        file_path = self.output_dir / filename
        file_path.write_text(server.code, encoding="utf-8")

        return file_path

    def _generate_fastapi_code(
        self,
        service: ExternalServiceDefinition,
        port: int,
        custom_responses: Dict[str, Any],
    ) -> str:
        """Generate FastAPI code for a service."""
        lines = []

        # Imports
        lines.extend(
            [
                '"""Auto-generated mock server for {name}."""',
                "",
                "from fastapi import FastAPI, HTTPException, Request, Header",
                "from fastapi.responses import JSONResponse",
                "import uvicorn",
                "import time",
                "import re",
                "from typing import Optional, Dict, Any",
                "",
            ]
        )

        # Create app
        lines.extend(
            [
                f'app = FastAPI(title="Mock {service.name} API", version="1.0.0")',
                "",
                f"# Service: {service.description}",
                f"# Base URL: {service.base_url}",
                f"# Auth Type: {service.auth_type}",
                "",
            ]
        )

        # Generate state storage
        lines.extend(
            [
                "# In-memory storage for stateful mocking",
                "_storage: Dict[str, Any] = {}",
                "_request_log: list = []",
                "",
            ]
        )

        # Generate auth verification
        lines.extend(self._generate_auth_middleware(service))

        # Generate endpoints
        for endpoint in service.endpoints:
            lines.extend(
                self._generate_endpoint_handler(endpoint, service, custom_responses)
            )
            lines.append("")

        # Generate utility endpoints
        lines.extend(self._generate_utility_endpoints())

        # Generate run function
        lines.extend(
            [
                "",
                'if __name__ == "__main__":',
                f'    uvicorn.run(app, host="0.0.0.0", port={port})',
            ]
        )

        code = "\n".join(lines)
        code = code.replace("{name}", service.name)

        return code

    def _generate_auth_middleware(
        self, service: ExternalServiceDefinition
    ) -> List[str]:
        """Generate authentication verification code."""
        lines = []

        if service.auth_type == "bearer":
            lines.extend(
                [
                    "def verify_auth(authorization: Optional[str] = Header(None)) -> bool:",
                    '    """Verify Bearer token authentication."""',
                    "    if not authorization:",
                    '        raise HTTPException(status_code=401, detail="Unauthorized")',
                    '    if not authorization.startswith("Bearer "):',
                    '        raise HTTPException(status_code=401, detail="Invalid token format")',
                    "    return True",
                    "",
                ]
            )
        elif service.auth_type == "api_key":
            lines.extend(
                [
                    "def verify_auth(x_api_key: Optional[str] = Header(None)) -> bool:",
                    '    """Verify API key authentication."""',
                    "    if not x_api_key:",
                    '        raise HTTPException(status_code=401, detail="API key required")',
                    "    return True",
                    "",
                ]
            )
        elif service.auth_type == "basic":
            lines.extend(
                [
                    "import base64",
                    "",
                    "def verify_auth(authorization: Optional[str] = Header(None)) -> bool:",
                    '    """Verify Basic authentication."""',
                    "    if not authorization:",
                    '        raise HTTPException(status_code=401, detail="Unauthorized")',
                    '    if not authorization.startswith("Basic "):',
                    '        raise HTTPException(status_code=401, detail="Invalid auth format")',
                    "    return True",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "def verify_auth(**kwargs) -> bool:",
                    '    """No authentication required."""',
                    "    return True",
                    "",
                ]
            )

        return lines

    def _generate_endpoint_handler(
        self,
        endpoint: MockEndpoint,
        service: ExternalServiceDefinition,
        custom_responses: Dict[str, Any],
    ) -> List[str]:
        """Generate FastAPI endpoint handler code."""
        lines = []

        # Convert path to Python function name
        func_name = self._path_to_function_name(endpoint.path, endpoint.method)

        # Build decorator
        decorator = f'@app.{endpoint.method.lower()}("{endpoint.path}")'
        lines.append(decorator)

        # Function signature
        signature_parts = ["request: Request"]

        # Add path parameters
        path_params = self._extract_path_params(endpoint.path)
        for param in path_params:
            signature_parts.append(f"{param}: str")

        # Add auth header
        if service.auth_type == "bearer":
            signature_parts.append("authorization: Optional[str] = Header(None)")
        elif service.auth_type == "api_key":
            signature_parts.append(
                'x_api_key: Optional[str] = Header(None, alias="X-API-Key")'
            )
        elif service.auth_type == "basic":
            signature_parts.append("authorization: Optional[str] = Header(None)")

        signature = f"async def {func_name}({', '.join(signature_parts)}):"
        lines.append(signature)

        # Function body
        indent = "    "

        # Add delay if specified
        if endpoint.delay_ms > 0:
            lines.append(f"{indent}time.sleep({endpoint.delay_ms / 1000})")

        # Verify auth
        if service.auth_type != "none":
            lines.append(
                f"{indent}verify_auth({self._get_auth_param(service.auth_type)})"
            )

        # Log request
        lines.append(f"{indent}_request_log.append({{")
        lines.append(f'{indent}    "method": "{endpoint.method}",')
        lines.append(f'{indent}    "path": "{endpoint.path}",')
        lines.append(f'{indent}    "timestamp": time.time(),')
        lines.append(f"{indent}}})")

        # Get response
        response_key = f"{endpoint.method.upper()} {endpoint.path}"
        if response_key in custom_responses:
            lines.append(
                f"{indent}response_data = {self._dict_to_python(custom_responses[response_key])}"
            )
        elif endpoint.conditional_response:
            lines.append(
                f"{indent}body = await request.json() if request.method in ['POST', 'PUT', 'PATCH'] else {{}}"
            )
            lines.append(
                f"{indent}response_data = _get_conditional_response_{func_name}(body)"
            )
        else:
            lines.append(
                f"{indent}response_data = {self._dict_to_python(endpoint.response_example or {})}"
            )

        # Return response
        lines.append(f"{indent}return JSONResponse(")
        lines.append(f"{indent}    content=response_data,")
        lines.append(f"{indent}    status_code={endpoint.status_code},")
        lines.append(f"{indent})")

        return lines

    def _generate_utility_endpoints(self) -> List[str]:
        """Generate utility endpoints for the mock server."""
        lines = [
            '@app.get("/__health")',
            "async def health_check():",
            '    """Health check endpoint."""',
            '    return {"status": "healthy"}',
            "",
            '@app.get("/__requests")',
            "async def get_requests():",
            '    """Get all captured requests."""',
            '    return {"requests": _request_log}',
            "",
            '@app.post("/__reset")',
            "async def reset_state():",
            '    """Reset mock server state."""',
            "    _storage.clear()",
            "    _request_log.clear()",
            '    return {"status": "reset"}',
            "",
        ]
        return lines

    def _path_to_function_name(self, path: str, method: str) -> str:
        """Convert URL path to valid Python function name."""
        # Remove leading slash and replace special chars
        name = path.strip("/").replace("/", "_").replace("-", "_")
        name = re.sub(r"[{}]", "", name)  # Remove path param braces
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        return f"handle_{method.lower()}_{name}"

    def _extract_path_params(self, path: str) -> List[str]:
        """Extract path parameters from URL pattern."""
        return re.findall(r"\{(\w+)\}", path)

    def _get_auth_param(self, auth_type: str) -> str:
        """Get the auth parameter name for the auth type."""
        if auth_type == "bearer":
            return "authorization"
        elif auth_type == "api_key":
            return "x_api_key"
        elif auth_type == "basic":
            return "authorization"
        return ""

    def _dict_to_python(self, data: Any, indent: int = 0) -> str:
        """Convert Python dict/list to Python code string."""
        if isinstance(data, dict):
            if not data:
                return "{}"
            items = []
            for k, v in data.items():
                key = f'"{k}"' if isinstance(k, str) else str(k)
                val = self._dict_to_python(v, indent + 1)
                items.append(f"{key}: {val}")
            return "{" + ", ".join(items) + "}"
        elif isinstance(data, list):
            if not data:
                return "[]"
            items = [self._dict_to_python(item, indent + 1) for item in data]
            return "[" + ", ".join(items) + "]"
        elif isinstance(data, str):
            # Escape quotes
            escaped = data.replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(data, bool):
            return str(data).lower()
        elif data is None:
            return "None"
        else:
            return str(data)

    def generate_docker_compose(
        self,
        servers: List[GeneratedMockServer],
        project_name: str = "e2e-mocks",
    ) -> str:
        """Generate docker-compose.yml for all mock servers.

        Args:
            servers: List of generated mock servers
            project_name: Docker Compose project name

        Returns:
            Docker Compose YAML content
        """
        lines = [
            "version: '3.8'",
            "",
            f"# Auto-generated docker-compose for {project_name}",
            "",
            "services:",
        ]

        for server in servers:
            service_name = f"mock-{server.service_name}"
            lines.extend(
                [
                    f"  {service_name}:",
                    "    build:",
                    "      context: .",
                    f"      dockerfile: Dockerfile.{server.service_name}",
                    "    ports:",
                    f'      - "{server.port}:{server.port}"',
                    "    environment:",
                    f"      - PORT={server.port}",
                    "    healthcheck:",
                    f'      test: ["CMD", "curl", "-f", "http://localhost:{server.port}/__health"]',
                    "      interval: 10s",
                    "      timeout: 5s",
                    "      retries: 3",
                    "",
                ]
            )

        return "\n".join(lines)

    def generate_dockerfile(self, server: GeneratedMockServer) -> str:
        """Generate Dockerfile for a mock server.

        Args:
            server: Generated mock server

        Returns:
            Dockerfile content
        """
        return f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn

# Copy mock server code
COPY mock_{server.service_name}.py ./app.py

# Expose port
EXPOSE {server.port}

# Run server
CMD ["python", "app.py"]
"""


def generate_mock_server(
    service_name: str,
    output_dir: str = ".e2e/mocks",
    port: int = 8000,
) -> Path:
    """Convenience function to generate and save a mock server.

    Args:
        service_name: Name of the external service to mock
        output_dir: Directory to save the mock server
        port: Port for the mock server

    Returns:
        Path to the generated file
    """
    generator = MockServerGenerator(Path(output_dir))
    server = generator.generate_mock_server(service_name, port)
    return generator.save_mock_server(server)
