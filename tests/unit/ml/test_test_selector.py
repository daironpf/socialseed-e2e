"""Unit tests for TestSelector.

Tests for the ML-based test selection functionality.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from socialseed_e2e.ml.models import (
    MLOrchestratorConfig,
    TestHistory,
    TestMetrics,
    TestPrediction,
    TestPriority,
)
from socialseed_e2e.ml.test_selector import TestSelector


class TestTestSelectorInit:
    """Test TestSelector initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        selector = TestSelector()
        assert selector.project_root == Path.cwd()
        assert selector.config is not None

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = MLOrchestratorConfig(
            selection_threshold=0.5,
            max_tests_to_select=20,
        )
        selector = TestSelector(config=config)
        assert selector.config.selection_threshold == 0.5
        assert selector.config.max_tests_to_select == 20


class TestRegisterTest:
    """Test test registration."""

    def test_register_basic_test(self):
        """Test registering a basic test."""
        selector = TestSelector()
        selector.register_test(
            test_id="test_001",
            test_name="test_login",
            file_path="tests/test_login.py",
        )

        assert "test_001" in selector._available_tests
        assert selector._available_tests["test_001"]["test_name"] == "test_login"

    def test_register_test_with_metadata(self):
        """Test registering a test with metadata."""
        selector = TestSelector()
        selector.register_test(
            test_id="test_001",
            test_name="test_login",
            file_path="tests/test_login.py",
            type="integration",
            endpoint="/api/login",
            service="auth",
        )

        metadata = selector._available_tests["test_001"]["metadata"]
        assert metadata["type"] == "integration"
        assert metadata["endpoint"] == "/api/login"


class TestPredictTest:
    """Test test prediction generation."""

    def test_predict_new_test(self, tmp_path):
        """Test prediction for a new test without history."""
        from socialseed_e2e.ml.flakiness_detector import FlakinessDetector

        history_file = tmp_path / "test_history.json"
        flakiness_detector = FlakinessDetector(history_file=history_file)
        selector = TestSelector(project_root=tmp_path)
        selector.flakiness_detector = flakiness_detector

        selector.register_test(
            test_id="test_001",
            test_name="test_login",
            file_path="tests/test_login.py",
        )

        prediction = selector._predict_test("test_001")

        assert prediction is not None
        assert prediction.test_id == "test_001"
        assert prediction.failure_probability > 0  # Should have some default probability
        assert prediction.confidence < 0.8  # Lower confidence for new test

    def test_predict_with_history(self, tmp_path):
        """Test prediction with test history."""
        from socialseed_e2e.ml.flakiness_detector import FlakinessDetector

        history_file = tmp_path / "test_history.json"
        flakiness_detector = FlakinessDetector(history_file=history_file)
        selector = TestSelector(project_root=tmp_path)
        selector.flakiness_detector = flakiness_detector

        selector.register_test(
            test_id="test_001",
            test_name="test_login",
            file_path="tests/test_login.py",
        )

        # Add history
        for i in range(10):
            selector.record_test_result(
                test_id="test_001",
                test_name="test_login",
                passed=i < 3,  # 7 failures, 3 passes
                duration_ms=1000,
            )

        prediction = selector._predict_test("test_001")

        assert prediction.failure_probability > 0.1  # Should have some failure probability
        assert prediction.confidence > 0.3  # Should have reasonable confidence

    def test_predict_unknown_test(self):
        """Test prediction for unknown test."""
        selector = TestSelector()
        prediction = selector._predict_test("unknown_test")
        assert prediction is None


class TestCalculateFailureProbability:
    """Test failure probability calculation."""

    def test_probability_with_no_history(self):
        """Test probability calculation with no history."""
        selector = TestSelector()
        prob = selector._calculate_failure_probability("test_001", None, None)
        assert 0.0 <= prob <= 1.0

    def test_probability_with_high_failure_rate(self):
        """Test probability with high failure rate."""
        selector = TestSelector()
        history = TestHistory(
            test_id="test_001",
            test_name="test_login",
            total_runs=10,
            pass_count=2,
            fail_count=8,
            failure_rate=0.8,
            flaky_score=0.6,
            runs=[
                TestMetrics(
                    test_id="test_001",
                    test_name="test_login",
                    duration_ms=1000,
                    passed=i % 2 == 0,  # Mix of passes and failures
                    failed=i % 2 == 1,
                    timestamp=datetime.utcnow(),
                )
                for i in range(10)
            ],
        )
        prob = selector._calculate_failure_probability("test_001", history, None)
        # With high failure rate and flaky score, should have elevated probability
        assert prob > 0.15

    def test_probability_with_low_failure_rate(self):
        """Test probability with low failure rate."""
        selector = TestSelector()
        history = TestHistory(
            test_id="test_001",
            test_name="test_login",
            total_runs=10,
            fail_count=1,
            failure_rate=0.1,
        )
        prob = selector._calculate_failure_probability("test_001", history, None)
        assert prob < 0.5


