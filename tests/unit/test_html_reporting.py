"""Tests for HTML Report Generation system."""

import json
import tempfile
from pathlib import Path

import pytest

from socialseed_e2e.reporting import (
    HTMLReportGenerator,
    TestResult,
    TestResultCollector,
    TestSuiteReport,
)
from socialseed_e2e.reporting.report_models import ReportSummary, TestStatus


class TestTestResult:
    """Test suite for TestResult."""

    def test_initialization(self):
        """Test TestResult initialization."""
        result = TestResult(
            id="test-1",
            name="test_create_user",
            service="users-api",
            status=TestStatus.PASSED,
            duration_ms=150.5,
        )

        assert result.id == "test-1"
        assert result.name == "test_create_user"
        assert result.service == "users-api"
        assert result.status == TestStatus.PASSED
        assert result.duration_ms == 150.5

    def test_duration_formatted_milliseconds(self):
        """Test duration formatting for milliseconds."""
        result = TestResult(
            id="test-1",
            name="test",
            service="api",
            status=TestStatus.PASSED,
            duration_ms=500,
        )

        assert result.duration_formatted == "500ms"

    def test_duration_formatted_seconds(self):
        """Test duration formatting for seconds."""
        result = TestResult(
            id="test-1",
            name="test",
            service="api",
            status=TestStatus.PASSED,
            duration_ms=2500,
        )

        assert result.duration_formatted == "2.50s"

    def test_is_slow(self):
        """Test slow test detection."""
        fast_test = TestResult(
            id="test-1",
            name="test",
            service="api",
            status=TestStatus.PASSED,
            duration_ms=1000,
        )

        slow_test = TestResult(
            id="test-2",
            name="test",
            service="api",
            status=TestStatus.PASSED,
            duration_ms=6000,
        )

        assert not fast_test.is_slow
        assert slow_test.is_slow

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = TestResult(
            id="test-1",
            name="test_create_user",
            service="users-api",
            status=TestStatus.PASSED,
            duration_ms=150,
            error_message=None,
        )

        data = result.to_dict()

        assert data["id"] == "test-1"
        assert data["name"] == "test_create_user"
        assert data["status"] == "passed"
        assert data["duration"] == "150ms"


