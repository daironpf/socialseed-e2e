"""HTML Report Generation for E2E Test Results.

This module provides beautiful HTML report generation with interactive
features, charts, and filtering capabilities.
"""

from .html_report_generator import HTMLReportGenerator
from .test_result_collector import TestResult, TestResultCollector
from .report_models import ReportSummary, TestStatus, TestSuiteReport

__all__ = [
    "HTMLReportGenerator",
    "TestResult",
    "TestResultCollector",
    "ReportSummary",
    "TestStatus",
    "TestSuiteReport",
]
