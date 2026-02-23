"""Semantic Drift Report Generator.

Generates comprehensive SEMANTIC_DRIFT_REPORT.md and JSON reports
comparing intended vs actual system behavior.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.agents.semantic_analyzer.models import (
    DriftSeverity,
    DriftType,
    LogicDrift,
    SemanticDriftReport,
    StateSnapshot,
)


class SemanticDriftReportGenerator:
    """Generates semantic drift analysis reports."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / ".e2e" / "semantic_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self, report: SemanticDriftReport, output_path: Optional[Path] = None
    ) -> Path:
        """Generate markdown report (SEMANTIC_DRIFT_REPORT.md)."""
        if output_path is None:
            output_path = self.reports_dir / f"SEMANTIC_DRIFT_REPORT_{report.report_id}.md"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        markdown_content = self._generate_markdown(report)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return output_path

    def generate_json_report(
        self, report: SemanticDriftReport, output_path: Optional[Path] = None
    ) -> Path:
        """Generate JSON report."""
        if output_path is None:
            output_path = self.reports_dir / f"semantic_drift_{report.report_id}.json"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        json_content = self._generate_json(report)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2, default=str)

        return output_path

    def _generate_markdown(self, report: SemanticDriftReport) -> str:
        """Generate comprehensive markdown report."""
        lines = []

        # Header
        lines.extend(self._generate_header(report))

        # Executive Summary
        lines.extend(self._generate_executive_summary(report))

        # Intent Baselines Section
        lines.extend(self._generate_intent_baselines_section(report))

        # State Snapshots Section
        lines.extend(self._generate_state_snapshots_section(report))

        # Detected Drifts Section
        lines.extend(self._generate_drifts_section(report))

        # Detailed Analysis
        lines.extend(self._generate_detailed_analysis(report))

        # Recommendations
        lines.extend(self._generate_recommendations(report))

        # Appendix
        lines.extend(self._generate_appendix(report))

        return "\n".join(lines)

    def _generate_header(self, report: SemanticDriftReport) -> List[str]:
        """Generate report header."""
        return [
            "# Semantic Drift Analysis Report",
            "",
            f"**Project:** {report.project_name}",
            f"**Report ID:** {report.report_id}",
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]

    def _generate_executive_summary(self, report: SemanticDriftReport) -> List[str]:
        """Generate executive summary section."""
        summary = report.generate_summary()

        lines = [
            "## Executive Summary",
            "",
            "This report presents the results of a semantic regression analysis comparing",
            "intended system behavior (derived from documentation and historical context)",
            "against actual system behavior observed through API and database state analysis.",
            "",
        ]

        # Commit information
        if report.baseline_commit or report.target_commit:
            lines.extend(
                [
                    "### Analysis Context",
                    "",
                ]
            )
            if report.baseline_commit:
                lines.append(f"- **Baseline Commit:** `{report.baseline_commit}`")
            if report.target_commit:
                lines.append(f"- **Target Commit:** `{report.target_commit}`")
            lines.append("")

        # Key Metrics
        lines.extend(
            [
                "### Key Metrics",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Total Intents Analyzed | {summary['total_intents_analyzed']} |",
                f"| Total Drifts Detected | {summary['total_drifts']} |",
                f"| Critical Issues | {summary['severity_distribution'].get('critical', 0)} |",
                f"| High Severity | {summary['severity_distribution'].get('high', 0)} |",
                "",
            ]
        )

        # Status indicator
        if summary["has_critical_issues"]:
            lines.extend(
                [
                    "### Status: 🚨 CRITICAL ISSUES FOUND",
                    "",
                    "> ⚠️ **IMMEDIATE ACTION REQUIRED**  ",
                    "> Critical semantic drifts have been detected that violate core business ",
                    "> functionality. These issues should be addressed before deployment.",
                    "",
                ]
            )
        elif summary["total_drifts"] > 0:
            lines.extend(
                [
                    "### Status: ⚠️ DRIFTS DETECTED",
                    "",
                    "> 🔍 **Review Recommended**  ",
                    "> Semantic drifts have been detected that may indicate deviations from ",
                    "> intended business logic. Please review the detailed analysis below.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "### Status: ✅ NO DRIFT DETECTED",
                    "",
                    "> ✓ **All Systems Aligned**  ",
                    "> No semantic drift detected. System behavior aligns with intended business logic.",
                    "",
                ]
            )

        lines.append("---")
        lines.append("")

        return lines

    def _generate_intent_baselines_section(self, report: SemanticDriftReport) -> List[str]:
        """Generate intent baselines section."""
        lines = [
            "## Intent Baselines",
            "",
            "The following intent baselines were extracted from documentation, GitHub issues,",
            "code comments, and test cases to establish the expected system behavior.",
            "",
        ]

        if not report.intent_baselines:
            lines.extend(
                [
                    "> ⚠️ No intent baselines were extracted. Please ensure documentation exists",
                    "> in the `docs/` folder or GitHub issues are available.",
                    "",
                ]
            )
            return lines

        # Summary by category
        category_counts: Dict[str, int] = {}
        for intent in report.intent_baselines:
            category_counts[intent.category] = category_counts.get(intent.category, 0) + 1

        lines.extend(
            [
                "### Baselines by Category",
                "",
                "| Category | Count |",
                "|----------|-------|",
            ]
        )

        for category, count in sorted(category_counts.items()):
            lines.append(f"| {category} | {count} |")

        lines.append("")

        # Detailed baselines
        lines.extend(
            [
                "### Detailed Baselines",
                "",
            ]
        )

        for i, intent in enumerate(report.intent_baselines[:20], 1):  # Limit to first 20
            lines.extend(
                [
                    f"#### {i}. {intent.description}",
                    "",
                    f"- **ID:** `{intent.intent_id}`",
                    f"- **Category:** {intent.category}",
                    f"- **Confidence:** {intent.confidence:.0%}",
                    "",
                    "**Expected Behavior:**",
                    f"> {intent.expected_behavior}",
                    "",
                ]
            )

            if intent.success_criteria:
                lines.extend(
                    [
                        "**Success Criteria:**",
                        "",
                    ]
                )
                for criterion in intent.success_criteria:
                    lines.append(f"- {criterion}")
                lines.append("")

            if intent.related_entities:
                lines.append(f"**Related Entities:** {', '.join(intent.related_entities)}")
                lines.append("")

        if len(report.intent_baselines) > 20:
            lines.append(f"*... and {len(report.intent_baselines) - 20} more baselines*")
            lines.append("")

        lines.append("---")
        lines.append("")

        return lines

    def _generate_state_snapshots_section(self, report: SemanticDriftReport) -> List[str]:
        """Generate state snapshots section."""
        lines = [
            "## State Snapshots",
            "",
            "Comparative analysis of system states before and after code changes.",
            "",
        ]

        # Baseline State
        if report.before_state:
            lines.extend(
                self._generate_snapshot_subsection("Baseline State (Before)", report.before_state)
            )

        # Current State
        if report.after_state:
            lines.extend(
                self._generate_snapshot_subsection("Current State (After)", report.after_state)
            )

        if not report.before_state and not report.after_state:
            lines.extend(
                [
                    "> ℹ️ No state snapshots were captured. State analysis was skipped.",
                    "",
                ]
            )

        lines.append("---")
        lines.append("")

        return lines

    def _generate_snapshot_subsection(self, title: str, snapshot: StateSnapshot) -> List[str]:
        """Generate subsection for a single snapshot."""
        lines = [
            f"### {title}",
            "",
        ]

        if snapshot.commit_hash:
            lines.append(f"- **Commit:** `{snapshot.commit_hash}`")
        if snapshot.branch:
            lines.append(f"- **Branch:** `{snapshot.branch}`")
        lines.append(f"- **Snapshot ID:** `{snapshot.snapshot_id}`")
        lines.append(f"- **Timestamp:** {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # API Snapshots
        if snapshot.api_snapshots:
            lines.extend(
                [
                    "#### API Snapshots",
                    "",
                    "| Endpoint | Method | Status | Duration (ms) |",
                    "|----------|--------|--------|---------------|",
                ]
            )

            for api in snapshot.api_snapshots:
                lines.append(
                    f"| {api.endpoint} | {api.method} | {api.response_status} | "
                    f"{api.duration_ms:.2f} |"
                )

            lines.append("")

        # Database Snapshots
        if snapshot.database_snapshots:
            lines.extend(
                [
                    "#### Database Snapshots",
                    "",
                ]
            )

            for db in snapshot.database_snapshots:
                lines.append(f"- **{db.database_type}**: {len(db.entities)} entity types")
                if db.relationships:
                    lines.append(f"  - {len(db.relationships)} relationships")

            lines.append("")

        return lines

    def _generate_drifts_section(self, report: SemanticDriftReport) -> List[str]:
        """Generate detected drifts section."""
        lines = [
            "## Detected Semantic Drifts",
            "",
        ]

        if not report.detected_drifts:
            lines.extend(
                [
                    "✅ **No semantic drifts detected.**",
                    "",
                    "The system behavior aligns with all extracted intent baselines.",
                    "",
                ]
            )
            return lines

        # Severity breakdown
        severity_counts: Dict[str, int] = {}
        for drift in report.detected_drifts:
            severity = drift.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        lines.extend(
            [
                "### Severity Distribution",
                "",
                "| Severity | Count |",
                "|----------|-------|",
            ]
        )

        for severity in ["critical", "high", "medium", "low", "info"]:
            count = severity_counts.get(severity, 0)
            emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "🔍",
                "low": "ℹ️",
                "info": "💡",
            }
            lines.append(f"| {emoji.get(severity, '')} {severity.upper()} | {count} |")

        lines.append("")

        # Type breakdown
        type_counts: Dict[str, int] = {}
        for drift in report.detected_drifts:
            type_name = drift.drift_type.name
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        lines.extend(
            [
                "### Drift Type Distribution",
                "",
                "| Type | Count |",
                "|------|-------|",
            ]
        )

        for drift_type, count in sorted(type_counts.items()):
            lines.append(f"| {drift_type} | {count} |")

        lines.append("")

        # Detailed drifts
        lines.extend(
            [
                "### Detailed Drift Analysis",
                "",
            ]
        )

        # Sort by severity (critical first)
        severity_order = {
            DriftSeverity.CRITICAL: 0,
            DriftSeverity.HIGH: 1,
            DriftSeverity.MEDIUM: 2,
            DriftSeverity.LOW: 3,
            DriftSeverity.INFO: 4,
        }
        sorted_drifts = sorted(
            report.detected_drifts, key=lambda d: severity_order.get(d.severity, 5)
        )

        for i, drift in enumerate(sorted_drifts, 1):
            lines.extend(self._generate_drift_detail(i, drift))

        lines.append("---")
        lines.append("")

        return lines

    def _generate_drift_detail(self, index: int, drift: LogicDrift) -> List[str]:
        """Generate detailed section for a single drift."""
        severity_emoji = {
            DriftSeverity.CRITICAL: "🚨",
            DriftSeverity.HIGH: "⚠️",
            DriftSeverity.MEDIUM: "🔍",
            DriftSeverity.LOW: "ℹ️",
            DriftSeverity.INFO: "💡",
        }

        lines = [
            f"#### {index}. {severity_emoji.get(drift.severity, '')} "
            f"{drift.severity.value.upper()}: {drift.description}",
            "",
            f"- **Drift ID:** `{drift.drift_id}`",
            f"- **Type:** {drift.drift_type.name}",
            f"- **Severity:** {drift.severity.value.upper()}",
            f"- **Confidence:** {drift.confidence:.0%}",
            "",
        ]

        # Intent information
        if drift.intent:
            lines.extend(
                [
                    "**Related Intent:**",
                    f"- ID: `{drift.intent.intent_id}`",
                    f"- Description: {drift.intent.description}",
                    "",
                ]
            )

        # Reasoning
        if drift.reasoning:
            lines.extend(
                [
                    "**Reasoning:**",
                    f"> {drift.reasoning}",
                    "",
                ]
            )

        # Affected endpoints/entities
        if drift.affected_endpoints:
            lines.append(f"**Affected Endpoints:** {', '.join(drift.affected_endpoints)}")
        if drift.affected_entities:
            lines.append(f"**Affected Entities:** {', '.join(drift.affected_entities)}")
        if drift.affected_endpoints or drift.affected_entities:
            lines.append("")

        # Evidence
        if drift.evidence:
            lines.extend(
                [
                    "**Evidence:**",
                    "",
                    "```json",
                ]
            )
            for evidence_item in drift.evidence:
                lines.append(json.dumps(evidence_item, indent=2, default=str))
            lines.extend(
                [
                    "```",
                    "",
                ]
            )

        # Recommendation
        if drift.recommendation:
            lines.extend(
                [
                    "**Recommendation:**",
                    f"> 💡 {drift.recommendation}",
                    "",
                ]
            )

        lines.append("---")
        lines.append("")

        return lines

    def _generate_detailed_analysis(self, report: SemanticDriftReport) -> List[str]:
        """Generate detailed analysis section."""
        lines = [
            "## Detailed Analysis",
            "",
            "This section provides in-depth analysis of the semantic drift patterns",
            "and their potential impact on system behavior.",
            "",
        ]

        # Behavioral Analysis
        lines.extend(
            [
                "### Behavioral Analysis",
                "",
            ]
        )

        behavioral_drifts = report.get_drifts_by_type(DriftType.BEHAVIORAL)
        if behavioral_drifts:
            lines.extend(
                [
                    f"**{len(behavioral_drifts)} behavioral drift(s) detected.**",
                    "",
                    "Behavioral drifts indicate changes in how the system responds to requests,",
                    "which may affect user experience or API contract stability.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "✅ No behavioral drifts detected.",
                    "",
                ]
            )

        # Relationship Analysis
        lines.extend(
            [
                "### Relationship Analysis",
                "",
            ]
        )

        relationship_drifts = report.get_drifts_by_type(DriftType.RELATIONSHIP)
        if relationship_drifts:
            lines.extend(
                [
                    f"**{len(relationship_drifts)} relationship drift(s) detected.**",
                    "",
                    "Relationship drifts indicate changes in how entities relate to each other,",
                    "particularly critical in graph databases or relational models.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "✅ No relationship drifts detected.",
                    "",
                ]
            )

        # Business Rule Analysis
        lines.extend(
            [
                "### Business Rule Analysis",
                "",
            ]
        )

        business_drifts = report.get_drifts_by_type(DriftType.BUSINESS_RULE)
        if business_drifts:
            lines.extend(
                [
                    f"**{len(business_drifts)} business rule drift(s) detected.**",
                    "",
                    "Business rule drifts represent violations of core business logic",
                    "and should be addressed with highest priority.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "✅ No business rule drifts detected.",
                    "",
                ]
            )

        lines.append("---")
        lines.append("")

        return lines

    def _generate_recommendations(self, report: SemanticDriftReport) -> List[str]:
        """Generate recommendations section."""
        lines = [
            "## Recommendations",
            "",
        ]

        critical_drifts = report.get_drifts_by_severity(DriftSeverity.CRITICAL)
        high_drifts = report.get_drifts_by_severity(DriftSeverity.HIGH)

        if critical_drifts:
            lines.extend(
                [
                    "### 🚨 Critical Priority",
                    "",
                    "The following critical issues require immediate attention:",
                    "",
                ]
            )
            for drift in critical_drifts:
                lines.append(f"- **{drift.drift_id}**: {drift.description}")
            lines.append("")

        if high_drifts:
            lines.extend(
                [
                    "### ⚠️ High Priority",
                    "",
                    "The following high-priority issues should be addressed before deployment:",
                    "",
                ]
            )
            for drift in high_drifts:
                lines.append(f"- **{drift.drift_id}**: {drift.description}")
            lines.append("")

        # General recommendations
        lines.extend(
            [
                "### General Recommendations",
                "",
            ]
        )

        if not report.detected_drifts:
            lines.extend(
                [
                    "- ✅ No action required. System behavior is aligned with intent.",
                    "- Consider adding more intent baselines from documentation.",
                    "- Continue monitoring for future changes.",
                ]
            )
        elif len(report.detected_drifts) > 10:
            lines.extend(
                [
                    "- 🔍 **High drift count detected.** Consider reviewing your testing strategy.",
                    "- Ensure all code changes are accompanied by updated documentation.",
                    "- Review intent baselines to ensure they accurately reflect requirements.",
                ]
            )
        else:
            lines.extend(
                [
                    "- Review each detected drift to determine if it's intentional or a bug.",
                    "- Update documentation to reflect any intentional behavioral changes.",
                    "- Consider adding automated tests for drift-prone areas.",
                ]
            )

        lines.extend(
            [
                "",
                "### Next Steps",
                "",
            ]
        )

        if critical_drifts:
            lines.append("1. **URGENT**: Fix all critical drift issues before deployment.")
            lines.append("2. Re-run semantic analysis after fixes.")
            lines.append("3. Update intent baselines if changes were intentional.")
        elif report.detected_drifts:
            lines.append("1. Review each drift in the detailed analysis section.")
            lines.append("2. Determine which drifts represent actual bugs vs. intentional changes.")
            lines.append("3. Update documentation and baselines as needed.")
        else:
            lines.append("1. Continue monitoring with regular semantic analysis runs.")
            lines.append("2. Expand intent baselines as new features are added.")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _generate_appendix(self, report: SemanticDriftReport) -> List[str]:
        """Generate appendix section."""
        return [
            "## Appendix",
            "",
            "### Report Metadata",
            "",
            f"- **Report ID:** {report.report_id}",
            f"- **Project:** {report.project_name}",
            f"- **Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Total Intents:** {len(report.intent_baselines)}",
            f"- **Total Drifts:** {len(report.detected_drifts)}",
            "",
            "### Severity Levels",
            "",
            "| Level | Description |",
            "|-------|-------------|",
            "| 🚨 CRITICAL | Breaks core business functionality |",
            "| ⚠️ HIGH | Significant deviation from intent |",
            "| 🔍 MEDIUM | Moderate deviation, may be intentional |",
            "| ℹ️ LOW | Minor deviation or cosmetic change |",
            "| 💡 INFO | Informational, no action required |",
            "",
            "### Drift Types",
            "",
            "| Type | Description |",
            "|------|-------------|",
            "| BEHAVIORAL | Behavior differs from intent |",
            "| RELATIONSHIP | Entity relationships changed |",
            "| STATE_TRANSITION | State machine transitions incorrect |",
            "| VALIDATION_LOGIC | Validation rules changed |",
            "| BUSINESS_RULE | Core business logic changed |",
            "| DATA_INTEGRITY | Data consistency issues |",
            "| SIDE_EFFECT | Unexpected side effects |",
            "| MISSING_FUNCTIONALITY | Expected behavior not present |",
            "",
            "---",
            "",
            "*Generated by SocialSeed E2E Semantic Analyzer*",
        ]

    def _generate_json(self, report: SemanticDriftReport) -> Dict[str, Any]:
        """Generate JSON report structure."""
        return {
            "report_id": report.report_id,
            "project_name": report.project_name,
            "baseline_commit": report.baseline_commit,
            "target_commit": report.target_commit,
            "generated_at": report.generated_at.isoformat(),
            "summary": report.generate_summary(),
            "intent_baselines": [
                {
                    "intent_id": b.intent_id,
                    "description": b.description,
                    "category": b.category,
                    "expected_behavior": b.expected_behavior,
                    "success_criteria": b.success_criteria,
                    "related_entities": b.related_entities,
                    "confidence": b.confidence,
                    "sources": [
                        {
                            "source_type": s.source_type,
                            "source_path": s.source_path,
                            "line_number": s.line_number,
                            "title": s.title,
                        }
                        for s in b.sources
                    ],
                }
                for b in report.intent_baselines
            ],
            "detected_drifts": [d.to_dict() for d in report.detected_drifts],
            "metadata": {
                "version": "1.0.0",
                "analyzer": "socialseed-e2e-semantic-analyzer",
            },
        }

    def get_latest_report(self) -> Optional[Path]:
        """Get the path to the most recent report."""
        if not self.reports_dir.exists():
            return None

        reports = list(self.reports_dir.glob("SEMANTIC_DRIFT_REPORT_*.md"))
        if not reports:
            return None

        return max(reports, key=lambda p: p.stat().st_mtime)

    def list_reports(self) -> List[Path]:
        """List all generated reports."""
        if not self.reports_dir.exists():
            return []

        return sorted(
            self.reports_dir.glob("SEMANTIC_DRIFT_REPORT_*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
