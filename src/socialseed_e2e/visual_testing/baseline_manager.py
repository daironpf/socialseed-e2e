"""Baseline management for visual regression testing.

This module manages visual baselines, including creation, updates,
versioning, and storage of baseline images.
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from socialseed_e2e.visual_testing.models import (
    BaselineInfo,
    BaselineSnapshot,
    ContentType,
    ViewportSize,
)

logger = logging.getLogger(__name__)


class BaselineManager:
    """Manage visual test baselines."""

    def __init__(self, baseline_dir: str = ".e2e/visual_baselines"):
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.baseline_dir / "baselines.json"
        self._baselines: Dict[str, BaselineInfo] = {}
        self._snapshots: Dict[str, List[BaselineSnapshot]] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load baseline metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)

                # Load baselines
                for baseline_data in data.get("baselines", []):
                    baseline = BaselineInfo.model_validate(baseline_data)
                    self._baselines[baseline.id] = baseline

                # Load snapshots
                for snapshot_data in data.get("snapshots", []):
                    snapshot = BaselineSnapshot.model_validate(snapshot_data)
                    if snapshot.baseline_id not in self._snapshots:
                        self._snapshots[snapshot.baseline_id] = []
                    self._snapshots[snapshot.baseline_id].append(snapshot)

            except Exception as e:
                logger.error(f"Failed to load baseline metadata: {e}")

    def _save_metadata(self) -> None:
        """Save baseline metadata to file."""
        try:
            data = {
                "baselines": [b.model_dump() for b in self._baselines.values()],
                "snapshots": [],
            }

            # Collect all snapshots
            for snapshots in self._snapshots.values():
                data["snapshots"].extend([s.model_dump() for s in snapshots])

            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save baseline metadata: {e}")

    def create_baseline(
        self,
        test_name: str,
        screenshot_path: str,
        content_type: ContentType = ContentType.HTML,
        viewport: Optional[ViewportSize] = None,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BaselineInfo:
        """Create a new baseline from a screenshot.

        Args:
            test_name: Associated test name
            screenshot_path: Path to screenshot file
            content_type: Type of content
            viewport: Viewport size used
            name: Baseline name (defaults to test name)
            tags: Tags for organization
            metadata: Additional metadata

        Returns:
            Created baseline info
        """
        screenshot_path = Path(screenshot_path)

        if not screenshot_path.exists():
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")

        # Generate baseline ID
        baseline_id = self._generate_baseline_id(test_name, viewport)

        # Copy screenshot to baseline directory
        baseline_file = self.baseline_dir / f"{baseline_id}.png"
        shutil.copy2(screenshot_path, baseline_file)

        # Calculate checksum
        checksum = self._calculate_checksum(baseline_file)

        # Create baseline info
        baseline = BaselineInfo(
            id=baseline_id,
            name=name or test_name,
            test_name=test_name,
            content_type=content_type,
            viewport=viewport or ViewportSize(),
            file_path=str(baseline_file),
            created_by=self._get_current_user(),
            tags=tags or [],
            metadata=metadata or {},
            checksum=checksum,
        )

        # Store baseline
        self._baselines[baseline_id] = baseline
        self._save_metadata()

        logger.info(f"Created baseline: {baseline_id} for test: {test_name}")

        return baseline

    def get_baseline(
        self,
        test_name: str,
        viewport: Optional[ViewportSize] = None,
    ) -> Optional[BaselineInfo]:
        """Get baseline for a test.

        Args:
            test_name: Test name
            viewport: Optional viewport size

        Returns:
            Baseline info or None
        """
        baseline_id = self._generate_baseline_id(test_name, viewport)
        return self._baselines.get(baseline_id)

    def get_baseline_by_id(self, baseline_id: str) -> Optional[BaselineInfo]:
        """Get baseline by ID.

        Args:
            baseline_id: Baseline ID

        Returns:
            Baseline info or None
        """
        return self._baselines.get(baseline_id)

    def update_baseline(
        self,
        baseline_id: str,
        screenshot_path: str,
        description: Optional[str] = None,
    ) -> BaselineInfo:
        """Update an existing baseline.

        Args:
            baseline_id: Baseline ID
            screenshot_path: Path to new screenshot
            description: Optional update description

        Returns:
            Updated baseline info
        """
        if baseline_id not in self._baselines:
            raise ValueError(f"Baseline not found: {baseline_id}")

        # Create snapshot of current baseline
        self._create_snapshot(baseline_id, description or "Update before replacement")

        # Copy new screenshot
        baseline = self._baselines[baseline_id]
        shutil.copy2(screenshot_path, baseline.file_path)

        # Update metadata
        baseline.updated_at = datetime.utcnow()
        baseline.checksum = self._calculate_checksum(Path(baseline.file_path))

        self._save_metadata()

        logger.info(f"Updated baseline: {baseline_id}")

        return baseline

    def delete_baseline(self, baseline_id: str) -> bool:
        """Delete a baseline.

        Args:
            baseline_id: Baseline ID

        Returns:
            True if deleted, False if not found
        """
        if baseline_id not in self._baselines:
            return False

        baseline = self._baselines[baseline_id]

        # Delete file
        baseline_file = Path(baseline.file_path)
        if baseline_file.exists():
            baseline_file.unlink()

        # Remove from storage
        del self._baselines[baseline_id]

        # Remove associated snapshots
        if baseline_id in self._snapshots:
            for snapshot in self._snapshots[baseline_id]:
                snapshot_file = Path(snapshot.file_path)
                if snapshot_file.exists():
                    snapshot_file.unlink()
            del self._snapshots[baseline_id]

        self._save_metadata()

        logger.info(f"Deleted baseline: {baseline_id}")

        return True

    def list_baselines(
        self,
        test_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        content_type: Optional[ContentType] = None,
    ) -> List[BaselineInfo]:
        """List baselines with optional filtering.

        Args:
            test_name: Filter by test name
            tags: Filter by tags (all must match)
            content_type: Filter by content type

        Returns:
            List of baseline info
        """
        baselines = list(self._baselines.values())

        # Apply filters
        if test_name:
            baselines = [b for b in baselines if b.test_name == test_name]

        if tags:
            baselines = [b for b in baselines if all(tag in b.tags for tag in tags)]

        if content_type:
            baselines = [b for b in baselines if b.content_type == content_type]

        # Sort by updated date (newest first)
        baselines.sort(key=lambda b: b.updated_at, reverse=True)

        return baselines

    def approve_current_as_baseline(
        self,
        test_name: str,
        current_screenshot_path: str,
        viewport: Optional[ViewportSize] = None,
    ) -> BaselineInfo:
        """Approve current screenshot as new baseline.

        Args:
            test_name: Test name
            current_screenshot_path: Path to current screenshot
            viewport: Optional viewport size

        Returns:
            Baseline info
        """
        existing_baseline = self.get_baseline(test_name, viewport)

        if existing_baseline:
            # Update existing
            return self.update_baseline(
                existing_baseline.id,
                current_screenshot_path,
                description="Approved as new baseline",
            )
        else:
            # Create new
            return self.create_baseline(
                test_name=test_name,
                screenshot_path=current_screenshot_path,
                viewport=viewport,
            )

    def get_snapshots(self, baseline_id: str) -> List[BaselineSnapshot]:
        """Get all snapshots for a baseline.

        Args:
            baseline_id: Baseline ID

        Returns:
            List of snapshots
        """
        return self._snapshots.get(baseline_id, [])

    def restore_snapshot(self, snapshot_id: str) -> Optional[BaselineInfo]:
        """Restore a baseline from a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Restored baseline or None
        """
        # Find snapshot
        for baseline_id, snapshots in self._snapshots.items():
            for snapshot in snapshots:
                if snapshot.id == snapshot_id:
                    # Restore snapshot to baseline
                    baseline = self._baselines.get(baseline_id)
                    if baseline:
                        # Create snapshot of current before restoring
                        self._create_snapshot(baseline_id, "Before restore")

                        # Restore
                        shutil.copy2(snapshot.file_path, baseline.file_path)
                        baseline.updated_at = datetime.utcnow()
                        baseline.checksum = self._calculate_checksum(
                            Path(baseline.file_path)
                        )

                        self._save_metadata()

                        logger.info(
                            f"Restored snapshot {snapshot_id} to baseline {baseline_id}"
                        )
                        return baseline

        return None

    def compare_to_baseline(
        self,
        test_name: str,
        current_screenshot_path: str,
        viewport: Optional[ViewportSize] = None,
    ) -> Tuple[bool, Optional[BaselineInfo]]:
        """Compare current screenshot to baseline.

        Args:
            test_name: Test name
            current_screenshot_path: Path to current screenshot
            viewport: Optional viewport size

        Returns:
            Tuple of (has_baseline, baseline_info)
        """
        baseline = self.get_baseline(test_name, viewport)

        if not baseline:
            return False, None

        # Check if file exists
        baseline_file = Path(baseline.file_path)
        if not baseline_file.exists():
            logger.warning(f"Baseline file missing: {baseline.file_path}")
            return False, None

        # Verify checksum
        current_checksum = self._calculate_checksum(Path(current_screenshot_path))
        if current_checksum == baseline.checksum:
            logger.debug(f"Screenshot matches baseline checksum for {test_name}")

        return True, baseline

    def get_baseline_stats(self) -> Dict[str, Any]:
        """Get statistics about baselines.

        Returns:
            Dictionary of statistics
        """
        total_baselines = len(self._baselines)
        total_snapshots = sum(len(s) for s in self._snapshots.values())

        # Group by content type
        content_types = {}
        for baseline in self._baselines.values():
            ct = baseline.content_type.value
            content_types[ct] = content_types.get(ct, 0) + 1

        # Group by tags
        tag_counts = {}
        for baseline in self._baselines.values():
            for tag in baseline.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Calculate storage size
        total_size = 0
        for baseline in self._baselines.values():
            file_path = Path(baseline.file_path)
            if file_path.exists():
                total_size += file_path.stat().st_size

        return {
            "total_baselines": total_baselines,
            "total_snapshots": total_snapshots,
            "content_type_breakdown": content_types,
            "tag_counts": tag_counts,
            "storage_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def cleanup_old_baselines(self, days: int = 90) -> int:
        """Remove baselines older than specified days.

        Args:
            days: Number of days

        Returns:
            Number of baselines removed
        """
        cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        to_remove = []

        for baseline_id, baseline in self._baselines.items():
            if baseline.updated_at.timestamp() < cutoff:
                to_remove.append(baseline_id)

        for baseline_id in to_remove:
            self.delete_baseline(baseline_id)

        logger.info(f"Cleaned up {len(to_remove)} old baselines")

        return len(to_remove)

    def export_baselines(self, export_dir: str) -> str:
        """Export all baselines to a directory.

        Args:
            export_dir: Directory to export to

        Returns:
            Path to export directory
        """
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)

        # Export baselines
        baselines_dir = export_path / "baselines"
        baselines_dir.mkdir(exist_ok=True)

        for baseline in self._baselines.values():
            src = Path(baseline.file_path)
            dst = baselines_dir / f"{baseline.id}.png"
            if src.exists():
                shutil.copy2(src, dst)

        # Export metadata
        metadata_export = export_path / "baselines.json"
        with open(metadata_export, "w") as f:
            json.dump(
                {
                    "baselines": [b.model_dump() for b in self._baselines.values()],
                    "exported_at": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
                default=str,
            )

        logger.info(f"Exported {len(self._baselines)} baselines to {export_path}")

        return str(export_path)

    def import_baselines(self, import_dir: str) -> int:
        """Import baselines from a directory.

        Args:
            import_dir: Directory to import from

        Returns:
            Number of baselines imported
        """
        import_path = Path(import_dir)

        if not import_path.exists():
            raise FileNotFoundError(f"Import directory not found: {import_path}")

        # Load metadata
        metadata_file = import_path / "baselines.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        with open(metadata_file, "r") as f:
            data = json.load(f)

        imported = 0

        for baseline_data in data.get("baselines", []):
            baseline = BaselineInfo.model_validate(baseline_data)

            # Check if source file exists
            src_path = import_path / "baselines" / f"{baseline.id}.png"
            if not src_path.exists():
                logger.warning(f"Baseline file not found: {src_path}")
                continue

            # Copy to baseline directory
            dst_path = self.baseline_dir / f"{baseline.id}.png"
            shutil.copy2(src_path, dst_path)

            # Update file path
            baseline.file_path = str(dst_path)

            # Store baseline
            self._baselines[baseline.id] = baseline
            imported += 1

        self._save_metadata()

        logger.info(f"Imported {imported} baselines from {import_path}")

        return imported

    def _generate_baseline_id(
        self,
        test_name: str,
        viewport: Optional[ViewportSize] = None,
    ) -> str:
        """Generate unique baseline ID.

        Args:
            test_name: Test name
            viewport: Viewport size

        Returns:
            Baseline ID
        """
        # Create unique string based on test name and viewport
        id_string = test_name
        if viewport:
            id_string += f"_{viewport.width}x{viewport.height}"

        # Hash and truncate
        hash_obj = hashlib.md5(id_string.encode())
        return f"baseline_{hash_obj.hexdigest()[:12]}"

    def _create_snapshot(self, baseline_id: str, description: str) -> BaselineSnapshot:
        """Create a snapshot of a baseline.

        Args:
            baseline_id: Baseline ID
            description: Snapshot description

        Returns:
            Created snapshot
        """
        baseline = self._baselines[baseline_id]

        # Generate snapshot ID
        snapshot_id = f"snapshot_{uuid.uuid4().hex[:12]}"

        # Copy baseline to snapshot
        snapshot_file = self.baseline_dir / "snapshots" / f"{snapshot_id}.png"
        snapshot_file.parent.mkdir(exist_ok=True)
        shutil.copy2(baseline.file_path, snapshot_file)

        # Create snapshot
        snapshot = BaselineSnapshot(
            id=snapshot_id,
            baseline_id=baseline_id,
            file_path=str(snapshot_file),
            description=description,
        )

        # Store snapshot
        if baseline_id not in self._snapshots:
            self._snapshots[baseline_id] = []
        self._snapshots[baseline_id].append(snapshot)

        return snapshot

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum.

        Args:
            file_path: Path to file

        Returns:
            Hex checksum
        """
        hash_obj = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def _get_current_user(self) -> str:
        """Get current user name.

        Returns:
            User name
        """
        import getpass

        try:
            return getpass.getuser()
        except:
            return "unknown"


