"""CI/CD Pipeline Templates Module.

This module provides enterprise-grade CI/CD pipeline templates:
- GitHub Actions workflows
- GitLab CI pipelines
- Jenkins pipelines
- Azure DevOps pipelines
- Kubernetes-native testing

Usage:
    from socialseed_e2e.ci_cd import (
        GitHubActionsTemplate,
        GitLabCITemplate,
        JenkinsTemplate,
    )
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Platform(str, Enum):
    """CI/CD platforms."""

    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure_devops"
    CIRCLECI = "circleci"


@dataclass
class PipelineConfig:
    """CI/CD pipeline configuration."""

    python_version: str = "3.11"
    test_command: str = "e2e run"
    parallel_workers: int = 4
    timeout_minutes: int = 30
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    notifications: Dict[str, Any] = field(default_factory=dict)


class BaseCITemplate:
    """Base class for CI templates."""

    def __init__(self, config: PipelineConfig):
        self.config = config

    def generate(self) -> str:
        """Generate pipeline configuration."""
        raise NotImplementedError

    def save(self, filepath: str):
        """Save configuration to file."""
        content = self.generate()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)


class GitHubActionsTemplate(BaseCITemplate):
    """GitHub Actions workflow template.

    Example:
        config = PipelineConfig(
            python_version="3.11",
            parallel_workers=4,
        )
        template = GitHubActionsTemplate(config)
        template.save(".github/workflows/e2e-tests.yml")
    """

    def generate(self) -> str:
        """Generate GitHub Actions workflow."""
        env_vars = "\n".join(
            f"          {k}: ${{{{ secrets.{k} }}}}" for k in self.config.secrets
        )

        artifacts = ""
        if self.config.artifacts:
            artifacts = """
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: |
""" + "\n".join(f"            {a}" for a in self.config.artifacts)

        return f"""name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run daily at 2 AM
    - cron: '0 2 * * *'

concurrency:
  group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: {self.config.timeout_minutes}

    strategy:
      matrix:
        python-version: ['{self.config.python_version}']
      fail-fast: false

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{{{ matrix.python-version }}}}
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ matrix.python-version }}}}

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements.txt') }}}}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e .

      - name: Run E2E tests
        run: {self.config.test_command}
        env:{env_vars}
{artifacts}

      - name: Upload coverage to Codecov
        if: always()
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
"""


class GitLabCITemplate(BaseCITemplate):
    """GitLab CI pipeline template.

    Example:
        config = PipelineConfig(parallel_workers=4)
        template = GitLabCITemplate(config)
        template.save(".gitlab-ci.yml")
    """

    def generate(self) -> str:
        """Generate GitLab CI configuration."""
        env_vars = "\n".join(
            f"    {k}: ${k}" for k in self.config.environment_variables
        )

        artifacts_section = ""
        if self.config.artifacts:
            artifacts_section = (
                """
  artifacts:
    when: always
    paths:
"""
                + "\n".join(f"      - {a}" for a in self.config.artifacts)
                + """
    reports:
      junit: report.xml
"""
            )

        return f"""stages:
  - test
  - report

variables:
  PYTHON_VERSION: "{self.config.python_version}"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
{env_vars}

cache:
  paths:
    - .cache/pip/
    - venv/

e2e-tests:
  stage: test
  image: python:${{PYTHON_VERSION}}
  timeout: {self.config.timeout_minutes} minutes
  parallel:
    matrix:
      - PYTHON_VERSION: [{self.config.python_version}]

  before_script:
    - python -m venv venv
    - source venv/bin/activate
    - pip install --upgrade pip
    - pip install -r requirements.txt
    - pip install -e .

  script:
    - {self.config.test_command}
{artifacts_section}

  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"
"""


class JenkinsTemplate(BaseCITemplate):
    """Jenkins pipeline template.

    Example:
        config = PipelineConfig()
        template = JenkinsTemplate(config)
        template.save("Jenkinsfile")
    """

    def generate(self) -> str:
        """Generate Jenkins pipeline."""
        env_vars = "\n".join(
            f"        {k} = credentials('{k}')" for k in self.config.secrets
        )

        artifacts_section = ""
        if self.config.artifacts:
            artifacts_section = (
                """
        always {
            script {
                def artifacts = '''
"""
                + "\n".join(f"                {a}" for a in self.config.artifacts)
                + """
                '''
                artifacts.eachLine { line ->
                    if (line.trim()) {
                        archiveArtifacts artifacts: line.trim(), allowEmptyArchive: true
                    }
                }
            }
        }
