"""Report generator for visual traceability.

This module generates comprehensive reports including sequence diagrams
and logic flow visualizations from test execution traces.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.core.traceability.collector import TraceCollector
from socialseed_e2e.core.traceability.logic_mapper import LogicMapper
from socialseed_e2e.core.traceability.models import (
    LogicFlow,
    TestTrace,
    TraceReport,
)
from socialseed_e2e.core.traceability.sequence_diagram import SequenceDiagramGenerator


class TraceReporter:
    """Generates comprehensive traceability reports.

    This class generates HTML and Markdown reports that include:
    - Sequence diagrams (Mermaid.js and PlantUML)
    - Logic flow visualizations
    - Test execution statistics
    - Component interaction summaries

    Example:
        >>> reporter = TraceReporter(collector)
        >>> report = reporter.generate_report()
        >>> reporter.save_html_report(report, "output/trace_report.html")
        >>> reporter.save_markdown_report(report, "output/trace_report.md")
    """

    def __init__(self, collector: Optional[TraceCollector] = None):
        """Initialize the trace reporter.

        Args:
            collector: TraceCollector instance (uses global if None)
        """
        self.collector = collector
        self.diagram_generator = SequenceDiagramGenerator()
        self.logic_mapper = LogicMapper()

    def generate_report(
        self,
        title: Optional[str] = None,
        include_mermaid: bool = True,
        include_plantuml: bool = False,
        include_logic_flows: bool = True,
    ) -> TraceReport:
        """Generate a complete traceability report.

        Args:
            title: Report title
            include_mermaid: Include Mermaid.js diagrams
            include_plantuml: Include PlantUML diagrams
            include_logic_flows: Include logic flow visualizations

        Returns:
            Complete TraceReport
        """
        collector = self.collector
        if collector is None:
            from socialseed_e2e.core.traceability.collector import get_global_collector

            collector = get_global_collector()

        if collector is None:
            raise ValueError("No trace collector available")

        traces = collector.get_all_traces()

        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Generate sequence diagrams
        sequence_diagrams = []
        if include_mermaid or include_plantuml:
            for trace in traces:
                if include_mermaid:
                    mermaid = self.diagram_generator.generate_mermaid(trace)
                    sequence_diagrams.append(mermaid)

                if include_plantuml:
                    plantuml = self.diagram_generator.generate_plantuml(trace)
                    sequence_diagrams.append(plantuml)

        # Generate logic flows
        logic_flows = []
        if include_logic_flows:
            for trace in traces:
                flow = self.logic_mapper.map_logic_flow(trace)
                logic_flows.append(flow)

        # Generate summary
        summary = self._generate_summary(traces)

        return TraceReport(
            report_id=report_id,
            generated_at=datetime.now(),
            traces=traces,
            sequence_diagrams=sequence_diagrams,
            logic_flows=logic_flows,
            summary=summary,
        )

    def save_html_report(
        self, report: TraceReport, output_path: str, template: Optional[str] = None
    ) -> str:
        """Save report as HTML file.

        Args:
            report: TraceReport to save
            output_path: Path to output file
            template: Optional custom HTML template

        Returns:
            Path to saved file
        """
        if template:
            html_content = template
        else:
            html_content = self._generate_html_template()

        # Fill in report data
        html_content = self._fill_html_template(html_content, report)

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def save_markdown_report(self, report: TraceReport, output_path: str) -> str:
        """Save report as Markdown file.

        Args:
            report: TraceReport to save
            output_path: Path to output file

        Returns:
            Path to saved file
        """
        markdown_content = self._generate_markdown_report(report)

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return output_path

    def save_json_report(self, report: TraceReport, output_path: str) -> str:
        """Save report as JSON file.

        Args:
            report: TraceReport to save
            output_path: Path to output file

        Returns:
            Path to saved file
        """
        # Convert report to dict
        report_dict = self._report_to_dict(report)

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, default=str)

        return output_path

    def _generate_summary(self, traces: List[TestTrace]) -> Dict[str, Any]:
        """Generate summary statistics for traces.

        Args:
            traces: List of test traces

        Returns:
            Summary dictionary
        """
        if not traces:
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "total_interactions": 0,
                "total_components": 0,
                "total_logic_branches": 0,
                "average_test_duration_ms": 0,
            }

        total_duration = sum(t.get_duration_ms() for t in traces)

        # Get unique components
        all_components = set()
        for trace in traces:
            for comp in trace.components:
                all_components.add(comp.name)

        return {
            "total_tests": len(traces),
            "passed": sum(1 for t in traces if t.status == "passed"),
            "failed": sum(1 for t in traces if t.status in ("failed", "error")),
            "total_interactions": sum(len(t.interactions) for t in traces),
            "total_components": len(all_components),
            "total_logic_branches": sum(len(t.logic_branches) for t in traces),
            "average_test_duration_ms": total_duration / len(traces),
            "total_duration_ms": total_duration,
        }

    def _generate_html_template(self) -> str:
        """Generate default HTML template.

        Returns:
            HTML template string
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }

        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }

        h2 {
            color: #34495e;
            margin: 30px 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #ecf0f1;
        }

        h3 {
            color: #7f8c8d;
            margin: 20px 0 10px 0;
        }

        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .summary-card.success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }

        .summary-card.error {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }

        .summary-card h4 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }

        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
        }

        .test-trace {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
        }

        .test-trace h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }

        .status-badge.passed {
            background: #d4edda;
            color: #155724;
        }

        .status-badge.failed {
            background: #f8d7da;
            color: #721c24;
        }

        .status-badge.error {
            background: #fff3cd;
            color: #856404;
        }

        .mermaid {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
        }

        .logic-flow {
            background: white;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 10px 0;
        }

        .logic-flow h4 {
            color: #2c3e50;
            margin-bottom: 10px;
        }

        .branch {
            padding: 10px;
            margin: 8px 0;
            background: #f8f9fa;
            border-radius: 4px;
        }

        .branch-header {
            font-weight: bold;
            color: #495057;
        }

        .branch .condition {
            font-family: 'Courier New', monospace;
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }

        .branch .decision {
            color: #28a745;
            font-weight: bold;
        }

        .branch .reason {
            color: #6c757d;
            font-style: italic;
            font-size: 0.9em;
            margin-top: 5px;
        }

        .timestamp {
            color: #6c757d;
            font-size: 0.85em;
        }

        pre {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
        }

        code {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        .info-section {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 15px 0;
        }

        .warning-section {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        {{content}}
    </div>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose'
        });
    </script>
