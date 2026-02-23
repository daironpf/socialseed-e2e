"""Performance profiling data models.

This module defines data structures for performance metrics,
thresholds, and regression detection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AlertSeverity(str, Enum):
    """Severity levels for performance alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class RegressionType(str, Enum):
    """Types of performance regressions."""

    LATENCY_INCREASE = "latency_increase"
    THROUGHPUT_DECREASE = "throughput_decrease"
    ERROR_RATE_INCREASE = "error_rate_increase"
    P95_INCREASE = "p95_increase"
    P99_INCREASE = "p99_increase"


@dataclass
class EndpointPerformanceMetrics:
    """Performance metrics for a single endpoint.

    Attributes:
        endpoint_path: The API endpoint path
        method: HTTP method (GET, POST, etc.)
        call_count: Number of calls made
        total_duration_ms: Total duration of all calls
        avg_latency_ms: Average latency in milliseconds
        min_latency_ms: Minimum latency observed
        max_latency_ms: Maximum latency observed
        p50_latency_ms: 50th percentile latency
        p95_latency_ms: 95th percentile latency
        p99_latency_ms: 99th percentile latency
        error_count: Number of failed requests
        error_rate: Error rate as percentage
        timestamp: When metrics were recorded
    """

    endpoint_path: str
    method: str
    call_count: int = 0
    total_duration_ms: float = 0.0
    avg_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    individual_times: List[float] = field(default_factory=list)

    def record_call(self, duration_ms: float, success: bool = True) -> None:
        """Record a single API call.

        Args:
            duration_ms: Duration of the call in milliseconds
            success: Whether the call was successful
        """
        self.call_count += 1
        self.total_duration_ms += duration_ms
        self.individual_times.append(duration_ms)

        if success:
            self.min_latency_ms = min(self.min_latency_ms, duration_ms)
            self.max_latency_ms = max(self.max_latency_ms, duration_ms)
        else:
            self.error_count += 1

        # Recalculate average
        if self.call_count > 0:
            self.avg_latency_ms = self.total_duration_ms / self.call_count
            self.error_rate = (self.error_count / self.call_count) * 100

    def calculate_percentiles(self) -> None:
        """Calculate latency percentiles from individual times."""
        if not self.individual_times:
            return

        sorted_times = sorted(self.individual_times)
        n = len(sorted_times)

        self.p50_latency_ms = sorted_times[int(n * 0.5)]
        self.p95_latency_ms = sorted_times[int(n * 0.95)]
        self.p99_latency_ms = sorted_times[int(n * 0.99)]


@dataclass
class PerformanceThreshold:
    """Threshold configuration for performance metrics.

    Attributes:
        endpoint_pattern: Regex pattern to match endpoints
        max_avg_latency_ms: Maximum allowed average latency
        max_p95_latency_ms: Maximum allowed P95 latency
        max_p99_latency_ms: Maximum allowed P99 latency
        max_error_rate: Maximum allowed error rate percentage
        regression_threshold_pct: Percentage increase to flag as regression
    """

    endpoint_pattern: str = ".*"
    max_avg_latency_ms: Optional[float] = None
    max_p95_latency_ms: Optional[float] = None
    max_p99_latency_ms: Optional[float] = None
    max_error_rate: float = 5.0
    regression_threshold_pct: float = 50.0


@dataclass
class PerformanceRegression:
    """Detected performance regression.

    Attributes:
        endpoint_path: Affected endpoint
        method: HTTP method
        regression_type: Type of regression
        previous_value: Performance metric before regression
        current_value: Performance metric after regression
        percentage_change: Percentage change in performance
        suspected_code: Code that might have caused the regression
        severity: Alert severity level
    """

    endpoint_path: str
    method: str
    regression_type: RegressionType
    previous_value: float
    current_value: float
    percentage_change: float
    suspected_code: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    severity: AlertSeverity = AlertSeverity.WARNING

    def __post_init__(self):
        """Calculate severity based on percentage change."""
        if abs(self.percentage_change) >= 100:
            self.severity = AlertSeverity.CRITICAL
        elif abs(self.percentage_change) >= 50:
            self.severity = AlertSeverity.WARNING
        else:
            self.severity = AlertSeverity.INFO