class BaselineReviewer:
    """Review and approve visual test results."""

    def __init__(self, baseline_manager: BaselineManager):
        self.baseline_manager = baseline_manager

    def review_failures(
        self,
        test_results: List[Any],
    ) -> Dict[str, Any]:
        """Review failed visual tests and suggest actions.

        Args:
            test_results: List of test results

        Returns:
            Review report
        """
        report = {
            "total_failures": 0,
            "suggested_updates": [],
            "new_baselines": [],
            "requires_investigation": [],
        }

        for result in test_results:
            if not result.passed:
                report["total_failures"] += 1

                if not result.baseline:
                    # No baseline exists
                    report["new_baselines"].append(
                        {
                            "test_name": result.test_name,
                            "action": "create_baseline",
                        }
                    )
                elif result.comparison and result.comparison.differences:
                    # Check if differences are acceptable
                    significant_diffs = [
                        d for d in result.comparison.differences if not d.is_dynamic
                    ]

                    if not significant_diffs:
                        # All differences are dynamic, suggest update
                        report["suggested_updates"].append(
                            {
                                "test_name": result.test_name,
                                "baseline_id": result.baseline.id,
                                "action": "update_baseline",
                                "reason": "All differences are dynamic content",
                            }
                        )
                    else:
                        # Has significant differences
                        report["requires_investigation"].append(
                            {
                                "test_name": result.test_name,
                                "baseline_id": result.baseline.id,
                                "differences": len(significant_diffs),
                                "action": "manual_review",
                            }
                        )

        return report

    def batch_approve(
        self,
        test_names: List[str],
        screenshot_paths: List[str],
    ) -> List[BaselineInfo]:
        """Batch approve screenshots as baselines.

        Args:
            test_names: List of test names
            screenshot_paths: List of screenshot paths

        Returns:
            List of created/updated baselines
        """
        baselines = []

        for test_name, screenshot_path in zip(test_names, screenshot_paths):
            baseline = self.baseline_manager.approve_current_as_baseline(
                test_name, screenshot_path
            )
            baselines.append(baseline)

        return baselines
