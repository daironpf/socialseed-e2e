"""Retrieval utility for RAG workflows.

This module provides high-level retrieval capabilities for AI agents,
allowing them to pull specific context from the project manifest
based on their current task.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from socialseed_e2e.project_manifest.models import DtoSchema, EndpointInfo
from socialseed_e2e.project_manifest.vector_store import (
    ManifestVectorStore,
    SearchResult,
)


@dataclass
class ContextChunk:
    """A chunk of context for RAG."""

    chunk_id: str
    chunk_type: str  # 'endpoint', 'dto', 'service', 'task_context'
    content: str
    metadata: Dict[str, Any]
    token_estimate: int


class RAGRetrievalEngine:
    """Retrieval engine for RAG workflows.

    This class provides intelligent retrieval of project context
    based on task descriptions, optimized for AI agent consumption.

    Example:
        >>> engine = RAGRetrievalEngine("/path/to/project")
        >>> context = engine.retrieve_for_task(
        ...     "create tests for user authentication",
        ...     max_chunks=5
        ... )
        >>> for chunk in context:
        ...     print(f"{chunk.chunk_type}: {chunk.token_estimate} tokens")
    """

    def __init__(
        self,
        project_root: Union[str, Path],
        embedding_model: Optional[str] = None,
    ):
        """Initialize the retrieval engine.

        Args:
            project_root: Root directory of the project
            embedding_model: Name of the embedding model to use
        """
        self.project_root = Path(project_root).resolve()
        self.vector_store = ManifestVectorStore(
            self.project_root, embedding_model=embedding_model
        )

        # Ensure index exists
        if not self.vector_store.is_index_valid():
            self.vector_store.build_index()

    def retrieve_for_task(
        self,
        task_description: str,
        max_chunks: int = 5,
        chunk_size: str = "medium",  # 'small', 'medium', 'large'
        include_dependencies: bool = True,
    ) -> List[ContextChunk]:
        """Retrieve relevant context chunks for a task.

        Args:
            task_description: Description of what the AI agent needs to do
            max_chunks: Maximum number of chunks to return
            chunk_size: Size of chunks ('small' ~512 tokens, 'medium' ~1024, 'large' ~2048)
            include_dependencies: Whether to include related DTOs and dependencies

        Returns:
            List of ContextChunk objects
        """
        # Search for relevant items
        results = self.vector_store.search(task_description, top_k=max_chunks * 2)

        # Build chunks
        chunks = []
        token_limits = {
            "small": 512,
            "medium": 1024,
            "large": 2048,
        }
        max_tokens = token_limits.get(chunk_size, 1024)

        for result in results:
            if len(chunks) >= max_chunks:
                break

            chunk = self._create_chunk_from_result(
                result, max_tokens, include_dependencies
            )
            if chunk:
                chunks.append(chunk)

        return chunks

    def _create_chunk_from_result(
        self,
        result: SearchResult,
        max_tokens: int,
        include_dependencies: bool,
    ) -> Optional[ContextChunk]:
        """Create a context chunk from a search result."""
        # Estimate tokens
        token_estimate = len(result.text) // 4

        if token_estimate > max_tokens:
            # Truncate if too long
            text = result.text[: max_tokens * 4]
            token_estimate = max_tokens
        else:
            text = result.text

        # Build metadata
        metadata = {
            "search_score": result.score,
            "item_type": result.item_type,
            "service_name": result.service_name,
        }

        # Add type-specific metadata
        if result.item_type == "endpoint":
            endpoint = result.item
            if isinstance(endpoint, EndpointInfo):
                metadata["method"] = str(endpoint.method)
                metadata["path"] = endpoint.full_path
                metadata["requires_auth"] = endpoint.requires_auth

                # Include related DTOs if requested
                if include_dependencies:
                    related_text = self._get_related_dto_text(endpoint)
                    if related_text:
                        text += "\n\n" + related_text
                        token_estimate = len(text) // 4

        elif result.item_type == "dto":
            dto = result.item
            if isinstance(dto, DtoSchema):
                metadata["field_count"] = len(dto.fields)
                metadata["base_classes"] = dto.base_classes

        # Generate chunk ID
        chunk_id = hashlib.md5(
            f"{result.item_type}:{result.item_id}:{text[:100]}".encode()
        ).hexdigest()[:12]

        return ContextChunk(
            chunk_id=chunk_id,
            chunk_type=result.item_type,
            content=text,
            metadata=metadata,
            token_estimate=token_estimate,
        )

    def _get_related_dto_text(self, endpoint: EndpointInfo) -> str:
        """Get text for DTOs related to an endpoint."""
        related_parts = ["Related Data Structures:"]

        if endpoint.request_dto:
            # Search for the request DTO
            dto_results = self.vector_store.search(
                f"DTO {endpoint.request_dto}",
                top_k=1,
                item_type="dto",
            )
            if dto_results:
                related_parts.append(f"\nRequest DTO:\n{dto_results[0].text}")

        if endpoint.response_dto:
            # Search for the response DTO
            dto_results = self.vector_store.search(
                f"DTO {endpoint.response_dto}",
                top_k=1,
                item_type="dto",
            )
            if dto_results:
                related_parts.append(f"\nResponse DTO:\n{dto_results[0].text}")

        return "\n".join(related_parts) if len(related_parts) > 1 else ""

    def get_endpoint_context(
        self,
        endpoint_path: str,
        method: Optional[str] = None,
    ) -> Optional[ContextChunk]:
        """Get context for a specific endpoint.

        Args:
            endpoint_path: Path of the endpoint (e.g., "/api/users")
            method: HTTP method (optional)

        Returns:
            ContextChunk with endpoint details or None
        """
        # Search for the endpoint
        query = f"{method or ''} {endpoint_path}".strip()
        results = self.vector_store.search(query, top_k=5, item_type="endpoint")

        for result in results:
            if isinstance(result.item, EndpointInfo):
                if result.item.full_path == endpoint_path:
                    if method is None or str(result.item.method) == method.upper():
                        return self._create_chunk_from_result(
                            result, max_tokens=2048, include_dependencies=True
                        )

        return None

    def get_dto_context(self, dto_name: str) -> Optional[ContextChunk]:
        """Get context for a specific DTO.

        Args:
            dto_name: Name of the DTO

        Returns:
            ContextChunk with DTO details or None
        """
        results = self.vector_store.search(f"DTO {dto_name}", top_k=5, item_type="dto")

        for result in results:
            if isinstance(result.item, DtoSchema):
                if result.item.name == dto_name:
                    return self._create_chunk_from_result(
                        result, max_tokens=1024, include_dependencies=False
                    )

        return None

    def refresh_index(self) -> None:
        """Refresh the vector index from the current manifest."""
        self.vector_store.invalidate_index()
        self.vector_store.build_index()

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about the retrieval engine.

        Returns:
            Dictionary with retrieval statistics
        """
        return {
            "index_valid": self.vector_store.is_index_valid(),
            "embedding_model": self.vector_store.embedding_model_name,
            "index_location": str(self.vector_store.index_dir),
        }


