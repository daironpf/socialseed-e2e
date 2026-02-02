# Contributing to socialseed-e2e

First off, thank you for considering contributing to socialseed-e2e! It's people like you that make this framework a great tool for the community.

This document provides guidelines and instructions for contributing to the project. We welcome contributions from both human developers and AI agents.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Contributing Code](#contributing-code)
- [Development Setup](#development-setup)
- [Code Style Guide](#code-style-guide)
- [Pull Request Process](#pull-request-process)
- [Commit Message Conventions](#commit-message-conventions)
- [AI Contributors](#ai-contributors)
- [Questions?](#questions)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please:

1. **Check existing issues** to see if the problem has already been reported
2. **Use the latest version** to verify the bug still exists
3. **Isolate the problem** to the smallest reproducible example

#### How to Submit a Good Bug Report

Bugs are tracked as [GitHub issues](https://github.com/daironpf/socialseed-e2e/issues). When creating a bug report, please include:

- **Use a clear and descriptive title** (e.g., "BasePage retry fails on 429 status code")
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** demonstrating the steps
- **Describe the behavior you observed** and what behavior you expected
- **Include code samples** and/or terminal output
- **Specify your environment**:
  - Python version: `python --version`
  - socialseed-e2e version: `pip show socialseed-e2e`
  - Operating system and version
  - Playwright version: `pip show playwright`

**Bug Report Template:**

```markdown
**Description:**
A clear description of the bug.

**Steps to Reproduce:**
1. Initialize project with 'e2e init'
2. Create service with 'e2e new-service test-api'
3. Run 'e2e run'
4. See error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened, including full error messages.

**Environment:**
- Python: 3.11.4
- socialseed-e2e: 0.1.0
- OS: Ubuntu 22.04
- Playwright: 1.40.0

**Additional Context:**
Add any other context about the problem here.
```

### Suggesting Features

Feature requests are welcome! When suggesting a feature:

1. **Check existing issues** to see if the feature has already been suggested
2. **Provide a clear use case** - explain why this feature would be useful
3. **Describe the solution** you'd like to see
4. **Consider alternatives** you've thought of

#### How to Submit a Feature Request

- **Use a clear and descriptive title** for the issue
- **Provide a detailed description** of the suggested feature
- **Explain why this feature would be useful** to most users
- **List some examples** of how the feature would be used
- **Note if you are willing to work on this feature** yourself

**Feature Request Template:**

```markdown
**Feature Description:**
A clear description of the feature you'd like to see.

**Use Case:**
Explain the scenario where this feature would be helpful.

**Proposed Solution:**
Describe how you think this should work.

**Alternatives Considered:**
Describe any alternative solutions you've considered.

**Additional Context:**
Add any other context or screenshots about the feature request.
```

### Contributing Code

#### Before You Start

1. **Check existing issues** or create a new one to discuss your proposed changes
2. **Fork the repository** and create a new branch for your changes
3. **Ensure your changes align** with the project's goals and architecture

#### Types of Contributions We Welcome

- 🐛 **Bug fixes** - Fix reported issues
- ✨ **New features** - Add functionality following our architecture
- 📝 **Documentation** - Improve docs, add examples, fix typos
- 🧪 **Tests** - Add test coverage for existing code
- 🔧 **Refactoring** - Improve code quality without changing behavior
- 🎨 **UI/UX improvements** - Enhance CLI output or user experience

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip or pipenv

### Setting Up Your Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/socialseed-e2e.git
   cd socialseed-e2e
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   playwright install chromium
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```
   This will automatically run code quality checks on each commit.

5. **Verify your setup:**
   ```bash
   e2e doctor
   pytest
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with coverage
pytest --cov=socialseed_e2e --cov-report=html

# Run specific test file
pytest tests/unit/test_base_page.py
```

### Code Quality Tools

We use several tools to maintain code quality. These are automatically run as **pre-commit hooks** on every commit, ensuring code quality before changes are submitted.

#### Pre-commit Hooks (Automatic)

Once you run `pre-commit install`, the following checks run automatically on each commit:

- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML syntax
- **check-json**: Validates JSON syntax
- **check-toml**: Validates TOML syntax
- **check-merge-conflict**: Prevents merge conflict markers from being committed
- **check-added-large-files**: Prevents large files from being committed
- **black**: Formats Python code
- **isort**: Sorts Python imports
- **flake8**: Checks Python style and syntax
- **mypy**: Performs static type checking

#### Manual Quality Checks

You can also run these tools manually:

```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Check style with flake8
flake8 src/ tests/

# Type checking
mypy src/socialseed_e2e

# Run all quality checks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## Code Style Guide

### Python Code Style

We follow [PEP 8](https://pep8.org/) with the following specifics:

- **Line length**: 100 characters maximum
- **Quotes**: Use double quotes for strings, single quotes for single characters
- **Imports**: Grouped as standard library, third-party, local (sorted alphabetically within groups)
- **Type hints**: Required for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public modules, classes, and functions

### Example:

```python
"""Module for user service testing.

This module provides functionality for testing user-related
API endpoints.
"""

from typing import Dict, Any, Optional
from playwright.sync_api import APIResponse

from socialseed_e2e.core.base_page import BasePage


class UserServicePage(BasePage):
    """Page object for user service API.

    Provides methods for interacting with user endpoints
    including CRUD operations and authentication.

    Attributes:
        base_url: The base URL for the user service
        auth_token: Authentication token for protected endpoints
    """

    def __init__(self, base_url: str) -> None:
        """Initialize the UserServicePage.

        Args:
            base_url: The base URL for the user service API
        """
        super().__init__(base_url)
        self.auth_token: Optional[str] = None

    def login(self, email: str, password: str) -> APIResponse:
        """Authenticate user and store token.

        Args:
            email: User's email address
            password: User's password

        Returns:
            APIResponse: The login response containing auth token

        Raises:
            AssertionError: If login fails (non-2xx status)
        """
        response = self.post(
            "/auth/login",
            json={"email": email, "password": password}
        )

        if response.ok:
            data = response.json()
            self.auth_token = data.get("token")

        return response
```

### Testing Guidelines

- **Test names**: Descriptive, prefixed with `test_`
- **Test organization**: Mirror the source structure in `tests/`
- **Use fixtures**: Leverage pytest fixtures for setup/teardown
- **Mock external services**: Use the built-in mock API or mocking libraries
- **Coverage**: Aim for >80% coverage on new code

### Documentation Guidelines

- **Update README.md** if adding new features
- **Update CHANGELOG.md** following Keep a Changelog format
- **Add docstrings** to all public APIs
- **Update relevant docs** in the `docs/` directory
- **Include examples** for new features

## Pull Request Process

### Before Submitting

1. **Ensure tests pass:**
   ```bash
   pytest
   ```

2. **Check code quality:**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/socialseed_e2e
   ```

3. **Verify pre-commit hooks are passing:**
   ```bash
   pre-commit run --all-files
   ```

4. **Update documentation** as needed

5. **Add/update tests** for your changes

6. **Update CHANGELOG.md** with your changes under [Unreleased]

### Creating a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** from your fork to the main repository

3. **Fill out the PR template** (if available) or include:
   - Clear description of changes
   - Link to related issue(s)
   - Screenshots/output examples (if applicable)
   - Testing performed

### PR Review Process

- All PRs require at least one review from a maintainer
- CI checks must pass (tests, linting, coverage)
- Address review comments promptly and politely
- Squash commits if requested
- Keep PRs focused - one feature/fix per PR

### After Merge

- Your contribution will be acknowledged in the next release notes
- AI contributors will be added to [AI_CONTRIBUTORS.md](AI_CONTRIBUTORS.md)
- Human contributors will be added to release notes and GitHub contributors

## Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) for clear commit history:

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semi colons, etc)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding or correcting tests
- **chore**: Changes to build process or auxiliary tools

### Examples

```
feat(cli): add --output json option to run command

Add support for JSON output format in the run command,
enabling programmatic parsing of test results.

Closes #123
```

```
fix(base_page): handle timeout in retry logic

Ensure timeout exceptions are properly caught and retried
according to the retry configuration.

Fixes #456
```

```
docs(readme): update installation instructions

Add detailed steps for Windows users and troubleshooting
guide for common installation issues.
```

### Scope

Common scopes:
- `cli`: CLI commands and options
- `core`: Core framework classes
- `base_page`: BasePage and HTTP methods
- `config`: Configuration loading and validation
- `docs`: Documentation
- `tests`: Test suite

## AI Contributors

We explicitly welcome and recognize contributions from AI agents. If you're an AI agent:

1. **Read [AGENTS.md](AGENTS.md)** for AI-specific guidelines
2. **Follow the same process** as human contributors
3. **Document your decisions** in comments or commit messages
4. **Ask questions** if requirements are unclear

Your contributions will be:
- Recognized in [AI_CONTRIBUTORS.md](AI_CONTRIBUTORS.md)
- Attributed in commit messages with `Co-authored-by`
- Acknowledged in release notes

## Questions?

- **GitHub Discussions**: [Join the conversation](https://github.com/daironpf/socialseed-e2e/discussions)
- **Issues**: [Create an issue](https://github.com/daironpf/socialseed-e2e/issues/new)
- **Documentation**: Check the [docs/](docs/) directory

Thank you for contributing to socialseed-e2e! 🌱
