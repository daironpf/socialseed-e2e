"""Endpoint scanner for extracting REST endpoints from source code.

This module provides automatic extraction of REST API endpoints from
various programming languages and frameworks.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Endpoint:
    """Represents a REST endpoint."""

    path: str
    method: str
    function_name: str
    class_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: int = 0
    auth_required: bool = False
    params: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    response_codes: List[int] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    description: str = ""


class EndpointScanner:
    """Scans source code to extract REST endpoints."""

    # Language-specific patterns
    LANGUAGE_PATTERNS = {
        "java": {
            "annotations": {
                "GET": [r"@GetMapping\(['\"]([^'\"]+)['\"]\)", r"@RequestMapping\(.*method.*GET"],
                "POST": [
                    r"@PostMapping\(['\"]([^'\"]+)['\"]\)",
                    r"@RequestMapping\(.*method.*POST",
                ],
                "PUT": [r"@PutMapping\(['\"]([^'\"]+)['\"]\)", r"@RequestMapping\(.*method.*PUT"],
                "DELETE": [
                    r"@DeleteMapping\(['\"]([^'\"]+)['\"]\)",
                    r"@RequestMapping\(.*method.*DELETE",
                ],
                "PATCH": [r"@PatchMapping\(['\"]([^'\"]+)['\"]\)"],
            },
            "class_pattern": r"@(Rest)?Controller\s*(?:\(\s*['\"]?([^'\"]+)['\"]?\s*\))?",
            "auth_annotations": ["@PreAuthorize", "@Secured", "@RolesAllowed"],
            "param_patterns": [
                (r"@PathVariable\s+(?:\{)?(\w+)(?:\})?\s+(\w+)", "path"),
                (r"@RequestParam\s+(?:\{)?(\w+)(?:\})?\s+(\w+)", "query"),
                (r"@RequestBody\s+(\w+)", "body"),
            ],
            "base_path": r"@RequestMapping\s*\(\s*['\"]?([^'\"\)]+)['\"]?\s*(?:,|\))",
        },
        "python": {
            "annotations": {
                "GET": [
                    r"@(?:app|router)\.get\(['\"]([^'\"]+)['\"]\)",
                    r"@\.get\(['\"]([^'\"]+)['\"]\)",
                ],
                "POST": [
                    r"@(?:app|router)\.post\(['\"]([^'\"]+)['\"]\)",
                    r"@\.post\(['\"]([^'\"]+)['\"]\)",
                ],
                "PUT": [
                    r"@(?:app|router)\.put\(['\"]([^'\"]+)['\"]\)",
                    r"@\.put\(['\"]([^'\"]+)['\"]\)",
                ],
                "DELETE": [
                    r"@(?:app|router)\.delete\(['\"]([^'\"]+)['\"]\)",
                    r"@\.delete\(['\"]([^'\"]+)['\"]\)",
                ],
                "PATCH": [
                    r"@(?:app|router)\.patch\(['\"]([^'\"]+)['\"]\)",
                    r"@\.patch\(['\"]([^'\"]+)['\"]\)",
                ],
            },
            "class_pattern": r"class\s+(\w+)\s*:\s*(?:.*)",
            "auth_annotations": ["@require", "Depends(", "auth", "token_required"],
            "param_patterns": [
                (r"(?:Path|Query|Body)\s*[=:]\s*(\w+)", "mixed"),
            ],
            "base_path": r"(?:app|router)\s*=\s*(?:APIRouter|FastAPI)\([^'\"]*['\"]([^'\"]+)['\"]",
        },
        "javascript": {
            "annotations": {
                "GET": [
                    r"router\.get\s*\(\s*['\"]([^'\"]+)['\"]",
                    r"app\.get\s*\(\s*['\"]([^'\"]+)['\"]",
                ],
                "POST": [
                    r"router\.post\s*\(\s*['\"]([^'\"]+)['\"]",
                    r"app\.post\s*\(\s*['\"]([^'\"]+)['\"]",
                ],
                "PUT": [
                    r"router\.put\s*\(\s*['\"]([^'\"]+)['\"]",
                    r"app\.put\s*\(\s*['\"]([^'\"]+)['\"]",
                ],
                "DELETE": [
                    r"router\.delete\s*\(\s*['\"]([^'\"]+)['\"]",
                    r"app\.delete\s*\(\s*['\"]([^'\"]+)['\"]",
                ],
            },
            "class_pattern": r"(?:class|const|let)\s+(\w+)\s*=.*Router",
            "auth_annotations": ["auth", "verifyToken", "requireAuth"],
            "param_patterns": [
                (r"req\.params\.(\w+)", "path"),
                (r"req\.query\.(\w+)", "query"),
                (r"req\.body", "body"),
            ],
            "base_path": r"(?:app|router)\.use\s*\(\s*['\"]([^'\"]+)['\"]",
        },
        "typescript": {
            "annotations": {
                "GET": [
                    r"@(?:Get|Get)\s*\(\s*['\"]([^'\"]+)['\"]\)",
                    r"@(\w+)\s*\(\s*['\"]([^'\"]+)['\"]\)",
                ],
                "POST": [r"@(?:Post|Post)\s*\(\s*['\"]([^'\"]+)['\"]\)"],
                "PUT": [r"@(?:Put|Put)\s*\(\s*['\"]([^'\"]+)['\"]\)"],
                "DELETE": [r"@(?:Delete|Delete)\s*\(\s*['\"]([^'\"]+)['\"]\)"],
            },
            "class_pattern": r"@Controller\s*(?:\(\s*['\"]?([^'\"]+)['\"]?\s*\))?|@Controller\s*\(?\s*['\"]?([^'\"]+)['\"]?\s*\)?",
            "auth_annotations": ["@UseGuards", "@Roles", "@Authorize"],
            "param_patterns": [
                (r"@Param\s*\(\s*['\"]?(\w+)['\"]?\)\s+(\w+)", "path"),
                (r"@Query\s*\(\s*['\"]?(\w+)['\"]?\)\s+(\w+)", "query"),
                (r"@Body\s*\(\s*\)\s+(\w+)", "body"),
            ],
            "base_path": r"@Controller\s*\(\s*['\"]?([^'\"\)]+)['\"]?\s*(?:,|\))",
        },
        "go": {
            "annotations": {
                "GET": [r"\.GET\s*\(\s*['\"]([^'\"]+)['\"]"],
                "POST": [r"\.POST\s*\(\s*['\"]([^'\"]+)['\"]"],
                "PUT": [r"\.PUT\s*\(\s*['\"]([^'\"]+)['\"]"],
                "DELETE": [r"\.DELETE\s*\(\s*['\"]([^'\"]+)['\"]"],
            },
            "class_pattern": r"(?:func|handle)\s+(\w+)",
            "auth_annotations": ["auth", "middleware", "Require"],
            "param_patterns": [
                (r"c\.Param\s*\(\s*'(\\w+)'\s*\)", "path"),
                (r"c\.Query\s*\(\s*'(\\w+)'\s*\)", "query"),
            ],
            "base_path": r"Group\s*\(\s*'([^']+)'",
        },
    }

    # File extensions to scan
    FILE_EXTENSIONS = {
        "java": [".java"],
        "python": [".py"],
        "javascript": [".js", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "go": [".go"],
    }

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path)
        self.endpoints: List[Endpoint] = []
        self.detected_language: Optional[str] = None
        self.base_paths: List[str] = []

    def detect_language(self) -> str:
        """Detect the programming language of the project."""
        extension_count: Dict[str, int] = {}

        for lang, extensions in self.FILE_EXTENSIONS.items():
            for ext in extensions:
                count = len(list(self.project_path.rglob(f"*{ext}")))
                if count > 0:
                    extension_count[lang] = count

        if extension_count:
            self.detected_language = max(extension_count, key=extension_count.get)
            return self.detected_language

        return "unknown"

    def scan(self) -> List[Endpoint]:
        """Scan the project and extract all endpoints."""
        language = self.detect_language()

        if language == "unknown":
            return []

        patterns = self.LANGUAGE_PATTERNS.get(language, {})

        # Find all source files
        source_files = []
        for ext in self.FILE_EXTENSIONS.get(language, []):
            source_files.extend(self.project_path.rglob(f"*{ext}"))

        # Skip test files and generated files
        source_files = [
            f
            for f in source_files
            if not any(
                x in str(f)
                for x in ["test", "Test", "__pycache__", "node_modules", "target", "dist", "build"]
            )
        ]

        for file_path in source_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                self._extract_endpoints_from_file(file_path, content, patterns, language)
            except Exception:
                continue

        return self.endpoints

    def _extract_endpoints_from_file(
        self,
        file_path: Path,
        content: str,
        patterns: Dict[str, Any],
        language: str,
    ) -> None:
        """Extract endpoints from a single file."""
        lines = content.split("\n")

        # Find class-level base path (for Java/TS controllers)
        base_path = ""
        for line in lines:
            base_match = re.search(patterns.get("base_path", ""), line)
            if base_match:
                base_path = base_match.group(1)
                if base_path not in self.base_paths:
                    self.base_paths.append(base_path)

        # Find class name
        class_name = None
        class_match = re.search(patterns.get("class_pattern", ""), content)
        if class_match:
            class_name = class_match.group(1) if class_match.lastindex else None

        # Extract endpoints for each HTTP method
        for method, method_patterns in patterns.get("annotations", {}).items():
            for pattern in method_patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    # Find line number
                    line_num = content[: match.start()].count("\n") + 1

                    # Extract path
                    path = match.group(1) if match.lastindex else ""

                    if not path:
                        continue

                    # Clean up path
                    path = path.strip()

                    # Combine with base path
                    full_path = f"{base_path}{path}".replace("//", "/")

                    # Find function name (look for def/func before the annotation)
                    before_match = content[: match.start()].split("\n")
                    func_name = "anonymous"
                    for i in range(len(before_match) - 1, -1, -1):
                        if "def " in before_match[i] or "func " in before_match[i]:
                            func_match = re.search(r"(?:def|func)\s+(\w+)", before_match[i])
                            if func_match:
                                func_name = func_match.group(1)
                            break

                    # Check for auth requirements
                    auth_required = any(
                        auth in content[max(0, match.start() - 500) : match.end() + 500]
                        for auth in patterns.get("auth_annotations", [])
                    )

                    endpoint = Endpoint(
                        path=full_path,
                        method=method.upper(),
                        function_name=func_name,
                        class_name=class_name,
                        file_path=str(file_path.relative_to(self.project_path)),
                        line_number=line_num,
                        auth_required=auth_required,
                    )

                    self.endpoints.append(endpoint)

    def to_markdown(self) -> str:
        """Generate markdown documentation from extracted endpoints."""
        if not self.endpoints:
            return "# Endpoints\n\nNo endpoints found.\n"

        # Group by base path
        by_path: Dict[str, List[Endpoint]] = {}
        for ep in self.endpoints:
            base = ep.path.split("/")[1] if "/" in ep.path else ""
            if base not in by_path:
                by_path[base] = []
            by_path[base].append(ep)

        md = "# API Endpoints\n\n"
        md += f"**Total endpoints:** {len(self.endpoints)}\n"
        md += f"**Language detected:** {self.detected_language}\n\n"

        # Group by method
        by_method: Dict[str, List[Endpoint]] = {}
        for ep in self.endpoints:
            if ep.method not in by_method:
                by_method[ep.method] = []
            by_method[ep.method].append(ep)

        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            if method not in by_method:
                continue

            md += f"## {method}\n\n"

            for ep in by_method[method]:
                auth_badge = " 🔒" if ep.auth_required else ""
                md += f"### {ep.path}{auth_badge}\n\n"
                md += f"**Method:** `{ep.method}`\n\n"

                if ep.class_name:
                    md += f"**Controller:** `{ep.class_name}`\n\n"

                md += f"**Handler:** `{ep.function_name}`\n\n"

                if ep.file_path:
                    md += f"**File:** `{ep.file_path}:{ep.line_number}`\n\n"

                md += "---\n\n"

        return md

    def to_json(self) -> Dict[str, Any]:
        """Export endpoints as JSON-serializable dict."""
        return {
            "total_endpoints": len(self.endpoints),
            "language": self.detected_language,
            "base_paths": self.base_paths,
            "endpoints": [
                {
                    "path": ep.path,
                    "method": ep.method,
                    "function_name": ep.function_name,
                    "class_name": ep.class_name,
                    "file_path": ep.file_path,
                    "line_number": ep.line_number,
                    "auth_required": ep.auth_required,
                }
                for ep in self.endpoints
            ],
        }


def scan_endpoints(project_path: str | Path) -> List[Endpoint]:
    """Convenience function to scan endpoints from a project."""
    scanner = EndpointScanner(project_path)
    return scanner.scan()


def generate_endpoints_doc(project_path: str | Path) -> str:
    """Convenience function to generate markdown documentation."""
    scanner = EndpointScanner(project_path)
    scanner.scan()
    return scanner.to_markdown()
