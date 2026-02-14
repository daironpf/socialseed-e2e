"""Postman Collection and Environment importer."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.importers.base import BaseImporter, ImportResult


class PostmanImporter(BaseImporter):
    """Import Postman Collections (v2.1) into SocialSeed E2E tests."""

    SUPPORTED_VERSIONS = ["2.1", "2.0"]

    def __init__(
        self, output_dir: Optional[Path] = None, service_name: str = "imported"
    ):
        super().__init__(output_dir)
        self.service_name = service_name
        self.variables: Dict[str, str] = {}

    def import_file(self, file_path: Path) -> ImportResult:
        """Import a Postman collection file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                collection = json.load(f)
        except json.JSONDecodeError as e:
            return ImportResult(False, f"Invalid JSON: {e}")
        except FileNotFoundError:
            return ImportResult(False, f"File not found: {file_path}")

        # Validate collection
        info = collection.get("info", {})
        schema = info.get("schema", "")

        if "v2.1" not in schema and "v2.0" not in schema:
            return ImportResult(
                False,
                f"Unsupported Postman collection version. Supported: {self.SUPPORTED_VERSIONS}",
            )

        # Extract variables from collection
        self.variables = self._extract_variables(collection)

        # Process items
        tests = []
        items = collection.get("item", [])

        for item in items:
            test_data = self._process_item(item)
            if test_data:
                tests.append(test_data)

        # Generate code
        generated_files = []
        for i, test in enumerate(tests):
            code = self.generate_code(test)
            test_name = test.get("name", f"test_{i + 1}")
            file_path = self._write_test_file(self._sanitize_name(test_name), code)
            generated_files.append(file_path)

        # Generate Page Object
        if tests:
            page_object = self._generate_page_object(tests)
            page_file = self.output_dir / f"{self.service_name}_page.py"
            page_file.write_text(page_object)
            generated_files.append(page_file)

        message = f"Successfully imported {len(tests)} requests from Postman collection"
        if self.warnings:
            message += f" with {len(self.warnings)} warnings"

        return ImportResult(
            success=True,
            message=message,
            tests=tests,
            warnings=self.warnings,
        )

    def _extract_variables(self, collection: Dict) -> Dict[str, str]:
        """Extract variables from collection."""
        variables = {}
        for var in collection.get("variable", []):
            key = var.get("key", "")
            value = var.get("value", "")
            if key:
                variables[key] = value
        return variables

    def _process_item(self, item: Dict, folder: str = "") -> Optional[Dict]:
        """Process a Postman item (request or folder)."""
        # If it's a folder, process children
        if "item" in item:
            folder_name = item.get("name", folder)
            for sub_item in item["item"]:
                self._process_item(sub_item, folder_name)
            return None

        # It's a request
        request = item.get("request", {})
        if isinstance(request, str):
            return None

        name = item.get("name", "Unnamed Request")
        method = request.get("method", "GET")
        url = self._extract_url(request.get("url", {}))
        headers = self._extract_headers(request.get("header", []))
        body = self._extract_body(request.get("body", {}))
        tests = self._extract_tests(item.get("event", []))

        return {
            "name": name,
            "method": method,
            "url": url,
            "headers": headers,
            "body": body,
            "tests": tests,
            "folder": folder,
        }

    def _extract_url(self, url: Any) -> str:
        """Extract URL from Postman URL object or string."""
        if isinstance(url, str):
            return self._replace_variables(url)

        if isinstance(url, dict):
            protocol = url.get("protocol", "https")
            host = url.get("host", [])
            if isinstance(host, list):
                host = ".".join(host)
            path = url.get("path", [])
            if isinstance(path, list):
                path = "/".join(path)

            return self._replace_variables(f"{protocol}://{host}/{path}")

        return ""

    def _extract_headers(self, headers: List) -> Dict[str, str]:
        """Extract headers from Postman header list."""
        result = {}
        for header in headers:
            if isinstance(header, dict):
                key = header.get("key", "")
                value = header.get("value", "")
                if key and not header.get("disabled", False):
                    result[key] = self._replace_variables(value)
        return result

    def _extract_body(self, body: Dict) -> Optional[Dict]:
        """Extract body from Postman body object."""
        if not body:
            return None

        mode = body.get("mode", "")

        if mode == "raw":
            raw_body = body.get("raw", "")
            try:
                parsed = json.loads(raw_body)
                return {"type": "json", "data": parsed}
            except json.JSONDecodeError:
                return {"type": "raw", "data": raw_body}

        elif mode in ["formdata", "urlencoded"]:
            data = body.get(mode, [])
            result = {}
            for item in data:
                if isinstance(item, dict) and not item.get("disabled", False):
                    key = item.get("key", "")
                    value = item.get("value", "")
                    if key:
                        result[key] = value
            return {"type": "form", "data": result}

        return None

    def _extract_tests(self, events: List) -> List[str]:
        """Extract test scripts from Postman events."""
        tests = []
        for event in events:
            if isinstance(event, dict) and event.get("listen") == "test":
                script = event.get("script", {})
                if isinstance(script, dict):
                    exec_list = script.get("exec", [])
                    if isinstance(exec_list, list):
                        tests.extend(exec_list)
        return tests

    def _replace_variables(self, text: str) -> str:
        """Replace Postman variables {{var}}."""
        return re.sub(r"\{\{(.*?)\}\}", lambda m: f"{{{m.group(1).strip()}}}", text)

    def generate_code(self, data: Dict) -> str:
        """Generate Python test code from Postman request."""
        method = data["method"].lower()
        url = data["url"]
        headers = data.get("headers", {})
        body = data.get("body")

        lines = [
            f'"""Test: {data["name"]}"""',
            "",
            "async def run(page):",
            f'    """{data["name"]}"""',
            "",
            "    # Arrange",
        ]

        if headers:
            lines.append("    headers = {")
            for k, v in headers.items():
                lines.append(f'        "{k}": "{v}",')
            lines.append("    }")

        if body:
            if body["type"] == "json":
                lines.append(f"    data = {json.dumps(body['data'], indent=4)}")
            else:
                lines.append(f"    data = {repr(body['data'])}")

        lines.extend(
            [
                "",
                "    # Act",
            ]
        )

        args = [f'"{url}"']
        if headers:
            args.append("headers=headers")
        if body:
            args.append("data=data")

        lines.append(f"    response = await page.request.{method}({', '.join(args)})")
        lines.extend(
            [
                "",
                "    # Assert",
                "    assert response.status == 200",
                "",
            ]
        )

        return "\n".join(lines)

    def _generate_page_object(self, tests: List[Dict]) -> str:
        """Generate a Page Object for imported tests."""
        lines = [
            f'"""Page Object for {self.service_name} (auto-generated from Postman)."""',
            "",
            "from socialseed_e2e import BasePage",
            "",
            "",
            f"class {self.service_name.title()}Page(BasePage):",
            f'    """Page Object for {self.service_name} service."""',
            "",
            "    async def check_health(self):",
            '        """Check if service is healthy."""',
            '        response = await self.page.request.get(f"{self.base_url}/health")',
            "        return response.status == 200",
            "",
        ]

        methods_added = set()
        for test in tests:
            name = test.get("name", "").lower().replace(" ", "_")
            method = test.get("method", "").lower()

            if name and name not in methods_added:
                methods_added.add(name)
                lines.extend(
                    [
                        f"    async def {name}(self, **kwargs):",
                        f'        """{test.get("name", "")}"""',
                        f"        response = await self.page.request.{method}(f'{{self.base_url}}/path', **kwargs)",
                        "        return response",
                        "",
                    ]
                )

        return "\n".join(lines)


