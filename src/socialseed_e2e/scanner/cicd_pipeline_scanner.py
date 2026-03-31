"""CI/CD pipeline scanner for detecting CI/CD configuration.

This module detects CI/CD pipelines and generates pipeline templates.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Pipeline:
    """Represents a CI/CD pipeline."""

    platform: str
    file_path: str
    jobs: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)


@dataclass
class CICDInfo:
    """Represents CI/CD information."""

    pipelines: List[Pipeline] = field(default_factory=list)
    detected_platforms: List[str] = field(default_factory=list)


class CICDPipelineScanner:
    """Scans for CI/CD pipelines."""

    PLATFORM_PATTERNS = {
        "GitHub Actions": [r".github/workflows/*.yml", r".github/workflows/*.yaml"],
        "GitLab CI": [r".gitlab-ci.yml"],
        "Jenkins": [r"Jenkinsfile", r"jenkinsfile"],
        "Azure Pipelines": [r"azure-pipelines.yml", r"azure-pipelines.yaml"],
        "CircleCI": [r".circleci/config.yml"],
        "Travis CI": [r".travis.yml"],
        "Bitbucket": [r"bitbucket-pipelines.yml"],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> CICDInfo:
        """Scan for CI/CD pipelines."""
        info = CICDInfo()

        self._detect_pipelines(info)
        self._extract_jobs(info)

        return info

    def _detect_pipelines(self, info: CICDInfo) -> None:
        """Detect CI/CD pipelines."""
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                matches = self.project_root.glob(pattern)
                for match in matches:
                    pipeline = Pipeline(
                        platform=platform,
                        file_path=str(match.relative_to(self.project_root)),
                    )
                    info.pipelines.append(pipeline)
                    info.detected_platforms.append(platform)

        info.detected_platforms = list(set(info.detected_platforms))

    def _extract_jobs(self, info: CICDInfo) -> None:
        """Extract jobs from pipeline files."""
        for pipeline in info.pipelines:
            file_path = self.project_root / pipeline.file_path
            if file_path.exists():
                content = file_path.read_text(errors="ignore")

                if "jobs:" in content:
                    job_pattern = re.compile(r"^\s+(\w+):", re.MULTILINE)
                    matches = job_pattern.finditer(content)
                    pipeline.jobs = [m.group(1) for m in matches if m.group(1) != "steps"]

                if "on:" in content:
                    trigger_patterns = [
                        r"push",
                        r"pull_request",
                        r"schedule",
                        r"workflow_dispatch",
                    ]
                    for t in trigger_patterns:
                        if t in content.lower():
                            pipeline.triggers.append(t)


def generate_cicd_pipeline_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate CI_CD_PIPELINE.md document."""
    scanner = CICDPipelineScanner(project_root)
    info = scanner.scan()

    doc = "# Pipeline de CI/CD\n\n"

    if info.detected_platforms:
        doc += "## Plataformas Detectadas\n\n"
        for platform in info.detected_platforms:
            doc += f"- ✅ {platform}\n"
        doc += "\n"
    else:
        doc += "No se detectó configuración de CI/CD.\n\n"

    if info.pipelines:
        doc += "## Pipelines Existentes\n\n"
        for pipeline in info.pipelines:
            doc += f"### {pipeline.platform}\n\n"
            doc += f"- Archivo: `{pipeline.file_path}`\n"

            if pipeline.jobs:
                doc += "- Jobs: " + ", ".join([f"`{j}`" for j in pipeline.jobs[:5]])
                doc += "\n"

            if pipeline.triggers:
                doc += "- Triggers: " + ", ".join(pipeline.triggers)
                doc += "\n"
            doc += "\n"

    doc += "---\n\n"
    doc += "## Generar Nuevo Pipeline\n\n"
    doc += "```bash\n"
    doc += "# Generar pipeline para GitHub Actions\n"
    doc += "e2e setup-ci github\n\n"
    doc += "# Generar pipeline para GitLab CI\n"
    doc += "e2e setup-ci gitlab\n\n"
    doc += "# Generar pipeline para Jenkins\n"
    doc += "e2e setup-ci jenkins\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_cicd_pipeline_doc(project_root))
    else:
        print("Usage: python cicd_pipeline_scanner.py <project_root>")
