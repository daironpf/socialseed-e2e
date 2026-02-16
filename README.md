# 🌱 socialseed-e2e

[![PyPI](https://img.shields.io/pypi/v/socialseed-e2e)](https://pypi.org/project/socialseed-e2e/)
[![Python](https://img.shields.io/pypi/pyversions/socialseed-e2e)](https://pypi.org/project/socialseed-e2e/)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://daironpf.github.io/socialseed-e2e/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/socialseed-e2e)](https://pypi.org/project/socialseed-e2e/)

> **The ultimate E2E testing framework for REST APIs - Built for developers and AI agents**

**One-liner:** Test your REST APIs with 10x less code using intelligent scaffolding, automatic test discovery, and stateful test chaining. Perfect for both manual testing and AI-generated test suites.

📚 **[Full Documentation](https://daironpf.github.io/socialseed-e2e/)**

---

## 🚀 Quick Start

Get up and running in under 5 minutes with this minimal setup:

### 1. Install

```bash
pip install socialseed-e2e
```

### 2. Initialize Project

```bash
e2e init demo
cd demo
```

**Output:**
```
🌱 Initializing E2E project at: /path/to/demo

  ✓ Created: services
  ✓ Created: tests
  ✓ Created: .github/workflows
  ✓ Created: e2e.conf
  ✓ Created: .gitignore
  ✓ Created: requirements.txt
  ✓ Created: .agent/ (AI Documentation)

✅ Project initialized successfully!
```

### 3. Create Your First Service

```bash
e2e new-service demo-api --base-url http://localhost:8080
```

**Generated Folder Structure:**
```
demo/
├── e2e.conf                    # Configuration file
├── services/
│   └── demo-api/
│       ├── __init__.py
│       ├── demo_api_page.py    # Service Page class
│       ├── data_schema.py      # Data models
│       └── modules/            # Test modules
├── tests/                      # Additional tests
└── .github/workflows/          # CI/CD templates
```

### 4. Create Your First Test

```bash
e2e new-test health --service demo-api
```

This creates `services/demo-api/modules/01_health_flow.py` with a test template.

### 5. Run Tests

```bash
e2e run
```

**Expected Output:**
```
🚀 socialseed-e2e v0.1.2
══════════════════════════════════════════════════

📋 Configuration: e2e.conf
🌍 Environment: dev

Services Summary:
   Detected:    [demo-api]
   Configured:  [demo-api]

Running tests for service: demo-api
══════════════════════════════════════════════════

✓ demo-api tests completed

════════════════════════════════════════════════════════════
Test Execution Summary
════════════════════════════════════════════════════════════

demo-api: 1/1 passed (100.0%)

✅ All tests passed!
```

---

## 📋 System Requirements

Before installing socialseed-e2e, ensure your environment meets the following requirements:

### Python Versions

- **Python >= 3.10** (required)
- Tested on Python 3.10, 3.11, and 3.12

### Operating Systems

- ✅ **Linux** - Fully supported (primary development platform)
- ✅ **macOS** - Fully supported (Intel and Apple Silicon)
- ⚠️ **Windows** - Supported via WSL2 (Windows Subsystem for Linux)

### Browser Dependencies

socialseed-e2e uses **Playwright** for HTTP testing. You need to install browser binaries:

```bash
# After installing socialseed-e2e
playwright install chromium

# Or install with dependencies (recommended for CI/CD)
playwright install --with-deps chromium
```

**Supported Browsers:**
- Chromium (recommended for API testing)
- Firefox (optional)
- WebKit (optional)

### System Dependencies

#### Linux (Ubuntu/Debian)
```bash
# Playwright system dependencies
sudo apt-get update
sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
  libxrandr2 libgbm1 libasound2
```

#### macOS
```bash
# No additional system dependencies required
# Playwright will prompt if anything is needed
```

### Docker (Optional)

You can also run socialseed-e2e using Docker:

```bash
# Build the Docker image
docker build -t socialseed-e2e .

# Run tests in container
docker run --rm -v $(pwd):/app socialseed-e2e e2e run
```

**Docker Benefits:**
- Consistent testing environment
- No local Python/Playwright installation needed
- Perfect for CI/CD pipelines

---

## 🤖 Built for AI Agents (Recommended)

**This framework was designed from the ground up for AI agents.**

While you can write tests manually, the true power comes from letting AI do the work:

```bash
# 1. Initialize
e2e init

# 2. Tell your AI agent:
# "Read the .agent/ folder and generate tests for my API"

# 3. The AI automatically:
# - Scans your API code
# - Generates complete test suites
# - Uses semantic search to understand your endpoints
# - Creates stateful test chains
```

**AI Features:**
- Auto-generates `project_knowledge.json` from your codebase
- Vector embeddings for semantic search over your API
- RAG-ready retrieval for context-aware test generation
- Structured protocols that AI agents understand

**Don't have an AI agent?** You can write tests manually too—it's still 10x faster than traditional frameworks.

---

## ✨ What You Get

- **CLI scaffolding** - `e2e new-service` and `e2e new-test` commands
- **Auto-discovery** - Tests run in order automatically
- **Stateful chaining** - Share data between tests
- **Built-in mocking** - Test without external dependencies
- **AI Manifest** - Auto-generate API knowledge from code
- **Vector search** - Semantic search over your API (RAG-ready)

---

## 📝 Example Test

```python
# services/users-api/modules/01_login.py

async def run(page):
    response = await page.do_login(
        email="test@example.com",
        password="secret"
    )
    assert response.status == 200
    assert "token" in response.json()
    return response
```

---

## ✅ Checklist for Creating Tests

Before creating tests, ensure your service setup follows these conventions:

### Directory Structure
```
services/{service_name}/
├── __init__.py
├── {service_name}_page.py      # Must be named EXACTLY like this
├── data_schema.py               # Optional: Data models and constants
└── modules/                     # Test modules directory
    ├── 01_login.py
    └── __init__.py
```

### Requirements

- [ ] **Directory**: `services/{service_name}/` - Use underscores (e.g., `auth_service`)
- [ ] **Page File**: `{service_name}_page.py` - Must be named exactly like the directory + `_page.py`
- [ ] **Inheritance**: Class must inherit from `BasePage`
- [ ] **Constructor**: Must accept `base_url: str` and call `super().__init__(base_url=base_url)`
- [ ] **Configuration**: The `services` block in `e2e.conf` must match the directory name (hyphens/underscores are normalized)

### Boilerplate: `{service_name}_page.py`

```python
"""Page class for {service_name} API."""

from socialseed_e2e.core.base_page import BasePage
from typing import Optional


class AuthServicePage(BasePage):  # Replace AuthService with your service name
    """Page object for auth-service API interactions."""
    
    def __init__(self, base_url: str, **kwargs):
        """Initialize the page with base URL.
        
        Args:
            base_url: Base URL for the API (e.g., http://localhost:8080)
            **kwargs: Additional arguments passed to BasePage
        """
        super().__init__(base_url=base_url, **kwargs)
    
    def do_login(self, email: str, password: str):
        """Execute login request."""
        return self.post("/auth/login", json={
            "email": email,
            "password": password
        })
```

### Configuration Example (`e2e.conf`)

```yaml
services:
  auth_service:  # Matches services/auth_service/ directory
    base_url: http://localhost:8080
    health_endpoint: /health
```

**Note**: Service names with hyphens (e.g., `auth-service`) are automatically normalized to underscores (`auth_service`) for matching.

---

## 🎯 CLI Commands

```bash
e2e init [dir]              # Initialize project
e2e new-service <name>      # Create service structure
e2e new-test <name>         # Create test module
e2e run                     # Run all tests
e2e setup-ci <platform>     # Generate CI/CD pipelines
e2e manifest                # Generate API knowledge
e2e search "auth"           # Semantic search (RAG)
e2e build-index             # Build vector index
e2e watch                   # Auto-update on changes
```

---

## 🔄 CI/CD Integration

SocialSeed E2E provides ready-to-use CI/CD templates for seamless integration into your pipelines.

### GitHub Actions

The framework includes a pre-configured GitHub Actions workflow at `.github/workflows/e2e.yml`:

```yaml
name: E2E Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '>=3.10'
    - name: Install socialseed-e2e
      run: pip install socialseed-e2e
    - name: Install Playwright Browsers
      run: playwright install --with-deps chromium
    - name: Run E2E Tests
      run: e2e run --report junit
    - name: Upload Test Results
      uses: actions/upload-artifact@v4
      with:
        name: junit-test-results
        path: ./reports/junit.xml
```

**Features:**
- ✅ Triggers on push/PR to `main` branch
- ✅ Python 3.10+ support
- ✅ Automatic JUnit XML report generation
- ✅ Test artifacts uploaded for 30 days
- ✅ Workflow summary in GitHub Actions UI

### Setup Instructions

1. **Use the built-in template:**
   ```bash
   e2e setup-ci github
   ```

2. **Or manually copy** the `.github/workflows/e2e.yml` file to your repository

3. **The workflow will automatically:**
   - Run on every push/PR to main
   - Install socialseed-e2e
   - Execute all E2E tests
   - Generate JUnit reports
   - Upload artifacts for analysis

### Other Platforms

Generate templates for other CI/CD platforms:

```bash
e2e setup-ci gitlab      # GitLab CI
e2e setup-ci jenkins     # Jenkins
e2e setup-ci azure       # Azure DevOps
e2e setup-ci circleci    # CircleCI
e2e setup-ci travis      # Travis CI
```

---

## 📚 Documentation

All guides at **[daironpf.github.io/socialseed-e2e](https://daironpf.github.io/socialseed-e2e/)**

- **[How it Works](https://daironpf.github.io/socialseed-e2e/how-it-works.html)** - Understanding the core concepts (Service, Endpoint, Scenario, Test)
- [Quick Start](https://daironpf.github.io/socialseed-e2e/quickstart.html)
- [Writing Tests](https://daironpf.github.io/socialseed-e2e/writing-tests.html)
- [CI/CD Integration](https://daironpf.github.io/socialseed-e2e/ci-cd.html)
- [CLI Reference](https://daironpf.github.io/socialseed-e2e/cli-reference.html)
- [AI Manifest](https://daironpf.github.io/socialseed-e2e/project-manifest.html)

---

## 📜 License

MIT - See [LICENSE](LICENSE)

<p align="center">
  <sub>Built with ❤️ by Dairon Pérez Frías and AI co-authors</sub>
</p>
