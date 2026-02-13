"""Heatmap Generator - Generates visual heat-map reports.

This module provides HTML and CLI visualization of regression risk levels.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from socialseed_e2e.risk_analyzer.risk_scorer import RiskResult


@dataclass
class HeatmapReport:
    """Complete heat-map report with all analysis data."""

    generated_at: datetime
    base_ref: str
    total_endpoints: int
    risk_results: List[RiskResult]
    summary: Dict
    recommendations: List[str]
    metadata: Dict = field(default_factory=dict)


class HeatmapGenerator:
    """Generates visual heat-map reports for regression risk."""

    # Risk level colors
    RISK_COLORS = {
        "high": {"bg": "#FF4444", "text": "#FFFFFF", "emoji": "🔴"},
        "medium": {"bg": "#FFA500", "text": "#000000", "emoji": "🟡"},
        "low": {"bg": "#44AA44", "text": "#FFFFFF", "emoji": "🟢"},
    }

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the heatmap generator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir) if output_dir else Path(".e2e/heatmaps")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_cli_output(
        self,
        risk_results: List[RiskResult],
        summary: Dict,
        base_ref: str = "main",
    ) -> str:
        """Generate CLI-formatted heat-map output.

        Args:
            risk_results: List of risk results
            summary: Summary statistics
            base_ref: Git reference used for comparison

        Returns:
            Formatted string for CLI display
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("🗺️  REGRESSION RISK HEAT-MAP")
        lines.append("=" * 80)
        lines.append(f"Base Reference: {base_ref}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary
        lines.append("📊 SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Endpoints Analyzed: {summary['total_endpoints']}")
        lines.append(f"🔴 High Risk: {summary['high_risk']}")
        lines.append(f"🟡 Medium Risk: {summary['medium_risk']}")
        lines.append(f"🟢 Low Risk: {summary['low_risk']}")
        lines.append(f"Average Risk Score: {summary['average_score']}/100")
        lines.append("")

        # High Risk Endpoints
        high_risk = [r for r in risk_results if r.risk_level == "high"]
        if high_risk:
            lines.append("🔴 HIGH RISK (Score: 70-100)")
            lines.append("-" * 80)
            for result in high_risk:
                lines.append(f"  {result.http_method} {result.endpoint_path}")
                lines.append(f"    Score: {result.risk_score}/100")
                lines.append(f"    Files: {', '.join(result.affected_files[:3])}")
                if result.historical_failures > 0:
                    lines.append(
                        f"    ⚠️  {result.historical_failures} historical failures"
                    )
                lines.append("")

        # Medium Risk Endpoints
        medium_risk = [r for r in risk_results if r.risk_level == "medium"]
        if medium_risk:
            lines.append("🟡 MEDIUM RISK (Score: 40-69)")
            lines.append("-" * 80)
            for result in medium_risk:
                lines.append(f"  {result.http_method} {result.endpoint_path}")
                lines.append(f"    Score: {result.risk_score}/100")
                lines.append("")

        # Low Risk Endpoints
        low_risk = [r for r in risk_results if r.risk_level == "low"]
        if low_risk:
            lines.append("🟢 LOW RISK (Score: 0-39)")
            lines.append("-" * 80)
            lines.append(f"  {len(low_risk)} endpoints with low risk")
            lines.append("")

        # Prioritized Test List
        lines.append("🎯 PRIORITIZED TEST EXECUTION ORDER")
        lines.append("-" * 80)
        for i, result in enumerate(risk_results[:10], 1):
            emoji = self.RISK_COLORS[result.risk_level]["emoji"]
            lines.append(
                f"{i:2}. {emoji} {result.http_method} {result.endpoint_path} "
                f"(Score: {result.risk_score})"
            )

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_html_report(
        self,
        report: HeatmapReport,
        output_file: Optional[str] = None,
    ) -> Path:
        """Generate HTML heat-map report.

        Args:
            report: Heatmap report data
            output_file: Output file path (optional)

        Returns:
            Path to generated HTML file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"risk_heatmap_{timestamp}.html"
        else:
            output_file = Path(output_file)

        html_content = self._build_html(report)
        output_file.write_text(html_content, encoding="utf-8")

        return output_file

    def _build_html(self, report: HeatmapReport) -> str:
        """Build HTML content for the report."""
        html_parts = []

        # HTML Head
        html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Regression Risk Heat-Map</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .card.high-risk { border-top: 4px solid #FF4444; }
        .card.medium-risk { border-top: 4px solid #FFA500; }
        .card.low-risk { border-top: 4px solid #44AA44; }
        .card h3 { font-size: 2em; margin-bottom: 5px; }
        .card p { color: #666; }
        .heatmap-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .endpoint-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .endpoint-card:hover { transform: translateY(-2px); }
        .endpoint-header {
            padding: 15px;
            color: white;
            font-weight: bold;
        }
        .endpoint-header.high { background: #FF4444; }
        .endpoint-header.medium { background: #FFA500; }
        .endpoint-header.low { background: #44AA44; }
        .endpoint-body {
            padding: 15px;
        }
        .endpoint-method {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 10px;
        }
        .endpoint-path { font-family: monospace; font-size: 1.1em; }
        .score-bar {
            height: 8px;
            background: #eee;
            border-radius: 4px;
            margin: 10px 0;
            overflow: hidden;
        }
        .score-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s;
        }
        .factors-list {
            margin-top: 10px;
            font-size: 0.9em;
        }
        .factor-item {
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            border-bottom: 1px solid #eee;
        }
        .recommendations {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .recommendations h2 { margin-bottom: 15px; }
        .recommendations ul { margin-left: 20px; }
        .recommendations li { margin-bottom: 8px; }
        .timestamp {
            text-align: center;
            color: #999;
            margin-top: 30px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">""")

        # Header
        html_parts.append(f"""
        <div class="header">
            <h1>🗺️ Regression Risk Heat-Map</h1>
            <p>Base Reference: {report.base_ref} | Generated: {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>""")

        # Summary Cards
        summary = report.summary
        html_parts.append(f"""
        <div class="summary-cards">
            <div class="card high-risk">
                <h3>{summary["high_risk"]}</h3>
                <p>High Risk Endpoints</p>
            </div>
            <div class="card medium-risk">
                <h3>{summary["medium_risk"]}</h3>
                <p>Medium Risk Endpoints</p>
            </div>
            <div class="card low-risk">
                <h3>{summary["low_risk"]}</h3>
                <p>Low Risk Endpoints</p>
            </div>
            <div class="card">
                <h3>{summary["average_score"]}</h3>
                <p>Average Risk Score</p>
            </div>
        </div>""")

        # Heatmap Grid
        html_parts.append('<div class="heatmap-grid">')

        for result in report.risk_results:
            risk_class = result.risk_level
            score_percent = result.risk_score

            # Determine color based on score
            if result.risk_score >= 70:
                fill_color = "#FF4444"
            elif result.risk_score >= 40:
                fill_color = "#FFA500"
            else:
                fill_color = "#44AA44"

            html_parts.append(f"""
            <div class="endpoint-card">
                <div class="endpoint-header {risk_class}">
                    Risk Score: {result.risk_score}/100
                </div>
                <div class="endpoint-body">
                    <div>
                        <span class="endpoint-method">{result.http_method}</span>
                        <span class="endpoint-path">{result.endpoint_path}</span>
                    </div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {score_percent}%; background: {fill_color};"></div>
                    </div>
                    <div class="factors-list">""")

            # Add factors
            for factor, value in result.factors.items():
                html_parts.append(f"""
                        <div class="factor-item">
                            <span>{factor.replace("_", " ").title()}</span>
                            <span>{value:.1f}</span>
                        </div>""")

            html_parts.append("""
                    </div>
                </div>
            </div>""")

        html_parts.append("</div>")  # Close heatmap-grid

        # Recommendations
        if report.recommendations:
            html_parts.append("""
        <div class="recommendations">
            <h2>📋 Recommendations</h2>
            <ul>""")

            for rec in report.recommendations[:10]:  # Limit to 10
                html_parts.append(f"<li>{rec}</li>")

            html_parts.append("""
            </ul>
        </div>""")

        # Footer
        html_parts.append(f"""
        <div class="timestamp">
            Report generated by socialseed-e2e Risk Analyzer
        </div>
    </div>
</body>
</html>""")

        return "\n".join(html_parts)

    def generate_json_report(
        self,
        report: HeatmapReport,
        output_file: Optional[str] = None,
    ) -> Path:
        """Generate JSON heat-map report.

        Args:
            report: Heatmap report data
            output_file: Output file path (optional)

        Returns:
            Path to generated JSON file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"risk_heatmap_{timestamp}.json"
        else:
            output_file = Path(output_file)

        # Convert to serializable format
        data = {
            "generated_at": report.generated_at.isoformat(),
            "base_ref": report.base_ref,
            "total_endpoints": report.total_endpoints,
            "summary": report.summary,
            "recommendations": report.recommendations,
            "endpoints": [],
        }

        for result in report.risk_results:
            data["endpoints"].append(
                {
                    "path": result.endpoint_path,
                    "method": result.http_method,
                    "risk_score": result.risk_score,
                    "risk_level": result.risk_level,
                    "factors": result.factors,
                    "affected_files": result.affected_files,
                    "historical_failures": result.historical_failures,
                    "recommendations": result.recommendations,
                }
            )

        output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        return output_file

    def generate_markdown_report(
        self,
        report: HeatmapReport,
        output_file: Optional[str] = None,
    ) -> Path:
        """Generate Markdown heat-map report.

        Args:
            report: Heatmap report data
            output_file: Output file path (optional)

        Returns:
            Path to generated Markdown file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"risk_heatmap_{timestamp}.md"
        else:
            output_file = Path(output_file)

        lines = []

        # Header
        lines.append("# 🗺️ Regression Risk Heat-Map Report\n")
        lines.append(
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append(f"**Base Reference:** {report.base_ref}\n")

        # Summary
        summary = report.summary
        lines.append("## 📊 Summary\n")
        lines.append(f"- **Total Endpoints:** {summary['total_endpoints']}")
        lines.append(f"- **🔴 High Risk:** {summary['high_risk']}")
        lines.append(f"- **🟡 Medium Risk:** {summary['medium_risk']}")
        lines.append(f"- **🟢 Low Risk:** {summary['low_risk']}")
        lines.append(f"- **Average Score:** {summary['average_score']}/100\n")

        # Risk Breakdown
        lines.append("## 🔥 Risk Breakdown\n")

        for result in report.risk_results:
            emoji = self.RISK_COLORS[result.risk_level]["emoji"]
            lines.append(f"### {emoji} {result.http_method} {result.endpoint_path}")
            lines.append(
                f"**Risk Score:** {result.risk_score}/100 ({result.risk_level.upper()})"
            )
            lines.append(f"**Affected Files:** {', '.join(result.affected_files[:5])}")

            if result.historical_failures > 0:
                lines.append(f"**Historical Failures:** {result.historical_failures}")

            lines.append("\n**Risk Factors:**")
            for factor, value in result.factors.items():
                lines.append(f"- {factor.replace('_', ' ').title()}: {value:.1f}")

            if result.recommendations:
                lines.append("\n**Recommendations:**")
                for rec in result.recommendations:
                    lines.append(f"- {rec}")

            lines.append("")

        # Write file
        output_file.write_text("\n".join(lines), encoding="utf-8")

        return output_file

    def create_report(
        self,
        risk_results: List[RiskResult],
        base_ref: str,
        summary: Dict,
        recommendations: List[str],
    ) -> HeatmapReport:
        """Create a complete heatmap report.

        Args:
            risk_results: List of risk results
            base_ref: Git reference used
            summary: Summary statistics
            recommendations: Global recommendations

        Returns:
            Complete heatmap report
        """
        return HeatmapReport(
            generated_at=datetime.now(),
            base_ref=base_ref,
            total_endpoints=len(risk_results),
            risk_results=risk_results,
            summary=summary,
            recommendations=recommendations,
            metadata={
                "generator_version": "1.0.0",
                "analysis_depth": "full",
            },
        )
