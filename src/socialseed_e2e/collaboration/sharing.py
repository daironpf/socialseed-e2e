"""
Test sharing and reusability module.
Manages test packages, metadata, and repository operations.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TestMetadata(BaseModel):
    """Metadata for a shared test."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    category: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TestPackage(BaseModel):
    """A packaged test with metadata and content."""

    metadata: TestMetadata
    test_content: str  # The actual test code
    fixtures: Dict[str, str] = Field(default_factory=dict)  # fixture_name -> content
    documentation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        metadata_dict = self.metadata.model_dump()
        # Convert datetime objects to ISO format strings
        if isinstance(metadata_dict.get("created_at"), datetime):
            metadata_dict["created_at"] = metadata_dict["created_at"].isoformat()
        if isinstance(metadata_dict.get("updated_at"), datetime):
            metadata_dict["updated_at"] = metadata_dict["updated_at"].isoformat()

        return {
            "metadata": metadata_dict,
            "test_content": self.test_content,
            "fixtures": self.fixtures,
            "documentation": self.documentation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestPackage":
        """Create from dictionary."""
        metadata_dict = data["metadata"]
        # Parse datetime strings back to datetime objects
        if isinstance(metadata_dict.get("created_at"), str):
            metadata_dict["created_at"] = datetime.fromisoformat(metadata_dict["created_at"])
        if isinstance(metadata_dict.get("updated_at"), str):
            metadata_dict["updated_at"] = datetime.fromisoformat(metadata_dict["updated_at"])

        return cls(
            metadata=TestMetadata(**metadata_dict),
            test_content=data["test_content"],
            fixtures=data.get("fixtures", {}),
            documentation=data.get("documentation", "")
        )


class TestRepository:
    """
    Manages a repository of shared tests.
    Supports local file-based storage with versioning.
    """

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.repo_path / "index.json"
        self._load_index()

    def _load_index(self):
        """Load the repository index."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {"tests": {}}

    def _save_index(self):
        """Save the repository index."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def publish(self, package: TestPackage) -> str:
        """
        Publish a test package to the repository.
        Returns the package ID.
        """
        package_id = f"{package.metadata.name}@{package.metadata.version}"
        package_dir = self.repo_path / package.metadata.name / package.metadata.version
        package_dir.mkdir(parents=True, exist_ok=True)

        # Save package content
        package_file = package_dir / "package.json"
        with open(package_file, 'w') as f:
            json.dump(package.to_dict(), f, indent=2)

        # Update index
        if package.metadata.name not in self.index["tests"]:
            self.index["tests"][package.metadata.name] = []

        version_info = {
            "version": package.metadata.version,
            "author": package.metadata.author,
            "created_at": package.metadata.created_at.isoformat(),
            "tags": package.metadata.tags,
            "category": package.metadata.category
        }

        # Remove old version if exists
        self.index["tests"][package.metadata.name] = [
            v for v in self.index["tests"][package.metadata.name]
            if v["version"] != package.metadata.version
        ]
        self.index["tests"][package.metadata.name].append(version_info)

        self._save_index()
        logger.info(f"Published test package: {package_id}")
        return package_id

    def get(self, name: str, version: Optional[str] = None) -> Optional[TestPackage]:
        """
        Retrieve a test package from the repository.
        If version is None, returns the latest version.
        """
        if name not in self.index["tests"]:
            logger.warning(f"Test '{name}' not found in repository")
            return None

        if version is None:
            # Get latest version
            versions = self.index["tests"][name]
            if not versions:
                return None
            version = versions[-1]["version"]

        package_file = self.repo_path / name / version / "package.json"
        if not package_file.exists():
            logger.warning(f"Package file not found: {package_file}")
            return None

        with open(package_file, 'r') as f:
            data = json.load(f)

        return TestPackage.from_dict(data)

    def list_tests(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all tests in the repository with optional filtering.
        """
        results = []
        for test_name, versions in self.index["tests"].items():
            for version_info in versions:
                # Apply filters
                if category and version_info.get("category") != category:
                    continue
                if tags and not any(tag in version_info.get("tags", []) for tag in tags):
                    continue

                results.append({
                    "name": test_name,
                    **version_info
                })

        return results

    def delete(self, name: str, version: str) -> bool:
        """Delete a specific version of a test."""
        if name not in self.index["tests"]:
            return False

        # Remove from index
        self.index["tests"][name] = [
            v for v in self.index["tests"][name]
            if v["version"] != version
        ]

        # Remove directory
        package_dir = self.repo_path / name / version
        if package_dir.exists():
            import shutil
            shutil.rmtree(package_dir)

        # Clean up empty test directory
        test_dir = self.repo_path / name
        if test_dir.exists() and not any(test_dir.iterdir()):
            test_dir.rmdir()
            del self.index["tests"][name]

        self._save_index()
        logger.info(f"Deleted test package: {name}@{version}")
        return True
