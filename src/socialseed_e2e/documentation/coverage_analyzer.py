"""Coverage analysis for test documentation.

This module analyzes test coverage including endpoint coverage,
scenario coverage, and gap analysis.
"""

from typing import List, Dict, Any, Set, Optional
from pathlib import Path
from datetime import datetime

from .models import CoverageReport, TestCaseDoc, EndpointDoc


class CoverageAnalyzer:
    """Analyze test coverage for API endpoints and scenarios."""

    def __init__(self):
        """Initialize the coverage analyzer."""
        self.known_endpoints: Set[str] = set()
        self.known_scenarios: Set[str] = set()

    def load_known_endpoints(self, paths: List[str]):
        """Load known API endpoints from OpenAPI spec or other sources.

        Args:
            paths: List of file paths to OpenAPI/ Swagger specs
        """
        import json
        import yaml

        for path in paths:
            try:
                with open(path, "r") as f:
                    if path.endswith(".json"):
                        spec = json.load(f)
                    else:
                        spec = yaml.safe_load(f)

                    paths_dict = spec.get("paths", {})
                    for path, methods in paths_dict.items():
                        for method in methods.keys():
                            if method.upper() in [
                                "GET",
                                "POST",
                                "PUT",
                                "PATCH",
                                "DELETE",
                                "HEAD",
                                "OPTIONS",
                            ]:
                                self.known_endpoints.add(f"{method.upper()} {path}")

            except Exception as e:
                print(f"Warning: Could not load endpoints from {path}: {e}")

    def add_endpoint(self, method: str, path: str):
        """Add a known endpoint to track.

        Args:
            method: HTTP method
            path: API path
        """
        self.known_endpoints.add(f"{method.upper()} {path}")

    def add_scenario(self, scenario: str):
        """Add a known scenario to track.

        Args:
            scenario: Scenario name
        """
        self.known_scenarios.add(scenario)

    def analyze_coverage(
        self,
        test_cases: List[TestCaseDoc],
        endpoints: Optional[List[EndpointDoc]] = None,
    ) -> CoverageReport:
        """Analyze test coverage.

        Args:
            test_cases: List of test case documents
            endpoints: Optional list of documented endpoints

        Returns:
            CoverageReport with coverage metrics
        """
        covered_endpoints = set()
        covered_scenarios = set()

        if endpoints:
            for endpoint in endpoints:
                key = f"{endpoint.method.upper()} {endpoint.path}"
                if endpoint.test_count > 0:
                    covered_endpoints.add(key)

        for test_case in test_cases:
            scenario_key = f"{test_case.service}:{test_case.test_name}"
            covered_scenarios.add(scenario_key)

            for step in test_case.steps:
                action = step.action.upper()
                if any(m in action for m in ["GET", "POST", "PUT", "PATCH", "DELETE"]):
                    for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                        if method in action:
                            covered_endpoints.add(f"{method} /api/{test_case.service}")
                            break

        uncovered_endpoints = list(self.known_endpoints - covered_endpoints)

        endpoint_coverage_percent = 0.0
        if self.known_endpoints:
            endpoint_coverage_percent = (
                len(covered_endpoints) / len(self.known_endpoints)
            ) * 100

        gap_analysis = self._generate_gap_analysis(
            uncovered_endpoints, covered_scenarios
        )

        return CoverageReport(
            total_endpoints=len(self.known_endpoints),
            covered_endpoints=len(covered_endpoints),
            uncovered_endpoints=uncovered_endpoints,
            endpoint_coverage_percent=round(endpoint_coverage_percent, 2),
            total_scenarios=len(self.known_scenarios),
            covered_scenarios=list(covered_scenarios),
            gap_analysis=gap_analysis,
        )

    def _generate_gap_analysis(
        self, uncovered_endpoints: List[str], covered_scenarios: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate gap analysis for uncovered endpoints.

        Args:
            uncovered_endpoints: List of endpoints not covered by tests
            covered_scenarios: List of covered scenarios

        Returns:
            List of gap analysis items
        """
        gaps = []

        for endpoint in uncovered_endpoints:
            gaps.append(
                {
                    "type": "endpoint",
                    "item": endpoint,
                    "severity": self._estimate_severity(endpoint),
                    "recommendation": self._generate_recommendation(endpoint),
                }
            )

        uncovered_scenarios = self.known_scenarios - set(covered_scenarios)
        for scenario in uncovered_scenarios:
            gaps.append(
                {
                    "type": "scenario",
                    "item": scenario,
                    "severity": "medium",
                    "recommendation": f"Add test cases for scenario: {scenario}",
                }
            )

        return sorted(
            gaps,
            key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
                x["severity"], 4
            ),
        )

    def _estimate_severity(self, endpoint: str) -> str:
        """Estimate the severity of an uncovered endpoint.

        Args:
            endpoint: Endpoint string (e.g., 'GET /api/users')

        Returns:
            Severity level
        """
        endpoint_lower = endpoint.lower()

        if (
            "auth" in endpoint_lower
            or "login" in endpoint_lower
            or "password" in endpoint_lower
        ):
            return "critical"
        elif (
            "payment" in endpoint_lower
            or "transaction" in endpoint_lower
            or "billing" in endpoint_lower
        ):
            return "high"
        elif "delete" in endpoint_lower or "remove" in endpoint_lower:
            return "high"

        return "medium"

    def _generate_recommendation(self, endpoint: str) -> str:
        """Generate a recommendation for an uncovered endpoint.

        Args:
            endpoint: Endpoint string

        Returns:
            Recommendation string
        """
        method = endpoint.split()[0] if " " in endpoint else "GET"
        path = endpoint.split()[1] if " " in endpoint else endpoint

        recommendations = {
            "GET": f"Add GET test for {path} - verify response status and body structure",
            "POST": f"Add POST test for {path} - verify resource creation and validation",
            "PUT": f"Add PUT test for {path} - verify resource update and partial update",
            "PATCH": f"Add PATCH test for {path} - verify partial update behavior",
            "DELETE": f"Add DELETE test for {path} - verify resource deletion and cleanup",
        }

        return recommendations.get(method, f"Add test case for {endpoint}")

    def get_coverage_summary(self, coverage: CoverageReport) -> Dict[str, Any]:
        """Get a summary of coverage metrics.

        Args:
            coverage: CoverageReport object

        Returns:
            Dictionary with summary metrics
        """
        return {
            "endpoint_coverage": f"{coverage.endpoint_coverage_percent:.1f}%",
            "endpoints_covered": f"{coverage.covered_endpoints}/{coverage.total_endpoints}",
            "total_gaps": len(coverage.gap_analysis),
            "critical_gaps": len(
                [g for g in coverage.gap_analysis if g["severity"] == "critical"]
            ),
            "high_gaps": len(
                [g for g in coverage.gap_analysis if g["severity"] == "high"]
            ),
            "medium_gaps": len(
                [g for g in coverage.gap_analysis if g["severity"] == "medium"]
            ),
            "low_gaps": len(
                [g for g in coverage.gap_analysis if g["severity"] == "low"]
            ),
        }

    def export_coverage_report(
        self, coverage: CoverageReport, format: str = "markdown"
    ) -> str:
        """Export coverage report in specified format.

        Args:
            coverage: CoverageReport object
            format: Output format ('markdown', 'json', 'html')

        Returns:
            Formatted report string
        """
        if format == "json":
            return coverage.model_dump_json(indent=2)

        elif format == "markdown":
            return self._export_markdown(coverage)

        elif format == "html":
            return self._export_html(coverage)

        return str(coverage)

    def _export_markdown(self, coverage: CoverageReport) -> str:
        """Export coverage report as Markdown."""
        lines = [
            "# Test Coverage Report",
            "",
            f"**Generated:** {coverage.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Endpoint Coverage:** {coverage.endpoint_coverage_percent:.1f}%",
            f"- **Covered Endpoints:** {coverage.covered_endpoints}/{coverage.total_endpoints}",
            f"- **Covered Scenarios:** {len(coverage.covered_scenarios)}",
            "",
        ]

        if coverage.uncovered_endpoints:
            lines.extend(
                [
                    "## Uncovered Endpoints",
                    "",
                    *[f"- {ep}" for ep in coverage.uncovered_endpoints],
                    "",
                ]
            )

        if coverage.gap_analysis:
            lines.extend(
                [
                    "## Gap Analysis",
                    "",
                    "| Item | Type | Severity | Recommendation |",
                    "|------|------|----------|----------------|",
                    *[
                        f"| {g['item']} | {g['type']} | {g['severity']} | {g['recommendation']} |"
                        for g in coverage.gap_analysis
                    ],
                    "",
                ]
            )

        return "\n".join(lines)

    def _export_html(self, coverage: CoverageReport) -> str:
        """Export coverage report as HTML."""
        summary = self.get_coverage_summary(coverage)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Coverage Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .severity-critical {{ color: #d32f2f; }}
        .severity-high {{ color: #f57c00; }}
        .severity-medium {{ color: #fbc02d; }}
        .severity-low {{ color: #388e3c; }}
    </style>
</head>
<body>
    <h1>Test Coverage Report</h1>
    <p>Generated: {coverage.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">
            <div class="metric-value">{summary["endpoint_coverage"]}</div>
            <div>Endpoint Coverage</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary["endpoints_covered"]}</div>
            <div>Endpoints Covered</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary["total_gaps"]}</div>
            <div>Total Gaps</div>
        </div>
    </div>
</body>
</html>
"""
        return html
