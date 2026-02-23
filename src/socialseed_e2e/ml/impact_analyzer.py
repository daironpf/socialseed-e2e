"""Code Impact Analyzer for ML-Based Predictive Test Selection.

This module analyzes git diffs and code changes to identify affected code paths
and determine which tests are most likely to be impacted by changes.
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from socialseed_e2e.ml.models import ChangeType, CodeChange, FileType, ImpactAnalysis, TestPriority


class ImpactAnalyzer:
    """Analyzes code changes and their impact on tests.

    This class uses git diff analysis to identify changed files, functions,
    and classes, then determines which tests are likely affected by these changes.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the impact analyzer.

        Args:
            project_root: Root directory of the project. If None, uses current directory.
        """
        self.project_root = project_root or Path.cwd()
        self._file_type_patterns = {
            FileType.TEST: r"(test_.*\.py$|.*_test\.py$|.*\.test\.(js|ts)$|.*\.spec\.(js|ts)$)",
            FileType.CONFIG: r".*\.(json|yaml|yml|toml|conf|config)$",
            FileType.PYTHON: r".*\.py$",
            FileType.JAVASCRIPT: r".*\.js$",
            FileType.TYPESCRIPT: r".*\.(ts|tsx)$",
            FileType.JAVA: r".*\.java$",
        }

    def analyze_git_diff(
        self,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
    ) -> ImpactAnalysis:
        """Analyze git diff between two references.

        Args:
            base_ref: Base git reference (commit, branch, etc.)
            head_ref: Head git reference

        Returns:
            ImpactAnalysis with detailed change information

        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        changed_files = self._get_changed_files(base_ref, head_ref)

        if not changed_files:
            return ImpactAnalysis(
                changed_files=[],
                affected_tests=[],
                impact_score=0.0,
                risk_level=TestPriority.LOW,
            )

        # Analyze each changed file
        analyzed_changes = []
        for change in changed_files:
            analyzed_change = self._analyze_file_change(change)
            analyzed_changes.append(analyzed_change)

        # Determine affected tests
        affected_tests = self._identify_affected_tests(analyzed_changes)

        # Calculate impact score
        impact_score = self._calculate_impact_score(analyzed_changes, affected_tests)

        # Determine risk level
        risk_level = self._determine_risk_level(impact_score, analyzed_changes)

        return ImpactAnalysis(
            changed_files=analyzed_changes,
            affected_tests=affected_tests,
            impact_score=impact_score,
            risk_level=risk_level,
            estimated_tests_to_run=len(affected_tests),
        )

    def _get_changed_files(
        self,
        base_ref: str,
        head_ref: str,
    ) -> List[Dict[str, Any]]:
        """Get list of changed files from git diff.

        Args:
            base_ref: Base git reference
            head_ref: Head git reference

        Returns:
            List of dictionaries with file change information
        """
        try:
            # Get changed files with status
            result = subprocess.run(
                ["git", "diff", "--name-status", base_ref, head_ref],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            changes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0]
                    file_path = parts[1]

                    change_type = self._parse_change_type(status)
                    changes.append(
                        {
                            "file_path": file_path,
                            "change_type": change_type,
                        }
                    )

            return changes

        except subprocess.CalledProcessError:
            return []

    def _parse_change_type(self, status: str) -> ChangeType:
        """Parse git status into ChangeType.

        Args:
            status: Git status character(s)

        Returns:
            ChangeType enum value
        """
        status_map = {
            "A": ChangeType.ADDED,
            "M": ChangeType.MODIFIED,
            "D": ChangeType.DELETED,
            "R": ChangeType.RENAMED,
        }

        # Handle status like 'R100' (rename with similarity)
        status_key = status[0] if status else "M"
        return status_map.get(status_key, ChangeType.MODIFIED)

    def _analyze_file_change(self, change: Dict[str, Any]) -> CodeChange:
        """Analyze a single file change in detail.

        Args:
            change: Dictionary with file_path and change_type

        Returns:
            CodeChange with detailed analysis
        """
        file_path = change["file_path"]
        change_type = change["change_type"]

        # Determine file type
        file_type = self._detect_file_type(file_path)

        # Get detailed diff stats
        lines_added, lines_deleted = self._get_diff_stats(file_path)

        # Extract changed functions and classes
        functions_changed = []
        classes_changed = []
        imports_changed = []

        if file_type in [
            FileType.PYTHON,
            FileType.JAVA,
            FileType.JAVASCRIPT,
            FileType.TYPESCRIPT,
        ]:
            functions_changed = self._extract_changed_functions(file_path)
            classes_changed = self._extract_changed_classes(file_path)
            imports_changed = self._extract_changed_imports(file_path)

        # Check if it's a test file
        is_test_file = self._is_test_file(file_path)

        return CodeChange(
            file_path=file_path,
            change_type=change_type,
            file_type=file_type,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            functions_changed=functions_changed,
            classes_changed=classes_changed,
            imports_changed=imports_changed,
            is_test_file=is_test_file,
        )

    def _detect_file_type(self, file_path: str) -> FileType:
        """Detect the type of a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            FileType enum value
        """
        for file_type, pattern in self._file_type_patterns.items():
            if re.match(pattern, file_path, re.IGNORECASE):
                return file_type
        return FileType.OTHER

    def _get_diff_stats(self, file_path: str) -> Tuple[int, int]:
        """Get line statistics for a file diff.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (lines_added, lines_deleted)
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--numstat", "HEAD~1", "HEAD", "--", file_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            line = result.stdout.strip()
            if line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    added = int(parts[0]) if parts[0].isdigit() else 0
                    deleted = int(parts[1]) if parts[1].isdigit() else 0
                    return added, deleted

            return 0, 0

        except (subprocess.CalledProcessError, ValueError):
            return 0, 0

    def _extract_changed_functions(self, file_path: str) -> List[str]:
        """Extract function/method names that changed in a file.

        Args:
            file_path: Path to the file

        Returns:
            List of changed function names
        """
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1", "HEAD", "--", file_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            diff_content = result.stdout
            functions = set()

            # Pattern for Python function definitions
            python_pattern = r"^[\+\-]\s*def\s+(\w+)"
            # Pattern for Java/JS/TS method definitions
            java_pattern = (
                r"^[\+\-]\s*(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\("
            )

            for line in diff_content.split("\n"):
                # Try Python pattern
                match = re.match(python_pattern, line)
                if match:
                    functions.add(match.group(1))

                # Try Java/JS/TS pattern
                match = re.match(java_pattern, line)
                if match:
                    functions.add(match.group(1))

            return list(functions)

        except subprocess.CalledProcessError:
            return []

    def _extract_changed_classes(self, file_path: str) -> List[str]:
        """Extract class names that changed in a file.

        Args:
            file_path: Path to the file

        Returns:
            List of changed class names
        """
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1", "HEAD", "--", file_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            diff_content = result.stdout
            classes = set()

            # Pattern for Python/Java/JS/TS class definitions
            pattern = r"^[\+\-]\s*class\s+(\w+)"

            for line in diff_content.split("\n"):
                match = re.match(pattern, line)
                if match:
                    classes.add(match.group(1))

            return list(classes)

        except subprocess.CalledProcessError:
            return []

    def _extract_changed_imports(self, file_path: str) -> List[str]:
        """Extract import statements that changed in a file.

        Args:
            file_path: Path to the file

        Returns:
            List of changed import statements
        """
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1", "HEAD", "--", file_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            diff_content = result.stdout
            imports = []

            # Pattern for Python/Java/JS/TS imports
            patterns = [
                r"^[\+\-]\s*import\s+(.+)",
                r"^[\+\-]\s*from\s+(.+)\s+import",
                r"^[\+\-]\s*require\s*\(\s*['\"](.+)['\"]\s*\)",
            ]

            for line in diff_content.split("\n"):
                for pattern in patterns:
                    match = re.match(pattern, line)
                    if match:
                        imports.append(match.group(1).strip())
                        break

            return imports

        except subprocess.CalledProcessError:
            return []

    def _is_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file.

        Args:
            file_path: Path to the file

        Returns:
            True if file appears to be a test file
        """
        # Check for test naming patterns
        test_patterns = [
            r"test_.*\.py$",
            r".*_test\.py$",
            r".*\.test\.(js|ts)$",
            r".*\.spec\.(js|ts)$",
        ]

        for pattern in test_patterns:
            if re.match(pattern, file_path, re.IGNORECASE):
                return True

        # Check for test directory patterns (match anywhere in path)
        test_dir_patterns = [
            r"(^|/)tests?/",
            r"/__tests__/",
        ]

        for pattern in test_dir_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True

        return False

    def _identify_affected_tests(self, changes: List[CodeChange]) -> List[str]:
        """Identify which tests are likely affected by code changes.

        Args:
            changes: List of code changes

        Returns:
            List of affected test identifiers
        """
        affected_tests = set()

        for change in changes:
            # If it's a test file change, include it directly
            if change.is_test_file:
                affected_tests.add(change.file_path)
                continue

            # For source files, find related tests
            related_tests = self._find_related_tests(change)
            affected_tests.update(related_tests)

        return sorted(affected_tests)

    def _find_related_tests(self, change: CodeChange) -> List[str]:
        """Find tests related to a code change.

        Args:
            change: Code change to analyze

        Returns:
            List of related test file paths
        """
        related_tests = []

        # Map source files to test files based on naming conventions
        source_path = Path(change.file_path)

        # Common test file naming patterns
        test_patterns = [
            f"test_{source_path.stem}.py",
            f"{source_path.stem}_test.py",
            f"{source_path.stem}.test.js",
            f"{source_path.stem}.spec.js",
            f"{source_path.stem}.test.ts",
            f"{source_path.stem}.spec.ts",
        ]

        # Look for tests in common locations
        test_dirs = ["tests", "test", "__tests__"]

        for test_dir in test_dirs:
            for pattern in test_patterns:
                test_path = self.project_root / test_dir / pattern
                if test_path.exists():
                    related_tests.append(str(test_path.relative_to(self.project_root)))

        # Also check in same directory
        for pattern in test_patterns:
            test_path = source_path.parent / pattern
            if test_path.exists():
                related_tests.append(str(test_path.relative_to(self.project_root)))

        return related_tests

    def _calculate_impact_score(
        self,
        changes: List[CodeChange],
        affected_tests: List[str],
    ) -> float:
        """Calculate overall impact score of changes.

        Args:
            changes: List of code changes
            affected_tests: List of affected tests

        Returns:
            Impact score from 0.0 to 1.0
        """
        if not changes:
            return 0.0

        score = 0.0

        # Factor 1: Number of files changed (normalized)
        score += min(len(changes) / 10.0, 0.3)

        # Factor 2: Total lines changed
        total_lines = sum(c.lines_added + c.lines_deleted for c in changes)
        score += min(total_lines / 500.0, 0.3)

        # Factor 3: Number of affected tests (normalized)
        score += min(len(affected_tests) / 50.0, 0.2)

        # Factor 4: Critical files changed
        critical_patterns = ["core", "api", "service", "model", "config"]
        for change in changes:
            if any(pattern in change.file_path.lower() for pattern in critical_patterns):
                score += 0.1
                break

        # Factor 5: Config files changed (higher impact)
        config_changes = [c for c in changes if c.file_type == FileType.CONFIG]
        score += min(len(config_changes) * 0.1, 0.1)

        return min(score, 1.0)

    def _determine_risk_level(
        self,
        impact_score: float,
        changes: List[CodeChange],
    ) -> TestPriority:
        """Determine risk level based on impact score and changes.

        Args:
            impact_score: Calculated impact score
            changes: List of code changes

        Returns:
            TestPriority enum value
        """
        # Check for critical changes
        has_critical_change = any(
            c.file_type == FileType.CONFIG
            or c.change_type == ChangeType.DELETED
            or (c.lines_added + c.lines_deleted > 100)
            for c in changes
        )

        if has_critical_change or impact_score >= 0.8:
            return TestPriority.CRITICAL
        elif impact_score >= 0.6:
            return TestPriority.HIGH
        elif impact_score >= 0.3:
            return TestPriority.MEDIUM
        else:
            return TestPriority.LOW

    def analyze_file_dependencies(self, file_path: str) -> List[str]:
        """Analyze dependencies of a file to find related code.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of dependent file paths
        """
        # This would require parsing imports and building a dependency graph
        # For now, return a simple heuristic-based result
        dependencies = []

        # Read file and extract imports (simplified)
        try:
            with open(self.project_root / file_path, "r") as f:
                content = f.read()

            # Extract Python imports
            import_pattern = r"^from\s+([\w.]+)\s+import|^import\s+([\w.]+)"
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                module = match.group(1) or match.group(2)
                if module:
                    # Convert module path to file path
                    module_path = module.replace(".", "/")
                    potential_path = self.project_root / f"{module_path}.py"
                    if potential_path.exists():
                        dependencies.append(str(potential_path.relative_to(self.project_root)))

        except (IOError, OSError):
            pass

        return dependencies

    def get_coverage_for_changes(
        self,
        changes: List[CodeChange],
        coverage_data: Optional[Dict] = None,
    ) -> Tuple[float, float]:
        """Get coverage information for changed code.

        Args:
            changes: List of code changes
            coverage_data: Optional coverage report data

        Returns:
            Tuple of (new_code_coverage, modified_code_coverage)
        """
        # This would integrate with coverage tools
        # For now, return placeholder values
        new_coverage = 0.0
        modified_coverage = 0.0

        new_changes = [c for c in changes if c.change_type == ChangeType.ADDED]
        modified_changes = [c for c in changes if c.change_type == ChangeType.MODIFIED]

        # Calculate based on number of changes (placeholder logic)
        if new_changes:
            new_coverage = min(100.0, len(new_changes) * 10.0)

        if modified_changes:
            modified_coverage = min(100.0, len(modified_changes) * 15.0)

        return new_coverage, modified_coverage
