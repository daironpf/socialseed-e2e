"""HTML Report Generator for E2E test results.

This module generates beautiful, interactive HTML reports with charts,
filtering, and export capabilities.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.reporting.report_models import (
    TestResult,
    TestStatus,
    TestSuiteReport,
)


class HTMLReportGenerator:
    """Generate beautiful HTML reports from test results.

    This class generates interactive HTML reports with charts, filtering,
    and export capabilities.

    Example:
        >>> from socialseed_e2e.reporting import TestResultCollector
        >>> collector = TestResultCollector()
        >>> # ... collect test results ...
        >>> report = collector.generate_report()
        >>>
        >>> generator = HTMLReportGenerator()
        >>> html_path = generator.generate(report, output_path="report.html")
        >>> print(f"Report generated: {html_path}")
    """

    def __init__(self, template_path: Optional[Path] = None):
        """Initialize the HTML report generator.

        Args:
            template_path: Path to custom HTML template
        """
        if template_path:
            self.template_path = template_path
        else:
            # Use default template
            import socialseed_e2e

            base_dir = Path(socialseed_e2e.__file__).parent
            self.template_path = base_dir / "templates" / "report.html.template"

    def generate(
        self,
        report: TestSuiteReport,
        output_path: str = "e2e-report.html",
        title: Optional[str] = None,
    ) -> Path:
        """Generate HTML report.

        Args:
            report: Test suite report
            output_path: Output file path
            title: Report title (uses report title if not specified)

        Returns:
            Path to generated HTML file
        """
        if title is None:
            title = report.title

        # Read template
        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Prepare template data
        template_data = self._prepare_template_data(report, title)

        # Render template
        html_content = self._render_template(template, template_data)

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file

    def _prepare_template_data(
        self, report: TestSuiteReport, title: str
    ) -> Dict[str, Any]:
        """Prepare data for template rendering.

        Args:
            report: Test suite report
            title: Report title

        Returns:
            Template data dictionary
        """
        summary = report.summary

        # Prepare tests data
        tests_data = []
        for test in report.tests:
            tests_data.append(
                {
                    "id": test.id,
                    "name": test.name,
                    "service": test.service,
                    "status": test.status.value,
                    "duration": test.duration_formatted,
                    "durationClass": "slow" if test.is_slow else "",
                }
            )

        # Prepare services data
        services_data = [{"name": service} for service in report.services]

        # Prepare test details for modal
        test_details = {}
        for test in report.tests:
            test_details[test.id] = {
                "name": test.name,
                "service": test.service,
                "status": test.status.value,
                "duration": test.duration_formatted,
                "timestamp": test.timestamp.isoformat(),
                "error": test.error_message,
                "stackTrace": test.stack_trace,
                "request": test.request,
                "response": test.response,
            }

        return {
            "title": title,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "duration": summary.duration_formatted,
            "total_passed": summary.passed,
            "total_failed": summary.failed,
            "total_skipped": summary.skipped,
            "success_rate": round(summary.success_rate, 1),
            "tests": tests_data,
            "services": services_data,
            "test_details_json": json.dumps(test_details),
        }

    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render template with data.

        Args:
            template: HTML template string
            data: Template data

        Returns:
            Rendered HTML string
        """
        result = template

        # Simple template rendering - replace {{variable}} with values
        for key, value in data.items():
            if isinstance(value, (str, int, float)):
                placeholder = f"{{{{ {key} }}}}"
                result = result.replace(placeholder, str(value))

        # Handle lists (mustache-style sections)
        # Handle tests list
        if "{{#tests}}" in result and "{{/tests}}" in result:
            start_idx = result.find("{{#tests}}")
            end_idx = result.find("{{/tests}}") + len("{{/tests}}")
            template_section = result[start_idx:end_idx]
            inner_template = template_section[len("{{#tests}}") : -len("{{/tests}}")]

            rendered_tests = ""
            for test in data.get("tests", []):
                test_html = inner_template
                for key, value in test.items():
                    placeholder = f"{{{{{key}}}}}"
                    test_html = test_html.replace(placeholder, str(value))
                rendered_tests += test_html

            result = result[:start_idx] + rendered_tests + result[end_idx:]

        # Handle services list
        if "{{#services}}" in result and "{{/services}}" in result:
            start_idx = result.find("{{#services}}")
            end_idx = result.find("{{/services}}") + len("{{/services}}")
            template_section = result[start_idx:end_idx]
            inner_template = template_section[
                len("{{#services}}") : -len("{{/services}}")
            ]

            rendered_services = ""
            for service in data.get("services", []):
                service_html = inner_template
                for key, value in service.items():
                    placeholder = f"{{{{{key}}}}}"
                    service_html = service_html.replace(placeholder, str(value))
                rendered_services += service_html

            result = result[:start_idx] + rendered_services + result[end_idx:]

        return result

    def export_to_csv(self, report: TestSuiteReport, output_path: str) -> Path:
        """Export test results to CSV.

        Args:
            report: Test suite report
            output_path: Output file path

        Returns:
            Path to generated CSV file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Test Name",
                    "Service",
                    "Status",
                    "Duration (ms)",
                    "Timestamp",
                    "Error Message",
                ]
            )

            # Write test data
            for test in report.tests:
                writer.writerow(
                    [
                        test.name,
                        test.service,
                        test.status.value,
                        test.duration_ms,
                        test.timestamp.isoformat(),
                        test.error_message or "",
                    ]
                )

        return output_file

    def export_to_json(self, report: TestSuiteReport, output_path: str) -> Path:
        """Export test results to JSON.

        Args:
            report: Test suite report
            output_path: Output file path

        Returns:
            Path to generated JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = report.to_dict()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return output_file

    def generate_summary_text(self, report: TestSuiteReport) -> str:
        """Generate text summary of test results.

        Args:
            report: Test suite report

        Returns:
            Summary text
        """
        summary = report.summary

        lines = [
            "=" * 70,
            report.title,
            "=" * 70,
            "",
            f"Total Tests: {summary.total_tests}",
            f"Passed: {summary.passed}",
            f"Failed: {summary.failed}",
            f"Skipped: {summary.skipped}",
            f"Success Rate: {summary.success_rate:.1f}%",
            f"Total Duration: {summary.duration_formatted}",
            "",
        ]

        if summary.failed > 0:
            lines.extend(["Failed Tests:", "-" * 70])
            for test in report.tests:
                if test.status == TestStatus.FAILED:
                    lines.append(f"  ✗ {test.name} ({test.service})")
                    if test.error_message:
                        lines.append(f"    Error: {test.error_message}")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)


def generate_report(
    report: TestSuiteReport,
    output_dir: str = ".e2e/reports",
    formats: Optional[List[str]] = None,
) -> Dict[str, Path]:
    """Generate reports in multiple formats.

    Args:
        report: Test suite report
        output_dir: Output directory
        formats: List of formats to generate (html, csv, json)

    Returns:
        Dictionary mapping format to file path
    """
    if formats is None:
        formats = ["html"]

    generator = HTMLReportGenerator()
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results = {}

    for fmt in formats:
        if fmt == "html":
            path = generator.generate(
                report, output_path=output_dir_path / f"report_{timestamp}.html"
            )
            results["html"] = path
        elif fmt == "csv":
            path = generator.export_to_csv(
                report, output_path=output_dir_path / f"report_{timestamp}.csv"
            )
            results["csv"] = path
        elif fmt == "json":
            path = generator.export_to_json(
                report, output_path=output_dir_path / f"report_{timestamp}.json"
            )
            results["json"] = path

    return results
