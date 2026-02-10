"""Tests for AI Mocking system."""

import json
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from socialseed_e2e.ai_mocking.contract_validator import (
    ContractValidator,
    ValidationError,
    ValidationResult,
    validate_request_contract,
    validate_response_contract,
)
from socialseed_e2e.ai_mocking.external_api_analyzer import (
    ExternalAPIAnalyzer,
    ExternalAPICall,
    ExternalAPIDependency,
    analyze_external_apis,
)
from socialseed_e2e.ai_mocking.external_service_registry import (
    ExternalServiceDefinition,
    ExternalServiceRegistry,
    MockEndpoint,
)
from socialseed_e2e.ai_mocking.mock_server_generator import (
    GeneratedMockServer,
    MockServerGenerator,
    generate_mock_server,
)


class TestExternalAPIAnalyzer:
    """Test suite for ExternalAPIAnalyzer."""

    def test_analyzer_initialization(self, tmp_path):
        """Test analyzer initialization."""
        analyzer = ExternalAPIAnalyzer(tmp_path)
        assert analyzer.project_root == tmp_path
        assert analyzer.detected_apis == {}

    def test_detect_language_python(self, tmp_path):
        """Test language detection for Python files."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        assert analyzer._detect_language(Path("test.py")) == "python"

    def test_detect_language_javascript(self, tmp_path):
        """Test language detection for JavaScript files."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        assert analyzer._detect_language(Path("test.js")) == "javascript"
        assert analyzer._detect_language(Path("test.ts")) == "javascript"
        assert analyzer._detect_language(Path("test.jsx")) == "javascript"
        assert analyzer._detect_language(Path("test.tsx")) == "javascript"

    def test_detect_language_java(self, tmp_path):
        """Test language detection for Java files."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        assert analyzer._detect_language(Path("Test.java")) == "java"

    def test_detect_language_unknown(self, tmp_path):
        """Test language detection for unknown files."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        assert analyzer._detect_language(Path("test.unknown")) == "unknown"

    def test_is_external_url(self, tmp_path):
        """Test external URL detection."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        assert analyzer._is_external_url("https://api.stripe.com")
        assert analyzer._is_external_url("http://example.com")
        assert analyzer._is_external_url("https://api.example.com/v1")

        assert not analyzer._is_external_url("/api/users")
        assert not analyzer._is_external_url("relative/path")

    def test_extract_service_name(self, tmp_path):
        """Test service name extraction from URLs."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        assert analyzer._extract_service_name("https://api.stripe.com/v1") == "stripe"
        assert analyzer._extract_service_name("https://maps.googleapis.com") == "google_maps"
        assert analyzer._extract_service_name("https://api.github.com") == "github"
        assert analyzer._extract_service_name("https://custom.api.com/v1") == "custom_api"

    def test_detect_method_from_context(self, tmp_path):
        """Test HTTP method detection from code context."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        assert analyzer._detect_method_from_context("requests.post(url)") == "POST"
        assert analyzer._detect_method_from_context("axios.get(url)") == "GET"
        assert analyzer._detect_method_from_context("client.put(url)") == "PUT"
        assert analyzer._detect_method_from_context("api.delete(url)") == "DELETE"
        assert analyzer._detect_method_from_context("some.other.call()") == "GET"

    def test_find_http_calls_python_requests(self, tmp_path):
        """Test finding HTTP calls with Python requests."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        content = """
import requests

response = requests.get("https://api.stripe.com/v1/customers")
data = requests.post("https://api.github.com/repos", json={"name": "test"})
"""
        lines = content.split("\n")

        analyzer._find_http_calls(content, lines, tmp_path / "test.py", "python")

        assert "stripe" in analyzer.detected_apis
        assert len(analyzer.detected_apis["stripe"].detected_calls) > 0

    def test_find_known_api_patterns(self, tmp_path):
        """Test finding known API patterns."""
        analyzer = ExternalAPIAnalyzer(tmp_path)

        content = """
# Using Stripe
response = requests.get("https://api.stripe.com/v1/customers")

