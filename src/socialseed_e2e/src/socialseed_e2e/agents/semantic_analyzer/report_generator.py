"""Semantic Drift Report Generator.

Generates comprehensive SEMANTIC_DRIFT_REPORT.md files documenting
detected logic drift and semantic regressions.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from models import DriftSeverity, LogicDrift, SemanticDriftReport


class SemanticDriftReportGenerator:
    """Generates semantic drift analysis reports."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(".")

    def generate_report(
        self,
        report: SemanticDriftReport,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate SEMANTIC_DRIFT_REPORT.md file."""
        if output_path is None:
            output_path = self.output_dir / "SEMANTIC_DRIFT_REPORT.md"

        content = self._build_report_content(report)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def _build_report_content(self, report: SemanticDriftReport) -> str:
        """Build the markdown content for the report."""
        lines = []

        # Header
        lines.append("# Semantic Drift Analysis Report")
        lines.append("")
        lines.append(f"**Project:** {report.project_name}")
        lines.append(f"**Report ID:** {report.report_id}")
        lines.append(
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append("")

        # Commit Information
        if report.baseline_commit or report.target_commit:
            lines.append("## Commit Information")
            lines.append("")
            if report.baseline_commit:
                lines.append(f"- **Baseline Commit:** `{report.baseline_commit}`")
            if report.target_commit:
                lines.append(f"- **Target Commit:** `{report.target_commit}`")
            lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")

        summary = report.generate_summary()
        total_drifts = summary["total_drifts"]
        critical_count = summary["severity_distribution"]["critical"]
        high_count = summary["severity_distribution"]["high"]

        if total_drifts == 0:
            lines.append(
                "✅ **No semantic drift detected.** All system behaviors align with intended business logic."
            )
        else:
            lines.append(
                f"⚠️ **{total_drifts} semantic drift(s) detected** across {summary['total_intents_analyzed']} intent(s)."
            )
            lines.append("")

            if critical_count > 0:
                lines.append(
                    f"🚨 **{critical_count} CRITICAL** issue(s) require immediate attention."
                )
            if high_count > 0:
                lines.append(
                    f"⚠️ **{high_count} HIGH** severity issue(s) should be addressed before deployment."
                )

        lines.append("")

        # Severity Distribution
        lines.append("### Severity Distribution")
        lines.append("")
        lines.append("| Severity | Count | Status |")
        lines.append("|----------|-------|--------|")

        severity_emojis = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚡",
            "low": "ℹ️",
            "info": "💡",
        }

        for severity, count in summary["severity_distribution"].items():
            emoji = severity_emojis.get(severity, "")
            status = "Action Required" if severity in ["critical", "high"] else "Review"
            lines.append(f"| {emoji} {severity.upper()} | {count} | {status} |")

        lines.append("")

        # Drift Type Distribution
        lines.append("### Drift Type Distribution")
        lines.append("")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")

        for drift_type, count in summary["type_distribution"].items():
            if count > 0:
                lines.append(f"| {drift_type.replace('_', ' ').title()} | {count} |")

        lines.append("")

        # Intent Baselines
        lines.append("## Intent Baselines Analyzed")
        lines.append("")
        lines.append(f"**Total Intents:** {len(report.intent_baselines)}")
        lines.append("")

        if report.intent_baselines:
            lines.append("| Intent ID | Category | Description | Confidence |")
            lines.append("|-----------|----------|-------------|------------|")

            for intent in report.intent_baselines[:20]:  # Show first 20
                desc = (
                    intent.description[:50] + "..."
                    if len(intent.description) > 50
                    else intent.description
                )
                lines.append(
                    f"| {intent.intent_id} | {intent.category} | {desc} | {intent.confidence:.0%} |"
                )

            if len(report.intent_baselines) > 20:
                lines.append(
                    f"| ... | ... | *{len(report.intent_baselines) - 20} more* | ... |"
                )

        lines.append("")

        # Detected Drifts (Detailed)
        if report.detected_drifts:
            lines.append("## Detected Semantic Drifts")
            lines.append("")

            # Group by severity
            for severity in [
                DriftSeverity.CRITICAL,
                DriftSeverity.HIGH,
                DriftSeverity.MEDIUM,
                DriftSeverity.LOW,
            ]:
                drifts = report.get_drifts_by_severity(severity)
                if drifts:
                    lines.append(f"### {severity.value.upper()} Severity")
                    lines.append("")

                    for drift in drifts:
                        lines.extend(self._format_drift_details(drift))
                        lines.append("")

        # State Snapshots
        lines.append("## State Snapshots")
        lines.append("")

        if report.before_state:
            lines.append("### Baseline State (Before)")
            lines.append(f"- **Snapshot ID:** {report.before_state.snapshot_id}")
            lines.append(f"- **Commit:** {report.before_state.commit_hash or 'N/A'}")
            lines.append(
                f"- **Timestamp:** {report.before_state.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            lines.append(
                f"- **API Endpoints:** {len(report.before_state.api_snapshots)}"
            )
            lines.append(
                f"- **Databases:** {len(report.before_state.database_snapshots)}"
            )
            lines.append("")

        if report.after_state:
            lines.append("### Current State (After)")
            lines.append(f"- **Snapshot ID:** {report.after_state.snapshot_id}")
            lines.append(f"- **Commit:** {report.after_state.commit_hash or 'N/A'}")
            lines.append(
                f"- **Timestamp:** {report.after_state.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            lines.append(
                f"- **API Endpoints:** {len(report.after_state.api_snapshots)}"
            )
            lines.append(
                f"- **Databases:** {len(report.after_state.database_snapshots)}"
            )
            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")

        if report.has_critical_drifts():
            lines.append("### 🚨 Critical Actions Required")
            lines.append("")
            critical_drifts = report.get_drifts_by_severity(DriftSeverity.CRITICAL)
            for drift in critical_drifts:
                lines.append(f"1. **{drift.intent.description}**")
                lines.append(f"   - {drift.recommendation}")
                lines.append("")

        if report.get_drifts_by_severity(DriftSeverity.HIGH):
            lines.append("### ⚠️ High Priority Items")
            lines.append("")
            high_drifts = report.get_drifts_by_severity(DriftSeverity.HIGH)
            for drift in high_drifts:
                lines.append(f"1. **{drift.intent.description}**")
                lines.append(f"   - {drift.recommendation}")
                lines.append("")

        if not report.detected_drifts:
            lines.append(
                "✅ No actions required. System behavior aligns with all documented intents."
            )
            lines.append("")

        # Methodology
        lines.append("## Analysis Methodology")
        lines.append("")
        lines.append("This semantic drift analysis was performed by:")
        lines.append("")
        lines.append(
            "1. **Intent Extraction:** Crawling documentation, GitHub issues, code comments, and test cases to build a semantic model of expected behavior"
        )
        lines.append(
            "2. **State Capture:** Taking snapshots of API responses and database states before and after code changes"
        )
        lines.append(
            "3. **Drift Detection:** Using LLM-based reasoning to compare actual vs. intended behavior"
        )
        lines.append(
            "4. **Impact Assessment:** Classifying drift by type (behavioral, relationship, state transition, etc.) and severity"
        )
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by SocialSeed E2E Semantic Regression Agent*")
        lines.append(f"*Report ID: {report.report_id}*")

        return "\n".join(lines)

    def _format_drift_details(self, drift: LogicDrift) -> List[str]:
        """Format a single drift's details."""
        lines = []

        # Header with ID and type
        emoji = "🚨" if drift.severity == DriftSeverity.CRITICAL else "⚠️"
        lines.append(
            f"#### {emoji} {drift.drift_id} ({drift.drift_type.name.replace('_', ' ').title()})"
        )
        lines.append("")

        # Description
        lines.append(f"**Description:** {drift.description}")
        lines.append("")

        # Related Intent
        lines.append(f"**Related Intent:** {drift.intent.intent_id}")
        lines.append(f"- Description: {drift.intent.description}")
        lines.append(f"- Expected Behavior: {drift.intent.expected_behavior}")
        lines.append("")

        # Reasoning
        lines.append(f"**Reasoning:** {drift.reasoning}")
        lines.append("")

        # Affected Components
        if drift.affected_endpoints:
            lines.append(
                f"**Affected Endpoints:** {', '.join(drift.affected_endpoints)}"
            )
        if drift.affected_entities:
            lines.append(f"**Affected Entities:** {', '.join(drift.affected_entities)}")
        lines.append("")

        # Confidence
        lines.append(f"**Confidence:** {drift.confidence:.0%}")
        lines.append("")

        # Recommendation
        lines.append(f"**Recommendation:** {drift.recommendation}")
        lines.append("")

        # Evidence (collapsible)
        if drift.evidence:
            lines.append("<details>")
            lines.append("<summary>Evidence</summary>")
            lines.append("")
            lines.append("```json")
            import json

            lines.append(json.dumps(drift.evidence, indent=2))
            lines.append("```")
            lines.append("")
            lines.append("</details>")

        return lines

    def generate_json_report(
        self, report: SemanticDriftReport, output_path: Path
    ) -> None:
        """Generate JSON version of the report."""
        import json

        data = {
            "report_id": report.report_id,
            "project_name": report.project_name,
            "baseline_commit": report.baseline_commit,
            "target_commit": report.target_commit,
            "generated_at": report.generated_at.isoformat(),
            "summary": report.generate_summary(),
            "intents": [
                {
                    "intent_id": i.intent_id,
                    "description": i.description,
                    "category": i.category,
                    "expected_behavior": i.expected_behavior,
                    "success_criteria": i.success_criteria,
                    "confidence": i.confidence,
                }
                for i in report.intent_baselines
            ],
            "drifts": [d.to_dict() for d in report.detected_drifts],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
