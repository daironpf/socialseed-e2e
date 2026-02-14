"""Semantic Analyzer Agent.

Main orchestrator for autonomous semantic regression and logic drift detection.
Coordinates intent extraction, state capture, drift detection, and report generation.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from models import SemanticDriftReport
from intent_baseline_extractor import IntentBaselineExtractor
from stateful_analyzer import StatefulAnalyzer
from logic_drift_detector import LogicDriftDetector
from report_generator import SemanticDriftReportGenerator


class SemanticAnalyzerAgent:
    """Autonomous agent for semantic regression and logic drift detection."""

    def __init__(
        self,
        project_root: Path,
        project_name: Optional[str] = None,
        base_url: Optional[str] = None,
        llm_client: Optional[Any] = None,
    ):
        self.project_root = Path(project_root)
        self.project_name = project_name or self.project_root.name
        self.base_url = base_url
        self.llm_client = llm_client

        # Initialize components
        self.intent_extractor = IntentBaselineExtractor(self.project_root)
        self.state_analyzer = StatefulAnalyzer(self.project_root, base_url)
        self.drift_detector = LogicDriftDetector(llm_client)
        self.report_generator = SemanticDriftReportGenerator(self.project_root)

    def analyze(
        self,
        baseline_commit: Optional[str] = None,
        target_commit: Optional[str] = None,
        api_endpoints: Optional[List[Dict[str, Any]]] = None,
        database_configs: Optional[List[Dict[str, Any]]] = None,
        capture_states: bool = True,
        output_path: Optional[Path] = None,
    ) -> SemanticDriftReport:
        """Run complete semantic drift analysis."""
        print(f"🔍 Starting Semantic Drift Analysis for {self.project_name}")
        print("=" * 60)

        # Step 1: Extract intent baselines
        print("\n📚 Step 1: Extracting Intent Baselines...")
        intent_baselines = self.intent_extractor.extract_all()
        print(f"   ✓ Extracted {len(intent_baselines)} intent baselines")

        # Step 2: Capture baseline state (before changes)
        before_state = None
        if capture_states:
            print("\n📸 Step 2: Capturing Baseline State...")
            before_state = self.state_analyzer.capture_baseline_state(
                commit_hash=baseline_commit,
                api_endpoints=api_endpoints,
                database_configs=database_configs,
            )
            print(f"   ✓ Captured {len(before_state.api_snapshots)} API snapshots")
            print(
                f"   ✓ Captured {len(before_state.database_snapshots)} database snapshots"
            )

        # Step 3: Capture current state (after changes)
        after_state = None
        if capture_states and before_state:
            print("\n📸 Step 3: Capturing Current State...")
            after_state = self.state_analyzer.capture_current_state(
                baseline_snapshot=before_state,
                commit_hash=target_commit,
            )
            print(f"   ✓ Captured {len(after_state.api_snapshots)} API snapshots")
            print(
                f"   ✓ Captured {len(after_state.database_snapshots)} database snapshots"
            )

        # Step 4: Detect logic drift
        print("\n🔎 Step 4: Detecting Logic Drift...")
        code_diff = self._get_code_diff(baseline_commit, target_commit)

        detected_drifts = []
        if before_state and after_state:
            detected_drifts = self.drift_detector.detect_drift(
                intent_baselines=intent_baselines,
                before_state=before_state,
                after_state=after_state,
                code_diff=code_diff,
            )
        print(f"   ✓ Detected {len(detected_drifts)} logic drift(s)")

        # Step 5: Generate report
        print("\n📊 Step 5: Generating Report...")
        report = SemanticDriftReport(
            report_id=f"sdr_{uuid.uuid4().hex[:12]}",
            project_name=self.project_name,
            baseline_commit=baseline_commit,
            target_commit=target_commit,
            intent_baselines=intent_baselines,
            before_state=before_state,
            after_state=after_state,
            detected_drifts=detected_drifts,
        )

        # Generate markdown report
        report_path = self.report_generator.generate_report(report, output_path)
        print(f"   ✓ Generated report: {report_path}")

        # Also generate JSON report
        json_path = report_path.with_suffix(".json")
        self.report_generator.generate_json_report(report, json_path)
        print(f"   ✓ Generated JSON: {json_path}")

        # Summary
        print("\n" + "=" * 60)
        print("📋 ANALYSIS COMPLETE")
        print("=" * 60)

        summary = report.generate_summary()
        print(f"\nTotal Intents Analyzed: {summary['total_intents_analyzed']}")
        print(f"Total Drifts Detected: {summary['total_drifts']}")

        if summary["has_critical_issues"]:
            print("\n🚨 CRITICAL ISSUES FOUND - Immediate action required!")
        elif summary["total_drifts"] > 0:
            print("\n⚠️  Drifts detected - Review recommended")
        else:
            print("\n✅ No semantic drift detected - All systems aligned")

        return report

    def analyze_pr(
        self,
        pr_number: int,
        api_endpoints: Optional[List[Dict[str, Any]]] = None,
        database_configs: Optional[List[Dict[str, Any]]] = None,
    ) -> SemanticDriftReport:
        """Analyze a specific Pull Request for semantic drift."""
        print(f"🔍 Analyzing PR #{pr_number} for Semantic Drift")

        # Get PR info
        pr_info = self._get_pr_info(pr_number)

        # Get commits
        base_commit = pr_info.get("base_commit")
        head_commit = pr_info.get("head_commit")

        # Run analysis
        return self.analyze(
            baseline_commit=base_commit,
            target_commit=head_commit,
            api_endpoints=api_endpoints,
            database_configs=database_configs,
        )

    def compare_commits(
        self,
        base_commit: str,
        head_commit: str,
        api_endpoints: Optional[List[Dict[str, Any]]] = None,
        database_configs: Optional[List[Dict[str, Any]]] = None,
    ) -> SemanticDriftReport:
        """Compare two commits for semantic drift."""
        return self.analyze(
            baseline_commit=base_commit,
            target_commit=head_commit,
            api_endpoints=api_endpoints,
            database_configs=database_configs,
        )

    def quick_check(
        self,
        intent_categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Quick semantic check without full state capture."""
        print("⚡ Running Quick Semantic Check...")

        # Extract intents
        intent_baselines = self.intent_extractor.extract_all()

        # Filter by category if specified
        if intent_categories:
            intent_baselines = [
                i for i in intent_baselines if i.category in intent_categories
            ]

        # Simple validation - check if intents are testable
        results = {
            "total_intents": len(intent_baselines),
            "by_category": {},
            "high_confidence_intents": [],
            "low_confidence_intents": [],
        }

        for intent in intent_baselines:
            # Count by category
            cat = intent.category
            results["by_category"][cat] = results["by_category"].get(cat, 0) + 1

            # Classify by confidence
            if intent.confidence >= 0.8:
                results["high_confidence_intents"].append(intent.intent_id)
            elif intent.confidence < 0.5:
                results["low_confidence_intents"].append(intent.intent_id)

        return results

    def _get_code_diff(
        self,
        baseline_commit: Optional[str],
        target_commit: Optional[str],
    ) -> Optional[str]:
        """Get code diff between two commits."""
        if not baseline_commit or not target_commit:
            return None

        try:
            result = subprocess.run(
                ["git", "diff", baseline_commit, target_commit],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Warning: Could not get code diff: {result.stderr}")
                return None
        except Exception as e:
            print(f"Warning: Error getting code diff: {e}")
            return None

    def _get_pr_info(self, pr_number: int) -> Dict[str, Any]:
        """Get PR information from GitHub or local git."""
        # This is a simplified implementation
        # In production, this would use GitHub API

        try:
            # Try to get PR info from git
            result = subprocess.run(
                ["git", "log", "--oneline", "-20"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Parse latest commits
                commits = result.stdout.strip().split("\n")
                if len(commits) >= 2:
                    head = commits[0].split()[0]
                    base = commits[-1].split()[0]
                    return {
                        "base_commit": base,
                        "head_commit": head,
                        "pr_number": pr_number,
                    }
        except Exception:
            pass

        return {
            "base_commit": None,
            "head_commit": None,
            "pr_number": pr_number,
        }

    def get_intent_summary(self) -> Dict[str, Any]:
        """Get summary of extracted intents."""
        intents = self.intent_extractor.extract_all()

        summary = {
            "total": len(intents),
            "by_category": {},
            "by_source_type": {},
            "high_confidence": 0,
            "low_confidence": 0,
        }

        for intent in intents:
            # By category
            cat = intent.category
            summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1

            # By source
            for source in intent.sources:
                source_type = source.source_type
                summary["by_source_type"][source_type] = (
                    summary["by_source_type"].get(source_type, 0) + 1
                )

            # Confidence
            if intent.confidence >= 0.8:
                summary["high_confidence"] += 1
            elif intent.confidence < 0.5:
                summary["low_confidence"] += 1

        return summary
