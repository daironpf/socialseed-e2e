"""
Business Traceability Generator for socialseed-e2e.

This module provides automatic generation of business documentation and
traceability maps linking tests to business requirements.

Features:
- Auto-generate PlantUML/Mermaid diagrams from test flows
- Link tests to project_knowledge.json domains
- Export traceability maps for Jira integration
- Generate business-readable documentation

Usage:
    >>> from socialseed_e2e.business_traceability import BusinessTraceabilityGenerator
    >>>
    >>> generator = BusinessTraceabilityGenerator("/path/to/services")
    >>> generator.generate_traceability_docs()
    >>> generator.export_jira_matrix()
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BusinessRequirement(BaseModel):
    """A business requirement or user story."""

    req_id: str
    title: str
    description: str
    domain: str
    priority: str = "medium"
    linked_tests: List[str] = Field(default_factory=list)


class TestScenario(BaseModel):
    """A test scenario with business context."""

    scenario_id: str
    test_file: str
    test_name: str

    description: str
    domain: str

    covered_requirements: List[str] = Field(default_factory=list)
    business_flow: List[str] = Field(default_factory=list)
    endpoints_used: List[str] = Field(default_factory=list)


class TraceabilityMap(BaseModel):
    """Complete traceability map linking tests to requirements."""

    generated_at: datetime = Field(default_factory=datetime.now)

    requirements: List[BusinessRequirement] = Field(default_factory=list)
    test_scenarios: List[TestScenario] = Field(default_factory=list)

    domain_coverage: Dict[str, float] = {}

    test_to_requirement_map: Dict[str, List[str]] = {}
    requirement_to_test_map: Dict[str, List[str]] = {}


class BusinessTraceabilityGenerator:
    """
    Generates business documentation and traceability maps.
    """

    def __init__(self, services_path: str, manifest_dir: Optional[str] = None):
        self.services_path = Path(services_path)
        self.manifest_dir = Path(manifest_dir) if manifest_dir else None

        self.traceability_map = TraceabilityMap()
        self.mermaid_diagrams: Dict[str, str] = {}
        self.plantuml_diagrams: Dict[str, str] = {}

    def load_manifest(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Load project knowledge manifest for a service."""
        if not self.manifest_dir:
            return None

        manifest_path = self.manifest_dir / service_name / "project_knowledge.json"
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                return json.load(f)
        return None

    def analyze_test_flows(self) -> List[TestScenario]:
        """Analyze test files to extract business flows."""
        scenarios = []

        if not self.services_path.exists():
            return scenarios

        for service_dir in self.services_path.iterdir():
            if not service_dir.is_dir():
                continue

            modules_dir = service_dir / "modules"
            if not modules_dir.exists():
                continue

            service_name = service_dir.name

            for test_file in modules_dir.glob("*.py"):
                if test_file.name.startswith("_"):
                    continue

                scenarios.extend(
                    self._extract_scenarios_from_file(test_file, service_name)
                )

        return scenarios

    def _extract_scenarios_from_file(
        self, test_file: Path, service_name: str
    ) -> List[TestScenario]:
        """Extract test scenarios from a test file."""
        scenarios = []

        try:
            with open(test_file, "r") as f:
                content = f.read()
        except Exception:
            return scenarios

        test_name = test_file.stem

        endpoints = self._extract_endpoints(content)

        scenario = TestScenario(
            scenario_id=f"{service_name}_{test_name}",
            test_file=str(test_file),
            test_name=test_name,
            description=self._generate_description(content),
            domain=service_name,
            endpoints_used=endpoints,
        )

        scenarios.append(scenario)
        return scenarios

    def _extract_endpoints(self, content: str) -> List[str]:
        """Extract API endpoints from test code."""
        import re

        endpoints = []
        patterns = [
            r'["\'](/api[^\'"]*)["\']',
            r'\.get\(["\'](/[^"\']+)["\']',
            r'\.post\(["\'](/[^"\']+)["\']',
            r'\.put\(["\'](/[^"\']+)["\']',
            r'\.delete\(["\'](/[^"\']+)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            endpoints.extend(matches)

        return list(set(endpoints))

    def _generate_description(self, content: str) -> str:
        """Generate business description from test code."""
        import re

        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip().split("\n")[0]

        return "Test scenario"

    def generate_mermaid_diagram(self, scenario: TestScenario) -> str:
        """Generate Mermaid sequence diagram for a test scenario."""
        diagram = f"""```mermaid
sequenceDiagram
    participant Client
    participant API as {scenario.domain}
"""

        for _i, endpoint in enumerate(scenario.endpoints_used):
            diagram += f"    Client->>API: {endpoint}\n"
            diagram += "    API-->>Client: Response\n"

        diagram += "```"
        return diagram

    def generate_plantuml_diagram(self, scenario: TestScenario) -> str:
        """Generate PlantUML diagram for a test scenario."""
        diagram = """@startuml
skinparam sequenceArrowThickness 2
skinparam roundcorner 20
skinparam maxmessagesize 60
hide footbox

actor Client
boundary API as "API Service"
"""

        for _i, endpoint in enumerate(scenario.endpoints_used):
            endpoint_name = endpoint.replace("/", "_").strip("_")
            diagram += f"Client -> API: {endpoint}\n"
            diagram += "activate API\n"
            diagram += "API -->> Client: Response\n"
            diagram += "deactivate API\n"

        diagram += "@enduml"
        return diagram

    def generate_all_diagrams(self) -> None:
        """Generate diagrams for all test scenarios."""
        scenarios = self.analyze_test_flows()
        self.traceability_map.test_scenarios = scenarios

        for scenario in scenarios:
            self.mermaid_diagrams[scenario.scenario_id] = self.generate_mermaid_diagram(
                scenario
            )
            self.plantuml_diagrams[scenario.scenario_id] = (
                self.generate_plantuml_diagram(scenario)
            )

    def link_to_manifest(self, service_name: str) -> None:
        """Link test scenarios to project manifest domains."""
        manifest = self.load_manifest(service_name)
        if not manifest:
            return

        endpoints_data = manifest.get("endpoints", [])

        for scenario in self.traceability_map.test_scenarios:
            for endpoint in scenario.endpoints_used:
                for ep in endpoints_data:
                    if ep.get("path") == endpoint:
                        domain = ep.get("domain", service_name)
                        if domain not in scenario.business_flow:
                            scenario.business_flow.append(domain)

    def export_markdown_report(self, output_path: str) -> None:
        """Export traceability report as Markdown."""
        report = "# Business Traceability Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += "## Test Scenarios\n\n"

        for scenario in self.traceability_map.test_scenarios:
            report += f"### {scenario.scenario_id}\n\n"
            report += f"**File:** `{scenario.test_file}`\n\n"
            report += f"**Description:** {scenario.description}\n\n"
            report += f"**Domain:** {scenario.domain}\n\n"

            if scenario.endpoints_used:
                report += "**Endpoints:**\n"
                for ep in scenario.endpoints_used:
                    report += f"- `{ep}`\n"
                report += "\n"

            if scenario.scenario_id in self.mermaid_diagrams:
                report += "**Flow Diagram:**\n\n"
                report += self.mermaid_diagrams[scenario.scenario_id] + "\n\n"

            report += "---\n\n"

        with open(output_path, "w") as f:
            f.write(report)

    def export_jira_matrix(self, output_path: str) -> None:
        """Export traceability matrix in Jira-compatible format."""
        matrix = {
            "export_date": datetime.now().isoformat(),
            "test_scenarios": [],
            "requirements": [],
        }

        for scenario in self.traceability_map.test_scenarios:
            matrix["test_scenarios"].append(
                {
                    "key": scenario.scenario_id,
                    "summary": scenario.description,
                    "domain": scenario.domain,
                    "endpoints": scenario.endpoints_used,
                    "linked_requirements": scenario.covered_requirements,
                }
            )

        with open(output_path, "w") as f:
            json.dump(matrix, f, indent=2)

    def export_json(self, output_path: str) -> None:
        """Export full traceability map as JSON."""
        with open(output_path, "w") as f:
            json.dump(self.traceability_map.model_dump(by_alias=True), f, indent=2)

    def generate_traceability_docs(
        self, output_dir: str = "e2e_reports"
    ) -> Dict[str, str]:
        """Generate all traceability documentation."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        self.generate_all_diagrams()

        files_generated = {}

        self.export_markdown_report(str(output / "traceability_report.md"))
        files_generated["markdown"] = str(output / "traceability_report.md")

        self.export_json(str(output / "traceability_map.json"))
        files_generated["json"] = str(output / "traceability_map.json")

        self.export_jira_matrix(str(output / "jira_matrix.json"))
        files_generated["jira"] = str(output / "jira_matrix.json")

        return files_generated


class TraceabilityExporter:
    """Exports traceability data in various formats."""

    @staticmethod
    def to_plantuml(scenarios: List[TestScenario]) -> str:
        """Export scenarios as PlantUML."""
        diagram = "@startuml\n"
        diagram += "skinparam linetype ortho\n"
        diagram += "skinparam componentStyle rectangle\n\n"

        for scenario in scenarios:
            diagram += f'component "{scenario.domain}" {{\n'
            for ep in scenario.endpoints_used:
                diagram += f"  note right: {ep}\n"
            diagram += "}\n\n"

        diagram += "@enduml"
        return diagram

    @staticmethod
    def to_mermaid(scenarios: List[TestScenario]) -> str:
        """Export scenarios as Mermaid flowchart."""
        diagram = "```mermaid\n"
        diagram += "flowchart TD\n"
        diagram += "    subgraph Tests\n"

        for scenario in scenarios:
            test_id = scenario.scenario_id.replace("-", "_")
            diagram += f"        T_{test_id}['{scenario.test_name}']\n"

        diagram += "    end\n"
        diagram += "```"
        return diagram


__all__ = [
    "BusinessRequirement",
    "TestScenario",
    "TraceabilityMap",
    "BusinessTraceabilityGenerator",
    "TraceabilityExporter",
]
