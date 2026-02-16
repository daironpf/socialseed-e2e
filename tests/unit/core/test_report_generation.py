"""Tests for report generation functionality.

This module contains tests for the JUnit and JSON report generation functions.
"""

import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from socialseed_e2e.core.test_runner import (
    TestResult,
    TestSuiteResult,
    generate_junit_report,
    generate_json_report,
)


class TestJUnitReportGeneration:
    """Test cases for JUnit XML report generation."""

    def test_generate_junit_report_with_passed_tests(self):
        """Test generating JUnit report with all passed tests."""
        # Create test results
        results = {
            "auth_service": TestSuiteResult(
                total=2,
                passed=2,
                failed=0,
                skipped=0,
                errors=0,
                total_duration_ms=1500.0,
                results=[
                    TestResult(
                        name="test_login",
                        service="auth_service",
                        status="passed",
                        duration_ms=800.0,
                    ),
                    TestResult(
                        name="test_logout",
                        service="auth_service",
                        status="passed",
                        duration_ms=700.0,
                    ),
                ],
            )
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "junit.xml")
            result_path = generate_junit_report(results, output_path)

            # Verify file was created
            assert os.path.exists(result_path)

            # Parse and verify XML content
            tree = ET.parse(result_path)
            root = tree.getroot()

            # Check root attributes
            assert root.get("name") == "socialseed-e2e"
            assert root.get("tests") == "2"
            assert root.get("failures") == "0"
            assert root.get("errors") == "0"

            # Check testsuite
            testsuite = root.find("testsuite")
            assert testsuite is not None
            assert testsuite.get("name") == "auth_service"
            assert testsuite.get("tests") == "2"
            assert testsuite.get("failures") == "0"

            # Check testcases
            testcases = testsuite.findall("testcase")
            assert len(testcases) == 2
            assert testcases[0].get("name") == "test_login"
            assert testcases[1].get("name") == "test_logout"

    def test_generate_junit_report_with_failed_tests(self):
        """Test generating JUnit report with failed tests."""
        results = {
            "user_service": TestSuiteResult(
                total=2,
                passed=1,
                failed=1,
                skipped=0,
                errors=0,
                total_duration_ms=2000.0,
                results=[
                    TestResult(
                        name="test_get_user",
                        service="user_service",
                        status="passed",
                        duration_ms=500.0,
                    ),
                    TestResult(
                        name="test_create_user",
                        service="user_service",
                        status="failed",
                        duration_ms=1500.0,
                        error_message="Expected status 201, got 400",
                        error_traceback="AssertionError: Expected status 201, got 400",
                    ),
                ],
            )
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "junit.xml")
            result_path = generate_junit_report(results, output_path)

            # Parse and verify XML
            tree = ET.parse(result_path)
            root = tree.getroot()

            # Check failures count
            assert root.get("failures") == "1"
            assert root.get("tests") == "2"

            # Check for failure element
            testsuite = root.find("testsuite")
            testcases = testsuite.findall("testcase")

            # First test should have no failure
            assert testcases[0].find("failure") is None

            # Second test should have failure
            failure = testcases[1].find("failure")
            assert failure is not None
            assert "Expected status 201" in failure.get("message")

    def test_generate_junit_report_creates_directory(self):
        """Test that JUnit report generation creates output directory if needed."""
        results = {
            "test_service": TestSuiteResult(
                total=1,
                passed=1,
                failed=0,
                skipped=0,
                errors=0,
                total_duration_ms=100.0,
                results=[],
            )
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a nested directory that doesn't exist
            output_path = os.path.join(tmpdir, "nested", "reports", "junit.xml")
            result_path = generate_junit_report(results, output_path)

            assert os.path.exists(result_path)


class TestJSONReportGeneration:
    """Test cases for JSON report generation."""

    def test_generate_json_report_structure(self):
        """Test JSON report has correct structure."""
        results = {
            "payment_service": TestSuiteResult(
                total=3,
                passed=2,
                failed=1,
                skipped=0,
                errors=0,
                total_duration_ms=3000.0,
                results=[
                    TestResult(
                        name="test_process_payment",
                        service="payment_service",
                        status="passed",
                        duration_ms=1000.0,
                    ),
                    TestResult(
                        name="test_refund",
                        service="payment_service",
                        status="passed",
                        duration_ms=800.0,
                    ),
                    TestResult(
                        name="test_invalid_card",
                        service="payment_service",
                        status="failed",
                        duration_ms=1200.0,
                        error_message="Card validation failed",
                    ),
                ],
            )
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            result_path = generate_json_report(results, output_path)

            # Verify file was created
            assert os.path.exists(result_path)

            # Load and verify JSON structure
            with open(result_path, "r") as f:
                report = json.load(f)

            # Check top-level fields
            assert report["framework"] == "socialseed-e2e"
            assert "version" in report
            assert "timestamp" in report

            # Check summary
            summary = report["summary"]
            assert summary["total"] == 3
            assert summary["passed"] == 2
            assert summary["failed"] == 1
            assert summary["success_rate"] == pytest.approx(66.67, rel=0.01)

            # Check services
            assert "payment_service" in report["services"]
            service = report["services"]["payment_service"]
            assert service["total"] == 3
            assert len(service["tests"]) == 3

            # Check failed test has error details
            failed_test = service["tests"][2]
            assert failed_test["status"] == "failed"
            assert "error" in failed_test
            assert "Card validation failed" in failed_test["error"]["message"]

    def test_generate_json_report_empty_results(self):
        """Test JSON report with no test results."""
        results = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            result_path = generate_json_report(results, output_path)

            with open(result_path, "r") as f:
                report = json.load(f)

            assert report["summary"]["total"] == 0
            assert report["summary"]["success_rate"] == 0.0
            assert report["services"] == {}

    def test_generate_json_report_creates_directory(self):
        """Test that JSON report generation creates output directory if needed."""
        results = {
            "test_service": TestSuiteResult(total=0, passed=0, failed=0, results=[])
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "reports", "output", "report.json")
            result_path = generate_json_report(results, output_path)

            assert os.path.exists(result_path)

    def test_generate_json_report_with_error_tests(self):
        """Test JSON report includes error test details."""
        results = {
            "api_service": TestSuiteResult(
                total=1,
                passed=0,
                failed=0,
                errors=1,
                total_duration_ms=500.0,
                results=[
                    TestResult(
                        name="test_connection",
                        service="api_service",
                        status="error",
                        duration_ms=500.0,
                        error_message="Connection timeout",
                        error_traceback="TimeoutError: Connection timeout after 30s",
                    ),
                ],
            )
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            generate_json_report(results, output_path)

            with open(output_path, "r") as f:
                report = json.load(f)

            assert report["summary"]["errors"] == 1
            test = report["services"]["api_service"]["tests"][0]
            assert test["status"] == "error"
            assert "Connection timeout" in test["error"]["message"]


class TestReportIntegration:
    """Integration tests for report generation."""

    def test_both_reports_generated_correctly(self):
        """Test that both JUnit and JSON reports can be generated from same results."""
        results = {
            "integration_service": TestSuiteResult(
                total=3,
                passed=2,
                failed=1,
                skipped=0,
                errors=0,
                total_duration_ms=2500.0,
                results=[
                    TestResult(
                        name="test_success",
                        service="integration_service",
                        status="passed",
                        duration_ms=500.0,
                    ),
                    TestResult(
                        name="test_another_success",
                        service="integration_service",
                        status="passed",
                        duration_ms=600.0,
                    ),
                    TestResult(
                        name="test_failure",
                        service="integration_service",
                        status="failed",
                        duration_ms=1400.0,
                        error_message="Test failed",
                    ),
                ],
            )
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate both reports
            junit_path = generate_junit_report(
                results, os.path.join(tmpdir, "junit.xml")
            )
            json_path = generate_json_report(
                results, os.path.join(tmpdir, "report.json")
            )

            # Verify both exist
            assert os.path.exists(junit_path)
            assert os.path.exists(json_path)

            # Verify counts match
            tree = ET.parse(junit_path)
            root = tree.getroot()
            junit_total = int(root.get("tests"))
            junit_failures = int(root.get("failures"))

            with open(json_path, "r") as f:
                json_report = json.load(f)

            json_total = json_report["summary"]["total"]
            json_failures = json_report["summary"]["failed"]

            assert junit_total == json_total == 3
            assert junit_failures == json_failures == 1
