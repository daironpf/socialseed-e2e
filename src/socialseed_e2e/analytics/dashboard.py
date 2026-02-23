"""Test Analytics Dashboard Module.

This module provides comprehensive test analytics dashboard capabilities:
- Historical trend analysis
- Coverage analytics and gap detection
- Failure pattern analysis
- Predictive analytics for flaky tests
- Dashboard visualization data

Usage:
    from socialseed_e2e.analytics.dashboard import (
        TestAnalyticsDashboard,
        CoverageDashboard,
        TrendDashboard,
    )
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from socialseed_e2e.analytics.trend_analyzer import TrendAnalyzer


@dataclass
class DashboardMetric:
    """Metric for dashboard display."""

    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class TestRunRecord:
    """Record of a test execution."""

    test_id: str
    test_name: str
    status: str  # passed, failed, skipped, error
    duration_ms: float
    timestamp: datetime
    error_message: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestHistoryTracker:
    """Tracks test execution history.

    Example:
        tracker = TestHistoryTracker()

        # Record test runs
        tracker.record_run(TestRunRecord(...))

        # Get history
        history = tracker.get_test_history("test_1", days=7)
    """

    def __init__(self):
        """Initialize history tracker."""
        self.runs: Dict[str, List[TestRunRecord]] = {}
        self.all_runs: List[TestRunRecord] = []

    def record_run(self, run: TestRunRecord) -> None:
        """Record a test run.

        Args:
            run: Test run record
        """
        if run.test_id not in self.runs:
            self.runs[run.test_id] = []
        self.runs[run.test_id].append(run)
        self.all_runs.append(run)

    def get_test_history(
        self,
        test_id: str,
        days: Optional[int] = None,
    ) -> List[TestRunRecord]:
        """Get history for a specific test.

        Args:
            test_id: Test ID
            days: Number of days to look back

        Returns:
            List of test runs
        """
        runs = self.runs.get(test_id, [])

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            runs = [r for r in runs if r.timestamp >= cutoff]

        return sorted(runs, key=lambda r: r.timestamp)

    def get_recent_runs(self, limit: int = 100) -> List[TestRunRecord]:
        """Get most recent test runs.

        Args:
            limit: Maximum number of runs

        Returns:
            List of recent runs
        """
        return sorted(self.all_runs, key=lambda r: r.timestamp, reverse=True)[:limit]

    def get_pass_rate(self, days: int = 7) -> float:
        """Calculate overall pass rate.

        Args:
            days: Number of days to analyze

        Returns:
            Pass rate (0-1)
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_runs = [r for r in self.all_runs if r.timestamp >= cutoff]

        if not recent_runs:
            return 0.0

        passed = sum(1 for r in recent_runs if r.status == "passed")
        return passed / len(recent_runs)


class CoverageDashboard:
    """Dashboard for coverage analytics.

    Example:
        dashboard = CoverageDashboard()

        # Register endpoints
        dashboard.register_endpoint("GET", "/api/users", ["test_list_users"])

        # Get coverage report
        report = dashboard.get_coverage_report()
    """

    def __init__(self):
        """Initialize coverage dashboard."""
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        self.tests_by_endpoint: Dict[str, Set[str]] = {}

    def register_endpoint(
        self,
        method: str,
        path: str,
        covering_tests: List[str] = None,
    ) -> None:
        """Register an API endpoint.

        Args:
            method: HTTP method
            path: Endpoint path
            covering_tests: Tests covering this endpoint
        """
        key = f"{method}:{path}"
        self.endpoints[key] = {
            "method": method,
            "path": path,
            "tests": set(covering_tests or []),
        }

        for test in covering_tests or []:
            if test not in self.tests_by_endpoint:
                self.tests_by_endpoint[test] = set()
            self.tests_by_endpoint[test].add(key)

    def get_coverage_report(self) -> Dict[str, Any]:
        """Get coverage report.

        Returns:
            Coverage report
        """
        total = len(self.endpoints)
        covered = sum(1 for e in self.endpoints.values() if e["tests"])
        uncovered = total - covered

        return {
            "total_endpoints": total,
            "covered_endpoints": covered,
            "uncovered_endpoints": uncovered,
            "coverage_percentage": (covered / total * 100) if total > 0 else 0,
            "uncovered_list": [
                {"method": e["method"], "path": e["path"]}
                for e in self.endpoints.values()
                if not e["tests"]
            ],
        }

    def get_endpoint_coverage(self, method: str, path: str) -> Dict[str, Any]:
        """Get coverage for specific endpoint.

        Args:
            method: HTTP method
            path: Endpoint path

        Returns:
            Coverage details
        """
        key = f"{method}:{path}"
        endpoint = self.endpoints.get(key, {})

        return {
            "method": method,
            "path": path,
            "is_covered": bool(endpoint.get("tests")),
            "covering_tests": list(endpoint.get("tests", [])),
            "test_count": len(endpoint.get("tests", [])),
        }

    def get_test_coverage_map(self, test_id: str) -> List[Dict[str, str]]:
        """Get all endpoints covered by a test.

        Args:
            test_id: Test ID

        Returns:
            List of covered endpoints
        """
        endpoints = self.tests_by_endpoint.get(test_id, set())
        return [{"method": e.split(":")[0], "path": e.split(":")[1]} for e in endpoints]