"""
            )

        return f"""pipeline {{
    agent {{
        docker {{
            image 'python:{self.config.python_version}-slim'
            args '-u root'
        }}
    }}

    options {{
        timeout(time: {self.config.timeout_minutes}, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }}

    environment {{
{env_vars}
    }}

    stages {{
        stage('Install Dependencies') {{
            steps {{
                sh '''
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -e .
                '''
            }}
        }}

        stage('Run E2E Tests') {{
            steps {{
                sh '{self.config.test_command}'
            }}
        }}
    }}

    post {{
{artifacts_section}
        failure {{
            emailext (
                subject: "E2E Tests Failed: ${{env.JOB_NAME}} - ${{env.BUILD_NUMBER}}",
                body: "E2E tests failed. Check console output.",
                to: "${{env.CHANGE_AUTHOR_EMAIL}}"
            )
        }}
    }}
}}
"""


class AzureDevOpsTemplate(BaseCITemplate):
    """Azure DevOps pipeline template.

    Example:
        config = PipelineConfig()
        template = AzureDevOpsTemplate(config)
        template.save("azure-pipelines.yml")
    """

    def generate(self) -> str:
        """Generate Azure DevOps pipeline."""
        env_vars = "\n".join(
            f"    {k}: $({k})" for k in self.config.environment_variables
        )

        return f"""trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '{self.config.python_version}'
{env_vars}

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(pythonVersion)'
  displayName: 'Use Python $(pythonVersion)'

- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
  displayName: 'Install dependencies'

- script: |
    {self.config.test_command}
  displayName: 'Run E2E tests'
  timeoutInMinutes: {self.config.timeout_minutes}

- task: PublishTestResults@2
  condition: succeededOrFailed()
  inputs:
    testResultsFiles: '**/test-results.xml'
    testRunTitle: 'E2E Tests'

- task: PublishCodeCoverageResults@1
  condition: succeededOrFailed()
  inputs:
    codeCoverageTool: Cobertura
    summaryFileLocation: '**/coverage.xml'
"""


class CircleCITemplate(BaseCITemplate):
    """CircleCI configuration template.

    Example:
        config = PipelineConfig()
        template = CircleCITemplate(config)
        template.save(".circleci/config.yml")
    """

    def generate(self) -> str:
        """Generate CircleCI configuration."""
        return f"""version: 2.1

orbs:
  python: circleci/python@2.1.1

jobs:
  e2e-tests:
    docker:
      - image: cimg/python:{self.config.python_version}
    parallelism: {self.config.parallel_workers}
    resource_class: medium

    steps:
      - checkout

      - python/install-packages:
          pkg-manager: pip
          pip-dependency-file: requirements.txt

      - run:
          name: Run E2E tests
          command: {self.config.test_command}
          no_output_timeout: {self.config.timeout_minutes}m

      - store_test_results:
          path: test-results

      - store_artifacts:
          path: test-results
          destination: test-results

workflows:
  version: 2
  test:
    jobs:
      - e2e-tests:
          filters:
            branches:
              only:
                - main
                - develop
          context:
            - e2e-testing
"""


class CITemplateGenerator:
    """Generator for CI/CD templates.

    Example:
        generator = CITemplateGenerator()

        # Generate all templates
        generator.generate_all(
            platform=Platform.GITHUB_ACTIONS,
            config=PipelineConfig(),
            output_dir=".github/workflows"
        )
    """

    TEMPLATES = {
        Platform.GITHUB_ACTIONS: GitHubActionsTemplate,
        Platform.GITLAB_CI: GitLabCITemplate,
        Platform.JENKINS: JenkinsTemplate,
        Platform.AZURE_DEVOPS: AzureDevOpsTemplate,
        Platform.CIRCLECI: CircleCITemplate,
    }

    def generate(
        self,
        platform: Platform,
        config: PipelineConfig,
        output_path: str,
    ) -> str:
        """Generate template for specific platform.

        Args:
            platform: CI/CD platform
            config: Pipeline configuration
            output_path: Output file path

        Returns:
            Generated content
        """
        template_class = self.TEMPLATES.get(platform)
        if not template_class:
            raise ValueError(f"Unsupported platform: {platform}")

        template = template_class(config)
        content = template.generate()

        # Save to file
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)

        return content

    def generate_all(
        self,
        config: PipelineConfig,
        base_dir: str = ".",
    ) -> Dict[Platform, str]:
        """Generate templates for all platforms.

        Args:
            config: Pipeline configuration
            base_dir: Base directory for output

        Returns:
            Dictionary mapping platforms to file paths
        """
        output_paths = {
            Platform.GITHUB_ACTIONS: os.path.join(
                base_dir, ".github/workflows/e2e-tests.yml"
            ),
            Platform.GITLAB_CI: os.path.join(base_dir, ".gitlab-ci.yml"),
            Platform.JENKINS: os.path.join(base_dir, "Jenkinsfile"),
            Platform.AZURE_DEVOPS: os.path.join(base_dir, "azure-pipelines.yml"),
            Platform.CIRCLECI: os.path.join(base_dir, ".circleci/config.yml"),
        }

        results = {}
        for platform, path in output_paths.items():
            self.generate(platform, config, path)
            results[platform] = path

        return results


class KubernetesTemplate:
    """Kubernetes-native testing template.

    Example:
        template = KubernetesTemplate()
        template.generate_test_job(
            name="e2e-tests",
            image="python:3.11",
            command=["e2e", "run"],
        )
    """

    def generate_test_job(
        self,
        name: str,
        image: str,
        command: List[str],
        namespace: str = "default",
        parallel: int = 1,
    ) -> str:
        """Generate Kubernetes Job for testing.

        Args:
            name: Job name
            image: Container image
            command: Command to run
            namespace: Kubernetes namespace
            parallel: Number of parallel pods

        Returns:
            Kubernetes YAML
        """
        cmd_str = " ".join(command)

        return f"""apiVersion: batch/v1
kind: Job
metadata:
  name: {name}
  namespace: {namespace}
spec:
  parallelism: {parallel}
  completions: {parallel}
  template:
    spec:
      containers:
      - name: e2e-tests
        image: {image}
        command:
        - /bin/sh
        - -c
        - |
          pip install -r requirements.txt
          pip install -e .
          {cmd_str}
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        volumeMounts:
        - name: test-results
          mountPath: /results
      volumes:
      - name: test-results
        emptyDir: {{}}
      restartPolicy: Never
  backoffLimit: 1
"""

    def generate_cronjob(
        self,
        name: str,
        schedule: str,
        image: str,
        command: List[str],
        namespace: str = "default",
    ) -> str:
        """Generate Kubernetes CronJob for scheduled testing.

        Args:
            name: CronJob name
            schedule: Cron schedule expression
            image: Container image
            command: Command to run
            namespace: Kubernetes namespace

        Returns:
            Kubernetes YAML
        """
        cmd_str = " ".join(command)

        return f"""apiVersion: batch/v1
kind: CronJob
metadata:
  name: {name}
  namespace: {namespace}
spec:
  schedule: "{schedule}"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: e2e-tests
            image: {image}
            command:
            - /bin/sh
            - -c
            - |
              pip install -r requirements.txt
              pip install -e .
              {cmd_str}
            resources:
              requests:
                memory: "512Mi"
                cpu: "500m"
          restartPolicy: OnFailure
"""


class CITemplateSuite:
    """Comprehensive CI/CD template suite.

    Example:
        suite = CITemplateSuite()

        # Generate GitHub Actions workflow
        suite.generate_github_actions(
            python_version="3.11",
            parallel=4,
        )

        # Generate all templates
        suite.generate_all_templates()
    """

    def __init__(self):
        """Initialize CI template suite."""
        self.generator = CITemplateGenerator()
        self.k8s = KubernetesTemplate()

    def generate_github_actions(
        self,
        python_version: str = "3.11",
        parallel: int = 4,
        output_dir: str = ".github/workflows",
    ) -> str:
        """Generate GitHub Actions workflow.

        Args:
            python_version: Python version
            parallel: Parallel workers
            output_dir: Output directory

        Returns:
            File path
        """
        config = PipelineConfig(
            python_version=python_version,
            parallel_workers=parallel,
        )
        path = os.path.join(output_dir, "e2e-tests.yml")
        return self.generator.generate(Platform.GITHUB_ACTIONS, config, path)

    def generate_gitlab_ci(
        self,
        python_version: str = "3.11",
        output_path: str = ".gitlab-ci.yml",
    ) -> str:
        """Generate GitLab CI configuration.

        Args:
            python_version: Python version
            output_path: Output file path

        Returns:
            File path
        """
        config = PipelineConfig(python_version=python_version)
        return self.generator.generate(Platform.GITLAB_CI, config, output_path)

    def generate_jenkins(
        self,
        output_path: str = "Jenkinsfile",
    ) -> str:
        """Generate Jenkins pipeline.

        Args:
            output_path: Output file path

        Returns:
            File path
        """
        config = PipelineConfig()
        return self.generator.generate(Platform.JENKINS, config, output_path)

    def generate_all_templates(
        self,
        python_version: str = "3.11",
        base_dir: str = ".",
    ) -> Dict[Platform, str]:
        """Generate all CI/CD templates.

        Args:
            python_version: Python version
            base_dir: Base directory

        Returns:
            Dictionary of generated files
        """
        config = PipelineConfig(python_version=python_version)
        return self.generator.generate_all(config, base_dir)

    def generate_kubernetes_job(
        self,
        name: str = "e2e-tests",
        image: str = "python:3.11",
        output_path: str = "k8s-test-job.yaml",
    ) -> str:
        """Generate Kubernetes test job.

        Args:
            name: Job name
            image: Container image
            output_path: Output file path

        Returns:
            File path
        """
        yaml = self.k8s.generate_test_job(
            name=name,
            image=image,
            command=["e2e", "run"],
        )

        with open(output_path, "w") as f:
            f.write(yaml)

        return output_path
