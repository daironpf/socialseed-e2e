"""Change Analyzer - Analyzes git changes for risk assessment.

This module provides functionality to analyze git diffs and identify
changed files that could impact API endpoints.
"""

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ChangedFile:
    """Represents a changed file in git."""

    path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    lines_added: int = 0
    lines_deleted: int = 0
    content_changes: List[str] = field(default_factory=list)
    affected_functions: List[str] = field(default_factory=list)


@dataclass
class CodeChange:
    """Represents a code change with impact analysis."""

    file_path: str
    function_name: Optional[str]
    change_type: str  # 'api_route', 'database', 'business_logic', 'test'
    complexity_score: int  # 1-10
    dependencies: List[str] = field(default_factory=list)


class ChangeAnalyzer:
    """Analyzes git changes to identify impacted code areas."""

    # Patterns to identify different types of changes
    API_PATTERNS = [
        r"@app\.(get|post|put|delete|patch)",
        r"@router\.(get|post|put|delete|patch)",
        r"@RequestMapping",
        r"@GetMapping",
        r"@PostMapping",
        r"@PutMapping",
        r"@DeleteMapping",
        r"router\.(get|post|put|delete|patch)",
        r"\.route\(['\"]",
    ]

    DB_PATTERNS = [
        r"@(Column|Entity|Table|Repository)",
        r"db\.(query|execute|session)",
        r"models?\.",
        r"schemas?\.",
    ]

    BUSINESS_LOGIC_PATTERNS = [
        r"def (validate_|process_|handle_|calculate_)",
        r"class.*Service",
        r"class.*Manager",
    ]

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize the change analyzer.

        Args:
            repo_path: Path to git repository. Uses current directory if None.
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.changed_files: List[ChangedFile] = []
        self.code_changes: List[CodeChange] = []

    def analyze_changes(self, since_ref: str = "main") -> List[ChangedFile]:
        """Analyze git changes since a reference.

        Args:
            since_ref: Git reference to compare against (branch, tag, commit)

        Returns:
            List of changed files with details
        """
        self.changed_files = []

        try:
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{since_ref}...HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) >= 2:
                    change_type = self._map_change_type(parts[0])
                    file_path = parts[1]

                    # Get detailed diff for the file
                    lines_added, lines_deleted = self._get_diff_stats(
                        file_path, since_ref
                    )

                    changed_file = ChangedFile(
                        path=file_path,
                        change_type=change_type,
                        lines_added=lines_added,
                        lines_deleted=lines_deleted,
                    )

                    # Analyze content changes
                    changed_file.content_changes = self._analyze_content_changes(
                        file_path, since_ref
                    )
                    changed_file.affected_functions = self._extract_affected_functions(
                        changed_file.content_changes
                    )

                    self.changed_files.append(changed_file)

        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not analyze git changes: {e}")

        return self.changed_files

    def _map_change_type(self, git_status: str) -> str:
        """Map git status to change type."""
        status_map = {
            "A": "added",
            "M": "modified",
            "D": "deleted",
            "R": "renamed",
            "C": "copied",
        }
        return status_map.get(git_status[0], "modified")

    def _get_diff_stats(self, file_path: str, since_ref: str) -> Tuple[int, int]:
        """Get line statistics for a file change."""
        try:
            result = subprocess.run(
                ["git", "diff", "--stat", f"{since_ref}...HEAD", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            # Parse stats like "file.py | 5 +++--"
            line = result.stdout.strip()
            if "|" in line:
                stats_part = line.split("|")[-1].strip()
                # Extract numbers
                additions = stats_part.count("+")
                deletions = stats_part.count("-")
                return additions, deletions

        except subprocess.CalledProcessError:
            pass

        return 0, 0

    def _analyze_content_changes(self, file_path: str, since_ref: str) -> List[str]:
        """Analyze actual content changes in a file."""
        changes = []

        try:
            result = subprocess.run(
                ["git", "diff", f"{since_ref}...HEAD", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            # Extract changed lines (lines starting with + or -)
            for line in result.stdout.split("\n"):
                if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                    changes.append(line[1:].strip())

        except subprocess.CalledProcessError:
            pass

        return changes

    def _extract_affected_functions(self, changes: List[str]) -> List[str]:
        """Extract function/method names from changes."""
        functions = []
        function_pattern = re.compile(r"^def\s+(\w+)|^class\s+(\w+)")

        for change in changes:
            match = function_pattern.match(change)
            if match:
                func_name = match.group(1) or match.group(2)
                if func_name and func_name not in functions:
                    functions.append(func_name)

        return functions

    def categorize_changes(self) -> Dict[str, List[ChangedFile]]:
        """Categorize changed files by type.

        Returns:
            Dictionary with categories and their files
        """
        categories = {
            "api_routes": [],
            "database": [],
            "business_logic": [],
            "tests": [],
            "config": [],
            "other": [],
        }

        for file in self.changed_files:
            if self._is_test_file(file.path):
                categories["tests"].append(file)
            elif self._is_api_file(file):
                categories["api_routes"].append(file)
            elif self._is_database_file(file):
                categories["database"].append(file)
            elif self._is_business_logic_file(file):
                categories["business_logic"].append(file)
            elif self._is_config_file(file.path):
                categories["config"].append(file)
            else:
                categories["other"].append(file)

        return categories

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        test_patterns = ["test_", "_test.py", "tests/", "__tests__/"]
        return any(pattern in file_path for pattern in test_patterns)

    def _is_api_file(self, changed_file: ChangedFile) -> bool:
        """Check if file contains API route changes."""
        # Check file path
        api_keywords = ["router", "controller", "endpoint", "route", "api"]
        if any(kw in changed_file.path.lower() for kw in api_keywords):
            return True

        # Check content changes
        for change in changed_file.content_changes:
            for pattern in self.API_PATTERNS:
                if re.search(pattern, change):
                    return True

        return False

    def _is_database_file(self, changed_file: ChangedFile) -> bool:
        """Check if file contains database-related changes."""
        db_keywords = ["model", "schema", "migration", "entity", "repository"]
        if any(kw in changed_file.path.lower() for kw in db_keywords):
            return True

        for change in changed_file.content_changes:
            for pattern in self.DB_PATTERNS:
                if re.search(pattern, change):
                    return True

        return False

    def _is_business_logic_file(self, changed_file: ChangedFile) -> bool:
        """Check if file contains business logic changes."""
        for change in changed_file.content_changes:
            for pattern in self.BUSINESS_LOGIC_PATTERNS:
                if re.search(pattern, change):
                    return True

        return False

    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        config_patterns = [
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".conf",
            "config",
            "settings",
        ]
        return any(pattern in file_path.lower() for pattern in config_patterns)

    def get_high_impact_files(self) -> List[ChangedFile]:
        """Get files with high impact potential.

        Returns:
            List of changed files with high impact
        """
        high_impact = []

        for file in self.changed_files:
            # High line count changes
            total_lines = file.lines_added + file.lines_deleted
            if total_lines > 50:
                high_impact.append(file)
                continue

            # API route changes
            if self._is_api_file(file):
                high_impact.append(file)
                continue

            # Database model changes
            if self._is_database_file(file):
                high_impact.append(file)
                continue

        return high_impact

    def get_change_summary(self) -> Dict[str, any]:
        """Get a summary of all changes.

        Returns:
            Summary dictionary with statistics
        """
        categories = self.categorize_changes()

        total_lines_added = sum(f.lines_added for f in self.changed_files)
        total_lines_deleted = sum(f.lines_deleted for f in self.changed_files)

        return {
            "total_files_changed": len(self.changed_files),
            "total_lines_added": total_lines_added,
            "total_lines_deleted": total_lines_deleted,
            "categories": {cat: len(files) for cat, files in categories.items()},
            "high_impact_files": len(self.get_high_impact_files()),
            "files_by_extension": self._group_by_extension(),
        }

    def _group_by_extension(self) -> Dict[str, int]:
        """Group changed files by extension."""
        extensions = {}
        for file in self.changed_files:
            ext = Path(file.path).suffix or "no_extension"
            extensions[ext] = extensions.get(ext, 0) + 1
        return extensions

    def get_affected_endpoints_from_changes(self) -> Set[str]:
        """Extract endpoint paths that might be affected by changes.

        Returns:
            Set of endpoint paths
        """
        endpoints = set()
        endpoint_pattern = re.compile(
            r"['\"]([\w/\-:]+)['\"]"  # Matches paths like '/api/users'
        )

        for file in self.changed_files:
            if self._is_api_file(file):
                for change in file.content_changes:
                    # Look for route definitions
                    for pattern in self.API_PATTERNS:
                        match = re.search(pattern + r"\(['\"]([^'\"]+)", change)
                        if match:
                            endpoints.add(match.group(1))

        return endpoints
