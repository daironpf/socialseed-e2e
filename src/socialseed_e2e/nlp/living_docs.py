"""
Living Documentation and BDD Translation System for socialseed-e2e.

This module provides:
- Continuous synchronization between BDD specifications and test code
- Semantic drift detection between product documentation and E2E implementation
- Alerting for undocumented business rules
- Integration with PlannerAgent and GeneratorAgent
"""

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocFormat(str, Enum):
    """Documentation format."""

    GHERKIN = "gherkin"
    MARKDOWN = "markdown"
    CONFLUENCE = "confluence"
    JIRA = "jira"


class BusinessRule(BaseModel):
    """A documented business rule."""

    rule_id: str
    title: str
    description: str

    source_format: DocFormat
    source_file: str

    gherkin_scenario: Optional[str] = None

    covered_by_tests: List[str] = Field(default_factory=list)

    last_verified: Optional[datetime] = None
    hash: str = ""


class TestCoverage(BaseModel):
    """Coverage of a business rule by tests."""

    test_file: str
    test_name: str

    covered_rules: List[str] = Field(default_factory=list)

    execution_status: str = "unknown"
    last_executed: Optional[datetime] = None


class SemanticDriftAlert(BaseModel):
    """Alert for semantic drift between documentation and implementation."""

    alert_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

    rule_id: str
    drift_type: str

    description: str
    severity: str = "medium"

    documentation_snippet: str = ""
    implementation_snippet: str = ""


class LivingDocConfig(BaseModel):
    """Configuration for living documentation system."""

    docs_directory: str = "docs"
    test_directory: str = "services"

    watch_for_changes: bool = True

    check_coverage: bool = True
    fail_on_missing_coverage: bool = False

    check_semantic_drift: bool = True


