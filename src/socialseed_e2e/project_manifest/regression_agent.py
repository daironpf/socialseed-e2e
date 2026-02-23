"""AI Regression Agents for Differential Testing.

This module provides intelligent regression testing by analyzing git diffs,
determining impact on existing tests, and executing only affected tests.

Issue #84: Implement AI Regression Agents for Differential Testing
"""

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CodeChange:
    """Represents a single code change from git diff."""

    file_path: Path
    change_type: str  # 'added', 'modified', 'deleted'
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    lines_added: int = 0
    lines_deleted: int = 0
    diff_content: str = ""
    affected_endpoints: List[str] = field(default_factory=list)


@dataclass
class ImpactAnalysis:
    """Analysis of impact from code changes."""

    changed_files: List[CodeChange]
    affected_services: List[str] = field(default_factory=list)
    affected_endpoints: List[str] = field(default_factory=list)
    affected_tests: List[str] = field(default_factory=list)
    new_tests_needed: List[str] = field(default_factory=list)
    risk_level: str = "low"  # 'low', 'medium', 'high', 'critical'


@dataclass
class RegressionTestResult:
    """Result of a regression test execution."""

    test_name: str
    service_name: str
    status: str  # 'passed', 'failed', 'skipped'
    execution_time_ms: float
    related_changes: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class GitDiffAnalyzer:
    """Analyzes git diffs to identify code changes."""

    # Patterns to identify different types of code elements
    FUNCTION_PATTERNS = {
        "python": r"def\s+(\w+)\s*\(",
        "java": r"(public|private|protected)?\s*(static)?\s*\w+\s+(\w+)\s*\(",
        "javascript": r"function\s+(\w+)\s*\(|(\w+)\s*[=:]\s*function\s*\(",
        "typescript": r"function\s+(\w+)\s*\(|(\w+)\s*[=:]\s*function\s*\(",
    }

    CLASS_PATTERNS = {
        "python": r"class\s+(\w+)",
        "java": r"class\s+(\w+)",
        "javascript": r"class\s+(\w+)",
        "typescript": r"class\s+(\w+)",
    }

    ENDPOINT_PATTERNS = {
        "python": r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)',
        "java": r'@(?:Get|Post|Put|Delete|Patch)Mapping\s*\(["\']?([^"\']+)["\']?',
        "javascript": r'\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)',
    }

    def __init__(self, project_root: Path):
        """Initialize the git diff analyzer.

        Args:
            project_root: Root directory of the git repository
        """
        self.project_root = Path(project_root).resolve()

    def get_changed_files(self, base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> List[Path]:
        """Get list of changed files between two git refs.

        Args:
            base_ref: Base git reference (e.g., "HEAD~1", "main")
            target_ref: Target git reference (e.g., "HEAD", "feature-branch")

        Returns:
            List of changed file paths
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", base_ref, target_ref],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            changed_files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    file_path = self.project_root / line
                    changed_files.append(file_path)

            return changed_files

        except subprocess.CalledProcessError as e:
            print(f"Error running git diff: {e}")
            return []

    def get_detailed_diff(
        self, file_path: Path, base_ref: str = "HEAD~1", target_ref: str = "HEAD"
    ) -> str:
        """Get detailed diff for a specific file.

        Args:
            file_path: Path to the file
            base_ref: Base git reference
            target_ref: Target git reference

        Returns:
            Diff content as string
        """
        try:
            relative_path = file_path.relative_to(self.project_root)
            result = subprocess.run(
                ["git", "diff", base_ref, target_ref, "--", str(relative_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout

        except subprocess.CalledProcessError as e:
            print(f"Error getting diff for {file_path}: {e}")
            return ""

    def analyze_changes(
        self, base_ref: str = "HEAD~1", target_ref: str = "HEAD"
    ) -> List[CodeChange]:
        """Analyze all changes between two git refs.

        Args:
            base_ref: Base git reference
            target_ref: Target git reference

        Returns:
            List of code changes
        """
        changed_files = self.get_changed_files(base_ref, target_ref)
        changes = []

        for file_path in changed_files:
            diff_content = self.get_detailed_diff(file_path, base_ref, target_ref)
            if diff_content:
                change = self._parse_diff(file_path, diff_content)
                changes.append(change)

        return changes

    def _parse_diff(self, file_path: Path, diff_content: str) -> CodeChange:
        """Parse diff content to extract change details.

        Args:
            file_path: Path to the changed file
            diff_content: Raw diff content

        Returns:
            CodeChange object with parsed information
        """
        # Determine file type
        file_extension = file_path.suffix.lower()
        language = self._get_language(file_extension)

        # Count lines added/deleted
        lines_added = len(re.findall(r"^\+[^+]", diff_content, re.MULTILINE))
        lines_deleted = len(re.findall(r"^-[^-]", diff_content, re.MULTILINE))

        # Determine change type
        if lines_added > 0 and lines_deleted == 0:
            change_type = "added"
        elif lines_added == 0 and lines_deleted > 0:
            change_type = "deleted"
        else:
            change_type = "modified"

        # Extract function names
        function_name = self._extract_function_name(diff_content, language)

        # Extract class names
        class_name = self._extract_class_name(diff_content, language)

        # Extract affected endpoints
        affected_endpoints = self._extract_endpoints(diff_content, language)

        return CodeChange(
            file_path=file_path,
            change_type=change_type,
            function_name=function_name,
            class_name=class_name,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            diff_content=diff_content,
            affected_endpoints=affected_endpoints,
        )

    def _get_language(self, file_extension: str) -> str:
        """Determine programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".java": "java",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
        }
        return extension_map.get(file_extension, "unknown")

    def _extract_function_name(self, diff_content: str, language: str) -> Optional[str]:
        """Extract function name from diff content."""
        pattern = self.FUNCTION_PATTERNS.get(language)
        if not pattern:
            return None

        match = re.search(pattern, diff_content, re.MULTILINE)
        if match:
            # Return the first non-None group
            for group in match.groups():
                if group:
                    return group
        return None

    def _extract_class_name(self, diff_content: str, language: str) -> Optional[str]:
        """Extract class name from diff content."""
        pattern = self.CLASS_PATTERNS.get(language)
        if not pattern:
            return None

        match = re.search(pattern, diff_content, re.MULTILINE)
        if match:
            return match.group(1)
        return None

    def _extract_endpoints(self, diff_content: str, language: str) -> List[str]:
        """Extract API endpoints from diff content."""
        pattern = self.ENDPOINT_PATTERNS.get(language)
        if not pattern:
            return []

        endpoints = []
        for match in re.finditer(pattern, diff_content, re.MULTILINE):
            # Extract endpoint path from match groups
            for group in match.groups():
                if group and group.startswith("/"):
                    endpoints.append(group)

        return endpoints


