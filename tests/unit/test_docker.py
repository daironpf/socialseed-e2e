"""Tests for Docker Compose integration.

This module contains unit tests for the Docker Compose integration.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from socialseed_e2e.docker import (
    ComposeConfig,
    DockerComposeError,
    DockerComposeManager,
    DockerComposeOptions,
    DockerComposeParser,
    HealthCheckError,
    ServiceConfig,
    ServiceNotFoundError,
    ServiceStatus,
)

pytestmark = pytest.mark.unit


class TestDockerComposeParser:
    """Test cases for DockerComposeParser."""

    @pytest.fixture
    def sample_compose_file(self):
        """Create a sample docker-compose.yml file."""
        content = """
version: '3.8'

services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    environment:
      - NGINX_HOST=localhost
      - NGINX_PORT=80
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - db_data:/var/lib/postgresql/data
    depends_on:
      - web

volumes:
  db_data:

networks:
  default:
    driver: bridge
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(content)
            return Path(f.name)

    def test_parse(self, sample_compose_file):
        """Test parsing a compose file."""
        parser = DockerComposeParser()
        config = parser.parse(sample_compose_file)

        assert isinstance(config, ComposeConfig)
        assert config.version == "3.8"
        assert "web" in config.services
        assert "db" in config.services

    def test_parse_services(self, sample_compose_file):
        """Test parsing service configurations."""
        parser = DockerComposeParser()
        config = parser.parse(sample_compose_file)

        web = config.services["web"]
        assert web.name == "web"
        assert web.image == "nginx:latest"
        assert "80:80" in web.ports
        assert web.health_check is not None

        db = config.services["db"]
        assert db.name == "db"
        assert db.image == "postgres:13"
        assert "5432:5432" in db.ports
        assert "web" in db.depends_on

    def test_parse_environment_dict(self, sample_compose_file):
        """Test parsing environment variables as dict."""
        parser = DockerComposeParser()
        config = parser.parse(sample_compose_file)

        db = config.services["db"]
        assert db.environment["POSTGRES_USER"] == "user"
        assert db.environment["POSTGRES_PASSWORD"] == "pass"

    def test_parse_environment_list(self):
        """Test parsing environment variables as list."""
        parser = DockerComposeParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("""
version: '3'
services:
  app:
    image: test
    environment:
      - KEY1=value1
      - KEY2=value2
""")
            f.flush()
            config = parser.parse(f.name)

        app = config.services["app"]
        assert app.environment["KEY1"] == "value1"
        assert app.environment["KEY2"] == "value2"

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        parser = DockerComposeParser()

        with pytest.raises(DockerComposeError):
            parser.parse("/nonexistent/docker-compose.yml")

    def test_get_service(self, sample_compose_file):
        """Test getting a specific service."""
        parser = DockerComposeParser()
        web = parser.get_service(sample_compose_file, "web")

        assert web.name == "web"
        assert web.image == "nginx:latest"

    def test_get_service_not_found(self, sample_compose_file):
        """Test getting non-existent service."""
        parser = DockerComposeParser()

        with pytest.raises(ServiceNotFoundError):
            parser.get_service(sample_compose_file, "nonexistent")

    def test_list_services(self, sample_compose_file):
        """Test listing services."""
        parser = DockerComposeParser()
        services = parser.list_services(sample_compose_file)

        assert "web" in services
        assert "db" in services
        assert len(services) == 2

    def test_validate_valid_file(self, sample_compose_file):
        """Test validating a valid compose file."""
        parser = DockerComposeParser()
        errors = parser.validate(sample_compose_file)

        assert len(errors) == 0

    def test_validate_empty_services(self):
        """Test validating file with no services."""
        parser = DockerComposeParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("version: '3'\nservices: {}")
            f.flush()
            errors = parser.validate(f.name)

        assert len(errors) > 0
        assert any("No services" in e for e in errors)

    def test_validate_missing_image(self):
        """Test validating service without image or build."""
        parser = DockerComposeParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("""
version: '3'
services:
  app:
    ports:
      - "80:80"
""")
            f.flush()
            errors = parser.validate(f.name)

        assert any("no image or build" in e.lower() for e in errors)


