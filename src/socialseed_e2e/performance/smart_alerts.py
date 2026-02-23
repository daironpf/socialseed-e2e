"""Smart Alert Generator for AI-powered performance insights.

This module generates intelligent alerts that provide context and
recommendations for performance regressions.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

from socialseed_e2e.performance.performance_models import (
    PerformanceAlert,
    PerformanceRegression,
    PerformanceReport,
)


class SmartAlertGenerator:
    """Generate intelligent alerts with context and recommendations.

    This class analyzes performance regressions and generates
    human-readable alerts with specific recommendations.

    Example:
        >>> generator = SmartAlertGenerator(project_root="/path/to/project")
        >>> alerts = generator.generate_alerts(report, regressions)
        >>>
        >>> for alert in alerts:
        ...     print(f"[{alert.severity.value}] {alert.title}")
        ...     print(alert.message)
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the smart alert generator.

        Args:
            project_root: Root directory of the project (to find code)
        """
        self.project_root = project_root
        self._code_cache: Dict[str, str] = {}

    def generate_alerts(
        self,
        report: PerformanceReport,
        regressions: List[PerformanceRegression],
    ) -> List[PerformanceAlert]:
        """Generate intelligent alerts for detected regressions.

        Args:
            report: Performance report
            regressions: List of detected regressions

        Returns:
            List of performance alerts
        """
        alerts = []

        for regression in regressions:
            alert = self._create_regression_alert(regression)
            if alert:
                alerts.append(alert)

        return alerts

    def _create_regression_alert(
        self, regression: PerformanceRegression
    ) -> Optional[PerformanceAlert]:
        """Create an alert for a specific regression.

        Args:
            regression: Performance regression data

        Returns:
            PerformanceAlert or None
        """
        # Generate title based on regression type
        title = self._generate_title(regression)

        # Generate detailed message
        message = self._generate_message(regression)

        # Find suspected code if applicable
        suspected_code = self._find_suspected_code(regression)
        if suspected_code:
            regression.suspected_code = suspected_code
            message += f"\n\nSuspected code block:\n{suspected_code}"

        # Generate recommendations
        recommendations = self._generate_recommendations(regression)

        return PerformanceAlert(
            title=title,
            message=message,
            severity=regression.severity,
            endpoint_path=regression.endpoint_path,
            method=regression.method,
            metric_name=regression.regression_type.value,
            threshold_value=regression.previous_value,
            actual_value=regression.current_value,
            recommendations=recommendations,
        )

    def _generate_title(self, regression: PerformanceRegression) -> str:
        """Generate alert title based on regression type.

        Args:
            regression: Performance regression

        Returns:
            Alert title
        """
        endpoint = f"{regression.method} {regression.endpoint_path}"

        if regression.regression_type.value == "latency_increase":
            return f"Latency Increased: {endpoint}"
        elif regression.regression_type.value == "p95_increase":
            return f"P95 Latency Increased: {endpoint}"
        elif regression.regression_type.value == "p99_increase":
            return f"P99 Latency Increased: {endpoint}"
        elif regression.regression_type.value == "error_rate_increase":
            return f"Error Rate Increased: {endpoint}"
        elif regression.regression_type.value == "throughput_decrease":
            return f"Throughput Decreased: {endpoint}"
        else:
            return f"Performance Regression: {endpoint}"

    def _generate_message(self, regression: PerformanceRegression) -> str:
        """Generate detailed alert message.

        Args:
            regression: Performance regression

        Returns:
            Detailed message
        """
        endpoint = f"{regression.method} {regression.endpoint_path}"

        lines = [
            f"Endpoint: {endpoint}",
            f"Metric: {regression.regression_type.value.replace('_', ' ').title()}",
            "",
            f"Previous Value: {self._format_value(regression.previous_value, regression.regression_type.value)}",
            f"Current Value: {self._format_value(regression.current_value, regression.regression_type.value)}",
            f"Change: {regression.percentage_change:+.1f}%",
            "",
        ]

        # Add severity-specific message
        if regression.severity.value == "critical":
            lines.append(
                "⚠️ CRITICAL: This regression is severe and should be addressed immediately."
            )
        elif regression.severity.value == "warning":
            lines.append(
                "⚠️ WARNING: This regression is significant and may impact user experience."
            )
        else:
            lines.append(
                "ℹ️ INFO: Minor performance change detected. Monitor for further degradation."
            )

        # Add context about potential impact
        if regression.percentage_change > 100:
            lines.append(
                "\nThe latency has more than doubled, which will significantly impact user experience."
            )
        elif regression.percentage_change > 50:
            lines.append(
                "\nThe performance degradation is substantial and should be investigated."
            )

        return "\n".join(lines)

    def _format_value(self, value: float, metric_type: str) -> str:
        """Format a metric value based on its type.

        Args:
            value: Metric value
            metric_type: Type of metric

        Returns:
            Formatted value string
        """
        if "latency" in metric_type or "p95" in metric_type or "p99" in metric_type:
            return f"{value:.2f} ms"
        elif "rate" in metric_type:
            return f"{value:.2f}%"
        else:
            return f"{value:.2f}"

    def _generate_recommendations(self, regression: PerformanceRegression) -> List[str]:
        """Generate recommendations for fixing the regression.

        Args:
            regression: Performance regression

        Returns:
            List of recommendations
        """
        recommendations = []

        if regression.regression_type.value == "latency_increase":
            recommendations.extend(
                [
                    "Check for missing database indexes on queries used by this endpoint",
                    "Review recent database schema changes that might affect this endpoint",
                    "Consider implementing caching for this endpoint if data doesn't change frequently",
                    "Check for N+1 query problems in the endpoint implementation",
                    "Review if any new middleware is adding overhead to this endpoint",
                ]
            )
        elif regression.regression_type.value in ["p95_increase", "p99_increase"]:
            recommendations.extend(
                [
                    "Analyze slowest requests to identify edge cases",
                    "Check for unoptimized queries that only affect certain data patterns",
                    "Review timeout configurations for external service calls",
                    "Consider implementing request queuing or rate limiting",
                ]
            )
        elif regression.regression_type.value == "error_rate_increase":
            recommendations.extend(
                [
                    "Check error logs for the specific errors occurring",
                    "Review recent code changes that might have introduced bugs",
                    "Verify database connection pool settings",
                    "Check external service dependencies for failures",
                ]
            )
        elif regression.regression_type.value == "throughput_decrease":
            recommendations.extend(
                [
                    "Check server resource utilization (CPU, memory)",
                    "Review connection pool settings",
                    "Consider horizontal scaling if load has increased",
                    "Optimize hot code paths identified by profiling",
                ]
            )

        # Generic recommendations
        recommendations.extend(
            [
                "Run a profiler on this endpoint to identify bottlenecks",
                "Compare this endpoint's implementation with the previous version",
                "Check if any dependencies were updated recently",
            ]
        )

        return recommendations

    def _find_suspected_code(self, regression: PerformanceRegression) -> Optional[str]:
        """Find the code that might have caused the regression.

        Args:
            regression: Performance regression

        Returns:
            Code snippet or None
        """
        if not self.project_root:
            return None

        # Try to find controller/service based on endpoint path
        endpoint_parts = regression.endpoint_path.strip("/").split("/")
        if not endpoint_parts:
            return None

        # Look for patterns like UserController, user_service, etc.
        resource_name = endpoint_parts[0].replace("-", "_").replace(".", "_")

        patterns_to_search = [
            rf"class\s+{resource_name.title()}Controller",
            rf"class\s+{resource_name.title()}Service",
            rf"def\s+{resource_name}_",
            rf"def\s+get_{resource_name}",
            rf"def\s+create_{resource_name}",
            rf"def\s+update_{resource_name}",
            rf"def\s+delete_{resource_name}",
        ]

        for pattern in patterns_to_search:
            code = self._search_code(pattern)
            if code:
                return code

        return None

    def _search_code(self, pattern: str) -> Optional[str]:
        """Search for code pattern in project files.

        Args:
            pattern: Regex pattern to search for

        Returns:
            Code snippet or None
        """
        if not self.project_root:
            return None

        try:
            for py_file in self.project_root.rglob("*.py"):
                # Skip common directories
                if any(
                    skip in str(py_file)
                    for skip in ["__pycache__", "venv", ".venv", "node_modules"]
                ):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    if re.search(pattern, content, re.IGNORECASE):
                        # Find the function or class definition
                        match = re.search(
                            rf"({pattern}.*?(?:\n\n|\nclass |\ndef |$))",
                            content,
                            re.IGNORECASE | re.DOTALL,
                        )
                        if match:
                            code = match.group(1).strip()
                            # Limit to first 50 lines
                            lines = code.split("\n")
                            if len(lines) > 50:
                                code = "\n".join(lines[:50]) + "\n..."
                            return code
                except (UnicodeDecodeError, IOError):
                    continue

        except Exception:
            pass

        return None

    def generate_summary_report(
        self, report: PerformanceReport, regressions: List[PerformanceRegression]
    ) -> str:
        """Generate a human-readable summary report.

        Args:
            report: Performance report
            regressions: List of regressions

        Returns:
            Summary report text
        """
        lines = [
            "=" * 70,
            "AI-POWERED PERFORMANCE ANALYSIS REPORT",
            "=" * 70,
            "",
            f"Service: {report.service_name}",
            f"Test Run: {report.test_run_id}",
            f"Timestamp: {report.timestamp.isoformat()}",
            "",
            f"Total Requests: {report.total_requests}",
            f"Overall Avg Latency: {report.overall_avg_latency:.2f}ms",
            f"Endpoints Analyzed: {len(report.endpoints)}",
            "",
        ]

        if regressions:
            lines.extend(
                [
                    "REGRESSIONS DETECTED",
                    "-" * 70,
                    f"Total: {len(regressions)}",
                    "",
                ]
            )

            # Group by severity
            critical = [r for r in regressions if r.severity.value == "critical"]
            warnings = [r for r in regressions if r.severity.value == "warning"]
            info = [r for r in regressions if r.severity.value == "info"]

            if critical:
                lines.extend(["🔴 CRITICAL:", ""])
                for r in critical:
                    lines.append(
                        f"  - {r.method} {r.endpoint_path}: "
                        f"{r.percentage_change:+.1f}% ({r.regression_type.value})"
                    )
                lines.append("")

            if warnings:
                lines.extend(["🟡 WARNINGS:", ""])
                for r in warnings:
                    lines.append(
                        f"  - {r.method} {r.endpoint_path}: "
                        f"{r.percentage_change:+.1f}% ({r.regression_type.value})"
                    )
                lines.append("")

            if info:
                lines.extend(["ℹ️  INFO:", ""])
                for r in info:
                    lines.append(
                        f"  - {r.method} {r.endpoint_path}: {r.percentage_change:+.1f}%"
                    )
                lines.append("")
        else:
            lines.extend(
                [
                    "✅ NO REGRESSIONS DETECTED",
                    "",
                    "All endpoints are performing within expected thresholds.",
                    "",
                ]
            )

        lines.append("=" * 70)

        return "\n".join(lines)
