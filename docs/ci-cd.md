# CI/CD Integration Guide

socialseed-e2e is designed to be CI-native, providing ready-to-use templates for all major platforms. This guide explains how to set up and customize your CI/CD pipelines.

## Automatic Setup

The easiest way to integrate socialseed-e2e into your CI/CD pipeline is using the `setup-ci` command:

```bash
e2e setup-ci <platform> [--force]
```

### Supported Platforms

- `github`: Generates GitHub Actions workflows in `.github/workflows/`
- `gitlab`: Generates `.gitlab-ci.yml`
- `jenkins`: Generates a `Jenkinsfile`
- `azure`: Generates `azure-pipelines.yml`
- `circleci`: Generates `.circleci/config.yml`
- `travis`: Generates `.travis.yml`
- `bitbucket`: Generates `bitbucket-pipelines.yml`
- `all`: Generates templates for all of the above

## GitHub Actions Workflows

When you run `e2e setup-ci github`, three workflows are created:

1.  **e2e-basic.yml**: A simple workflow that runs all tests on every push and pull request.
2.  **e2e-parallel.yml**: Uses the framework's built-in parallel execution (`--parallel auto`).
3.  **e2e-matrix.yml** (Recommended for Microservices):
    *   **Dynamic Discovery**: Automatically detects services in your project.
    *   **Matrix Strategy**: Creates a separate job for each service, running them in isolation.
    *   **Reporting**: Aggregates results and uploads artifacts for each service.

## Key Features in Templates

### 1. Smart Caching
All templates include caching for `pip` and Playwright browsers to significantly reduce execution time.

### 2. Artifact Management
Templates are pre-configured to save the `.e2e/reports/` directory as a build artifact. This allows you to view the HTML test report directly from your CI platform.

### 3. Parallel Execution
The templates utilize the framework's parallel capabilities:
- `--parallel auto`: Uses all available CPU cores.
- `--parallel-mode test`: Runs individual test modules in parallel (best for large test suites).
- `--parallel-mode service`: Runs different services in parallel.

### 4. Headless Execution
socialseed-e2e and Playwright are configured to run headlessly by default in these templates, making them compatible with standard CI runners (Ubuntu, Debian, etc.).

## Customizing Your Pipeline

### Environment Variables
Most CI systems allow you to define secrets. You can pass these to your tests via environment variables in the workflow files:

```yaml
# Example in GitHub Actions
- name: Run E2E Tests
  run: e2e run
  env:
    API_KEY: ${{ secrets.API_KEY }}
    BASE_URL: https://staging.api.example.com
```

### Notifications
The templates include placeholders for Slack or Teams notifications. For GitHub Actions, we include a step using `8398a7/action-slack` which requires a `SLACK_WEBHOOK_URL` secret.

## Best Practices

1.  **Use isolation**: Leverage the Matrix strategy for microservice architectures to pinpoint which service failed.
2.  **Retain artifacts**: Keep test reports for at least 30 days to debug intermittent failures.
3.  **Schedule runs**: Use the `schedule` trigger (cron) in `e2e-matrix.yml` to run full regression suites daily.
4.  **Health checks**: Ensure your services are up before running tests. The framework handles this if `health_endpoint` is configured in `e2e.conf`.
