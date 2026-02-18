"""Unit tests for retrieval engine."""

import pytest

from socialseed_e2e.project_manifest.models import (
    DtoField,
    DtoSchema,
    EndpointInfo,
    HttpMethod,
)
from socialseed_e2e.project_manifest.retrieval import (
    ContextChunk,
    RAGRetrievalEngine,
    TaskContextBuilder,
)


class TestContextChunk:
    """Tests for ContextChunk dataclass."""

    def test_context_chunk_creation(self):
        """Test creating a ContextChunk."""
        chunk = ContextChunk(
            chunk_id="abc123",
            chunk_type="endpoint",
            content="Test endpoint content",
            metadata={"score": 0.95},
            token_estimate=100,
        )

        assert chunk.chunk_id == "abc123"
        assert chunk.chunk_type == "endpoint"
        assert chunk.content == "Test endpoint content"
        assert chunk.token_estimate == 100


class TestRAGRetrievalEngine:
    """Tests for RAGRetrievalEngine."""

    def test_engine_initialization(self, tmp_path):
        """Test engine initialization."""
        pytest.importorskip("sentence_transformers")

        engine = RAGRetrievalEngine(tmp_path)
        assert engine.project_root == tmp_path

    def test_get_retrieval_stats(self, tmp_path):
        """Test getting retrieval stats."""
        pytest.importorskip("sentence_transformers")

        engine = RAGRetrievalEngine(tmp_path)
        stats = engine.get_retrieval_stats()

        assert "index_valid" in stats
        assert "embedding_model" in stats
        assert "index_location" in stats


class TestTaskContextBuilder:
    """Tests for TaskContextBuilder."""

    def test_builder_creation(self, tmp_path):
        """Test creating a TaskContextBuilder."""
        pytest.importorskip("sentence_transformers")

        engine = RAGRetrievalEngine(tmp_path)
        builder = TaskContextBuilder(engine)

        assert builder.engine == engine

    def test_build_endpoint_test_context_not_found(self, tmp_path):
        """Test building context for non-existent endpoint."""
        pytest.importorskip("sentence_transformers")

        engine = RAGRetrievalEngine(tmp_path)
        builder = TaskContextBuilder(engine)

        # Should return error for non-existent endpoint
        context = builder.build_endpoint_test_context("/nonexistent", "GET")

        assert "error" in context
        assert "not found" in context["error"].lower()


class TestContextChunkTypes:
    """Tests for different context chunk types."""

    def test_endpoint_chunk(self):
        """Test endpoint chunk creation."""
        endpoint = EndpointInfo(
            name="create_user",
            method=HttpMethod.POST,
            path="/users",
            full_path="/api/v1/users",
            description="Create a new user",
            request_dto="UserRequest",
            response_dto="UserResponse",
            requires_auth=True,
            auth_roles=["admin"],
            tags=["users"],
            file_path="/app/routes.py",
        )

        chunk = ContextChunk(
            chunk_id="endpoint_123",
            chunk_type="endpoint",
            content=f"Endpoint: {endpoint.name}\nMethod: {endpoint.method}\nPath: {endpoint.full_path}",
            metadata={
                "method": endpoint.method.value,
                "path": endpoint.full_path,
                "requires_auth": endpoint.requires_auth,
            },
            token_estimate=150,
        )

        assert chunk.chunk_type == "endpoint"
        assert chunk.metadata["requires_auth"] is True
        assert chunk.metadata["method"] == "POST"

    def test_dto_chunk(self):
        """Test DTO chunk creation."""
        dto = DtoSchema(
            name="UserRequest",
            fields=[
                DtoField(name="email", type="str", required=True),
                DtoField(name="password", type="str", required=True),
            ],
            file_path="/app/schemas.py",
            base_classes=["BaseModel"],
        )

        chunk = ContextChunk(
            chunk_id="dto_123",
            chunk_type="dto",
            content=f"DTO: {dto.name}\nFields: {', '.join(f.name for f in dto.fields)}",
            metadata={
                "field_count": 2,
                "base_classes": ["BaseModel"],
            },
            token_estimate=80,
        )

        assert chunk.chunk_type == "dto"
        assert chunk.metadata["field_count"] == 2
        assert "BaseModel" in chunk.metadata["base_classes"]
