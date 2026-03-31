"""Dependencies scanner for listing project dependencies.

This module scans and lists all project dependencies with versions.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Dependency:
    """Represents a project dependency."""

    name: str
    version: str
    type: str  # "runtime", "dev", "peer"
    source: str  # "npm", "pip", "maven", etc.


@dataclass
class DependenciesInfo:
    """Represents dependencies information."""

    dependencies: List[Dependency] = field(default_factory=list)
    total_runtime: int = 0
    total_dev: int = 0


class DependenciesScanner:
    """Scans for project dependencies."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> DependenciesInfo:
        """Scan for dependencies."""
        info = DependenciesInfo()

        self._scan_package_json(info)
        self._scan_requirements_txt(info)
        self._scan_pom_xml(info)
        self._scan_build_gradle(info)
        self._scan_go_mod(info)

        return info

    def _scan_package_json(self, info: DependenciesInfo) -> None:
        """Scan package.json files."""
        for pkg_file in self.project_root.glob("package.json"):
            try:
                content = json.loads(pkg_file.read_text(errors="ignore"))
                
                for dep_type, deps in [("dependencies", "runtime"), ("devDependencies", "dev"), ("peerDependencies", "peer")]:
                    if dep_type in content:
                        for name, version in content[dep_type].items():
                            info.dependencies.append(Dependency(
                                name=name,
                                version=str(version),
                                type=deps,
                                source="npm",
                            ))
                            if deps == "runtime":
                                info.total_runtime += 1
                            else:
                                info.total_dev += 1
            except Exception:
                pass

    def _scan_requirements_txt(self, info: DependenciesInfo) -> None:
        """Scan requirements.txt files."""
        for req_file in self.project_root.glob("requirements*.txt"):
            content = req_file.read_text(errors="ignore")
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" in line:
                        name, version = line.split("==", 1)
                        info.dependencies.append(Dependency(
                            name=name.strip(),
                            version=version.strip(),
                            type="runtime",
                            source="pip",
                        ))
                        info.total_runtime += 1
                    elif ">=" in line:
                        name, version = line.split(">=", 1)
                        info.dependencies.append(Dependency(
                            name=name.strip(),
                            version=f">={version.strip()}",
                            type="runtime",
                            source="pip",
                        ))
                        info.total_runtime += 1

    def _scan_pom_xml(self, info: DependenciesInfo) -> None:
        """Scan pom.xml files."""
        for pom_file in self.project_root.glob("pom.xml"):
            content = pom_file.read_text(errors="ignore")
            
            dep_pattern = re.compile(r"<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]+)</version>", re.DOTALL)
            matches = dep_pattern.finditer(content)
            
            for match in matches:
                info.dependencies.append(Dependency(
                    name=f"{match.group(1)}:{match.group(2)}",
                    version=match.group(3),
                    type="runtime",
                    source="maven",
                ))
                info.total_runtime += 1

    def _scan_build_gradle(self, info: DependenciesInfo) -> None:
        """Scan build.gradle files."""
        for gradle_file in self.project_root.glob("build.gradle"):
            content = gradle_file.read_text(errors="ignore")
            
            dep_pattern = re.compile(r"(?:implementation|compile|api)\s*['\"]([^:]+):([^:]+):([^'\"]+)['\"]")
            matches = dep_pattern.finditer(content)
            
            for match in matches:
                info.dependencies.append(Dependency(
                    name=f"{match.group(1)}:{match.group(2)}",
                    version=match.group(3),
                    type="runtime",
                    source="gradle",
                ))
                info.total_runtime += 1

    def _scan_go_mod(self, info: DependenciesInfo) -> None:
        """Scan go.mod files."""
        for go_file in self.project_root.glob("go.mod"):
            content = go_file.read_text(errors="ignore")
            in_require = False
            
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("require ("):
                    in_require = True
                elif line == ")" and in_require:
                    in_require = False
                elif line and not line.startswith("//"):
                    if "(" in line:
                        in_require = True
                    parts = line.split()
                    if len(parts) >= 2:
                        info.dependencies.append(Dependency(
                            name=parts[0],
                            version=parts[1] if len(parts) > 1 else "N/A",
                            type="runtime",
                            source="go",
                        ))
                        info.total_runtime += 1


def generate_dependencies_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate DEPENDENCIES.md document."""
    scanner = DependenciesScanner(project_root)
    info = scanner.scan()

    doc = "# Dependencias del Proyecto\n\n"

    doc += f"**Total Runtime**: {info.total_runtime}\n"
    doc += f"**Total Dev**: {info.total_dev}\n\n"

    by_source = {}
    for dep in info.dependencies:
        if dep.source not in by_source:
            by_source[dep.source] = []
        by_source[dep.source].append(dep)

    for source, deps in by_source.items():
        doc += f"## {source.upper()}\n\n"
        doc += "| Paquete | Versión | Tipo |\n"
        doc += "|---------|---------|------|\n"
        for dep in deps:
            doc += f"| {dep.name} | {dep.version} | {dep.type} |\n"
        doc += "\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_dependencies_doc(project_root))
    else:
        print("Usage: python dependencies_scanner.py <project_root>")
