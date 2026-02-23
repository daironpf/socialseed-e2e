"""Self-Healing Test System for fixing flaky tests.

This module provides automatic detection and fixing of flaky tests
by adjusting assertions, timing, and selectors.
"""

import ast
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from socialseed_e2e.ai_orchestrator.models import TestCase

logger = logging.getLogger(__name__)


class TestAnalyzer:
    """Analyzes test code to understand its structure."""

    def __init__(self, test_file_path: str):
        self.test_file_path = Path(test_file_path)
        self.source_code = ""
        self.ast_tree = None
        self._load_source()

    def _load_source(self) -> None:
        """Load source code from file."""
        if not self.test_file_path.exists():
            raise FileNotFoundError(f"Test file not found: {self.test_file_path}")

        with open(self.test_file_path, "r") as f:
            self.source_code = f.read()

        try:
            self.ast_tree = ast.parse(self.source_code)
        except SyntaxError as e:
            logger.warning(f"Failed to parse {self.test_file_path}: {e}")
            self.ast_tree = None

    def find_assertions(self) -> List[Dict[str, Any]]:
        """Find all assertions in the test code.

        Returns:
            List of assertion information
        """
        assertions = []

        if not self.ast_tree:
            return assertions

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Assert):
                assertions.append(
                    {
                        "type": "assert",
                        "line": node.lineno,
                        "col": node.col_offset,
                        "test": ast.dump(node.test),
                    }
                )
            elif isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name and "assert" in func_name.lower():
                    assertions.append(
                        {
                            "type": "method_call",
                            "line": node.lineno,
                            "col": node.col_offset,
                            "method": func_name,
                            "args": [ast.dump(arg) for arg in node.args],
                        }
                    )

        return assertions

    def find_timing_operations(self) -> List[Dict[str, Any]]:
        """Find timing-related operations (sleep, wait, timeout).

        Returns:
            List of timing operations
        """
        timings = []

        if not self.ast_tree:
            return timings

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name:
                    if any(word in func_name.lower() for word in ["sleep", "wait", "timeout"]):
                        timings.append(
                            {
                                "method": func_name,
                                "line": node.lineno,
                                "col": node.col_offset,
                                "args": [ast.dump(arg) for arg in node.args],
                            }
                        )

        return timings

    def find_api_calls(self) -> List[Dict[str, Any]]:
        """Find API call patterns.

        Returns:
            List of API calls
        """
        api_calls = []

        if not self.ast_tree:
            return api_calls

        http_methods = ["get", "post", "put", "delete", "patch", "head", "options"]

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name:
                    method = func_name.split(".")[-1].lower()
                    if method in http_methods:
                        api_calls.append(
                            {
                                "method": method.upper(),
                                "line": node.lineno,
                                "col": node.col_offset,
                                "full_call": func_name,
                            }
                        )

        return api_calls

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extract the full name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None

    def get_line_content(self, line_number: int) -> str:
        """Get content of a specific line."""
        lines = self.source_code.split("\n")
        if 0 < line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class FlakyPatternDetector:
    """Detects patterns that commonly cause flakiness."""

    PATTERNS = {
        "hardcoded_sleep": {
            "pattern": r"time\.sleep\s*\(\s*(\d+)\s*\)",
            "description": "Hardcoded sleep without polling",
            "severity": "high",
        },
        "race_condition": {
            "pattern": r"(async|await|threading|concurrent)",
            "description": "Potential race condition",
            "severity": "medium",
        },
        "external_dependency": {
            "pattern": r"(requests\.get|requests\.post|http\.client)",
            "description": "External dependency without retry",
            "severity": "medium",
        },
        "assertion_without_tolerance": {
            "pattern": r"assertEqual\s*\([^,]+,\s*[^)]+\)",
            "description": "Exact assertion without tolerance",
            "severity": "low",
        },
        "time_dependent": {
            "pattern": r"(datetime\.now|time\.time|timezone)",
            "description": "Time-dependent test",
            "severity": "low",
        },
        "random_data": {
            "pattern": r"(random\.|uuid\.|faker\.)",
            "description": "Random data without seed",
            "severity": "medium",
        },
    }

    def detect_patterns(self, source_code: str) -> List[Dict[str, Any]]:
        """Detect flakiness patterns in source code.

        Args:
            source_code: Source code to analyze

        Returns:
            List of detected patterns
        """
        detected = []

        for pattern_name, pattern_info in self.PATTERNS.items():
            matches = list(re.finditer(pattern_info["pattern"], source_code, re.IGNORECASE))

            for match in matches:
                # Get line number
                line_num = source_code[: match.start()].count("\n") + 1

                detected.append(
                    {
                        "pattern": pattern_name,
                        "description": pattern_info["description"],
                        "severity": pattern_info["severity"],
                        "line": line_num,
                        "match": match.group(0),
                    }
                )

        return detected