class TestDockerComposeManager:
    """Test cases for DockerComposeManager."""

    @pytest.fixture
    def sample_compose_file(self):
        """Create a sample docker-compose.yml file."""
        content = """
version: '3'
services:
  web:
    image: nginx
    ports:
      - "80:80"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(content)
            return Path(f.name)

    @pytest.fixture
    def manager(self, sample_compose_file):
        """Create a DockerComposeManager instance."""
        return DockerComposeManager(sample_compose_file)

    def test_init(self, sample_compose_file):
        """Test initialization."""
        manager = DockerComposeManager(sample_compose_file)

        assert manager.compose_file == Path(sample_compose_file)
        assert manager.parser is not None

    def test_init_with_options(self, sample_compose_file):
        """Test initialization with options."""
        options = DockerComposeOptions(build=True, detach=False)
        manager = DockerComposeManager(sample_compose_file, options)

        assert manager.options.build is True
        assert manager.options.detach is False

    @patch("subprocess.run")
    def test_up(self, mock_run, manager):
        """Test starting services."""
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        manager.up()

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "up" in call_args
        assert "-d" in call_args

    @patch("subprocess.run")
    def test_up_with_build(self, mock_run, manager):
        """Test starting services with build."""
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        manager.up(build=True)

        call_args = mock_run.call_args[0][0]
        assert "--build" in call_args

    @patch("subprocess.run")
    def test_down(self, mock_run, manager):
        """Test stopping services."""
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        manager.down()

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "down" in call_args

    @patch("subprocess.run")
    def test_ps(self, mock_run, manager):
        """Test getting service status."""
        mock_run.return_value = Mock(
            stdout='[{"Service": "web", "State": "running", "Health": "healthy"}]',
            stderr="",
            returncode=0,
        )

        status = manager.ps()

        assert len(status) == 1
        assert status[0].name == "web"
        assert status[0].state == "running"

    @patch("subprocess.run")
    def test_is_running(self, mock_run, manager):
        """Test checking if service is running."""
        mock_run.return_value = Mock(
            stdout='[{"Service": "web", "State": "running"}]',
            stderr="",
            returncode=0,
        )

        assert manager.is_running("web") is True
        assert manager.is_running("nonexistent") is False

    @patch("subprocess.run")
    def test_is_healthy(self, mock_run, manager):
        """Test checking if service is healthy."""
        mock_run.return_value = Mock(
            stdout='[{"Service": "web", "State": "running", "Health": "healthy"}]',
            stderr="",
            returncode=0,
        )

        assert manager.is_healthy("web") is True
        assert manager.is_healthy("db") is False  # Not in output

    @patch("subprocess.run")
    def test_logs(self, mock_run, manager):
        """Test getting logs."""
        mock_run.return_value = Mock(
            stdout="Log line 1\nLog line 2",
            stderr="",
            returncode=0,
        )

        logs = manager.logs()

        assert "Log line 1" in logs
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_build(self, mock_run, manager):
        """Test building services."""
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        manager.build()

        call_args = mock_run.call_args[0][0]
        assert "build" in call_args

    def test_list_services(self, manager):
        """Test listing services."""
        services = manager.list_services()

        assert "web" in services
        assert len(services) == 1


class TestDockerComposeOptions:
    """Test cases for DockerComposeOptions."""

    def test_default_values(self):
        """Test default option values."""
        options = DockerComposeOptions()

        assert options.file == "docker-compose.yml"
        assert options.project_name is None
        assert options.build is False
        assert options.detach is True
        assert options.timeout == 30

    def test_custom_values(self):
        """Test custom option values."""
        options = DockerComposeOptions(
            file="custom-compose.yml",
            project_name="my-project",
            build=True,
            detach=False,
            timeout=60,
        )

        assert options.file == "custom-compose.yml"
        assert options.project_name == "my-project"
        assert options.build is True
        assert options.detach is False
        assert options.timeout == 60


class TestServiceConfig:
    """Test cases for ServiceConfig."""

    def test_creation(self):
        """Test creating a ServiceConfig."""
        config = ServiceConfig(
            name="web",
            image="nginx:latest",
            ports=["80:80", "443:443"],
            environment={"ENV": "production"},
            depends_on=["db"],
        )

        assert config.name == "web"
        assert config.image == "nginx:latest"
        assert len(config.ports) == 2
        assert config.environment["ENV"] == "production"
        assert "db" in config.depends_on


class TestServiceStatus:
    """Test cases for ServiceStatus."""

    def test_creation(self):
        """Test creating a ServiceStatus."""
        status = ServiceStatus(
            name="web",
            state="running",
            health="healthy",
            ports={"80": "8080"},
            uptime="5 minutes",
        )

        assert status.name == "web"
        assert status.state == "running"
        assert status.health == "healthy"
        assert status.ports["80"] == "8080"
        assert status.uptime == "5 minutes"


class TestExceptions:
    """Test cases for exceptions."""

    def test_docker_compose_error(self):
        """Test DockerComposeError."""
        error = DockerComposeError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_service_not_found_error(self):
        """Test ServiceNotFoundError."""
        error = ServiceNotFoundError("Service not found")
        assert "Service not found" in str(error)
        assert isinstance(error, DockerComposeError)

    def test_health_check_error(self):
        """Test HealthCheckError."""
        error = HealthCheckError("Health check failed")
        assert "Health check failed" in str(error)
        assert isinstance(error, DockerComposeError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
