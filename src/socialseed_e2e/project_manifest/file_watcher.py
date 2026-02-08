"""File watcher for Smart Sync functionality.

This module provides file system watching capabilities to detect changes
in the project and trigger incremental updates to the manifest.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set, Tuple

from socialseed_e2e.project_manifest.models import FileMetadata

if TYPE_CHECKING:
    from socialseed_e2e.project_manifest.generator import ManifestGenerator


class FileWatcher:
    """Watches files for changes and triggers callbacks."""

    def __init__(
        self,
        project_root: Path,
        file_patterns: List[str],
        exclude_patterns: Optional[List[str]] = None,
        poll_interval: float = 1.0,
    ):
        """Initialize file watcher.

        Args:
            project_root: Root directory to watch
            file_patterns: List of glob patterns to watch (e.g., ["*.py", "*.java"])
            exclude_patterns: List of glob patterns to exclude
            poll_interval: Seconds between polling cycles
        """
        self.project_root = Path(project_root).resolve()
        self.file_patterns = file_patterns
        self.exclude_patterns = exclude_patterns or [
            "**/node_modules/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/venv/**",
            "**/.venv/**",
            "**/target/**",
            "**/build/**",
            "**/dist/**",
        ]
        self.poll_interval = poll_interval

        self._file_states: Dict[str, FileMetadata] = {}
        self._callbacks: List[Callable[[str, str], None]] = []
        self._running = False

    def add_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add a callback for file changes.

        Args:
            callback: Function to call on file change. Signature: callback(file_path, event_type)
                     where event_type is 'created', 'modified', or 'deleted'
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str, str], None]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start(self) -> None:
        """Start watching files (blocking)."""
        self._running = True
        print(f"👁️  Starting file watcher on {self.project_root}")
        print(f"   Watching patterns: {', '.join(self.file_patterns)}")
        print("   Press Ctrl+C to stop\n")

        # Initial scan
        self._scan_files()

        try:
            while self._running:
                time.sleep(self.poll_interval)
                changes = self._detect_changes()

                for file_path, event_type in changes:
                    self._notify_callbacks(file_path, event_type)

        except KeyboardInterrupt:
            print("\n🛑 File watcher stopped.")
            self.stop()

    def stop(self) -> None:
        """Stop watching files."""
        self._running = False

    def scan_once(self) -> List[Tuple[str, str]]:
        """Perform a single scan and return changes.

        Returns:
            List of (file_path, event_type) tuples
        """
        return self._detect_changes()

    def _scan_files(self) -> None:
        """Scan all watched files and store their state."""
        files = self._discover_files()

        for file_path in files:
            file_key = str(file_path.relative_to(self.project_root))
            metadata = self._get_file_metadata(file_path)
            if metadata:
                self._file_states[file_key] = metadata

    def _detect_changes(self) -> List[Tuple[str, str]]:
        """Detect changes in watched files.

        Returns:
            List of (file_path, event_type) tuples
        """
        changes = []
        current_files = self._discover_files()
        current_file_paths = {str(f.relative_to(self.project_root)) for f in current_files}

        # Check for new and modified files
        for file_path in current_files:
            file_key = str(file_path.relative_to(self.project_root))
            metadata = self._get_file_metadata(file_path)

            if not metadata:
                continue

            if file_key not in self._file_states:
                # New file
                changes.append((file_key, "created"))
                self._file_states[file_key] = metadata
            elif metadata.checksum != self._file_states[file_key].checksum:
                # Modified file
                changes.append((file_key, "modified"))
                self._file_states[file_key] = metadata

        # Check for deleted files
        for file_key in list(self._file_states.keys()):
            if file_key not in current_file_paths:
                changes.append((file_key, "deleted"))
                del self._file_states[file_key]

        return changes

    def _discover_files(self) -> List[Path]:
        """Discover all files matching watched patterns."""
        files = []

        for pattern in self.file_patterns:
            for file_path in self.project_root.rglob(pattern):
                if not self._should_exclude(file_path):
                    files.append(file_path)

        return files

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded."""
        import fnmatch

        str_path = str(file_path)
        relative_path = str(file_path.relative_to(self.project_root))

        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(str_path, pattern) or fnmatch.fnmatch(relative_path, pattern):
                return True

        return False

    def _get_file_metadata(self, file_path: Path) -> Optional[FileMetadata]:
        """Get metadata for a file."""
        try:
            stat = file_path.stat()
            content = file_path.read_bytes()

            return FileMetadata(
                path=str(file_path.relative_to(self.project_root)),
                checksum=hashlib.md5(content).hexdigest(),
                last_modified=datetime.fromtimestamp(stat.st_mtime),
            )
        except (OSError, IOError):
            return None

    def _notify_callbacks(self, file_path: str, event_type: str) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(file_path, event_type)
            except Exception as e:
                print(f"⚠️  Error in file watcher callback: {e}")


class SmartSyncManager:
    """Manages smart synchronization between file changes and manifest updates."""

    def __init__(
        self,
        generator: "ManifestGenerator",
        debounce_seconds: float = 2.0,
    ):
        """Initialize smart sync manager.

        Args:
            generator: ManifestGenerator instance
            debounce_seconds: Seconds to wait after last change before updating
        """
        self.generator = generator
        self.debounce_seconds = debounce_seconds
        self._pending_changes: Set[str] = set()
        self._last_change_time: Optional[float] = None
        self._watcher: Optional[FileWatcher] = None

    def start_watching(self, blocking: bool = True) -> None:
        """Start watching files and updating manifest.

        Args:
            blocking: If True, blocks until stopped. If False, returns immediately.
        """
        self._watcher = FileWatcher(
            project_root=self.generator.project_root,
            file_patterns=["*.py", "*.java", "*.js", "*.ts", "*.go", "*.cs"],
            exclude_patterns=self.generator.exclude_patterns,
            poll_interval=1.0,
        )

        self._watcher.add_callback(self._on_file_change)

        if blocking:
            self._watcher.start()
        else:
            # Start in background thread
            import threading

            self._watch_thread = threading.Thread(target=self._watcher.start)
            self._watch_thread.daemon = True
            self._watch_thread.start()

    def stop_watching(self) -> None:
        """Stop watching files."""
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def sync_now(self) -> None:
        """Force immediate synchronization."""
        if self._pending_changes:
            print(f"🔄 Syncing {len(self._pending_changes)} pending changes...")
            self.generator.generate(force_full_scan=False)
            self._pending_changes.clear()

    def _on_file_change(self, file_path: str, event_type: str) -> None:
        """Handle file change event."""
        self._pending_changes.add(file_path)
        self._last_change_time = time.time()

        print(f"📝 File {event_type}: {file_path}")

        # Schedule debounced update
        self._schedule_update()

    def _schedule_update(self) -> None:
        """Schedule a debounced manifest update."""
        import threading

        def delayed_update():
            time.sleep(self.debounce_seconds)

            if (
                self._last_change_time
                and time.time() - self._last_change_time >= self.debounce_seconds
            ):
                if self._pending_changes:
                    self.sync_now()

        thread = threading.Thread(target=delayed_update)
        thread.daemon = True
        thread.start()
