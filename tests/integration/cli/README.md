# CLI Integration Tests

This directory contains integration tests for the socialseed-e2e CLI commands.
The tests have been organized into separate files by command/functionality for better maintainability.

## Structure

```
tests/integration/cli/
├── __init__.py              # Package initialization with module documentation
├── conftest.py              # Shared fixtures for all CLI tests
├── test_init.py             # Tests for 'e2e init' command
├── test_new_service.py      # Tests for 'e2e new-service' command
├── test_new_test.py         # Tests for 'e2e new-test' command
├── test_run.py              # Tests for 'e2e run' command
├── test_doctor.py           # Tests for 'e2e doctor' command
├── test_config.py           # Tests for 'e2e config' command
├── test_error_handling.py   # Tests for CLI error handling
└── test_workflows.py        # End-to-end workflow tests
```

## Test Organization

### By Command (7 files)
Each CLI command has its own dedicated test file:

- **test_init.py** (7 tests): Tests project initialization
  - Directory structure creation
  - e2e.conf file creation
  - .gitignore creation
  - Force flag behavior
  - Success messages

- **test_new_service.py** (7 tests): Tests service creation
  - File structure creation
  - Service page generation
  - Config file creation
  - Data schema creation
  - e2e.conf updates

- **test_new_test.py** (5 tests): Tests test module creation
  - Test file creation
  - Automatic numbering
  - File content verification
  - Error cases

- **test_run.py** (5 tests): Tests test execution command
  - Configuration display
  - Environment display
  - Services table
  - Filter options

- **test_doctor.py** (5 tests): Tests system check command
  - System verification
  - Python version check
  - Playwright check
  - Status reporting

- **test_config.py** (5 tests): Tests configuration display
  - Config display
  - Environment info
  - Timeout settings
  - Services table

### By Functionality (2 files)

- **test_error_handling.py** (5 tests): Cross-cutting error handling tests
  - Invalid commands
  - Missing arguments
  - CLI version
  - CLI help

- **test_workflows.py** (3 tests): End-to-end integration tests
  - Complete project setup
  - Multiple services
  - Project recreation

## Shared Resources

### Fixtures (conftest.py)

All test files use fixtures defined in `conftest.py`:

- `cli_runner`: Provides a Click CliRunner instance
- `temp_dir`: Provides a temporary directory
- `isolated_cli_runner`: Changes to temp directory for isolation
- `initialized_project`: Pre-initialized project fixture
- `project_with_service`: Project with a service already created

### Running Tests

Run all CLI tests:
```bash
pytest tests/integration/cli/
```

Run tests for specific command:
```bash
pytest tests/integration/cli/test_init.py
pytest tests/integration/cli/test_new_service.py
# etc.
```

Run with verbose output:
```bash
pytest tests/integration/cli/ -v
```

## Benefits of This Organization

1. **Single Responsibility**: Each file tests one command or aspect
2. **Easier Navigation**: Find tests quickly by command name
3. **Better Maintainability**: Changes to one command don't affect others
4. **Parallel Development**: Multiple developers can work on different commands
5. **Clearer Failures**: Test failures immediately indicate which command has issues
6. **Faster Feedback**: Run only relevant tests during development

## Total Coverage

- **40 tests passing**
- **2 tests skipped** (intentionally skipped edge cases)
- All major CLI commands covered
- End-to-end workflows tested
- Error cases handled

## Notes

- Tests use `isolated_cli_runner` fixture to ensure directory isolation
- Fixtures from conftest.py are automatically available to all test files
- Each test file is self-contained with its own docstrings and imports
