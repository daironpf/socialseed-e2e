"""Metrics collection and SLA validation for socialseed-e2e performance tests."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class SLAPolicy:
    max_avg_latency_ms: float
    p95_latency_ms: float
    max_error_rate: float # 0.0 to 1.0


class MetricsCollector:
    """Aggregates and analyzes performance metrics."""

    def __init__(self, latencies: List[float], total_requests: int, failed_requests: int):
        self.latencies = sorted(latencies)
        self.total = total_requests
        self.failed = failed_requests

    def get_percentile(self, percentile: float) -> float:
        """Get the N-th percentile latency."""
        if not self.latencies:
            return 0.0
        idx = int(len(self.latencies) * (percentile / 100))
        return self.latencies[min(idx, len(self.latencies) - 1)]

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        if not self.latencies:
            return {"status": "no_data"}

        return {
            "total_requests": self.total,
            "failed_requests": self.failed,
            "error_rate": (self.failed / self.total) if self.total > 0 else 0,
            "avg_latency": sum(self.latencies) / len(self.latencies),
            "min_latency": self.latencies[0],
            "max_latency": self.latencies[-1],
            "p50": self.get_percentile(50),
            "p90": self.get_percentile(90),
            "p95": self.get_percentile(95),
            "p99": self.get_percentile(99),
        }

    def validate_sla(self, sla: SLAPolicy) -> List[str]:
        """Check if metrics satisfy the SLA policy. Returns list of violations."""
        summary = self.get_summary()
        violations = []

        if summary["avg_latency"] > sla.max_avg_latency_ms:
            violations.append(f"Avg latency {summary['avg_latency']:.2f}ms exceeds SLA {sla.max_avg_latency_ms}ms")

        p95 = summary["p95"]
        if p95 > sla.p95_latency_ms:
            violations.append(f"P95 latency {p95:.2f}ms exceeds SLA {sla.p95_latency_ms}ms")

        error_rate = summary["error_rate"]
        if error_rate > sla.max_error_rate:
            violations.append(f"Error rate {error_rate*100:.2f}% exceeds SLA {sla.max_error_rate*100:.2f}%")

        return violations
