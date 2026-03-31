"""Health checks scanner for detecting health endpoints.

This module detects health check endpoints and liveness/readiness probes.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class HealthEndpoint:
    """Represents a health check endpoint."""

    path: str
    method: str = "GET"
    type: str = "health"  # "health", "liveness", "readiness"
    dependencies: List[str] = field(default_factory=list)


@dataclass
class HealthInfo:
    """Represents health check information."""

    endpoints: List[HealthEndpoint] = field(default_factory=list)
    kubernetes_probes: Dict[str, Any] = field(default_factory=dict)


class HealthCheckScanner:
    """Scans for health check endpoints."""

    HEALTH_PATTERNS = [
        r"/health",
        r"/healthz",
        r"/_health",
        r"/actuator/health",
        r"/status",
        r"/ping",
        r"/ready",
        r"/live",
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> HealthInfo:
        """Scan for health check endpoints."""
        info = HealthInfo()

        self._scan_code_for_health_endpoints(info)
        self._scan_kubernetes_probes(info)

        return info

    def _scan_code_for_health_endpoints(self, info: HealthInfo) -> None:
        """Scan code for health endpoints."""
        for ext in [".py", ".js", ".ts", ".java", ".go"]:
            for file_path in self.project_root.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(errors="ignore")
                    
                    for pattern in self.HEALTH_PATTERNS:
                        if re.search(pattern, content, re.IGNORECASE):
                            endpoint = HealthEndpoint(path=pattern)
                            info.endpoints.append(endpoint)
                except Exception:
                    pass

    def _scan_kubernetes_probes(self, info: HealthInfo) -> None:
        """Scan for Kubernetes probe configurations."""
        k8s_files = list(self.project_root.glob("*.yml")) + list(self.project_root.glob("*.yaml"))
        
        for k8s_file in k8s_files:
            content = k8s_file.read_text(errors="ignore")
            
            liveness_match = re.search(r"livenessProbe:\s*(\w+)", content)
            readiness_match = re.search(r"readinessProbe:\s*(\w+)", content)
            
            if liveness_match or readiness_match:
                if liveness_match:
                    info.kubernetes_probes["liveness"] = liveness_match.group(1)
                if readiness_match:
                    info.kubernetes_probes["readiness"] = readiness_match.group(1)


def generate_health_checks_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate HEALTH_CHECKS.md document."""
    scanner = HealthCheckScanner(project_root)
    info = scanner.scan()

    doc = "# Health Checks\n\n"

    if info.endpoints:
        doc += "## Endpoints de Health\n\n"
        doc += "| Path | Método | Tipo |\n"
        doc += "|------|--------|------|\n"
        for endpoint in info.endpoints:
            doc += f"| {endpoint.path} | {endpoint.method} | {endpoint.type} |\n"
        doc += "\n"
    else:
        doc += "No se detectaron endpoints de health.\n\n"

    if info.kubernetes_probes:
        doc += "## Kubernetes Probes\n\n"
        for probe_type, config in info.kubernetes_probes.items():
            doc += f"- **{probe_type}**: `{config}`\n"
        doc += "\n"

    doc += "---\n\n"
    doc += "## Ejemplo de Test de Health\n\n"
    doc += "```python\n"
    doc += "def test_health_endpoint(page):\n"
    doc += "    \"\"\"Test: Verificar que el servicio está healthy\"\"\"\n"
    doc += "    response = page.get(\"/health\")\n"
    doc += "    assert response.status == 200\n"
    doc += "    assert response.json().get(\"status\") == \"UP\"\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_health_checks_doc(project_root))
    else:
        print("Usage: python health_checks_scanner.py <project_root>")
