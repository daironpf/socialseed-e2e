"""Test Generator for Shadow Runner.

Generates test cases from captured traffic.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.shadow_runner.traffic_interceptor import CapturedInteraction


@dataclass
class GeneratedTest:
    """A generated test case."""

    name: str
    description: str
    code: str
    interactions: List[CapturedInteraction]
    assertions: List[str]
    metadata: Dict[str, Any]

    def save(self, file_path: Path) -> None:
        """Save test to file.

        Args:
            file_path: Path to save file
        """
        file_path.write_text(self.code)


class TestGenerator:
    """Generates tests from captured traffic."""

    def __init__(self):
        """Initialize the test generator."""
        self.template_engine = TestTemplateEngine()

    def generate_test_from_interaction(
        self, interaction: CapturedInteraction, test_name: Optional[str] = None
    ) -> GeneratedTest:
        """Generate a test from a single interaction.

        Args:
            interaction: Captured interaction
            test_name: Optional test name

        Returns:
            Generated test
        """
        if not test_name:
            test_name = self._generate_test_name(interaction)

        # Generate test code
        code = self._generate_single_test_code(interaction, test_name)

        # Generate assertions
        assertions = self._generate_assertions(interaction)

        return GeneratedTest(
            name=test_name,
            description=f"Test for {interaction.request.method} {interaction.request.path}",
            code=code,
            interactions=[interaction],
            assertions=assertions,
            metadata={
                "source": "shadow_runner",
                "generated_at": "auto",
                "interaction_count": 1,
            },
        )

    def generate_test_from_session(
        self,
        interactions: List[CapturedInteraction],
        test_name: str,
        description: str = "",
    ) -> GeneratedTest:
        """Generate a test from a session (multiple interactions).

        Args:
            interactions: List of interactions
            test_name: Test name
            description: Test description

        Returns:
            Generated test
        """
        # Sort by sequence
        sorted_interactions = sorted(interactions, key=lambda i: i.sequence_number)

        # Generate test code
        code = self._generate_session_test_code(sorted_interactions, test_name)

        # Generate assertions for each interaction
        all_assertions = []
        for interaction in sorted_interactions:
            all_assertions.extend(self._generate_assertions(interaction))

        return GeneratedTest(
            name=test_name,
            description=description or f"Session test with {len(interactions)} interactions",
            code=code,
            interactions=sorted_interactions,
            assertions=all_assertions,
            metadata={
                "source": "shadow_runner",
                "generated_at": "auto",
                "interaction_count": len(interactions),
                "is_session_test": True,
            },
        )

    def generate_tests_from_traffic(
        self,
        interactions: List[CapturedInteraction],
        group_by: str = "endpoint",  # "endpoint", "session", "none"
    ) -> List[GeneratedTest]:
        """Generate multiple tests from traffic.

        Args:
            interactions: List of captured interactions
            group_by: How to group tests

        Returns:
            List of generated tests
        """
        tests = []

        if group_by == "none":
            # Generate individual tests
            for i, interaction in enumerate(interactions):
                test_name = f"test_captured_{i + 1}"
                test = self.generate_test_from_interaction(interaction, test_name)
                tests.append(test)

        elif group_by == "endpoint":
            # Group by endpoint
            endpoint_groups: Dict[str, List[CapturedInteraction]] = {}

            for interaction in interactions:
                key = f"{interaction.request.method}_{interaction.request.path}"
                if key not in endpoint_groups:
                    endpoint_groups[key] = []
                endpoint_groups[key].append(interaction)

            for endpoint, endpoint_interactions in endpoint_groups.items():
                test_name = f"test_{self._sanitize_name(endpoint)}"

                if len(endpoint_interactions) == 1:
                    test = self.generate_test_from_interaction(endpoint_interactions[0], test_name)
                else:
                    test = self.generate_test_from_session(
                        endpoint_interactions,
                        test_name,
                        f"Tests for {endpoint}",
                    )
                tests.append(test)

        elif group_by == "session":
            # Group by session
            session_groups: Dict[str, List[CapturedInteraction]] = {}

            for interaction in interactions:
                session_id = interaction.session_id or "no_session"
                if session_id not in session_groups:
                    session_groups[session_id] = []
                session_groups[session_id].append(interaction)

            for session_id, session_interactions in session_groups.items():
                if len(session_interactions) == 1:
                    test = self.generate_test_from_interaction(session_interactions[0])
                else:
                    test_name = f"test_session_{session_id[:8]}"
                    test = self.generate_test_from_session(
                        session_interactions,
                        test_name,
                        f"Session test ({len(session_interactions)} interactions)",
                    )
                tests.append(test)

        return tests

    def _generate_single_test_code(self, interaction: CapturedInteraction, test_name: str) -> str:
        """Generate code for a single test.

        Args:
            interaction: Captured interaction
            test_name: Test name

        Returns:
            Test code
        """
        request = interaction.request
        response = interaction.response

        code_lines = [
            f"async def {test_name}(page):",
            f'    """Test for {request.method} {request.path}"""',
            "",
        ]

        # Generate request
        method = request.method.lower()
        url = request.url

        # Build kwargs
        kwargs = []

        # Add headers if present
        if request.headers:
            headers_dict = self._format_dict(request.headers)
            kwargs.append(f"headers={headers_dict}")

        # Add body if present
        if request.body:
            body_formatted = self._format_body(request.body)
            kwargs.append(f"{body_formatted}")

        kwargs_str = ", ".join(kwargs)

        if kwargs_str:
            code_lines.append(f'    response = await page.{method}("{url}", {kwargs_str})')
        else:
            code_lines.append(f'    response = await page.{method}("{url}")')

        code_lines.append("")

        # Add assertions
        if response:
            code_lines.append("    # Assertions")
            code_lines.append(f"    assert response.status == {response.status_code}")

            # Add body assertion if response has body
            if response.body:
                code_lines.append("")
                code_lines.append("    # Verify response body")
                code_lines.append("    data = await response.json()")
                # Try to extract key fields for assertion
                key_fields = self._extract_key_fields(response.body)
                for field in key_fields[:3]:  # Limit to first 3 fields
                    code_lines.append(f'    assert "{field}" in data')

        code_lines.append("")

        return "\n".join(code_lines)

    def _generate_session_test_code(
        self, interactions: List[CapturedInteraction], test_name: str
    ) -> str:
        """Generate code for a session test.

        Args:
            interactions: List of interactions
            test_name: Test name

        Returns:
            Test code
        """
        code_lines = [
            f"async def {test_name}(page):",
            f'    """Session test with {len(interactions)} steps"""',
            "",
        ]

        for i, interaction in enumerate(interactions, 1):
            request = interaction.request
            response = interaction.response

            code_lines.append(f"    # Step {i}: {request.method} {request.path}")

            method = request.method.lower()
            url = request.url

            # Build kwargs
            kwargs = []

            if request.headers:
                headers_dict = self._format_dict(request.headers)
                kwargs.append(f"headers={headers_dict}")

            if request.body:
                body_formatted = self._format_body(request.body)
                kwargs.append(f"{body_formatted}")

            kwargs_str = ", ".join(kwargs)

            if kwargs_str:
                code_lines.append(f'    response = await page.{method}("{url}", {kwargs_str})')
            else:
                code_lines.append(f'    response = await page.{method}("{url}")')

            # Add assertion
            if response:
                code_lines.append(f"    assert response.status == {response.status_code}")

            code_lines.append("")

        return "\n".join(code_lines)

    def _generate_assertions(self, interaction: CapturedInteraction) -> List[str]:
        """Generate assertions for an interaction.

        Args:
            interaction: Captured interaction

        Returns:
            List of assertions
        """
        assertions = []

        if interaction.response:
            assertions.append(f"Status code == {interaction.response.status_code}")

            # Try to check response time
            if interaction.response.latency_ms > 0:
                assertions.append(f"Response time < {interaction.response.latency_ms * 2:.0f}ms")

            # Check for error status codes
            if interaction.response.status_code >= 400:
                assertions.append("Error response structure valid")

        return assertions

    def _generate_test_name(self, interaction: CapturedInteraction) -> str:
        """Generate a test name from an interaction.

        Args:
            interaction: Captured interaction

        Returns:
            Test name
        """
        method = interaction.request.method.lower()
        path = interaction.request.path.replace("/", "_").strip("_")
        path = re.sub(r"[^a-zA-Z0-9_]", "_", path)

        return f"test_{method}_{path}"

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in Python.

        Args:
            name: Name to sanitize

        Returns:
            Sanitized name
        """
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        name = re.sub(r"_+", "_", name)
        return name.strip("_").lower()

    def _format_dict(self, data: Dict[str, str]) -> str:
        """Format a dictionary for code.

        Args:
            data: Dictionary

        Returns:
            Formatted string
        """
        items = [f'"{k}": "{v}"' for k, v in list(data.items())[:5]]  # Limit to 5 headers
        return "{" + ", ".join(items) + "}"

    def _format_body(self, body: str) -> str:
        """Format a body for code.

        Args:
            body: Body string

        Returns:
            Formatted string
        """
        try:
            import json

            data = json.loads(body)
            # Limit depth and size
            if isinstance(data, dict):
                limited = {k: v for i, (k, v) in enumerate(data.items()) if i < 5}
                return f"json={json.dumps(limited)}"
        except json.JSONDecodeError:
            pass

        # Return as string
        body_escaped = body.replace('"', '\\"')[:200]  # Limit length
        return f'data="{body_escaped}"'

    def _extract_key_fields(self, body: str) -> List[str]:
        """Extract key fields from a JSON body.

        Args:
            body: JSON body

        Returns:
            List of field names
        """
        try:
            import json

            data = json.loads(body)
            if isinstance(data, dict):
                return list(data.keys())[:5]
        except json.JSONDecodeError:
            pass

        return []


