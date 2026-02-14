"""OpenAPI/Swagger specification importer."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.importers.base import BaseImporter, ImportResult


class OpenAPIImporter(BaseImporter):
    """Import OpenAPI/Swagger specifications (3.0+) into test modules."""

    SUPPORTED_VERSIONS = ["3.0", "3.1", "2.0"]  # 2.0 = Swagger

    def __init__(
        self, output_dir: Optional[Path] = None, service_name: str = "imported"
    ):
        super().__init__(output_dir)
        self.service_name = service_name
        self.spec: Dict = {}
        self.base_url: str = ""

    def import_file(self, file_path: Path) -> ImportResult:
        """Import an OpenAPI specification file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Try JSON first, then YAML
            try:
                self.spec = json.loads(content)
            except json.JSONDecodeError:
                try:
                    import yaml

                    self.spec = yaml.safe_load(content)
                except ImportError:
                    return ImportResult(
                        False, "YAML support requires 'pip install pyyaml'"
                    )
        except FileNotFoundError:
            return ImportResult(False, f"File not found: {file_path}")
        except Exception as e:
            return ImportResult(False, f"Error parsing file: {e}")

        # Validate version
        version = self._get_version()
        if not any(v in version for v in self.SUPPORTED_VERSIONS):
            return ImportResult(
                False,
                f"Unsupported OpenAPI version: {version}. Supported: {self.SUPPORTED_VERSIONS}",
            )

        # Extract base URL
        self.base_url = self._extract_base_url()

        # Extract endpoints
        tests = []
        paths = self.spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "head",
                    "options",
                ]:
                    test_data = self._process_endpoint(path, method, details)
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

        # Generate config
        config = self._generate_config()
        config_file = self.output_dir / "openapi_config.yaml"
        config_file.write_text(config)
        generated_files.append(config_file)

        message = f"Successfully imported {len(tests)} endpoints from OpenAPI spec"
        if self.warnings:
            message += f" with {len(self.warnings)} warnings"

        return ImportResult(
            success=True,
            message=message,
            tests=tests,
            warnings=self.warnings,
        )

    def _get_version(self) -> str:
        """Extract OpenAPI version from spec."""
        # OpenAPI 3.x
        if "openapi" in self.spec:
            return self.spec["openapi"]
        # Swagger 2.0
        elif "swagger" in self.spec:
            return self.spec["swagger"]
        return "unknown"

    def _extract_base_url(self) -> str:
        """Extract base URL from spec."""
        # OpenAPI 3.x
        servers = self.spec.get("servers", [])
        if servers:
            return servers[0].get("url", "")

        # Swagger 2.0
        host = self.spec.get("host", "")
        base_path = self.spec.get("basePath", "")
        scheme = self.spec.get("schemes", ["https"])[0]

        if host:
            return f"{scheme}://{host}{base_path}"

        return "http://localhost:8080"

    def _process_endpoint(
        self, path: str, method: str, details: Dict
    ) -> Optional[Dict]:
        """Process an OpenAPI endpoint."""
        summary = details.get("summary", "")
        description = details.get("description", "")
        operation_id = details.get("operationId", "")

        # Use operationId or generate name
        if operation_id:
            name = operation_id
        elif summary:
            name = summary
        else:
            name = f"{method}_{path.replace('/', '_')}"

        # Extract parameters
        parameters = details.get("parameters", [])
        path_params = []
        query_params = []
        headers = {}
        body = None

        for param in parameters:
            param_in = param.get("in", "")
            param_name = param.get("name", "")

            if param_in == "path":
                path_params.append(param_name)
            elif param_in == "query":
                query_params.append(param_name)
            elif param_in == "header":
                headers[param_name] = param.get("schema", {}).get("example", "")

        # Extract request body
        request_body = details.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                body = self._generate_example_from_schema(schema)

        # Extract responses
        responses = details.get("responses", {})
        expected_status = "200"
        for status in ["200", "201", "204"]:
            if status in responses:
                expected_status = status
                break

        return {
            "name": name,
            "method": method.upper(),
            "path": path,
            "description": description or summary,
            "path_params": path_params,
            "query_params": query_params,
            "headers": headers,
            "body": body,
            "expected_status": expected_status,
        }

    def _generate_example_from_schema(self, schema: Dict) -> Any:
        """Generate example data from JSON schema."""
        schema_type = schema.get("type", "object")

        if schema_type == "object":
            result = {}
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                result[prop_name] = self._generate_example_from_schema(prop_schema)
            return result

        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._generate_example_from_schema(items)]

        elif schema_type == "string":
            return schema.get("example", "string_value")

        elif schema_type == "integer":
            return schema.get("example", 123)

        elif schema_type == "number":
            return schema.get("example", 123.45)

        elif schema_type == "boolean":
            return schema.get("example", True)

        return None

    def generate_code(self, data: Dict) -> str:
        """Generate Python test code from OpenAPI endpoint."""
        method = data["method"].lower()
        path = data["path"]
        path_params = data.get("path_params", [])
        query_params = data.get("query_params", [])
        headers = data.get("headers", {})
        body = data.get("body")
        expected_status = data.get("expected_status", "200")

        lines = [
            f'"""Test: {data["name"]}"""',
            f"# {data.get('description', '')}",
            "",
            "async def run(page):",
            f'    """{data["name"]}"""',
            "",
            "    # Arrange",
        ]

        # Add path parameters
        if path_params:
            for param in path_params:
                lines.append(
                    f'    {param} = "example_{param}"  # TODO: Set actual value'
                )

        # Build URL with path params
        url = path
        if path_params:
            for param in path_params:
                url = url.replace(f"{{{param}}}", f"{{{param}}}")
            lines.append(f'    url = f"{{self.base_url}}{url}"')
        else:
            lines.append(f'    url = "{{self.base_url}}{url}"')

        # Add query parameters
        if query_params:
            lines.append("    # Query parameters")
            for param in query_params:
                lines.append(f'    {param} = "value"  # TODO: Set actual value')
            lines.append(
                f'    url += "?" + "&".join([f"{{p}}={{{{p}}}}" for p in {query_params}])'
            )

        # Add headers
        if headers:
            lines.append("    headers = {")
            for key, value in headers.items():
                lines.append(f'        "{key}": "{value}",')
            lines.append("    }")

        # Add body
        if body:
            lines.append(f"    data = {json.dumps(body, indent=4)}")

        lines.append("")
        lines.append("    # Act")

        # Build request
        args = ["url"]
        if headers:
            args.append("headers=headers")
        if body:
            args.append("data=data")

        lines.append(f"    response = await page.request.{method}({', '.join(args)})")
        lines.append("")
        lines.append("    # Assert")
        lines.append(f"    assert response.status == {expected_status}")
        lines.append("")

        return "\n".join(lines)

    def _generate_page_object(self, tests: List[Dict]) -> str:
        """Generate a Page Object for imported endpoints."""
        lines = [
            f'"""Page Object for {self.service_name} (auto-generated from OpenAPI)."""',
            "",
            "from socialseed_e2e import BasePage",
            "from typing import Optional, Dict, Any",
            "",
            "",
            f"class {self.service_name.title()}Page(BasePage):",
            f'    """Page Object for {self.service_name} API."""',
            "",
            f"    def __init__(self, *args, **kwargs):",
            "        super().__init__(*args, **kwargs)",
            f'        self.base_url = "{self.base_url}"',
            "",
            "    async def check_health(self) -> bool:",
            '        """Check if service is healthy."""',
            '        response = await self.page.request.get(f"{self.base_url}/health")',
            "        return response.status == 200",
            "",
        ]

        # Add methods for each endpoint
        methods_added = set()
        for test in tests:
            name = self._sanitize_name(test.get("name", ""))
            method = test.get("method", "").lower()
            path = test.get("path", "")
            path_params = test.get("path_params", [])

            if name and name not in methods_added:
                methods_added.add(name)

                # Build method signature
                params = ["self"]
                for p in path_params:
                    params.append(f"{p}: str")
                params.append("**kwargs")

                sig = ", ".join(params)

                lines.extend(
                    [
                        f"    async def {name}({sig}):",
                        f'        """{test.get("description", "")}"""',
                    ]
                )

                # Build URL
                url = path
                if path_params:
                    for p in path_params:
                        url = url.replace(f"{{{p}}}", f"{{{p}}}")
                    lines.append(f'        url = f"{{self.base_url}}{url}"')
                else:
                    lines.append(f'        url = f"{{self.base_url}}{path}"')

                lines.append(
                    f"        response = await self.page.request.{method}(url, **kwargs)"
                )
                lines.append("        return response")
                lines.append("")

        return "\n".join(lines)

    def _generate_config(self) -> str:
        """Generate e2e.conf from OpenAPI spec."""
        title = self.spec.get("info", {}).get("title", self.service_name)
        version = self.spec.get("info", {}).get("version", "1.0.0")

        lines = [
            f"# Auto-generated from OpenAPI: {title} v{version}",
            "",
            "environment: imported",
            "",
            "services:",
            f"  {self.service_name}:",
            f"    name: {self.service_name}",
            f"    base_url: {self.base_url}",
            "    timeout: 5000",
            "    health_endpoint: /health",
        ]

        return "\n".join(lines)
