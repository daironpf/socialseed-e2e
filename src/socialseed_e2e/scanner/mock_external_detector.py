"""External API detector for mocking external dependencies.

This module detects external APIs used by the project and generates
mock configurations.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExternalAPI:
    """Represents an external API."""

    name: str
    base_url: str
    endpoints: List[Dict[str, str]] = field(default_factory=list)
    auth_type: str = ""
    usage_count: int = 0


@dataclass
class MockInfo:
    """Represents external API mock information."""

    apis: List[ExternalAPI] = field(default_factory=list)
    mock_config: Dict[str, Any] = field(default_factory=dict)


class ExternalAPIDetector:
    """Detects external APIs used in the project."""

    COMMON_API_PATTERNS = {
        "stripe": ["api.stripe.com", "stripe.com"],
        "paypal": ["api.paypal.com", "paypal.com"],
        "twilio": ["api.twilio.com"],
        "sendgrid": ["api.sendgrid.com", "sendgrid.net"],
        "aws": ["amazonaws.com", "aws.amazon.com"],
        "firebase": ["firebase.google.com", "firebaseio.com"],
        "auth0": ["auth0.com", "tenant.auth0.com"],
        "google": ["googleapis.com"],
        "github": ["api.github.com"],
        "slack": ["slack.com", "slack-api.com"],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def detect(self) -> MockInfo:
        """Detect external APIs."""
        info = MockInfo()

        self._scan_code_for_apis(info)
        self._scan_config_files(info)
        self._generate_mock_config(info)

        return info

    def _scan_code_for_apis(self, info: MockInfo) -> None:
        """Scan code for external API usage."""
        for ext in [".py", ".js", ".ts"]:
            for file_path in self.project_root.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(errors="ignore")

                    for api_name, domains in self.COMMON_API_PATTERNS.items():
                        for domain in domains:
                            if domain in content:
                                self._add_api(info, api_name, domain, file_path)
                except Exception:
                    pass

    def _add_api(self, info: MockInfo, api_name: str, domain: str, file_path: Path) -> None:
        """Add or update an external API."""
        for api in info.apis:
            if api.name == api_name:
                api.usage_count += 1
                return

        info.apis.append(ExternalAPI(
            name=api_name,
            base_url=f"https://{domain}",
            usage_count=1,
        ))

    def _scan_config_files(self, info: MockInfo) -> None:
        """Scan config files for API keys and endpoints."""
        config_files = [
            self.project_root / ".env",
            self.project_root / ".env.local",
            self.project_root / "config.json",
            self.project_root / "settings.py",
        ]

        for conf_file in config_files:
            if conf_file.exists():
                content = conf_file.read_text(errors="ignore")
                for api_name, domains in self.COMMON_API_PATTERNS.items():
                    for domain in domains:
                        if domain in content:
                            self._add_api(info, api_name, domain, conf_file)

    def _generate_mock_config(self, info: MockInfo) -> None:
        """Generate mock server configuration."""
        info.mock_config = {
            "mockserver": {
                "port": 1080,
                "verbose": True,
            },
            "mappings": [],
        }

        for api in info.apis:
            mapping = {
                "name": api.name,
                "base_url": api.base_url,
                "endpoints": [
                    {"method": "GET", "path": "/", "response": {"status": 200}},
                ],
            }
            info.mock_config["mappings"].append(mapping)


def generate_mock_external_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate MOCK_EXTERNAL.md document."""
    detector = ExternalAPIDetector(project_root)
    info = detector.detect()

    doc = "# APIs Externas y Mocks\n\n"

    if info.apis:
        doc += "## APIs Externas Detectadas\n\n"
        doc += "| API | URL Base | Usos |\n"
        doc += "|-----|----------|------|\n"
        for api in info.apis:
            doc += f"| {api.name} | {api.base_url} | {api.usage_count} |\n"
        doc += "\n"
    else:
        doc += "No se detectaron APIs externas.\n\n"

    doc += "## Configuración de Mocks\n\n"
    doc += "```yaml\n"
    doc += f"port: {info.mock_config.get('mockserver', {}).get('port', 1080)}\n"
    doc += "verbose: true\n"
    doc += "```\n\n"

    if info.mock_config.get("mappings"):
        doc += "### Mappings\n\n"
        for mapping in info.mock_config["mappings"]:
            doc += f"#### {mapping['name']}\n"
            doc += f"- Base URL: `{mapping['base_url']}`\n"
            doc += "- Endpoints: "
            doc += ", ".join([f"`{e['method']} {e['path']}`" for e in mapping["endpoints"]])
            doc += "\n\n"

    doc += "---\n\n"
    doc += "## Ejecución\n\n"
    doc += "```bash\n"
    doc += "# Generar mock server\n"
    doc += "e2e mock-generate\n\n"
    doc += "# Ejecutar mocks\n"
    doc += "e2e mock-run\n\n"
    doc += "# Validar contratos\n"
    doc += "e2e mock-validate\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_mock_external_doc(project_root))
    else:
        print("Usage: python mock_external_detector.py <project_root>")