class TestTemplateEngine:
    """Template engine for generating test code."""

    TEMPLATES = {
        "basic_get": """
async def {test_name}(page):
    \"\"\"{description}\"\"\"
    response = await page.get("{url}")
    assert response.status == {status_code}
""",
        "basic_post": """
async def {test_name}(page):
    \"\"\"{description}\"\"\"
    data = {body}
    response = await page.post("{url}", json=data)
    assert response.status == {status_code}
""",
        "session_flow": """
async def {test_name}(page):
    \"\"\"{description}\"\"\"
{steps}
""",
    }

    def render(self, template_name: str, **kwargs) -> str:
        """Render a template.

        Args:
            template_name: Template name
            **kwargs: Template variables

        Returns:
            Rendered template
        """
        template = self.TEMPLATES.get(template_name, self.TEMPLATES["basic_get"])
        return template.format(**kwargs)


class TestExporter:
    """Exports generated tests to various formats."""

    def export_to_python_file(
        self,
        tests: List[GeneratedTest],
        output_path: Path,
        service_name: str = "captured",
    ) -> None:
        """Export tests to a Python file.

        Args:
            tests: List of tests
            output_path: Output file path
            service_name: Service name
        """
        lines = [
            f'"""Auto-generated tests from shadow runner for {service_name} service."""',
            "",
            "from socialseed_e2e.core.base_page import BasePage",
            "",
            "",
            f"class {service_name.title()}CapturedTests(BasePage):",
            f'    """Captured tests for {service_name}."""',
            "",
            "    def __init__(self):",
            '        super().__init__(base_url="http://localhost:8000")',
            "",
        ]

        for test in tests:
            lines.append(test.code)
            lines.append("")

        output_path.write_text("\n".join(lines))

    def export_to_service_directory(
        self,
        tests: List[GeneratedTest],
        service_name: str,
        base_path: Path = Path("services"),
    ) -> Path:
        """Export tests to a service directory structure.

        Args:
            tests: List of tests
            service_name: Service name
            base_path: Base services path

        Returns:
            Path to created file
        """
        # Create directory structure
        service_dir = base_path / service_name / "modules"
        service_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py if not exists
        init_file = service_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")

        # Create test file
        test_file = service_dir / "test_shadow_captured.py"

        self.export_to_python_file(tests, test_file, service_name)

        return test_file
