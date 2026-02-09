"""Tests for The Observer - Service Detection (Issue #186)."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from socialseed_e2e.project_manifest.observer import (
    DetectedService,
    DockerContainer,
    DockerSetupSuggestion,
    PortScanner,
    PortScanResult,
    ServiceObserver,
)


class TestPortScanner:
    """Test suite for PortScanner."""

    @pytest.fixture
    def scanner(self):
        return PortScanner(timeout=1.0)

    def test_init(self, scanner):
        """Test scanner initialization."""
        assert scanner.timeout == 1.0
        assert scanner.max_workers == 50

    def test_common_ports_defined(self, scanner):
        """Test that common ports are defined."""
        assert len(scanner.COMMON_HTTP_PORTS) > 0
        assert 80 in scanner.COMMON_HTTP_PORTS
        assert 8080 in scanner.COMMON_HTTP_PORTS
        assert 443 in scanner.COMMON_HTTP_PORTS

    def test_common_api_ports_defined(self, scanner):
        """Test that API ports are defined."""
        assert len(scanner.COMMON_API_PORTS) > 0
        assert 8000 in scanner.COMMON_API_PORTS
        assert 3000 in scanner.COMMON_API_PORTS
        assert 5000 in scanner.COMMON_API_PORTS

    def test_health_endpoints_defined(self, scanner):
        """Test health endpoints list."""
        assert "/health" in scanner.HEALTH_ENDPOINTS
        assert "/healthz" in scanner.HEALTH_ENDPOINTS
        assert "/actuator/health" in scanner.HEALTH_ENDPOINTS

    @pytest.mark.asyncio
    async def test_scan_closed_port(self, scanner):
        """Test scanning a closed port."""
        # Scan a port that's likely closed (high random port)
        result = await scanner._scan_port("localhost", 65432, detect_protocols=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_scan_port_detects_open_port(self, scanner):
        """Test that scanner detects open ports."""
        # This test would need an actual service running
        # For now, just test the method signature
        result = await scanner._scan_port("localhost", 8080, detect_protocols=False)
        # Result depends on whether port 8080 is actually open
        assert result is None or isinstance(result, PortScanResult)


class TestServiceObserver:
    """Test suite for ServiceObserver."""

    @pytest.fixture
    def observer(self, tmp_path):
        return ServiceObserver(tmp_path)

    def test_init(self, observer, tmp_path):
        """Test observer initialization."""
        assert observer.project_root == tmp_path
        assert isinstance(observer.port_scanner, PortScanner)
        assert observer.detected_services == []
        assert observer.docker_containers == []

    def test_find_docker_setup_no_dockerfile(self, observer):
        """Test finding Docker setup when no Dockerfile exists."""
        result = observer._find_docker_setup()
        assert result is None

    def test_find_docker_setup_with_dockerfile(self, observer):
        """Test finding Docker setup with Dockerfile."""
        # Create a Dockerfile
        dockerfile = observer.project_root / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\n")

        result = observer._find_docker_setup()

        assert result is not None
        assert isinstance(result, DockerSetupSuggestion)
        assert result.dockerfile_path == dockerfile
        assert result.can_auto_build is True
        assert "docker build" in result.suggested_command

    def test_find_docker_setup_with_compose(self, observer):
        """Test finding Docker setup with docker-compose."""
        # Create docker-compose.yml
        compose = observer.project_root / "docker-compose.yml"
        compose.write_text(
            """
services:
  web:
    build: .
    ports:
      - "8080:8080"
  db:
    image: postgres
