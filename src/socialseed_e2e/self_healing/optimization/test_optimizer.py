"""
Test optimizer for self-healing tests.

Optimizes test suites by removing redundancy, merging similar tests,
and optimizing execution order.
"""

import ast
import uuid
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..models import ChangeType, HealingSuggestion, HealingType, TestOptimization


class TestOptimizer:
    """Optimizes test suites for efficiency and maintainability.

    Analyzes test suites and suggests optimizations:
    - Remove redundant tests
    - Merge similar tests
    - Optimize test order for faster execution
    - Identify slow tests

    Example:
        optimizer = TestOptimizer()

        # Analyze test directory
        optimizations = optimizer.analyze_test_suite(
            test_dir="tests/",
            min_similarity=0.8,
        )

        for opt in optimizations:
            print(f"{opt.optimization_type}: {opt.description}")
    """

    def __init__(self):
        """Initialize test optimizer."""
        self.optimization_history: List[TestOptimization] = []
        self.test_analysis_cache: Dict[str, Dict[str, Any]] = {}

    def analyze_test_suite(
        self,
        test_dir: str,
        min_similarity: float = 0.8,
        execution_times: Optional[Dict[str, float]] = None,
    ) -> List[TestOptimization]:
        """Analyze test suite and suggest optimizations.

        Args:
            test_dir: Directory containing tests
            min_similarity: Minimum similarity threshold for duplicate detection
            execution_times: Optional dict of test execution times

        Returns:
            List of optimization suggestions
        """
        optimizations = []

        # Find all test files
        test_files = list(Path(test_dir).rglob("test_*.py"))

        if len(test_files) < 2:
            return optimizations

        # Analyze each test file
        for test_file in test_files:
            self._analyze_test_file(test_file)

        # Find redundant tests
        redundant = self._find_redundant_tests(test_files, min_similarity)
        for pair in redundant:
            opt = TestOptimization(
                id=str(uuid.uuid4()),
                optimization_type="remove_redundant",
                test_files=[str(pair[0]), str(pair[1])],
                description=f"Tests in {pair[0].name} and {pair[1].name} are highly similar ({pair[2]:.0%})",
                expected_improvement="Reduce test suite size and maintenance burden",
                confidence=pair[2],
            )
            optimizations.append(opt)

        # Find mergeable tests
        mergeable = self._find_mergeable_tests(test_files, min_similarity)
        for group in mergeable:
            opt = TestOptimization(
                id=str(uuid.uuid4()),
                optimization_type="merge_similar",
                test_files=[str(f) for f in group],
                description=f"Consider merging {len(group)} similar test files",
                expected_improvement="Improve maintainability by reducing code duplication",
                confidence=0.75,
            )
            optimizations.append(opt)

        # Optimize order if execution times available
        if execution_times:
            order_opt = self._suggest_order_optimization(test_files, execution_times)
            if order_opt:
                optimizations.append(order_opt)

        # Find slow tests
        slow_tests = self._identify_slow_tests(execution_times or {})
        if slow_tests:
            opt = TestOptimization(
                id=str(uuid.uuid4()),
                optimization_type="optimize_slow",
                test_files=slow_tests,
                description=f"Found {len(slow_tests)} slow tests that could be optimized",
                expected_improvement="Reduce overall test execution time",
                confidence=0.8,
            )
            optimizations.append(opt)

        self.optimization_history.extend(optimizations)
        return optimizations

    def optimize_test_order(
        self,
        test_files: List[Path],
        execution_times: Dict[str, float],
    ) -> List[Path]:
        """Optimize test execution order for faster feedback.

        Strategy: Run fastest tests first to get quick feedback.

        Args:
            test_files: List of test files
            execution_times: Dict mapping file paths to execution times

        Returns:
            Optimized order of test files
        """
        # Sort by execution time (fastest first)
        sorted_files = sorted(
            test_files, key=lambda f: execution_times.get(str(f), float("inf"))
        )

        return sorted_files

    def suggest_test_merge(
        self,
        test_file1: Path,
        test_file2: Path,
    ) -> Optional[HealingSuggestion]:
        """Suggest merging two similar test files.

        Args:
            test_file1: First test file
            test_file2: Second test file

        Returns:
            Healing suggestion or None
        """
        similarity = self._calculate_file_similarity(test_file1, test_file2)

        if similarity < 0.7:
            return None

        return HealingSuggestion(
            id=str(uuid.uuid4()),
            healing_type=HealingType.TEST_OPTIMIZATION,
            change_type=ChangeType.SCHEMA_STRUCTURE,
            description=f"Merge similar test files: {test_file1.name} and {test_file2.name} ({similarity:.0%} similar)",
            code_patch=f"""# Test Merge Suggestion
# Files to merge:
# - {test_file1}
# - {test_file2}

# Consider creating a base test class with common functionality
# and specific test classes for unique behavior

class BaseTest:
    # Common setup and helper methods
    pass

class {test_file1.stem.title()}Test(BaseTest):
    # Specific tests from {test_file1.name}
    pass

class {test_file2.stem.title()}Test(BaseTest):
    # Specific tests from {test_file2.name}
    pass
""",
            confidence=similarity,
            affected_files=[str(test_file1), str(test_file2)],
            auto_applicable=False,
        )

    def identify_unused_tests(
        self,
        test_files: List[Path],
        code_coverage: Dict[str, float],
    ) -> List[TestOptimization]:
        """Identify tests with low or no code coverage.

        Args:
            test_files: List of test files
            code_coverage: Dict mapping test files to coverage percentage

        Returns:
            List of optimization suggestions for unused tests
        """
        optimizations = []

        for test_file in test_files:
            coverage = code_coverage.get(str(test_file), 0)

            if coverage == 0:
                opt = TestOptimization(
                    id=str(uuid.uuid4()),
                    optimization_type="remove_unused",
                    test_files=[str(test_file)],
                    description=f"Test file {test_file.name} has 0% code coverage",
                    expected_improvement="Remove dead code from test suite",
                    confidence=0.9,
                )
                optimizations.append(opt)
            elif coverage < 10:
                opt = TestOptimization(
                    id=str(uuid.uuid4()),
                    optimization_type="review_low_coverage",
                    test_files=[str(test_file)],
                    description=f"Test file {test_file.name} has low coverage ({coverage:.1f}%)",
                    expected_improvement="Review and improve test coverage or remove if redundant",
                    confidence=0.7,
                )
                optimizations.append(opt)

        return optimizations

    def _analyze_test_file(self, test_file: Path) -> Dict[str, Any]:
        """Analyze a single test file.

        Args:
            test_file: Path to test file

        Returns:
            Analysis results
        """
        if str(test_file) in self.test_analysis_cache:
            return self.test_analysis_cache[str(test_file)]

        try:
            content = test_file.read_text()

            # Parse AST
            tree = ast.parse(content)

            # Extract test functions
            test_functions = [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            ]

            # Extract imports
            imports = [
                node.names[0].name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import) and node.names
            ]

            analysis = {
                "file": str(test_file),
                "test_count": len(test_functions),
                "test_functions": test_functions,
                "imports": imports,
                "content": content,
                "lines": len(content.splitlines()),
            }

            self.test_analysis_cache[str(test_file)] = analysis
            return analysis

        except Exception:
            return {
                "file": str(test_file),
                "test_count": 0,
                "test_functions": [],
                "imports": [],
                "content": "",
                "lines": 0,
            }

    def _find_redundant_tests(
        self,
        test_files: List[Path],
        min_similarity: float,
    ) -> List[Tuple[Path, Path, float]]:
        """Find pairs of redundant test files.

        Args:
            test_files: List of test files
            min_similarity: Minimum similarity threshold

        Returns:
            List of (file1, file2, similarity) tuples
        """
        redundant = []

        for i, file1 in enumerate(test_files):
            for file2 in test_files[i + 1 :]:
                similarity = self._calculate_file_similarity(file1, file2)

                if similarity >= min_similarity:
                    redundant.append((file1, file2, similarity))

        return redundant

    def _find_mergeable_tests(
        self,
        test_files: List[Path],
        min_similarity: float,
    ) -> List[List[Path]]:
        """Find groups of mergeable test files.

        Args:
            test_files: List of test files
            min_similarity: Minimum similarity threshold

        Returns:
            List of file groups
        """
        # Build similarity graph
        similar_pairs = self._find_redundant_tests(test_files, min_similarity)

        # Group connected files
        groups: List[Set[Path]] = []

        for file1, file2, _ in similar_pairs:
            # Find if either file is already in a group
            found_group = None
            for group in groups:
                if file1 in group or file2 in group:
                    found_group = group
                    break

            if found_group:
                found_group.add(file1)
                found_group.add(file2)
            else:
                groups.append({file1, file2})

        return [list(group) for group in groups if len(group) > 1]

    def _calculate_file_similarity(self, file1: Path, file2: Path) -> float:
        """Calculate similarity between two test files.

        Args:
            file1: First file
            file2: Second file

        Returns:
            Similarity ratio (0-1)
        """
        try:
            content1 = file1.read_text()
            content2 = file2.read_text()

            return SequenceMatcher(None, content1, content2).ratio()
        except Exception:
            return 0.0

    def _suggest_order_optimization(
        self,
        test_files: List[Path],
        execution_times: Dict[str, float],
    ) -> Optional[TestOptimization]:
        """Suggest optimization of test execution order.

        Args:
            test_files: List of test files
            execution_times: Execution times for each test

        Returns:
            Optimization suggestion or None
        """
        current_order_time = sum(execution_times.get(str(f), 0) for f in test_files)

        # Calculate optimal order time
        sorted_files = sorted(test_files, key=lambda f: execution_times.get(str(f), 0))
        optimal_order_time = sum(execution_times.get(str(f), 0) for f in sorted_files)

        # Time is the same, but feedback is faster
        fastest_first_time = (
            execution_times.get(str(sorted_files[0]), 0) if sorted_files else 0
        )

        if current_order_time > 0:
            return TestOptimization(
                id=str(uuid.uuid4()),
                optimization_type="optimize_order",
                test_files=[str(f) for f in test_files[:5]],  # Show first 5
                description=f"Run fastest tests first for quicker feedback (first test: {fastest_first_time:.2f}s)",
                expected_improvement="Faster feedback on test failures",
                confidence=0.85,
            )

        return None

    def _identify_slow_tests(
        self,
        execution_times: Dict[str, float],
        threshold_seconds: float = 10.0,
    ) -> List[str]:
        """Identify slow tests that could be optimized.

        Args:
            execution_times: Execution times for tests
            threshold_seconds: Threshold for "slow" tests

        Returns:
            List of slow test file paths
        """
        return [
            test_file
            for test_file, time in execution_times.items()
            if time > threshold_seconds
        ]

    def get_optimization_history(self) -> List[TestOptimization]:
        """Get history of all optimizations suggested.

        Returns:
            List of TestOptimization objects
        """
        return self.optimization_history
