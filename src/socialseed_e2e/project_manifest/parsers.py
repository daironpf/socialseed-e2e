"""Language parsers for extracting project information from source code.

This module provides parsers for multiple programming languages to extract:
- Endpoints and HTTP methods
- DTO schemas and validation rules
- Configuration (ports, environment variables)
- Service dependencies
"""

import ast
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple, Type

from socialseed_e2e.project_manifest.models import (
    DtoField,
    DtoSchema,
    EndpointInfo,
    EndpointParameter,
    EnvironmentVariable,
    FileMetadata,
    HttpMethod,
    PortConfig,
    ServiceDependency,
    ValidationRule,
)


@dataclass
class ParseResult:
    """Result from parsing a file."""

    endpoints: List[EndpointInfo]
    dto_schemas: List[DtoSchema]
    ports: List[PortConfig]
    env_vars: List[EnvironmentVariable]
    dependencies: List[ServiceDependency]
    file_metadata: FileMetadata


class BaseParser(ABC):
    """Base class for language-specific parsers."""

    LANGUAGE: str = ""
    FILE_EXTENSIONS: List[str] = []

    def __init__(self, project_root: Path):
        """Initialize parser with project root.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if parser can handle this file
        """
        pass

    @abstractmethod
    def parse_file(self, file_path: Path, content: Optional[str] = None) -> ParseResult:
        """Parse a single file and extract information.

        Args:
            file_path: Path to the file to parse
            content: Optional file content (if already read)

        Returns:
            ParseResult with extracted information
        """
        pass

    def _compute_checksum(self, content: str) -> str:
        """Compute MD5 checksum of content."""
        return hashlib.md5(content.encode()).hexdigest()

    def _get_file_metadata(self, file_path: Path, content: str) -> FileMetadata:
        """Generate file metadata."""
        import datetime

        stat = file_path.stat()
        return FileMetadata(
            path=str(file_path.relative_to(self.project_root)),
            checksum=self._compute_checksum(content),
            last_modified=datetime.datetime.fromtimestamp(stat.st_mtime),
            language=self.LANGUAGE,
        )


