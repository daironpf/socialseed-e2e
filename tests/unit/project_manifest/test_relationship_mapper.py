"""Unit tests for relationship mapper (Phase 2)."""

import pytest

from socialseed_e2e.project_manifest.relationship_mapper import (
    MicroserviceRelationshipMapper,
    ServiceDependency,
)


class TestMicroserviceRelationshipMapper:
    """Tests for MicroserviceRelationshipMapper (Phase 2)."""

    @pytest.fixture
    def project_with_env(self, tmp_path):
        """Create a project with .env files."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
# Service configuration
AUTH_SERVICE_URL=http://localhost:8080
USER_SERVICE_HOST=localhost
PAYMENT_API_PORT=8082
DATABASE_URL=postgres://localhost:5432/db

# Other config
DEBUG=true
""")
        return tmp_path

    @pytest.fixture
    def project_with_docker_compose(self, tmp_path):
        """Create a project with docker-compose file."""
        docker_compose = tmp_path / "docker-compose.yml"
        docker_compose.write_text("""
version: '3.8'
services:
  auth-service:
    image: auth-service:latest
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgres://db:5432/auth

  user-service:
    image: user-service:latest
    ports:
      - "8081:8081"
    depends_on:
      - auth-service

  payment-api:
    image: payment-api:latest
    ports:
      - "8082:8082"
""")
        return tmp_path

    def test_detect_service_dependencies_from_env(self, project_with_env):
        """Test detecting service dependencies from .env file."""
        mapper = MicroserviceRelationshipMapper(project_with_env)
        deps = mapper.detect_service_dependencies()
        
        assert len(deps) >= 2
        service_names = [d.target_service for d in deps]
        
    def test_detect_service_dependencies_from_docker_compose(self, project_with_docker_compose):
        """Test detecting service dependencies from docker-compose."""
        mapper = MicroserviceRelationshipMapper(project_with_docker_compose)
        deps = mapper.detect_service_dependencies()
        
        assert len(deps) >= 1

    def test_normalize_service_name(self):
        """Test service name normalization."""
        mapper = MicroserviceRelationshipMapper.__new__(MicroserviceRelationshipMapper)
        
        assert mapper._normalize_service_name("AUTH-SERVICE") == "auth-service"
        assert mapper._normalize_service_name("user_service") == "user_service"
        assert mapper._normalize_service_name("PaymentAPI") == "paymentapi"

    def test_detect_connection_type_http(self):
        """Test HTTP connection type detection."""
        mapper = MicroserviceRelationshipMapper.__new__(MicroserviceRelationshipMapper)
        
        content = "AUTH_SERVICE_URL=http://localhost:8080"
        conn_type = mapper._detect_connection_type(content, "auth")
        
        assert conn_type == "http"

    def test_detect_connection_type_database(self):
        """Test database connection type detection."""
        mapper = MicroserviceRelationshipMapper.__new__(MicroserviceRelationshipMapper)
        
        content = "DATABASE_URL=postgres://localhost:5432/mydb"
        conn_type = mapper._detect_connection_type(content, "database")
        
        assert conn_type == "database"

    def test_detect_connection_type_grpc(self):
        """Test gRPC connection type detection."""
        mapper = MicroserviceRelationshipMapper.__new__(MicroserviceRelationshipMapper)
        
        content = "GRPC_HOST=localhost:50051"
        conn_type = mapper._detect_connection_type(content, "grpc")
        
        assert conn_type == "grpc"

    def test_extract_endpoint(self):
        """Test endpoint extraction from content."""
        mapper = MicroserviceRelationshipMapper.__new__(MicroserviceRelationshipMapper)
        
        content = "AUTH_SERVICE_URL=http://auth:8080/api/v1"
        endpoint = mapper._extract_endpoint(content, "auth")
        
        assert "auth" in endpoint.lower() or "http" in endpoint.lower()

    def test_service_dependency_dataclass(self):
        """Test ServiceDependency dataclass."""
        dep = ServiceDependency(
            source_service="frontend",
            target_service="auth",
            connection_type="http",
            endpoint="/api/auth/login",
            environment_vars=["AUTH_SERVICE_URL"],
            confidence=0.8,
        )
        
        assert dep.source_service == "frontend"
        assert dep.target_service == "auth"
        assert dep.connection_type == "http"
        assert dep.confidence == 0.8
