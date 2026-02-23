"""Test result collection and aggregation.

This module collects test results during E2E execution for HTML report generation.
"""

import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from socialseed_e2e.reporting.report_models import (
    ReportSummary,
    TestResult,
    TestStatus,
    TestSuiteReport,
)


class TestResultCollector:
    """Collector for test results during E2E execution.

    This class collects test results and generates a comprehensive test suite report.

    Example:
        >>> collector = TestResultCollector()
        >>> collector.start_collection()
        >>>
        >>> # During test execution
        >>> collector.record_test_start("test-1", "test_create_user", "users-api")
        >>> # ... run test ...
        >>> collector.record_test_end("test-1", status="passed", duration_ms=150)
        >>>
        >>> report = collector.generate_report()
    """

    def __init__(self, title: str = "E2E Test Report"):
        """Initialize the test result collector.

        Args:
            title: Report title
        """
        self.title = title
        self.summary = ReportSummary()
        self.tests: List[TestResult] = []
        self._active_tests: Dict[str, Dict[str, Any]] = {}
        self._start_time: Optional[datetime] = None

    def start_collection(self) -> None:
        """Start collecting test results."""
        self._start_time = datetime.utcnow()
        self.summary.start_time = self._start_time
        self.tests = []
        self._active_tests = {}

    def end_collection(self) -> None:
        """End test collection."""
        self.summary.end_time = datetime.utcnow()

    def record_test_start(
        self,
        test_id: str,
        test_name: str,
        service: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record the start of a test.

        Args:
            test_id: Unique test identifier
            test_name: Test name
            service: Service/module name
            metadata: Additional test metadata
        """
        self._active_tests[test_id] = {
            "test_name": test_name,
            "service": service,
            "start_time": time.time(),
            "metadata": metadata or {},
        }

    def record_test_end(
        self,
        test_id: str,
        status: str,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None,
        request: Optional[Dict[str, Any]] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> TestResult:
        """Record the end of a test.

        Args:
            test_id: Test identifier
            status: Test status (passed, failed, skipped, error)
            duration_ms: Test duration (auto-calculated if not provided)
            error_message: Error message if failed
            stack_trace: Stack trace if failed
            request: HTTP request data
            response: HTTP response data

        Returns:
            TestResult object
        """
        if test_id not in self._active_tests:
            raise ValueError(f"Test {test_id} was not started")

        test_data = self._active_tests.pop(test_id)

        # Calculate duration if not provided
        if duration_ms is None:
            end_time = time.time()
            duration_ms = (end_time - test_data["start_time"]) * 1000

        # Create test result
        result = TestResult(
            id=test_id,
            name=test_data["test_name"],
            service=test_data["service"],
            status=TestStatus(status),
            duration_ms=duration_ms,
            error_message=error_message,
            stack_trace=stack_trace,
            request=request,
            response=response,
            metadata=test_data["metadata"],
        )

        self.tests.append(result)
        self._update_summary(result)

        return result

    def _update_summary(self, result: TestResult) -> None:
        """Update summary statistics."""
        self.summary.total_tests += 1
        self.summary.total_duration_ms += result.duration_ms

        if result.status == TestStatus.PASSED:
            self.summary.passed += 1
        elif result.status == TestStatus.FAILED:
            self.summary.failed += 1
        elif result.status == TestStatus.SKIPPED:
            self.summary.skipped += 1
        elif result.status == TestStatus.ERROR:
            self.summary.errors += 1

    def generate_report(self) -> TestSuiteReport:
        """Generate the test suite report.

        Returns:
            TestSuiteReport with all collected data
        """
        self.end_collection()

        report = TestSuiteReport(
            title=self.title,
            summary=self.summary,
            tests=self.tests.copy(),
        )

        return report

    def get_failed_tests(self) -> List[TestResult]:
        """Get all failed tests."""
        return [test for test in self.tests if test.status == TestStatus.FAILED]

    def get_slow_tests(self, threshold_ms: float = 5000) -> List[TestResult]:
        """Get tests that exceeded duration threshold."""
        return [test for test in self.tests if test.duration_ms > threshold_ms]

    def get_stats_by_service(self) -> Dict[str, Dict[str, int]]:
        """Get test statistics grouped by service."""
        stats: Dict[str, Dict[str, int]] = {}

        for test in self.tests:
            if test.service not in stats:
                stats[test.service] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                }

            stats[test.service]["total"] += 1
            stats[test.service][test.status.value] += 1

        return stats

    def reset(self) -> None:
        """Reset the collector."""
        self.summary = ReportSummary()
        self.tests = []
        self._active_tests = {}
        self._start_time = None


def record_test(func: Callable) -> Callable:
    """Decorator to automatically record test results.

    This decorator automatically tracks test execution time and status.

    Example:
        >>> collector = TestResultCollector()
        >>>
        >>> @record_test
        >>> def test_create_user(collector):
        ...     # Test code here
        ...     pass
    """

    def wrapper(*args, **kwargs):
        # Find collector in arguments
        collector = None
        for arg in args:
            if isinstance(arg, TestResultCollector):
                collector = arg
                break

        if collector is None:
            for _key, value in kwargs.items():
                if isinstance(value, TestResultCollector):
                    collector = value
                    break

        if collector is None:
            # No collector found, just run the test
            return func(*args, **kwargs)

        test_id = str(uuid.uuid4())
        test_name = func.__name__
        service = kwargs.get("service", "unknown")

        # Record start
        collector.record_test_start(test_id, test_name, service)

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            collector.record_test_end(test_id, "passed", duration_ms)
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            import traceback

            collector.record_test_end(
                test_id,
                "failed",
                duration_ms,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
            )
            raise

    return wrapper