# Using Google Maps
geocode_result = requests.get("https://maps.googleapis.com/maps/api/geocode/json")
"""
        lines = content.split("\n")

        analyzer._find_known_api_patterns(content, lines, tmp_path / "test.py")

        # Should detect APIs
        assert any("stripe" in name for name in analyzer.detected_apis.keys())

    def test_convenience_function(self, tmp_path):
        """Test analyze_external_apis convenience function."""
        # Create a test file
        test_file = tmp_path / "test_api.py"
        test_file.write_text(
            """
import requests
response = requests.get("https://api.stripe.com/v1/customers")
"""
        )

        result = analyze_external_apis(str(tmp_path))

        assert isinstance(result, dict)


class TestExternalServiceRegistry:
    """Test suite for ExternalServiceRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ExternalServiceRegistry()

        assert len(registry.list_services()) > 0

    def test_get_service_stripe(self):
        """Test getting Stripe service definition."""
        registry = ExternalServiceRegistry()

        service = registry.get_service("stripe")
        assert service is not None
        assert service.name == "stripe"
        assert service.base_url == "https://api.stripe.com"
        assert service.auth_type == "bearer"

    def test_get_service_google_maps(self):
        """Test getting Google Maps service definition."""
        registry = ExternalServiceRegistry()

        service = registry.get_service("google_maps")
        assert service is not None
        assert service.name == "google_maps"
        assert service.auth_type == "api_key"

    def test_get_service_aws_s3(self):
        """Test getting AWS S3 service definition."""
        registry = ExternalServiceRegistry()

        service = registry.get_service("aws_s3")
        assert service is not None
        assert service.auth_type == "aws_signature"

    def test_get_service_nonexistent(self):
        """Test getting non-existent service."""
        registry = ExternalServiceRegistry()

        assert registry.get_service("nonexistent") is None

    def test_has_service(self):
        """Test checking if service exists."""
        registry = ExternalServiceRegistry()

        assert registry.has_service("stripe")
        assert registry.has_service("google_maps")
        assert not registry.has_service("nonexistent")

    def test_list_services(self):
        """Test listing all services."""
        registry = ExternalServiceRegistry()

        services = registry.list_services()
        assert "stripe" in services
        assert "google_maps" in services
        assert "aws_s3" in services

    def test_get_mock_endpoint(self):
        """Test getting specific mock endpoint."""
        registry = ExternalServiceRegistry()

        endpoint = registry.get_mock_endpoint("stripe", "/v1/customers", "POST")
        assert endpoint is not None
        assert endpoint.method == "POST"
        assert endpoint.path == "/v1/customers"

    def test_register_custom_service(self):
        """Test registering custom service."""
        registry = ExternalServiceRegistry()

        custom_service = ExternalServiceDefinition(
            name="custom_api",
            base_url="https://api.custom.com",
            description="Custom API",
            auth_type="api_key",
        )

        registry.register_service(custom_service)

        assert registry.has_service("custom_api")
        retrieved = registry.get_service("custom_api")
        assert retrieved.base_url == "https://api.custom.com"