class BusinessRuleExtractor:
    """
    Extracts business rules from documentation sources.
    """

    def __init__(self):
        self.rules: Dict[str, BusinessRule] = {}

    def extract_from_gherkin(self, feature_file: str) -> List[BusinessRule]:
        """Extract rules from Gherkin feature files."""
        rules = []

        path = Path(feature_file)
        if not path.exists():
            return rules

        with open(path, "r") as f:
            content = f.read()

        lines = content.split("\n")
        current_scenario = ""
        current_rule = None

        for line in lines:
            if line.startswith("Feature:"):
                feature_name = line.replace("Feature:", "").strip()
                current_rule = BusinessRule(
                    rule_id=str(uuid.uuid4()),
                    title=feature_name,
                    description=feature_name,
                    source_format=DocFormat.GHERKIN,
                    source_file=feature_file,
                    hash=self._compute_hash(content),
                )
            elif line.startswith("Scenario:"):
                if current_rule:
                    current_rule.gherkin_scenario = line.strip()
                    rules.append(current_rule)
                    current_rule = None

        return rules

    def extract_from_markdown(self, md_file: str) -> List[BusinessRule]:
        """Extract rules from Markdown documentation."""
        rules = []

        path = Path(md_file)
        if not path.exists():
            return rules

        with open(path, "r") as f:
            content = f.read()

        lines = content.split("\n")
        current_rule = None

        for line in lines:
            if line.startswith("# "):
                if current_rule:
                    rules.append(current_rule)

                current_rule = BusinessRule(
                    rule_id=str(uuid.uuid4()),
                    title=line.replace("# ", "").strip(),
                    description="",
                    source_format=DocFormat.MARKDOWN,
                    source_file=md_file,
                    hash=self._compute_hash(content),
                )
            elif current_rule and line.strip():
                current_rule.description += line.strip() + " "

        if current_rule:
            rules.append(current_rule)

        return rules

    def _compute_hash(self, content: str) -> str:
        """Compute hash of content for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class SemanticDriftDetector:
    """
    Detects semantic drift between documentation and test implementation.
    """

    def __init__(self):
        self.alerts: List[SemanticDriftAlert] = []

    def detect_drift(
        self,
        documented_rule: BusinessRule,
        test_implementation: str,
    ) -> Optional[SemanticDriftAlert]:
        """Detect semantic drift between documentation and implementation."""
        if not documented_rule.gherkin_scenario:
            return None

        scenario_keywords = ["Given", "When", "Then", "And"]
        has_keywords = any(kw in test_implementation for kw in scenario_keywords)

        if documented_rule.gherkin_scenario and not has_keywords:
            alert = SemanticDriftAlert(
                alert_id=str(uuid.uuid4()),
                rule_id=documented_rule.rule_id,
                drift_type="missing_steps",
                description=f"Scenario '{documented_rule.gherkin_scenario}' not implemented",
                severity="high",
                documentation_snippet=documented_rule.gherkin_scenario,
                implementation_snippet="No matching test found",
            )
            self.alerts.append(alert)
            return alert

        return None

    def get_alerts(self) -> List[SemanticDriftAlert]:
        """Get all drift alerts."""
        return self.alerts

    def reset(self) -> None:
        """Reset alerts."""
        self.alerts.clear()


class CoverageTracker:
    """
    Tracks coverage of business rules by tests.
    """

    def __init__(self):
        self.test_coverage: Dict[str, TestCoverage] = {}

    def analyze_test_file(self, test_file: str) -> TestCoverage:
        """Analyze a test file for rule coverage."""
        path = Path(test_file)
        if not path.exists():
            return TestCoverage(test_file=test_file, test_name="unknown")

        with open(path, "r") as f:
            content = f.read()

        test_name = path.stem

        coverage = TestCoverage(
            test_file=test_file,
            test_name=test_name,
        )

        gherkin_keywords = ["given_", "when_", "then_"]
        for kw in gherkin_keywords:
            if kw in content.lower():
                coverage.covered_rules.append(kw)

        return coverage

    def check_uncovered_rules(
        self,
        rules: List[BusinessRule],
        tests: List[TestCoverage],
    ) -> List[BusinessRule]:
        """Check which rules are not covered by any test."""
        covered_rule_ids = set()
        for test in tests:
            covered_rule_ids.update(test.covered_rules)

        uncovered = [rule for rule in rules if rule.rule_id not in covered_rule_ids]

        return uncovered


class LivingDocumentationGenerator:
    """
    Generates and maintains living documentation.
    """

    def __init__(
        self,
        config: Optional[LivingDocConfig] = None,
    ):
        self.config = config or LivingDocConfig()
        self.extractor = BusinessRuleExtractor()
        self.drift_detector = SemanticDriftDetector()
        self.coverage_tracker = CoverageTracker()

    def scan_documentation(self, directory: str) -> List[BusinessRule]:
        """Scan documentation directory for business rules."""
        all_rules = []

        docs_path = Path(directory)
        if not docs_path.exists():
            return all_rules

        for file_path in docs_path.rglob("*.feature"):
            rules = self.extractor.extract_from_gherkin(str(file_path))
            all_rules.extend(rules)

        for file_path in docs_path.rglob("*.md"):
            rules = self.extractor.extract_from_markdown(str(file_path))
            all_rules.extend(rules)

        return all_rules

    def analyze_coverage(
        self,
        rules: List[BusinessRule],
        test_directory: str,
    ) -> Dict[str, Any]:
        """Analyze test coverage of business rules."""
        test_files = []
        test_path = Path(test_directory)

        if test_path.exists():
            test_files = list(test_path.rglob("test_*.py"))

        test_coverages = []
        for test_file in test_files:
            coverage = self.coverage_tracker.analyze_test_file(str(test_file))
            test_coverages.append(coverage)

        uncovered = self.coverage_tracker.check_uncovered_rules(rules, test_coverages)

        return {
            "total_rules": len(rules),
            "total_tests": len(test_coverages),
            "uncovered_rules": uncovered,
            "coverage_percentage": (
                (len(rules) - len(uncovered)) / len(rules) * 100 if rules else 100
            ),
        }

    def generate_report(self) -> str:
        """Generate living documentation status report."""
        alerts = self.drift_detector.get_alerts()

        report = "# Living Documentation Status Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += "## Semantic Drift Alerts\n\n"
        if alerts:
            for alert in alerts:
                report += f"### {alert.rule_id}\n"
                report += f"**Severity:** {alert.severity}\n"
                report += f"**Description:** {alert.description}\n\n"
        else:
            report += "No semantic drift detected.\n\n"

        return report


__all__ = [
    "BusinessRule",
    "BusinessRuleExtractor",
    "CoverageTracker",
    "DocFormat",
    "LivingDocConfig",
    "LivingDocumentationGenerator",
    "SemanticDriftAlert",
    "SemanticDriftDetector",
    "TestCoverage",
]
