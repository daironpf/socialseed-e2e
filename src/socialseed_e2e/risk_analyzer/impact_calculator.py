"""Impact Calculator - Calculates endpoint impact from code changes.

This module provides functionality to trace which endpoints are affected
by code changes and calculate the impact level.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from socialseed_e2e.risk_analyzer.change_analyzer import ChangedFile


@dataclass
class ImpactResult:
    """Result of impact analysis for an endpoint."""

    endpoint_path: str
    http_method: str
    impact_score: int  # 0-100
    affected_files: List[str] = field(default_factory=list)
    impact_factors: Dict[str, int] = field(default_factory=dict)
    direct_change: bool = False
    dependencies: List[str] = field(default_factory=list)


class ImpactCalculator:
    """Calculates the impact of code changes on API endpoints."""

    # Common dependency patterns
    IMPORT_PATTERNS = [
        r"^from\s+([\w.]+)\s+import",
        r"^import\s+([\w.]+)",
    ]

    # Endpoint definition patterns by framework
    ENDPOINT_PATTERNS = {
        "fastapi": [
            r"@app\.(get|post|put|delete|patch)\(['\"]([^'\"]+)",
            r"@router\.(get|post|put|delete|patch)\(['\"]([^'\"]+)",
        ],
        "flask": [
            r"@app\.route\(['\"]([^'\"]+)",
            r"@.*\.route\(['\"]([^'\"]+)",
        ],
        "spring": [
            r"@(Get|Post|Put|Delete|Patch)Mapping\(['\"]([^'\"]+)",
            r"@RequestMapping\(['\"]([^'\"]+)",
        ],
        "express": [
            r"\.(get|post|put|delete|patch)\(['\"]([^'\"]+)",
            r"router\.(get|post|put|delete|patch)\(['\"]([^'\"]+)",
        ],
    }

    def __init__(self, project_path: Optional[str] = None):
        """Initialize the impact calculator.

        Args:
            project_path: Path to project root. Uses current directory if None.
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.endpoint_map: Dict[
            str, Dict
        ] = {}  # endpoint -> {file, method, dependencies}
        self.dependency_graph: Dict[
            str, Set[str]
        ] = {}  # file -> set of files it depends on

    def discover_endpoints(self) -> Dict[str, Dict]:
        """Discover all API endpoints in the project.

        Returns:
            Dictionary mapping endpoint paths to their metadata
        """
        self.endpoint_map = {}

        # Scan Python files
        for py_file in self.project_path.rglob("*.py"):
            endpoints = self._extract_endpoints_from_file(py_file)
            for endpoint, metadata in endpoints.items():
                self.endpoint_map[endpoint] = metadata

        # Scan Java files
        for java_file in self.project_path.rglob("*.java"):
            endpoints = self._extract_endpoints_from_java(java_file)
            for endpoint, metadata in endpoints.items():
                self.endpoint_map[endpoint] = metadata

        # Scan JavaScript/TypeScript files
        for js_file in self.project_path.rglob("*.js"):
            endpoints = self._extract_endpoints_from_js(js_file)
            for endpoint, metadata in endpoints.items():
                self.endpoint_map[endpoint] = metadata

        for ts_file in self.project_path.rglob("*.ts"):
            endpoints = self._extract_endpoints_from_js(ts_file)
            for endpoint, metadata in endpoints.items():
                self.endpoint_map[endpoint] = metadata

        return self.endpoint_map

    def _extract_endpoints_from_file(self, file_path: Path) -> Dict[str, Dict]:
        """Extract endpoints from a Python file."""
        endpoints = {}

        try:
            content = file_path.read_text()

            # Try FastAPI patterns
            for pattern in self.ENDPOINT_PATTERNS["fastapi"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    method = (match.group(1) if match.groups() else "get").upper()
                    path = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    endpoint_key = f"{method} {path}"
                    endpoints[endpoint_key] = {
                        "file": str(file_path.relative_to(self.project_path)),
                        "method": method,
                        "path": path,
                        "framework": "fastapi",
                        "dependencies": self._extract_dependencies(content),
                    }

            # Try Flask patterns
            for pattern in self.ENDPOINT_PATTERNS["flask"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    path = match.group(1)
                    # Look for methods in decorator or function
                    method = self._extract_http_method(content, match.start())
                    endpoint_key = f"{method} {path}"
                    endpoints[endpoint_key] = {
                        "file": str(file_path.relative_to(self.project_path)),
                        "method": method,
                        "path": path,
                        "framework": "flask",
                        "dependencies": self._extract_dependencies(content),
                    }

        except Exception:
            pass

        return endpoints

    def _extract_endpoints_from_java(self, file_path: Path) -> Dict[str, Dict]:
        """Extract endpoints from a Java file."""
        endpoints = {}

        try:
            content = file_path.read_text()

            for pattern in self.ENDPOINT_PATTERNS["spring"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    method = match.group(1).upper() if match.group(1) else "GET"
                    path = match.group(2)
                    endpoint_key = f"{method} {path}"
                    endpoints[endpoint_key] = {
                        "file": str(file_path.relative_to(self.project_path)),
                        "method": method,
                        "path": path,
                        "framework": "spring",
                        "dependencies": [],
                    }

        except Exception:
            pass

        return endpoints

    def _extract_endpoints_from_js(self, file_path: Path) -> Dict[str, Dict]:
        """Extract endpoints from a JavaScript/TypeScript file."""
        endpoints = {}

        try:
            content = file_path.read_text()

            for pattern in self.ENDPOINT_PATTERNS["express"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    endpoint_key = f"{method} {path}"
                    endpoints[endpoint_key] = {
                        "file": str(file_path.relative_to(self.project_path)),
                        "method": method,
                        "path": path,
                        "framework": "express",
                        "dependencies": self._extract_js_dependencies(content),
                    }

        except Exception:
            pass

        return endpoints

    def _extract_http_method(self, content: str, position: int) -> str:
        """Extract HTTP method from Flask decorator."""
        # Look for methods= parameter in the decorator
        snippet = content[max(0, position - 200) : position + 200]

        methods_match = re.search(r"methods\s*=\s*\[([^\]]+)\]", snippet)
        if methods_match:
            methods_str = methods_match.group(1)
            # Extract first method
            first_method = re.search(r"['\"](\w+)['\"]", methods_str)
            if first_method:
                return first_method.group(1).upper()

        return "GET"  # Default

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract Python import dependencies from file content."""
        dependencies = []

        for pattern in self.IMPORT_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                module = match.group(1)
                if module and module not in dependencies:
                    dependencies.append(module)

        return dependencies

    def _extract_js_dependencies(self, content: str) -> List[str]:
        """Extract JavaScript import dependencies from file content."""
        dependencies = []

        # ES6 imports
        es6_pattern = r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]"
        matches = re.finditer(es6_pattern, content)
        for match in matches:
            dep = match.group(1)
            if dep and dep not in dependencies:
                dependencies.append(dep)

        # CommonJS requires
        cjs_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
        matches = re.finditer(cjs_pattern, content)
        for match in matches:
            dep = match.group(1)
            if dep and dep not in dependencies:
                dependencies.append(dep)

        return dependencies

    def calculate_impact(
        self,
        changed_files: List[ChangedFile],
        consider_dependencies: bool = True,
    ) -> List[ImpactResult]:
        """Calculate impact of changes on endpoints.

        Args:
            changed_files: List of changed files
            consider_dependencies: Whether to consider dependency impact

        Returns:
            List of impact results for affected endpoints
        """
        if not self.endpoint_map:
            self.discover_endpoints()

        impact_results = []
        changed_file_paths = {f.path for f in changed_files}

        # Build reverse dependency graph if needed
        if consider_dependencies:
            self._build_dependency_graph()

        for endpoint_key, metadata in self.endpoint_map.items():
            impact_score = 0
            affected_files = []
            impact_factors = {}
            direct_change = False
            dependencies = []

            # Check if endpoint file was directly changed
            if metadata["file"] in changed_file_paths:
                impact_score += 50
                affected_files.append(metadata["file"])
                impact_factors["direct_change"] = 50
                direct_change = True

            # Check for indirect impact through dependencies
            if consider_dependencies:
                for changed_file in changed_files:
                    # Check if changed file is a dependency of this endpoint
                    if self._is_dependency(metadata["file"], changed_file.path):
                        impact_score += 25
                        affected_files.append(changed_file.path)
                        impact_factors["dependency"] = (
                            impact_factors.get("dependency", 0) + 25
                        )
                        dependencies.append(changed_file.path)

            # Adjust score based on change magnitude
            for changed_file in changed_files:
                if changed_file.path in affected_files:
                    total_lines = changed_file.lines_added + changed_file.lines_deleted
                    if total_lines > 50:
                        impact_score += 15
                        impact_factors["large_change"] = 15
                    elif total_lines > 20:
                        impact_score += 10
                        impact_factors["medium_change"] = 10

                    # Check for critical patterns
                    if self._has_critical_changes(changed_file):
                        impact_score += 20
                        impact_factors["critical_pattern"] = 20

            # Cap at 100
            impact_score = min(impact_score, 100)

            if impact_score > 0:
                result = ImpactResult(
                    endpoint_path=metadata["path"],
                    http_method=metadata["method"],
                    impact_score=impact_score,
                    affected_files=list(set(affected_files)),
                    impact_factors=impact_factors,
                    direct_change=direct_change,
                    dependencies=dependencies,
                )
                impact_results.append(result)

        # Sort by impact score (descending)
        impact_results.sort(key=lambda x: x.impact_score, reverse=True)

        return impact_results

    def _build_dependency_graph(self):
        """Build a graph of file dependencies."""
        self.dependency_graph = {}

        for endpoint_key, metadata in self.endpoint_map.items():
            file_path = metadata["file"]
            self.dependency_graph[file_path] = set(metadata.get("dependencies", []))

    def _is_dependency(self, endpoint_file: str, changed_file: str) -> bool:
        """Check if changed file is a dependency of the endpoint file."""
        # Simple string matching - can be enhanced with AST parsing
        endpoint_deps = self.dependency_graph.get(endpoint_file, set())

        # Check if changed file matches any dependency
        changed_base = Path(changed_file).stem
        for dep in endpoint_deps:
            if changed_base in dep or dep in changed_file:
                return True

        return False

    def _has_critical_changes(self, changed_file: ChangedFile) -> bool:
        """Check if changes contain critical patterns."""
        critical_patterns = [
            r"def\s+validate",
            r"def\s+authenticate",
            r"def\s+authorize",
            r"raise\s+",
            r"return\s+.*error",
            r"status_code\s*=\s*",
            r"json\(",
            r"db\.(commit|flush)",
        ]

        for change in changed_file.content_changes:
            for pattern in critical_patterns:
                if re.search(pattern, change, re.IGNORECASE):
                    return True

        return False

    def get_impact_summary(self, impact_results: List[ImpactResult]) -> Dict:
        """Get a summary of impact analysis.

        Args:
            impact_results: List of impact results

        Returns:
            Summary dictionary
        """
        if not impact_results:
            return {
                "total_endpoints_affected": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "average_impact_score": 0,
            }

        high_risk = sum(1 for r in impact_results if r.impact_score >= 70)
        medium_risk = sum(1 for r in impact_results if 40 <= r.impact_score < 70)
        low_risk = sum(1 for r in impact_results if r.impact_score < 40)

        avg_score = sum(r.impact_score for r in impact_results) / len(impact_results)

        # Count files affected
        all_files = set()
        for result in impact_results:
            all_files.update(result.affected_files)

        return {
            "total_endpoints_affected": len(impact_results),
            "high_risk_count": high_risk,
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
            "average_impact_score": round(avg_score, 2),
            "total_files_affected": len(all_files),
            "directly_changed_endpoints": sum(
                1 for r in impact_results if r.direct_change
            ),
        }

    def prioritize_tests(
        self,
        impact_results: List[ImpactResult],
        available_tests: Optional[List[str]] = None,
    ) -> List[Tuple[str, int]]:
        """Prioritize tests based on impact analysis.

        Args:
            impact_results: List of impact results
            available_tests: Optional list of available test names

        Returns:
            List of (test_name, priority_score) tuples sorted by priority
        """
        prioritized = []

        for result in impact_results:
            # Generate test name from endpoint
            test_name = f"test_{result.http_method.lower()}_{result.endpoint_path.replace('/', '_').strip('_')}"

            # Calculate priority (higher impact = higher priority)
            priority = result.impact_score

            # Boost priority for direct changes
            if result.direct_change:
                priority += 10

            # Cap at 100
            priority = min(priority, 100)

            prioritized.append((test_name, priority))

        # Sort by priority (descending)
        prioritized.sort(key=lambda x: x[1], reverse=True)

        return prioritized