class TestMockServerGenerator:
    """Test suite for MockServerGenerator."""

    def test_generator_initialization(self, tmp_path):
        """Test generator initialization."""
        generator = MockServerGenerator(tmp_path)

        assert generator.output_dir == tmp_path
        assert generator.registry is not None

    def test_generate_mock_server_stripe(self, tmp_path):
        """Test generating Stripe mock server."""
        generator = MockServerGenerator(tmp_path)

        server = generator.generate_mock_server("stripe", port=8001)

        assert isinstance(server, GeneratedMockServer)
        assert server.service_name == "stripe"
        assert server.port == 8001
        assert "FastAPI" in server.code
        assert "stripe" in server.code

    def test_generate_mock_server_invalid_service(self, tmp_path):
        """Test generating mock for invalid service."""
        generator = MockServerGenerator(tmp_path)

        with pytest.raises(ValueError, match="nonexistent"):
            generator.generate_mock_server("nonexistent")

    def test_save_mock_server(self, tmp_path):
        """Test saving mock server to file."""
        generator = MockServerGenerator(tmp_path)
        server = generator.generate_mock_server("stripe", port=8001)

        file_path = generator.save_mock_server(server)

        assert file_path.exists()
        assert file_path.name == "mock_stripe.py"
        content = file_path.read_text()
        assert "FastAPI" in content

    def test_generate_dockerfile(self, tmp_path):
        """Test generating Dockerfile."""
        generator = MockServerGenerator(tmp_path)
        server = generator.generate_mock_server("stripe", port=8001)

        dockerfile = generator.generate_dockerfile(server)

        assert "FROM python:3.11-slim" in dockerfile
        assert "pip install fastapi uvicorn" in dockerfile
        assert "8001" in dockerfile

    def test_generate_docker_compose(self, tmp_path):
        """Test generating docker-compose.yml."""
        generator = MockServerGenerator(tmp_path)
        servers = [
            generator.generate_mock_server("stripe", port=8001),
            generator.generate_mock_server("google_maps", port=8002),
        ]

        compose = generator.generate_docker_compose(servers)

        assert "version: '3.8'" in compose
        assert "mock-stripe:" in compose
        assert "mock-google_maps:" in compose
        assert "8001:8001" in compose
        assert "8002:8002" in compose

    def test_generate_all_mock_servers(self, tmp_path):
        """Test generating multiple mock servers."""
        generator = MockServerGenerator(tmp_path)

        servers = generator.generate_all_mock_servers(["stripe", "google_maps"], base_port=9000)

        assert len(servers) == 2
        assert servers[0].port == 9000
        assert servers[1].port == 9001

    def test_convenience_function(self, tmp_path):
        """Test generate_mock_server convenience function."""
        with patch("socialseed_e2e.ai_mocking.mock_server_generator.Path") as mock_path:
            mock_path.return_value = tmp_path

            result = generate_mock_server("stripe", str(tmp_path), port=8001)

            assert isinstance(result, Path)


class TestContractValidator:
    """Test suite for ContractValidator."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = ContractValidator()

        assert validator._schemas == {}

    def test_validate_request_valid(self):
        """Test validating valid request."""
        validator = ContractValidator()

        request = {"name": "John", "email": "john@example.com"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["name", "email"],
        }

        result = validator.validate_request(request, schema)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_request_missing_required(self):
        """Test validating request with missing required field."""
        validator = ContractValidator()

        request = {"name": "John"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["name", "email"],
        }

        result = validator.validate_request(request, schema)

        assert not result.is_valid
        assert len(result.errors) == 1
        assert "email" in result.errors[0].field

    def test_validate_request_type_mismatch(self):
        """Test validating request with type mismatch."""
        validator = ContractValidator()

        request = {"count": "not a number"}
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
            },
        }

        result = validator.validate_request(request, schema)

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_string_format_email(self):
        """Test email format validation."""
        validator = ContractValidator()

        valid = validator._validate_email("test@example.com")
        assert valid.is_valid

        invalid = validator._validate_email("not-an-email")
        assert not invalid.is_valid

    def test_validate_string_format_uuid(self):
        """Test UUID format validation."""
        validator = ContractValidator()

        valid = validator._validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        assert valid.is_valid

        invalid = validator._validate_uuid("not-a-uuid")
        assert not invalid.is_valid

    def test_validate_number_constraints(self):
        """Test number constraint validation."""
        validator = ContractValidator()

        schema = {"type": "number", "minimum": 0, "maximum": 100}

        result = validator._validate_number_constraints(50, schema, "test")
        assert result.is_valid

        result = validator._validate_number_constraints(-1, schema, "test")
        assert not result.is_valid

        result = validator._validate_number_constraints(101, schema, "test")
        assert not result.is_valid

    def test_validate_response_status_code(self):
        """Test response status code validation."""
        validator = ContractValidator()

        result = validator.validate_response(
            {"id": 1},
            {"type": "object"},
            expected_status=200,
            actual_status=404,
        )

        assert not result.is_valid
        assert any("status" in e.field for e in result.errors)

    def test_validate_url_path(self):
        """Test URL path validation."""
        validator = ContractValidator()

        result = validator.validate_url_path(
            "/users/123",
            "/users/{id}",
        )
        assert result.is_valid

        result = validator.validate_url_path(
            "/products/abc",
            "/users/{id}",
        )
        assert not result.is_valid

    def test_validate_headers(self):
        """Test header validation."""
        validator = ContractValidator()

        headers = {"Authorization": "Bearer token123"}
        result = validator.validate_headers(headers, ["Authorization"])

        assert result.is_valid

        result = validator.validate_headers(headers, ["Authorization", "X-API-Key"])

        assert not result.is_valid

    def test_validation_result_merge(self):
        """Test merging validation results."""
        result1 = ValidationResult(is_valid=True)
        result2 = ValidationResult(is_valid=False)
        result2.add_error("field", "error message")

        result1.merge(result2)

        assert not result1.is_valid
        assert len(result1.errors) == 1

    def test_convenience_functions(self):
        """Test convenience validation functions."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        result = validate_request_contract({"name": "test"}, schema)
        assert isinstance(result, ValidationResult)

        result = validate_response_contract({"id": 1}, schema)
        assert isinstance(result, ValidationResult)


