"""Plugin marketplace for discovering and installing plugins.

This module provides a marketplace for finding, installing,
and managing plugins from official and community sources.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginListing:
    """Represents a plugin in the marketplace."""

    def __init__(
        self,
        plugin_id: str,
        name: str,
        version: str,
        description: str,
        author: str,
        category: str = "general",
        tags: List[str] = None,
        downloads: int = 0,
        rating: float = 0.0,
        reviews: int = 0,
        repository_url: Optional[str] = None,
        homepage: Optional[str] = None,
        license: str = "MIT",
    ):
        """Initialize plugin listing."""
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.category = category
        self.tags = tags or []
        self.downloads = downloads
        self.rating = rating
        self.reviews = reviews
        self.repository_url = repository_url
        self.homepage = homepage
        self.license = license
        self.installed = False
        self.installed_version: Optional[str] = None


class PluginMarketplace:
    """Manage plugin marketplace operations."""

    def __init__(self, cache_dir: str = ".e2e/plugins/cache"):
        """Initialize plugin marketplace.

        Args:
            cache_dir: Directory for caching marketplace data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._official_plugins: List[PluginListing] = self._load_official_plugins()
        self._community_plugins: List[PluginListing] = []

    def _load_official_plugins(self) -> List[PluginListing]:
        """Load official plugins."""
        return [
            PluginListing(
                plugin_id="e2e-aws-lambda",
                name="AWS Lambda Testing",
                version="1.0.0",
                description="Test AWS Lambda functions locally",
                author="SocialSeed Team",
                category="cloud",
                tags=["aws", "lambda", "serverless"],
                downloads=1500,
                rating=4.5,
                reviews=45,
            ),
            PluginListing(
                plugin_id="e2e-azure-functions",
                name="Azure Functions Testing",
                version="1.0.0",
                description="Test Azure Functions locally",
                author="SocialSeed Team",
                category="cloud",
                tags=["azure", "functions", "serverless"],
                downloads=800,
                rating=4.3,
                reviews=28,
            ),
            PluginListing(
                plugin_id="e2e-graphql-validator",
                name="GraphQL Schema Validator",
                version="1.0.0",
                description="Validate GraphQL schemas and operations",
                author="SocialSeed Team",
                category="validation",
                tags=["graphql", "schema", "validation"],
                downloads=2200,
                rating=4.7,
                reviews=89,
            ),
            PluginListing(
                plugin_id="e2e-jwt-auth",
                name="JWT Authentication",
                version="1.0.0",
                description="JWT token generation and validation",
                author="SocialSeed Team",
                category="security",
                tags=["jwt", "auth", "security"],
                downloads=3100,
                rating=4.8,
                reviews=156,
            ),
            PluginListing(
                plugin_id="e2e-kafka-producer",
                name="Kafka Producer",
                version="1.0.0",
                description="Produce messages to Kafka topics",
                author="SocialSeed Team",
                category="messaging",
                tags=["kafka", "messaging", "streaming"],
                downloads=950,
                rating=4.4,
                reviews=32,
            ),
        ]

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[PluginListing]:
        """Search for plugins.

        Args:
            query: Search query
            category: Optional category filter
            tags: Optional tags filter

        Returns:
            List of matching plugins
        """
        all_plugins = self._official_plugins + self._community_plugins

        results = []
        query_lower = query.lower()

        for plugin in all_plugins:
            if (
                query_lower not in plugin.name.lower()
                and query_lower not in plugin.description.lower()
            ):
                continue

            if category and plugin.category != category:
                continue

            if tags and not any(tag in plugin.tags for tag in tags):
                continue

            results.append(plugin)

        return sorted(results, key=lambda p: p.downloads, reverse=True)

    def get_by_category(self, category: str) -> List[PluginListing]:
        """Get plugins by category.

        Args:
            category: Category name

        Returns:
            List of plugins in category
        """
        return [
            p
            for p in self._official_plugins + self._community_plugins
            if p.category == category
        ]

    def get_featured(self) -> List[PluginListing]:
        """Get featured plugins.

        Returns:
            List of featured plugins
        """
        all_plugins = self._official_plugins + self._community_plugins
        return sorted(all_plugins, key=lambda p: p.rating, reverse=True)[:5]

    def get_popular(self) -> List[PluginListing]:
        """Get popular plugins.

        Returns:
            List of popular plugins
        """
        all_plugins = self._official_plugins + self._community_plugins
        return sorted(all_plugins, key=lambda p: p.downloads, reverse=True)[:10]

    def add_community_plugin(self, plugin: PluginListing):
        """Add a community plugin to the marketplace.

        Args:
            plugin: Plugin to add
        """
        self._community_plugins.append(plugin)

    def rate_plugin(self, plugin_id: str, rating: float):
        """Rate a plugin.

        Args:
            plugin_id: Plugin ID
            rating: Rating (1-5)
        """
        for plugin in self._official_plugins + self._community_plugins:
            if plugin.plugin_id == plugin_id:
                total_rating = plugin.rating * plugin.reviews + rating
                plugin.reviews += 1
                plugin.rating = total_rating / plugin.reviews
                break


