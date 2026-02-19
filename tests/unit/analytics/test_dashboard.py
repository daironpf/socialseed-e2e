"""Tests for Analytics Dashboard Module.

This module tests the analytics dashboard features.
"""

import pytest
from datetime import datetime, timedelta

from socialseed_e2e.analytics.dashboard import (
    CoverageDashboard,
    DashboardMetric,
    FlakyTestAnalyzer,
    TestAnalyticsDashboard,
    TestHistoryTracker,
    TestRunRecord,
    TrendDashboard,
)


class TestTestRunRecord:
    """Tests for TestRunRecord."""

    def test_initialization(self):
        """Test record initialization."""
        record = TestRunRecord(
            test_id="test_1",
            test_name="Test 1",
            status="passed",
            duration_ms=100,
            timestamp=datetime.now(),
        )
        assert record.test_id == "test_1"
        assert record.status == "passed"


class TestTestHistoryTracker:
    """Tests for TestHistoryTracker."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = TestHistoryTracker()
        assert len(tracker.runs) == 0

    def test_record_run(self):
        """Test recording a run."""
        tracker = TestHistoryTracker()
        run = TestRunRecord(
            test_id="test_1",
            test_name="Test 1",
            status="passed",
            duration_ms=100,
            timestamp=datetime.now(),
        )
        tracker.record_run(run)

        assert len(tracker.runs) == 1
        assert len(tracker.all_runs) == 1

    def test_get_test_history(self):
        """Test getting test history."""
        tracker = TestHistoryTracker()
        now = datetime.now()

        run1 = TestRunRecord(
            test_id="test_1",
            test_name="Test 1",
            status="passed",
            duration_ms=100,
            timestamp=now,
        )
        run2 = TestRunRecord(
            test_id="test_1",
            test_name="Test 1",
            status="failed",
            duration_ms=200,
            timestamp=now - timedelta(days=1),
        )

        tracker.record_run(run1)
        tracker.record_run(run2)

        history = tracker.get_test_history("test_1")
        assert len(history) == 2

    def test_get_pass_rate(self):
        """Test calculating pass rate."""
        tracker = TestHistoryTracker()
        now = datetime.now()

        tracker.record_run(
            TestRunRecord(
                test_id="test_1",
                test_name="Test 1",
                status="passed",
                duration_ms=100,
                timestamp=now,
            )
        )
        tracker.record_run(
            TestRunRecord(
                test_id="test_2",
                test_name="Test 2",
                status="failed",
                duration_ms=100,
                timestamp=now,
            )
        )

        pass_rate = tracker.get_pass_rate(days=1)
        assert pass_rate == 0.5


class TestCoverageDashboard:
    """Tests for CoverageDashboard."""

    def test_initialization(self):
        """Test dashboard initialization."""
        dashboard = CoverageDashboard()
        assert len(dashboard.endpoints) == 0

    def test_register_endpoint(self):
        """Test registering endpoint."""
        dashboard = CoverageDashboard()
        dashboard.register_endpoint("GET", "/api/users", ["test_list_users"])

        assert len(dashboard.endpoints) == 1

    def test_get_coverage_report(self):
        """Test getting coverage report."""
        dashboard = CoverageDashboard()
        dashboard.register_endpoint("GET", "/api/users", ["test_list_users"])
        dashboard.register_endpoint("POST", "/api/users", [])

        report = dashboard.get_coverage_report()
        assert report["total_endpoints"] == 2
        assert report["covered_endpoints"] == 1
        assert report["coverage_percentage"] == 50.0

    def test_get_endpoint_coverage(self):
        """Test getting endpoint coverage."""
        dashboard = CoverageDashboard()
        dashboard.register_endpoint("GET", "/api/users", ["test_list_users"])

        coverage = dashboard.get_endpoint_coverage("GET", "/api/users")
        assert coverage["is_covered"] is True
        assert "test_list_users" in coverage["covering_tests"]


class TestTrendDashboard:
    """Tests for TrendDashboard."""

    def test_initialization(self):
        """Test dashboard initialization."""
        tracker = TestHistoryTracker()
        dashboard = TrendDashboard(tracker)
        assert dashboard.history == tracker

    def test_analyze_test_trend(self):
        """Test analyzing test trend."""
        tracker = TestHistoryTracker()
        dashboard = TrendDashboard(tracker)

        now = datetime.now()
        tracker.record_run(
            TestRunRecord(
                test_id="test_1",
                test_name="Test 1",
                status="passed",
                duration_ms=100,
                timestamp=now,
            )
        )
        tracker.record_run(
            TestRunRecord(
                test_id="test_1",
                test_name="Test 1",
                status="passed",
                duration_ms=150,
                timestamp=now - timedelta(days=1),
            )
        )

        trend = dashboard.analyze_test_trend("test_1")
        assert trend["has_data"] is True
        assert trend["pass_rate"] == 1.0

    def test_get_pass_rate_trend(self):
        """Test getting pass rate trend."""
        tracker = TestHistoryTracker()
        dashboard = TrendDashboard(tracker)

        now = datetime.now()
        tracker.record_run(
            TestRunRecord(
                test_id="test_1",
                test_name="Test 1",
                status="passed",
                duration_ms=100,
                timestamp=now,
            )
        )

        trend = dashboard.get_pass_rate_trend(days=7)
        assert len(trend) >= 1

    def test_find_degrading_tests(self):
        """Test finding degrading tests."""
        tracker = TestHistoryTracker()
        dashboard = TrendDashboard(tracker)

        now = datetime.now()
        # Add failing test
        for i in range(5):
            tracker.record_run(
                TestRunRecord(
                    test_id="test_failing",
                    test_name="Failing Test",
                    status="failed",
                    duration_ms=100,
                    timestamp=now - timedelta(days=i),
                )
            )

        degrading = dashboard.find_degrading_tests(days=7, threshold=0.5)
        assert len(degrading) >= 1


class TestFlakyTestAnalyzer:
    """Tests for FlakyTestAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        tracker = TestHistoryTracker()
        analyzer = FlakyTestAnalyzer(tracker)
        assert analyzer.history == tracker

    def test_calculate_flakiness_score(self):
        """Test calculating flakiness score."""
        tracker = TestHistoryTracker()
        analyzer = FlakyTestAnalyzer(tracker)

        now = datetime.now()
        # Alternating pass/fail pattern
        statuses = ["passed", "failed", "passed", "failed", "passed"]
        for i, status in enumerate(statuses):
            tracker.record_run(
                TestRunRecord(
                    test_id="test_flaky",
                    test_name="Flaky Test",
                    status=status,
                    duration_ms=100,
                    timestamp=now - timedelta(hours=i),
                )
            )

        score = analyzer.calculate_flakiness_score("test_flaky")
        assert score > 0.5  # High flakiness

    def test_find_flaky_tests(self):
        """Test finding flaky tests."""
        tracker = TestHistoryTracker()
        analyzer = FlakyTestAnalyzer(tracker)

        now = datetime.now()
        # Alternating pattern for flaky test
        for i in range(10):
            tracker.record_run(
                TestRunRecord(
                    test_id="test_flaky",
                    test_name="Flaky Test",
                    status="passed" if i % 2 == 0 else "failed",
                    duration_ms=100,
                    timestamp=now - timedelta(hours=i),
                )
            )

        flaky = analyzer.find_flaky_tests(min_runs=5, threshold=0.3)
        assert len(flaky) >= 1
        assert flaky[0]["test_id"] == "test_flaky"