class TestIntegration:
    """Integration tests for AI Mocking system."""

    def test_end_to_end_analyze_and_generate(self, tmp_path):
        """Test end-to-end flow: analyze project and generate mocks."""
        # Create a project with external API calls
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        code_file = project_dir / "api_client.py"
        code_file.write_text(
            '''
import requests
import os

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

def create_customer(email):
    """Create a Stripe customer."""
    response = requests.post(
        "https://api.stripe.com/v1/customers",
        headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
        data={"email": email}
    )
    return response.json()

def geocode_address(address):
    """Geocode address using Google Maps."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": address, "key": api_key}
    )
    return response.json()
'''
        )

        # Create .env file
        env_file = project_dir / ".env"
        env_file.write_text(
            """
STRIPE_SECRET_KEY=sk_test_123
GOOGLE_MAPS_API_KEY=abc123
"""
        )

        # Step 1: Analyze
        from socialseed_e2e.ai_mocking import ExternalAPIAnalyzer

        analyzer = ExternalAPIAnalyzer(project_dir)
        detected_apis = analyzer.analyze_project()

        assert len(detected_apis) > 0

        # Step 2: Generate mocks
        from socialseed_e2e.ai_mocking import MockServerGenerator

        output_dir = tmp_path / "mocks"
        generator = MockServerGenerator(output_dir)

        for service_name in detected_apis.keys():
            try:
                server = generator.generate_mock_server(service_name, port=8000)
                generator.save_mock_server(server)
            except ValueError:
                pass  # Service might not be in registry

        # Verify mocks were created
        mock_files = list(output_dir.glob("mock_*.py"))
        assert len(mock_files) > 0 or len(detected_apis) == 0

    def test_mock_server_code_contains_expected_elements(self, tmp_path):
        """Test that generated mock server code contains expected elements."""
        from socialseed_e2e.ai_mocking import MockServerGenerator

        generator = MockServerGenerator(tmp_path)
        server = generator.generate_mock_server("stripe", port=8001)

        code = server.code

        # Should contain FastAPI imports
        assert "from fastapi import FastAPI" in code

        # Should contain service info
        assert "stripe" in code.lower()

        # Should contain auth verification
        assert "verify_auth" in code

        # Should contain utility endpoints
        assert "/__health" in code
        assert "/__reset" in code

    def test_contract_validation_with_real_schema(self):
        """Test contract validation with a realistic schema."""
        from socialseed_e2e.ai_mocking import ContractValidator

        validator = ContractValidator()

        # Stripe customer creation schema
        request_schema = {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                },
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["email"],
        }

        # Valid request
        valid_request = {"email": "test@example.com", "name": "Test User"}
        result = validator.validate_request(valid_request, request_schema)
        assert result.is_valid

        # Invalid request (missing required field)
        invalid_request = {"name": "Test User"}
        result = validator.validate_request(invalid_request, request_schema)
        assert not result.is_valid

        # Invalid request (wrong email format)
        invalid_email = {"email": "not-an-email"}
        result = validator.validate_request(invalid_email, request_schema)
        # Note: Email format validation might be a warning, not an error
        assert not result.is_valid or len(result.warnings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
