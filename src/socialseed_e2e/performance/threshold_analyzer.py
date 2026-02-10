"""Threshold Analyzer for performance regression detection.

This module compares current performance metrics with historical
data to detect regressions and performance degradation.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from socialseed_e2e.performance.performance_models import (
    EndpointPerformanceMetrics,
    PerformanceRegression,
    PerformanceReport,
    PerformanceThreshold,
    RegressionType,
)


class ThresholdAnalyzer:
    """Analyzer for detecting performance regressions by comparing runs.

    This class compares current performance metrics with historical
    data from previous runs to detect performance degradation.

    Example:
        >>> analyzer = ThresholdAnalyzer()
        >>> analyzer.load_baseline(".e2e/performance/baseline.json")
        >>>
        >>> current_report = profiler.generate_report()
        >>> regressions = analyzer.detect_regressions(current_report)
        >>>
        >>> for reg in regressions:
        ...     print(f"{reg.endpoint_path}: {reg.percentage_change:+.1f}%")
    """

    def __init__(
        self,
        performance_dir: Optional[Path] = None,
        regression_threshold_pct: float = 50.0,
    ):
        """Initialize the threshold analyzer.

        Args:
            performance_dir: Directory containing performance reports
            regression_threshold_pct: Percentage change to flag as regression
        """
        self.performance_dir = performance_dir or Path(".e2e/performance")
        self.regression_threshold_pct = regression_threshold_pct
        self.baseline: Optional[PerformanceReport] = None
        self.thresholds: List[PerformanceThreshold] = []
        self._history: List[PerformanceReport] = []

        # Default thresholds
        self._setup_default_thresholds()

    def _setup_default_thresholds(self) -> None:
        """Set up default performance thresholds."""
        self.thresholds = [
            PerformanceThreshold(
                endpoint_pattern=".*",
                max_avg_latency_ms=1000.0,
                max_p95_latency_ms=2000.0,
                max_p99_latency_ms=5000.0,
                max_error_rate=5.0,
                regression_threshold_pct=self.regression_threshold_pct,
            ),
            PerformanceThreshold(
                endpoint_pattern=".*health.*",
                max_avg_latency_ms=100.0,
                max_p95_latency_ms=200.0,
                regression_threshold_pct=20.0,
            ),
        ]

    def add_threshold(self, threshold: PerformanceThreshold) -> None:
        """Add a custom performance threshold.

        Args:
            threshold: Threshold configuration to add
        """
        self.thresholds.append(threshold)

    def load_baseline(self, baseline_path: Optional[Path] = None) -> bool:
        """Load baseline performance data from a file.

        Args:
            baseline_path: Path to baseline file (auto-detects if not provided)

        Returns:
            True if baseline loaded successfully
        """
        if baseline_path is None:
            baseline_path = self._find_baseline_file()

        if not baseline_path or not baseline_path.exists():
            return False

        try:
            with open(baseline_path, "r") as f:
                data = json.load(f)

            self.baseline = self._report_from_dict(data)
            return True
        except (json.JSONDecodeError, KeyError):
            return False

    def _find_baseline_file(self) -> Optional[Path]:
        """Find the most recent baseline performance file.

        Returns:
            Path to baseline file or None if not found
        """
        if not self.performance_dir.exists():
            return None

        # Look for baseline file or most recent report
        baseline_file = self.performance_dir / "baseline.json"
        if baseline_file.exists():
            return baseline_file

        # Find most recent report
        reports = sorted(
            self.performance_dir.glob("perf_report_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        return reports[0] if reports else None

    def load_history(self, days: int = 7) -> None:
        """Load historical performance reports.

        Args:
            days: Number of days of history to load
        """
        if not self.performance_dir.exists():
            return

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        self._history = []

        for report_file in self.performance_dir.glob("perf_report_*.json"):
            try:
                with open(report_file, "r") as f:
                    data = json.load(f)

                report_date = datetime.fromisoformat(data["timestamp"])
                if report_date >= cutoff_date:
                    self._history.append(self._report_from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue

    def detect_regressions(
        self, current_report: PerformanceReport
    ) -> List[PerformanceRegression]:
        """Detect performance regressions by comparing with baseline.

        Args:
            current_report: Current performance report

        Returns:
            List of detected regressions
        """
        regressions = []

        if not self.baseline:
            return regressions

        for key, current_metrics in current_report.endpoints.items():
            if key in self.baseline.endpoints:
                baseline_metrics = self.baseline.endpoints[key]

                # Check for latency regression
                if baseline_metrics.avg_latency_ms > 0:
                    change_pct = (
                        (
                            current_metrics.avg_latency_ms
                            - baseline_metrics.avg_latency_ms
                        )
                        / baseline_metrics.avg_latency_ms
                    ) * 100

                    if abs(change_pct) >= self.regression_threshold_pct:
                        regressions.append(
                            PerformanceRegression(
                                endpoint_path=current_metrics.endpoint_path,
                                method=current_metrics.method,
                                regression_type=RegressionType.LATENCY_INCREASE,
                                previous_value=baseline_metrics.avg_latency_ms,
                                current_value=current_metrics.avg_latency_ms,
                                percentage_change=change_pct,
                            )
                        )

                # Check for P95 regression
                if baseline_metrics.p95_latency_ms > 0:
                    p95_change = (
                        (
                            current_metrics.p95_latency_ms
                            - baseline_metrics.p95_latency_ms
                        )
                        / baseline_metrics.p95_latency_ms
                    ) * 100

                    if p95_change >= self.regression_threshold_pct:
                        regressions.append(
                            PerformanceRegression(
                                endpoint_path=current_metrics.endpoint_path,
                                method=current_metrics.method,
                                regression_type=RegressionType.P95_INCREASE,
                                previous_value=baseline_metrics.p95_latency_ms,
                                current_value=current_metrics.p95_latency_ms,
                                percentage_change=p95_change,
                            )
                        )

                # Check for P99 regression
                if baseline_metrics.p99_latency_ms > 0:
                    p99_change = (
                        (
                            current_metrics.p99_latency_ms
                            - baseline_metrics.p99_latency_ms
                        )
                        / baseline_metrics.p99_latency_ms
                    ) * 100

                    if p99_change >= self.regression_threshold_pct:
                        regressions.append(
                            PerformanceRegression(
                                endpoint_path=current_metrics.endpoint_path,
                                method=current_metrics.method,
                                regression_type=RegressionType.P99_INCREASE,
                                previous_value=baseline_metrics.p99_latency_ms,
                                current_value=current_metrics.p99_latency_ms,
                                percentage_change=p99_change,
                            )
                        )

                # Check for error rate increase
                if baseline_metrics.error_rate >= 0:
                    error_change = (
                        current_metrics.error_rate - baseline_metrics.error_rate
                    )

                    if error_change > 2.0:  # More than 2% increase
                        regressions.append(
                            PerformanceRegression(
                                endpoint_path=current_metrics.endpoint_path,
                                method=current_metrics.method,
                                regression_type=RegressionType.ERROR_RATE_INCREASE,
                                previous_value=baseline_metrics.error_rate,
                                current_value=current_metrics.error_rate,
                                percentage_change=error_change,
                            )
                        )

        return regressions

    def check_thresholds(self, report: PerformanceReport) -> List[Dict[str, any]]:
        """Check if metrics exceed defined thresholds.

        Args:
            report: Performance report to check

        Returns:
            List of threshold violations
        """
        violations = []

        for key, metrics in report.endpoints.items():
            for threshold in self.thresholds:
                import re

                if re.match(threshold.endpoint_pattern, metrics.endpoint_path):
                    # Check average latency
                    if (
                        threshold.max_avg_latency_ms
                        and metrics.avg_latency_ms > threshold.max_avg_latency_ms
                    ):
                        violations.append(
                            {
                                "endpoint": key,
                                "metric": "avg_latency_ms",
                                "threshold": threshold.max_avg_latency_ms,
                                "actual": metrics.avg_latency_ms,
                                "severity": "warning",
                            }
                        )

                    # Check P95 latency
                    if (
                        threshold.max_p95_latency_ms
                        and metrics.p95_latency_ms > threshold.max_p95_latency_ms
                    ):
                        violations.append(
                            {
                                "endpoint": key,
                                "metric": "p95_latency_ms",
                                "threshold": threshold.max_p95_latency_ms,
                                "actual": metrics.p95_latency_ms,
                                "severity": "critical",
                            }
                        )

                    # Check error rate
                    if metrics.error_rate > threshold.max_error_rate:
                        violations.append(
                            {
                                "endpoint": key,
                                "metric": "error_rate",
                                "threshold": threshold.max_error_rate,
                                "actual": metrics.error_rate,
                                "severity": "critical",
                            }
                        )

        return violations

    def set_baseline(self, report: PerformanceReport) -> Path:
        """Set current report as the baseline.

        Args:
            report: Report to use as baseline

        Returns:
            Path to saved baseline file
        """
        self.performance_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = self.performance_dir / "baseline.json"

        with open(baseline_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        self.baseline = report
        return baseline_path

    def _report_from_dict(self, data: Dict) -> PerformanceReport:
        """Create a PerformanceReport from dictionary data.

        Args:
            data: Dictionary containing report data

        Returns:
            PerformanceReport object
        """
        report = PerformanceReport(
            test_run_id=data.get("test_run_id", "unknown"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            service_name=data.get("service_name", "unknown"),
            total_requests=data.get("total_requests", 0),
            total_duration_ms=data.get("total_duration_ms", 0.0),
            overall_avg_latency=data.get("overall_avg_latency", 0.0),
            summary=data.get("summary", ""),
            recommendations=data.get("recommendations", []),
        )

        # Restore endpoint metrics
        for key, endpoint_data in data.get("endpoints", {}).items():
            metrics = EndpointPerformanceMetrics(
                endpoint_path=endpoint_data["path"],
                method=endpoint_data["method"],
                call_count=endpoint_data.get("call_count", 0),
                avg_latency_ms=endpoint_data.get("avg_latency_ms", 0.0),
                p95_latency_ms=endpoint_data.get("p95_latency_ms", 0.0),
                p99_latency_ms=endpoint_data.get("p99_latency_ms", 0.0),
                error_rate=endpoint_data.get("error_rate", 0.0),
            )
            report.endpoints[key] = metrics

        return report

    def get_trend_analysis(
        self, endpoint_key: str, metric: str = "avg_latency_ms"
    ) -> Dict[str, any]:
        """Analyze performance trend for an endpoint over time.

        Args:
            endpoint_key: Endpoint identifier (e.g., "GET /users")
            metric: Metric to analyze

        Returns:
            Trend analysis data
        """
        if not self._history:
            self.load_history()

        values = []
        for report in sorted(self._history, key=lambda r: r.timestamp):
            if endpoint_key in report.endpoints:
                metrics = report.endpoints[endpoint_key]
                value = getattr(metrics, metric, None)
                if value is not None:
                    values.append((report.timestamp, value))

        if len(values) < 2:
            return {"trend": "insufficient_data", "values": values}

        # Calculate trend
        first_value = values[0][1]
        last_value = values[-1][1]
        change_pct = (
            ((last_value - first_value) / first_value) * 100 if first_value else 0
        )

        trend = "stable"
        if change_pct > 20:
            trend = "increasing"
        elif change_pct < -20:
            trend = "decreasing"

        return {
            "trend": trend,
            "change_percentage": change_pct,
            "values": values,
            "count": len(values),
        }