</body>
</html>"""

    def _fill_html_template(self, template: str, report: TraceReport) -> str:
        """Fill HTML template with report data.

        Args:
            template: HTML template
            report: TraceReport data

        Returns:
            Filled HTML content
        """
        title = f"Test Traceability Report - {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"

        content_parts = [f"<h1>{title}</h1>"]

        # Summary section
        content_parts.append("<h2>Summary</h2>")
        content_parts.append(self._generate_summary_html(report.summary))

        # Test traces section
        content_parts.append(f"<h2>Test Traces ({len(report.traces)})</h2>")

        for i, trace in enumerate(report.traces):
            content_parts.append(self._generate_trace_html(trace, i))

        # Sequence diagrams section
        if report.sequence_diagrams:
            content_parts.append(f"<h2>Sequence Diagrams ({len(report.sequence_diagrams)})</h2>")

            for diagram in report.sequence_diagrams:
                if diagram.format == "mermaid":
                    content_parts.append(f"<h3>{diagram.title}</h3>")
                    content_parts.append(f'<div class="mermaid">\n{diagram.content}\n</div>')

        # Logic flows section
        if report.logic_flows:
            content_parts.append(f"<h2>Logic Flows ({len(report.logic_flows)})</h2>")

            for flow in report.logic_flows:
                content_parts.append(self._generate_logic_flow_html(flow))

        content = "\n".join(content_parts)

        return template.replace("{{title}}", title).replace("{{content}}", content)

    def _generate_summary_html(self, summary: Dict[str, Any]) -> str:
        """Generate HTML for summary section.

        Args:
            summary: Summary dictionary

        Returns:
            HTML string
        """
        cards = [
            ("Total Tests", summary.get("total_tests", 0), ""),
            ("Passed", summary.get("passed", 0), "success"),
            ("Failed", summary.get("failed", 0), "error"),
            ("Total Interactions", summary.get("total_interactions", 0), ""),
            ("Components", summary.get("total_components", 0), ""),
            ("Logic Branches", summary.get("total_logic_branches", 0), ""),
        ]

        html = ['<div class="summary">']

        for label, value, css_class in cards:
            card_class = f"summary-card {css_class}".strip()
            html.append(
                f"""
                <div class="{card_class}">
                    <h4>{label}</h4>
                    <div class="value">{value}</div>
                </div>
            """
            )

        html.append("</div>")

        return "\n".join(html)

    def _generate_trace_html(self, trace: TestTrace, index: int) -> str:
        """Generate HTML for a test trace.

        Args:
            trace: TestTrace
            index: Trace index

        Returns:
            HTML string
        """
        status_class = trace.status
        duration = trace.get_duration_ms()

        html = f"""
        <div class="test-trace">
            <h3>{index + 1}. {trace.test_name}</h3>
            <span class="status-badge {status_class}">{trace.status}</span>
            <span class="timestamp">Duration: {duration:.0f}ms</span>
            <p>Service: {trace.service_name}</p>
            <p>Interactions: {len(trace.interactions)} | Logic Branches: {len(trace.logic_branches)}</p>
        </div>
        """

        return html

    def _generate_logic_flow_html(self, flow: LogicFlow) -> str:
        """Generate HTML for a logic flow.

        Args:
            flow: LogicFlow

        Returns:
            HTML string
        """
        html = f"""
        <div class="logic-flow">
            <h4>{flow.title}</h4>
            <p>Decision Points: {flow.decision_points}</p>
        """

        for branch in flow.branches:
            html += f"""
            <div class="branch">
                <div class="branch-header">{branch.type.name}</div>
                <div>Condition: <span class="condition">{branch.condition}</span></div>
                <div class="decision">→ {branch.decision}</div>
                {f'<div class="reason">{branch.reason}</div>' if branch.reason else ""}
            </div>
            """

        html += "</div>"

        return html

    def _generate_markdown_report(self, report: TraceReport) -> str:
        """Generate Markdown report content.

        Args:
            report: TraceReport

        Returns:
            Markdown string
        """
        lines = [
            "# Test Traceability Report",
            "",
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Report ID:** {report.report_id}",
            "",
            "## Summary",
            "",
        ]

        # Summary table
        summary = report.summary
        lines.extend(
            [
                "| Metric | Value |",
                "|--------|-------|",
                f"| Total Tests | {summary.get('total_tests', 0)} |",
                f"| Passed | {summary.get('passed', 0)} |",
                f"| Failed | {summary.get('failed', 0)} |",
                f"| Total Interactions | {summary.get('total_interactions', 0)} |",
                f"| Total Components | {summary.get('total_components', 0)} |",
                f"| Total Logic Branches | {summary.get('total_logic_branches', 0)} |",
                f"| Average Duration | {summary.get('average_test_duration_ms', 0):.0f}ms |",
                "",
            ]
        )

        # Test traces
        lines.extend(
            [
                f"## Test Traces ({len(report.traces)})",
                "",
            ]
        )

        for i, trace in enumerate(report.traces):
            status_emoji = "✅" if trace.status == "passed" else "❌"
            lines.extend(
                [
                    f"### {i + 1}. {trace.test_name}",
                    "",
                    f"- **Status:** {status_emoji} {trace.status}",
                    f"- **Service:** {trace.service_name}",
                    f"- **Duration:** {trace.get_duration_ms():.0f}ms",
                    f"- **Interactions:** {len(trace.interactions)}",
                    f"- **Logic Branches:** {len(trace.logic_branches)}",
                    "",
                ]
            )

        # Sequence diagrams
        if report.sequence_diagrams:
            lines.extend(
                [
                    f"## Sequence Diagrams ({len(report.sequence_diagrams)})",
                    "",
                ]
            )

            for diagram in report.sequence_diagrams:
                lines.extend(
                    [
                        f"### {diagram.title}",
                        "",
                        f"**Format:** {diagram.format}",
                        "",
                        "```",
                        diagram.content,
                        "```",
                        "",
                    ]
                )

        # Logic flows
        if report.logic_flows:
            lines.extend(
                [
                    f"## Logic Flows ({len(report.logic_flows)})",
                    "",
                ]
            )

            for flow in report.logic_flows:
                lines.append(flow.flow_description)
                lines.append("")

        return "\n".join(lines)

    def _report_to_dict(self, report: TraceReport) -> Dict[str, Any]:
        """Convert TraceReport to dictionary.

        Args:
            report: TraceReport

        Returns:
            Dictionary representation
        """
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "summary": report.summary,
            "traces": [
                {
                    "test_id": t.test_id,
                    "test_name": t.test_name,
                    "service_name": t.service_name,
                    "status": t.status,
                    "duration_ms": t.get_duration_ms(),
                    "interactions_count": len(t.interactions),
                    "logic_branches_count": len(t.logic_branches),
                    "components": [c.name for c in t.components],
                }
                for t in report.traces
            ],
            "sequence_diagrams": [
                {
                    "title": d.title,
                    "format": d.format,
                    "components": d.components,
                    "interactions_count": d.interactions_count,
                }
                for d in report.sequence_diagrams
            ],
            "logic_flows": [
                {
                    "title": f.title,
                    "decision_points": f.decision_points,
                }
                for f in report.logic_flows
            ],
        }