class TaskContextBuilder:
    """Builds context for specific testing tasks.

    This class helps AI agents build the right context for different
    types of testing tasks.
    """

    def __init__(self, retrieval_engine: RAGRetrievalEngine):
        """Initialize the context builder.

        Args:
            retrieval_engine: Initialized retrieval engine
        """
        self.engine = retrieval_engine

    def build_test_context(
        self,
        test_type: str,  # 'unit', 'integration', 'e2e', 'contract'
        target: str,  # e.g., 'user authentication', 'payment flow'
        include_setup: bool = True,
    ) -> Dict[str, Any]:
        """Build context for creating tests.

        Args:
            test_type: Type of tests to create
            target: What is being tested
            include_setup: Whether to include setup/teardown context

        Returns:
            Dictionary with test context
        """
        # Create task description
        task = f"Create {test_type} tests for {target}"

        # Retrieve relevant context
        chunks = self.engine.retrieve_for_task(
            task,
            max_chunks=5,
            chunk_size="medium",
            include_dependencies=True,
        )

        context = {
            "task": task,
            "test_type": test_type,
            "target": target,
            "chunks": [],
            "total_tokens": 0,
        }

        for chunk in chunks:
            context["chunks"].append(
                {
                    "id": chunk.chunk_id,
                    "type": chunk.chunk_type,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "tokens": chunk.token_estimate,
                }
            )
            context["total_tokens"] += chunk.token_estimate

        # Add setup context if requested
        if include_setup:
            setup_chunks = self.engine.retrieve_for_task(
                "authentication setup test configuration",
                max_chunks=2,
                chunk_size="small",
            )
            if setup_chunks:
                context["setup_context"] = [
                    {
                        "id": c.chunk_id,
                        "type": c.chunk_type,
                        "content": c.content,
                        "tokens": c.token_estimate,
                    }
                    for c in setup_chunks
                ]

        return context

    def build_endpoint_test_context(
        self,
        endpoint_path: str,
        method: str,
    ) -> Dict[str, Any]:
        """Build context for testing a specific endpoint.

        Args:
            endpoint_path: Path of the endpoint
            method: HTTP method

        Returns:
            Dictionary with endpoint test context
        """
        # Get endpoint context
        chunk = self.engine.get_endpoint_context(endpoint_path, method)

        if not chunk:
            return {
                "error": f"Endpoint {method} {endpoint_path} not found",
                "context": None,
            }

        context = {
            "endpoint": f"{method} {endpoint_path}",
            "endpoint_chunk": {
                "id": chunk.chunk_id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "tokens": chunk.token_estimate,
            },
            "related_chunks": [],
        }

        # Find related endpoints (similar functionality)
        related = self.engine.vector_store.search(
            chunk.content,
            top_k=3,
            item_type="endpoint",
        )

        for result in related:
            if isinstance(result.item, EndpointInfo):
                if not (
                    result.item.full_path == endpoint_path
                    and str(result.item.method) == method.upper()
                ):
                    related_chunk = self.engine._create_chunk_from_result(
                        result, max_tokens=1024, include_dependencies=False
                    )
                    if related_chunk:
                        context["related_chunks"].append(
                            {
                                "id": related_chunk.chunk_id,
                                "endpoint": f"{result.item.method} {result.item.full_path}",
                                "content": related_chunk.content[:500] + "...",
                                "tokens": related_chunk.token_estimate,
                            }
                        )

        return context