class PythonParser(BaseParser):
    """Parser for Python projects (Flask, FastAPI, Django)."""

    LANGUAGE = "python"
    FILE_EXTENSIONS = [".py"]

    # Patterns for endpoint detection in different frameworks
    FASTAPI_PATTERNS = [
        (r'@(?:app|router)\.get\s*\(\s*["\']([^"\']+)["\']', HttpMethod.GET),
        (r'@(?:app|router)\.post\s*\(\s*["\']([^"\']+)["\']', HttpMethod.POST),
        (r'@(?:app|router)\.put\s*\(\s*["\']([^"\']+)["\']', HttpMethod.PUT),
        (r'@(?:app|router)\.delete\s*\(\s*["\']([^"\']+)["\']', HttpMethod.DELETE),
        (r'@(?:app|router)\.patch\s*\(\s*["\']([^"\']+)["\']', HttpMethod.PATCH),
    ]

    FLASK_PATTERNS = [
        (
            r'@(?:app|bp|blueprint)\.route\s*\(\s*["\']([^"\']+)["\']'
            r"[^)]*methods\s*=\s*\[([^\]]+)\]",
            None,
        ),
    ]

    # Pydantic validation patterns
    FIELD_VALIDATION_PATTERNS = {
        "min_length": r"min_length\s*=\s*(\d+)",
        "max_length": r"max_length\s*=\s*(\d+)",
        "gt": r"gt\s*=\s*(\d+)",
        "lt": r"lt\s*=\s*(\d+)",
        "ge": r"ge\s*=\s*(\d+)",
        "le": r"le\s*=\s*(\d+)",
        "regex": r'pattern\s*=\s*["\']([^"\']+)["\']',
    }

    def can_parse(self, file_path: Path) -> bool:
        """Check if file is a Python file."""
        return file_path.suffix == ".py"

    def parse_file(self, file_path: Path, content: Optional[str] = None) -> ParseResult:
        """Parse a Python file for endpoints, DTOs, and configuration."""
        if content is None:
            content = file_path.read_text(encoding="utf-8")

        file_metadata = self._get_file_metadata(file_path, content)

        endpoints = []
        dto_schemas = []
        ports = []
        env_vars = []
        dependencies = []

        # Detect framework
        framework = self._detect_framework(content)

        # Parse endpoints based on framework
        if framework in ["fastapi", "flask"]:
            endpoints = self._parse_endpoints(content, str(file_path))

        # Parse DTOs (Pydantic models or dataclasses)
        dto_schemas = self._parse_dtos(content, str(file_path))

        # Parse configuration
        ports, env_vars = self._parse_config(content, str(file_path))

        # Parse dependencies
        dependencies = self._parse_dependencies(content, str(file_path))

        return ParseResult(
            endpoints=endpoints,
            dto_schemas=dto_schemas,
            ports=ports,
            env_vars=env_vars,
            dependencies=dependencies,
            file_metadata=file_metadata,
        )

    def _detect_framework(self, content: str) -> Optional[str]:
        """Detect which web framework is being used."""
        if "from fastapi" in content or "import fastapi" in content:
            return "fastapi"
        elif "from flask" in content or "import flask" in content:
            return "flask"
        elif "from django" in content or "import django" in content:
            return "django"
        return None

    def _parse_endpoints(self, content: str, file_path: str) -> List[EndpointInfo]:
        """Parse HTTP endpoints from Python code."""
        endpoints = []

        # Try FastAPI patterns
        for pattern, method in self.FASTAPI_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                path = match.group(1)
                # Find function name
                func_start = match.end()
                func_match = re.search(
                    r"\s*async\s+def\s+(\w+)|\s*def\s+(\w+)",
                    content[func_start : func_start + 200],
                )
                if func_match:
                    func_name = func_match.group(1) or func_match.group(2)
                    line_num = content[: match.start()].count("\n") + 1

                    endpoints.append(
                        EndpointInfo(
                            name=func_name,
                            method=method,
                            path=path,
                            full_path=path,
                            file_path=file_path,
                            line_number=line_num,
                        )
                    )

        return endpoints

    def _parse_dtos(self, content: str, file_path: str) -> List[DtoSchema]:
        """Parse Pydantic models and dataclasses from Python code."""
        dtos = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a Pydantic model or dataclass
                    is_pydantic = any(
                        base.attr == "BaseModel"
                        if isinstance(base, ast.Attribute)
                        else base.id == "BaseModel"
                        for base in node.bases
                        if isinstance(base, (ast.Name, ast.Attribute))
                    )

                    is_dataclass = any(
                        dec.id == "dataclass"
                        for dec in node.decorator_list
                        if isinstance(dec, ast.Name)
                    )

                    if is_pydantic or is_dataclass:
                        fields = self._extract_class_fields(node, content)
                        base_classes = [
                            base.id if isinstance(base, ast.Name) else ast.dump(base)
                            for base in node.bases
                        ]

                        dtos.append(
                            DtoSchema(
                                name=node.name,
                                fields=fields,
                                file_path=file_path,
                                line_number=node.lineno,
                                base_classes=base_classes,
                            )
                        )

        except SyntaxError:
            pass

        return dtos

    def _extract_class_fields(self, node: ast.ClassDef, content: str) -> List[DtoField]:
        """Extract fields from a class definition."""
        fields = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                field_type = self._get_type_hint(item.annotation)
                required = item.value is None
                default_value = None
                validations = []
                alias = None

                if not required and item.value:
                    default_value = self._get_default_value(item.value)

                # Check for Field() with validations
                if item.value and isinstance(item.value, ast.Call):
                    validations, alias = self._extract_validations(item.value, content)

                fields.append(
                    DtoField(
                        name=field_name,
                        type=field_type,
                        required=required,
                        default_value=default_value,
                        validations=validations,
                        alias=alias,
                    )
                )

        return fields

    def _get_type_hint(self, annotation: ast.AST) -> str:
        """Convert AST annotation to type hint string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            value = self._get_type_hint(annotation.value)
            slice_val = self._get_type_hint(annotation.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.Attribute):
            return annotation.attr
        elif isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            left = self._get_type_hint(annotation.left)
            right = self._get_type_hint(annotation.right)
            return f"{left} | {right}"
        return "Any"

    def _get_default_value(self, value: ast.AST) -> Any:
        """Extract default value from AST node."""
        if isinstance(value, ast.Constant):
            return value.value
        elif isinstance(value, ast.NameConstant):
            return value.value
        elif isinstance(value, ast.Name):
            return value.id
        return None

    def _extract_validations(
        self, call: ast.Call, content: str
    ) -> Tuple[List[ValidationRule], Optional[str]]:
        """Extract validation rules from Field() call."""
        validations = []
        alias = None

        for keyword in call.keywords:
            if keyword.arg == "alias" and isinstance(keyword.value, ast.Constant):
                alias = keyword.value.value
            elif keyword.arg in ["min_length", "max_length", "gt", "lt", "ge", "le"]:
                if isinstance(keyword.value, ast.Constant):
                    validations.append(
                        ValidationRule(rule_type=keyword.arg, value=keyword.value.value)
                    )
            elif keyword.arg == "pattern":
                if isinstance(keyword.value, ast.Constant):
                    validations.append(
                        ValidationRule(rule_type="regex", value=keyword.value.value)
                    )

        return validations, alias

    def _parse_config(
        self, content: str, file_path: str
    ) -> Tuple[List[PortConfig], List[EnvironmentVariable]]:
        """Parse configuration (ports and environment variables)."""
        ports = []
        env_vars = []

        # Look for port configurations
        port_patterns = [
            r"port\s*=\s*(\d+)",
            r"PORT\s*=\s*(\d+)",
            r'["\']PORT["\']\s*:\s*(\d+)',
            r"--port\s+(\d+)",
            r"app\.run\s*\([^)]*port\s*=\s*(\d+)",
        ]

        for pattern in port_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    port = int(match.group(1))
                    if 1 <= port <= 65535:
                        ports.append(
                            PortConfig(
                                port=port,
                                protocol="http",
                                description=f"Detected from {file_path}",
                            )
                        )
                except (ValueError, IndexError):
                    pass

        # Look for environment variables
        env_patterns = [
            r'os\.getenv\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']\s*,?\s*([^)]*)\)',
            r'os\.environ\.get\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']\s*,?\s*([^)]*)\)',
            r'os\.environ\[["\']([A-Z_][A-Z0-9_]*)["\']\]',
        ]

        for pattern in env_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                var_name = match.group(1)
                default_value = None
                required = True

                if len(match.groups()) > 1:
                    default_part = match.group(2).strip()
                    if default_part:
                        required = False
                        # Extract default value
                        default_match = re.search(r'["\']([^"\']+)["\']', default_part)
                        if default_match:
                            default_value = default_match.group(1)

                # Avoid duplicates
                if not any(v.name == var_name for v in env_vars):
                    env_vars.append(
                        EnvironmentVariable(
                            name=var_name,
                            default_value=default_value,
                            required=required,
                        )
                    )

        return ports, env_vars

    def _parse_dependencies(
        self, content: str, file_path: str
    ) -> List[ServiceDependency]:
        """Parse service dependencies."""
        dependencies = []

        # Look for HTTP client calls to other services
        http_patterns = [
            r'requests\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'httpx\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'aiohttp\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        ]

        for pattern in http_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                method_str = match.group(1).upper()
                url = match.group(2)

                # Try to extract service name from URL
                service_match = re.search(r"https?://([^/:]+)", url)
                if service_match:
                    service_name = service_match.group(1)
                    dependencies.append(
                        ServiceDependency(
                            service_name=service_name,
                            method=HttpMethod(method_str)
                            if method_str in ["GET", "POST", "PUT", "DELETE", "PATCH"]
                            else None,
                            description=f"HTTP call from {file_path}",
                        )
                    )

        return dependencies


class JavaParser(BaseParser):
    """Parser for Java projects (Spring Boot)."""

    LANGUAGE = "java"
    FILE_EXTENSIONS = [".java"]

    # Spring Boot endpoint patterns
    ENDPOINT_PATTERNS = [
        (r'@GetMapping\s*\(\s*["\']?([^"\']*)["\']?\s*\)', HttpMethod.GET),
        (r'@PostMapping\s*\(\s*["\']?([^"\']*)["\']?\s*\)', HttpMethod.POST),
        (r'@PutMapping\s*\(\s*["\']?([^"\']*)["\']?\s*\)', HttpMethod.PUT),
        (r'@DeleteMapping\s*\(\s*["\']?([^"\']*)["\']?\s*\)', HttpMethod.DELETE),
        (r'@PatchMapping\s*\(\s*["\']?([^"\']*)["\']?\s*\)', HttpMethod.PATCH),
        (
            r'@RequestMapping\s*\(\s*["\']?([^"\']*)["\']?[^)]*method\s*=\s*RequestMethod\.(\w+)',
            None,
        ),
    ]

    # Validation annotations
    VALIDATION_ANNOTATIONS = {
        "@NotNull": ("required", True),
        "@NotEmpty": ("required", True),
        "@NotBlank": ("required", True),
        "@Email": ("regex", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
        "@Size": [
            ("min_length", r"min\s*=\s*(\d+)"),
            ("max_length", r"max\s*=\s*(\d+)"),
        ],
        "@Min": ("ge", r"(\d+)"),
        "@Max": ("le", r"(\d+)"),
        "@Pattern": ("regex", r'regexp\s*=\s*["\']([^"\']+)["\']'),
    }

    def can_parse(self, file_path: Path) -> bool:
        """Check if file is a Java file."""
        return file_path.suffix == ".java"

    def parse_file(self, file_path: Path, content: Optional[str] = None) -> ParseResult:
        """Parse a Java file for endpoints, DTOs, and configuration."""
        if content is None:
            content = file_path.read_text(encoding="utf-8")

        file_metadata = self._get_file_metadata(file_path, content)

        endpoints = self._parse_endpoints(content, str(file_path))
        dto_schemas = self._parse_dtos(content, str(file_path))
        ports = self._parse_ports(content, str(file_path))
        env_vars = self._parse_env_vars(content, str(file_path))
        dependencies = self._parse_dependencies(content, str(file_path))

        return ParseResult(
            endpoints=endpoints,
            dto_schemas=dto_schemas,
            ports=ports,
            env_vars=env_vars,
            dependencies=dependencies,
            file_metadata=file_metadata,
        )

    def _parse_endpoints(self, content: str, file_path: str) -> List[EndpointInfo]:
        """Parse Spring Boot endpoints from Java code."""
        endpoints = []

        # Get class-level @RequestMapping
        class_mapping = re.search(
            r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']\s*\)', content
        )
        base_path = class_mapping.group(1) if class_mapping else ""

        for pattern, method in self.ENDPOINT_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                path = match.group(1) or "/"
                full_path = base_path + path

                # Determine HTTP method
                http_method = method
                if http_method is None and len(match.groups()) > 1:
                    method_str = match.group(2)
                    http_method = (
                        HttpMethod(method_str.upper()) if method_str else HttpMethod.GET
                    )

                # Find method name after the annotation
                remaining = content[match.end() :]
                method_match = re.search(
                    r"(?:public\s+)?(?:ResponseEntity<[^>]+>|\w+)\s+(\w+)\s*\([^)]*\)",
                    remaining[:500],
                )
                method_name = method_match.group(1) if method_match else "unknown"
                line_num = content[: match.start()].count("\n") + 1

                # Check for @RequestBody and @ResponseBody
                next_section = remaining[:1000]
                request_dto = None
                response_dto = None

                request_body_match = re.search(
                    r"@RequestBody\s+(?:\w+\s+)*(\w+)", next_section
                )
                if request_body_match:
                    request_dto = request_body_match.group(1)

                response_body_match = re.search(r"ResponseEntity<(\w+)", next_section)
                if response_body_match:
                    response_dto = response_body_match.group(1)

                # Check authentication
                requires_auth = (
                    "@PreAuthorize" in next_section or "@Secured" in next_section
                )

                # Extract path parameters
                path_params = re.findall(r"\{(\w+)\}", path)
                parameters = [
                    EndpointParameter(
                        name=p, param_type="string", location="path", required=True
                    )
                    for p in path_params
                ]

                endpoints.append(
                    EndpointInfo(
                        name=method_name,
                        method=http_method or HttpMethod.GET,
                        path=path,
                        full_path=full_path,
                        parameters=parameters,
                        request_dto=request_dto,
                        response_dto=response_dto,
                        requires_auth=requires_auth,
                        file_path=file_path,
                        line_number=line_num,
                    )
                )

        return endpoints

    def _parse_dtos(self, content: str, file_path: str) -> List[DtoSchema]:
        """Parse Java DTOs/records from code."""
        dtos = []

        # Parse records
        record_pattern = r"(?:public\s+)?record\s+(\w+)\s*\(\s*([^)]+)\)"
        record_matches = re.finditer(record_pattern, content, re.DOTALL)

        for match in record_matches:
            record_name = match.group(1)
            components = match.group(2)
            line_num = content[: match.start()].count("\n") + 1

            fields = self._parse_java_fields(components)

            dtos.append(
                DtoSchema(
                    name=record_name,
                    fields=fields,
                    file_path=file_path,
                    line_number=line_num,
                    base_classes=["java.lang.Record"],
                )
            )

        # Parse classes with getters (traditional DTOs)
        class_pattern = r"(?:public\s+)?class\s+(\w+)\s*[^{]*\{"
        class_matches = re.finditer(class_pattern, content)

        for match in class_matches:
            class_name = match.group(1)
            if class_name in ["Builder", "Factory", "Config"]:
                continue

            # Find class body
            start = match.end()
            brace_count = 1
            end = start
            while brace_count > 0 and end < len(content):
                if content[end] == "{":
                    brace_count += 1
                elif content[end] == "}":
                    brace_count -= 1
                end += 1

            class_body = content[start:end]
            fields = self._parse_java_class_fields(class_body)

            if fields:
                line_num = content[: match.start()].count("\n") + 1
                dtos.append(
                    DtoSchema(
                        name=class_name,
                        fields=fields,
                        file_path=file_path,
                        line_number=line_num,
                        base_classes=["java.lang.Object"],
                    )
                )

        return dtos

    def _parse_java_fields(self, components: str) -> List[DtoField]:
        """Parse fields from Java record components."""
        fields = []

        # Split by comma but respect generics
        field_defs = re.findall(
            r"((?:@\w+(?:\([^)]*\))?\s+)*)(\w+(?:<[^>]+>)?)\s+(\w+)",
            components,
        )

        for annotations, type_hint, name in field_defs:
            validations = self._extract_java_validations(annotations)
            py_type = self._map_java_type(type_hint.strip())

            # Check for @Email
            if "@Email" in annotations and py_type == "str":
                py_type = "EmailStr"

            fields.append(
                DtoField(
                    name=name,
                    type=py_type,
                    required="@NotNull" in annotations or "@NotEmpty" in annotations,
                    validations=validations,
                )
            )

        return fields

    def _parse_java_class_fields(self, class_body: str) -> List[DtoField]:
        """Parse fields from traditional Java class."""
        fields = []

        # Match private fields with optional annotations
        field_pattern = (
            r"((?:@\w+(?:\([^)]*\))?\s+)*)(?:private\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*;"
        )
        field_matches = re.finditer(field_pattern, class_body)

        for match in field_matches:
            annotations = match.group(1)
            type_hint = match.group(2)
            name = match.group(3)

            validations = self._extract_java_validations(annotations)
            py_type = self._map_java_type(type_hint.strip())

            fields.append(
                DtoField(
                    name=name,
                    type=py_type,
                    required="@NotNull" in annotations,
                    validations=validations,
                )
            )

        return fields

    def _extract_java_validations(self, annotations: str) -> List[ValidationRule]:
        """Extract validation rules from Java annotations."""
        validations = []

        for annotation, rules in self.VALIDATION_ANNOTATIONS.items():
            if annotation in annotations:
                if isinstance(rules, list):
                    for rule_type, pattern in rules:
                        match = re.search(pattern, annotations)
                        if match:
                            try:
                                value = (
                                    int(match.group(1))
                                    if match.group(1).isdigit()
                                    else match.group(1)
                                )
                                validations.append(
                                    ValidationRule(rule_type=rule_type, value=value)
                                )
                            except (ValueError, IndexError):
                                pass
                elif isinstance(rules, tuple):
                    rule_type, value = rules
                    if isinstance(value, str) and value.startswith(r"\'"):
                        match = re.search(value, annotations)
                        if match:
                            value = match.group(1)
                    validations.append(ValidationRule(rule_type=rule_type, value=value))

        return validations

    def _map_java_type(self, java_type: str) -> str:
        """Map Java types to Python types."""
        type_mapping = {
            "String": "str",
            "Integer": "int",
            "int": "int",
            "Long": "int",
            "Boolean": "bool",
            "boolean": "bool",
            "Double": "float",
            "double": "float",
            "Float": "float",
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
                inner_start = java_type.find("<") + 1
                inner_end = java_type.rfind(">")
                inner_type = java_type[inner_start:inner_end]
                inner_python = self._map_java_type(inner_type.strip())
                return f"{python}[{inner_python}]"
            elif java_type == java:
                return python

        return "str"

    def _parse_ports(self, content: str, file_path: str) -> List[PortConfig]:
        """Parse port configurations."""
        ports = []

        # application.properties or application.yml style
        port_patterns = [
            r"server\.port\s*=\s*(\d+)",
            r'["\']?server\.port["\']?\s*:\s*(\d+)',
        ]

        for pattern in port_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                try:
                    port = int(match.group(1))
                    if 1 <= port <= 65535:
                        ports.append(
                            PortConfig(
                                port=port,
                                protocol="http",
                                description="Server port",
                            )
                        )
                except (ValueError, IndexError):
                    pass

        return ports

    def _parse_env_vars(
        self, content: str, file_path: str
    ) -> List[EnvironmentVariable]:
        """Parse environment variable usage."""
        env_vars = []

        # Spring Boot @Value annotations
        value_pattern = r'@Value\s*\(\s*["\']\$\{([^}:]+)(?::([^}]+))?\}["\']\s*\)'
        matches = re.finditer(value_pattern, content)

        for match in matches:
            var_name = match.group(1)
            default_value = match.group(2)
            required = default_value is None

            if not any(v.name == var_name for v in env_vars):
                env_vars.append(
                    EnvironmentVariable(
                        name=var_name,
                        default_value=default_value,
                        required=required,
                    )
                )

        # System.getenv calls
        getenv_pattern = r'System\.getenv\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']\s*\)'
        getenv_matches = re.finditer(getenv_pattern, content)

        for match in getenv_matches:
            var_name = match.group(1)
            if not any(v.name == var_name for v in env_vars):
                env_vars.append(EnvironmentVariable(name=var_name, required=True))

        return env_vars

    def _parse_dependencies(
        self, content: str, file_path: str
    ) -> List[ServiceDependency]:
        """Parse service dependencies."""
        dependencies = []

        # Look for RestTemplate, WebClient, or Feign client usage
        rest_patterns = [
            r"(?:restTemplate|webClient)\."
            r'(?:getForObject|postForObject|exchange)\s*\(\s*["\']([^"\']+)["\']',
            r'@FeignClient\s*\(\s*["\']([^"\']+)["\']',
        ]

        for pattern in rest_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                url_or_name = match.group(1)

                # Try to extract service name
                service_match = re.search(r"https?://([^/:]+)", url_or_name)
                service_name = service_match.group(1) if service_match else url_or_name

                dependencies.append(
                    ServiceDependency(
                        service_name=service_name,
                        description=f"Detected from {file_path}",
                    )
                )

        return dependencies


class NodeParser(BaseParser):
    """Parser for Node.js/JavaScript projects (Express, NestJS, Fastify)."""

    LANGUAGE = "javascript"
    FILE_EXTENSIONS = [".js", ".ts", ".jsx", ".tsx"]

    # Express endpoint patterns
    EXPRESS_PATTERNS = [
        (r'(?:app|router)\.(get)\s*\(\s*["\']([^"\']+)["\']', HttpMethod.GET),
        (r'(?:app|router)\.(post)\s*\(\s*["\']([^"\']+)["\']', HttpMethod.POST),
        (r'(?:app|router)\.(put)\s*\(\s*["\']([^"\']+)["\']', HttpMethod.PUT),
        (r'(?:app|router)\.(delete)\s*\(\s*["\']([^"\']+)["\']', HttpMethod.DELETE),
        (r'(?:app|router)\.(patch)\s*\(\s*["\']([^"\']+)["\']', HttpMethod.PATCH),
    ]

    def can_parse(self, file_path: Path) -> bool:
        """Check if file is a JavaScript/TypeScript file."""
        return file_path.suffix in self.FILE_EXTENSIONS

    def parse_file(self, file_path: Path, content: Optional[str] = None) -> ParseResult:
        """Parse a Node.js file."""
        if content is None:
            content = file_path.read_text(encoding="utf-8")

        file_metadata = self._get_file_metadata(file_path, content)

        endpoints = self._parse_endpoints(content, str(file_path))
        dto_schemas = self._parse_dtos(content, str(file_path))
        ports = self._parse_ports(content, str(file_path))
        env_vars = self._parse_env_vars(content, str(file_path))
        dependencies = self._parse_dependencies(content, str(file_path))

        return ParseResult(
            endpoints=endpoints,
            dto_schemas=dto_schemas,
            ports=ports,
            env_vars=env_vars,
            dependencies=dependencies,
            file_metadata=file_metadata,
        )

    def _parse_endpoints(self, content: str, file_path: str) -> List[EndpointInfo]:
        """Parse Express endpoints."""
        endpoints = []

        for pattern, method in self.EXPRESS_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                path = match.group(2)
                http_method = method or HttpMethod.GET
                line_num = content[: match.start()].count("\n") + 1

                endpoints.append(
                    EndpointInfo(
                        name=f"handler_{len(endpoints)}",
                        method=http_method,
                        path=path,
                        full_path=path,
                        file_path=file_path,
                        line_number=line_num,
                    )
                )

        return endpoints

    def _parse_dtos(self, content: str, file_path: str) -> List[DtoSchema]:
        """Parse JavaScript/TypeScript interfaces and types."""
        dtos = []

        # TypeScript interface pattern
        interface_pattern = r"(?:export\s+)?interface\s+(\w+)\s*\{([^}]+)\}"
        matches = re.finditer(interface_pattern, content, re.DOTALL)

        for match in matches:
            interface_name = match.group(1)
            body = match.group(2)
            line_num = content[: match.start()].count("\n") + 1

            fields = self._parse_ts_fields(body)

            dtos.append(
                DtoSchema(
                    name=interface_name,
                    fields=fields,
                    file_path=file_path,
                    line_number=line_num,
                )
            )

        return dtos

    def _parse_ts_fields(self, body: str) -> List[DtoField]:
        """Parse TypeScript interface fields."""
        fields = []

        # Match field definitions
        field_pattern = r"(\w+)\??\s*:\s*([^;]+);"
        field_matches = re.finditer(field_pattern, body)

        for match in field_matches:
            name = match.group(1)
            type_hint = match.group(2).strip()
            required = "?" not in match.group(0)

            py_type = self._map_ts_type(type_hint)

            fields.append(
                DtoField(
                    name=name,
                    type=py_type,
                    required=required,
                )
            )

        return fields

    def _map_ts_type(self, ts_type: str) -> str:
        """Map TypeScript types to Python types."""
        type_mapping = {
            "string": "str",
            "number": "float",
            "boolean": "bool",
            "any": "Any",
            "unknown": "Any",
            "void": "None",
            "null": "None",
            "undefined": "None",
            "Date": "datetime",
            "string[]": "List[str]",
            "number[]": "List[float]",
            "boolean[]": "List[bool]",
            "any[]": "List[Any]",
        }

        # Handle arrays
        if ts_type.endswith("[]"):
            base_type = ts_type[:-2]
            return f"List[{self._map_ts_type(base_type)}]"

        # Handle generics
        if "<" in ts_type and ">" in ts_type:
            base = ts_type[: ts_type.find("<")]
            inner = ts_type[ts_type.find("<") + 1 : ts_type.rfind(">")]
            if base == "Array":
                return f"List[{self._map_ts_type(inner)}]"
            elif base in ["Record", "Map"]:
                return "Dict"

        return type_mapping.get(ts_type, "Any")

    def _parse_ports(self, content: str, file_path: str) -> List[PortConfig]:
        """Parse port configurations."""
        ports = []

        port_patterns = [
            r"app\.listen\s*\(\s*(\d+)",
            r'["\']PORT["\']\s*:\s*(\d+)',
            r"PORT\s*=\s*(\d+)",
            r"process\.env\.PORT\s*\|\|\s*(\d+)",
        ]

        for pattern in port_patterns:
            try:
                matches = re.finditer(pattern, content)
                for match in matches:
                    try:
                        # Check if group 1 exists and is not None
                        if match.lastindex is None or match.lastindex < 1:
                            continue
                        port_str = match.group(1)
                        if port_str is None or not port_str.strip():
                            continue
                        port = int(port_str)
                        if 1 <= port <= 65535:
                            ports.append(
                                PortConfig(
                                    port=port,
                                    protocol="http",
                                    description=f"Detected from {file_path}",
                                )
                            )
                    except (ValueError, IndexError, TypeError):
                        # Skip invalid port values
                        continue
            except re.error:
                # Skip invalid regex patterns
                continue

        return ports

    def _parse_env_vars(
        self, content: str, file_path: str
    ) -> List[EnvironmentVariable]:
        """Parse environment variable usage."""
        env_vars = []

        # process.env patterns
        env_patterns = [
            r"process\.env\.([A-Z_][A-Z0-9_]*)",
            r'process\.env\[["\']([A-Z_][A-Z0-9_]*)["\']\]',
        ]

        for pattern in env_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                var_name = match.group(1)
                if not any(v.name == var_name for v in env_vars):
                    env_vars.append(EnvironmentVariable(name=var_name, required=True))

        return env_vars

    def _parse_dependencies(
        self, content: str, file_path: str
    ) -> List[ServiceDependency]:
        """Parse service dependencies."""
        dependencies = []

        # HTTP client calls
        http_patterns = [
            r'axios\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'fetch\s*\(\s*["\']([^"\']+)["\']',
            r'http\.request\s*\(\s*.*?hostname\s*:\s*["\']([^"\']+)["\']',
        ]

        for pattern in http_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    method_str = match.group(1).upper()
                    url = match.group(2)
                else:
                    method_str = "GET"
                    url = match.group(1)

                service_match = re.search(r"https?://([^/:]+)", url)
                if service_match:
                    service_name = service_match.group(1)
                    dependencies.append(
                        ServiceDependency(
                            service_name=service_name,
                            method=HttpMethod(method_str)
                            if method_str in ["GET", "POST", "PUT", "DELETE", "PATCH"]
                            else None,
                        )
                    )

        return dependencies


class ParserRegistry:
    """Registry for language parsers."""

    def __init__(self):
        """Initialize with default parsers."""
        self._parsers: List[Type[BaseParser]] = []
        self.register_defaults()

    def register(self, parser_class: Type[BaseParser]) -> None:
        """Register a parser class."""
        self._parsers.append(parser_class)

    def register_defaults(self) -> None:
        """Register default parsers."""
        self.register(PythonParser)
        self.register(JavaParser)
        self.register(NodeParser)

    def get_parser(self, file_path: Path, project_root: Path) -> Optional[BaseParser]:
        """Get appropriate parser for a file."""
        for parser_class in self._parsers:
            parser = parser_class(project_root)
            if parser.can_parse(file_path):
                return parser
        return None

    def get_parser_for_language(
        self, language: str, project_root: Path
    ) -> Optional[BaseParser]:
        """Get parser by language name."""
        for parser_class in self._parsers:
            if parser_class.LANGUAGE == language.lower():
                return parser_class(project_root)
        return None


# Global registry instance
parser_registry = ParserRegistry()
