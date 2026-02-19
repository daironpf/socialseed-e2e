"""VS Code extension integration.

This module provides VS Code extension support including:
- Test generation
- Test execution
- Debugging support
- Code completion
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import (
    IDEType,
    TestTemplate,
    LaunchConfig,
    DebugConfig,
    CompletionItem,
)


class VSCodeExtension:
    """VS Code extension for SocialSeed E2E."""

    def __init__(self, workspace_path: str):
        """Initialize VS Code extension.

        Args:
            workspace_path: Path to VS Code workspace
        """
        self.workspace_path = Path(workspace_path)
        self.extension_dir = self.workspace_path / ".vscode"
        self.extension_dir.mkdir(parents=True, exist_ok=True)

    def generate_settings(
        self, base_url: str = "http://localhost:8080"
    ) -> Dict[str, Any]:
        """Generate VS Code settings for E2E testing.

        Args:
            base_url: Base URL for API testing

        Returns:
            Settings dictionary
        """
        settings = {
            "e2e.baseUrl": base_url,
            "e2e.defaultTimeout": 30000,
            "e2e.headless": True,
            "e2e.trace": "off",
            "python.testing.pytestEnabled": True,
            "python.testing.pytestArgs": ["-v", "--tb=short"],
        }
        return settings

    def generate_launch_config(self) -> LaunchConfig:
        """Generate launch configuration for debugging tests.

        Returns:
            LaunchConfig object
        """
        config = LaunchConfig(
            version="0.2.0",
            configurations=[
                DebugConfig(
                    name="E2E: Run All Tests",
                    type="python",
                    request="launch",
                    module="pytest",
                    args=["tests/", "-v"],
                    env={"E2E_MODE": "test"},
                ),
                DebugConfig(
                    name="E2E: Run Current Test",
                    type="python",
                    request="launch",
                    module="pytest",
                    args=["-v", "--tb=short", "${relativeFile}"],
                    env={"E2E_MODE": "test"},
                ),
                DebugConfig(
                    name="E2E: Debug Test",
                    type="python",
                    request="launch",
                    module="pytest",
                    args=[
                        "-v",
                        "--tb=long",
                        "${relativeFile}",
                        "-k",
                        "${selectedText}",
                    ],
                    env={"E2E_MODE": "debug"},
                ),
                DebugConfig(
                    name="E2E: Record Session",
                    type="python",
                    request="launch",
                    module="e2e",
                    args=["recorder", "start"],
                    env={"E2E_MODE": "record"},
                ),
            ],
        )
        return config

    def generate_tasks(self) -> Dict[str, Any]:
        """Generate VS Code tasks.

        Returns:
            Tasks configuration
        """
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "E2E: Install Dependencies",
                    "type": "shell",
                    "command": "pip install -e .",
                    "problemMatcher": [],
                    "group": "none",
                },
                {
                    "label": "E2E: Run Tests",
                    "type": "shell",
                    "command": "e2e run",
                    "problemMatcher": ["$pytest"],
                    "group": "test",
                },
                {
                    "label": "E2E: Generate Tests",
                    "type": "shell",
                    "command": "e2e generate-tests",
                    "problemMatcher": [],
                    "group": "build",
                },
                {
                    "label": "E2E: Record Session",
                    "type": "shell",
                    "command": "e2e recorder start",
                    "problemMatcher": [],
                    "group": "none",
                },
            ],
        }
        return tasks

    def generate_snippets(self) -> Dict[str, List[Dict[str, str]]]:
        """Generate code snippets for test writing.

        Returns:
            Snippets configuration
        """
        snippets = {
            "e2e-test": [
                {
                    "prefix": "e2etest",
                    "body": [
                        "def test_${1:scenario}(page):",
                        '    """${2:Test description}"""',
                        '    response = page.get("${3:/api/endpoint}")',
                        "    assert response.status_code == ${4:200}",
                        "",
                    ],
                    "description": "E2E API test",
                }
            ],
            "e2e-post": [
                {
                    "prefix": "e2epost",
                    "body": [
                        "def test_create_${1:resource}(page):",
                        '    """Create ${2:resource}"""',
                        "    payload = {",
                        "        ${3}",
                        "    }",
                        '    response = page.post("${4:/api/${5:resource}}", data=payload)',
                        "    assert response.status_code == 201",
                    ],
                    "description": "E2E POST test",
                }
            ],
            "e2e-assert": [
                {
                    "prefix": "e2eassert",
                    "body": [
                        'assert response.json()[${1:"field"}] == ${2:expected}',
                    ],
                    "description": "E2E assertion",
                }
            ],
        }
        return snippets

    def write_config_files(self, base_url: str = "http://localhost:8080"):
        """Write all VS Code configuration files.

        Args:
            base_url: Base URL for testing
        """
        settings = self.generate_settings(base_url)
        launch = self.generate_launch_config()
        tasks = self.generate_tasks()
        snippets = self.generate_snippets()

        (self.extension_dir / "settings.json").write_text(
            json.dumps(settings, indent=2)
        )
        (self.extension_dir / "launch.json").write_text(
            json.dumps(launch.model_dump(), indent=2)
        )
        (self.extension_dir / "tasks.json").write_text(json.dumps(tasks, indent=2))

        snippets_file = self.extension_dir / "e2e.code-snippets"
        snippets_content = self._format_snippets(snippets)
        snippets_file.write_text(snippets_content)

    def _format_snippets(self, snippets: Dict[str, List[Dict[str, str]]]) -> str:
        """Format snippets for VS Code.

        Args:
            snippets: Snippets dictionary

        Returns:
            Formatted snippets content
        """
        lines = []

        for scope, snippet_list in snippets.items():
            for snippet in snippet_list:
                lines.append(f"'{scope}.{snippet['prefix']}':")
                lines.append(f"    prefix: {snippet['prefix']}")
                lines.append(f"    body: |")
                for line in snippet["body"]:
                    lines.append(f"        {line}")
                lines.append(f"    description: {snippet['description']}")
                lines.append("")

        return "\n".join(lines)


class VSCodeCommands:
    """VS Code commands for E2E testing."""

    @staticmethod
    def generate_test_from_endpoint(endpoint: str, method: str) -> str:
        """Generate test code for an endpoint.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            Test code string
        """
        test_name = f"test_{method.lower()}_{endpoint.replace('/', '_').strip('_')}"

        code = f'''
def {test_name}(page):
    """Test {method} {endpoint}"""
    response = page.{method.lower()}("{endpoint}")
    assert response.status_code == 200
'''
        return code

    @staticmethod
    def generate_test_from_openapi(spec_path: str) -> List[str]:
        """Generate tests from OpenAPI spec.

        Args:
            spec_path: Path to OpenAPI spec

        Returns:
            List of test code strings
        """
        tests = []

        try:
            spec = json.loads(Path(spec_path).read_text())
            paths = spec.get("paths", {})

            for path, methods in paths.items():
                for method in methods.keys():
                    if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        test_code = VSCodeCommands.generate_test_from_endpoint(
                            path, method
                        )
                        tests.append(test_code)

        except Exception as e:
            print(f"Error generating tests: {e}")

        return tests

    @staticmethod
    def get_completions() -> List[CompletionItem]:
        """Get code completion items for E2E API.

        Returns:
            List of completion items
        """
        return [
            CompletionItem(
                label="page.get",
                kind="function",
                detail="page.get(path: str, **kwargs) -> APIResponse",
                insert_text='page.get("${1:/api/endpoint}"${2})',
                documentation="Send GET request to API endpoint",
            ),
            CompletionItem(
                label="page.post",
                kind="function",
                detail="page.post(path: str, data: dict, **kwargs) -> APIResponse",
                insert_text='page.post("${1:/api/endpoint}", data=${2:payload})${3}',
                documentation="Send POST request to API endpoint",
            ),
            CompletionItem(
                label="page.put",
                kind="function",
                detail="page.put(path: str, data: dict, **kwargs) -> APIResponse",
                insert_text='page.put("${1:/api/endpoint}", data=${2:payload})${3}',
                documentation="Send PUT request to API endpoint",
            ),
            CompletionItem(
                label="page.delete",
                kind="function",
                detail="page.delete(path: str, **kwargs) -> APIResponse",
                insert_text='page.delete("${1:/api/endpoint}"${2})',
                documentation="Send DELETE request to API endpoint",
            ),
            CompletionItem(
                label="assert_response",
                kind="function",
                detail="assert_response(response, **kwargs)",
                insert_text="assert_response(response, status_code=${1:200})${2}",
                documentation="Assert response properties",
            ),
        ]
