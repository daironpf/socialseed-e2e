"""Code Generator for Natural Language to Test Code Translation.

This module generates executable Python test code from parsed natural language
test descriptions.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from socialseed_e2e.nlp.models import (
    ActionType,
    AssertionType,
    EntityType,
    GeneratedCode,
    Language,
    NaturalLanguageTest,
    TranslationContext,
    TranslationResult,
)
from socialseed_e2e.nlp.translator import MultiLanguageTranslator


class TestCodeGenerator:
    """Generate test code from natural language descriptions."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.indent = "    "

    def generate(
        self,
        parsed_test: NaturalLanguageTest,
        context: Optional[TranslationContext] = None,
    ) -> GeneratedCode:
        """Generate test code from parsed test.

        Args:
            parsed_test: Parsed natural language test
            context: Optional translation context

        Returns:
            Generated test code
        """
        context = context or TranslationContext()

        # Generate test name
        test_name = self._generate_test_name(parsed_test)

        # Generate imports
        imports = self._generate_imports(parsed_test, context)

        # Generate docstring
        docstring = self._generate_docstring(parsed_test)

        # Generate test body
        body_code = self._generate_test_body(parsed_test, context)

        # Combine into full test function
        code = self._assemble_test_function(test_name, docstring, body_code)

        # Calculate metrics
        assertions_count = len(parsed_test.assertions)
        lines_of_code = len(code.split("\n"))

        # Determine if review is needed
        requires_review = self._requires_review(parsed_test)

        # Generate suggestions
        suggestions = self._generate_suggestions(parsed_test, context)

        return GeneratedCode(
            test_name=test_name,
            module_name=self._generate_module_name(parsed_test, context),
            code=code,
            imports=imports,
            docstring=docstring,
            assertions_count=assertions_count,
            lines_of_code=lines_of_code,
            source_nl=parsed_test.raw_text,
            confidence=parsed_test.confidence_score,
            requires_review=requires_review,
            suggestions=suggestions,
        )

    def _generate_test_name(self, parsed_test: NaturalLanguageTest) -> str:
        """Generate test function name from parsed test.

        Args:
            parsed_test: Parsed test

        Returns:
            Test function name
        """
        # Start with intent
        name_parts = ["test"]

        # Add action
        if parsed_test.actions:
            action = parsed_test.actions[0]
            action_name = action.action_type.value.lower()
            name_parts.append(action_name)

            # Add target
            if action.target:
                target_clean = re.sub(r"[^\w]", "_", action.target.lower())
                name_parts.append(target_clean)

        # Add entity
        elif parsed_test.entities:
            entity = parsed_test.entities[0]
            entity_name = entity.name.replace(" ", "_").lower()
            name_parts.append(entity_name)

        # Add intent if no other info
        else:
            name_parts.append(parsed_test.intent.value.lower())

        # Add assertion indicator
        if parsed_test.assertions:
            name_parts.append("and_verify")

        return "_".join(name_parts)

    def _generate_imports(
        self, parsed_test: NaturalLanguageTest, context: TranslationContext
    ) -> List[str]:
        """Generate required imports.

        Args:
            parsed_test: Parsed test
            context: Translation context

        Returns:
            List of import statements
        """
        imports = [
            "from socialseed_e2e.core.base_page import BasePage",
            "import pytest",
        ]

        # Add service-specific imports if context available
        if context.service:
            imports.append(
                f"from services.{context.service}.{context.service}_page import {self._to_class_name(context.service)}Page"
            )

        # Add assertions import
        if parsed_test.assertions:
            imports.append("from playwright.sync_api import APIResponse")

        return imports

    def _generate_docstring(self, parsed_test: NaturalLanguageTest) -> str:
        """Generate test docstring.

        Args:
            parsed_test: Parsed test

        Returns:
            Generated docstring
        """
        lines = ['"""']
        lines.append(parsed_test.description)
        lines.append("")

        # Add preconditions
        if parsed_test.preconditions:
            lines.append("Preconditions:")
            for pre in parsed_test.preconditions:
                lines.append(f"    - {pre}")
            lines.append("")

        # Add extracted info
        if parsed_test.entities:
            lines.append("Entities:")
            for entity in parsed_test.entities:
                lines.append(f"    - {entity.entity_type.value}: {entity.name}")
            lines.append("")

        if parsed_test.actions:
            lines.append("Actions:")
            for action in parsed_test.actions:
                action_str = f"    - {action.action_type.value}"
                if action.target:
                    action_str += f" {action.target}"
                lines.append(action_str)
            lines.append("")

        lines.append(f"Generated from: {parsed_test.raw_text[:80]}...")
        lines.append('"""')

        return "\n".join(lines)

    def _generate_test_body(
        self, parsed_test: NaturalLanguageTest, context: TranslationContext
    ) -> List[str]:
        """Generate test body code.

        Args:
            parsed_test: Parsed test
            context: Translation context

        Returns:
            List of code lines
        """
        lines = []

        # Setup
        lines.append("# Initialize page")
        if context.service:
            page_class = self._to_class_name(context.service) + "Page"
            lines.append(f'page = {page_class}("http://localhost:8000")')
        else:
            lines.append('page = BasePage("http://localhost:8000")')
        lines.append("page.setup()")
        lines.append("")

        # Handle authentication if needed
        if context.auth_required or any(
            e.entity_type in [EntityType.USER, EntityType.ADMIN]
            for e in parsed_test.entities
        ):
            lines.append("# Authenticate")
            lines.append('page.headers["Authorization"] = "Bearer ${token}"')
            lines.append("")

        # Generate action code
        for action in parsed_test.actions:
            action_code = self._generate_action_code(action, context)
            lines.extend(action_code)
            lines.append("")

        # Generate assertion code
        for assertion in parsed_test.assertions:
            assertion_code = self._generate_assertion_code(assertion)
            lines.extend(assertion_code)
            lines.append("")

        # Cleanup
        lines.append("# Cleanup")
        lines.append("page.teardown()")

        return lines

    def _generate_action_code(
        self, action: Any, context: TranslationContext
    ) -> List[str]:
        """Generate code for an action.

        Args:
            action: Parsed action
            context: Translation context

        Returns:
            List of code lines
        """
        lines = []

        # Get endpoint info if available
        endpoint_info = action.parameters.get("endpoint", {})
        path = endpoint_info.get("path", "/api/resource")
        method = endpoint_info.get("method", "GET")

        # Generate code based on action type
        if action.action_type == ActionType.LOGIN:
            lines.append("# Perform login")
            lines.append(
                'response = page.post("/api/auth/login", json={"username": "testuser", "password": "Test123!"})'
            )
            lines.append("assert response.status == 200")
            lines.append('token = response.json().get("token")')
            lines.append('page.headers["Authorization"] = f"Bearer {token}"')

        elif action.action_type in [ActionType.CREATE, ActionType.SEND]:
            lines.append(f"# Create/Send request")
            payload = action.parameters.get("suggested_payload", {"key": "value"})
            payload_str = str(payload).replace("'", '"')
            lines.append(f'response = page.post("{path}", json={payload_str})')
            lines.append("page.assert_ok(response)")

        elif action.action_type == ActionType.READ:
            lines.append(f"# Read/Retrieve data")
            lines.append(f'response = page.get("{path}")')
            lines.append("page.assert_ok(response)")
            lines.append("data = response.json()")

        elif action.action_type == ActionType.UPDATE:
            lines.append(f"# Update data")
            payload = action.parameters.get("suggested_payload", {"key": "value"})
            payload_str = str(payload).replace("'", '"')
            lines.append(f'response = page.put("{path}", json={payload_str})')
            lines.append("page.assert_ok(response)")

        elif action.action_type == ActionType.DELETE:
            lines.append(f"# Delete resource")
            lines.append(f'response = page.delete("{path}")')
            lines.append("page.assert_ok(response)")

        elif action.action_type == ActionType.SEARCH:
            lines.append(f"# Search")
            search_term = action.target or "search_term"
            lines.append(f'response = page.get("{path}?q={search_term}")')
            lines.append("page.assert_ok(response)")
            lines.append("results = response.json()")

        else:
            # Generic action
            lines.append(f"# Perform action: {action.action_type.value}")
            if method == "GET":
                lines.append(f'response = page.get("{path}")')
            elif method == "POST":
                lines.append(f'response = page.post("{path}", json={{}})')
            else:
                lines.append(f'response = page.{method.lower()}("{path}")')
            lines.append("page.assert_ok(response)")

        return lines

    def _generate_assertion_code(self, assertion: Any) -> List[str]:
        """Generate code for an assertion.

        Args:
            assertion: Parsed assertion

        Returns:
            List of code lines
        """
        lines = []

        if assertion.assertion_type == AssertionType.STATUS_CODE:
            expected = assertion.expected_value or 200
            lines.append(f"# Assert status code")
            lines.append(f"page.assert_status(response, {expected})")

        elif assertion.assertion_type == AssertionType.FIELD_EXISTS:
            field = assertion.field or "field_name"
            lines.append(f"# Assert field exists")
            lines.append(f'assert "{field}" in data')

        elif assertion.assertion_type == AssertionType.FIELD_VALUE:
            field = assertion.field or "field_name"
            expected = assertion.expected_value or "expected_value"
            if isinstance(expected, str):
                expected = f'"{expected}"'
            lines.append(f"# Assert field value")
            lines.append(f'assert data["{field}"] == {expected}')

        elif assertion.assertion_type == AssertionType.CONTAINS:
            field = assertion.field or "data"
            expected = assertion.expected_value or "expected"
            if isinstance(expected, str):
                expected = f'"{expected}"'
            lines.append(f"# Assert contains")
            lines.append(f"assert {expected} in {field}")

        elif assertion.assertion_type == AssertionType.EQUALS:
            field = assertion.field or "data"
            expected = assertion.expected_value or "expected"
            if isinstance(expected, str):
                expected = f'"{expected}"'
            lines.append(f"# Assert equals")
            lines.append(f"assert {field} == {expected}")

        elif assertion.assertion_type == AssertionType.RESPONSE_TIME:
            max_time = assertion.expected_value or 1000
            lines.append(f"# Assert response time")
            lines.append(f"# TODO: Implement response time assertion")

        elif assertion.assertion_type == AssertionType.IS_NOT_EMPTY:
            field = assertion.field or "data"
            lines.append(f"# Assert not empty")
            lines.append(f"assert len({field}) > 0")

        elif assertion.assertion_type == AssertionType.IS_EMPTY:
            field = assertion.field or "data"
            lines.append(f"# Assert is empty")
            lines.append(f"assert len({field}) == 0")

        else:
            # Generic assertion
            lines.append(f"# Assert: {assertion.assertion_type.value}")
            lines.append("# TODO: Implement custom assertion")

        return lines

    def _assemble_test_function(
        self, test_name: str, docstring: str, body_lines: List[str]
    ) -> str:
        """Assemble complete test function.

        Args:
            test_name: Test function name
            docstring: Test docstring
            body_lines: Body code lines

        Returns:
            Complete test function code
        """
        lines = [f"def {test_name}():"]
        lines.append(self.indent + docstring.replace("\n", "\n" + self.indent))
        lines.append("")

        for line in body_lines:
            if line.strip():
                lines.append(self.indent + line)
            else:
                lines.append("")

        return "\n".join(lines)

    def _generate_module_name(
        self, parsed_test: NaturalLanguageTest, context: TranslationContext
    ) -> str:
        """Generate suggested module name.

        Args:
            parsed_test: Parsed test
            context: Translation context

        Returns:
            Module name
        """
        if context.service:
            service = context.service.lower().replace("-", "_")

            # Determine module based on actions
            if parsed_test.actions:
                action = parsed_test.actions[0].action_type.value
                return f"services/{service}/modules/{action}_{service}.py"

            return f"services/{service}/modules/test_{service}.py"

        return "tests/generated/test_from_nl.py"

    def _requires_review(self, parsed_test: NaturalLanguageTest) -> bool:
        """Determine if test requires manual review.

        Args:
            parsed_test: Parsed test

        Returns:
            True if review needed
        """
        # Low confidence
        if parsed_test.confidence_score < 0.6:
            return True

        # No actions found
        if not parsed_test.actions:
            return True

        # No assertions found
        if not parsed_test.assertions:
            return True

        # Unclear entities
        if any(e.confidence < 0.5 for e in parsed_test.entities):
            return True

        return False

    def _generate_suggestions(
        self, parsed_test: NaturalLanguageTest, context: TranslationContext
    ) -> List[str]:
        """Generate improvement suggestions.

        Args:
            parsed_test: Parsed test
            context: Translation context

        Returns:
            List of suggestions
        """
        suggestions = []

        if not context.service:
            suggestions.append(
                "Consider specifying the target service for better context"
            )

        if not parsed_test.assertions:
            suggestions.append("Add specific assertions to validate the test")

        if parsed_test.confidence_score < 0.7:
            suggestions.append(
                "Review the test description for clarity and specificity"
            )

        if any(a.action_type == ActionType.LOGIN for a in parsed_test.actions):
            suggestions.append("Ensure proper test credentials are configured")

        return suggestions

    def _to_class_name(self, name: str) -> str:
        """Convert snake_case to ClassName.

        Args:
            name: Snake case name

        Returns:
            Class name
        """
        return "".join(word.capitalize() for word in name.split("_"))


