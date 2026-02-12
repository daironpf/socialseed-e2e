"""Unit tests for FlakinessDetector.

Tests for the flaky test detection functionality.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from socialseed_e2e.ml.flakiness_detector import FlakinessDetector
from socialseed_e2e.ml.models import TestMetrics


class TestFlakinessDetectorInit:
    """Test FlakinessDetector initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        detector = FlakinessDetector()
        assert detector.flakiness_threshold == 0.2
        assert detector.history_file.name == "test_history.json"

    def test_init_with_custom_values(self, tmp_path):
        """Test initialization with custom values."""
        history_file = tmp_path / "custom_history.json"
        detector = FlakinessDetector(
            history_file=history_file,
            flakiness_threshold=0.3,
        )
        assert detector.flakiness_threshold == 0.3
        assert detector.history_file == history_file


class TestRecordTestExecution:
    """Test recording test executions."""

    def test_record_passed_test(self, tmp_path):
        """Test recording a passed test."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        metrics = TestMetrics(
            test_id="test_001",
            test_name="test_login",
            duration_ms=1000,
            passed=True,
            failed=False,
        )

        detector.record_test_execution(metrics)

        history = detector.get_test_history("test_001")
        assert history is not None
        assert history.total_runs == 1
        assert history.pass_count == 1
        assert history.fail_count == 0

    def test_record_failed_test(self, tmp_path):
        """Test recording a failed test."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        metrics = TestMetrics(
            test_id="test_001",
            test_name="test_login",
            duration_ms=1000,
            passed=False,
            failed=True,
            error_message="Assertion error",
        )

        detector.record_test_execution(metrics)

        history = detector.get_test_history("test_001")
        assert history.fail_count == 1
        assert history.failure_rate == 1.0

    def test_record_multiple_executions(self, tmp_path):
        """Test recording multiple test executions."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        # Record 5 passed and 5 failed
        for i in range(10):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000,
                passed=i < 5,
                failed=i >= 5,
            )
            detector.record_test_execution(metrics)

        history = detector.get_test_history("test_001")
        assert history.total_runs == 10
        assert history.pass_count == 5
        assert history.fail_count == 5
        assert history.failure_rate == 0.5

    def test_record_persists_to_file(self, tmp_path):
        """Test that records persist to file."""
        history_file = tmp_path / "history.json"

        # Create detector and record
        detector1 = FlakinessDetector(history_file=history_file)
        metrics = TestMetrics(
            test_id="test_001",
            test_name="test_login",
            duration_ms=1000,
            passed=True,
            failed=False,
        )
        detector1.record_test_execution(metrics)

        # Create new detector and verify data loaded
        detector2 = FlakinessDetector(history_file=history_file)
        history = detector2.get_test_history("test_001")
        assert history is not None
        assert history.total_runs == 1


class TestFlakinessScore:
    """Test flakiness score calculation."""

    def test_flaky_score_with_alternating_pattern(self, tmp_path):
        """Test flakiness score with alternating pass/fail pattern."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        # Record alternating pattern: pass, fail, pass, fail, ...
        for i in range(10):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000 + (i % 3) * 100,  # Varying duration
                passed=i % 2 == 0,
                failed=i % 2 == 1,
            )
            detector.record_test_execution(metrics)

        history = detector.get_test_history("test_001")
        assert history.flaky_score > 0.3  # Should have high flakiness

    def test_flaky_score_consistent_pass(self, tmp_path):
        """Test flakiness score with consistent passes."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        for i in range(10):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000,
                passed=True,
                failed=False,
            )
            detector.record_test_execution(metrics)

        history = detector.get_test_history("test_001")
        assert history.flaky_score < 0.2  # Should have low flakiness

    def test_flaky_score_not_enough_data(self, tmp_path):
        """Test flakiness score with insufficient data."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        # Only 3 runs
        for i in range(3):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000,
                passed=i % 2 == 0,
                failed=i % 2 == 1,
            )
            detector.record_test_execution(metrics)

        history = detector.get_test_history("test_001")
        assert history.flaky_score == 0.0  # Should be 0 with < 5 runs


class TestDetectFlakyTests:
    """Test flaky test detection."""

    def test_detect_no_flaky_tests(self, tmp_path):
        """Test detection with no flaky tests."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        # Add consistent tests
        for i in range(10):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000,
                passed=True,
                failed=False,
            )
            detector.record_test_execution(metrics)

        report = detector.detect_flaky_tests()
        assert report.flaky_count == 0
        assert report.flaky_rate == 0.0

    def test_detect_flaky_tests(self, tmp_path):
        """Test detection with flaky tests."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        # Add flaky test (alternating)
        for i in range(10):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000,
                passed=i % 2 == 0,
                failed=i % 2 == 1,
            )
            detector.record_test_execution(metrics)

        report = detector.detect_flaky_tests()
        assert report.flaky_count >= 1
        assert report.flaky_rate > 0.0
        assert "test_login" in report.top_flaky_tests

    def test_flaky_test_recommendation(self, tmp_path):
        """Test flaky test recommendations."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        # Add very flaky test
        for i in range(10):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000,
                passed=i % 2 == 0,
                failed=i % 2 == 1,
            )
            detector.record_test_execution(metrics)

        report = detector.detect_flaky_tests(min_runs=5)

        if report.flaky_tests:
            flaky_info = report.flaky_tests[0]
            assert "recommendation" in flaky_info


class TestAnalyzeFailurePattern:
    """Test failure pattern analysis."""

    def test_analyze_no_failures(self, tmp_path):
        """Test analysis with no failures."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        for i in range(5):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000,
                passed=True,
                failed=False,
            )
            detector.record_test_execution(metrics)

        pattern = detector.analyze_failure_pattern("test_001")
        assert pattern is None

    def test_analyze_failure_pattern(self, tmp_path):
        """Test analysis with failures."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        for i in range(5):
            metrics = TestMetrics(
                test_id="test_001",
                test_name="test_login",
                duration_ms=1000,
                passed=False,
                failed=True,
                error_message="Connection timeout" if i % 2 == 0 else "Assertion failed",
            )
            detector.record_test_execution(metrics)

        pattern = detector.analyze_failure_pattern("test_001")
        assert pattern is not None
        assert pattern["test_id"] == "test_001"
        assert pattern["failure_count"] == 5


class TestHistoryManagement:
    """Test history management operations."""

    def test_clear_history(self, tmp_path):
        """Test clearing history."""
        history_file = tmp_path / "history.json"
        detector = FlakinessDetector(history_file=history_file)

        metrics = TestMetrics(
            test_id="test_001",
            test_name="test_login",
            duration_ms=1000,
            passed=True,
            failed=False,
        )
        detector.record_test_execution(metrics)

        detector.clear_history()

        assert detector.get_test_history("test_001") is None
        assert not history_file.exists()

    def test_export_import_history(self, tmp_path):
        """Test exporting and importing history."""
        history_file = tmp_path / "history.json"
        export_file = tmp_path / "export.json"

        # Create and populate detector
        detector1 = FlakinessDetector(history_file=history_file)
        metrics = TestMetrics(
            test_id="test_001",
            test_name="test_login",
            duration_ms=1000,
            passed=True,
            failed=False,
        )
        detector1.record_test_execution(metrics)

        # Export
        detector1.export_history(export_file)
        assert export_file.exists()

        # Import to new detector
        detector2 = FlakinessDetector(history_file=tmp_path / "history2.json")
        detector2.import_history(export_file)

        history = detector2.get_test_history("test_001")
        assert history is not None
        assert history.total_runs == 1