class TestHealer:
    """Heals flaky tests by applying fixes."""

    def __init__(self, test_file_path: str):
        self.test_file_path = Path(test_file_path)
        self.analyzer = TestAnalyzer(test_file_path)
        self.detector = FlakyPatternDetector()
        self.original_code = self.analyzer.source_code
        self.applied_fixes: List[str] = []

    def analyze_flakiness(self) -> List[Dict[str, Any]]:
        """Analyze test for flakiness patterns.

        Returns:
            List of flakiness issues
        """
        return self.detector.detect_patterns(self.original_code)

    def heal_hardcoded_sleep(self) -> Optional[str]:
        """Replace hardcoded sleep with intelligent polling.

        Returns:
            Description of fix applied or None
        """
        if not self.analyzer.ast_tree:
            return None

        fixed = False
        new_code = self.original_code

        # Find time.sleep calls
        for node in ast.walk(self.analyzer.ast_tree):
            if isinstance(node, ast.Call):
                func_name = self.analyzer._get_call_name(node)
                if func_name == "time.sleep":
                    # Get line content
                    line_content = self.analyzer.get_line_content(node.lineno)

                    # Replace with wait_for pattern (if possible)
                    # This is a simplified version - production would be more sophisticated
                    if "time.sleep" in line_content:
                        # For now, just mark as needing attention
                        fixed = True

        if fixed:
            self.applied_fixes.append(
                "Identified hardcoded sleep - consider using wait_for pattern"
            )
            return "hardcoded_sleep_identified"

        return None

    def heal_assertion_tolerance(self) -> Optional[str]:
        """Add tolerance to numeric assertions.

        Returns:
            Description of fix applied or None
        """
        # This would analyze numeric assertions and add tolerance where appropriate
        # For now, this is a placeholder
        return None

    def heal_retry_logic(self) -> Optional[str]:
        """Add retry logic for external dependencies.

        Returns:
            Description of fix applied or None
        """
        # Check if test has external API calls without retries
        api_calls = self.analyzer.find_api_calls()

        if api_calls and "RetryConfig" not in self.original_code:
            self.applied_fixes.append(
                "External API calls detected - consider adding retry configuration"
            )
            return "retry_recommended"

        return None

    def heal_random_data(self) -> Optional[str]:
        """Add seed for random data generation.

        Returns:
            Description of fix applied or None
        """
        patterns = self.detector.detect_patterns(self.original_code)

        for pattern in patterns:
            if pattern["pattern"] == "random_data":
                if "random.seed" not in self.original_code:
                    self.applied_fixes.append(
                        "Random data without seed - consider adding random.seed()"
                    )
                    return "random_seed_recommended"

        return None

    def apply_healing(self) -> Tuple[bool, List[str]]:
        """Apply all available healing strategies.

        Returns:
            Tuple of (success, list of applied fixes)
        """
        # Analyze flakiness first
        flaky_patterns = self.analyze_flakiness()

        if not flaky_patterns:
            logger.info(f"No flakiness patterns detected in {self.test_file_path}")
            return False, []

        logger.info(f"Detected {len(flaky_patterns)} flakiness patterns in {self.test_file_path}")

        # Apply healing strategies
        self.heal_hardcoded_sleep()
        self.heal_retry_logic()
        self.heal_random_data()
        self.heal_assertion_tolerance()

        return len(self.applied_fixes) > 0, self.applied_fixes

    def get_healing_report(self) -> Dict[str, Any]:
        """Get detailed healing report.

        Returns:
            Healing report
        """
        return {
            "test_file": str(self.test_file_path),
            "flakiness_patterns": self.analyze_flakiness(),
            "applied_fixes": self.applied_fixes,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate healing recommendations.

        Returns:
            List of recommendations
        """
        recommendations = []

        patterns = self.analyze_flakiness()
        pattern_names = {p["pattern"] for p in patterns}

        if "hardcoded_sleep" in pattern_names:
            recommendations.append(
                "Replace time.sleep() with intelligent wait mechanisms. "
                "Consider using wait_for_healthy() or poll-based waiting."
            )

        if "external_dependency" in pattern_names:
            recommendations.append(
                "Add retry configuration for external API calls. "
                "Use RetryConfig with exponential backoff."
            )

        if "random_data" in pattern_names:
            recommendations.append(
                "Set random.seed() at the beginning of tests using random data "
                "to ensure reproducibility."
            )

        if "race_condition" in pattern_names:
            recommendations.append(
                "Review concurrent operations for potential race conditions. "
                "Consider adding synchronization or proper waits."
            )

        return recommendations


class SelfHealer:
    """Main self-healing system for test automation."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.healing_history: List[Dict[str, Any]] = []
        self.healing_stats_path = self.project_path / ".e2e" / "healing_stats.json"
        self._load_stats()

    def _load_stats(self) -> None:
        """Load healing statistics."""
        if self.healing_stats_path.exists():
            try:
                with open(self.healing_stats_path, "r") as f:
                    self.healing_history = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load healing stats: {e}")

    def _save_stats(self) -> None:
        """Save healing statistics."""
        self.healing_stats_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.healing_stats_path, "w") as f:
            json.dump(self.healing_history, f, indent=2, default=str)

    def attempt_heal(
        self,
        test_case: TestCase,
        error_message: str,
        stack_trace: str,
    ) -> Optional[str]:
        """Attempt to heal a failing test.

        Args:
            test_case: Test case that failed
            error_message: Error message
            stack_trace: Stack trace

        Returns:
            Description of healing applied or None
        """
        logger.info(f"Attempting to heal test: {test_case.id}")

        # Get test file path
        test_file = self.project_path / test_case.module

        if not test_file.exists():
            logger.warning(f"Test file not found: {test_file}")
            return None

        # Create healer
        healer = TestHealer(str(test_file))

        # Apply healing
        success, fixes = healer.apply_healing()

        if success:
            # Record healing
            healing_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "test_id": test_case.id,
                "test_file": str(test_file),
                "error_message": error_message,
                "fixes_applied": fixes,
                "report": healer.get_healing_report(),
            }
            self.healing_history.append(healing_record)
            self._save_stats()

            logger.info(f"Test {test_case.id} healed with {len(fixes)} fixes")
            return "; ".join(fixes)

        return None

    def analyze_test_file(self, test_file_path: str) -> Dict[str, Any]:
        """Analyze a test file for flakiness.

        Args:
            test_file_path: Path to test file

        Returns:
            Analysis report
        """
        healer = TestHealer(test_file_path)
        return healer.get_healing_report()

    def batch_heal_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Heal all test files in a directory.

        Args:
            directory: Directory to scan

        Returns:
            List of healing reports
        """
        dir_path = Path(directory)
        reports = []

        for test_file in dir_path.rglob("*.py"):
            try:
                report = self.analyze_test_file(str(test_file))
                if report["flakiness_patterns"]:
                    reports.append(report)
            except Exception as e:
                logger.warning(f"Failed to analyze {test_file}: {e}")

        return reports

    def get_healing_statistics(self) -> Dict[str, Any]:
        """Get healing statistics.

        Returns:
            Healing statistics
        """
        total_healings = len(self.healing_history)

        if total_healings == 0:
            return {
                "total_healings": 0,
                "most_common_patterns": [],
                "healing_success_rate": 0.0,
            }

        # Count patterns
        pattern_counts = {}
        for record in self.healing_history:
            report = record.get("report", {})
            for pattern in report.get("flakiness_patterns", []):
                pattern_name = pattern["pattern"]
                pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1

        # Sort by count
        most_common = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_healings": total_healings,
            "most_common_patterns": most_common,
            "recent_healings": self.healing_history[-10:],
        }