class PostmanEnvironmentImporter(BaseImporter):
    """Import Postman Environments into framework config."""

    def import_file(self, file_path: Path) -> ImportResult:
        """Import a Postman environment file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                env = json.load(f)
        except json.JSONDecodeError as e:
            return ImportResult(False, f"Invalid JSON: {e}")
        except FileNotFoundError:
            return ImportResult(False, f"File not found: {file_path}")

        variables = {}
        for var in env.get("values", []):
            key = var.get("key", "")
            value = var.get("value", "")
            if key:
                variables[key] = value

        config = self._generate_config(env.get("name", "imported"), variables)
        config_path = self.output_dir / "imported_config.yaml"
        config_path.write_text(config)

        return ImportResult(
            success=True,
            message=f"Imported {len(variables)} environment variables",
            tests=[{"config_file": str(config_path)}],
            warnings=self.warnings,
        )

    def _generate_config(self, name: str, variables: Dict) -> str:
        """Generate YAML config from environment."""
        lines = [
            f"# Auto-generated from Postman Environment: {name}",
            "",
            "environment: imported",
            "",
            "services:",
            f"  {name}:",
            f"    name: {name}",
        ]

        if "base_url" in variables:
            lines.append(f"    base_url: {variables['base_url']}")

        lines.extend(
            [
                "    timeout: 5000",
                "",
                "# Environment variables:",
            ]
        )

        for key, value in variables.items():
            lines.append(f"#   {key}: {value}")

        return "\n".join(lines)

    def generate_code(self, data: Dict) -> str:
        """Not used for environment importer."""
        return ""