class TrendDashboard:
    """Dashboard for trend analytics.

    Example:
        dashboard = TrendDashboard(history_tracker)

        # Analyze trends
        trends = dashboard.analyze_trends(days=7)

        # Get pass rate trend
        pass_trend = dashboard.get_pass_rate_trend()
    """

    def __init__(self, history_tracker: TestHistoryTracker):
        """Initialize trend dashboard.

        Args:
            history_tracker: TestHistoryTracker instance
        """
        self.history = history_tracker
        self.trend_analyzer = TrendAnalyzer()

    def analyze_test_trend(
        self,
        test_id: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Analyze trend for a specific test.

        Args:
            test_id: Test ID
            days: Number of days to analyze

        Returns:
            Trend analysis
        """
        runs = self.history.get_test_history(test_id, days)

        if not runs:
            return {"test_id": test_id, "has_data": False}

        total = len(runs)
        passed = sum(1 for r in runs if r.status == "passed")
        failed = total - passed

        durations = [r.duration_ms for r in runs]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Calculate trend direction
        if total >= 2:
            mid = total // 2
            first_half_passed = sum(1 for r in runs[:mid] if r.status == "passed")
            second_half_passed = sum(1 for r in runs[mid:] if r.status == "passed")

            first_half_rate = first_half_passed / mid if mid > 0 else 0
            second_half_rate = (
                second_half_passed / (total - mid) if (total - mid) > 0 else 0
            )

            if second_half_rate > first_half_rate:
                trend_direction = "improving"
            elif second_half_rate < first_half_rate:
                trend_direction = "degrading"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"

        return {
            "test_id": test_id,
            "test_name": runs[0].test_name if runs else test_id,
            "has_data": True,
            "total_runs": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total,
            "avg_duration_ms": avg_duration,
            "trend_direction": trend_direction,
            "last_run_status": runs[-1].status if runs else None,
        }

    def get_pass_rate_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get pass rate trend over time.

        Args:
            days: Number of days

        Returns:
            Daily pass rates
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_runs = [r for r in self.history.all_runs if r.timestamp >= cutoff]

        # Group by day
        daily_stats: Dict[datetime, Dict[str, int]] = {}
        for run in recent_runs:
            day = run.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            if day not in daily_stats:
                daily_stats[day] = {"passed": 0, "total": 0}
            daily_stats[day]["total"] += 1
            if run.status == "passed":
                daily_stats[day]["passed"] += 1

        # Calculate daily pass rates
        result = []
        for day in sorted(daily_stats.keys()):
            stats = daily_stats[day]
            pass_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
            result.append(
                {
                    "date": day.isoformat(),
                    "pass_rate": pass_rate,
                    "total_runs": stats["total"],
                }
            )

        return result

    def find_degrading_tests(
        self, days: int = 7, threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Find tests with degrading pass rates.

        Args:
            days: Number of days to analyze
            threshold: Pass rate threshold

        Returns:
            List of degrading tests
        """
        degrading = []

        for test_id in self.history.runs.keys():
            trend = self.analyze_test_trend(test_id, days)
            if trend.get("has_data") and trend["pass_rate"] < threshold:
                degrading.append(trend)

        return sorted(degrading, key=lambda x: x["pass_rate"])

    def find_slow_tests(
        self, days: int = 7, threshold_ms: float = 5000
    ) -> List[Dict[str, Any]]:
        """Find slow tests.

        Args:
            days: Number of days
            threshold_ms: Duration threshold

        Returns:
            List of slow tests
        """
        slow = []

        for test_id in self.history.runs.keys():
            trend = self.analyze_test_trend(test_id, days)
            if trend.get("has_data") and trend["avg_duration_ms"] > threshold_ms:
                slow.append(trend)

        return sorted(slow, key=lambda x: x["avg_duration_ms"], reverse=True)


class FlakyTestAnalyzer:
    """Analyzes and detects flaky tests.

    Example:
        analyzer = FlakyTestAnalyzer(history_tracker)

        # Find flaky tests
        flaky = analyzer.find_flaky_tests(min_runs=5)

        # Get flakiness score
        score = analyzer.calculate_flakiness_score("test_1")
    """

    def __init__(self, history_tracker: TestHistoryTracker):
        """Initialize flaky test analyzer.

        Args:
            history_tracker: TestHistoryTracker instance
        """
        self.history = history_tracker

    def calculate_flakiness_score(self, test_id: str) -> float:
        """Calculate flakiness score (0-1).

        Args:
            test_id: Test ID

        Returns:
            Flakiness score
        """
        runs = self.history.get_test_history(test_id)

        if len(runs) < 5:
            return 0.0

        # Count status transitions
        transitions = 0
        for i in range(1, len(runs)):
            if runs[i].status != runs[i - 1].status:
                transitions += 1

        return transitions / (len(runs) - 1)

    def find_flaky_tests(
        self,
        min_runs: int = 5,
        threshold: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """Find flaky tests.

        Args:
            min_runs: Minimum runs required
            threshold: Flakiness threshold

        Returns:
            List of flaky tests
        """
        flaky = []

        for test_id in self.history.runs.keys():
            runs = self.history.get_test_history(test_id)

            if len(runs) < min_runs:
                continue

            score = self.calculate_flakiness_score(test_id)

            if score >= threshold:
                passed = sum(1 for r in runs if r.status == "passed")
                flaky.append(
                    {
                        "test_id": test_id,
                        "test_name": runs[0].test_name if runs else test_id,
                        "flakiness_score": score,
                        "total_runs": len(runs),
                        "pass_rate": passed / len(runs),
                        "recent_status_changes": sum(
                            1
                            for i in range(1, min(10, len(runs)))
                            if runs[i].status != runs[i - 1].status
                        ),
                    }
                )

        return sorted(flaky, key=lambda x: x["flakiness_score"], reverse=True)


class TestAnalyticsDashboard:
    """Comprehensive test analytics dashboard.

    Example:
        dashboard = TestAnalyticsDashboard()

        # Record test runs
        dashboard.record_test_run(TestRunRecord(...))

        # Get full report
        report = dashboard.generate_report()

        # Export to file
        dashboard.export_report("report.json")
    """

    def __init__(self):
        """Initialize analytics dashboard."""
        self.history = TestHistoryTracker()
        self.coverage = CoverageDashboard()
        self.trends = TrendDashboard(self.history)
        self.flaky = FlakyTestAnalyzer(self.history)

    def record_test_run(self, run: TestRunRecord) -> None:
        """Record a test run.

        Args:
            run: Test run record
        """
        self.history.record_run(run)

    def register_endpoint(
        self, method: str, path: str, tests: List[str] = None
    ) -> None:
        """Register an API endpoint.

        Args:
            method: HTTP method
            path: Endpoint path
            tests: Covering tests
        """
        self.coverage.register_endpoint(method, path, tests)

    def generate_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive analytics report.

        Args:
            days: Number of days to analyze

        Returns:
            Full report
        """
        coverage_report = self.coverage.get_coverage_report()
        flaky_tests = self.flaky.find_flaky_tests()
        degrading = self.trends.find_degrading_tests(days=days)
        slow = self.trends.find_slow_tests(days=days)
        pass_trend = self.trends.get_pass_rate_trend(days=days)

        return {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "summary": {
                "total_tests": len(self.history.runs),
                "total_runs": len(self.history.all_runs),
                "overall_pass_rate": self.history.get_pass_rate(days),
                "coverage_percentage": coverage_report["coverage_percentage"],
                "flaky_tests_count": len(flaky_tests),
                "degrading_tests_count": len(degrading),
                "slow_tests_count": len(slow),
            },
            "coverage": coverage_report,
            "pass_rate_trend": pass_trend,
            "flaky_tests": flaky_tests[:10],  # Top 10
            "degrading_tests": degrading[:10],
            "slow_tests": slow[:10],
        }

    def export_report(self, filepath: str, days: int = 7) -> None:
        """Export report to JSON file.

        Args:
            filepath: Output file path
            days: Number of days to analyze
        """
        report = self.generate_report(days)

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

    def get_summary_metrics(self) -> List[DashboardMetric]:
        """Get summary metrics for dashboard.

        Returns:
            List of dashboard metrics
        """
        return [
            DashboardMetric(
                name="total_tests",
                value=len(self.history.runs),
                unit="tests",
            ),
            DashboardMetric(
                name="total_runs",
                value=len(self.history.all_runs),
                unit="runs",
            ),
            DashboardMetric(
                name="pass_rate",
                value=self.history.get_pass_rate(7) * 100,
                unit="%",
            ),
            DashboardMetric(
                name="coverage",
                value=self.coverage.get_coverage_report()["coverage_percentage"],
                unit="%",
            ),
        ]
