"""Performance Profiler for tracking endpoint latency.

This module integrates with BasePage to capture detailed
performance metrics during E2E test execution.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from socialseed_e2e.performance.performance_models import (
    EndpointPerformanceMetrics,
    PerformanceReport,
)


class PerformanceProfiler:
    """Profiler for tracking endpoint performance during E2E runs.

    This class integrates with BasePage to automatically capture
    latency metrics for every HTTP request made during testing.

    Example:
        >>> profiler = PerformanceProfiler()
        >>> profiler.start_profiling()
        >>>
        >>> # Run your tests here
        >>> page.get("/users")
        >>> page.post("/users", data={"name": "John"})
        >>>
        >>> report = profiler.generate_report()
        >>> print(report.summary)
    """

    def __init__(
        self,
        service_name: str = "unknown",
        output_dir: Optional[Path] = None,
    ):
        """Initialize the performance profiler.

        Args:
            service_name: Name of the service being profiled
            output_dir: Directory to save performance reports
        """
        self.service_name = service_name
        self.output_dir = output_dir or Path(".e2e/performance")
        self.test_run_id = str(uuid.uuid4())[:8]
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Storage for metrics
        self._metrics: Dict[str, EndpointPerformanceMetrics] = {}
        self._active_requests: Dict[str, Dict[str, Any]] = {}

    def start_profiling(self) -> None:
        """Start a new profiling session."""
        self.start_time = datetime.utcnow()
        self._metrics.clear()
        self._active_requests.clear()

    def stop_profiling(self) -> None:
        """Stop the current profiling session."""
        self.end_time = datetime.utcnow()

    def start_request(self, request_id: str, method: str, url: str) -> None:
        """Mark the start of an HTTP request.

        Args:
            request_id: Unique identifier for the request
            method: HTTP method (GET, POST, etc.)
            url: Full request URL
        """
        self._active_requests[request_id] = {
            "method": method,
            "url": url,
            "start_time": time.time(),
        }

    def end_request(
        self,
        request_id: str,
        status_code: int,
        error: Optional[str] = None,
    ) -> None:
        """Mark the end of an HTTP request and record metrics.

        Args:
            request_id: Unique identifier for the request
            status_code: HTTP response status code
            error: Error message if request failed
        """
        if request_id not in self._active_requests:
            return

        request_data = self._active_requests.pop(request_id)
        end_time = time.time()
        duration_ms = (end_time - request_data["start_time"]) * 1000

        # Extract endpoint path from URL
        endpoint_path = self._extract_endpoint_path(request_data["url"])
        method = request_data["method"]
        key = f"{method} {endpoint_path}"

        # Create or get metrics for this endpoint
        if key not in self._metrics:
            self._metrics[key] = EndpointPerformanceMetrics(
                endpoint_path=endpoint_path,
                method=method,
            )

        # Record the call
        success = 200 <= status_code < 300
        self._metrics[key].record_call(duration_ms, success)

    def _extract_endpoint_path(self, url: str) -> str:
        """Extract endpoint path from full URL.

        Args:
            url: Full URL

        Returns:
            Endpoint path (e.g., "/api/users")
        """
        # Remove base URL and query parameters
        if "?" in url:
            url = url.split("?")[0]

        # Try to extract just the path
        if "://" in url:
            parts = url.split("://", 1)[1]
            if "/" in parts:
                return "/" + parts.split("/", 1)[1]

        return url

    def calculate_percentiles(self) -> None:
        """Calculate percentile metrics for all endpoints."""
        for metrics in self._metrics.values():
            metrics.calculate_percentiles()

    def generate_report(self) -> PerformanceReport:
        """Generate a performance report from collected metrics.

        Returns:
            PerformanceReport with all collected metrics
        """
        if not self.end_time:
            self.stop_profiling()

        # Calculate percentiles
        self.calculate_percentiles()

        # Create report
        report = PerformanceReport(
            test_run_id=self.test_run_id,
            timestamp=self.start_time or datetime.utcnow(),
            service_name=self.service_name,
        )

        # Add endpoint metrics
        for metrics in self._metrics.values():
            report.add_endpoint_metrics(metrics)

        # Calculate overall stats
        if report.total_requests > 0:
            report.overall_avg_latency = (
                report.total_duration_ms / report.total_requests
            )

        # Generate summary
        report.generate_summary()

        return report

    def save_report(self, report: Optional[PerformanceReport] = None) -> Path:
        """Save the performance report to disk.

        Args:
            report: Report to save (generates if not provided)

        Returns:
            Path to saved report file
        """
        if report is None:
            report = self.generate_report()

        self.output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"perf_report_{self.test_run_id}.json"
        filepath = self.output_dir / filename

        import json

        with open(filepath, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        return filepath

    def get_metrics_for_endpoint(
        self, path: str, method: str
    ) -> Optional[EndpointPerformanceMetrics]:
        """Get metrics for a specific endpoint.

        Args:
            path: Endpoint path
            method: HTTP method

        Returns:
            Metrics for the endpoint or None if not found
        """
        key = f"{method} {path}"
        return self._metrics.get(key)

    def get_all_metrics(self) -> List[EndpointPerformanceMetrics]:
        """Get all collected endpoint metrics.

        Returns:
            List of all endpoint metrics
        """
        return list(self._metrics.values())

    def wrap_request(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator/wrapper to automatically profile a request function.

        Args:
            func: Function to wrap

        Returns:
            Wrapped function that tracks performance
        """

        def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())

            # Extract method and URL from arguments
            method = kwargs.get("method", "GET")
            url = args[0] if args else kwargs.get("url", "")

            self.start_request(request_id, method, url)

            try:
                result = func(*args, **kwargs)
                status_code = getattr(result, "status", 200)
                self.end_request(request_id, status_code)
                return result
            except Exception as e:
                self.end_request(request_id, 0, error=str(e))
                raise

        return wrapper

    def reset(self) -> None:
        """Reset all collected metrics."""
        self._metrics.clear()
        self._active_requests.clear()
        self.start_time = None
        self.end_time = None
        self.test_run_id = str(uuid.uuid4())[:8]
