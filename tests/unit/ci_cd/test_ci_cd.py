"""Tests for CI/CD Templates Module.

This module tests the CI/CD pipeline template features.
"""

import os
import tempfile

import pytest

from socialseed_e2e.ci_cd import (
    BaseCITemplate,
    CircleCITemplate,
    CITemplateGenerator,
    CITemplateSuite,
    GitHubActionsTemplate,
    GitLabCITemplate,
    JenkinsTemplate,
    KubernetesTemplate,
    PipelineConfig,
    Platform,
    AzureDevOpsTemplate,
)


class TestPipelineConfig:
    """Tests for PipelineConfig."""

    def test_initialization(self):
        """Test config initialization."""
        config = PipelineConfig()
        assert config.python_version == "3.11"
        assert config.parallel_workers == 4
        assert config.timeout_minutes == 30

    def test_custom_config(self):
        """Test custom configuration."""
        config = PipelineConfig(
            python_version="3.10",
            parallel_workers=8,
            timeout_minutes=60,
        )
        assert config.python_version == "3.10"
        assert config.parallel_workers == 8


class TestGitHubActionsTemplate:
    """Tests for GitHubActionsTemplate."""

    def test_generate(self):
        """Test workflow generation."""
        config = PipelineConfig(python_version="3.11")
        template = GitHubActionsTemplate(config)

        content = template.generate()
        assert "name: E2E Tests" in content
        assert "python-version: ['3.11']" in content
        assert "e2e run" in content

    def test_with_secrets(self):
        """Test workflow with secrets."""
        config = PipelineConfig(
            secrets=["API_KEY", "SECRET_TOKEN"],
        )
        template = GitHubActionsTemplate(config)

        content = template.generate()
        assert "API_KEY" in content
        assert "SECRET_TOKEN" in content


class TestGitLabCITemplate:
    """Tests for GitLabCITemplate."""

    def test_generate(self):
        """Test pipeline generation."""
        config = PipelineConfig()
        template = GitLabCITemplate(config)

        content = template.generate()
        assert "stages:" in content
        assert "e2e-tests:" in content
        assert "e2e run" in content


class TestJenkinsTemplate:
    """Tests for JenkinsTemplate."""

    def test_generate(self):
        """Test Jenkinsfile generation."""
        config = PipelineConfig()
        template = JenkinsTemplate(config)

        content = template.generate()
        assert "pipeline {" in content
        assert "e2e run" in content


class TestAzureDevOpsTemplate:
    """Tests for AzureDevOpsTemplate."""

    def test_generate(self):
        """Test Azure pipeline generation."""
        config = PipelineConfig()
        template = AzureDevOpsTemplate(config)

        content = template.generate()
        assert "trigger:" in content
        assert "e2e run" in content


class TestCircleCITemplate:
    """Tests for CircleCITemplate."""

    def test_generate(self):
        """Test CircleCI config generation."""
        config = PipelineConfig()
        template = CircleCITemplate(config)

        content = template.generate()
        assert "version: 2.1" in content
        assert "e2e-tests:" in content


class TestCITemplateGenerator:
    """Tests for CITemplateGenerator."""

    def test_generate_github_actions(self, tmp_path):
        """Test generating GitHub Actions template."""
        generator = CITemplateGenerator()
        config = PipelineConfig()

        output_path = tmp_path / "e2e-tests.yml"
        content = generator.generate(
            Platform.GITHUB_ACTIONS,
            config,
            str(output_path),
        )

        assert output_path.exists()
        assert "E2E Tests" in content

    def test_generate_all(self, tmp_path):
        """Test generating all templates."""
        generator = CITemplateGenerator()
        config = PipelineConfig()

        results = generator.generate_all(config, str(tmp_path))

        assert len(results) == 5
        assert Platform.GITHUB_ACTIONS in results


class TestKubernetesTemplate:
    """Tests for KubernetesTemplate."""

    def test_generate_test_job(self):
        """Test Kubernetes job generation."""
        template = KubernetesTemplate()

        yaml = template.generate_test_job(
            name="e2e-tests",
            image="python:3.11",
            command=["e2e", "run"],
        )

        assert "apiVersion: batch/v1" in yaml
        assert "kind: Job" in yaml
        assert "e2e-tests" in yaml

    def test_generate_cronjob(self):
        """Test Kubernetes CronJob generation."""
        template = KubernetesTemplate()

        yaml = template.generate_cronjob(
            name="scheduled-e2e",
            schedule="0 2 * * *",
            image="python:3.11",
            command=["e2e", "run"],
        )

        assert "kind: CronJob" in yaml
        assert "0 2 * * *" in yaml


class TestCITemplateSuite:
    """Tests for CITemplateSuite."""

    def test_initialization(self):
        """Test suite initialization."""
        suite = CITemplateSuite()
        assert suite.generator is not None
        assert suite.k8s is not None

    def test_generate_github_actions(self, tmp_path):
        """Test generating GitHub Actions."""
        suite = CITemplateSuite()
        os.chdir(tmp_path)

        path = suite.generate_github_actions()
        assert os.path.exists(path)

    def test_generate_gitlab_ci(self, tmp_path):
        """Test generating GitLab CI."""
        suite = CITemplateSuite()
        os.chdir(tmp_path)

        path = suite.generate_gitlab_ci()
        assert os.path.exists(path)

    def test_generate_kubernetes_job(self, tmp_path):
        """Test generating Kubernetes job."""
        suite = CITemplateSuite()
        os.chdir(tmp_path)

        path = suite.generate_kubernetes_job()
        assert os.path.exists(path)


class TestPlatform:
    """Tests for Platform enum."""

    def test_platforms(self):
        """Test platform values."""
        assert Platform.GITHUB_ACTIONS.value == "github_actions"
        assert Platform.GITLAB_CI.value == "gitlab_ci"
        assert Platform.JENKINS.value == "jenkins"
        assert Platform.AZURE_DEVOPS.value == "azure_devops"
        assert Platform.CIRCLECI.value == "circleci"
