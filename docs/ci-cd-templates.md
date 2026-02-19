# CI/CD Pipeline Templates

Enterprise-grade CI/CD pipeline templates for socialseed-e2e testing framework.

## Overview

This module provides production-ready templates for:

- **GitHub Actions** - Matrix testing, parallel execution, artifact management
- **GitLab CI** - Multi-stage pipelines, Docker integration, caching
- **Jenkins** - Shared libraries, pipeline-as-code, distributed builds
- **Azure DevOps** - YAML pipelines, service connections, deployment groups
- **Kubernetes** - Native testing jobs, CronJobs, resource management

## Quick Start

### Python API

```python
from socialseed_e2e.ci_cd import TemplateManager, PipelineConfig, Platform, TemplateType

# Create manager
manager = TemplateManager()

# Configure pipeline
config = PipelineConfig(
    platform=Platform.GITHUB_ACTIONS,
    template_type=TemplateType.MATRIX,
    project_name="my-api-tests",
    python_versions=["3.9", "3.10", "3.11"],
    os_list=["ubuntu-latest", "windows-latest", "macos-latest"],
    coverage_threshold=80,
)

# Generate pipeline
manager.generate(config, ".github/workflows/e2e-tests.yml")
```

### CLI Usage

```bash
# Generate GitHub Actions workflow
e2e setup-ci github --python 3.11 --template matrix

# Generate all CI configurations
e2e setup-ci all --python 3.11

# Generate with custom configuration
e2e setup-ci gitlab --python 3.9,3.10,3.11 --coverage-threshold 85
```

## Template Types

### Basic
Simple, single-environment testing suitable for small projects.

### Matrix
Multi-environment testing across Python versions and operating systems.

**Features:**
- Parallel testing across Python 3.9, 3.10, 3.11
- Cross-platform testing (Ubuntu, Windows, macOS)
- Coverage reporting per environment
- Artifact collection

### Parallel
Test file splitting for faster execution.

**Features:**
- Automatic test discovery and splitting
- Configurable parallel workers
- Distributed test execution

### Enterprise
Comprehensive testing with security scanning and deployment stages.

**Features:**
- Linting (black, flake8, mypy)
- Security scanning (bandit, safety)
- Multi-stage testing (unit, integration, e2e)
- Deployment to staging/production
- Slack/email notifications
- Coverage gates

### Nightly
Scheduled comprehensive testing.

**Features:**
- Daily scheduled execution
- Full test suite
- Extended timeout
- Comprehensive reporting

## Platform-Specific Features

### GitHub Actions

- **Matrix Strategy**: Test across multiple Python versions and OS
- **Artifact Management**: Automatic test result collection
- **Caching**: pip cache for faster builds
- **Concurrency Control**: Cancel in-progress runs
- **Secret Management**: Environment variable injection
- **Slack Integration**: Build notifications

### GitLab CI

- **Parallel Matrix**: Python version × OS matrix
- **Multi-Stage Pipelines**: build → test → report → deploy
- **Docker Integration**: Container-based testing
- **Caching**: pip and venv caching
- **Artifacts**: Test results and coverage reports
- **Environments**: Staging and production deployment
- **Rules**: Conditional job execution

### Jenkins

- **Pipeline as Code**: Jenkinsfile-based configuration
- **Matrix Builds**: Cross-platform testing
- **Shared Libraries**: Reusable pipeline components
- **Distributed Builds**: Agent-based execution
- **Plugins**: HTML publisher, JUnit, Coverage
- **Notifications**: Email and Slack

### Azure DevOps

- **YAML Pipelines**: Version-controlled configuration
- **Matrix Strategy**: Parallel testing
- **Service Connections**: Secure secret management
- **Deployment Groups**: Environment-based deployment
- **Artifacts**: Test results and coverage
- **Gates**: Quality gates before deployment

### Kubernetes

- **Jobs**: On-demand test execution
- **CronJobs**: Scheduled testing
- **Resource Management**: CPU/memory limits
- **Parallel Execution**: Indexed jobs for test splitting
- **ConfigMaps**: Configuration management
- **Secrets**: Secure credential storage
- **RBAC**: Role-based access control

## Configuration Options

### PipelineConfig

```python
PipelineConfig(
    # Required
    platform=Platform.GITHUB_ACTIONS,
    project_name="my-project",
    
    # Testing
    python_versions=["3.9", "3.10", "3.11"],
    os_list=["ubuntu-latest"],
    test_markers=["e2e", "integration"],
    coverage_threshold=80,
    fail_fast=False,
    
    # Services
    needs_database=False,
    needs_cache=True,
    
    # Notifications
    slack_webhook="https://hooks.slack.com/...",
    email_notifications=True,
    
    # Security
    secrets=["API_KEY", "DB_PASSWORD"],
    
    # Timing
    timeout_minutes=30,
)
```

## Best Practices

