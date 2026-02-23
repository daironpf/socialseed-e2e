"""Intent Baseline Extractor.

Extracts semantic intent baselines from documentation, GitHub issues,
code comments, and test cases to build a model of expected system behavior.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from socialseed_e2e.agents.semantic_analyzer.models import IntentBaseline, IntentSource


class IntentBaselineExtractor:
    """Extracts intent baselines from multiple sources."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.baselines: List[IntentBaseline] = []
        self.extracted_sources: Set[str] = set()

    def extract_all(self) -> List[IntentBaseline]:
        """Extract intent baselines from all available sources."""
        # Extract from documentation
        self._extract_from_docs()

        # Extract from GitHub issues
        self._extract_from_github_issues()

        # Extract from code comments
        self._extract_from_code_comments()

        # Extract from test cases
        self._extract_from_test_cases()

        return self.baselines

    def _extract_from_docs(self) -> None:
        """Extract intent baselines from documentation files."""
        docs_path = self.project_root / "docs"
        if not docs_path.exists():
            return

        # Supported documentation formats
        doc_patterns = ["*.md", "*.rst", "*.txt"]

        for pattern in doc_patterns:
            for doc_file in docs_path.rglob(pattern):
                if str(doc_file) in self.extracted_sources:
                    continue

                try:
                    content = doc_file.read_text(encoding="utf-8")
                    baselines = self._parse_documentation_content(content, doc_file)
                    self.baselines.extend(baselines)
                    self.extracted_sources.add(str(doc_file))
                except Exception as e:
                    print(f"Warning: Could not read {doc_file}: {e}")

    def _parse_documentation_content(self, content: str, file_path: Path) -> List[IntentBaseline]:
        """Parse documentation content to extract intent baselines."""
        baselines = []

        # Look for sections describing behavior
        # Pattern: "## Feature: ..." or "### Behavior: ..."
        behavior_patterns = [
            r"#{2,4}\s*(?:Feature|Behavior|Functionality)[:\s]+(.+?)(?=\n#{2,4}|\Z)",
            r"(?:When|If)\s+(.+?)\s+(?:then|should)\s+(.+?)(?=\n(?:When|If)|\Z)",
        ]

        for pattern in behavior_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for i, match in enumerate(matches):
                title = match.group(1).strip() if match.groups() else f"Doc_{i}"
                full_content = match.group(0).strip()

                # Generate intent ID
                intent_id = f"doc_{file_path.stem}_{i}_{hash(title) % 10000}"

                # Extract expected behavior
                expected_behavior = self._extract_expected_behavior(full_content)

                # Extract success criteria
                success_criteria = self._extract_success_criteria(full_content)

                # Create source reference
                source = IntentSource(
                    source_type="documentation",
                    source_path=str(file_path.relative_to(self.project_root)),
                    title=title,
                    content=full_content[:500],  # First 500 chars
                )

                baseline = IntentBaseline(
                    intent_id=intent_id,
                    description=title,
                    category=self._categorize_intent(title, full_content),
                    expected_behavior=expected_behavior,
                    success_criteria=success_criteria,
                    sources=[source],
                )

                baselines.append(baseline)

        return baselines

    def _extract_from_github_issues(self) -> None:
        """Extract intent baselines from GitHub issues."""
        issues_path = self.project_root / ".github" / "issues"

        # Also check for issues exported as JSON
        issues_json_path = self.project_root / "issues.json"

        if issues_json_path.exists():
            try:
                with open(issues_json_path) as f:
                    issues = json.load(f)

                for issue in issues:
                    if str(issue.get("number")) in self.extracted_sources:
                        continue

                    baseline = self._parse_github_issue(issue)
                    if baseline:
                        self.baselines.append(baseline)
                        self.extracted_sources.add(str(issue.get("number")))
            except Exception as e:
                print(f"Warning: Could not parse issues.json: {e}")

    def _parse_github_issue(self, issue: Dict) -> Optional[IntentBaseline]:
        """Parse a GitHub issue to extract intent baseline."""
        title = issue.get("title", "")
        body = issue.get("body", "")

        # Only extract from feature requests or bugs with expected behavior
        labels = [l.get("name", "").lower() for l in issue.get("labels", [])]

        if not any(l in ["feature", "enhancement", "bug"] for l in labels):
            return None

        # Extract expected behavior from body
        expected_behavior = self._extract_expected_behavior(body)
        if not expected_behavior:
            expected_behavior = title

        # Create source reference
        source = IntentSource(
            source_type="github_issue",
            source_path=f"Issue #{issue.get('number')}",
            url=issue.get("html_url"),
            title=title,
            content=body[:500] if body else "",
        )

        intent_id = f"github_issue_{issue.get('number')}"

        return IntentBaseline(
            intent_id=intent_id,
            description=title,
            category=self._categorize_intent(title, body),
            expected_behavior=expected_behavior,
            success_criteria=self._extract_success_criteria(body),
            sources=[source],
        )

    def _extract_from_code_comments(self) -> None:
        """Extract intent baselines from code comments."""
        # Look for docstrings and comments in source files
        source_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.go"]

        for pattern in source_patterns:
            for source_file in self.project_root.rglob(pattern):
                # Skip test files and virtual environments
                if "test" in str(source_file) or "venv" in str(source_file):
                    continue

                if str(source_file) in self.extracted_sources:
                    continue

                try:
                    content = source_file.read_text(encoding="utf-8")
                    baselines = self._parse_code_comments(content, source_file)
                    self.baselines.extend(baselines)
                    if baselines:
                        self.extracted_sources.add(str(source_file))
                except Exception as e:
                    pass  # Silently skip files that can't be read

    def _parse_code_comments(self, content: str, file_path: Path) -> List[IntentBaseline]:
        """Parse code comments to extract intent baselines."""
        baselines = []

        # Pattern for docstrings describing behavior
        docstring_patterns = [
            r'"""(.+?)"""',
            r"'''(.+?)'''",
        ]

        for pattern in docstring_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for _i, match in enumerate(matches):
                docstring = match.group(1).strip()

                # Look for behavior descriptions in docstrings
                if any(
                    keyword in docstring.lower()
                    for keyword in ["should", "must", "behavior", "when", "if"]
                ):
                    # Find line number
                    line_num = content[: match.start()].count("\n") + 1

                    source = IntentSource(
                        source_type="code_comment",
                        source_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        content=docstring[:300],
                    )

                    intent_id = f"code_{file_path.stem}_{line_num}"

                    baseline = IntentBaseline(
                        intent_id=intent_id,
                        description=docstring.split("\n")[0][:100],
                        category=self._categorize_intent(docstring, ""),
                        expected_behavior=self._extract_expected_behavior(docstring),
                        success_criteria=self._extract_success_criteria(docstring),
                        sources=[source],
                    )

                    baselines.append(baseline)

        return baselines

    def _extract_from_test_cases(self) -> None:
        """Extract intent baselines from test cases."""
        tests_path = self.project_root / "tests"
        if not tests_path.exists():
            return

        test_patterns = ["test_*.py", "*_test.py"]

        for pattern in test_patterns:
            for test_file in tests_path.rglob(pattern):
                if str(test_file) in self.extracted_sources:
                    continue

                try:
                    content = test_file.read_text(encoding="utf-8")
                    baselines = self._parse_test_cases(content, test_file)
                    self.baselines.extend(baselines)
                    if baselines:
                        self.extracted_sources.add(str(test_file))
                except Exception as e:
                    pass

    def _parse_test_cases(self, content: str, file_path: Path) -> List[IntentBaseline]:
        """Parse test cases to extract intent baselines."""
        baselines = []

        # Pattern for test functions
        test_pattern = (
            r"def\s+(test_\w+)\s*\([^)]*\):\s*(?:\"\"\"|''')?\s*(.+?)(?:\"\"\"|''')?(?=\n\s*def|\Z)"
        )

        matches = re.finditer(test_pattern, content, re.DOTALL)
        for match in matches:
            test_name = match.group(1)
            test_body = match.group(2).strip()

            # Find line number
            line_num = content[: match.start()].count("\n") + 1

            source = IntentSource(
                source_type="test_case",
                source_path=str(file_path.relative_to(self.project_root)),
                line_number=line_num,
                title=test_name,
                content=test_body[:300],
            )

            intent_id = f"test_{file_path.stem}_{test_name}"

            baseline = IntentBaseline(
                intent_id=intent_id,
                description=f"Test: {test_name}",
                category=self._categorize_intent(test_name, test_body),
                expected_behavior=self._extract_expected_behavior(test_body),
                success_criteria=self._extract_success_criteria(test_body),
                sources=[source],
                confidence=0.9,  # High confidence from test cases
            )

            baselines.append(baseline)

        return baselines

    def _extract_expected_behavior(self, content: str) -> str:
        """Extract expected behavior from content."""
        # Look for "should", "must", "expected" patterns
        patterns = [
            r"(?:should|must|expected to|will)\s+(.+?)(?:\n|$)",
            r"(?:then|and)\s+(.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: return first sentence
        sentences = content.split(".")
        return sentences[0].strip() if sentences else content.strip()

    def _extract_success_criteria(self, content: str) -> List[str]:
        """Extract success criteria from content."""
        criteria = []

        # Look for bullet points or numbered lists
        bullet_pattern = r"(?:^|\n)[\s]*[-*•][\s]*(.+?)(?=\n[\s]*[-*•]|\n\n|\Z)"
        matches = re.finditer(bullet_pattern, content)

        for match in matches:
            criteria.append(match.group(1).strip())

        # Also look for "success criteria", "acceptance criteria" sections
        criteria_section = re.search(
            r"(?:success|acceptance)\s+criteria[:\s]+(.+?)(?=\n\n|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if criteria_section:
            section_content = criteria_section.group(1)
            # Split by newlines or bullets
            for line in section_content.split("\n"):
                line = line.strip().lstrip("-*•").strip()
                if line and len(line) > 10:
                    criteria.append(line)

        return criteria[:5]  # Limit to top 5 criteria

    def _categorize_intent(self, title: str, content: str) -> str:
        """Categorize intent based on keywords."""
        text = (title + " " + content).lower()

        categories = {
            "user_management": ["user", "login", "auth", "register", "profile"],
            "payment_processing": ["payment", "pay", "billing", "invoice", "charge"],
            "data_management": ["data", "create", "update", "delete", "read", "crud"],
            "notification": ["notify", "email", "push", "alert", "message"],
            "social_features": ["follow", "friend", "like", "share", "comment"],
            "search_discovery": ["search", "find", "filter", "sort", "discover"],
            "security": ["security", "permission", "role", "access", "encrypt"],
            "performance": ["performance", "cache", "optimize", "speed"],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "general"

    def get_baselines_by_category(self, category: str) -> List[IntentBaseline]:
        """Get all baselines for a specific category."""
        return [b for b in self.baselines if b.category == category]

    def get_baselines_by_entity(self, entity: str) -> List[IntentBaseline]:
        """Get all baselines related to a specific entity."""
        return [
            b for b in self.baselines if entity.lower() in [e.lower() for e in b.related_entities]
        ]
