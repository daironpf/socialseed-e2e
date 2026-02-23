"""Source code hash tracking and validation for Project Manifest.

This module provides hash-based validation to quickly detect when the manifest
is outdated without requiring a full re-scan.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from socialseed_e2e.project_manifest.models import ManifestFreshness, ProjectKnowledge


class HashValidator:
    """Validates manifest freshness using source code hashes."""

    def __init__(
        self,
        project_root: Path,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """Initialize hash validator.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Optional custom exclude patterns. If None, uses defaults.
        """
        self.project_root = Path(project_root).resolve()
        self.exclude_patterns = exclude_patterns

    def compute_file_hash(self, file_path: Path) -> Optional[str]:
        """Compute SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash string or None if file cannot be read
        """
        try:
            content = file_path.read_bytes()
            return f"sha256:{hashlib.sha256(content).hexdigest()}"
        except (OSError, IOError):
            return None

    def compute_hashes_for_files(self, file_paths: List[Path]) -> Dict[str, str]:
        """Compute SHA-256 hashes for multiple files.

        Args:
            file_paths: List of file paths

        Returns:
            Dictionary mapping relative file paths to their SHA-256 hashes
        """
        hashes = {}
        for file_path in file_paths:
            file_hash = self.compute_file_hash(file_path)
            if file_hash:
                relative_path = str(file_path.relative_to(self.project_root))
                hashes[relative_path] = file_hash
        return hashes

    def validate_manifest(
        self, manifest: ProjectKnowledge
    ) -> Tuple[ManifestFreshness, Dict[str, str]]:
        """Quickly validate manifest freshness using hashes.

        Args:
            manifest: The manifest to validate

        Returns:
            Tuple of (freshness_status, changed_files)
            - freshness_status: fresh, stale, or partial
            - changed_files: Dictionary of changed files with their new hashes
        """
        if not manifest.source_hashes:
            # No hashes stored, manifest needs full update
            return ManifestFreshness.STALE, {}

        changed_files = {}
        missing_files = []
        new_files = []

        # Discover current files
        current_files = self._discover_source_files()
        current_file_paths = {str(f.relative_to(self.project_root)) for f in current_files}
        manifest_file_paths = set(manifest.source_hashes.keys())

        # Check for deleted files
        removed_files = manifest_file_paths - current_file_paths
        if removed_files:
            return ManifestFreshness.STALE, {}

        # Check for new files
        new_files = list(current_file_paths - manifest_file_paths)
        if new_files:
            # New files detected, manifest is stale
            return ManifestFreshness.STALE, {}

        # Check hashes of existing files
        for file_path in current_files:
            relative_path = str(file_path.relative_to(self.project_root))

            if relative_path not in manifest.source_hashes:
                new_files.append(relative_path)
                continue

            current_hash = self.compute_file_hash(file_path)
            stored_hash = manifest.source_hashes[relative_path]

            if current_hash != stored_hash:
                changed_files[relative_path] = current_hash

        # Determine freshness
        if changed_files:
            return ManifestFreshness.STALE, changed_files
        elif new_files:
            return ManifestFreshness.STALE, changed_files
        else:
            return ManifestFreshness.FRESH, {}

    def quick_check(self, manifest: ProjectKnowledge) -> bool:
        """Ultra-fast check if manifest is fresh (no changed files).

        Args:
            manifest: The manifest to check

        Returns:
            True if manifest is fresh, False otherwise
        """
        freshness, _ = self.validate_manifest(manifest)
        return freshness == ManifestFreshness.FRESH

    def get_changed_files_only(
        self, manifest: ProjectKnowledge
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """Get only the files that have changed, been added, or removed.

        Args:
            manifest: The manifest to check

        Returns:
            Tuple of (changed, added, removed) file sets
        """
        current_files = self._discover_source_files()
        current_file_paths = {str(f.relative_to(self.project_root)) for f in current_files}
        manifest_file_paths = set(manifest.source_hashes.keys())

        # Find added and removed files
        added_files = current_file_paths - manifest_file_paths
        removed_files = manifest_file_paths - current_file_paths

        # Find modified files by comparing hashes
        changed_files = set()
        for file_path in current_files:
            relative_path = str(file_path.relative_to(self.project_root))
            if relative_path in manifest.source_hashes:
                current_hash = self.compute_file_hash(file_path)
                if current_hash != manifest.source_hashes[relative_path]:
                    changed_files.add(relative_path)

        return changed_files, added_files, removed_files

    def _discover_source_files(self) -> List[Path]:
        """Discover all source files in the project."""
        source_files = []

        # Use custom patterns if provided, otherwise use defaults
        if self.exclude_patterns is not None:
            exclude_patterns = self.exclude_patterns
        else:
            exclude_patterns = [
                "**/node_modules/**",
                "**/.git/**",
                "**/__pycache__/**",
                "**/*.pyc",
                "**/venv/**",
                "**/.venv/**",
                "**/target/**",
                "**/build/**",
                "**/dist/**",
                "**/.idea/**",
                "**/.vscode/**",
            ]

        for ext in ["*.py", "*.java", "*.js", "*.ts", "*.go", "*.cs"]:
            for file_path in self.project_root.rglob(ext):
                if not self._should_exclude(file_path, exclude_patterns):
                    source_files.append(file_path)

        return source_files

    def _should_exclude(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded from scanning."""
        import fnmatch

        str_path = str(file_path)
        relative_path = str(file_path.relative_to(self.project_root))

        for pattern in exclude_patterns:
            if fnmatch.fnmatch(str_path, pattern) or fnmatch.fnmatch(relative_path, pattern):
                return True

        return False


class ManifestVersionManager:
    """Manages manifest versioning and migrations."""

    CURRENT_VERSION = "2.0"

    @classmethod
    def check_version(cls, manifest: ProjectKnowledge) -> Tuple[bool, str]:
        """Check if manifest version is current.

        Args:
            manifest: The manifest to check

        Returns:
            Tuple of (is_current, current_version)
        """
        return manifest.version == cls.CURRENT_VERSION, manifest.version

    @classmethod
    def migrate_if_needed(cls, manifest: ProjectKnowledge) -> ProjectKnowledge:
        """Migrate manifest to current version if needed.

        Args:
            manifest: Manifest to migrate

        Returns:
            Migrated manifest
        """
        if manifest.version == "1.0.0":
            # Migration from 1.0.0 to 2.0
            manifest.version = cls.CURRENT_VERSION

            # Initialize source_hashes from file_metadata if available
            if hasattr(manifest, "file_metadata") and manifest.file_metadata:
                manifest.source_hashes = {}
                project_root = Path(manifest.project_root)
                for file_key, _metadata in manifest.file_metadata.items():
                    # Convert MD5 to SHA-256 by recomputing
                    file_path = project_root / file_key
                    if file_path.exists():
                        validator = HashValidator(project_root)
                        file_hash = validator.compute_file_hash(file_path)
                        if file_hash:
                            manifest.source_hashes[file_key] = file_hash

            manifest.manifest_freshness = ManifestFreshness.FRESH

        return manifest