class TestDeterminePriority:
    """Test priority determination."""

    def test_critical_priority(self):
        """Test critical priority assignment."""
        selector = TestSelector()
        # Register the test with a file path
        selector.register_test(
            test_id="test_001",
            test_name="test_login",
            file_path="tests/test_login.py",
        )
        # Create a mock impact analysis where test is affected
        mock_impact = Mock()
        mock_impact.affected_tests = ["tests/test_login.py"]
        mock_impact.changed_files = []
        priority = selector._determine_priority(0.8, "test_001", mock_impact)
        assert priority == TestPriority.CRITICAL

    def test_high_priority(self):
        """Test high priority assignment."""
        selector = TestSelector()
        priority = selector._determine_priority(0.6, "test_001", None)
        assert priority == TestPriority.HIGH

    def test_medium_priority(self):
        """Test medium priority assignment."""
        selector = TestSelector()
        priority = selector._determine_priority(0.3, "test_001", None)
        assert priority == TestPriority.MEDIUM

    def test_low_priority(self):
        """Test low priority assignment."""
        selector = TestSelector()
        priority = selector._determine_priority(0.1, "test_001", None)
        assert priority == TestPriority.LOW

    def test_skip_priority(self):
        """Test skip priority for very low probability."""
        selector = TestSelector()
        priority = selector._determine_priority(0.01, "test_001", None)
        assert priority == TestPriority.SKIP


class TestApplySelectionCriteria:
    """Test selection criteria application."""

    def test_select_high_priority_tests(self):
        """Test selecting high priority tests."""
        selector = TestSelector()
        predictions = [
            TestPrediction(
                test_id="t1",
                test_name="test1",
                failure_probability=0.8,
                estimated_duration_ms=1000,
                priority=TestPriority.CRITICAL,
                confidence=0.9,
            ),
            TestPrediction(
                test_id="t2",
                test_name="test2",
                failure_probability=0.1,
                estimated_duration_ms=1000,
                priority=TestPriority.SKIP,
                confidence=0.9,
            ),
        ]

        selected = selector._apply_selection_criteria(predictions)
        assert len(selected) == 1
        assert selected[0].test_id == "t1"

    def test_select_affected_tests(self):
        """Test selecting tests affected by changes."""
        selector = TestSelector()
        predictions = [
            TestPrediction(
                test_id="t1",
                test_name="test1",
                failure_probability=0.1,
                estimated_duration_ms=1000,
                priority=TestPriority.LOW,
                confidence=0.5,
                affected_by_changes=True,
            ),
            TestPrediction(
                test_id="t2",
                test_name="test2",
                failure_probability=0.1,
                estimated_duration_ms=1000,
                priority=TestPriority.LOW,
                confidence=0.5,
                affected_by_changes=False,
            ),
        ]

        selected = selector._apply_selection_criteria(predictions)
        assert len(selected) == 1
        assert selected[0].test_id == "t1"

    def test_respect_max_tests_limit(self):
        """Test respecting maximum tests limit."""
        config = MLOrchestratorConfig(max_tests_to_select=2)
        selector = TestSelector(config=config)

        predictions = [
            TestPrediction(
                test_id=f"t{i}",
                test_name=f"test{i}",
                failure_probability=0.5 + i * 0.05,
                estimated_duration_ms=1000,
                priority=TestPriority.HIGH,
                confidence=0.9,
            )
            for i in range(5)
        ]

        selected = selector._apply_selection_criteria(predictions)
        assert len(selected) == 2


