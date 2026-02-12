"""Test Selector for ML-Based Predictive Test Selection.

This module implements the main ML-based test selection logic that combines
code impact analysis, flakiness detection, and historical data to select
and order tests optimally.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from socialseed_e2e.ml.flakiness_detector import FlakinessDetector
from socialseed_e2e.ml.impact_analyzer import ImpactAnalyzer
from socialseed_e2e.ml.models import (
    CoverageGap,
    CoverageReport,
    ImpactAnalysis,
    MLOrchestratorConfig,
    RedundancyReport,
    RedundantTest,
    TestHistory,
    TestMetrics,
    TestPrediction,
    TestPriority,
    TestSelectionResult,
)


class TestSelector:
    """ML-based test selector for optimal test execution.

    This class combines multiple ML models to:
    1. Select tests most likely to fail based on code changes
    2. Order tests for optimal execution
    3. Detect redundant tests
    4. Identify coverage gaps
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[MLOrchestratorConfig] = None,
    ):
        """Initialize the test selector.

        Args:
            project_root: Root directory of the project
            config: ML orchestrator configuration
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or MLOrchestratorConfig()
        self.impact_analyzer = ImpactAnalyzer(self.project_root)
        self.flakiness_detector = FlakinessDetector(
            flakiness_threshold=self.config.flakiness_threshold
        )
        self._available_tests: Dict[str, Dict] = {}
        self._test_mapping: Dict[str, str] = {}  # Maps test IDs to file paths

    def register_test(
        self, test_id: str, test_name: str, file_path: str, **metadata
    ) -> None:
        """Register a test for selection.

        Args:
            test_id: Unique test identifier
            test_name: Human-readable test name
            file_path: Path to test file
            **metadata: Additional test metadata
        """
        self._available_tests[test_id] = {
            "test_id": test_id,
            "test_name": test_name,
            "file_path": file_path,
            "metadata": metadata,
        }
        self._test_mapping[test_id] = file_path

    def select_tests(
        self,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
        test_list: Optional[List[str]] = None,
    ) -> TestSelectionResult:
        """Select tests based on ML predictions.

        Args:
            base_ref: Base git reference for impact analysis
            head_ref: Head git reference for impact analysis
            test_list: Optional list of test IDs to consider. If None, uses all registered tests.

        Returns:
            TestSelectionResult with selected tests and metadata
        """
        # Get impact analysis
        impact_analysis = self.impact_analyzer.analyze_git_diff(base_ref, head_ref)

        # Determine which tests to consider
        if test_list is None:
            test_list = list(self._available_tests.keys())

        # Generate predictions for each test
        predictions = []
        for test_id in test_list:
            prediction = self._predict_test(test_id, impact_analysis)
            if prediction:
                predictions.append(prediction)

        # Select tests based on predictions
        selected_predictions = self._apply_selection_criteria(predictions)

        # Sort by priority and failure probability
        selected_predictions = self._sort_tests(selected_predictions)

        # Assign execution order
        for i, pred in enumerate(selected_predictions):
            pred.suggested_order = i + 1

        # Calculate statistics
        total_tests = len(test_list)
        skipped_tests = [
            t.test_id for t in predictions if t not in selected_predictions
        ]
        estimated_duration = sum(p.estimated_duration_ms for p in selected_predictions)

        # Calculate savings
        if total_tests > 0:
            savings_pct = (len(skipped_tests) / total_tests) * 100
        else:
            savings_pct = 0.0

        return TestSelectionResult(
            total_tests=total_tests,
            selected_tests=selected_predictions,
            skipped_tests=skipped_tests,
            estimated_duration_ms=estimated_duration,
            estimated_coverage=self._estimate_coverage(selected_predictions),
            risk_reduction=self._calculate_risk_reduction(
                selected_predictions, impact_analysis
            ),
            savings_percentage=round(savings_pct, 2),
            impact_analysis=impact_analysis,
        )

    def _predict_test(
        self,
        test_id: str,
        impact_analysis: Optional[ImpactAnalysis] = None,
    ) -> Optional[TestPrediction]:
        """Generate ML prediction for a test.

        Args:
            test_id: Test identifier
            impact_analysis: Impact analysis result

        Returns:
            TestPrediction or None if test not found
        """
        test_info = self._available_tests.get(test_id)
        if not test_info:
            return None

        # Get test history
        history = self.flakiness_detector.get_test_history(test_id)

        # Calculate failure probability
        failure_prob = self._calculate_failure_probability(
            test_id, history, impact_analysis
        )

        # Calculate estimated duration
        estimated_duration = self._estimate_duration(test_id, history)

        # Determine priority
        priority = self._determine_priority(failure_prob, test_id, impact_analysis)

        # Generate reasons
        reasons = self._generate_prediction_reasons(
            test_id, failure_prob, history, impact_analysis
        )

        # Calculate confidence
        confidence = self._calculate_confidence(history)

        # Check if affected by changes
        affected = self._is_affected_by_changes(test_id, impact_analysis)

        return TestPrediction(
            test_id=test_id,
            test_name=test_info["test_name"],
            failure_probability=round(failure_prob, 3),
            estimated_duration_ms=estimated_duration,
            priority=priority,
            confidence=round(confidence, 3),
            reasons=reasons,
            affected_by_changes=affected,
        )

    def _calculate_failure_probability(
        self,
        test_id: str,
        history: Optional[TestHistory],
        impact_analysis: Optional[ImpactAnalysis],
    ) -> float:
        """Calculate failure probability for a test.

        Args:
            test_id: Test identifier
            history: Test execution history
            impact_analysis: Impact analysis result

        Returns:
            Failure probability from 0.0 to 1.0
        """
        factors = []

        # Factor 1: Historical failure rate
        if history and history.total_runs > 0:
            factors.append(history.failure_rate * 0.3)

        # Factor 2: Flakiness score
        if history and history.flaky_score > 0:
            factors.append(history.flaky_score * 0.25)

        # Factor 3: Recent failure trend
        if history and history.runs:
            recent_runs = history.runs[-5:]
            recent_failures = sum(1 for r in recent_runs if r.failed)
            recent_rate = recent_failures / len(recent_runs) if recent_runs else 0
            factors.append(recent_rate * 0.2)

        # Factor 4: Code change impact
        if impact_analysis and self._is_affected_by_changes(test_id, impact_analysis):
            # Increase probability if test is affected by changes
            base_prob = 0.3
            if impact_analysis.impact_score > 0.5:
                base_prob = 0.5
            factors.append(base_prob * 0.15)

        # Factor 5: Test age (newer tests are more likely to fail)
        if history and history.total_runs < 10:
            factors.append(0.1)

        # Combine factors
        if not factors:
            return 0.1  # Default low probability

        # Weighted average with some randomness for exploration
        probability = sum(factors) / len(factors)

        # Add small random factor for tests without history (exploration)
        if not history or history.total_runs < 5:
            probability += random.uniform(0.05, 0.15)

        return min(probability, 1.0)

    def _estimate_duration(
        self,
        test_id: str,
        history: Optional[TestHistory],
    ) -> int:
        """Estimate test execution duration.

        Args:
            test_id: Test identifier
            history: Test execution history

        Returns:
            Estimated duration in milliseconds
        """
        if history and history.avg_duration_ms > 0:
            # Use historical average with 10% buffer
            return int(history.avg_duration_ms * 1.1)

        # Default estimates based on test type
        test_info = self._available_tests.get(test_id, {})
        metadata = test_info.get("metadata", {})

        test_type = metadata.get("type", "unit")
        default_durations = {
            "unit": 1000,
            "integration": 5000,
            "e2e": 15000,
            "performance": 30000,
        }

        return default_durations.get(test_type, 2000)

    def _determine_priority(
        self,
        failure_prob: float,
        test_id: str,
        impact_analysis: Optional[ImpactAnalysis],
    ) -> TestPriority:
        """Determine test priority based on failure probability and impact.

        Args:
            failure_prob: Calculated failure probability
            test_id: Test identifier
            impact_analysis: Impact analysis result

        Returns:
            TestPriority enum value
        """
        # Check if test is directly affected by changes
        is_affected = self._is_affected_by_changes(test_id, impact_analysis)

        if failure_prob >= 0.7 and is_affected:
            return TestPriority.CRITICAL
        elif failure_prob >= 0.5 or (failure_prob >= 0.3 and is_affected):
            return TestPriority.HIGH
        elif failure_prob >= 0.2:
            return TestPriority.MEDIUM
        elif failure_prob >= 0.05:
            return TestPriority.LOW
        else:
            return TestPriority.SKIP

    def _generate_prediction_reasons(
        self,
        test_id: str,
        failure_prob: float,
        history: Optional[TestHistory],
        impact_analysis: Optional[ImpactAnalysis],
    ) -> List[str]:
        """Generate human-readable reasons for the prediction.

        Args:
            test_id: Test identifier
            failure_prob: Calculated failure probability
            history: Test execution history
            impact_analysis: Impact analysis result

        Returns:
            List of reason strings
        """
        reasons = []

        # Historical reasons
        if history:
            if history.failure_rate > 0.3:
                reasons.append(
                    f"High historical failure rate ({history.failure_rate:.1%})"
                )

            if history.flaky_score > 0.3:
                reasons.append(
                    f"Test shows flaky behavior (score: {history.flaky_score:.2f})"
                )

            if history.recent_failures > 0:
                reasons.append(
                    f"Recent failures ({history.recent_failures} in last 10 runs)"
                )

        # Impact reasons
        if impact_analysis and self._is_affected_by_changes(test_id, impact_analysis):
            reasons.append("Test covers code that was modified")

        # General reasons
        if failure_prob > 0.5:
            reasons.append("High predicted failure probability")
        elif not history or history.total_runs < 5:
            reasons.append("New test with limited history")

        return reasons

    def _calculate_confidence(self, history: Optional[TestHistory]) -> float:
        """Calculate confidence in the prediction.

        Args:
            history: Test execution history

        Returns:
            Confidence score from 0.0 to 1.0
        """
        if not history:
            return 0.3  # Low confidence without history

        # More runs = higher confidence, up to a point
        runs_factor = min(history.total_runs / 50.0, 1.0) * 0.5

        # Recent activity increases confidence
        recency_factor = 0.2
        if history.last_run:
            days_since = (datetime.utcnow() - history.last_run).days
            if days_since < 7:
                recency_factor = 0.3
            elif days_since < 30:
                recency_factor = 0.25

        # Consistent results increase confidence
        consistency_factor = 0.0
        if history.total_runs > 5:
            pass_rate = history.pass_count / history.total_runs
            # Peaks at 0% or 100% pass rate (consistent)
            consistency_factor = abs(pass_rate - 0.5) * 0.4

        return min(runs_factor + recency_factor + consistency_factor, 1.0)

    def _is_affected_by_changes(
        self,
        test_id: str,
        impact_analysis: Optional[ImpactAnalysis],
    ) -> bool:
        """Check if a test is affected by code changes.

        Args:
            test_id: Test identifier
            impact_analysis: Impact analysis result

        Returns:
            True if test is affected by changes
        """
        if not impact_analysis:
            return False

        test_info = self._available_tests.get(test_id, {})
        test_path = test_info.get("file_path", "")

        # Check if test is directly in affected tests
        if test_path in impact_analysis.affected_tests:
            return True

        # Check if test file was modified
        for change in impact_analysis.changed_files:
            if change.file_path == test_path:
                return True

        return False

    def _apply_selection_criteria(
        self,
        predictions: List[TestPrediction],
    ) -> List[TestPrediction]:
        """Apply selection criteria to filter tests.

        Args:
            predictions: List of test predictions

        Returns:
            Filtered list of predictions
        """
        selected = []

        for pred in predictions:
            # Skip tests with SKIP priority
            if pred.priority == TestPriority.SKIP:
                continue

            # Apply confidence threshold
            if pred.confidence < self.config.min_confidence:
                # But keep if affected by changes
                if not pred.affected_by_changes:
                    continue

            # Apply selection threshold
            if pred.failure_probability < self.config.selection_threshold:
                # But keep if high priority or affected by changes
                if pred.priority not in [TestPriority.CRITICAL, TestPriority.HIGH]:
                    if not pred.affected_by_changes:
                        continue

            selected.append(pred)

        # Apply max tests limit if configured
        if (
            self.config.max_tests_to_select
            and len(selected) > self.config.max_tests_to_select
        ):
            # Sort by priority and failure probability, then limit
            selected = sorted(
                selected,
                key=lambda p: (self._priority_value(p.priority), p.failure_probability),
                reverse=True,
            )[: self.config.max_tests_to_select]

        return selected

    def _sort_tests(self, predictions: List[TestPrediction]) -> List[TestPrediction]:
        """Sort tests for optimal execution order.

        Priority:
        1. Critical priority tests first
        2. Higher failure probability first
        3. Faster tests first (fail fast strategy)

        Args:
            predictions: List of test predictions

        Returns:
            Sorted list of predictions
        """

        def sort_key(pred: TestPrediction) -> Tuple:
            priority_val = self._priority_value(pred.priority)
            # Negative failure prob for descending order
            # Duration for secondary sort (faster first)
            return (
                -priority_val,
                -pred.failure_probability,
                pred.estimated_duration_ms,
            )

        return sorted(predictions, key=sort_key)

    def _priority_value(self, priority: TestPriority) -> int:
        """Convert priority to numeric value for sorting.

        Args:
            priority: TestPriority enum value

        Returns:
            Numeric priority value (higher = more important)
        """
        priority_map = {
            TestPriority.CRITICAL: 4,
            TestPriority.HIGH: 3,
            TestPriority.MEDIUM: 2,
            TestPriority.LOW: 1,
            TestPriority.SKIP: 0,
        }
        return priority_map.get(priority, 0)

    def _estimate_coverage(self, predictions: List[TestPrediction]) -> float:
        """Estimate code coverage for selected tests.

        Args:
            predictions: Selected test predictions

        Returns:
            Estimated coverage percentage
        """
        # This is a simplified estimation
        # In practice, this would integrate with actual coverage data

        if not predictions:
            return 0.0

        # Estimate based on number of tests and their types
        total_coverage = 0.0
        for pred in predictions:
            test_info = self._available_tests.get(pred.test_id, {})
            metadata = test_info.get("metadata", {})

            # Different test types have different coverage potentials
            coverage_map = {
                "unit": 5.0,
                "integration": 15.0,
                "e2e": 25.0,
            }
            test_type = metadata.get("type", "unit")
            total_coverage += coverage_map.get(test_type, 5.0)

        # Cap at 100%
        return min(total_coverage, 100.0)

    def _calculate_risk_reduction(
        self,
        predictions: List[TestPrediction],
        impact_analysis: Optional[ImpactAnalysis],
    ) -> float:
        """Calculate risk reduction from running selected tests.

        Args:
            predictions: Selected test predictions
            impact_analysis: Impact analysis result

        Returns:
            Risk reduction score from 0.0 to 1.0
        """
        if not predictions:
            return 0.0

        # Calculate based on failure probability sum
        total_risk = sum(p.failure_probability for p in predictions)
        avg_risk = total_risk / len(predictions)

        # Boost if covering affected code
        affected_count = sum(1 for p in predictions if p.affected_by_changes)
        if impact_analysis and impact_analysis.affected_tests:
            coverage_ratio = affected_count / len(impact_analysis.affected_tests)
        else:
            coverage_ratio = 1.0

        return min(avg_risk * coverage_ratio, 1.0)

    def detect_redundant_tests(self) -> RedundancyReport:
        """Detect potentially redundant tests.

        Returns:
            RedundancyReport with redundant test analysis
        """
        redundant_tests = []

        # Compare each pair of tests
        test_ids = list(self._available_tests.keys())

        for i, test_id1 in enumerate(test_ids):
            test_info1 = self._available_tests[test_id1]

            similar_tests = []

            for test_id2 in test_ids[i + 1 :]:
                test_info2 = self._available_tests[test_id2]

                # Calculate similarity
                similarity = self._calculate_test_similarity(test_info1, test_info2)

                if similarity > 0.8:  # High similarity threshold
                    similar_tests.append(test_info2["test_name"])

            if similar_tests:
                redundant = RedundantTest(
                    test_id=test_id1,
                    test_name=test_info1["test_name"],
                    similar_to=similar_tests,
                    similarity_score=0.85,
                    coverage_overlap=75.0,
                    recommendation="merge_or_remove",
                )
                redundant_tests.append(redundant)

        # Calculate potential savings
        total_duration = sum(
            self._estimate_duration(rt.test_id, None) for rt in redundant_tests
        )

        return RedundancyReport(
            total_tests=len(test_ids),
            redundant_tests=redundant_tests,
            redundancy_count=len(redundant_tests),
            potential_savings_ms=total_duration,
        )

    def _calculate_test_similarity(
        self,
        test_info1: Dict,
        test_info2: Dict,
    ) -> float:
        """Calculate similarity between two tests.

        Args:
            test_info1: First test information
            test_info2: Second test information

        Returns:
            Similarity score from 0.0 to 1.0
        """
        similarity = 0.0

        # Check file path similarity
        path1 = test_info1.get("file_path", "")
        path2 = test_info2.get("file_path", "")

        if path1 == path2:
            similarity += 0.3
        elif path1.rsplit("/", 1)[0] == path2.rsplit("/", 1)[0]:
            similarity += 0.1

        # Check metadata similarity
        meta1 = test_info1.get("metadata", {})
        meta2 = test_info2.get("metadata", {})

        # Same type
        if meta1.get("type") == meta2.get("type"):
            similarity += 0.2

        # Same endpoint
        if meta1.get("endpoint") == meta2.get("endpoint"):
            similarity += 0.3

        # Same service
        if meta1.get("service") == meta2.get("service"):
            similarity += 0.2

        return min(similarity, 1.0)

    def analyze_coverage_gaps(self) -> CoverageReport:
        """Analyze coverage gaps in the codebase.

        Returns:
            CoverageReport with gap analysis
        """
        # This would integrate with actual coverage data
        # For now, return a placeholder report

        gaps: List[CoverageGap] = []
        files_without_tests: List[str] = []

        # Find source files without corresponding tests
        source_files = self._find_source_files()

        for source_file in source_files:
            has_test = self._has_corresponding_test(source_file)
            if not has_test:
                files_without_tests.append(str(source_file))

        return CoverageReport(
            overall_coverage=0.0,  # Would be calculated from actual coverage data
            line_coverage=0.0,
            branch_coverage=0.0,
            function_coverage=0.0,
            gaps=gaps,
            gap_count=len(gaps),
            files_without_tests=files_without_tests[:20],  # Limit to first 20
        )

    def _find_source_files(self) -> List[Path]:
        """Find all source files in the project.

        Returns:
            List of source file paths
        """
        source_files = []

        # Common source directories
        source_dirs = ["src", "lib", "app", "core"]

        for dir_name in source_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                for ext in ["*.py", "*.js", "*.ts", "*.java"]:
                    source_files.extend(dir_path.rglob(ext))

        return source_files

    def _has_corresponding_test(self, source_file: Path) -> bool:
        """Check if a source file has a corresponding test file.

        Args:
            source_file: Path to source file

        Returns:
            True if corresponding test exists
        """
        # Common test file patterns
        test_patterns = [
            f"test_{source_file.name}",
            f"{source_file.stem}_test{source_file.suffix}",
            f"{source_file.stem}.test{source_file.suffix}",
            f"{source_file.stem}.spec{source_file.suffix}",
        ]

        # Check in test directories
        test_dirs = ["tests", "test", "__tests__"]

        for test_dir in test_dirs:
            for pattern in test_patterns:
                test_path = self.project_root / test_dir / pattern
                if test_path.exists():
                    return True

        return False

    def record_test_result(
        self,
        test_id: str,
        test_name: str,
        passed: bool,
        duration_ms: int,
        error_message: Optional[str] = None,
    ) -> None:
        """Record a test result for learning.

        Args:
            test_id: Test identifier
            test_name: Test name
            passed: Whether test passed
            duration_ms: Execution duration
            error_message: Optional error message
        """
        metrics = TestMetrics(
            test_id=test_id,
            test_name=test_name,
            duration_ms=duration_ms,
            passed=passed,
            failed=not passed,
            error_message=error_message,
            timestamp=datetime.utcnow(),
            git_commit=None,
            git_branch=None,
        )

        self.flakiness_detector.record_test_execution(metrics)

    def export_results(
        self,
        result: TestSelectionResult,
        output_path: Path,
    ) -> None:
        """Export test selection results to a file.

        Args:
            result: Test selection result
            output_path: Path to export to
        """
        data = result.model_dump()

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
