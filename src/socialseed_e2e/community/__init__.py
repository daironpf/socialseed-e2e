"""Community Hub and Test Marketplace for SocialSeed-E2E.

This module provides a platform for the community to share tests,
plugins, templates, and best practices.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


class ResourceType(str, Enum):
    """Types of community resources."""

    TEST_TEMPLATE = "test_template"
    PLUGIN = "plugin"
    BEST_PRACTICE = "best_practice"
    CASE_STUDY = "case_study"
    UTILITY = "utility"


class ResourceStatus(str, Enum):
    """Status of a community resource."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


@dataclass
class CommunityResource:
    """A community-contributed resource."""

    id: str
    name: str
    description: str
    resource_type: ResourceType
    author: str
    version: str
    tags: List[str] = field(default_factory=list)
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    status: ResourceStatus = ResourceStatus.PENDING_REVIEW
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    file_path: Optional[Path] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resource_type": self.resource_type.value,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "downloads": self.downloads,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "file_path": str(self.file_path) if self.file_path else None,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommunityResource":
        """Create resource from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            resource_type=ResourceType(data["resource_type"]),
            author=data["author"],
            version=data["version"],
            tags=data.get("tags", []),
            downloads=data.get("downloads", 0),
            rating=data.get("rating", 0.0),
            rating_count=data.get("rating_count", 0),
            status=ResourceStatus(data.get("status", "pending_review")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            file_path=Path(data["file_path"]) if data.get("file_path") else None,
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TestTemplate(CommunityResource):
    """A test template for the marketplace."""

    resource_type: ResourceType = field(default=ResourceType.TEST_TEMPLATE, init=False)
    framework: str = ""
    language: str = "python"
    test_count: int = 0
    example_usage: str = ""


@dataclass
class PluginResource(CommunityResource):
    """A plugin for the repository."""

    resource_type: ResourceType = field(default=ResourceType.PLUGIN, init=False)
    entry_point: str = ""
    hooks: List[str] = field(default_factory=list)
    compatible_versions: List[str] = field(default_factory=list)


class CommunityHub:
    """Main community hub for managing resources."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the community hub.

        Args:
            storage_path: Path to store community resources
        """
        self.storage_path = storage_path or Path(".e2e/community")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.resources_file = self.storage_path / "resources.json"
        self.index_file = self.storage_path / "index.json"

        self.resources: Dict[str, CommunityResource] = {}
        self._load_resources()

    def _load_resources(self) -> None:
        """Load resources from storage."""
        if self.resources_file.exists():
            try:
                with open(self.resources_file, "r") as f:
                    data = json.load(f)
                    for item in data:
                        resource = CommunityResource.from_dict(item)
                        self.resources[resource.id] = resource
            except Exception:
                pass

    def _save_resources(self) -> None:
        """Save resources to storage."""
        data = [resource.to_dict() for resource in self.resources.values()]
        with open(self.resources_file, "w") as f:
            json.dump(data, f, indent=2)

    def publish_resource(self, resource: CommunityResource) -> bool:
        """Publish a new resource to the marketplace.

        Args:
            resource: Resource to publish

        Returns:
            True if published successfully
        """
        if resource.id in self.resources:
            return False

        self.resources[resource.id] = resource
        self._save_resources()
        return True

    def update_resource(self, resource_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing resource.

        Args:
            resource_id: ID of resource to update
            updates: Dictionary of updates

        Returns:
            True if updated successfully
        """
        if resource_id not in self.resources:
            return False

        resource = self.resources[resource_id]

        for key, value in updates.items():
            if hasattr(resource, key):
                setattr(resource, key, value)

        resource.updated_at = datetime.utcnow()
        self._save_resources()
        return True

    def get_resource(self, resource_id: str) -> Optional[CommunityResource]:
        """Get a resource by ID.

        Args:
            resource_id: Resource ID

        Returns:
            Resource or None
        """
        return self.resources.get(resource_id)

    def search_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        query: Optional[str] = None,
        status: Optional[ResourceStatus] = None,
    ) -> List[CommunityResource]:
        """Search for resources.

        Args:
            resource_type: Filter by type
            tags: Filter by tags
            author: Filter by author
            query: Search query
            status: Filter by status

        Returns:
            List of matching resources
        """
        results = list(self.resources.values())

        if resource_type:
            results = [r for r in results if r.resource_type == resource_type]

        if tags:
            results = [r for r in results if any(tag in r.tags for tag in tags)]

        if author:
            results = [r for r in results if r.author.lower() == author.lower()]

        if query:
            query_lower = query.lower()
            results = [
                r
                for r in results
                if query_lower in r.name.lower()
                or query_lower in r.description.lower()
                or any(query_lower in tag.lower() for tag in r.tags)
            ]

        if status:
            results = [r for r in results if r.status == status]
        else:
            # Default to approved resources
            results = [r for r in results if r.status == ResourceStatus.APPROVED]

        # Sort by rating and downloads
        results.sort(key=lambda r: (r.rating, r.downloads), reverse=True)

        return results

    def download_resource(self, resource_id: str) -> Optional[Path]:
        """Download a resource.

        Args:
            resource_id: Resource ID

        Returns:
            Path to downloaded file or None
        """
        resource = self.resources.get(resource_id)
        if not resource or resource.status != ResourceStatus.APPROVED:
            return None

        # Increment download count
        resource.downloads += 1
        self._save_resources()

        return resource.file_path

    def rate_resource(self, resource_id: str, rating: float) -> bool:
        """Rate a resource.

        Args:
            resource_id: Resource ID
            rating: Rating from 0.0 to 5.0

        Returns:
            True if rated successfully
        """
        if resource_id not in self.resources:
            return False

        resource = self.resources[resource_id]

        # Update rating (simple average)
        total_rating = resource.rating * resource.rating_count + rating
        resource.rating_count += 1
        resource.rating = total_rating / resource.rating_count

        self._save_resources()
        return True

    def get_popular_resources(self, limit: int = 10) -> List[CommunityResource]:
        """Get most popular resources.

        Args:
            limit: Maximum number to return

        Returns:
            List of popular resources
        """
        approved = [
            r for r in self.resources.values() if r.status == ResourceStatus.APPROVED
        ]
        approved.sort(key=lambda r: r.downloads, reverse=True)
        return approved[:limit]

    def get_top_rated(self, limit: int = 10) -> List[CommunityResource]:
        """Get top rated resources.

        Args:
            limit: Maximum number to return

        Returns:
            List of top rated resources
        """
        approved = [
            r for r in self.resources.values() if r.status == ResourceStatus.APPROVED
        ]
        approved.sort(key=lambda r: r.rating, reverse=True)
        return approved[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get marketplace statistics.

        Returns:
            Statistics dictionary
        """
        total_resources = len(self.resources)
        approved_resources = len(
            [r for r in self.resources.values() if r.status == ResourceStatus.APPROVED]
        )

        type_counts = {}
        for resource_type in ResourceType:
            count = len(
                [r for r in self.resources.values() if r.resource_type == resource_type]
            )
            type_counts[resource_type.value] = count

        total_downloads = sum(r.downloads for r in self.resources.values())

        return {
            "total_resources": total_resources,
            "approved_resources": approved_resources,
            "pending_review": total_resources - approved_resources,
            "total_downloads": total_downloads,
            "by_type": type_counts,
        }