class ImpactAnalyzer:
    """Analyzes the impact of code changes on tests."""

    def __init__(self, project_root: Path, manifest: Any):
        """Initialize the impact analyzer.

        Args:
            project_root: Root directory of the project
            manifest: Project manifest with service information
        """
        self.project_root = Path(project_root).resolve()
        self.manifest = manifest

    def analyze_impact(self, changes: List[CodeChange]) -> ImpactAnalysis:
        """Analyze the impact of code changes.

        Args:
            changes: List of code changes

        Returns:
            ImpactAnalysis with detailed impact information
        """
        affected_services = []
        affected_endpoints = []
        affected_tests = []
        new_tests_needed = []

        for change in changes:
            # Determine affected services
            services = self._identify_affected_services(change)
            affected_services.extend(services)

            # Determine affected endpoints
            endpoints = self._identify_affected_endpoints(change)
            affected_endpoints.extend(endpoints)

            # Identify existing tests that need to run
            tests = self._identify_affected_tests(change)
            affected_tests.extend(tests)

            # Identify new tests needed
            new_tests = self._identify_new_tests_needed(change)
            new_tests_needed.extend(new_tests)

        # Calculate risk level
        risk_level = self._calculate_risk_level(changes, affected_services)

        return ImpactAnalysis(
            changed_files=changes,
            affected_services=list(set(affected_services)),
            affected_endpoints=list(set(affected_endpoints)),
            affected_tests=list(set(affected_tests)),
            new_tests_needed=list(set(new_tests_needed)),
            risk_level=risk_level,
        )

    def _identify_affected_services(self, change: CodeChange) -> List[str]:
        """Identify which services are affected by a change."""
        affected = []

        # Check if change is in a service directory
        for service in getattr(self.manifest, "services", []):
            service_path = self.project_root / service.name
            if service_path in change.file_path.parents or service_path == change.file_path.parent:
                affected.append(service.name)

        # Check endpoint mappings
        for endpoint in change.affected_endpoints:
            service = self._map_endpoint_to_service(endpoint)
            if service:
                affected.append(service)

        return affected

    def _identify_affected_endpoints(self, change: CodeChange) -> List[str]:
        """Identify which endpoints are affected by a change."""
        endpoints = []

        # Direct endpoint changes
        endpoints.extend(change.affected_endpoints)

        # Check if function name matches an endpoint
        if change.function_name:
            for service in getattr(self.manifest, "services", []):
                for ep in service.endpoints:
                    if change.function_name.lower() in ep.name.lower():
                        endpoints.append(ep.name)

        return endpoints

    def _identify_affected_tests(self, change: CodeChange) -> List[str]:
        """Identify existing tests that should be run."""
        tests = []

        # Find tests related to changed endpoints
        for endpoint in change.affected_endpoints:
            test_pattern = f"*{endpoint}*"
            tests.append(test_pattern)

        # Find tests related to changed functions
        if change.function_name:
            tests.append(f"*{change.function_name}*")

        # Find tests related to changed classes
        if change.class_name:
            tests.append(f"*{change.class_name}*")

        return tests

    def _identify_new_tests_needed(self, change: CodeChange) -> List[str]:
        """Identify new tests that should be created."""
        new_tests = []

        # New endpoints need tests
        if change.change_type == "added" and change.affected_endpoints:
            for endpoint in change.affected_endpoints:
                new_tests.append(f"Test for new endpoint: {endpoint}")

        # New functions need tests
        if change.change_type == "added" and change.function_name:
            new_tests.append(f"Test for new function: {change.function_name}")

        # Modified logic might need updated tests
        if change.change_type == "modified" and change.lines_added > 5:
            new_tests.append(f"Update tests for modified: {change.file_path.name}")

        return new_tests

    def _map_endpoint_to_service(self, endpoint: str) -> Optional[str]:
        """Map an endpoint path to a service name."""
        for service in getattr(self.manifest, "services", []):
            for ep in service.endpoints:
                if endpoint in ep.path or endpoint in ep.name:
                    return service.name
        return None

    def _calculate_risk_level(self, changes: List[CodeChange], affected_services: List[str]) -> str:
        """Calculate the risk level of changes."""
        total_lines_changed = sum(c.lines_added + c.lines_deleted for c in changes)

        # Critical: Changes to critical services or many lines
        if len(affected_services) > 2 or total_lines_changed > 500:
            return "critical"

        # High: Changes affecting multiple services or moderate lines
        if len(affected_services) > 1 or total_lines_changed > 200:
            return "high"

        # Medium: Changes with some complexity
        if total_lines_changed > 50 or any(c.change_type == "deleted" for c in changes):
            return "medium"

        # Low: Simple changes
        return "low"


