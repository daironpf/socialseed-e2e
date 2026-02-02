# Pytest Configuration and Testing Guide

This document describes the pytest configuration for the socialseed-e2e framework and how to run different types of tests.

## Configuration Overview

The pytest configuration is defined in `pyproject.toml` under the `[tool.pytest.ini_options]` section.

### Test Discovery

- **Test paths**: `tests/`
- **Test files**: `test_*.py`
- **Test classes**: `Test*`
- **Test functions**: `test_*`

### Test Markers

We use markers to categorize tests for selective execution:

| Marker | Description | Example Usage |
|--------|-------------|---------------|
| `@pytest.mark.unit` | Fast, isolated unit tests | Testing individual functions |
| `@pytest.mark.integration` | Integration tests | Testing component interactions |
| `@pytest.mark.slow` | Tests that take significant time | Long-running operations |
| `@pytest.mark.cli` | CLI command tests | Testing CLI commands |
| `@pytest.mark.core` | Core framework tests | Testing framework internals |
| `@pytest.mark.e2e` | End-to-end tests | Full workflow tests |
| `@pytest.mark.mock_api` | Tests using mock API | Tests with Flask mock server |

### Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Run unit tests excluding slow ones
pytest -m "unit and not slow"

# Run multiple marker types
pytest -m "unit or cli"

# Run integration tests using mock API
pytest -m "integration and mock_api"
```

### Default Options

The following options are applied by default:
- `-v`: Verbose output
- `--tb=short`: Short traceback format
- `--strict-markers`: Fail on unknown markers

## Coverage Configuration

Coverage is configured in `pyproject.toml` with the following settings:

### Coverage Settings

- **Source**: `src/socialseed_e2e`
- **Omit**: Tests, cache, templates
- **Branch coverage**: Enabled
- **Minimum coverage**: 80%
- **HTML report**: `htmlcov/`

### Running Tests with Coverage

```bash
# Run all tests with coverage
pytest --cov=socialseed_e2e

# Run with coverage and generate HTML report
pytest --cov=socialseed_e2e --cov-report=html

# Run with coverage and generate XML report (for CI)
pytest --cov=socialseed_e2e --cov-report=xml

# Run with coverage and show missing lines
pytest --cov=socialseed_e2e --cov-report=term-missing

# Fail if coverage is below 80%
pytest --cov=socialseed_e2e --cov-fail-under=80
```

## Common Test Commands

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_validators.py

# Run specific test class
pytest tests/unit/test_validators.py::TestValidateUrl

# Run specific test method
pytest tests/unit/test_validators.py::TestValidateUrl::test_valid_https_url
```

### Running Test Suites

```bash
# Run all unit tests
pytest tests/unit/

# Run all integration tests
pytest tests/integration/

# Run CLI integration tests
pytest tests/integration/cli/

# Run mock API tests
pytest tests/integration/test_mock_api_integration.py
```

### Debugging Tests

```bash
# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Run with debugger on failure
pytest --pdb

# Show local variables in tracebacks
pytest -l

# Show full traceback
pytest --tb=long
```

### Parallel Test Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Run with 4 workers
pytest -n 4
```

## CI/CD Integration

### GitHub Actions

The project includes GitHub Actions workflow configured in `.github/workflows/ci.yml`:

```yaml
- name: Test with pytest
  run: pytest --cov=socialseed_e2e --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
```

### Coverage Reporting (codecov.io)

Coverage reports are automatically uploaded to codecov.io when tests run in CI.

To view coverage reports:
1. Visit: `https://codecov.io/gh/daironpf/socialseed-e2e`
2. View trends, file coverage, and diff coverage on PRs

## Test Organization

### Unit Tests (`tests/unit/`)

Tests for individual components in isolation:
- `test_base_page.py` - HTTP client tests
- `test_config_loader.py` - Configuration management tests
- `test_loaders.py` - Module loader tests
- `test_orchestrator.py` - Test orchestration tests
- `test_validators.py` - Validation helper tests
- `test_template_engine.py` - Template system tests
- `test_imports_compatibility.py` - Import system tests

All unit tests are marked with `@pytest.mark.unit`.

### Integration Tests (`tests/integration/`)

Tests for component interactions:
- `cli/` - CLI command integration tests
- `test_mock_api_integration.py` - Mock API integration tests

All integration tests are marked with `@pytest.mark.integration`.

## Fixtures

Common fixtures are defined in `tests/conftest.py`:

### Mock API Fixtures

- `mock_api_server` - Session-scoped running Flask server
- `mock_api_url` - Base URL string for mock API
- `mock_api_reset` - Function-scoped data reset
- `sample_user_data` - Sample user data for testing
- `admin_credentials` - Admin user credentials
- `user_credentials` - Regular user credentials

### CLI Fixtures

- `cli_runner` - Click test runner
- `temp_dir` - Temporary directory for CLI tests

## Writing Tests

### Unit Test Example

```python
import pytest

pytestmark = pytest.mark.unit

def test_validate_url():
    """Test URL validation."""
    from socialseed_e2e.utils.validators import validate_url

    result = validate_url("https://api.example.com")
    assert result == "https://api.example.com"
```

### Integration Test Example

```python
import pytest

pytestmark = pytest.mark.integration

def test_cli_init(cli_runner, temp_dir):
    """Test CLI init command."""
    from socialseed_e2e.cli import cli

    result = cli_runner.invoke(cli, ['init', str(temp_dir)])
    assert result.exit_code == 0
    assert (temp_dir / "services").exists()
```

### Slow Test Example

```python
import pytest

@pytest.mark.slow
def test_long_running_operation():
    """Test that takes significant time."""
    import time
    time.sleep(5)
    assert True
```

## Best Practices

1. **Use markers**: Always mark tests with appropriate markers
2. **Keep unit tests fast**: Unit tests should run in milliseconds
3. **Use fixtures**: Leverage fixtures for setup/teardown
4. **Test docstrings**: Write clear docstrings explaining what the test verifies
5. **Coverage**: Aim for >80% coverage on new code
6. **CI first**: Ensure tests pass in CI before merging

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "marker not registered"
**Solution**: Add the marker to `pyproject.toml` in `[tool.pytest.ini_options].markers`

**Issue**: Coverage report shows 0%
**Solution**: Ensure `--cov=src/socialseed_e2e` points to the correct source directory

**Issue**: Mock API tests timeout
**Solution**: The mock API server may not have started. Check port availability (default: 8765)

**Issue**: Import errors in tests
**Solution**: Install package in editable mode: `pip install -e ".[dev]"`

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Codecov Documentation](https://docs.codecov.io/)
