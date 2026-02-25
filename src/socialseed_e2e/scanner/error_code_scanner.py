"""Error code scanner for extracting error codes from source code.

This module provides automatic extraction of error codes and
exception handling patterns from source code.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ErrorCode:
    """Represents an error code."""

    code: str
    http_status: int
    message: str
    description: str = ""
    file_path: Optional[str] = None
    line_number: int = 0


class ErrorCodeScanner:
    """Scans source code to extract error codes."""

    # HTTP status code mappings
    HTTP_STATUS = {
        "BAD_REQUEST": 400,
        "UNAUTHORIZED": 401,
        "FORBIDDEN": 403,
        "NOT_FOUND": 404,
        "CONFLICT": 409,
        "UNPROCESSABLE_ENTITY": 422,
        "TOO_MANY_REQUESTS": 429,
        "INTERNAL_SERVER_ERROR": 500,
        "BAD_GATEWAY": 502,
        "SERVICE_UNAVAILABLE": 503,
        "GATEWAY_TIMEOUT": 504,
    }

    # Exception patterns by language
    LANGUAGE_PATTERNS = {
        "java": {
            "exception_class": r"class\s+(\w+(?:Exception|Error))\s+(?:extends\s+\w+)?",
            "enum_value": r"(\w+)\s*\(\s*(\w+)\s*,\s*(\d+)\s*,\s*\"([^\"]+)\"",
            "http_status": r"HttpStatus\.(\w+)",
            "response_status": r"@ResponseStatus\s*\(\s*HttpStatus\.(\w+)",
        },
        "python": {
            "exception_class": r"class\s+(\w+(?:Exception|Error))\s*[:\(]",
            "enum_value": r"(\w+)\s*=\s*(\w+)\s*\(\s*(\d+\)",
            "http_status": r"status\.(\w+)",
        },
        "typescript": {
            "exception_class": r"class\s+(\w+(?:Exception|Error))\s+",
            "enum_value": r"(\w+)\s*=\s*\{\s*code:\s*['\"](\w+)['\"]",
            "http_status": r"status:\s*(\d+)",
        },
    }

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path)
        self.errors: List[ErrorCode] = []
        self.detected_language: Optional[str] = None

    def detect_language(self) -> str:
        """Detect the programming language."""
        extension_count: Dict[str, int] = {}

        extensions_map = {
            "java": [".java"],
            "python": [".py"],
            "typescript": [".ts", ".tsx"],
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

    def scan(self) -> List[ErrorCode]:
        """Scan the project and extract error codes."""
        language = self.detect_language()

        if language == "unknown":
            return []

        # Find all source files
        source_files = []
        for ext in [".java", ".py", ".ts", ".tsx"]:
            source_files.extend(self.project_path.rglob(f"*{ext}"))

        # Focus on error/exception files
        source_files = [
            f
            for f in source_files
            if any(
                x in str(f).lower()
                for x in ["error", "exception", "handler", "response", "result", "status", "code"]
            )
            and not any(x in str(f) for x in ["test", "Test", "__pycache__", "node_modules"])
        ]

        for file_path in source_files[:30]:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                self._extract_errors_from_file(file_path, content, language)
            except Exception:
                continue

        return self.errors

    def _extract_errors_from_file(
        self,
        file_path: Path,
        content: str,
        language: str,
    ) -> None:
        """Extract errors from a single file."""

        # Extract exception classes
        if language == "java":
            # Find error code enums
            enum_pattern = r"enum\s+(\w+(?:Code|Error|Status))"
            for match in re.finditer(enum_pattern, content):
                enum_name = match.group(1)
                # Look for enum values in the enum body
                enum_body_start = content.find("{", match.end())
                enum_body_end = content.find("}", enum_body_start)
                if enum_body_start > 0 and enum_body_end > enum_body_start:
                    enum_body = content[enum_body_start:enum_body_end]
                    # Extract values like ERROR_NAME(400, "message")
                    for val_match in re.finditer(
                        r"(\w+)\s*\(\s*(\d+)\s*,\s*\"([^\"]+)\"", enum_body
                    ):
                        error = ErrorCode(
                            code=val_match.group(1),
                            http_status=int(val_match.group(2)),
                            message=val_match.group(3),
                            description=f"Error code from {enum_name}",
                            file_path=str(file_path.relative_to(self.project_path)),
                            line_number=content[: match.start()].count("\n") + 1,
                        )
                        self.errors.append(error)

        # Find @ResponseStatus annotations
        for match in re.finditer(r"@ResponseStatus\s*\(\s*(?:HttpStatus\.)?(\w+)", content):
            status = match.group(1)
            if status in self.HTTP_STATUS:
                # Look for exception class before this annotation
                before = content[: match.start()].rfind("class ")
                if before >= 0:
                    class_line = content[before : content.find("\n", before)]
                    class_match = re.search(r"class\s+(\w+)", class_line)
                    if class_match:
                        error = ErrorCode(
                            code=class_match.group(1).upper(),
                            http_status=self.HTTP_STATUS.get(status, 500),
                            message=f"HTTP {status}",
                            description=f"Exception class",
                            file_path=str(file_path.relative_to(self.project_path)),
                            line_number=content[:before].count("\n") + 1,
                        )
                        self.errors.append(error)

        # Add common error codes
        self._add_common_errors()

    def _add_common_errors(self) -> None:
        """Add common HTTP error codes."""
        common_errors = [
            ErrorCode("BAD_REQUEST", 400, "Bad Request", "The request was invalid"),
            ErrorCode("UNAUTHORIZED", 401, "Unauthorized", "Authentication required"),
            ErrorCode("FORBIDDEN", 403, "Forbidden", "Access denied"),
            ErrorCode("NOT_FOUND", 404, "Not Found", "Resource not found"),
            ErrorCode("CONFLICT", 409, "Conflict", "Resource already exists"),
            ErrorCode("UNPROCESSABLE_ENTITY", 422, "Unprocessable Entity", "Validation failed"),
            ErrorCode("TOO_MANY_REQUESTS", 429, "Too Many Requests", "Rate limit exceeded"),
            ErrorCode("INTERNAL_SERVER_ERROR", 500, "Internal Server Error", "Server error"),
            ErrorCode("SERVICE_UNAVAILABLE", 503, "Service Unavailable", "Service down"),
        ]

        for err in common_errors:
            if not any(e.code == err.code for e in self.errors):
                self.errors.append(err)

    def to_markdown(self) -> str:
        """Generate markdown documentation from extracted errors."""

        md = "# Error Codes\n\n"
        md += f"**Total error codes:** {len(self.errors)}\n"
        md += f"**Language detected:** {self.detected_language}\n\n"

        # Group by HTTP status
        by_status: Dict[int, List[ErrorCode]] = {}
        for err in self.errors:
            if err.http_status not in by_status:
                by_status[by_status.__len__() if by_status else 0] = []
            key = err.http_status
            if key not in by_status:
                by_status[key] = []
            by_status[key].append(err)

        # Sort by status code
        for status in sorted(by_status.keys()):
            errors = by_status[status]
            status_name = self._get_status_name(status)
            md += f"## {status} - {status_name}\n\n"

            md += "| Code | Message | Description |\n"
            md += "|------|---------|-------------|\n"
            for err in errors:
                md += f"| `{err.code}` | {err.message} | {err.description} |\n"
            md += "\n"

        return md

    def _get_status_name(self, status: int) -> str:
        """Get HTTP status name."""
        for name, code in self.HTTP_STATUS.items():
            if code == status:
                return name.replace("_", " ")
        return "Unknown"

    def to_json(self) -> Dict[str, Any]:
        """Export errors as JSON-serializable dict."""
        return {
            "total_errors": len(self.errors),
            "language": self.detected_language,
            "errors": [
                {
                    "code": e.code,
                    "http_status": e.http_status,
                    "message": e.message,
                    "description": e.description,
                    "file_path": e.file_path,
                    "line_number": e.line_number,
                }
                for e in self.errors
            ],
        }


def scan_error_codes(project_path: str | Path) -> List[ErrorCode]:
    """Convenience function to scan error codes from a project."""
    scanner = ErrorCodeScanner(project_path)
    return scanner.scan()


def generate_error_codes_doc(project_path: str | Path) -> str:
    """Convenience function to generate markdown documentation."""
    scanner = ErrorCodeScanner(project_path)
    scanner.scan()
    return scanner.to_markdown()
