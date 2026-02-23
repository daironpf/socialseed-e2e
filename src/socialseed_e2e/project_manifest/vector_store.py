"""Vector store for semantic search on Project Manifest.

This module provides vector embeddings and similarity search capabilities
for the project manifest, enabling RAG (Retrieval-Augmented Generation) workflows.
"""

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from socialseed_e2e.project_manifest.models import (
    DtoSchema,
    EndpointInfo,
    ProjectKnowledge,
    ServiceInfo,
)


@dataclass
class SearchResult:
    """Result from a semantic search."""

    item_type: str  # 'endpoint', 'dto', 'service'
    item_id: str  # Unique identifier
    item: Union[EndpointInfo, DtoSchema, ServiceInfo, Dict[str, Any]]
    score: float  # Similarity score (0-1)
    text: str  # Text that was embedded
    service_name: Optional[str] = None


class ManifestVectorStore:
    """Vector store for semantic search on project manifest.

    This class creates and manages vector embeddings for endpoints, DTOs,
    and services in the project manifest, enabling semantic search capabilities
    for RAG workflows.

    Example:
        >>> store = ManifestVectorStore(project_path)
        >>> store.build_index()  # Create embeddings
        >>> results = store.search("authentication endpoints", top_k=5)
        >>> for result in results:
        ...     print(f"{result.item_id}: {result.score}")
    """

    INDEX_FILENAME = "manifest_index.pkl"
    EMBEDDINGS_FILENAME = "manifest_embeddings.npy"
    METADATA_FILENAME = "manifest_index_metadata.json"

    def __init__(
        self,
        project_root: Union[str, Path],
        embedding_model: Optional[str] = None,
        index_dir: Optional[Path] = None,
    ):
        """Initialize the vector store.

        Args:
            project_root: Root directory of the project
            embedding_model: Name of the sentence-transformers model to use
            index_dir: Directory to store index files (default: project_root/.e2e)
        """
        self.project_root = Path(project_root).resolve()
        self.index_dir = index_dir or (self.project_root / ".e2e")
        self.embedding_model_name = embedding_model or "all-MiniLM-L6-v2"

        # Index files
        self.index_path = self.index_dir / self.INDEX_FILENAME
        self.embeddings_path = self.index_dir / self.EMBEDDINGS_FILENAME
        self.metadata_path = self.index_dir / self.METADATA_FILENAME

        # Internal state
        self._embeddings: Optional[Any] = None
        self._metadata: List[Dict[str, Any]] = []
        self._model: Optional[Any] = None
        self._manifest: Optional[ProjectKnowledge] = None

        # Ensure index directory exists
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def _get_embedding_model(self):
        """Get or load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.embedding_model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embeddings. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def _create_text_representation(
        self,
        item: Union[EndpointInfo, DtoSchema, ServiceInfo],
        item_type: str,
        service_name: Optional[str] = None,
    ) -> str:
        """Create a text representation of an item for embedding.

        Args:
            item: The item to convert to text
            item_type: Type of item ('endpoint', 'dto', 'service')
            service_name: Name of the service (for endpoints and DTOs)

        Returns:
            Text representation suitable for embedding
        """
        parts = []

        if item_type == "endpoint":
            endpoint = item
            parts.append(f"Endpoint: {endpoint.name}")
            parts.append(f"Method: {endpoint.method}")
            parts.append(f"Path: {endpoint.full_path}")
            if endpoint.description:
                parts.append(f"Description: {endpoint.description}")
            if endpoint.request_dto:
                parts.append(f"Request DTO: {endpoint.request_dto}")
            if endpoint.response_dto:
                parts.append(f"Response DTO: {endpoint.response_dto}")
            if endpoint.tags:
                parts.append(f"Tags: {', '.join(endpoint.tags)}")
            if endpoint.requires_auth:
                parts.append("Requires Authentication: Yes")
            if endpoint.auth_roles:
                parts.append(f"Required Roles: {', '.join(endpoint.auth_roles)}")
            if service_name:
                parts.append(f"Service: {service_name}")

        elif item_type == "dto":
            dto = item
            parts.append(f"DTO: {dto.name}")
            if dto.description:
                parts.append(f"Description: {dto.description}")
            if dto.fields:
                field_descs = []
                for field in dto.fields:
                    field_desc = f"{field.name} ({field.type})"
                    if field.required:
                        field_desc += " [required]"
                    if field.description:
                        field_desc += f" - {field.description}"
                    field_descs.append(field_desc)
                parts.append(f"Fields: {'; '.join(field_descs)}")
            if dto.base_classes:
                parts.append(f"Base Classes: {', '.join(dto.base_classes)}")
            if service_name:
                parts.append(f"Service: {service_name}")

        elif item_type == "service":
            service = item
            parts.append(f"Service: {service.name}")
            parts.append(f"Language: {service.language}")
            if service.framework:
                parts.append(f"Framework: {service.framework}")
            if service.endpoints:
                parts.append(f"Endpoints: {len(service.endpoints)}")
            if service.dto_schemas:
                parts.append(f"DTOs: {len(service.dto_schemas)}")

        return "\n".join(parts)

    def build_index(self, manifest: Optional[ProjectKnowledge] = None) -> None:
        """Build the vector index from the manifest.

        Args:
            manifest: Optional manifest to index. If None, loads from project.
        """
        if manifest is None:
            from socialseed_e2e.project_manifest.api import ManifestAPI

            api = ManifestAPI(self.project_root)
            manifest = api.manifest

        self._manifest = manifest

        # Collect all items to index
        texts = []
        metadata = []

        for service in manifest.services:
            # Index service
            service_text = self._create_text_representation(service, "service")
            texts.append(service_text)
            metadata.append(
                {
                    "type": "service",
                    "id": service.name,
                    "service_name": service.name,
                    "text": service_text,
                }
            )

            # Index endpoints
            for endpoint in service.endpoints:
                endpoint_text = self._create_text_representation(
                    endpoint, "endpoint", service.name
                )
                texts.append(endpoint_text)
                metadata.append(
                    {
                        "type": "endpoint",
                        "id": f"{service.name}.{endpoint.method}.{endpoint.full_path}",
                        "service_name": service.name,
                        "text": endpoint_text,
                        "endpoint_name": endpoint.name,
                        "method": str(endpoint.method),
                        "path": endpoint.full_path,
                    }
                )

            # Index DTOs
            for dto in service.dto_schemas:
                dto_text = self._create_text_representation(dto, "dto", service.name)
                texts.append(dto_text)
                metadata.append(
                    {
                        "type": "dto",
                        "id": f"{service.name}.{dto.name}",
                        "service_name": service.name,
                        "text": dto_text,
                        "dto_name": dto.name,
                    }
                )

        # Generate embeddings
        model = self._get_embedding_model()
        embeddings = model.encode(texts, show_progress_bar=True)

        # Store
        self._embeddings = np.array(embeddings)
        self._metadata = metadata

        # Save to disk
        self._save_index()

    def _save_index(self) -> None:
        """Save the index to disk."""
        if self._embeddings is None or not self._metadata:
            raise ValueError("No index to save. Call build_index() first.")

        # Save embeddings
        np.save(self.embeddings_path, self._embeddings)

        # Save metadata
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2)

        # Save index info
        index_info = {
            "embedding_model": self.embedding_model_name,
            "num_items": len(self._metadata),
            "item_types": list({m["type"] for m in self._metadata}),
        }
        with open(self.index_path, "wb") as f:
            pickle.dump(index_info, f)

    def load_index(self) -> bool:
        """Load the index from disk.

        Returns:
            True if index was loaded successfully, False otherwise
        """
        if not all(
            p.exists()
            for p in [self.index_path, self.embeddings_path, self.metadata_path]
        ):
            return False

        try:
            # Load embeddings
            self._embeddings = np.load(self.embeddings_path)

            # Load metadata
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

            return True
        except Exception:
            return False

    def search(
        self,
        query: str,
        top_k: int = 5,
        item_type: Optional[str] = None,
        service_name: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        """Search for items semantically similar to the query.

        Args:
            query: Search query text
            top_k: Number of results to return
            item_type: Filter by item type ('endpoint', 'dto', 'service')
            service_name: Filter by service name
            min_score: Minimum similarity score (0-1)

        Returns:
            List of SearchResult objects sorted by relevance
        """
        if self._embeddings is None:
            if not self.load_index():
                raise ValueError("No index loaded. Call build_index() first.")

        # Generate query embedding
        model = self._get_embedding_model()
        query_embedding = model.encode([query])[0]

        # Compute similarities
        similarities = np.dot(self._embeddings, query_embedding) / (
            np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Filter and sort results
        results = []
        for idx, score in enumerate(similarities):
            if score < min_score:
                continue

            meta = self._metadata[idx]

            # Apply filters
            if item_type and meta["type"] != item_type:
                continue
            if service_name and meta.get("service_name") != service_name:
                continue

            results.append((idx, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        # Take top_k
        results = results[:top_k]

        # Build SearchResult objects
        search_results = []
        for idx, score in results:
            meta = self._metadata[idx]
            search_results.append(
                SearchResult(
                    item_type=meta["type"],
                    item_id=meta["id"],
                    item=self._get_item_by_id(meta["id"], meta["type"]),
                    score=float(score),
                    text=meta["text"],
                    service_name=meta.get("service_name"),
                )
            )

        return search_results

    def _get_item_by_id(
        self, item_id: str, item_type: str
    ) -> Union[EndpointInfo, DtoSchema, ServiceInfo, Dict[str, Any]]:
        """Get an item by its ID."""
        if self._manifest is None:
            from socialseed_e2e.project_manifest.api import ManifestAPI

            api = ManifestAPI(self.project_root)
            self._manifest = api.manifest

        # Parse ID
        if item_type == "service":
            for service in self._manifest.services:
                if service.name == item_id:
                    return service
        elif item_type == "endpoint":
            # Format: service_name.METHOD.path
            parts = item_id.split(".", 2)
            if len(parts) >= 3:
                service_name = parts[0]
                method = parts[1]
                path = parts[2]
                for service in self._manifest.services:
                    if service.name == service_name:
                        for endpoint in service.endpoints:
                            if (
                                str(endpoint.method) == method
                                and endpoint.full_path == path
                            ):
                                return endpoint
        elif item_type == "dto":
            # Format: service_name.dto_name
            parts = item_id.split(".", 1)
            if len(parts) == 2:
                service_name, dto_name = parts
                for service in self._manifest.services:
                    if service.name == service_name:
                        for dto in service.dto_schemas:
                            if dto.name == dto_name:
                                return dto

        return {"id": item_id, "type": item_type}

    def get_context_for_task(
        self,
        task_description: str,
        max_tokens: int = 2000,
        include_related: bool = True,
    ) -> Dict[str, Any]:
        """Get relevant context for a specific task.

        This method retrieves the most relevant endpoints, DTOs, and services
        for a given task description, formatted for AI consumption.

        Args:
            task_description: Description of the task (e.g., "create user authentication tests")
            max_tokens: Approximate maximum tokens to return
            include_related: Whether to include related items (e.g., DTOs for endpoints)

        Returns:
            Dictionary with relevant context
        """
        # Search for relevant items
        results = self.search(task_description, top_k=10)

        context = {
            "task": task_description,
            "relevant_endpoints": [],
            "relevant_dtos": [],
            "relevant_services": [],
            "search_results": [],
        }

        # Estimate tokens (rough approximation: 4 chars per token)
        current_tokens = 0
        max_chars = max_tokens * 4

        for result in results:
            item_tokens = len(result.text) // 4

            if current_tokens + item_tokens > max_chars:
                break

            current_tokens += item_tokens

            # Add to appropriate list
            if result.item_type == "endpoint":
                endpoint_data = {
                    "name": result.item_id,
                    "score": result.score,
                    "text": result.text,
                }
                context["relevant_endpoints"].append(endpoint_data)

                # Include related DTOs if requested
                if include_related and hasattr(result.item, "request_dto"):
                    # Find and add the request DTO
                    if result.item.request_dto:
                        dto_results = self.search(
                            f"{result.service_name} {result.item.request_dto}",
                            top_k=1,
                            item_type="dto",
                        )
                        if dto_results:
                            context["relevant_dtos"].append(
                                {
                                    "name": dto_results[0].item_id,
                                    "score": dto_results[0].score,
                                    "text": dto_results[0].text,
                                }
                            )

            elif result.item_type == "dto":
                context["relevant_dtos"].append(
                    {
                        "name": result.item_id,
                        "score": result.score,
                        "text": result.text,
                    }
                )
            elif result.item_type == "service":
                context["relevant_services"].append(
                    {
                        "name": result.item_id,
                        "score": result.score,
                        "text": result.text,
                    }
                )

            context["search_results"].append(
                {
                    "id": result.item_id,
                    "type": result.item_type,
                    "score": result.score,
                }
            )

        return context

    def invalidate_index(self) -> None:
        """Invalidate the current index (e.g., when manifest changes)."""
        # Remove index files
        for path in [self.index_path, self.embeddings_path, self.metadata_path]:
            if path.exists():
                path.unlink()

        self._embeddings = None
        self._metadata = []

    def is_index_valid(self) -> bool:
        """Check if the current index is valid (exists and up-to-date).

        Returns:
            True if index exists and is up-to-date with manifest
        """
        if not all(
            p.exists()
            for p in [self.index_path, self.embeddings_path, self.metadata_path]
        ):
            return False

        # Check if manifest is newer than index
        manifest_path = self.project_root / "project_knowledge.json"
        if manifest_path.exists():
            manifest_mtime = manifest_path.stat().st_mtime
            index_mtime = self.index_path.stat().st_mtime
            if manifest_mtime > index_mtime:
                return False

        return True