class TestReportSummary:
    """Test suite for ReportSummary."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        summary = ReportSummary(
            total_tests=100,
            passed=80,
            failed=15,
            skipped=5,
        )

        assert summary.success_rate == 80.0

    def test_success_rate_zero_tests(self):
        """Test success rate with zero tests."""
        summary = ReportSummary(total_tests=0)

        assert summary.success_rate == 0.0

    def test_duration_formatted_milliseconds(self):
        """Test duration formatting for milliseconds."""
        summary = ReportSummary(total_duration_ms=500)

        assert summary.duration_formatted == "500ms"

    def test_duration_formatted_seconds(self):
        """Test duration formatting for seconds."""
        summary = ReportSummary(total_duration_ms=45000)

        assert summary.duration_formatted == "45.0s"

    def test_duration_formatted_minutes(self):
        """Test duration formatting for minutes."""
        summary = ReportSummary(total_duration_ms=125000)

        assert "2m" in summary.duration_formatted


class TestTestResultCollector:
    """Test suite for TestResultCollector."""

    def test_initialization(self):
        """Test collector initialization."""
        collector = TestResultCollector(title="My Test Report")

        assert collector.title == "My Test Report"
        assert len(collector.tests) == 0

    def test_start_collection(self):
        """Test starting collection."""
        collector = TestResultCollector()
        collector.start_collection()

        assert collector._start_time is not None
        assert collector.summary.start_time is not None

    def test_record_test(self):
        """Test recording a test."""
        collector = TestResultCollector()
        collector.start_collection()

        collector.record_test_start("test-1", "test_create_user", "users-api")
        result = collector.record_test_end("test-1", "passed", duration_ms=150)

        assert result.status == TestStatus.PASSED
        assert result.name == "test_create_user"
        assert collector.summary.passed == 1
        assert collector.summary.total_tests == 1

    def test_record_failed_test(self):
        """Test recording a failed test."""
        collector = TestResultCollector()
        collector.start_collection()

        collector.record_test_start("test-1", "test_create_user", "users-api")
        result = collector.record_test_end(
            "test-1",
            "failed",
            duration_ms=200,
            error_message="User not found",
        )

        assert result.status == TestStatus.FAILED
        assert result.error_message == "User not found"
        assert collector.summary.failed == 1

    def test_get_failed_tests(self):
        """Test getting failed tests."""
        collector = TestResultCollector()
        collector.start_collection()

        # Record passed test
        collector.record_test_start("test-1", "test_pass", "api")
        collector.record_test_end("test-1", "passed")

        # Record failed test
        collector.record_test_start("test-2", "test_fail", "api")
        collector.record_test_end("test-2", "failed")

        failed = collector.get_failed_tests()

        assert len(failed) == 1
        assert failed[0].name == "test_fail"

    def test_get_slow_tests(self):
        """Test getting slow tests."""
        collector = TestResultCollector()
        collector.start_collection()

        # Record fast test
        collector.record_test_start("test-1", "test_fast", "api")
        collector.record_test_end("test-1", "passed", duration_ms=100)

        # Record slow test
        collector.record_test_start("test-2", "test_slow", "api")
        collector.record_test_end("test-2", "passed", duration_ms=6000)

        slow = collector.get_slow_tests(threshold_ms=5000)

        assert len(slow) == 1
        assert slow[0].name == "test_slow"

    def test_get_stats_by_service(self):
        """Test getting stats by service."""
        collector = TestResultCollector()
        collector.start_collection()

        # Record tests for different services
        collector.record_test_start("test-1", "test1", "users-api")
        collector.record_test_end("test-1", "passed")

        collector.record_test_start("test-2", "test2", "users-api")
        collector.record_test_end("test-2", "failed")

        collector.record_test_start("test-3", "test3", "orders-api")
        collector.record_test_end("test-3", "passed")

        stats = collector.get_stats_by_service()

        assert stats["users-api"]["total"] == 2
        assert stats["users-api"]["passed"] == 1
        assert stats["orders-api"]["total"] == 1

    def test_generate_report(self):
        """Test generating report."""
        collector = TestResultCollector(title="Test Report")
        collector.start_collection()

        collector.record_test_start("test-1", "test_create_user", "users-api")
        collector.record_test_end("test-1", "passed", duration_ms=150)

        report = collector.generate_report()

        assert report.title == "Test Report"
        assert len(report.tests) == 1
        assert report.summary.total_tests == 1


class TestHTMLReportGenerator:
    """Test suite for HTMLReportGenerator."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = HTMLReportGenerator()

        assert generator.template_path.exists()

    def test_generate_html_report(self):
        """Test HTML report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test report
            collector = TestResultCollector()
            collector.start_collection()

            collector.record_test_start("test-1", "test_create_user", "users-api")
            collector.record_test_end("test-1", "passed", duration_ms=150)

            report = collector.generate_report()

            # Generate HTML
            generator = HTMLReportGenerator()
            output_path = Path(tmpdir) / "report.html"
            result_path = generator.generate(report, output_path=str(output_path))

            assert result_path.exists()
            assert result_path.suffix == ".html"

            # Check content
            content = result_path.read_text()
            assert "test_create_user" in content
            assert "users-api" in content

    def test_export_to_csv(self):
        """Test CSV export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test report
            collector = TestResultCollector()
            collector.start_collection()

            collector.record_test_start("test-1", "test_create_user", "users-api")
            collector.record_test_end("test-1", "passed", duration_ms=150)

            report = collector.generate_report()

            # Export to CSV
            generator = HTMLReportGenerator()
            output_path = Path(tmpdir) / "report.csv"
            result_path = generator.export_to_csv(report, str(output_path))

            assert result_path.exists()
            assert result_path.suffix == ".csv"

            # Check content
            content = result_path.read_text()
            assert "test_create_user" in content
            assert "users-api" in content

    def test_export_to_json(self):
        """Test JSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test report
            collector = TestResultCollector()
            collector.start_collection()

            collector.record_test_start("test-1", "test_create_user", "users-api")
            collector.record_test_end("test-1", "passed", duration_ms=150)

            report = collector.generate_report()

            # Export to JSON
            generator = HTMLReportGenerator()
            output_path = Path(tmpdir) / "report.json"
            result_path = generator.export_to_json(report, str(output_path))

            assert result_path.exists()
            assert result_path.suffix == ".json"

            # Check content
            data = json.loads(result_path.read_text())
            assert data["title"] == "E2E Test Report"
            assert len(data["tests"]) == 1

    def test_generate_summary_text(self):
        """Test summary text generation."""
        # Create test report
        collector = TestResultCollector(title="Test Summary")
        collector.start_collection()

        collector.record_test_start("test-1", "test_create_user", "users-api")
        collector.record_test_end("test-1", "passed", duration_ms=150)

        collector.record_test_start("test-2", "test_delete_user", "users-api")
        collector.record_test_end("test-2", "failed", duration_ms=200)

        report = collector.generate_report()

        # Generate summary
        generator = HTMLReportGenerator()
        summary = generator.generate_summary_text(report)

        assert "Test Summary" in summary
        assert "Total Tests: 2" in summary
        assert "Passed: 1" in summary
        assert "Failed: 1" in summary


class TestIntegration:
    """Integration tests for reporting system."""

    def test_end_to_end_report_generation(self):
        """Test complete report generation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Collect test results
            collector = TestResultCollector(title="Integration Test Report")
            collector.start_collection()

            # Simulate test execution
            tests = [
                ("test_create_user", "users-api", "passed", 150),
                ("test_get_user", "users-api", "passed", 120),
                ("test_update_user", "users-api", "failed", 200),
                ("test_create_order", "orders-api", "passed", 300),
                ("test_slow_endpoint", "orders-api", "passed", 6000),
            ]

            for i, (name, service, status, duration) in enumerate(tests):
                test_id = f"test-{i}"
                collector.record_test_start(test_id, name, service)

                if status == "failed":
                    collector.record_test_end(
                        test_id,
                        status,
                        duration_ms=duration,
                        error_message="Test failed",
                    )
                else:
                    collector.record_test_end(test_id, status, duration_ms=duration)

            # Step 2: Generate report
            report = collector.generate_report()

            # Step 3: Generate HTML
            generator = HTMLReportGenerator()

            html_path = generator.generate(
                report, output_path=Path(tmpdir) / "report.html"
            )
            csv_path = generator.export_to_csv(
                report, output_path=Path(tmpdir) / "report.csv"
            )
            json_path = generator.export_to_json(
                report, output_path=Path(tmpdir) / "report.json"
            )

            # Verify all files exist
            assert html_path.exists()
            assert csv_path.exists()
            assert json_path.exists()

            # Verify HTML content
            html_content = html_path.read_text()
            assert "Integration Test Report" in html_content
            assert "test_create_user" in html_content
            assert "users-api" in html_content

            # Verify CSV content
            csv_content = csv_path.read_text()
            assert "test_create_user" in csv_content

            # Verify JSON content
            json_data = json.loads(json_path.read_text())
            assert json_data["summary"]["total_tests"] == 5

    def test_generate_function(self):
        """Test generate function with multiple formats."""
        from socialseed_e2e.reporting.html_report_generator import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test report
            collector = TestResultCollector()
            collector.start_collection()

            collector.record_test_start("test-1", "test", "api")
            collector.record_test_end("test-1", "passed")

            report = collector.generate_report()

            # Generate all formats
            results = generate_report(
                report, output_dir=tmpdir, formats=["html", "csv", "json"]
            )

            assert "html" in results
            assert "csv" in results
            assert "json" in results

            assert results["html"].exists()
            assert results["csv"].exists()
            assert results["json"].exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