class RegressionAgent:
    """AI Regression Agent for differential testing."""

    def __init__(self, project_root: Path, base_ref: str = "HEAD~1", target_ref: str = "HEAD"):
        """Initialize the regression agent.

        Args:
            project_root: Root directory of the project
            base_ref: Base git reference for comparison
            target_ref: Target git reference for comparison
        """
        self.project_root = Path(project_root).resolve()
        self.base_ref = base_ref
        self.target_ref = target_ref
        self.git_analyzer = GitDiffAnalyzer(project_root)
        self.impact_analyzer: Optional[ImpactAnalyzer] = None

    def load_manifest(self) -> Any:
        """Load the project manifest."""
        manifest_path = self.project_root / "project_knowledge.json"
        if not manifest_path.exists():
            return None

        try:
            import json

            with open(manifest_path, "r") as f:
                data = json.load(f)
            # Import here to avoid circular imports
            from socialseed_e2e.project_manifest.models import ProjectKnowledge

            return ProjectKnowledge(**data)
        except Exception:
            return None

    def run_analysis(self) -> ImpactAnalysis:
        """Run complete regression analysis.

        Returns:
            ImpactAnalysis with all findings
        """
        # Load manifest
        manifest = self.load_manifest()
        if not manifest:
            raise ValueError("No project manifest found. Run 'e2e manifest' first.")

        # Initialize impact analyzer
        self.impact_analyzer = ImpactAnalyzer(self.project_root, manifest)

        # Analyze git changes
        changes = self.git_analyzer.analyze_changes(self.base_ref, self.target_ref)

        if not changes:
            print("No changes detected.")
            return ImpactAnalysis(changed_files=[])

        # Analyze impact
        impact = self.impact_analyzer.analyze_impact(changes)

        return impact

    def get_tests_to_run(self, impact: ImpactAnalysis) -> Dict[str, List[str]]:
        """Get list of tests that should be executed.

        Args:
            impact: Impact analysis results

        Returns:
            Dictionary mapping service names to test patterns
        """
        tests_by_service: Dict[str, List[str]] = {}

        for service in impact.affected_services:
            tests_by_service[service] = []

        # Map affected tests to services
        for test_pattern in impact.affected_tests:
            for service in impact.affected_services:
                if service not in tests_by_service:
                    tests_by_service[service] = []
                tests_by_service[service].append(test_pattern)

        return tests_by_service

    def generate_report(self, impact: ImpactAnalysis) -> str:
        """Generate a markdown report of the analysis.

        Args:
            impact: Impact analysis results

        Returns:
            Markdown formatted report
        """
        lines = [
            "# 🤖 AI Regression Analysis Report",
            "",
            f"**Base Reference:** `{self.base_ref}`",
            f"**Target Reference:** `{self.target_ref}`",
            f"**Risk Level:** {impact.risk_level.upper()}",
            "",
            "---",
            "",
            "## 📊 Summary",
            "",
            f"- **Files Changed:** {len(impact.changed_files)}",
            f"- **Services Affected:** {len(impact.affected_services)}",
            f"- **Endpoints Affected:** {len(impact.affected_endpoints)}",
            f"- **Tests to Run:** {len(impact.affected_tests)}",
            f"- **New Tests Needed:** {len(impact.new_tests_needed)}",
            "",
        ]

        # Changed files
        if impact.changed_files:
            lines.extend(["## 📝 Changed Files", ""])
            for change in impact.changed_files:
                lines.append(f"### {change.file_path.name}")
                lines.append(f"- **Type:** {change.change_type}")
                lines.append(f"- **Lines:** +{change.lines_added}/-{change.lines_deleted}")
                if change.function_name:
                    lines.append(f"- **Function:** `{change.function_name}`")
                if change.class_name:
                    lines.append(f"- **Class:** `{change.class_name}`")
                if change.affected_endpoints:
                    lines.append(f"- **Endpoints:** {', '.join(change.affected_endpoints)}")
                lines.append("")

        # Affected services
        if impact.affected_services:
            lines.extend(["## 🎯 Affected Services", ""])
            for service in impact.affected_services:
                lines.append(f"- {service}")
            lines.append("")

        # Tests to run
        if impact.affected_tests:
            lines.extend(["## 🧪 Tests to Execute", ""])
            lines.append("Run these tests to verify the changes:")
            lines.append("")
            lines.append("```bash")
            for service in impact.affected_services:
                lines.append(f"e2e run --service {service}")
            lines.append("```")
            lines.append("")

        # New tests needed
        if impact.new_tests_needed:
            lines.extend(["## ✨ New Tests Recommended", ""])
            for test in impact.new_tests_needed:
                lines.append(f"- [ ] {test}")
            lines.append("")

        # Recommendations
        lines.extend(
            [
                "## 💡 Recommendations",
                "",
            ]
        )

        if impact.risk_level in ["critical", "high"]:
            lines.extend(
                [
                    "🔴 **High Risk Changes Detected**",
                    "- Run all affected tests before merging",
                    "- Consider manual code review",
                    "- Verify no breaking changes introduced",
                    "",
                ]
            )

        lines.extend(
            [
                "✅ **Next Steps:**",
                "1. Execute the affected tests listed above",
                "2. Review any new tests recommended",
                "3. Ensure all tests pass before merging",
                "",
            ]
        )

        lines.extend(
            [
                "---",
                "",
                "*Generated by AI Regression Agent*",
            ]
        )

        return "\n".join(lines)


def run_regression_analysis(
    project_root: Path, base_ref: str = "HEAD~1", target_ref: str = "HEAD"
) -> Tuple[ImpactAnalysis, str]:
    """Convenience function to run regression analysis.

    Args:
        project_root: Root directory of the project
        base_ref: Base git reference
        target_ref: Target git reference

    Returns:
        Tuple of (ImpactAnalysis, report_markdown)
    """
    agent = RegressionAgent(project_root, base_ref, target_ref)
    impact = agent.run_analysis()
    report = agent.generate_report(impact)
    return impact, report
