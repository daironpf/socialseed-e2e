"""AI Code Generation Helper for socialseed-e2e.

This module provides intelligent code generation for AI agents
to automatically create tests from REST controller analysis.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class EndpointInfo:
    """Information about a REST endpoint."""

    method: str
    path: str
    name: str
    request_dto: Optional[str] = None
    response_dto: Optional[str] = None
    requires_auth: bool = False
    path_params: List[str] = None
    query_params: List[str] = None


@dataclass
class DtoField:
    """Field information for DTO generation."""

    name: str
    type_hint: str
    required: bool = True
    validations: List[str] = None


class JavaControllerParser:
    """Parser for Java Spring Boot controllers."""

    @staticmethod
    def parse_controller(java_code: str) -> List[EndpointInfo]:
        """Parse Java controller code and extract endpoints.

        Args:
            java_code: Java source code

        Returns:
            List of EndpointInfo objects
        """
        endpoints = []

        # Even more robust regex for Spring Boot methods
        method_pattern = r'@(?:Post|Get|Put|Delete|Patch)Mapping\s*\(\s*(?:(?:value|path)\s*=\s*)?"([^"]+)"[^)]*\)\s*(?:@[^;{]+\s+)*?(?:public\s+)?\s*(?:ResponseEntity<[^>]+>|[\w<>\?]+)\s+(\w+)\s*\(([^)]*)\)'

        # We need to find the HTTP method separately because we removed it from the capturing group to simplify the regex
        all_mapping_patterns = [
            (r"@PostMapping", "POST"),
            (r"@GetMapping", "GET"),
            (r"@PutMapping", "PUT"),
            (r"@DeleteMapping", "DELETE"),
            (r"@PatchMapping", "PATCH"),
        ]

        for mapping_tag, http_method in all_mapping_patterns:
            pattern = (
                mapping_tag
                + r'\s*\(\s*(?:(?:value|path)\s*=\s*)?"([^"]+)"[^)]*\)\s*(?:@[^;{]+\s+)*?(?:public\s+)?\s*(?:ResponseEntity<[^>]+>|[\w<>\?]+)\s+(\w+)\s*\(([^)]*)\)'
            )
            matches = re.finditer(pattern, java_code, re.MULTILINE | re.DOTALL)
            for match in matches:
                path = match.group(1)
                method_name = match.group(2)
                arguments = match.group(3)

                # Check for @RequestBody
                request_dto = None
                request_body_match = re.search(
                    r"@RequestBody\s+(?:@\w+\s+)*(\w+)\s+(\w+)", arguments
                )
                if request_body_match:
                    request_dto = request_body_match.group(1)

                # Check for authentication requirements
                requires_auth = (
                    "@PreAuthorize" in java_code or "@AuthenticationPrincipal" in java_code
                )

                # Extract path parameters
                path_params = re.findall(r"\{(\w+)\}", path)

                endpoints.append(
                    EndpointInfo(
                        method=http_method,
                        path=path,
                        name=method_name,
                        request_dto=request_dto,
                        requires_auth=requires_auth,
                        path_params=path_params,
                    )
                )

        return endpoints

    @staticmethod
    def parse_dto(java_code: str, dto_name: str) -> List[DtoField]:
        """Parse a Java DTO and extract fields.

        Args:
            java_code: Java DTO source code
            dto_name: Name of the DTO class

        Returns:
            List of DtoField objects
        """
        fields = []

        # Pattern for record fields
        record_pattern = rf"record\s+{dto_name}\s*\(\s*([^)]+)\)"
        record_match = re.search(record_pattern, java_code, re.DOTALL)

        if record_match:
            # Parse record components
            components = record_match.group(1)
            # Split by comma, but be careful with generics
            # Improved regex to capture annotations for each field
            field_defs = re.findall(
                r"((?:@\w+(?:\([^)]*\))?\s*)*)(\w+(?:<[^>]+>)?)\s+(\w+)", components
            )

            for annotations, type_hint, name in field_defs:
                # Map Java types to Python
                py_type = JavaControllerParser._map_java_type(type_hint.strip())

                # Check for @Email specifically in this field's annotations
                if "@Email" in annotations and py_type == "str":
                    py_type = "EmailStr"

                fields.append(DtoField(name=name, type_hint=py_type, required=True))

        return fields

    @staticmethod
    def _map_java_type(java_type: str) -> str:
        """Map Java types to Python type hints."""
        type_mapping = {
            "String": "str",
            "Integer": "int",
            "int": "int",
            "Long": "int",
            "long": "int",
            "Boolean": "bool",
            "boolean": "bool",
            "Double": "float",
            "double": "float",
            "Float": "float",
            "float": "float",
            "UUID": "UUID",
            "Instant": "datetime",
            "LocalDateTime": "datetime",
            "Set": "Set",
            "List": "List",
            "Map": "Dict",
        }

        # Handle generics
        for java, python in type_mapping.items():
            if java_type.startswith(java + "<"):
                inner_type = java_type[java_type.find("<") + 1 : java_type.rfind(">")]
                inner_python = JavaControllerParser._map_java_type(inner_type.strip())
                return f"{python}[{inner_python}]"
            elif java_type == java:
                return python

        return "str"  # Default to str


class PythonCodeGenerator:
    """Generator for Python test code."""

    @staticmethod
    def generate_data_schema(
        endpoints: List[EndpointInfo],
        dto_definitions: Dict[str, List[DtoField]],
        service_name: str,
    ) -> str:
        """Generate data_schema.py content.

        Args:
            endpoints: List of endpoints
            dto_definitions: Dictionary mapping DTO names to fields
            service_name: Name of the service

        Returns:
            Python code for data_schema.py
        """
        lines = [
            '"""Data schema for {} API.'.format(service_name),
            "",
            "Auto-generated from Java controller analysis.",
            '"""',
            "from pydantic import BaseModel, Field, EmailStr",
            "from typing import Optional, Set, List, Dict",
            "from datetime import datetime",
            "from uuid import UUID",
            "",
            "",
            "# =============================================================================",
            "# Request DTOs",
            "# =============================================================================",
            "",
        ]

        # Generate request DTOs
        generated_dtos = set()
        for endpoint in endpoints:
            if endpoint.request_dto and endpoint.request_dto not in generated_dtos:
                dto_name = endpoint.request_dto.replace("DTO", "Request")
                fields = dto_definitions.get(endpoint.request_dto, [])

                lines.append(f"class {dto_name}(BaseModel):")
                lines.append(f'    """{endpoint.request_dto} request."""')
                lines.append('    model_config = {"populate_by_name": True}')
                lines.append("")

                for field in fields:
                    if field.name in [
                        "refresh_token",
                        "access_token",
                        "new_password",
                        "current_password",
                        "user_id",
                        "created_at",
                        "updated_at",
                        "last_login_at",
                    ]:
                        # Use camelCase alias
                        camel_name = PythonCodeGenerator._to_camel_case(field.name)
                        lines.append(f"    {field.name}: {field.type_hint} = Field(")
                        lines.append(f"        ...,")
                        lines.append(f'        alias="{camel_name}",')
                        lines.append(f'        serialization_alias="{camel_name}"')
                        lines.append(f"    )")
                    else:
                        lines.append(f"    {field.name}: {field.type_hint}")

                lines.append("")
                lines.append("")
                generated_dtos.add(endpoint.request_dto)

        # Generate ENDPOINTS constant
        lines.append(
            "# ============================================================================="
        )
        lines.append("# Endpoint Constants")
        lines.append(
            "# ============================================================================="
        )
        lines.append("")
        lines.append("ENDPOINTS = {")

        for endpoint in endpoints:
            key = endpoint.name.lower().replace("get", "get_").replace("post", "create_")
            key = (
                key.replace("put", "update_")
                .replace("delete", "delete_")
                .replace("patch", "patch_")
            )
            key = re.sub(r"([a-z])([A-Z])", r"\1_\2", key).lower()

            lines.append(f'    "{key}": "{endpoint.path}",')

        lines.append("}")
        lines.append("")
        lines.append("")

        # Generate TEST_DATA
        lines.append(
            "# ============================================================================="
        )
        lines.append("# Test Data")
        lines.append(
            "# ============================================================================="
        )
        lines.append("")
        lines.append("TEST_DATA = {")
        lines.append('    "user": {')
        lines.append('        "username": "testuser_e2e",')
        lines.append('        "email": "testuser_e2e@example.com",')
        lines.append('        "password": "TestPassword123!"')
        lines.append("    }")
        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def generate_page_class(
        endpoints: List[EndpointInfo], service_name: str, service_class_name: str
    ) -> str:
        """Generate page class content.

        Args:
            endpoints: List of endpoints
            service_name: Name of the service
            service_class_name: PascalCase service name

        Returns:
            Python code for {service}_page.py
        """
        lines = [
            '"""Page object for {} API.""".format(service_name)',
            "from typing import Optional, Dict, Any",
            "from playwright.sync_api import APIResponse",
            "from socialseed_e2e import BasePage",
            "",
            "from services.{}.data_schema import (".format(service_name),
            "    ENDPOINTS,",
        ]

        # Import request DTOs
        for endpoint in endpoints:
            if endpoint.request_dto:
                dto_name = endpoint.request_dto.replace("DTO", "Request")
                lines.append(f"    {dto_name},")

        lines.append(")")
        lines.append("")
        lines.append("")
        lines.append(f"class {service_class_name}Page(BasePage):")
        lines.append(f'    """Page object for {service_name} service API."""')
        lines.append("")
        lines.append("    def __init__(self, base_url: str, **kwargs):")
        lines.append("        super().__init__(base_url=base_url, **kwargs)")
        lines.append("        self.access_token: Optional[str] = None")
        lines.append("        self.current_user: Optional[Dict[str, Any]] = None")
        lines.append("")
        lines.append("    def _get_headers(self, extra: Optional[Dict] = None) -> Dict[str, str]:")
        lines.append('        """Build headers with authentication if available."""')
        lines.append('        headers = {"Content-Type": "application/json"}')
        lines.append("        if self.access_token:")
        lines.append('            headers["Authorization"] = f"Bearer {self.access_token}"')
        lines.append("        if extra:")
        lines.append("            headers.update(extra)")
        lines.append("        return headers")
        lines.append("")

        # Generate methods for each endpoint
        for endpoint in endpoints:
            method_name = PythonCodeGenerator._generate_method_name(endpoint)
            lines.append(f"    def {method_name}(self, request) -> APIResponse:")
            lines.append(f'        """{endpoint.name} endpoint."""')

            # Handle path parameters
            path = endpoint.path
            if endpoint.path_params:
                for param in endpoint.path_params:
                    path = path.replace(f"{{{param}}}", f"{{{param}}}")
                lines.append(
                    f'        path = ENDPOINTS["{key}"].format({", ".join(endpoint.path_params)})'
                )
                lines.append(
                    f"        response = self.{endpoint.method.lower()}(path, data=request.model_dump(by_alias=True))"
                )
            else:
                key = endpoint.name.lower().replace("get", "get_").replace("post", "create_")
                key = (
                    key.replace("put", "update_")
                    .replace("delete", "delete_")
                    .replace("patch", "patch_")
                )
                key = re.sub(r"([a-z])([A-Z])", r"\1_\2", key).lower()
                lines.append(f"        response = self.{endpoint.method.lower()}(")
                lines.append(f'            ENDPOINTS["{key}"],')
                lines.append(
                    f"            data=request.model_dump(by_alias=True)  # ✅ SIEMPRE by_alias=True"
                )
                lines.append(f"        )")

            lines.append("        return response")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _to_camel_case(snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split("_")
        return components[0] + "".join(x.capitalize() for x in components[1:])

    @staticmethod
    def _generate_method_name(endpoint: EndpointInfo) -> str:
        """Generate Python method name from endpoint info."""
        prefix = "do_"

        # Map HTTP methods to action verbs
        if endpoint.method == "GET":
            if "ById" in endpoint.name or "By" in endpoint.name:
                action = "get"
            else:
                action = "list"
        elif endpoint.method == "POST":
            action = "create"
        elif endpoint.method == "PUT":
            action = "update"
        elif endpoint.method == "PATCH":
            action = "patch"
        elif endpoint.method == "DELETE":
            action = "delete"
        else:
            action = endpoint.method.lower()

        # Extract resource name
        name = endpoint.name
        name = re.sub(r"^(get|post|put|delete|patch)", "", name, flags=re.IGNORECASE)
        name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name).lower()

        return f"{prefix}{action}_{name}".rstrip("_")