class TestTestAnalyticsDashboard:
    """Tests for TestAnalyticsDashboard."""

    def test_initialization(self):
        """Test dashboard initialization."""
        dashboard = TestAnalyticsDashboard()
        assert dashboard is not None

    def test_record_test_run(self):
        """Test recording test run."""
        dashboard = TestAnalyticsDashboard()
        run = TestRunRecord(
            test_id="test_1",
            test_name="Test 1",
            status="passed",
            duration_ms=100,
            timestamp=datetime.now(),
        )
        dashboard.record_test_run(run)

        assert len(dashboard.history.all_runs) == 1

    def test_register_endpoint(self):
        """Test registering endpoint."""
        dashboard = TestAnalyticsDashboard()
        dashboard.register_endpoint("GET", "/api/users", ["test_list_users"])

        report = dashboard.coverage.get_coverage_report()
        assert report["total_endpoints"] == 1

    def test_generate_report(self):
        """Test generating report."""
        dashboard = TestAnalyticsDashboard()

        # Add test runs
        now = datetime.now()
        dashboard.record_test_run(
            TestRunRecord(
                test_id="test_1",
                test_name="Test 1",
                status="passed",
                duration_ms=100,
                timestamp=now,
            )
        )

        # Register endpoint
        dashboard.register_endpoint("GET", "/api/users", ["test_list_users"])

        report = dashboard.generate_report(days=7)
        assert "summary" in report
        assert "coverage" in report
        assert report["summary"]["total_tests"] == 1

    def test_get_summary_metrics(self):
        """Test getting summary metrics."""
        dashboard = TestAnalyticsDashboard()
        dashboard.record_test_run(
            TestRunRecord(
                test_id="test_1",
                test_name="Test 1",
                status="passed",
                duration_ms=100,
                timestamp=datetime.now(),
            )
        )

        metrics = dashboard.get_summary_metrics()
        assert len(metrics) == 4
        assert any(m.name == "total_tests" for m in metrics)


class TestDashboardMetric:
    """Tests for DashboardMetric."""

    def test_initialization(self):
        """Test metric initialization."""
        metric = DashboardMetric(name="test_metric", value=100.0, unit="ms")
        assert metric.name == "test_metric"
        assert metric.value == 100.0
        assert metric.unit == "ms"
