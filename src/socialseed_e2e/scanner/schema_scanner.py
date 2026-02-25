"""Schema scanner for extracting DTOs and models from source code.

This module provides automatic extraction of data schemas from
various programming languages and frameworks.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SchemaField:
    """Represents a field in a schema."""

    name: str
    field_type: str
    required: bool = False
    description: str = ""
    validation: List[str] = field(default_factory=list)
    default: Optional[str] = None


@dataclass
class Schema:
    """Represents a data schema/DTO."""

    name: str
    fields: List[SchemaField] = field(default_factory=list)
    file_path: Optional[str] = None
    line_number: int = 0
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    enum_values: List[str] = field(default_factory=list)
    is_enum: bool = False


class SchemaScanner:
    """Scans source code to extract DTOs and models."""

    LANGUAGE_PATTERNS = {
        "java": {
            "class_pattern": r"(?:public\s+)?(?:class|interface|enum|record)\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?",
            "field_patterns": [
                r"(?:private|public|protected)\s+(\w+(?:<[^>]+>)?(?:\[\])?)\s+(\w+)\s*(?:=\s*([^;]+))?;",
                r"@JsonProperty\s*\(\s*['\"](\w+)['\"]\s*\)\s*(?:\w+)\s+(\w+)",  # For records
            ],
            "annotation_field": r"@(\w+)\s+(?:\([^)]*\))?\s*(?:private|public|protected)?\s*\w+",
            "request_body": ["@RequestBody"],
            "validations": {
                "@NotNull": "not null",
                "@NotEmpty": "not empty",
                "@NotBlank": "not blank",
                "@Size": "size validation",
                "@Min": "minimum value",
                "@Max": "maximum value",
                "@Email": "valid email",
                "@Pattern": "pattern match",
                "@Length": "length validation",
            },
            "enum_value": r"(\w+)(?:\s*=\s*[^,]+)?(?:,\s*|$)",
        },
        "python": {
            "class_pattern": r"class\s+(\w+)(?:\(([^)]+)\))?:",
            "field_patterns": [
                r"(\w+):\s*(\w+(?:\[[^\]]+\])?(?:\|[^=]+)?(?:\s*=\s*[^,]+)?)",
            ],
            "annotation_field": r"Field\([^)]+\)",
            "request_body": ["Body", "Form"],
            "validations": {
                "Field(...)": "field validation",
                "validator": "custom validation",
            },
            "enum_value": r"(\w+)(?:\s*=\s*[^,]+)?(?:,\s*|$)",
        },
        "typescript": {
            "class_pattern": r"(?:export\s+)?(?:class|interface|type|enum)\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?",
            "field_patterns": [
                r"(\w+)(?:\??):\s*(\w+(?:\[[^\]]+\])?(?:\|[^;]+)?(?:;|\s*=)?)",
            ],
            "annotation_field": r"@(?:Prop|Column|...)",
            "request_body": ["@Body", "@Param"],
            "validations": {
                "@IsNotEmpty": "not empty",
                "@IsEmail": "valid email",
                "@Min": "minimum",
                "@Max": "maximum",
            },
            "enum_value": r"(\w+)(?:\s*=\s*[^,]+)?(?:,\s*|$)",
        },
        "javascript": {
            "class_pattern": r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?",
            "field_patterns": [
                r"(?:async\s+)?(?:\w+)\s*\([^)]*\)\s*\{[^}]*(?:return|this\.(\w+)\s*=)",
            ],
            "request_body": ["req.body"],
            "validations": {},
            "enum_value": r"(\w+):\s*['\"]?(\w+)['\"]?(?:,\s*|$)",
        },
    }

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path)
        self.schemas: List[Schema] = []
        self.detected_language: Optional[str] = None

    def detect_language(self) -> str:
        """Detect the programming language."""
        extension_count: Dict[str, int] = {}

        extensions_map = {
            "java": [".java"],
            "python": [".py"],
            "typescript": [".ts", ".tsx"],
            "javascript": [".js", ".mjs"],
        }

        for lang, extensions in extensions_map.items():
            for ext in extensions:
                count = len(list(self.project_path.rglob(f"*{ext}")))
                if count > 0:
                    extension_count[lang] = count

        if extension_count:
            self.detected_language = max(extension_count, key=extension_count.get)
            return self.detected_language

        return "unknown"

    def scan(self) -> List[Schema]:
        """Scan the project and extract all schemas."""
        language = self.detect_language()

        if language == "unknown":
            return []

        patterns = self.LANGUAGE_PATTERNS.get(language, {})

        # Find all source files (focus on dto, model, entity, schema directories)
        source_files = []
        for ext in [".java", ".py", ".ts", ".tsx", ".js"]:
            # Prioritize files in dto, model, entity, schema folders
            source_files.extend(self.project_path.rglob(f"*{ext}"))

        # Focus on relevant files
        source_files = [
            f
            for f in source_files
            if any(
                x in str(f).lower()
                for x in [
                    "dto",
                    "model",
                    "entity",
                    "schema",
                    "request",
                    "response",
                    "domain",
                    "vo",
                    "pojo",
                    "data",
                ]
            )
            and not any(
                x in str(f).lower() for x in ["test", "Test", "__pycache__", "node_modules"]
            )
        ]

        # If no focused files, scan all
        if not source_files:
            for ext in [".java", ".py", ".ts", ".tsx", ".js"]:
                source_files.extend(self.project_path.rglob(f"*{ext}"))
            source_files = [
                f
                for f in source_files
                if not any(
                    x in str(f) for x in ["test", "Test", "__pycache__", "node_modules", "target"]
                )
            ]

        for file_path in source_files[:50]:  # Limit files
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                self._extract_schemas_from_file(file_path, content, patterns, language)
            except Exception:
                continue

        return self.schemas

    def _extract_schemas_from_file(
        self,
        file_path: Path,
        content: str,
        patterns: Dict[str, Any],
        language: str,
    ) -> None:
        """Extract schemas from a single file."""
        lines = content.split("\n")

        # Check if it's an enum
        is_enum = "enum " in content[:200]

        # Find class/interface declarations
        class_matches = list(re.finditer(patterns.get("class_pattern", ""), content, re.MULTILINE))

        # Also find Java records
        record_matches = list(re.finditer(r"record\s+(\w+)\s*\(([^)]+)\)", content, re.MULTILINE))

        for match in record_matches:
            schema_name = match.group(1)
            params_str = match.group(2)

            # Parse record parameters
            fields = []
            # Split by comma but handle nested generics
            param_parts = []
            depth = 0
            current = ""
            for char in params_str:
                if char in "<(":
                    depth += 1
                    current += char
                elif char in ">)":
                    depth -= 1
                    current += char
                elif char == "," and depth == 0:
                    param_parts.append(current.strip())
                    current = ""
                else:
                    current += char
            if current.strip():
                param_parts.append(current.strip())

            for param in param_parts:
                # Extract type and name
                parts = param.strip().split()
                if len(parts) >= 2:
                    field_type = parts[0]
                    field_name = parts[-1]

                    sf = SchemaField(
                        name=field_name,
                        field_type=field_type,
                        required=True,
                    )
                    fields.append(sf)

            schema = Schema(
                name=schema_name,
                fields=fields,
                file_path=str(file_path.relative_to(self.project_path)),
                line_number=content[: match.start()].count("\n") + 1,
            )
            self.schemas.append(schema)

        for match in class_matches:
            schema_name = match.group(1)
            extends = match.group(2) if match.lastindex >= 2 else None
            implements_str = match.group(3) if match.lastindex >= 3 else None

            if is_enum:
                # Extract enum values
                enum_section = re.search(r"\{([^}]+)\}", content[match.start() :])
                if enum_section:
                    values = re.findall(r"(\w+)(?:\s*=\s*[^,]+)?", enum_section.group(1))
                    schema = Schema(
                        name=schema_name,
                        is_enum=True,
                        enum_values=values,
                        file_path=str(file_path.relative_to(self.project_path)),
                        line_number=content[: match.start()].count("\n") + 1,
                    )
                    self.schemas.append(schema)
                continue

            # Extract fields
            fields = []
            file_content = content[match.start() :]

            # Look for field declarations
            field_patterns = patterns.get("field_patterns", [])
            for field_pattern in field_patterns:
                for field_match in re.finditer(field_pattern, file_content):
                    if len(field_match.groups()) >= 2:
                        field_type = field_match.group(1)
                        field_name = field_match.group(2)

                        # Skip methods
                        if "(" in field_type:
                            continue

                        # Check for validation annotations
                        validations = []
                        for val_key, val_desc in patterns.get("validations", {}).items():
                            if (
                                val_key
                                in file_content[
                                    max(0, field_match.start() - 200) : field_match.end() + 100
                                ]
                            ):
                                validations.append(val_desc)

                        # Check if required (no default, or has NotNull)
                        required = "=" not in field_match.group(
                            0
                        ) or "NotNull" in field_match.group(0)

                        sf = SchemaField(
                            name=field_name,
                            field_type=field_type,
                            required=required,
                            validation=validations,
                        )
                        fields.append(sf)

            if fields or extends or implements_str:
                schema = Schema(
                    name=schema_name,
                    fields=fields,
                    extends=extends,
                    implements=[x.strip() for x in implements_str.split(",")]
                    if implements_str
                    else [],
                    file_path=str(file_path.relative_to(self.project_path)),
                    line_number=content[: match.start()].count("\n") + 1,
                )
                self.schemas.append(schema)

    def to_markdown(self) -> str:
        """Generate markdown documentation from extracted schemas."""
        if not self.schemas:
            return "# Data Schemas\n\nNo schemas found.\n"

        md = "# Data Schemas\n\n"
        md += f"**Total schemas:** {len(self.schemas)}\n"
        md += f"**Language detected:** {self.detected_language}\n\n"

        # Group enums first
        enums = [s for s in self.schemas if s.is_enum]
        classes = [s for s in self.schemas if not s.is_enum]

        if enums:
            md += "## Enums\n\n"
            for schema in enums:
                md += f"### {schema.name}\n\n"
                md += f"**File:** `{schema.file_path}:{schema.line_number}`\n\n"
                md += "| Value | Description |\n"
                md += "|-------|-------------|\n"
                for val in schema.enum_values:
                    md += f"| `{val}` | - |\n"
                md += "\n---\n\n"

        if classes:
            md += "## Classes/Interfaces\n\n"
            for schema in classes:
                md += f"### {schema.name}\n\n"

                if schema.extends:
                    md += f"**Extends:** `{schema.extends}`\n\n"

                if schema.implements:
                    md += f"**Implements:** {', '.join([f'`{x}`' for x in schema.implements])}\n\n"

                md += f"**File:** `{schema.file_path}:{schema.line_number}`\n\n"

                if schema.fields:
                    md += "| Field | Type | Required | Validation |\n"
                    md += "|-------|------|----------|------------|\n"
                    for field in schema.fields:
                        req = "✅" if field.required else "❌"
                        vals = ", ".join(field.validation) if field.validation else "-"
                        md += f"| `{field.name}` | `{field.field_type}` | {req} | {vals} |\n"
                    md += "\n"

                md += "---\n\n"

        return md

    def to_json(self) -> Dict[str, Any]:
        """Export schemas as JSON-serializable dict."""
        return {
            "total_schemas": len(self.schemas),
            "language": self.detected_language,
            "schemas": [
                {
                    "name": s.name,
                    "is_enum": s.is_enum,
                    "enum_values": s.enum_values,
                    "extends": s.extends,
                    "implements": s.implements,
                    "fields": [
                        {
                            "name": f.name,
                            "type": f.field_type,
                            "required": f.required,
                            "validation": f.validation,
                        }
                        for f in s.fields
                    ],
                    "file_path": s.file_path,
                    "line_number": s.line_number,
                }
                for s in self.schemas
            ],
        }


def scan_schemas(project_path: str | Path) -> List[Schema]:
    """Convenience function to scan schemas from a project."""
    scanner = SchemaScanner(project_path)
    return scanner.scan()


def generate_schemas_doc(project_path: str | Path) -> str:
    """Convenience function to generate markdown documentation."""
    scanner = SchemaScanner(project_path)
    scanner.scan()
    return scanner.to_markdown()
