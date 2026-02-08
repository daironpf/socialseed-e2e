"""Unit tests for file watcher."""

import time

import pytest

from socialseed_e2e.project_manifest.file_watcher import FileWatcher, SmartSyncManager


class TestFileWatcher:
    """Test FileWatcher class."""

    @pytest.fixture
    def watched_project(self, tmp_path):
        """Create a sample project for watching."""
        # Create initial files
        (tmp_path / "app.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")

        # Create subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "module.py").write_text("class MyClass: pass")

        return tmp_path

    @pytest.fixture
    def watcher(self, watched_project):
        """Create a FileWatcher instance."""
        return FileWatcher(
            project_root=watched_project,
            file_patterns=["*.py"],
            poll_interval=0.1,
        )

    def test_init(self, watched_project):
        """Test file watcher initialization."""
        watcher = FileWatcher(
            project_root=watched_project,
            file_patterns=["*.py"],
        )

        assert watcher.project_root == watched_project
        assert watcher.file_patterns == ["*.py"]
        assert watcher.poll_interval == 1.0

    def test_add_callback(self, watcher):
        """Test adding a callback."""
        calls = []

        def callback(file_path, event_type):
            calls.append((file_path, event_type))

        watcher.add_callback(callback)

        assert len(watcher._callbacks) == 1

    def test_remove_callback(self, watcher):
        """Test removing a callback."""

        def callback(file_path, event_type):
            pass

        watcher.add_callback(callback)
        watcher.remove_callback(callback)

        assert len(watcher._callbacks) == 0

    def test_discover_files(self, watcher, watched_project):
        """Test file discovery."""
        files = watcher._discover_files()

        assert len(files) == 3  # app.py, utils.py, subdir/module.py

    def test_should_exclude(self, watched_project):
        """Test file exclusion."""
        watcher = FileWatcher(
            project_root=watched_project,
            file_patterns=["*.py"],
            exclude_patterns=["**/__pycache__/**", "**/node_modules/**"],
        )

        # Create excluded directories
        pycache = watched_project / "__pycache__"
        pycache.mkdir()
        (pycache / "cache.pyc").write_text("cache")

        # Should exclude
        assert watcher._should_exclude(pycache / "cache.pyc") is True

        # Should not exclude
        assert watcher._should_exclude(watched_project / "app.py") is False

    def test_detect_changes_new_file(self, watcher, watched_project):
        """Test detecting new file creation."""
        # Initial scan
        watcher._scan_files()

        # Create new file
        (watched_project / "new_file.py").write_text("# new file")

        # Detect changes
        changes = watcher._detect_changes()

        assert len(changes) == 1
        assert changes[0] == ("new_file.py", "created")

    def test_detect_changes_modified_file(self, watcher, watched_project):
        """Test detecting file modification."""
        # Initial scan
        watcher._scan_files()

        # Modify file
        time.sleep(0.1)  # Ensure timestamp changes
        (watched_project / "app.py").write_text("# modified content")

        # Detect changes
        changes = watcher._detect_changes()

        assert len(changes) == 1
        assert changes[0] == ("app.py", "modified")

    def test_detect_changes_deleted_file(self, watcher, watched_project):
        """Test detecting file deletion."""
        # Initial scan
        watcher._scan_files()

        # Delete file
        (watched_project / "utils.py").unlink()

        # Detect changes
        changes = watcher._detect_changes()

        assert len(changes) == 1
        assert changes[0] == ("utils.py", "deleted")

    def test_scan_once(self, watcher, watched_project):
        """Test single scan operation."""
        # Create new file
        (watched_project / "another.py").write_text("# another file")

        # Single scan
        changes = watcher.scan_once()

        assert len(changes) == 4  # All files discovered for first time

    def test_get_file_metadata(self, watcher, watched_project):
        """Test getting file metadata."""
        file_path = watched_project / "app.py"
        metadata = watcher._get_file_metadata(file_path)

        assert metadata is not None
        assert metadata.path == "app.py"
        assert len(metadata.checksum) == 32  # MD5 hash
        assert metadata.last_modified is not None


class TestSmartSyncManager:
    """Test SmartSyncManager class."""

    @pytest.fixture
    def mock_generator(self, tmp_path):
        """Create a mock ManifestGenerator."""
        from unittest.mock import MagicMock

        mock = MagicMock()
        mock.project_root = tmp_path
        mock.exclude_patterns = []
        return mock

    def test_init(self, mock_generator):
        """Test SmartSyncManager initialization."""
        manager = SmartSyncManager(mock_generator)

        assert manager.generator == mock_generator
        assert manager.debounce_seconds == 2.0

    def test_custom_debounce(self, mock_generator):
        """Test custom debounce seconds."""
        manager = SmartSyncManager(mock_generator, debounce_seconds=5.0)

        assert manager.debounce_seconds == 5.0

    def test_sync_now(self, mock_generator):
        """Test immediate synchronization."""
        from socialseed_e2e.project_manifest.models import ProjectKnowledge

        # Mock generator response
        mock_generator.generate.return_value = ProjectKnowledge(
            version="1.0.0",
            project_name="test",
            project_root=str(mock_generator.project_root),
        )

        manager = SmartSyncManager(mock_generator)
        manager._pending_changes.add("file.py")

        manager.sync_now()

        mock_generator.generate.assert_called_once_with(force_full_scan=False)
        assert len(manager._pending_changes) == 0

    def test_on_file_change(self, mock_generator):
        """Test handling file change event."""
        manager = SmartSyncManager(mock_generator)

        manager._on_file_change("test.py", "modified")

        assert "test.py" in manager._pending_changes
        assert manager._last_change_time is not None


class TestFileWatcherIntegration:
    """Integration tests for FileWatcher."""

    def test_callbacks_notified_on_change(self, tmp_path):
        """Test that callbacks are notified when files change."""
        calls = []

        def callback(file_path, event_type):
            calls.append((file_path, event_type))

        # Create initial file
        (tmp_path / "app.py").write_text("print('hello')")

        watcher = FileWatcher(
            project_root=tmp_path,
            file_patterns=["*.py"],
            poll_interval=0.05,
        )
        watcher.add_callback(callback)

        # Start watching in background
        import threading

        stop_event = threading.Event()

        def watch():
            watcher._scan_files()
            while not stop_event.is_set():
                changes = watcher._detect_changes()
                for file_path, event_type in changes:
                    watcher._notify_callbacks(file_path, event_type)
                time.sleep(0.05)

        thread = threading.Thread(target=watch)
        thread.start()

        try:
            # Wait for initial scan
            time.sleep(0.1)

            # Create new file
            time.sleep(0.1)
            (tmp_path / "new.py").write_text("# new")

            # Wait for detection
            time.sleep(0.15)

            assert len(calls) == 1
            assert calls[0] == ("new.py", "created")

        finally:
            stop_event.set()
            thread.join(timeout=1.0)
