"""Documentation exporter for multiple formats.

This module handles exporting documentation to various formats
including Markdown, HTML, PDF, and OpenAPI.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .models import (
    APIDocumentation,
    CoverageReport,
    DocFormat,
    DocumentationProject,
    TestCaseDoc,
)


class DocumentationExporter:
    """Export documentation to various formats."""

    def __init__(self, output_dir: str = "docs"):
        """Initialize the documentation exporter.

        Args:
            output_dir: Directory to save exported documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_project(
        self, project: DocumentationProject, format: DocFormat = DocFormat.MARKDOWN
    ) -> Path:
        """Export entire documentation project.

        Args:
            project: DocumentationProject to export
            format: Output format

        Returns:
            Path to exported file
        """
        if format == DocFormat.MARKDOWN:
            return self._export_markdown(project)
        elif format == DocFormat.HTML:
            return self._export_html(project)
        elif format == DocFormat.OPENAPI:
            return self._export_openapi(project)

        raise ValueError(f"Unsupported format: {format}")

    def export_test_cases(
        self, test_cases: List[TestCaseDoc], format: DocFormat = DocFormat.MARKDOWN
    ) -> Path:
        """Export test case documentation.

        Args:
            test_cases: List of test case documents
            format: Output format

        Returns:
            Path to exported file
        """
        if format == DocFormat.MARKDOWN:
            return self._export_test_cases_markdown(test_cases)
        elif format == DocFormat.HTML:
            return self._export_test_cases_html(test_cases)

        raise ValueError(f"Unsupported format: {format}")

    def export_api_docs(
        self, api_docs: APIDocumentation, format: DocFormat = DocFormat.MARKDOWN
    ) -> Path:
        """Export API documentation.

        Args:
            api_docs: APIDocumentation to export
            format: Output format

        Returns:
            Path to exported file
        """
        if format == DocFormat.MARKDOWN:
            return self._export_api_docs_markdown(api_docs)
        elif format == DocFormat.HTML:
            return self._export_api_docs_html(api_docs)
        elif format == DocFormat.OPENAPI:
            return self._export_openapi_spec(api_docs)

        raise ValueError(f"Unsupported format: {format}")

    def export_coverage_report(
        self, coverage: CoverageReport, format: DocFormat = DocFormat.MARKDOWN
    ) -> Path:
        """Export coverage report.

        Args:
            coverage: CoverageReport to export
            format: Output format

        Returns:
            Path to exported file
        """
        if format == DocFormat.MARKDOWN:
            return self._export_coverage_markdown(coverage)
        elif format == DocFormat.HTML:
            return self._export_coverage_html(coverage)

        raise ValueError(f"Unsupported format: {format}")

    def _export_markdown(self, project: DocumentationProject) -> Path:
        """Export project as Markdown."""
        lines = [
            f"# {project.project_name} - Test Documentation",
            "",
            f"**Generated:** {project.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Version:** {project.version}",
            "",
        ]

        if project.api_docs:
            lines.extend(
                [
                    "# API Documentation",
                    "",
                    self._format_api_docs_markdown(project.api_docs),
                    "",
                ]
            )

        if project.test_cases:
            lines.extend(
                [
                    "# Test Cases",
                    "",
                    *[self._format_test_case_markdown(tc) for tc in project.test_cases],
                    "",
                ]
            )

        if project.coverage_report:
            lines.extend(
                [
                    "# Coverage Report",
                    "",
                    self._format_coverage_markdown(project.coverage_report),
                    "",
                ]
            )

        output_path = self.output_dir / f"{project.project_name}_docs.md"
        output_path.write_text("\n".join(lines))
        return output_path

    def _format_test_case_markdown(self, tc: TestCaseDoc) -> str:
        """Format a test case as Markdown."""
        lines = [
            f"## {tc.test_name}",
            "",
            f"**ID:** {tc.test_id}",
            f"**Module:** {tc.module}",
            f"**Service:** {tc.service}",
            f"**Severity:** {tc.severity}",
            "",
            "### Description",
            "",
            tc.description,
            "",
        ]

        if tc.steps:
            lines.extend(
                [
                    "### Test Steps",
                    "",
                    *[
                        f"{step.step_number}. **{step.description}**\n   - Action: `{step.action}`\n   - Expected: {step.expected_result}"
                        for step in tc.steps
                    ],
                    "",
                ]
            )

        if tc.tags:
            lines.append(f"**Tags:** {', '.join(tc.tags)}")
            lines.append("")

        return "\n".join(lines)

    def _format_api_docs_markdown(self, api_docs: APIDocumentation) -> str:
        """Format API docs as Markdown."""
        lines = [
            f"## {api_docs.title}",
            f"**Version:** {api_docs.version}",
            f"**Base URL:** {api_docs.base_url}",
            "",
        ]

        for endpoint in api_docs.endpoints:
            lines.extend(
                [
                    f"### {endpoint.method} {endpoint.path}",
                    "",
                    f"**Summary:** {endpoint.summary}",
                    "",
                ]
            )

            if endpoint.description:
                lines.append(endpoint.description)
                lines.append("")

            if endpoint.parameters:
                lines.extend(
                    [
                        "**Parameters:**",
                        "",
                        "| Name | In | Type | Required |",
                        "|------|----|------|----------|",
                        *[
                            f"| {p['name']} | {p['in']} | {p['type']} | {p.get('required', False)} |"
                            for p in endpoint.parameters
                        ],
                        "",
                    ]
                )

            if endpoint.responses:
                lines.extend(
                    [
                        "**Responses:**",
                        "",
                        *[
                            f"- **{status}**: {resp.get('description', 'No description')}"
                            for status, resp in endpoint.responses.items()
                        ],
                        "",
                    ]
                )

        if api_docs.error_codes:
            lines.extend(
                [
                    "## Error Codes",
                    "",
                    "| Code | Message | Description |",
                    "|------|---------|------------|",
                    *[
                        f"| {ec.code} | {ec.message} | {ec.description} |"
                        for ec in api_docs.error_codes
                    ],
                    "",
                ]
            )

        return "\n".join(lines)

    def _format_coverage_markdown(self, coverage: CoverageReport) -> str:
        """Format coverage report as Markdown."""
        lines = [
            f"**Endpoint Coverage:** {coverage.endpoint_coverage_percent:.1f}%",
            f"**Covered Endpoints:** {coverage.covered_endpoints}/{coverage.total_endpoints}",
            "",
        ]

        if coverage.uncovered_endpoints:
            lines.extend(
                [
                    "### Uncovered Endpoints",
                    "",
                    *[f"- {ep}" for ep in coverage.uncovered_endpoints],
                    "",
                ]
            )

        if coverage.gap_analysis:
            lines.extend(
                [
                    "### Gap Analysis",
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

    def _export_test_cases_markdown(self, test_cases: List[TestCaseDoc]) -> Path:
        """Export test cases as Markdown."""
        lines = [
            "# Test Case Documentation",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Tests:** {len(test_cases)}",
            "",
            "## Table of Contents",
            "",
        ]

        lines.extend([f"- [{tc.test_name}](#{tc.test_id})" for tc in test_cases])
        lines.append("")

        for tc in test_cases:
            lines.append(self._format_test_case_markdown(tc))

        output_path = self.output_dir / "test_cases.md"
        output_path.write_text("\n".join(lines))
        return output_path

    def _export_test_cases_html(self, test_cases: List[TestCaseDoc]) -> Path:
        """Export test cases as HTML."""
        html_parts = ["<!DOCTYPE html><html><head><title>Test Cases</title>"]
        html_parts.append(
            "<style>body{font-family:Arial;margin:20px}table{width:100%;border-collapse:collapse}"
        )
        html_parts.append(
            "th,td{border:1px solid #ddd;padding:8px;text-align:left}</style></head><body>"
        )
        html_parts.append("<h1>Test Case Documentation</h1>")
        html_parts.append(
            f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        )
        html_parts.append(f"<p>Total Tests: {len(test_cases)}</p>")
        html_parts.append(
            "<table><tr><th>ID</th><th>Name</th><th>Service</th><th>Severity</th></tr>"
        )

        for tc in test_cases:
            html_parts.append(
                f"<tr><td>{tc.test_id}</td><td>{tc.test_name}</td><td>{tc.service}</td><td>{tc.severity}</td></tr>"
            )

        html_parts.append("</table></body></html>")

        output_path = self.output_dir / "test_cases.html"
        output_path.write_text("".join(html_parts))
        return output_path

    def _export_api_docs_markdown(self, api_docs: APIDocumentation) -> Path:
        """Export API docs as Markdown."""
        output_path = self.output_dir / "api_docs.md"
        output_path.write_text(self._format_api_docs_markdown(api_docs))
        return output_path

    def _export_api_docs_html(self, api_docs: APIDocumentation) -> Path:
        """Export API docs as HTML."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{api_docs.title}</title>
    <style>
        body {{ font-family: Arial, margin: 20px; }}
        .endpoint {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .method {{ font-weight: bold; padding: 3px 8px; border-radius: 3px; }}
        .GET {{ background: #61affe; color: white; }}
        .POST {{ background: #49cc90; color: white; }}
        .PUT {{ background: #fca130; color: white; }}
        .DELETE {{ background: #f93e3e; color: white; }}
    </style>
</head>
<body>
    <h1>{api_docs.title}</h1>
    <p>Version: {api_docs.version}</p>
    <p>Base URL: {api_docs.base_url}</p>
"""

        for endpoint in api_docs.endpoints:
            html += f"""
    <div class="endpoint">
        <span class="method {endpoint.method}">{endpoint.method}</span>
        <strong>{endpoint.path}</strong>
        <p>{endpoint.summary}</p>
    </div>
"""

        html += "</body></html>"

        output_path = self.output_dir / "api_docs.html"
        output_path.write_text(html)
        return output_path

    def _export_openapi(self, project: DocumentationProject) -> Path:
        """Export project as OpenAPI spec."""
        if not project.api_docs:
            raise ValueError("No API documentation available")

        return self._export_openapi_spec(project.api_docs)

    def _export_openapi_spec(self, api_docs: APIDocumentation) -> Path:
        """Export API docs as OpenAPI specification."""
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": api_docs.title,
                "version": api_docs.version,
                "description": api_docs.description or "",
            },
            "servers": [{"url": api_docs.base_url}],
            "paths": {},
            "components": {
                "schemas": api_docs.schemas,
                "securitySchemes": {},
            },
        }

        for endpoint in api_docs.endpoints:
            path_item = openapi_spec["paths"].setdefault(endpoint.path, {})

            method_lower = endpoint.method.lower()
            path_item[method_lower] = {
                "summary": endpoint.summary,
                "description": endpoint.description or "",
                "tags": endpoint.tags,
                "parameters": endpoint.parameters,
                "requestBody": {
                    "content": {
                        "application/json": {"schema": endpoint.request_body or {}}
                    }
                }
                if endpoint.request_body
                else None,
                "responses": {
                    status: {"description": resp.get("description", "")}
                    for status, resp in endpoint.responses.items()
                },
            }

        output_path = self.output_dir / "openapi.json"
        output_path.write_text(json.dumps(openapi_spec, indent=2))
        return output_path

    def _export_coverage_markdown(self, coverage: CoverageReport) -> Path:
        """Export coverage report as Markdown."""
        output_path = self.output_dir / "coverage_report.md"
        output_path.write_text(self._format_coverage_markdown(coverage))
        return output_path

    def _export_coverage_html(self, coverage: CoverageReport) -> Path:
        """Export coverage report as HTML."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Coverage Report</title>
    <style>
        body {{ font-family: Arial, margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px 30px; text-align: center; }}
        .metric-value {{ font-size: 32px; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Test Coverage Report</h1>
    <p>Generated: {coverage.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
    <div class="summary">
        <div class="metric">
            <div class="metric-value">{coverage.endpoint_coverage_percent:.1f}%</div>
            <div>Endpoint Coverage</div>
        </div>
        <div class="metric">
            <div class="metric-value">{coverage.covered_endpoints}/{coverage.total_endpoints}</div>
            <div>Endpoints Covered</div>
        </div>
    </div>
</body>
</html>
"""

        output_path = self.output_dir / "coverage_report.html"
        output_path.write_text(html)
        return output_path