class PluginInstaller:
    """Install and manage plugin installations."""

    def __init__(self, plugins_dir: str = ".e2e/plugins"):
        """Initialize plugin installer.

        Args:
            plugins_dir: Directory for installed plugins
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.plugins_dir / "manifest.json"
        self._load_manifest()

    def _load_manifest(self):
        """Load installed plugins manifest."""
        if self.manifest_file.exists():
            self.manifest = json.loads(self.manifest_file.read_text())
        else:
            self.manifest = {"plugins": {}}

    def _save_manifest(self):
        """Save installed plugins manifest."""
        self.manifest_file.write_text(json.dumps(self.manifest, indent=2))

    def install(
        self, plugin_id: str, version: str, source: str = "marketplace"
    ) -> bool:
        """Install a plugin.

        Args:
            plugin_id: Plugin ID
            version: Version to install
            source: Installation source

        Returns:
            True if successful
        """
        plugin_dir = self.plugins_dir / plugin_id
        plugin_dir.mkdir(parents=True, exist_ok=True)

        self.manifest["plugins"][plugin_id] = {
            "version": version,
            "source": source,
            "installed_at": datetime.now().isoformat(),
            "enabled": True,
        }

        self._save_manifest()
        logger.info(f"Installed plugin: {plugin_id}@{version}")
        return True

    def uninstall(self, plugin_id: str) -> bool:
        """Uninstall a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if successful
        """
        if plugin_id not in self.manifest["plugins"]:
            return False

        plugin_dir = self.plugins_dir / plugin_id
        if plugin_dir.exists():
            import shutil

            shutil.rmtree(plugin_dir)

        del self.manifest["plugins"][plugin_id]
        self._save_manifest()

        logger.info(f"Uninstalled plugin: {plugin_id}")
        return True

    def enable(self, plugin_id: str) -> bool:
        """Enable a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if successful
        """
        if plugin_id in self.manifest["plugins"]:
            self.manifest["plugins"][plugin_id]["enabled"] = True
            self._save_manifest()
            return True
        return False

    def disable(self, plugin_id: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if successful
        """
        if plugin_id in self.manifest["plugins"]:
            self.manifest["plugins"][plugin_id]["enabled"] = False
            self._save_manifest()
            return True
        return False

    def list_installed(self) -> List[Dict[str, Any]]:
        """List installed plugins.

        Returns:
            List of installed plugins
        """
        return [
            {"plugin_id": pid, **info} for pid, info in self.manifest["plugins"].items()
        ]

    def is_installed(self, plugin_id: str) -> bool:
        """Check if a plugin is installed.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if installed
        """
        return plugin_id in self.manifest["plugins"]
