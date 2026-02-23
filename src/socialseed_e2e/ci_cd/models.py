"""
Models for CI/CD pipeline templates.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Platform(str, Enum):
    """Supported CI/CD platforms."""

    GITHUB_ACTIONS = "github"
    GITLAB_CI = "gitlab"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure"
    KUBERNETES = "kubernetes"


class TemplateType(str, Enum):
    """Types of pipeline templates."""

    BASIC = "basic"
    MATRIX = "matrix"
    PARALLEL = "parallel"
    ENTERPRISE = "enterprise"
    NIGHTLY = "nightly"
    PR_VALIDATION = "pr_validation"
    RELEASE = "release"


class TestEnvironment(BaseModel):
    """Test environment configuration."""

    name: str = Field(..., description="Environment name")
    python_version: str = Field(default="3.11", description="Python version")
    os: str = Field(default="ubuntu-latest", description="Operating system")
    services: List[str] = Field(default_factory=list, description="Required services")
    variables: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )


class PipelineStage(BaseModel):
    """Pipeline stage configuration."""

    name: str = Field(..., description="Stage name")
    commands: List[str] = Field(default_factory=list, description="Stage commands")
    depends_on: List[str] = Field(default_factory=list, description="Dependencies")
    artifacts: List[str] = Field(default_factory=list, description="Artifact paths")
    timeout_minutes: int = Field(default=30, description="Timeout in minutes")
    parallel_jobs: int = Field(default=1, description="Number of parallel jobs")


class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""

    platform: Platform = Field(..., description="CI/CD platform")
    template_type: TemplateType = Field(
        default=TemplateType.BASIC, description="Template type"
    )
    project_name: str = Field(..., description="Project name")
    python_versions: List[str] = Field(
        default_factory=lambda: ["3.9", "3.10", "3.11"],
        description="Python versions to test",
    )
    os_list: List[str] = Field(
        default_factory=lambda: ["ubuntu-latest"], description="Operating systems"
    )

    # Test configuration
    test_markers: List[str] = Field(default_factory=list, description="pytest markers")
    coverage_threshold: int = Field(
        default=80, description="Coverage threshold percentage"
    )
    fail_fast: bool = Field(default=False, description="Fail fast on first error")

    # Services
    needs_database: bool = Field(default=False, description="Requires database")
    needs_cache: bool = Field(default=True, description="Use caching")

    # Notifications
    slack_webhook: Optional[str] = Field(default=None, description="Slack webhook URL")
    email_notifications: bool = Field(
        default=False, description="Enable email notifications"
    )

    # Security
    secrets: List[str] = Field(default_factory=list, description="Required secrets")

    # Advanced
    stages: List[PipelineStage] = Field(
        default_factory=list, description="Custom stages"
    )
    environments: List[TestEnvironment] = Field(
        default_factory=list, description="Test environments"
    )

    model_config = {"populate_by_name": True}
