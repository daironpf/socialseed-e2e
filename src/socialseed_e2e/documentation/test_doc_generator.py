"""Test case documentation generator.

This module automatically generates documentation for test cases,
including step-by-step descriptions and expected results.
"""

import ast
import inspect
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import TestCaseDoc, TestStepDoc


class TestDocGenerator:
    """Generate automatic documentation for test cases."""

    def __init__(self, project_path: str):
        """Initialize the test documentation generator.

        Args:
            project_path: Path to the test project
        """
        self.project_path = Path(project_path)
        self.test_cases: List[TestCaseDoc] = []

    def scan_test_files(self, patterns: List[str] = None) -> List[Path]:
        """Scan project for test files.

        Args:
            patterns: Glob patterns for test files (default: common patterns)

        Returns:
            List of discovered test file paths
        """
        if patterns is None:
            patterns = [
                "**/test_*.py",
                "**/*_test.py",
                "**/tests/**/*.py",
                "**/modules/**/*.py",
            ]

        test_files = []
        for pattern in patterns:
            test_files.extend(self.project_path.glob(pattern))

        return list(set(test_files))

    def parse_test_function(self, node: ast.FunctionDef, source: str) -> TestCaseDoc:
        """Parse a test function and extract documentation.

        Args:
            node: AST node for the test function
            source: Source code of the file

        Returns:
            TestCaseDoc with extracted information
        """
        test_name = node.name
        docstring = ast.get_docstring(node) or f"Auto-generated test for {test_name}"

        module = self.project_path.name
        service = self._infer_service(node)

        steps = self._extract_steps(node, source)

        return TestCaseDoc(
            test_id=self._generate_test_id(test_name),
            test_name=test_name,
            description=docstring,
            module=module,
            service=service,
            steps=steps,
            expected_outcome=self._extract_expected_outcome(node),
            tags=self._extract_tags(node),
            severity=self._infer_severity(test_name),
        )

    def _infer_service(self, node: ast.FunctionDef) -> str:
        """Infer the service name from test context."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                return decorator.id
            elif isinstance(decorator, ast.Attribute):
                return decorator.attr

        func_name_lower = node.name.lower()
        if "auth" in func_name_lower:
            return "authentication"
        elif "user" in func_name_lower:
            return "users"
        elif "payment" in func_name_lower:
            return "payments"

        return "unknown"

    def _extract_steps(self, node: ast.FunctionDef, source: str) -> List[TestStepDoc]:
        """Extract test steps from the function body.

        Args:
            node: AST node for the test function
            source: Source code of the file

        Returns:
            List of TestStepDoc objects
        """
        steps = []
        step_number = 1

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                step = TestStepDoc(
                    step_number=step_number,
                    description=self._describe_call(child),
                    action=self._format_call(child),
                    expected_result="Verify expected behavior",
                )
                steps.append(step)
                step_number += 1

            elif isinstance(child, ast.Assert):
                step = TestStepDoc(
                    step_number=step_number,
                    description="Assertion check",
                    action=self._format_assert(child),
                    expected_result="Assertion passes",
                )
                steps.append(step)
                step_number += 1

        if not steps:
            steps.append(
                TestStepDoc(
                    step_number=1,
                    description="Execute test",
                    action=node.name,
                    expected_result="Test completes successfully",
                )
            )

        return steps

    def _describe_call(self, node: ast.Call) -> str:
        """Generate a human-readable description for a function call."""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            method_name = node.func.id
        else:
            method_name = "unknown"

        if "get" in method_name.lower():
            return f"Retrieve data using {method_name}"
        elif "post" in method_name.lower():
            return f"Create new resource with {method_name}"
        elif "put" in method_name.lower() or "update" in method_name.lower():
            return f"Update resource using {method_name}"
        elif "delete" in method_name.lower():
            return f"Delete resource using {method_name}"
        elif "assert" in method_name.lower():
            return f"Verify condition with {method_name}"

        return f"Execute {method_name}"

    def _format_call(self, node: ast.Call) -> str:
        """Format a function call as source code."""
        return f"{ast.unparse(node.func)}()"

    def _format_assert(self, node: ast.Assert) -> str:
        """Format an assertion as source code."""
        return f"assert {ast.unparse(node.test)}"

    def _extract_expected_outcome(self, node: ast.FunctionDef) -> str:
        """Extract expected outcome from docstring or infer."""
        docstring = ast.get_docstring(node)
        if docstring:
            lines = docstring.strip().split("\n")
            for line in lines:
                if "expect" in line.lower() or "result" in line.lower():
                    return line.strip()

        return "Test passes without errors"

    def _extract_tags(self, node: ast.FunctionDef) -> List[str]:
        """Extract tags from decorators and naming conventions."""
        tags = []

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                tags.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                if isinstance(decorator.value, ast.Name):
                    tags.append(f"{decorator.value.id}.{decorator.attr}")

        func_name = node.name.lower()
        if "smoke" in func_name:
            tags.append("smoke")
        if "integration" in func_name:
            tags.append("integration")
        if "unit" in func_name:
            tags.append("unit")
        if "e2e" in func_name or "endtoend" in func_name:
            tags.append("e2e")

        return list(set(tags))

    def _infer_severity(self, test_name: str) -> str:
        """Infer test severity from naming conventions."""
        name_lower = test_name.lower()

        if "critical" in name_lower or "core" in name_lower:
            return "critical"
        elif "high" in name_lower or "auth" in name_lower or "security" in name_lower:
            return "high"
        elif "low" in name_lower:
            return "low"

        return "medium"

    def _generate_test_id(self, test_name: str) -> str:
        """Generate a unique test ID."""
        return f"TC-{test_name.upper().replace('_', '-')}"

    def generate_docs(
        self, test_files: Optional[List[Path]] = None
    ) -> List[TestCaseDoc]:
        """Generate documentation for all test cases.

        Args:
            test_files: Optional list of specific test files to process

        Returns:
            List of TestCaseDoc objects
        """
        if test_files is None:
            test_files = self.scan_test_files()

        for test_file in test_files:
            try:
                source = test_file.read_text()
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith(
                        "test_"
                    ):
                        test_case = self.parse_test_function(node, source)
                        self.test_cases.append(test_case)

            except Exception as e:
                print(f"Warning: Could not parse {test_file}: {e}")

        return self.test_cases

    def get_test_by_id(self, test_id: str) -> Optional[TestCaseDoc]:
        """Get a specific test case by ID."""
        for test_case in self.test_cases:
            if test_case.test_id == test_id:
                return test_case
        return None

    def get_tests_by_service(self, service: str) -> List[TestCaseDoc]:
        """Get all test cases for a specific service."""
        return [tc for tc in self.test_cases if tc.service == service]

    def get_tests_by_tag(self, tag: str) -> List[TestCaseDoc]:
        """Get all test cases with a specific tag."""
        return [tc for tc in self.test_cases if tag in tc.tags]

    def get_tests_by_severity(self, severity: str) -> List[TestCaseDoc]:
        """Get all test cases with a specific severity."""
        return [tc for tc in self.test_cases if tc.severity == severity]