### 1. Use Matrix Testing

Test across multiple Python versions and OS to ensure compatibility:

```python
config = PipelineConfig(
    template_type=TemplateType.MATRIX,
    python_versions=["3.9", "3.10", "3.11"],
    os_list=["ubuntu-latest", "windows-latest"],
)
```

### 2. Enable Caching

Speed up builds with pip caching:

```python
config = PipelineConfig(
    needs_cache=True,
)
```

### 3. Set Coverage Gates

Enforce code quality with coverage thresholds:

```python
config = PipelineConfig(
    coverage_threshold=85,
)
```

### 4. Use Secrets for Credentials

Never hardcode credentials in pipeline files:

```python
config = PipelineConfig(
    secrets=["API_KEY", "DB_PASSWORD", "SLACK_WEBHOOK"],
)
```

### 5. Parallelize Tests

Split tests across multiple jobs for faster execution:

```python
config = PipelineConfig(
    template_type=TemplateType.PARALLEL,
    parallel_workers=4,
)
```

### 6. Multi-Stage Pipelines

Use enterprise template for comprehensive testing:

```python
config = PipelineConfig(
    template_type=TemplateType.ENTERPRISE,
)
```

## Migration Guides

### From Existing CI

To migrate from an existing CI configuration:

1. Run `e2e setup-ci <platform> --dry-run` to preview
2. Review the generated configuration
3. Copy secrets from old configuration
4. Update environment variables
5. Test in a feature branch
6. Switch over once validated

### Platform Switching

Switching between platforms is easy:

```python
# Generate for GitHub Actions
config.platform = Platform.GITHUB_ACTIONS
manager.generate(config, ".github/workflows/e2e.yml")

# Generate for GitLab CI
config.platform = Platform.GITLAB_CI
manager.generate(config, ".gitlab-ci.yml")
```

## Examples

### E-Commerce API Testing

```python
config = PipelineConfig(
    platform=Platform.GITHUB_ACTIONS,
    template_type=TemplateType.ENTERPRISE,
    project_name="ecommerce-api-tests",
    python_versions=["3.10", "3.11"],
    coverage_threshold=85,
    needs_database=True,
    secrets=["STRIPE_API_KEY", "DB_PASSWORD"],
    slack_webhook="${{ secrets.SLACK_WEBHOOK }}",
)
```

### Microservices Testing

```python
config = PipelineConfig(
    platform=Platform.KUBERNETES,
    template_type=TemplateType.MATRIX,
    project_name="microservices-e2e",
    python_versions=["3.11"],
    parallel_workers=5,
)
```

### Banking API (High Security)

```python
config = PipelineConfig(
    platform=Platform.GITLAB_CI,
    template_type=TemplateType.ENTERPRISE,
    project_name="banking-api-tests",
    coverage_threshold=95,
    secrets=["API_KEY", "CERTIFICATE", "DB_PASSWORD"],
)
```

## Troubleshooting

### Builds are slow

- Enable caching: `needs_cache=True`
- Use parallel testing: `template_type=TemplateType.PARALLEL`
- Split tests into smaller files

### Coverage not reported

- Ensure `pytest-cov` is installed
- Check artifact paths in configuration
- Verify coverage file generation

### Secrets not available

- Add secrets to `PipelineConfig.secrets`
- Configure secrets in CI platform
- Use environment-specific secrets

### Tests timeout

- Increase timeout: `timeout_minutes=60`
- Split tests into multiple jobs
- Optimize test execution time

## Advanced Usage

### Custom Templates

Create custom Jinja2 templates:

```python
manager = TemplateManager(templates_dir="/path/to/custom/templates")
manager.generate(config, output_path, template_name="custom/template.yml.j2")
```

### Multi-Platform Generation

Generate all configurations at once:

```python
results = manager.generate_all(config, base_dir="./ci")
# Returns: {Platform.GITHUB_ACTIONS: "./ci/.github/workflows/e2e-tests.yml", ...}
```

### Validation

Validate configuration before generation:

```python
errors = manager.validate_config(config)
if errors:
    print("Validation errors:", errors)
else:
    manager.generate(config, output_path)
```

## Integration with Other Features

### AI Orchestrator

Combine with AI test generation:

```bash
# Generate tests and CI configuration
e2e plan-strategy --generate-tests
e2e setup-ci github --template enterprise
```

### Performance Testing

Include performance tests in CI:

```python
config = PipelineConfig(
    test_markers=["e2e", "performance"],
    timeout_minutes=60,
)
```

### Contract Testing

Validate contracts in CI:

```bash
e2e contract-verify --pact-broker https://pact.example.com
```

## Support

For issues or questions:

- GitHub Issues: https://github.com/daironpf/socialseed-e2e/issues
- Documentation: https://socialseed-e2e.readthedocs.io
- Community: https://github.com/daironpf/socialseed-e2e/discussions
