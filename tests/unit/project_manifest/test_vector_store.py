"""Unit tests for vector store."""

import pytest

from socialseed_e2e.project_manifest.models import (
    DtoField,
    DtoSchema,
    EndpointInfo,
    HttpMethod,
    ServiceInfo,
)


class TestManifestVectorStore:
    """Tests for ManifestVectorStore."""

    @pytest.fixture
    def sample_service(self):
        """Create a sample service for testing."""
        return ServiceInfo(
            name="users-api",
            language="python",
            framework="fastapi",
            root_path="/app",
            endpoints=[
                EndpointInfo(
                    name="get_user",
                    method=HttpMethod.GET,
                    path="/users/{id}",
                    full_path="/api/v1/users/{id}",
                    description="Get user by ID",
                    request_dto=None,
                    response_dto="UserResponse",
                    requires_auth=True,
                    tags=["users", "auth"],
                    file_path="/app/routes.py",
                ),
                EndpointInfo(
                    name="create_user",
                    method=HttpMethod.POST,
                    path="/users",
                    full_path="/api/v1/users",
                    description="Create a new user",
                    request_dto="UserRequest",
                    response_dto="UserResponse",
                    requires_auth=True,
                    auth_roles=["admin"],
                    tags=["users", "admin"],
                    file_path="/app/routes.py",
                ),
            ],
            dto_schemas=[
                DtoSchema(
                    name="UserRequest",
                    fields=[
                        DtoField(name="email", type="str", required=True),
                        DtoField(name="password", type="str", required=True),
                    ],
                    file_path="/app/schemas.py",
                ),
                DtoSchema(
                    name="UserResponse",
                    fields=[
                        DtoField(name="id", type="int", required=True),
                        DtoField(name="email", type="str", required=True),
                    ],
                    file_path="/app/schemas.py",
                ),
            ],
        )

    def test_create_text_representation_endpoint(self, sample_service):
        """Test text representation creation for endpoints."""
        pytest.importorskip("sentence_transformers")

        from socialseed_e2e.project_manifest.vector_store import ManifestVectorStore

        store = ManifestVectorStore("/tmp/test")
        endpoint = sample_service.endpoints[0]

        text = store._create_text_representation(endpoint, "endpoint", sample_service.name)

        assert "get_user" in text
        assert "GET" in text
        assert "/api/v1/users/{id}" in text
        assert "Get user by ID" in text
        assert "users-api" in text
        assert "UserResponse" in text
        assert "Requires Authentication: Yes" in text

    def test_create_text_representation_dto(self, sample_service):
        """Test text representation creation for DTOs."""
        pytest.importorskip("sentence_transformers")

        from socialseed_e2e.project_manifest.vector_store import ManifestVectorStore

        store = ManifestVectorStore("/tmp/test")
        dto = sample_service.dto_schemas[0]

        text = store._create_text_representation(dto, "dto", sample_service.name)

        assert "UserRequest" in text
        assert "email" in text
        assert "password" in text
        assert "users-api" in text

    def test_create_text_representation_service(self, sample_service):
        """Test text representation creation for services."""
        pytest.importorskip("sentence_transformers")

        from socialseed_e2e.project_manifest.vector_store import ManifestVectorStore

        store = ManifestVectorStore("/tmp/test")

        text = store._create_text_representation(sample_service, "service")

        assert "users-api" in text
        assert "python" in text
        assert "fastapi" in text
        assert "Endpoints: 2" in text
        assert "DTOs: 2" in text

    def test_search_result_dataclass(self):
        """Test SearchResult dataclass."""
        from socialseed_e2e.project_manifest.vector_store import SearchResult

        result = SearchResult(
            item_type="endpoint",
            item_id="users-api.GET./api/v1/users",
            item={"name": "test"},
            score=0.95,
            text="Test endpoint",
            service_name="users-api",
        )

        assert result.item_type == "endpoint"
        assert result.score == 0.95
        assert result.service_name == "users-api"


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        from socialseed_e2e.project_manifest.vector_store import SearchResult

        result = SearchResult(
            item_type="dto",
            item_id="users-api.UserRequest",
            item={"name": "UserRequest"},
            score=0.88,
            text="DTO: UserRequest",
            service_name="users-api",
        )

        assert result.item_type == "dto"
        assert result.item_id == "users-api.UserRequest"
        assert result.score == 0.88

    def test_search_result_without_service(self):
        """Test SearchResult without service name."""
        from socialseed_e2e.project_manifest.vector_store import SearchResult

        result = SearchResult(
            item_type="service",
            item_id="users-api",
            item={"name": "users-api"},
            score=0.92,
            text="Service: users-api",
            service_name=None,
        )

        assert result.service_name is None