class AICodeGenerator:
    """Main class for AI-assisted code generation."""

    @staticmethod
    def analyze_and_generate(
        controller_code: str, dto_codes: Dict[str, str], service_name: str
    ) -> Dict[str, str]:
        """Analyze Java code and generate Python test code.

        Args:
            controller_code: Java controller source code
            dto_codes: Dictionary of DTO name to source code
            service_name: Name of the service

        Returns:
            Dictionary with 'data_schema' and 'page_class' keys
        """
        # Parse controller
        endpoints = JavaControllerParser.parse_controller(controller_code)

        # Parse DTOs
        dto_definitions = {}
        for dto_name, dto_code in dto_codes.items():
            fields = JavaControllerParser.parse_dto(dto_code, dto_name)
            dto_definitions[dto_name] = fields

        # Generate service class name
        service_class_name = "".join(word.capitalize() for word in service_name.split("_"))

        # Generate code
        data_schema = PythonCodeGenerator.generate_data_schema(
            endpoints, dto_definitions, service_name
        )

        page_class = PythonCodeGenerator.generate_page_class(
            endpoints, service_name, service_class_name
        )

        return {
            "data_schema": data_schema,
            "page_class": page_class,
            "endpoints": endpoints,
            "dto_definitions": dto_definitions,
        }