class TestSortTests:
    """Test test sorting."""

    def test_sort_by_priority(self):
        """Test sorting by priority."""
        selector = TestSelector()
        predictions = [
            TestPrediction(
                test_id="t1",
                test_name="test1",
                failure_probability=0.5,
                estimated_duration_ms=1000,
                priority=TestPriority.LOW,
            ),
            TestPrediction(
                test_id="t2",
                test_name="test2",
                failure_probability=0.5,
                estimated_duration_ms=1000,
                priority=TestPriority.CRITICAL,
            ),
        ]

        sorted_tests = selector._sort_tests(predictions)
        assert sorted_tests[0].test_id == "t2"  # Critical should come first

    def test_sort_by_failure_probability(self):
        """Test sorting by failure probability."""
        selector = TestSelector()
        predictions = [
            TestPrediction(
                test_id="t1",
                test_name="test1",
                failure_probability=0.3,
                estimated_duration_ms=1000,
                priority=TestPriority.HIGH,
            ),
            TestPrediction(
                test_id="t2",
                test_name="test2",
                failure_probability=0.8,
                estimated_duration_ms=1000,
                priority=TestPriority.HIGH,
            ),
        ]

        sorted_tests = selector._sort_tests(predictions)
        assert sorted_tests[0].test_id == "t2"  # Higher failure prob should come first


class TestCalculateTestSimilarity:
    """Test test similarity calculation."""

    def test_similar_same_endpoint(self):
        """Test similarity for tests with same endpoint."""
        selector = TestSelector()
        test1 = {
            "test_id": "t1",
            "test_name": "test1",
            "file_path": "tests/test1.py",
            "metadata": {"endpoint": "/api/login", "type": "integration"},
        }
        test2 = {
            "test_id": "t2",
            "test_name": "test2",
            "file_path": "tests/test2.py",
            "metadata": {"endpoint": "/api/login", "type": "integration"},
        }

        similarity = selector._calculate_test_similarity(test1, test2)
        assert similarity > 0.5

    def test_different_tests(self):
        """Test similarity for different tests."""
        selector = TestSelector()
        test1 = {
            "test_id": "t1",
            "test_name": "test1",
            "file_path": "tests/auth/test1.py",
            "metadata": {"endpoint": "/api/login", "type": "integration"},
        }
        test2 = {
            "test_id": "t2",
            "test_name": "test2",
            "file_path": "tests/payment/test2.py",
            "metadata": {"endpoint": "/api/pay", "type": "integration"},
        }

        similarity = selector._calculate_test_similarity(test1, test2)
        assert similarity < 0.5


class TestRecordTestResult:
    """Test recording test results."""

    def test_record_result_updates_history(self, tmp_path):
        """Test that recording updates history."""
        from socialseed_e2e.ml.flakiness_detector import FlakinessDetector

        history_file = tmp_path / "test_history.json"
        flakiness_detector = FlakinessDetector(history_file=history_file)
        selector = TestSelector(project_root=tmp_path)
        selector.flakiness_detector = flakiness_detector

        selector.record_test_result(
            test_id="test_001",
            test_name="test_login",
            passed=True,
            duration_ms=1000,
        )

        history = selector.flakiness_detector.get_test_history("test_001")
        assert history is not None
        assert history.total_runs == 1

    def test_record_failed_result(self, tmp_path):
        """Test recording a failed result."""
        from socialseed_e2e.ml.flakiness_detector import FlakinessDetector

        history_file = tmp_path / "test_history.json"
        flakiness_detector = FlakinessDetector(history_file=history_file)
        selector = TestSelector(project_root=tmp_path)
        selector.flakiness_detector = flakiness_detector

        selector.record_test_result(
            test_id="test_001",
            test_name="test_login",
            passed=False,
            duration_ms=1000,
            error_message="Timeout",
        )

        history = selector.flakiness_detector.get_test_history("test_001")
        assert history.fail_count == 1


class TestExportResults:
    """Test result export."""

    def test_export_results(self, tmp_path):
        """Test exporting results to file."""
        selector = TestSelector(project_root=tmp_path)

        prediction = TestPrediction(
            test_id="test_001",
            test_name="test_login",
            failure_probability=0.8,
            estimated_duration_ms=1000,
            priority=TestPriority.HIGH,
        )

        from socialseed_e2e.ml.models import TestSelectionResult

        result = TestSelectionResult(
            total_tests=1,
            selected_tests=[prediction],
            estimated_duration_ms=1000,
        )

        output_path = tmp_path / "results.json"
        selector.export_results(result, output_path)

        assert output_path.exists()
