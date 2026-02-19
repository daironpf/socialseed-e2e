"""API version detection and strategy identification.

This module detects the versioning strategy used by an API
and provides utilities for version-aware testing.
"""

import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from .models import VersionStrategy, APIVersion


class VersionDetector:
    """Detect API versioning strategy and available versions."""

    def __init__(self, base_url: str):
        """Initialize version detector.

        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url
        self.strategy: Optional[VersionStrategy] = None
        self.discovered_versions: List[APIVersion] = []

    def detect_strategy(self, endpoints: List[Dict[str, Any]]) -> VersionStrategy:
        """Detect the versioning strategy from endpoints.

        Args:
            endpoints: List of discovered API endpoints

        Returns:
            Detected VersionStrategy
        """
        url_path_versions = set()
        header_versions = set()
        query_versions = set()

        for endpoint in endpoints:
            path = endpoint.get("path", "")

            version_match = re.search(r"/v(\d+)/|/version/(\w+)/|/api/(\w+)/", path)
            if version_match:
                for group in version_match.groups():
                    if group:
                        url_path_versions.add(group)

            if "version" in endpoint.get("parameters", []):
                query_versions.add("query")

            if "accept" in endpoint.get("headers", []) or "api-version" in endpoint.get(
                "headers", []
            ):
                header_versions.add("header")

        if url_path_versions:
            self.strategy = VersionStrategy.URL_PATH
        elif header_versions:
            self.strategy = VersionStrategy.HEADER
        elif query_versions:
            self.strategy = VersionStrategy.QUERY_PARAM
        else:
            self.strategy = VersionStrategy.URL_PATH

        return self.strategy

    def discover_versions(
        self, strategy: Optional[VersionStrategy] = None
    ) -> List[APIVersion]:
        """Discover available API versions.

        Args:
            strategy: Versioning strategy to use

        Returns:
            List of discovered APIVersion objects
        """
        if strategy:
            self.strategy = strategy
        elif not self.strategy:
            self.strategy = VersionStrategy.URL_PATH

        if self.strategy == VersionStrategy.URL_PATH:
            return self._discover_url_path_versions()
        elif self.strategy == VersionStrategy.HEADER:
            return self._discover_header_versions()
        elif self.strategy == VersionStrategy.QUERY_PARAM:
            return self._discover_query_versions()

        return []

    def _discover_url_path_versions(self) -> List[APIVersion]:
        """Discover versions from URL paths."""
        versions = []

        common_versions = ["v1", "v2", "v3", "v1.0", "v2.0", "v3.0", "v1_0", "v2_0"]

        for version in common_versions:
            url = f"{self.base_url.rstrip('/')}/{version}"
            versions.append(
                APIVersion(
                    version=version,
                    base_url=url,
                )
            )

        self.discovered_versions = versions
        return versions

    def _discover_header_versions(self) -> List[APIVersion]:
        """Discover versions from headers."""
        versions = []

        common_versions = ["1", "2", "3", "1.0", "2.0", "3.0"]

        for version in common_versions:
            versions.append(
                APIVersion(
                    version=version,
                    base_url=self.base_url,
                )
            )

        self.discovered_versions = versions
        return versions

    def _discover_query_versions(self) -> List[APIVersion]:
        """Discover versions from query parameters."""
        return self._discover_url_path_versions()

    def get_version_url(self, version: str) -> str:
        """Get the full URL for a specific version.

        Args:
            version: Version string

        Returns:
            Full URL with version applied
        """
        if self.strategy == VersionStrategy.URL_PATH:
            return f"{self.base_url.rstrip('/')}/{version}"
        elif self.strategy == VersionStrategy.HEADER:
            return self.base_url
        elif self.strategy == VersionStrategy.QUERY_PARAM:
            separator = "&" if "?" in self.base_url else "?"
            return f"{self.base_url}{separator}version={version}"

        return self.base_url

    def get_version_headers(self, version: str) -> Dict[str, str]:
        """Get headers for a specific version.

        Args:
            version: Version string

        Returns:
            Dictionary of headers
        """
        if self.strategy == VersionStrategy.HEADER:
            return {
                "Accept": f"application/vnd.api+json;version={version}",
                "api-version": version,
            }
        elif self.strategy == VersionStrategy.MEDIA_TYPE:
            return {
                "Accept": f"application/vnd.api.v{version}+json",
            }

        return {}

    def get_version_params(self, version: str) -> Dict[str, str]:
        """Get query parameters for a specific version.

        Args:
            version: Version string

        Returns:
            Dictionary of query parameters
        """
        if self.strategy == VersionStrategy.QUERY_PARAM:
            return {"version": version}

        return {}

    def is_version_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated.

        Args:
            version: Version string

        Returns:
            True if deprecated
        """
        for v in self.discovered_versions:
            if v.version == version:
                return v.is_deprecated

        deprecated_patterns = ["v1", "v1.0", "1.0", "1"]
        return version in deprecated_patterns

    def get_latest_version(self) -> Optional[str]:
        """Get the latest non-deprecated version.

        Returns:
            Latest version string or None
        """
        non_deprecated = [v for v in self.discovered_versions if not v.is_deprecated]

        if not non_deprecated:
            return (
                self.discovered_versions[-1].version
                if self.discovered_versions
                else None
            )

        version_nums = []
        for v in non_deprecated:
            match = re.search(r"(\d+)", v.version)
            if match:
                version_nums.append((int(match.group(1)), v.version))

        if version_nums:
            return max(version_nums)[1]

        return non_deprecated[-1].version

    def get_supported_versions(self) -> List[str]:
        """Get list of supported (non-deprecated) versions.

        Returns:
            List of version strings
        """
        return [v.version for v in self.discovered_versions if not v.is_deprecated]

    def get_deprecated_versions(self) -> List[str]:
        """Get list of deprecated versions.

        Returns:
            List of version strings
        """
        return [v.version for v in self.discovered_versions if v.is_deprecated]