@dataclass
class PerformanceAlert:
    """Performance alert with context.

    Attributes:
        title: Alert title
        message: Detailed alert message
        severity: Alert severity
        endpoint_path: Affected endpoint
        method: HTTP method
        metric_name: Name of the affected metric
        threshold_value: Expected threshold
        actual_value: Actual measured value
        timestamp: When the alert was generated
        recommendations: List of recommendations
    """

    title: str
    message: str
    severity: AlertSeverity
    endpoint_path: str
    method: str
    metric_name: str
    threshold_value: float
    actual_value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "endpoint": f"{self.method} {self.endpoint_path}",
            "metric": self.metric_name,
            "threshold": self.threshold_value,
            "actual": self.actual_value,
            "timestamp": self.timestamp.isoformat(),
            "recommendations": self.recommendations,
        }


@dataclass
class PerformanceReport:
    """Complete performance report for a test run.

    Attributes:
        test_run_id: Unique identifier for the test run
        timestamp: When the report was generated
        service_name: Name of the service being tested
        total_requests: Total number of requests made
        total_duration_ms: Total duration of all requests
        overall_avg_latency: Overall average latency
        endpoints: Performance metrics per endpoint
        regressions: Detected regressions
        alerts: Generated alerts
        summary: Textual summary
    """

    test_run_id: str
    timestamp: datetime
    service_name: str
    total_requests: int = 0
    total_duration_ms: float = 0.0
    overall_avg_latency: float = 0.0
    endpoints: Dict[str, EndpointPerformanceMetrics] = field(default_factory=dict)
    regressions: List[PerformanceRegression] = field(default_factory=list)
    alerts: List[PerformanceAlert] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)

    def add_endpoint_metrics(self, metrics: EndpointPerformanceMetrics) -> None:
        """Add metrics for an endpoint."""
        key = f"{metrics.method} {metrics.endpoint_path}"
        self.endpoints[key] = metrics
        self.total_requests += metrics.call_count
        self.total_duration_ms += metrics.total_duration_ms

    def generate_summary(self) -> str:
        """Generate a textual summary of the report."""
        lines = [
            f"Performance Report - {self.service_name}",
            f"Test Run: {self.test_run_id}",
            f"Timestamp: {self.timestamp.isoformat()}",
            "",
            f"Total Requests: {self.total_requests}",
            f"Overall Avg Latency: {self.overall_avg_latency:.2f}ms",
            "",
            f"Endpoints Analyzed: {len(self.endpoints)}",
            f"Regressions Detected: {len(self.regressions)}",
            f"Alerts Generated: {len(self.alerts)}",
        ]

        if self.regressions:
            lines.extend(["", "Top Regressions:"])
            for reg in sorted(
                self.regressions, key=lambda x: abs(x.percentage_change), reverse=True
            )[:5]:
                lines.append(
                    f"  - {reg.method} {reg.endpoint_path}: "
                    f"{reg.percentage_change:+.1f}% ({reg.regression_type.value})"
                )

        self.summary = "\n".join(lines)
        return self.summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "test_run_id": self.test_run_id,
            "timestamp": self.timestamp.isoformat(),
            "service_name": self.service_name,
            "total_requests": self.total_requests,
            "overall_avg_latency": self.overall_avg_latency,
            "endpoints": {
                k: {
                    "path": v.endpoint_path,
                    "method": v.method,
                    "call_count": v.call_count,
                    "avg_latency_ms": v.avg_latency_ms,
                    "p95_latency_ms": v.p95_latency_ms,
                    "p99_latency_ms": v.p99_latency_ms,
                    "error_rate": v.error_rate,
                }
                for k, v in self.endpoints.items()
            },
            "regressions": [
                {
                    "endpoint": f"{r.method} {r.endpoint_path}",
                    "type": r.regression_type.value,
                    "change_pct": r.percentage_change,
                    "severity": r.severity.value,
                }
                for r in self.regressions
            ],
            "alerts": [a.to_dict() for a in self.alerts],
            "summary": self.summary,
            "recommendations": self.recommendations,
        }
