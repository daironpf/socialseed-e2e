"""Flakiness Detector for ML-Based Predictive Test Selection.

This module implements machine learning models to detect flaky tests based on
historical execution data, test characteristics, and failure patterns.
"""

import json
import re
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from socialseed_e2e.ml.models import FlakinessReport, TestHistory, TestMetrics


class FlakinessDetector:
    """Detects flaky tests using ML-based analysis.

    This class analyzes test execution history to identify tests that exhibit
    flaky behavior - tests that pass and fail inconsistently without code changes.
    """

    def __init__(
        self,
        history_file: Optional[Path] = None,
        flakiness_threshold: float = 0.2,
    ):
        """Initialize the flakiness detector.

        Args:
            history_file: Path to store/load test history. If None, uses default.
            flakiness_threshold: Threshold for considering a test flaky (0.0-1.0)
        """
        self.history_file = history_file or Path(".e2e/test_history.json")
        self.flakiness_threshold = flakiness_threshold
        self._test_histories: Dict[str, TestHistory] = {}
        self._load_history()

    def _load_history(self) -> None:
        """Load test history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    for test_id, history_data in data.items():
                        self._test_histories[test_id] = TestHistory(**history_data)
            except (json.JSONDecodeError, IOError):
                self._test_histories = {}

    def _save_history(self) -> None:
        """Save test history to file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w") as f:
            data = {
                test_id: history.model_dump() for test_id, history in self._test_histories.items()
            }
            json.dump(data, f, indent=2, default=str)

    def record_test_execution(self, metrics: TestMetrics) -> None:
        """Record a test execution for history tracking.

        Args:
            metrics: Test execution metrics
        """
        test_id = metrics.test_id

        if test_id not in self._test_histories:
            self._test_histories[test_id] = TestHistory(
                test_id=test_id,
                test_name=metrics.test_name,
            )

        history = self._test_histories[test_id]

        # Update counts
        history.total_runs += 1
        if metrics.passed:
            history.pass_count += 1
        elif metrics.failed:
            history.fail_count += 1
        elif metrics.skipped:
            history.skip_count += 1

        # Update timing
        history.last_run = metrics.timestamp

        # Add to recent runs (keep last 50)
        history.runs.append(metrics)
        if len(history.runs) > 50:
            history.runs = history.runs[-50:]

        # Recalculate statistics
        self._update_history_stats(history)

        # Save history
        self._save_history()

    def _update_history_stats(self, history: TestHistory) -> None:
        """Update statistical calculations for test history.

        Args:
            history: Test history to update
        """
        if history.total_runs > 0:
            history.failure_rate = history.fail_count / history.total_runs

        # Calculate average duration
        durations = [r.duration_ms for r in history.runs if not r.skipped]
        if durations:
            history.avg_duration_ms = statistics.mean(durations)

        # Calculate recent failures (last 10 runs)
        recent_runs = history.runs[-10:] if len(history.runs) >= 10 else history.runs
        history.recent_failures = sum(1 for r in recent_runs if r.failed)

        # Calculate flakiness score
        history.flaky_score = self._calculate_flakiness_score(history)

    def _calculate_flakiness_score(self, history: TestHistory) -> float:
        """Calculate flakiness score for a test.

        The flakiness score is based on:
        - Pass/fail pattern volatility
        - Failure rate vs expected
        - Duration variance
        - Recent failure trend

        Args:
            history: Test execution history

        Returns:
            Flakiness score from 0.0 (not flaky) to 1.0 (very flaky)
        """
        if history.total_runs < 5:
            # Not enough data
            return 0.0

        scores = []

        # Score 1: Pass/fail volatility (alternating pattern)
        volatility_score = self._calculate_volatility(history.runs)
        scores.append(volatility_score * 0.35)

        # Score 2: Failure rate (tests with 10-90% failure rate are suspicious)
        failure_rate = history.failure_rate
        if 0.1 <= failure_rate <= 0.9:
            # Normalize to 0-1 range, peaking at 50%
            failure_score = 1.0 - abs(failure_rate - 0.5) * 2.0
            scores.append(failure_score * 0.25)

        # Score 3: Duration variance (high variance suggests instability)
        duration_variance_score = self._calculate_duration_variance(history.runs)
        scores.append(duration_variance_score * 0.20)

        # Score 4: Recent trend (recent failures indicate flakiness)
        if history.runs:
            recent_runs = history.runs[-10:]
            recent_pass_rate = sum(1 for r in recent_runs if r.passed) / len(recent_runs)
            if 0.2 <= recent_pass_rate <= 0.8:
                trend_score = 1.0 - abs(recent_pass_rate - 0.5) * 2.0
                scores.append(trend_score * 0.20)

        return min(sum(scores), 1.0)

    def _calculate_volatility(self, runs: List[TestMetrics]) -> float:
        """Calculate pass/fail volatility score.

        Args:
            runs: List of test runs

        Returns:
            Volatility score from 0.0 to 1.0
        """
        if len(runs) < 3:
            return 0.0

        # Count transitions between pass and fail
        transitions = 0
        for i in range(1, len(runs)):
            prev_passed = runs[i - 1].passed and not runs[i - 1].skipped
            curr_passed = runs[i].passed and not runs[i].skipped
            if prev_passed != curr_passed:
                transitions += 1

        # Normalize by number of possible transitions
        volatility = transitions / (len(runs) - 1)
        return min(volatility * 1.5, 1.0)  # Scale up slightly

    def _calculate_duration_variance(self, runs: List[TestMetrics]) -> float:
        """Calculate duration variance score.

        Args:
            runs: List of test runs

        Returns:
            Variance score from 0.0 to 1.0
        """
        durations = [r.duration_ms for r in runs if not r.skipped]

        if len(durations) < 3:
            return 0.0

        try:
            mean_duration = statistics.mean(durations)
            if mean_duration == 0:
                return 0.0

            std_dev = statistics.stdev(durations)
            coefficient_of_variation = std_dev / mean_duration

            # Higher variance = higher score
            return min(coefficient_of_variation, 1.0)
        except statistics.StatisticsError:
            return 0.0

    def detect_flaky_tests(
        self,
        min_runs: int = 5,
    ) -> FlakinessReport:
        """Detect flaky tests based on history.

        Args:
            min_runs: Minimum number of runs required for analysis

        Returns:
            FlakinessReport with detection results
        """
        flaky_tests = []

        for test_id, history in self._test_histories.items():
            if history.total_runs < min_runs:
                continue

            if history.flaky_score >= self.flakiness_threshold:
                flaky_info = {
                    "test_id": test_id,
                    "test_name": history.test_name,
                    "flaky_score": round(history.flaky_score, 3),
                    "failure_rate": round(history.failure_rate, 3),
                    "total_runs": history.total_runs,
                    "recent_failures": history.recent_failures,
                    "avg_duration_ms": round(history.avg_duration_ms, 2),
                    "recommendation": self._get_recommendation(history),
                }
                flaky_tests.append(flaky_info)

        # Sort by flakiness score (highest first)
        flaky_tests.sort(key=lambda x: x["flaky_score"], reverse=True)

        total_tests = len(self._test_histories)
        flaky_count = len(flaky_tests)
        flaky_rate = flaky_count / total_tests if total_tests > 0 else 0.0

        return FlakinessReport(
            total_tests=total_tests,
            flaky_tests=flaky_tests,
            flaky_count=flaky_count,
            flaky_rate=round(flaky_rate, 3),
            top_flaky_tests=[t["test_name"] for t in flaky_tests[:10]],
        )

    def _get_recommendation(self, history: TestHistory) -> str:
        """Get recommendation for a flaky test.

        Args:
            history: Test history

        Returns:
            Recommendation string
        """
        if history.flaky_score >= 0.8:
            return "quarantine"
        elif history.flaky_score >= 0.5:
            return "review_and_fix"
        elif history.failure_rate > 0.5:
            return "investigate_failures"
        else:
            return "monitor"

    def get_test_history(self, test_id: str) -> Optional[TestHistory]:
        """Get history for a specific test.

        Args:
            test_id: Test identifier

        Returns:
            TestHistory if found, None otherwise
        """
        return self._test_histories.get(test_id)

    def analyze_failure_pattern(
        self,
        test_id: str,
    ) -> Optional[Dict]:
        """Analyze failure patterns for a specific test.

        Args:
            test_id: Test identifier

        Returns:
            Dictionary with pattern analysis or None
        """
        history = self._test_histories.get(test_id)
        if not history or len(history.runs) < 3:
            return None

        failures = [r for r in history.runs if r.failed]
        if not failures:
            return None

        # Analyze error messages
        error_patterns = {}
        for failure in failures:
            if failure.error_message:
                # Simplify error message to find patterns
                simplified = self._simplify_error(failure.error_message)
                error_patterns[simplified] = error_patterns.get(simplified, 0) + 1

        # Find most common error pattern
        most_common_error = (
            max(error_patterns.items(), key=lambda x: x[1]) if error_patterns else ("unknown", 0)
        )

        # Analyze timing patterns
        failure_times = [r.timestamp for r in failures]
        timing_pattern = self._analyze_timing_pattern(failure_times)

        return {
            "test_id": test_id,
            "test_name": history.test_name,
            "failure_count": len(failures),
            "most_common_error": most_common_error[0],
            "error_pattern_frequency": most_common_error[1],
            "timing_pattern": timing_pattern,
            "consecutive_failures": self._count_consecutive_failures(history.runs),
            "intermittent_pattern": self._is_intermittent_pattern(history.runs),
        }

    def _simplify_error(self, error_message: str) -> str:
        """Simplify error message to find patterns.

        Args:
            error_message: Original error message

        Returns:
            Simplified error pattern
        """
        # Remove specific values (numbers, IDs, etc.)
        simplified = error_message
        simplified = re.sub(r"\d+", "<NUM>", simplified)
        simplified = re.sub(r"[a-f0-9]{8,}", "<HASH>", simplified, flags=re.IGNORECASE)
        simplified = re.sub(r"'[^']+'", "'<STR>'", simplified)
        simplified = re.sub(r'"[^"]+"', '"<STR>"', simplified)

        # Extract error type
        if ":" in simplified:
            simplified = simplified.split(":")[0]

        return simplified.strip()

    def _analyze_timing_pattern(self, timestamps: List[datetime]) -> str:
        """Analyze timing pattern of failures.

        Args:
            timestamps: List of failure timestamps

        Returns:
            Timing pattern description
        """
        if len(timestamps) < 3:
            return "insufficient_data"

        # Sort timestamps
        sorted_times = sorted(timestamps)

        # Calculate intervals between failures
        intervals = []
        for i in range(1, len(sorted_times)):
            interval = (sorted_times[i] - sorted_times[i - 1]).total_seconds()
            intervals.append(interval)

        if not intervals:
            return "unknown"

        # Check for patterns
        avg_interval = statistics.mean(intervals)

        if avg_interval < 3600:  # Less than 1 hour
            return "frequent_failures"
        elif avg_interval < 86400:  # Less than 1 day
            return "daily_pattern"
        elif avg_interval < 604800:  # Less than 1 week
            return "weekly_pattern"
        else:
            return "sporadic"

    def _count_consecutive_failures(self, runs: List[TestMetrics]) -> int:
        """Count the maximum consecutive failures.

        Args:
            runs: List of test runs

        Returns:
            Maximum number of consecutive failures
        """
        max_consecutive = 0
        current_consecutive = 0

        for run in runs:
            if run.failed:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _is_intermittent_pattern(self, runs: List[TestMetrics]) -> bool:
        """Check if failures follow an intermittent pattern.

        Args:
            runs: List of test runs

        Returns:
            True if pattern is intermittent
        """
        if len(runs) < 5:
            return False

        # Check for alternating pass/fail pattern
        recent_runs = runs[-10:]
        pass_fail_sequence = ["P" if r.passed else "F" for r in recent_runs if not r.skipped]

        if len(pass_fail_sequence) < 5:
            return False

        # Count transitions
        transitions = sum(
            1
            for i in range(1, len(pass_fail_sequence))
            if pass_fail_sequence[i] != pass_fail_sequence[i - 1]
        )

        # If more than 40% transitions, it's intermittent
        return transitions / len(pass_fail_sequence) > 0.4

    def clear_history(self) -> None:
        """Clear all test history."""
        self._test_histories = {}
        if self.history_file.exists():
            self.history_file.unlink()

    def export_history(self, output_path: Path) -> None:
        """Export test history to a file.

        Args:
            output_path: Path to export to
        """
        data = {test_id: history.model_dump() for test_id, history in self._test_histories.items()}

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def import_history(self, input_path: Path) -> None:
        """Import test history from a file.

        Args:
            input_path: Path to import from
        """
        with open(input_path, "r") as f:
            data = json.load(f)
            for test_id, history_data in data.items():
                self._test_histories[test_id] = TestHistory(**history_data)

        self._save_history()
