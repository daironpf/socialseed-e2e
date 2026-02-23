"""AI Discovery Report Generator for socialseed-e2e.

This module generates a comprehensive "Discovery Report" after the first scan,
presenting a "Mental Map" of the AI's understanding of the developer's project.

Issue #187: Generate an AI "Discovery Report" after the first scan
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.project_manifest.models import ProjectKnowledge


@dataclass
class DiscoveredFlow:
    """A discovered business flow in the project."""

    name: str
    description: str
    endpoints_count: int
    flow_type: str  # 'authentication', 'crud', 'management', 'custom'
    complexity: str  # 'simple', 'moderate', 'complex'


@dataclass
class DiscoverySummary:
    """Summary of discovered project information."""

    project_name: str
    project_path: Path
    analysis_timestamp: datetime
    tech_stack: Dict[str, Any]
    services_count: int
    endpoints_count: int
    dtos_count: int
    flows_discovered: List[DiscoveredFlow]
    tests_generated: int
    output_directory: Path


class DiscoveryReportGenerator:
    """Generates AI Discovery Reports after scanning projects."""

    def __init__(self, project_root: Path, output_dir: Optional[Path] = None):
        """Initialize the discovery report generator.

        Args:
            project_root: Root directory of the project
            output_dir: Directory where reports will be saved (default: project_root/.e2e)
        """
        self.project_root = Path(project_root).resolve()
        self.output_dir = output_dir or (self.project_root / ".e2e")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        manifest: Optional[ProjectKnowledge] = None,
        flows: Optional[List[Dict[str, Any]]] = None,
        tests_generated: int = 0,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Generate the discovery report.

        Args:
            manifest: Project manifest with discovered information
            flows: List of discovered flows from business logic inference
            tests_generated: Number of test files generated
            output_dir: Directory where tests were generated

        Returns:
            Path to the generated report file
        """
        # Load manifest if not provided
        if manifest is None:
            manifest = self._load_manifest()

        # Create summary
        summary = self._create_summary(manifest, flows, tests_generated, output_dir)

        # Generate markdown report
        report_path = self._generate_markdown_report(summary)

        # Also generate CLI summary
        self._print_cli_summary(summary)

        return report_path

    def _load_manifest(self) -> Optional[ProjectKnowledge]:
        """Load existing project manifest."""
        manifest_path = self.project_root / "project_knowledge.json"
        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)

            # Parse into ProjectKnowledge (simplified)
            return ProjectKnowledge(**data)
        except Exception:
            return None

    def _create_summary(
        self,
        manifest: Optional[ProjectKnowledge],
        flows: Optional[List[Dict[str, Any]]],
        tests_generated: int,
        output_dir: Optional[Path],
    ) -> DiscoverySummary:
        """Create discovery summary from manifest and flows."""

        # Get project name
        project_name = self.project_root.name

        # Count services and endpoints
        services_count = 0
        endpoints_count = 0
        dtos_count = 0
        tech_stack = {}

        if manifest:
            services = getattr(manifest, "services", [])
            services_count = len(services)

            for service in services:
                endpoints_count += len(getattr(service, "endpoints", []))
                dtos_count += len(getattr(service, "dto_schemas", []))

                # Get tech stack info
                framework = getattr(service, "framework", None)
                language = getattr(service, "language", "unknown")

                if framework:
                    tech_stack[service.name] = {
                        "framework": framework,
                        "language": language,
                    }

        # Process flows
        discovered_flows = []
        if flows:
            for flow in flows:
                discovered_flows.append(
                    DiscoveredFlow(
                        name=flow.get("name", "Unknown Flow"),
                        description=flow.get("description", ""),
                        endpoints_count=len(flow.get("steps", [])),
                        flow_type=flow.get("flow_type", "custom"),
                        complexity=self._calculate_complexity(flow),
                    )
                )

        return DiscoverySummary(
            project_name=project_name,
            project_path=self.project_root,
            analysis_timestamp=datetime.now(),
            tech_stack=tech_stack,
            services_count=services_count,
            endpoints_count=endpoints_count,
            dtos_count=dtos_count,
            flows_discovered=discovered_flows,
            tests_generated=tests_generated,
            output_directory=output_dir or self.project_root / "services",
        )

    def _calculate_complexity(self, flow: Dict[str, Any]) -> str:
        """Calculate flow complexity based on steps and relationships."""
        steps_count = len(flow.get("steps", []))

        if steps_count <= 2:
            return "simple"
        elif steps_count <= 4:
            return "moderate"
        else:
            return "complex"

    def _generate_markdown_report(self, summary: DiscoverySummary) -> Path:
        """Generate markdown discovery report."""
        report_path = self.output_dir / "DISCOVERY_REPORT.md"

        # Build the report content
        content = self._build_markdown_content(summary)

        # Write to file
        with open(report_path, "w") as f:
            f.write(content)

        return report_path

    def _build_markdown_content(self, summary: DiscoverySummary) -> str:
        """Build the markdown report content."""

        lines = [
            "# 🔍 AI Discovery Report",
            "",
            f"**Project:** `{summary.project_name}`  ",
            f"**Path:** `{summary.project_path}`  ",
            f"**Generated:** {summary.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 🧠 Mental Map of Your Project",
            "",
        ]

        # Tech Stack Summary
        if summary.tech_stack:
            lines.extend(
                [
                    "### 📦 Technology Stack",
                    "",
                ]
            )

            for service_name, tech in summary.tech_stack.items():
                framework = tech.get("framework", "Unknown")
                language = tech.get("language", "Unknown")
                lines.append(f"- **{service_name}**: {framework} ({language})")

            lines.append("")

        # Statistics
        lines.extend(
            [
                "### 📊 Project Statistics",
                "",
                "| Metric | Count |",
                "|--------|-------|",
                f"| Services | {summary.services_count} |",
                f"| REST Endpoints | {summary.endpoints_count} |",
                f"| DTOs/Models | {summary.dtos_count} |",
                f"| Business Flows | {len(summary.flows_discovered)} |",
                f"| Test Files Generated | {summary.tests_generated} |",
                "",
            ]
        )

        # Discovered Flows
        if summary.flows_discovered:
            lines.extend(
                [
                    "### 🌊 Discovered Business Flows",
                    "",
                ]
            )

            for flow in summary.flows_discovered:
                emoji = self._get_flow_emoji(flow.flow_type)
                complexity_emoji = self._get_complexity_emoji(flow.complexity)
                lines.extend(
                    [
                        f"#### {emoji} {flow.name}",
                        "",
                        f"- **Description:** {flow.description}",
                        f"- **Type:** {flow.flow_type.title()}",
                        f"- **Endpoints:** {flow.endpoints_count}",
                        f"- **Complexity:** {complexity_emoji} {flow.complexity.title()}",
                        "",
                    ]
                )

        # Single Command Execution
        lines.extend(
            [
                "---",
                "",
                "## 🚀 Ready to Run?",
                "",
                "I've analyzed your project and created comprehensive test suites.",
                "",
                "### Execute All Tests",
                "",
                "```bash",
                f"cd {summary.project_path}",
                "e2e run",
                "```",
                "",
                "### Or Execute with Options",
                "",
                "```bash",
                "# Run specific service",
                f"e2e run --service {summary.tech_stack.get(list(summary.tech_stack.keys())[0], {}).get('name', 'service')}"
                if summary.tech_stack
                else "e2e run --service <service-name>",
                "",
                "# Run with verbose output",
                "e2e run --verbose",
                "",
                "# Generate new tests if code changed",
                "e2e generate-tests --force",
                "```",
                "",
            ]
        )

        # Quick Reference
        lines.extend(
            [
                "### 📖 Quick Reference",
                "",
                "| Command | Description |",
                "|---------|-------------|",
                "| `e2e run` | Run all tests |",
                "| `e2e run --service <name>` | Run tests for specific service |",
                "| `e2e run --verbose` | Run with detailed output |",
                "| `e2e observe` | Check for running services |",
                "| `e2e manifest` | Re-scan project |",
                "| `e2e generate-tests` | Regenerate test suites |",
                "",
            ]
        )

        # What's Next
        lines.extend(
            [
                "### 🎯 What's Next?",
                "",
                "1. **Review the generated tests** in the `services/` directory",
                "2. **Customize test data** in `data_schema.py` files",
                "3. **Run the tests** with `e2e run`",
                "4. **Add custom tests** for specific business logic",
                "",
                "### 📁 Generated Files",
                "",
                f"All test files have been generated in: `{summary.output_directory}`",
                "",
                "```",
                summary.output_directory.name if summary.output_directory else "services",
                "/",
                "├── <service-name>/",
                "│   ├── __init__.py",
                "│   ├── data_schema.py       # DTOs and test data",
                "│   ├── <service>_page.py    # Page objects",
                "│   └── modules/",
                "│       ├── _01_<flow>.py    # Flow tests",
                "│       └── _99_validation.py # Validation tests",
                "```",
                "",
                "---",
                "",
                "*This report was automatically generated by socialseed-e2e AI.*",
                "",
            ]
        )

        return "\n".join(lines)

    def _get_flow_emoji(self, flow_type: str) -> str:
        """Get emoji for flow type."""
        emojis = {
            "authentication": "🔐",
            "crud": "📋",
            "management": "⚙️",
            "registration": "📝",
            "checkout": "🛒",
            "workflow": "🔄",
            "custom": "📌",
        }
        return emojis.get(flow_type, "📌")

    def _get_complexity_emoji(self, complexity: str) -> str:
        """Get emoji for complexity level."""
        emojis = {
            "simple": "🟢",
            "moderate": "🟡",
            "complex": "🔴",
        }
        return emojis.get(complexity, "⚪")

    def _print_cli_summary(self, summary: DiscoverySummary) -> None:
        """Print a CLI summary of the discovery."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        # Build the summary message
        tech_info = ""
        if summary.tech_stack:
            tech_list = [
                f"{info['framework']} ({info['language']})" for info in summary.tech_stack.values()
            ]
            tech_info = f" in {', '.join(set(tech_list))}"

        # Main summary panel
        message = (
            f"I've analyzed your project. I found {summary.endpoints_count} REST "
            f"endpoints{tech_info}.\n\n"
            f"I've created {len(summary.flows_discovered)} complex business flows:\n"
        )

        for flow in summary.flows_discovered:
            message += f"  • {flow.name} ({flow.endpoints_count} steps)\n"

        message += (
            f"\n📁 Generated {summary.tests_generated} test files in "
            f"`{summary.output_directory.relative_to(summary.project_path)}`\n\n"
            f"✅ Ready to run? Execute: `e2e run`"
        )

        console.print(Panel(message, title="🤖 AI Discovery Complete", border_style="green"))

        # Statistics table
        table = Table(title="Project Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Services", str(summary.services_count))
        table.add_row("Endpoints", str(summary.endpoints_count))
        table.add_row("DTOs/Models", str(summary.dtos_count))
        table.add_row("Business Flows", str(len(summary.flows_discovered)))
        table.add_row("Test Files", str(summary.tests_generated))

        console.print(table)
        console.print()

        # Report location
        report_path = self.output_dir / "DISCOVERY_REPORT.md"
        console.print(f"📄 Full report saved to: {report_path}")
        console.print()

    def get_single_command(self) -> str:
        """Get the single command to execute everything.

        Returns:
            Command string to execute all tests
        """
        return f"cd {self.project_root} && e2e run"


def generate_discovery_report(
    project_root: Path,
    manifest: Optional[ProjectKnowledge] = None,
    flows: Optional[List[Dict[str, Any]]] = None,
    tests_generated: int = 0,
    output_dir: Optional[Path] = None,
) -> Path:
    """Convenience function to generate a discovery report.

    Args:
        project_root: Root directory of the project
        manifest: Project manifest
        flows: Discovered flows
        tests_generated: Number of test files generated
        output_dir: Output directory for tests

    Returns:
        Path to the generated report
    """
    generator = DiscoveryReportGenerator(project_root)
    return generator.generate_report(manifest, flows, tests_generated, output_dir)
