"""Data management and lifecycle for test data.

This module handles test data lifecycle, refresh automation,
and data subsetting.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import random
import string

from .models import (
    DataRefreshPolicy,
    DataQualityRule,
    DataQualityResult,
    DataGovernanceReport,
)


class DataLifecycleManager:
    """Manage test data lifecycle and refresh."""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize data lifecycle manager.

        Args:
            storage_path: Path to store data snapshots
        """
        self.storage_path = (
            Path(storage_path) if storage_path else Path("data_snapshots")
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.policies: Dict[str, DataRefreshPolicy] = {}

    def create_refresh_policy(
        self,
        name: str,
        frequency: str,
        retention_days: int,
        cleanup_strategy: str = "delete",
    ) -> DataRefreshPolicy:
        """Create a data refresh policy.

        Args:
            name: Policy name
            frequency: How often to refresh (daily, weekly, monthly)
            retention_days: How many days to keep data
            cleanup_strategy: Strategy for cleanup

        Returns:
            DataRefreshPolicy object
        """
        policy = DataRefreshPolicy(
            frequency=frequency,
            retention_days=retention_days,
            cleanup_strategy=cleanup_strategy,
            last_refresh=datetime.now(),
            next_refresh=self._calculate_next_refresh(frequency),
        )

        self.policies[name] = policy
        return policy

    def _calculate_next_refresh(self, frequency: str) -> datetime:
        """Calculate next refresh date based on frequency."""
        now = datetime.now()

        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)

        return now + timedelta(days=1)

    def snapshot_data(self, name: str, data: Any) -> Path:
        """Create a snapshot of test data.

        Args:
            name: Snapshot name
            data: Data to snapshot

        Returns:
            Path to snapshot file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.json"
        filepath = self.storage_path / filename

        snapshot = {
            "name": name,
            "timestamp": timestamp,
            "data": data,
        }

        filepath.write_text(json.dumps(snapshot, indent=2, default=str))
        return filepath

    def restore_snapshot(self, snapshot_path: str) -> Any:
        """Restore data from a snapshot.

        Args:
            snapshot_path: Path to snapshot file

        Returns:
            Restored data
        """
        filepath = Path(snapshot_path)

        if not filepath.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

        snapshot = json.loads(filepath.read_text())
        return snapshot.get("data")

    def cleanup_old_snapshots(self, name: str, retention_days: int):
        """Clean up old snapshots.

        Args:
            name: Snapshot name prefix
            retention_days: Number of days to retain
        """
        cutoff = datetime.now() - timedelta(days=retention_days)

        for filepath in self.storage_path.glob(f"{name}_*.json"):
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            if mtime < cutoff:
                filepath.unlink()

    def get_latest_snapshot(self, name: str) -> Optional[Path]:
        """Get the most recent snapshot.

        Args:
            name: Snapshot name

        Returns:
            Path to latest snapshot or None
        """
        snapshots = sorted(
            self.storage_path.glob(f"{name}_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        return snapshots[0] if snapshots else None


class DataSubsetGenerator:
    """Generate subsets of test data."""

    def __init__(self):
        """Initialize data subset generator."""
        self.subsets: Dict[str, Any] = {}

    def generate_subset(
        self, data: List[Any], size: int, strategy: str = "random"
    ) -> List[Any]:
        """Generate a subset of data.

        Args:
            data: Full dataset
            size: Subset size
            strategy: Selection strategy (random, first, last, slice)

        Returns:
            Subset of data
        """
        if size >= len(data):
            return data

        if strategy == "random":
            return random.sample(data, size)

        elif strategy == "first":
            return data[:size]

        elif strategy == "last":
            return data[-size:]

        elif strategy == "slice":
            step = len(data) // size
            return data[::step][:size]

        return data[:size]

    def generate_stratified_subset(
        self, data: List[Dict], stratify_field: str, size: int
    ) -> List[Dict]:
        """Generate a stratified subset maintaining field distribution.

        Args:
            data: Full dataset
            stratify_field: Field to use for stratification
            size: Subset size

        Returns:
            Stratified subset
        """
        groups: Dict[Any, List[Dict]] = {}

        for item in data:
            if isinstance(item, dict) and stratify_field in item:
                key = item[stratify_field]
                if key not in groups:
                    groups[key] = []
                groups[key].append(item)

        subset_size_per_group = max(1, size // len(groups))
        subset = []

        for group_key, group_data in groups.items():
            group_subset = self.generate_subset(group_data, subset_size_per_group)
            subset.extend(group_subset)

        return subset[:size]


class DataQualityValidator:
    """Validate test data quality."""

    def __init__(self):
        """Initialize data quality validator."""
        self.rules: List[DataQualityRule] = []

    def add_rule(self, rule: DataQualityRule):
        """Add a quality validation rule."""
        self.rules.append(rule)

    def validate_data(self, data: List[Dict]) -> List[DataQualityResult]:
        """Validate data against all rules.

        Args:
            data: Data to validate

        Returns:
            List of validation results
        """
        results = []

        for rule in self.rules:
            result = self._validate_rule(rule, data)
            results.append(result)

        return results

    def _validate_rule(
        self, rule: DataQualityRule, data: List[Dict]
    ) -> DataQualityResult:
        """Validate a single rule."""
        affected_count = 0

        for item in data:
            if not isinstance(item, dict):
                continue

            value = item.get(rule.field_name)

            if rule.rule_type == "not_null" and value is None:
                affected_count += 1

            elif rule.rule_type == "unique":
                duplicates = [
                    i
                    for i, x in enumerate(data)
                    if isinstance(x, dict) and x.get(rule.field_name) == value
                ]
                if len(duplicates) > 1:
                    affected_count += 1

            elif rule.rule_type == "range":
                min_val = rule.parameters.get("min")
                max_val = rule.parameters.get("max")
                if value is not None:
                    if (min_val is not None and value < min_val) or (
                        max_val is not None and value > max_val
                    ):
                        affected_count += 1

            elif rule.rule_type == "pattern":
                import re

                pattern = rule.parameters.get("pattern")
                if value is not None and pattern:
                    if not re.match(pattern, str(value)):
                        affected_count += 1

        passed = affected_count == 0

        return DataQualityResult(
            rule_name=rule.rule_name,
            passed=passed,
            message=f"{affected_count} records failed validation"
            if not passed
            else "All records valid",
            affected_records=affected_count,
        )

    def calculate_quality_score(self, results: List[DataQualityResult]) -> float:
        """Calculate overall data quality score.

        Args:
            results: Validation results

        Returns:
            Quality score (0-100)
        """
        if not results:
            return 100.0

        critical_rules = [r for r in results if r.is_critical]
        critical_failed = len([r for r in critical_rules if not r.passed])

        if critical_failed > 0:
            return 0.0

        non_critical_failed = len(
            [r for r in results if not r.passed and not r.is_critical]
        )
        total_rules = len(results)

        if total_rules == 0:
            return 100.0

        return ((total_rules - non_critical_failed) / total_rules) * 100


class DataGovernanceOrchestrator:
    """Orchestrate all data governance operations."""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize data governance orchestrator."""
        self.privacy_manager = None
        self.lifecycle_manager = DataLifecycleManager(storage_path)
        self.subset_generator = DataSubsetGenerator()
        self.quality_validator = DataQualityValidator()

    def generate_governance_report(self, data: List[Dict]) -> DataGovernanceReport:
        """Generate comprehensive data governance report.

        Args:
            data: Data to analyze

        Returns:
            DataGovernanceReport
        """
        from .privacy import PIIDetector, DataMasker

        pii_detector = PIIDetector()
        masker = DataMasker()

        total_records = len(data)
        pii_records = 0
        encrypted_records = 0

        for item in data:
            detected = pii_detector.detect_pii(item)
            if detected:
                pii_records += 1

        quality_results = self.quality_validator.validate_data(data)
        quality_score = self.quality_validator.calculate_quality_score(quality_results)

        violations = []
        if pii_records > 0:
            violations.append(f"Found PII in {pii_records} records")

        return DataGovernanceReport(
            total_records=total_records,
            pii_records=pii_records,
            encrypted_records=encrypted_records,
            compliant_records=total_records - pii_records,
            violations=violations,
            quality_score=quality_score,
        )
