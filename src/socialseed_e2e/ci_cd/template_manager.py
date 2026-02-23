"""
Template Manager for CI/CD pipeline generation.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from .models import PipelineConfig, Platform, TemplateType


class TemplateManager:
    """Manager for CI/CD pipeline templates.

    Generates enterprise-grade CI/CD configurations for multiple platforms
    with support for matrix testing, artifact management, and secret handling.

    Example:
        manager = TemplateManager()

        # Generate GitHub Actions with matrix testing
        config = PipelineConfig(
            platform=Platform.GITHUB_ACTIONS,
            template_type=TemplateType.MATRIX,
            python_versions=["3.9", "3.10", "3.11"],
            os_list=["ubuntu-latest", "windows-latest", "macos-latest"],
        )
        manager.generate(config, output_path=".github/workflows/e2e-matrix.yml")
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """Initialize template manager.

        Args:
            templates_dir: Directory containing templates. If None, uses built-in templates.
        """
        if templates_dir:
            self.env = Environment(loader=FileSystemLoader(templates_dir))
        else:
            # Use built-in templates
            builtin_dir = Path(__file__).parent / "templates"
            self.env = Environment(loader=FileSystemLoader(str(builtin_dir)))

    def generate(
        self,
        config: PipelineConfig,
        output_path: str,
        template_name: Optional[str] = None,
    ) -> str:
        """Generate pipeline configuration.

        Args:
            config: Pipeline configuration
            output_path: Output file path
            template_name: Specific template name. If None, uses default for platform.

        Returns:
            Generated configuration content
        """
        if template_name is None:
            template_name = (
                f"{config.platform.value}/{config.template_type.value}.yml.j2"
            )

        template = self.env.get_template(template_name)
        content = template.render(config=config)

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Write to file
        with open(output_path, "w") as f:
            f.write(content)

        return content

    def generate_all(
        self, config: PipelineConfig, base_dir: str = "."
    ) -> Dict[Platform, str]:
        """Generate configurations for all platforms.

        Args:
            config: Base configuration (platform will be overridden)
            base_dir: Base directory for output

        Returns:
            Dictionary mapping platforms to output paths
        """
        outputs = {}

        for platform in Platform:
            platform_config = config.copy()
            platform_config.platform = platform

            output_paths = {
                Platform.GITHUB_ACTIONS: f"{base_dir}/.github/workflows/e2e-tests.yml",
                Platform.GITLAB_CI: f"{base_dir}/.gitlab-ci.yml",
                Platform.JENKINS: f"{base_dir}/Jenkinsfile",
                Platform.AZURE_DEVOPS: f"{base_dir}/azure-pipelines.yml",
                Platform.KUBERNETES: f"{base_dir}/k8s/e2e-tests.yaml",
            }

            output_path = output_paths[platform]
            self.generate(platform_config, output_path)
            outputs[platform] = output_path

        return outputs

    def list_templates(self, platform: Optional[Platform] = None) -> List[str]:
        """List available templates.

        Args:
            platform: Filter by platform

        Returns:
            List of template names
        """
        templates = []

        for p in Platform if platform is None else [platform]:
            platform_dir = Path(__file__).parent / "templates" / p.value
            if platform_dir.exists():
                for template in platform_dir.glob("*.yml.j2"):
                    templates.append(f"{p.value}/{template.name}")

        return sorted(templates)

    def validate_config(self, config: PipelineConfig) -> List[str]:
        """Validate pipeline configuration.

        Args:
            config: Pipeline configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not config.project_name:
            errors.append("project_name is required")

        if not config.python_versions:
            errors.append("At least one Python version is required")

        if config.coverage_threshold < 0 or config.coverage_threshold > 100:
            errors.append("coverage_threshold must be between 0 and 100")

        if config.template_type == TemplateType.MATRIX and len(config.os_list) < 1:
            errors.append("MATRIX template requires at least one OS")

        return errors