class GherkinToCodeConverter:
    """Convert Gherkin/Cucumber features to test code."""

    def __init__(self, project_path: str):
        self.generator = TestCodeGenerator(project_path)

    def convert_feature(self, feature: Any) -> List[GeneratedCode]:
        """Convert Gherkin feature to test code.

        Args:
            feature: Gherkin feature

        Returns:
            List of generated test codes
        """
        generated_tests = []

        for scenario in feature.scenarios:
            # Combine steps into description
            description_parts = [scenario.name]

            if feature.background:
                description_parts.append(f"Background: {feature.background}")

            description_parts.extend([f"Given {s}" for s in scenario.given_steps])
            description_parts.extend([f"When {s}" for s in scenario.when_steps])
            description_parts.extend([f"Then {s}" for s in scenario.then_steps])

            description = ". ".join(description_parts)

            # Parse using translator
            translator = MultiLanguageTranslator()
            parsed = translator.parse(description)

            # Generate code
            code = self.generator.generate(parsed)
            generated_tests.append(code)

        return generated_tests


class NLToCodePipeline:
    """Complete pipeline from natural language to test code."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.translator = MultiLanguageTranslator()
        self.generator = TestCodeGenerator(project_path)

    def translate(
        self,
        description: str,
        context: Optional[TranslationContext] = None,
        language: Optional[Language] = None,
    ) -> TranslationResult:
        """Translate natural language to test code.

        Args:
            description: Natural language description
            context: Optional translation context
            language: Optional specific language

        Returns:
            Translation result
        """
        errors = []
        warnings = []

        try:
            # Parse natural language
            parsed = self.translator.parse(description, language)

            if parsed.confidence_score < 0.5:
                warnings.append(
                    f"Low parsing confidence ({parsed.confidence_score:.2f}). "
                    "Review recommended."
                )

            # Generate code
            generated = self.generator.generate(parsed, context)

            if generated.requires_review:
                warnings.append(
                    "Generated code requires manual review before execution"
                )

            return TranslationResult(
                success=True,
                parsed_test=parsed,
                generated_code=generated,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            errors.append(f"Translation failed: {str(e)}")
            return TranslationResult(
                success=False,
                errors=errors,
                warnings=warnings,
            )

    def translate_batch(
        self,
        descriptions: List[str],
        context: Optional[TranslationContext] = None,
    ) -> List[TranslationResult]:
        """Translate multiple descriptions.

        Args:
            descriptions: List of descriptions
            context: Optional translation context

        Returns:
            List of translation results
        """
        return [self.translate(desc, context) for desc in descriptions]
