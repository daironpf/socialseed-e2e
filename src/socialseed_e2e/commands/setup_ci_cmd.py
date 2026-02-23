"""Setup CI/CD command for socialseed-e2e CLI.

This module provides the setup-ci command using POO and SOLID principles.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import click
from rich.console import Console

from socialseed_e2e.utils import TemplateEngine

console = Console()


class CIConfig:
    """Represents CI/CD configuration (Data Class)."""

    def __init__(
        self,
        platform: str,
        templates: List[Tuple[str, str]],
    ):
        self.platform = platform
        self.templates = templates


class CITemplateGenerator:
    """Handles CI/CD template generation (Single Responsibility)."""

    CI_CONFIGS: Dict[str, CIConfig] = {
        "github": CIConfig(
            "github",
            [
                (
                    "ci-cd/github-actions/basic-workflow.yml.template",
                    ".github/workflows/e2e-basic.yml",
                ),
                (
                    "ci-cd/github-actions/parallel-workflow.yml.template",
                    ".github/workflows/e2e-parallel.yml",
                ),
                (
                    "ci-cd/github-actions/advanced-matrix-workflow.yml.template",
                    ".github/workflows/e2e-matrix.yml",
                ),
            ],
        ),
        "gitlab": CIConfig(
            "gitlab",
            [("ci-cd/gitlab-ci/gitlab-ci.yml.template", ".gitlab-ci.yml")],
        ),
        "jenkins": CIConfig(
            "jenkins",
            [("ci-cd/jenkins/Jenkinsfile.template", "Jenkinsfile")],
        ),
        "azure": CIConfig(
            "azure",
            [
                (
                    "ci-cd/azure-devops/azure-pipelines.yml.template",
                    "azure-pipelines.yml",
                )
            ],
        ),
        "circleci": CIConfig(
            "circleci",
            [("ci-cd/circleci/config.yml.template", ".circleci/config.yml")],
        ),
        "travis": CIConfig(
            "travis",
            [("ci-cd/travis/travis.yml.template", ".travis.yml")],
        ),
        "bitbucket": CIConfig(
            "bitbucket",
            [
                (
                    "ci-cd/bitbucket/bitbucket-pipelines.yml.template",
                    "bitbucket-pipelines.yml",
                )
            ],
        ),
        "aws": CIConfig(
            "aws",
            [("ci-cd/aws/codepipeline.yml.template", "aws-codepipeline.yml")],
        ),
    }

    def __init__(self, force: bool = False):
        self.force = force
        self.engine = TemplateEngine()

    def setup(self, platform: str) -> None:
        """Setup CI/CD templates for the specified platform."""
        platforms_to_setup = self._get_platforms(platform)

        for p in platforms_to_setup:
            self._generate_platform_templates(p)

    def _get_platforms(self, platform: str) -> List[str]:
        """Get list of platforms to setup."""
        if platform == "all":
            return list(self.CI_CONFIGS.keys())

        if platform not in self.CI_CONFIGS:
            console.print(f"[red]❌ Unknown platform:[/red] {platform}")
            console.print(f"Available: {', '.join(self.CI_CONFIGS.keys())}")
            sys.exit(1)

        return [platform]

    def _generate_platform_templates(self, platform: str) -> None:
        """Generate templates for a specific platform."""
        config = self.CI_CONFIGS[platform]
        console.print(f"📦 [bold cyan]{config.platform.upper()}[/bold cyan]")

        for template_path, output_path in config.templates:
            self._generate_template(template_path, output_path)

    def _generate_template(self, template_path: str, output_path: str) -> None:
        """Generate a single template file."""
        output = Path(output_path)

        try:
            self.engine.render_to_file(
                template_path, {}, str(output), overwrite=self.force
            )
            console.print(f"  [green]✓[/green] Generated: {output}")
        except FileExistsError:
            console.print(
                f"  [yellow]⚠[/yellow] Already exists: {output} (use --force to overwrite)"
            )
        except Exception as e:
            console.print(f"  [red]❌ Error generating {output}:[/red] {e}")


@click.command()
@click.argument("platform")
@click.option("--force", is_flag=True, help="Overwrite existing files")
def setup_ci_cmd(platform: str, force: bool):
    """Generate CI/CD pipeline templates for various platforms.

    Args:
        platform: Target platform (github, gitlab, jenkins, azure, circleci, travis, bitbucket, aws, all)

    Examples:
        e2e setup-ci github
        e2e setup-ci gitlab
        e2e setup-ci all
    """
    console.print(
        f"\n🚀 [bold cyan]Setting up CI/CD templates for:[/bold cyan] {platform}\n"
    )

    if not Path("e2e.conf").exists():
        console.print(
            "[red]❌ Error:[/red] e2e.conf not found. Are you in an E2E project?"
        )
        sys.exit(1)

    generator = CITemplateGenerator(force=force)
    generator.setup(platform)

    console.print(
        "\n[bold green]✅ CI/CD templates generated successfully![/bold green]\n"
    )


def get_setup_ci_command():
    """Get the setup-ci command for lazy loading."""
    return setup_ci_cmd


__all__ = ["setup_ci_cmd", "get_setup_ci_command"]
