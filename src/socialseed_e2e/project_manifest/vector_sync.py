"""Vector index synchronization with manifest changes.

This module integrates the vector store with the file watcher
to automatically update embeddings when the manifest changes.
"""

import time
from pathlib import Path
from typing import Callable, Optional, Union

from socialseed_e2e.project_manifest.file_watcher import SmartSyncManager
from socialseed_e2e.project_manifest.vector_store import ManifestVectorStore


class VectorIndexSyncManager:
    """Manages synchronization between manifest changes and vector index.

    This class watches for changes to the project_knowledge.json file
    and automatically rebuilds the vector index when needed.

    Example:
        >>> sync_manager = VectorIndexSyncManager("/path/to/project")
        >>> sync_manager.start_auto_sync()
        >>> # Index will be updated automatically when manifest changes
    """

    def __init__(
        self,
        project_root: Union[str, Path],
        embedding_model: Optional[str] = None,
        debounce_seconds: float = 5.0,
    ):
        """Initialize the sync manager.

        Args:
            project_root: Root directory of the project
            embedding_model: Name of the embedding model to use
            debounce_seconds: Seconds to wait after manifest change before rebuilding
        """
        self.project_root = Path(project_root).resolve()
        self.debounce_seconds = debounce_seconds
        self._manifest_path = self.project_root / "project_knowledge.json"

        # Initialize vector store
        self.vector_store = ManifestVectorStore(
            self.project_root, embedding_model=embedding_model
        )

        # Ensure initial index exists
        if not self.vector_store.is_index_valid():
            self._rebuild_index()

        # Callbacks
        self._on_update_callbacks: list[Callable[[], None]] = []
        self._last_manifest_mtime: Optional[float] = None
        self._pending_update: bool = False

    def _rebuild_index(self) -> None:
        """Rebuild the vector index."""
        print("📊 Rebuilding vector index...")
        self.vector_store.build_index()
        print("✅ Vector index updated")

        # Notify callbacks
        for callback in self._on_update_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"⚠️  Error in update callback: {e}")

    def check_and_update(self) -> bool:
        """Check if manifest has changed and update index if needed.

        Returns:
            True if index was updated, False otherwise
        """
        if not self._manifest_path.exists():
            return False

        current_mtime = self._manifest_path.stat().st_mtime

        if self._last_manifest_mtime is None:
            self._last_manifest_mtime = current_mtime
            return False

        if current_mtime > self._last_manifest_mtime:
            self._last_manifest_mtime = current_mtime
            self._rebuild_index()
            return True

        return False

    def start_auto_sync(self, check_interval: float = 5.0) -> None:
        """Start automatic synchronization.

        Args:
            check_interval: Seconds between manifest change checks
        """
        print(f"🔄 Starting auto-sync (checking every {check_interval}s)")
        print("   Press Ctrl+C to stop\n")

        try:
            while True:
                self.check_and_update()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\n🛑 Auto-sync stopped")

    def on_index_update(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when index is updated.

        Args:
            callback: Function to call when index is updated
        """
        self._on_update_callbacks.append(callback)

    def force_rebuild(self) -> None:
        """Force a complete rebuild of the vector index."""
        self.vector_store.invalidate_index()
        self._rebuild_index()

    def get_stats(self) -> dict:
        """Get statistics about the vector index.

        Returns:
            Dictionary with sync statistics
        """
        return {
            "index_valid": self.vector_store.is_index_valid(),
            "embedding_model": self.vector_store.embedding_model_name,
            "manifest_exists": self._manifest_path.exists(),
            "manifest_path": str(self._manifest_path),
        }


class IntegratedSyncManager:
    """Integrated manager for manifest and vector index synchronization.

    This class combines the SmartSyncManager (for manifest generation)
    with VectorIndexSyncManager (for vector embeddings) into a single
    coordinated system.

    Example:
        >>> manager = IntegratedSyncManager("/path/to/project")
        >>> manager.start_watching()  # Watches files, updates manifest and index
    """

    def __init__(
        self,
        project_root: Union[str, Path],
        embedding_model: Optional[str] = None,
    ):
        """Initialize the integrated sync manager.

        Args:
            project_root: Root directory of the project
            embedding_model: Name of the embedding model to use
        """
        self.project_root = Path(project_root).resolve()

        # Initialize manifest sync
        from socialseed_e2e.project_manifest import ManifestGenerator

        self.manifest_generator = ManifestGenerator(self.project_root)
        self.manifest_sync = SmartSyncManager(self.manifest_generator)

        # Initialize vector sync (will be created after manifest)
        self.vector_sync: Optional[VectorIndexSyncManager] = None
        self._embedding_model = embedding_model

    def start_watching(self, blocking: bool = True) -> None:
        """Start watching files and updating both manifest and vector index.

        Args:
            blocking: If True, blocks until stopped. If False, returns immediately.
        """

        # Set up callback to rebuild vector index when manifest updates
        def on_manifest_update():
            print("📝 Manifest updated, rebuilding vector index...")
            if self.vector_sync is None:
                self.vector_sync = VectorIndexSyncManager(
                    self.project_root,
                    embedding_model=self._embedding_model,
                )
            self.vector_sync.force_rebuild()

        # Register callback
        self.manifest_sync._on_update_callbacks.append(on_manifest_update)

        # Start watching
        print("👁️  Starting integrated file watcher")
        print("   - Will update manifest on source changes")
        print("   - Will update vector index on manifest changes")
        print("   - Press Ctrl+C to stop\n")

        if blocking:
            try:
                self.manifest_sync.start_watching(blocking=True)
            except KeyboardInterrupt:
                print("\n🛑 Integrated watcher stopped")
        else:
            self.manifest_sync.start_watching(blocking=False)
