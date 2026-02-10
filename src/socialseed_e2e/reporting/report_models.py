"""Data models for HTML reports.

This module defines the data structures used for HTML report generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TestStatus(str, Enum):
    """Test execution status."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Individual test result data.

    Attributes:
        id: Unique test identifier
        name: Test name
        service: Service/module name
        status: Test status
        duration_ms: Test duration in milliseconds
        timestamp: When test was executed
        error_message: Error message if failed
        stack_trace: Stack trace if failed
        request: HTTP request data
        response: HTTP response data
        metadata: Additional test metadata
    """

    id: str
    name: str
    service: str
    status: TestStatus
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if self.duration_ms < 1000:
            return f"{self.duration_ms:.0f}ms"
        else:
            return f"{self.duration_ms / 1000:.2f}s"

    @property
    def is_slow(self) -> bool:
        """Check if test is slow (> 5 seconds)."""
        return self.duration_ms > 5000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "service": self.service,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "duration": self.duration_formatted,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "request": self.request,
            "response": self.response,
            "metadata": self.metadata,
        }


@dataclass
class ReportSummary:
    """Summary of test execution.

    Attributes:
        total_tests: Total number of tests
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        errors: Number of tests with errors
        total_duration_ms: Total execution time
        start_time: When tests started
        end_time: When tests ended
    """

    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    @property
    def duration_formatted(self) -> str:
        """Get formatted total duration."""
        if self.total_duration_ms < 1000:
            return f"{self.total_duration_ms:.0f}ms"
        elif self.total_duration_ms < 60000:
            return f"{self.total_duration_ms / 1000:.1f}s"
        else:
            minutes = int(self.total_duration_ms / 60000)
            seconds = (self.total_duration_ms % 60000) / 1000
            return f"{minutes}m {seconds:.0f}s"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "success_rate": round(self.success_rate, 2),
            "total_duration_ms": self.total_duration_ms,
            "duration": self.duration_formatted,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


@dataclass
class TestSuiteReport:
    """Complete test suite report.

    Attributes:
        title: Report title
        summary: Execution summary
        tests: List of test results
        services: List of service names
        metadata: Additional report metadata
    """

    title: str = "E2E Test Report"
    summary: ReportSummary = field(default_factory=ReportSummary)
    tests: List[TestResult] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize services list from tests."""
        if not self.services and self.tests:
            self.services = sorted(set(test.service for test in self.tests))

    def add_test(self, test: TestResult) -> None:
        """Add a test result and update summary."""
        self.tests.append(test)
        self.summary.total_tests += 1

        if test.status == TestStatus.PASSED:
            self.summary.passed += 1
        elif test.status == TestStatus.FAILED:
            self.summary.failed += 1
        elif test.status == TestStatus.SKIPPED:
            self.summary.skipped += 1
        elif test.status == TestStatus.ERROR:
            self.summary.errors += 1

        self.summary.total_duration_ms += test.duration_ms

        # Update services list
        if test.service not in self.services:
            self.services.append(test.service)
            self.services.sort()

    def get_tests_by_status(self, status: TestStatus) -> List[TestResult]:
        """Get tests filtered by status."""
        return [test for test in self.tests if test.status == status]

    def get_tests_by_service(self, service: str) -> List[TestResult]:
        """Get tests filtered by service."""
        return [test for test in self.tests if test.service == service]

    def get_slow_tests(self, threshold_ms: float = 5000) -> List[TestResult]:
        """Get tests that exceeded duration threshold."""
        return [test for test in self.tests if test.duration_ms > threshold_ms]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "summary": self.summary.to_dict(),
            "tests": [test.to_dict() for test in self.tests],
            "services": self.services,
            "metadata": self.metadata,
        }
