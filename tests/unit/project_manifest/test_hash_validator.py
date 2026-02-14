"""Tests for hash_validator module."""

import hashlib
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from socialseed_e2e.project_manifest.hash_validator import HashValidator, ManifestVersionManager
from socialseed_e2e.project_manifest.models import (
    FileMetadata,
    ManifestFreshness,
    ProjectKnowledge,
    ServiceInfo,
)


class TestHashValidator:
    """Tests for HashValidator class."""

    def test_compute_file_hash(self, tmp_path):
        """Test computing SHA-256 hash of a file."""
        # Create test file
        test_file = tmp_path / "test.py"
        content = b"print('hello world')"
        test_file.write_bytes(content)

        validator = HashValidator(tmp_path)
        file_hash = validator.compute_file_hash(test_file)

        expected_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
        assert file_hash == expected_hash

    def test_compute_file_hash_nonexistent(self, tmp_path):
        """Test computing hash of non-existent file returns None."""
        validator = HashValidator(tmp_path)
        file_hash = validator.compute_file_hash(tmp_path / "nonexistent.py")
        assert file_hash is None

    def test_compute_hashes_for_files(self, tmp_path):
        """Test computing hashes for multiple files."""
        # Create test files
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("content1")
        file2.write_text("content2")

        validator = HashValidator(tmp_path)
        hashes = validator.compute_hashes_for_files([file1, file2])

        assert len(hashes) == 2
        assert "file1.py" in hashes
        assert "file2.py" in hashes
        assert hashes["file1.py"].startswith("sha256:")
        assert hashes["file2.py"].startswith("sha256:")

    def test_validate_manifest_fresh(self, tmp_path):
        """Test validation returns FRESH when manifest matches files."""
        # Create test file
        test_file = tmp_path / "app.py"
        test_file.write_text("content")

        # Compute hash - disable exclude patterns for test
        validator = HashValidator(tmp_path, exclude_patterns=[])
        content = test_file.read_bytes()
        file_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"

        # Create manifest with matching hash
        manifest = ProjectKnowledge(
            version="2.0",
            project_name="test",
            project_root=str(tmp_path),
            source_hashes={"app.py": file_hash},
        )

        freshness, changed = validator.validate_manifest(manifest)
        assert freshness == ManifestFreshness.FRESH
        assert changed == {}

    def test_validate_manifest_stale(self, tmp_path):
        """Test validation returns STALE when files have changed."""
        # Create test file
        test_file = tmp_path / "app.py"
        test_file.write_text("original content")

        # Create manifest with different hash - disable exclude patterns for test
        manifest = ProjectKnowledge(
            version="2.0",
            project_name="test",
            project_root=str(tmp_path),
            source_hashes={"app.py": "sha256:oldhash123"},
        )

        validator = HashValidator(tmp_path, exclude_patterns=[])
        freshness, changed = validator.validate_manifest(manifest)

        assert freshness == ManifestFreshness.STALE
        assert "app.py" in changed

    def test_validate_manifest_new_files(self, tmp_path):
        """Test validation returns STALE when new files exist."""
        # Create test file
        test_file = tmp_path / "new_file.py"
        test_file.write_text("content")

        # Create manifest without the new file - disable exclude patterns for test
        manifest = ProjectKnowledge(
            version="2.0",
            project_name="test",
            project_root=str(tmp_path),
            source_hashes={},
        )

        validator = HashValidator(tmp_path, exclude_patterns=[])
        freshness, changed = validator.validate_manifest(manifest)

        assert freshness == ManifestFreshness.STALE

    def test_validate_manifest_removed_files(self, tmp_path):
        """Test validation returns STALE when files are removed."""
        # Create manifest with a file that doesn't exist
        manifest = ProjectKnowledge(
            version="2.0",
            project_name="test",
            project_root=str(tmp_path),
            source_hashes={"removed.py": "sha256:hash123"},
        )

        validator = HashValidator(tmp_path)
        freshness, changed = validator.validate_manifest(manifest)

        assert freshness == ManifestFreshness.STALE

    def test_quick_check_fresh(self, tmp_path):
        """Test quick_check returns True when manifest is fresh."""
        # Create test file
        test_file = tmp_path / "app.py"
        test_file.write_text("content")

        # Disable exclude patterns for test
        validator = HashValidator(tmp_path, exclude_patterns=[])
        content = test_file.read_bytes()
        file_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"

        manifest = ProjectKnowledge(
            version="2.0",
            project_name="test",
            project_root=str(tmp_path),
            source_hashes={"app.py": file_hash},
        )

        assert validator.quick_check(manifest) is True

    def test_quick_check_stale(self, tmp_path):
        """Test quick_check returns False when manifest is stale."""
        # Create test file
        test_file = tmp_path / "app.py"
        test_file.write_text("content")

        # Disable exclude patterns for test
        manifest = ProjectKnowledge(
            version="2.0",
            project_name="test",
            project_root=str(tmp_path),
            source_hashes={"app.py": "sha256:wronghash"},
        )

        validator = HashValidator(tmp_path, exclude_patterns=[])
        assert validator.quick_check(manifest) is False

    def test_get_changed_files_only(self, tmp_path):
        """Test getting only changed files."""
        # Create files
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("content1")
        file2.write_text("content2")

        # Create manifest where file2 has wrong hash
        content1 = file1.read_bytes()
        hash1 = f"sha256:{hashlib.sha256(content1).hexdigest()}"

        manifest = ProjectKnowledge(
            version="2.0",
            project_name="test",
            project_root=str(tmp_path),
            source_hashes={
                "file1.py": hash1,
                "file2.py": "sha256:wronghash",
            },
        )

        # Disable exclude patterns for test
        validator = HashValidator(tmp_path, exclude_patterns=[])
        changed, added, removed = validator.get_changed_files_only(manifest)

        assert "file2.py" in changed
        assert len(added) == 0
        assert len(removed) == 0


class TestManifestVersionManager:
    """Tests for ManifestVersionManager class."""

    def test_current_version(self):
        """Test current version is 2.0."""
        assert ManifestVersionManager.CURRENT_VERSION == "2.0"

    def test_check_version_current(self):
        """Test check_version returns True for current version."""
        manifest = ProjectKnowledge(
            version="2.0",
            project_name="test",
            project_root="/tmp",
        )

        is_current, version = ManifestVersionManager.check_version(manifest)
        assert is_current is True
        assert version == "2.0"

    def test_check_version_outdated(self):
        """Test check_version returns False for outdated version."""
        manifest = ProjectKnowledge(
            version="1.0.0",
            project_name="test",
            project_root="/tmp",
        )

        is_current, version = ManifestVersionManager.check_version(manifest)
        assert is_current is False
        assert version == "1.0.0"

    def test_migrate_from_1_0_0(self, tmp_path):
        """Test migration from version 1.0.0 to 2.0."""
        # Create a test file
        test_file = tmp_path / "app.py"
        test_file.write_text("content")

        # Create old-style manifest with file_metadata
        metadata = FileMetadata(
            path="app.py",
            checksum="old_md5_hash",
            last_modified=datetime.now(),
        )

        manifest = ProjectKnowledge(
            version="1.0.0",
            project_name="test",
            project_root=str(tmp_path),
            source_hashes={},  # Empty in old version
            file_metadata={"app.py": metadata},
        )

        migrated = ManifestVersionManager.migrate_if_needed(manifest)

        assert migrated.version == "2.0"
        assert "app.py" in migrated.source_hashes
        assert migrated.source_hashes["app.py"].startswith("sha256:")