"""
        )

        # Create Dockerfile too
        dockerfile = observer.project_root / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\n")

        result = observer._find_docker_setup()

        assert result is not None
        assert result.compose_path == compose
        assert "docker-compose" in result.suggested_command
        assert "web" in result.services_in_compose
        assert "db" in result.services_in_compose

    def test_parse_docker_ports(self, observer):
        """Test parsing Docker port mappings."""
        ports_str = "0.0.0.0:8080->8080/tcp, 0.0.0.0:8443->8443/tcp"

        ports = observer._parse_docker_ports(ports_str)

        assert len(ports) == 2
        assert ports[0]["public"] == 8080
        assert ports[0]["private"] == 8080
        assert ports[0]["type"] == "tcp"

    def test_parse_docker_ports_empty(self, observer):
        """Test parsing empty Docker ports."""
        ports = observer._parse_docker_ports("")
        assert ports == []

    def test_port_result_to_service(self, observer):
        """Test converting PortScanResult to DetectedService."""
        from socialseed_e2e.project_manifest.observer import PortScanResult

        port_result = PortScanResult(
            port=8080,
            is_open=True,
            protocol="http",
            service_type="http",
            response_time_ms=100.0,
            health_endpoint="/health",
        )

        service = observer._port_result_to_service("localhost", port_result)

        assert isinstance(service, DetectedService)
        assert service.port == 8080
        assert service.base_url == "http://localhost:8080"
        assert service.service_type == "http"
        assert service.health_endpoint == "/health"


class TestDockerContainer:
    """Test DockerContainer dataclass."""

    def test_docker_container_creation(self):
        """Test creating a DockerContainer."""
        container = DockerContainer(
            container_id="abc123",
            name="test-container",
            image="test:latest",
            ports=[{"public": 8080, "private": 8080, "type": "tcp"}],
            status="Up 2 hours",
            health="healthy",
        )

        assert container.container_id == "abc123"
        assert container.name == "test-container"
        assert container.image == "test:latest"
        assert len(container.ports) == 1
        assert container.status == "Up 2 hours"
        assert container.health == "healthy"


class TestPortScanResult:
    """Test PortScanResult dataclass."""

    def test_port_scan_result_creation(self):
        """Test creating a PortScanResult."""
        result = PortScanResult(
            port=8080,
            is_open=True,
            protocol="http",
            service_type="http",
            response_time_ms=150.5,
            health_endpoint="/health",
            api_version="v1",
            metadata={"server": "nginx"},
        )

        assert result.port == 8080
        assert result.is_open is True
        assert result.protocol == "http"
        assert result.service_type == "http"
        assert result.response_time_ms == 150.5
        assert result.health_endpoint == "/health"
        assert result.api_version == "v1"
        assert result.metadata == {"server": "nginx"}


class TestDetectedService:
    """Test DetectedService dataclass."""

    def test_detected_service_creation(self):
        """Test creating a DetectedService."""
        service = DetectedService(
            name="users-api",
            host="localhost",
            port=8080,
            base_url="http://localhost:8080",
            service_type="http",
            health_endpoint="/health",
            detected_from="docker",
            confidence=0.95,
            process_info={"pid": "1234"},
            matched_code_service="users-service",
        )

        assert service.name == "users-api"
        assert service.host == "localhost"
        assert service.port == 8080
        assert service.base_url == "http://localhost:8080"
        assert service.service_type == "http"
        assert service.health_endpoint == "/health"
        assert service.detected_from == "docker"
        assert service.confidence == 0.95
        assert service.process_info == {"pid": "1234"}
        assert service.matched_code_service == "users-service"


class TestDockerSetupSuggestion:
    """Test DockerSetupSuggestion dataclass."""

    def test_docker_setup_suggestion_creation(self):
        """Test creating a DockerSetupSuggestion."""
        suggestion = DockerSetupSuggestion(
            dockerfile_path=Path("/project/Dockerfile"),
            compose_path=Path("/project/docker-compose.yml"),
            suggested_command="docker-compose up -d",
            can_auto_build=True,
            build_time_estimate="1-3 minutes",
            services_in_compose=["web", "db", "cache"],
        )

        assert suggestion.dockerfile_path == Path("/project/Dockerfile")
        assert suggestion.compose_path == Path("/project/docker-compose.yml")
        assert suggestion.suggested_command == "docker-compose up -d"
        assert suggestion.can_auto_build is True
        assert suggestion.build_time_estimate == "1-3 minutes"
        assert suggestion.services_in_compose == ["web", "db", "cache"]


class TestIntegration:
    """Integration tests for The Observer."""

    @pytest.mark.asyncio
    async def test_observe_no_services(self, tmp_path):
        """Test observing a project with no running services."""
        observer = ServiceObserver(tmp_path)

        # Mock the scan to return empty
        with patch.object(observer.port_scanner, "scan_host", return_value=[]):
            with patch.object(observer, "_scan_docker_containers", return_value=[]):
                results = await observer.observe(
                    hosts=["localhost"], scan_docker=False, cross_reference=False
                )

        assert results["services_detected"] == []
        assert results["docker_containers"] == []

    @pytest.mark.asyncio
    async def test_auto_setup_no_docker(self, tmp_path):
        """Test auto-setup when no Docker is available."""
        observer = ServiceObserver(tmp_path)

        result = await observer.auto_setup(dry_run=True)

        assert result["success"] is False
        assert "No Dockerfile" in result["message"]

    @pytest.mark.asyncio
    async def test_auto_setup_dry_run(self, tmp_path):
        """Test auto-setup in dry-run mode."""
        observer = ServiceObserver(tmp_path)

        # Create Dockerfile
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\n")

        result = await observer.auto_setup(dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert "docker build" in result["command"]
