"""Integration tests generator for multi-endpoint workflows.

This module detects multi-endpoint workflows and generates integration tests.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Workflow:
    """Represents a workflow/test chain."""

    name: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    description: str = ""


@dataclass
class IntegrationInfo:
    """Represents integration test information."""

    workflows: List[Workflow] = field(default_factory=list)
    test_dependencies: Dict[str, List[str]] = field(default_factory=dict)


class IntegrationTestGenerator:
    """Generates integration tests for workflows."""

    COMMON_WORKFLOWS = [
        ("user_registration", "Registro de usuario", [
            {"endpoint": "/auth/register", "method": "POST", "save": ["user_id", "token"]},
            {"endpoint": "/auth/login", "method": "POST", "save": ["token"]},
            {"endpoint": "/users/me", "method": "GET", "uses": ["token"]},
        ]),
        ("order_checkout", "Proceso de compra", [
            {"endpoint": "/auth/login", "method": "POST", "save": ["token"]},
            {"endpoint": "/cart", "method": "GET", "uses": ["token"]},
            {"endpoint": "/cart/items", "method": "POST", "uses": ["token"], "save": ["cart_id"]},
            {"endpoint": "/orders/checkout", "method": "POST", "uses": ["token", "cart_id"], "save": ["order_id"]},
            {"endpoint": "/orders/{order_id}", "method": "GET", "uses": ["token", "order_id"]},
        ]),
        ("content_publishing", "Publicación de contenido", [
            {"endpoint": "/auth/login", "method": "POST", "save": ["token"]},
            {"endpoint": "/posts", "method": "POST", "uses": ["token"], "save": ["post_id"]},
            {"endpoint": "/posts/{post_id}", "method": "GET", "uses": ["post_id"]},
            {"endpoint": "/posts/{post_id}/publish", "method": "POST", "uses": ["token", "post_id"]},
        ]),
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def generate(self) -> IntegrationInfo:
        """Generate integration tests."""
        info = IntegrationInfo()

        self._generate_workflows(info)
        self._detect_test_dependencies(info)

        return info

    def _generate_workflows(self, info: IntegrationInfo) -> None:
        """Generate workflow tests."""
        for workflow_name, description, steps in self.COMMON_WORKFLOWS:
            workflow = Workflow(name=workflow_name, description=description)
            
            for i, step in enumerate(steps, 1):
                test_code = self._generate_step_code(step, i, workflow_name)
                workflow.steps.append({
                    "step": i,
                    "endpoint": step["endpoint"],
                    "method": step["method"],
                    "test_code": test_code,
                })
            
            info.workflows.append(workflow)

    def _generate_step_code(self, step: Dict, step_num: int, workflow: str) -> str:
        """Generate test code for a workflow step."""
        endpoint = step["endpoint"]
        method = step["method"]
        uses = step.get("uses", [])
        saves = step.get("save", [])

        code = f'''def {workflow}_step{step_num}(page):
    """Step {step_num}: {method} {endpoint}"""
'''
        if uses:
            code += f"    # Uses: {', '.join(uses)}\n"
        
        code += f'    headers = {{}}\n'
        
        if "token" in uses:
            code += '    headers["Authorization"] = f"Bearer {{page.access_token}}"\n'
        
        if method == "GET":
            code += f'    response = page.get("{endpoint}")\n'
        elif method == "POST":
            code += f'    response = page.post("{endpoint}", data={{}})\n'
        elif method == "PUT":
            code += f'    response = page.put("{endpoint}", data={{}})\n'
        elif method == "DELETE":
            code += f'    response = page.delete("{endpoint}")\n'

        code += "    assert response.status in [200, 201]\n"

        return code

    def _detect_test_dependencies(self, info: IntegrationInfo) -> None:
        """Detect test dependencies from test files."""
        test_files = list(self.project_root.glob("tests/**/*.py"))
        
        for test_file in test_files:
            content = test_file.read_text(errors="ignore")
            
            test_funcs = re.findall(r"def (test_\w+)", content)
            for func in test_funcs:
                depends = re.findall(r"(test_\w+)\(", content)
                info.test_dependencies[func] = depends[1:] if len(depends) > 1 else []


def generate_integration_tests_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate INTEGRATION_TESTS.md document."""
    generator = IntegrationTestGenerator(project_root)
    info = generator.generate()

    doc = "# Tests de Integración\n\n"

    doc += "## Flujos de Trabajo (Workflows)\n\n"
    for workflow in info.workflows:
        doc += f"### {workflow.name}\n\n"
        doc += f"**Descripción**: {workflow.description}\n\n"

        doc += "| Step | Endpoint | Method |\n"
        doc += "|------|----------|--------|\n"
        for step in workflow.steps:
            doc += f"| {step['step']} | {step['endpoint']} | {step['method']} |\n"
        doc += "\n"

        doc += "```python\n"
        for step in workflow.steps:
            doc += step["test_code"] + "\n"
        doc += "```\n\n"

    if info.test_dependencies:
        doc += "## Dependencias entre Tests\n\n"
        doc += "| Test | Depende de |\n"
        doc += "|------|----------|\n"
        for test, deps in info.test_dependencies.items():
            doc += f"| {test} | {', '.join(deps) if deps else 'Ninguna'} |\n"
        doc += "\n"

    doc += "---\n\n"
    doc += "## Ejecución\n\n"
    doc += "```bash\n"
    doc += "# Ejecutar workflow completo\n"
    doc += "e2e run --service auth-service --tag workflow\n\n"
    doc += "# Ejecutar solo primer paso\n"
    doc += "e2e run --service auth-service --filter test_user_registration_step1\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_integration_tests_doc(project_root))
    else:
        print("Usage: python integration_tests_generator.py <project_root>")
