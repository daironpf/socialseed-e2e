"""HTML Report Generation for E2E Test Results.

This module provides beautiful HTML report generation with interactive
features, charts, and filtering capabilities.
"""

from .html_report_generator import HTMLReportGenerator
from .report_models import ReportSummary, TestStatus, TestSuiteReport
from .test_result_collector import TestResult, TestResultCollector

__all__ = [
    "HTMLReportGenerator",
    "TestResult",
    "TestResultCollector",
    "ReportSummary",
    "TestStatus",
    "TestSuiteReport",
]
