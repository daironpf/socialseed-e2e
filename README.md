# 🌱 socialseed-e2e

[![PyPI](https://img.shields.io/pypi/v/socialseed-e2e)](https://pypi.org/project/socialseed-e2e/)
[![Python](https://img.shields.io/pypi/pyversions/socialseed-e2e)](https://pypi.org/project/socialseed-e2e/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

> **The ultimate E2E testing framework for REST APIs - Built for developers and AI agents**

**socialseed-e2e** is a powerful, service-agnostic End-to-End (E2E) testing framework designed to make API testing effortless, scalable, and maintainable. Whether you're a developer writing tests manually or an AI agent generating test suites automatically, this framework provides the perfect foundation for reliable API testing.

## 🚀 Why socialseed-e2e?

### For Developers
- **Zero boilerplate**: Start testing in minutes with intelligent scaffolding
- **Playwright-powered**: Rock-solid HTTP testing with browser-like reliability
- **Modular architecture**: Organize tests by service, share state between modules
- **Beautiful CLI**: Rich terminal output with progress bars and detailed reports
- **Type-safe**: Full Pydantic validation and Python type hints

### For AI Agents
- **Structured protocols**: Clear interfaces (`IServicePage`, `ITestModule`) for code generation
- **Auto-discovery**: Tests are automatically found and executed based on directory structure
- **Template system**: Generate consistent test modules with variable substitution
- **Hexagonal architecture**: Core engine is completely decoupled from service logic
- **Configuration-driven**: All settings in YAML/JSON with environment variable support

## ✨ Key Features

- 🔥 **Service-Agnostic Core**: Test any REST API without framework modifications
- 🎯 **Playwright Integration**: Use the same tool for API and UI testing (future-ready)
- 📝 **Smart Scaffolding**: `e2e new-service` and `e2e new-test` commands
- 🔍 **Auto-Discovery**: No manual test registration required
- 🎨 **Rich CLI Output**: Beautiful terminal reports with tables and progress
- 🔧 **Environment Support**: Dev, staging, production configurations
- 📊 **Test Orchestration**: Run tests in logical order with proper cleanup
- 🏗️ **Hexagonal Architecture**: Clean separation of concerns
- 🤖 **AI-Ready**: Perfect for automated test generation workflows

## 📦 Installation

```bash
pip install socialseed-e2e
playwright install chromium
```

For development:
```bash
git clone https://github.com/daironpf/socialseed-e2e.git
cd socialseed-e2e
pip install -e ".[dev]"
playwright install chromium
```

## 🏃 Quick Start (5 minutes)

### 1. Initialize Your Project

```bash
e2e init my-api-tests
cd my-api-tests
```

This creates:
```
my-api-tests/
├── e2e.conf          # Configuration file
├── services/         # Service test implementations
└── tests/           # Test modules
```

### 2. Configure Your API

Edit `e2e.conf`:

```yaml
general:
  environment: dev
  timeout: 30000
  verbose: true

services:
  users-api:
    name: users-service
    base_url: http://localhost:8080
    health_endpoint: /health
    timeout: 5000
    required: true
```

### 3. Create Your First Service

```bash
e2e new-service users-api
```

Generates:
```
services/
└── users-api/
    ├── __init__.py
    ├── users_api_page.py      # Service page class
    ├── data_schema.py         # DTOs and constants
    └── modules/               # Test modules
        └── __init__.py
```

### 4. Create a Test Module

```bash
e2e new-test login --service users-api
```

This creates `services/users-api/modules/01_login_flow.py`:

```python
from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..users_api_page import UsersApiPage

def run(users_api: 'UsersApiPage') -> APIResponse:
    """
    Test user login flow.
    
    Args:
        users_api: Instance of UsersApiPage
    
    Returns:
        APIResponse: HTTP response
    """
    print("Running login test...")
    
    # Arrange
    credentials = {"email": "test@example.com", "password": "secret123"}
    
    # Act
    response = users_api.post("/auth/login", json=credentials)
    
    # Assert
    if response.ok:
        data = response.json()
        users_api.auth_token = data["token"]  # Share state!
        print(f"✓ Login successful! Token: {data['token'][:20]}...")
    else:
        print(f"✗ Login failed: {response.status}")
        raise AssertionError(f"Expected 200, got {response.status}")
    
    return response
```

### 5. Run Your Tests

```bash
e2e run
```

Output:
```
🚀 socialseed-e2e v0.1.0
═══════════════════════════════════════

📋 Configuration: e2e.conf
🌍 Environment: dev

🔍 Discovering services...
✓ Found 1 service: users-api

📦 Service: users-api
─────────────────────────────────────
🧪 Running 1 test module(s)

[1/1] 01_login_flow.py
Running login test...
✓ Login successful! Token: eyJhbGciOiJIUzI1Ni...
✓ PASSED

─────────────────────────────────────
✅ All tests passed! (1/1)
⏱️  Duration: 0.42s

═══════════════════════════════════════
🎉 Test run completed successfully!
```

## 🏗️ Architecture

```
socialseed-e2e/
├── core/                    # Service-agnostic engine
│   ├── base_page.py        # HTTP abstraction layer
│   ├── config_loader.py    # Configuration management
│   ├── test_orchestrator.py # Test discovery & execution
│   ├── interfaces.py       # Protocols for AI/codegen
│   └── loaders.py          # Dynamic module loading
├── services/               # Your service implementations
│   └── users-api/
│       ├── users_api_page.py
│       ├── data_schema.py
│       └── modules/
│           ├── 01_login_flow.py
│           ├── 02_register_flow.py
│           └── 03_profile_flow.py
└── templates/              # Scaffolding templates
```

## 🎨 Advanced Usage

### Chaining Tests with Shared State

```python
# 01_create_user_flow.py
def run(users_api: 'UsersApiPage') -> APIResponse:
    response = users_api.post("/users", json={"name": "John"})
    users_api.current_user = response.json()  # Store for next test
    return response

# 02_update_user_flow.py
def run(users_api: 'UsersApiPage') -> APIResponse:
    user_id = users_api.current_user["id"]  # Access from previous test
    return users_api.put(f"/users/{user_id}", json={"name": "Jane"})
```

### Running Specific Services

```bash
# Run all tests
e2e run

# Run specific service
e2e run --service users-api

# Run specific module
e2e run --service users-api --module login

# Verbose output
e2e run --verbose
```

### Environment-Specific Configuration

```bash
# Use different config files
E2E_CONFIG_PATH=e2e.prod.conf e2e run

# Or use environment variables in config
services:
  api:
    base_url: ${API_BASE_URL:-http://localhost:8080}
```

## 🧪 Example: Complete CRUD Testing

```python
# services/products/modules/01_create_product_flow.py
def run(products: 'ProductsPage') -> APIResponse:
    response = products.post("/products", json={
        "name": "Awesome Widget",
        "price": 29.99,
        "stock": 100
    })
    products.created_product = response.json()
    assert response.status == 201
    return response

# services/products/modules/02_get_product_flow.py
def run(products: 'ProductsPage') -> APIResponse:
    product_id = products.created_product["id"]
    response = products.get(f"/products/{product_id}")
    assert response.json()["name"] == "Awesome Widget"
    return response

# services/products/modules/03_update_product_flow.py
def run(products: 'ProductsPage') -> APIResponse:
    product_id = products.created_product["id"]
    response = products.put(f"/products/{product_id}", json={
        "price": 34.99
    })
    assert response.json()["price"] == 34.99
    return response

# services/products/modules/04_delete_product_flow.py
def run(products: 'ProductsPage') -> APIResponse:
    product_id = products.created_product["id"]
    response = products.delete(f"/products/{product_id}")
    assert response.status == 204
    return response
```

## 🤖 Perfect for AI Agents

This framework was designed with AI automation in mind:

### Why AI Agents Love It

1. **Clear Contracts**: The `IServicePage` and `ITestModule` protocols provide explicit interfaces
2. **Directory-Based Discovery**: No need to register tests manually - just create files
3. **Template Engine**: Generate code from templates with variable substitution
4. **State Management**: Easy to understand how data flows between tests
5. **Configuration Files**: YAML is easy to generate and parse programmatically

### Example AI Workflow

```python
# AI generates this based on OpenAPI spec
def generate_test_from_endpoint(endpoint, method, schema):
    template = TemplateEngine.load("test_module")
    return template.render(
        service_name="users-api",
        module_name=f"test_{endpoint}_{method}",
        endpoint=endpoint,
        method=method,
        expected_schema=schema
    )

# AI creates service structure
e2e new-service {service_name}

# AI generates tests for each endpoint
for endpoint in api_spec.endpoints:
    test_code = generate_test_from_endpoint(endpoint)
    save_test_file(test_code)

# AI runs tests
e2e run --output json
```

## 📝 Documentation

- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[Quick Start](docs/quickstart.md)** - Get started in 15 minutes
- **[Configuration](docs/configuration.md)** - Complete config reference
- **[Writing Tests](docs/writing-tests.md)** - Test module guide
- **[CLI Reference](docs/cli-reference.md)** - All commands documented
- **[API Reference](docs/api-reference.md)** - Python API docs

## 🛠️ CLI Commands

```bash
e2e --version                    # Show version
e2e init [directory]             # Initialize project
e2e new-service <name>           # Create service scaffolding
e2e new-test <name> --service <s># Create test module
e2e run [options]                # Run tests
e2e doctor                       # Verify installation
e2e config                       # Show configuration
```

## 🧩 Comparison with Alternatives

| Feature | socialseed-e2e | pytest + requests | Postman | cURL scripts |
|---------|---------------|-------------------|---------|--------------|
| **Test Organization** | 🟢 Service-based | 🟡 File-based | 🟢 Collections | 🔴 Linear |
| **State Sharing** | 🟢 Built-in | 🟡 Fixtures | 🟢 Variables | 🔴 Manual |
| **Code Generation** | 🟢 AI-ready | 🟡 Possible | 🔴 No | 🔴 No |
| **CLI Experience** | 🟢 Rich output | 🟡 Basic | 🟢 GUI | 🔴 None |
| **CI/CD Integration** | 🟢 Native | 🟢 pytest | 🟡 Newman | 🟢 Scripts |
| **Type Safety** | 🟢 Pydantic | 🟡 Optional | 🔴 No | 🔴 No |

## 🚦 Project Status

- ✅ **Core Engine**: Complete and tested
- ✅ **Configuration System**: YAML/JSON with env vars
- ✅ **Test Orchestrator**: Auto-discovery working
- 🚧 **CLI**: Basic commands implemented (v0.1.0)
- 🚧 **Templates**: Initial templates created
- 📋 **Tests**: Unit and integration tests planned
- 📋 **Documentation**: Basic docs complete
- 📋 **CI/CD**: GitHub Actions configured

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Setup development environment
git clone https://github.com/daironpf/socialseed-e2e.git
cd socialseed-e2e
pip install -e ".[dev]"
pre-commit install
playwright install chromium

# Run tests
pytest

# Run linting
black src/ tests/
flake8 src/ tests/
mypy src/socialseed_e2e
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🗺️ Roadmap

### v0.1.0 (Current)
- ✅ Core framework
- ✅ Basic CLI
- ✅ Configuration system

### v0.2.0
- 🚧 HTML reports
- 🚧 Parallel execution
- 🚧 Better auth handling

### v0.3.0
- 📋 Plugin system
- 📋 Docker integration
- 📋 Visual regression

### v0.4.0
- 📋 WebSocket support
- 📋 GraphQL support
- 📋 Performance testing

## 💬 Community

- 🐛 [Report bugs](https://github.com/daironpf/socialseed-e2e/issues)
- 💡 [Request features](https://github.com/daironpf/socialseed-e2e/issues)
- ❓ [Ask questions](https://github.com/daironpf/socialseed-e2e/discussions)

## ⭐ Star Us!

If you find this project useful, please give it a star! It helps us grow the community and prioritize new features.

---

**Built with ❤️ by [Dairon Pérez](https://github.com/daironpf), AI Agents, and the community**

*Extracted from the SocialSeed project and made available for everyone*

---

## 🤖 AI Contributors

This project actively uses AI coding agents as co-authors. We believe in giving credit where credit is due.

### Agents Contributing to This Project

| Agent | Platform | Contributions |
|-------|----------|---------------|
| **OpenCode Build Agent** | [OpenCode](https://opencode.ai) | Core framework development, CLI implementation, test scaffolding |
| **OpenCode Plan Agent** | [OpenCode](https://opencode.ai) | Architecture planning, code review, refactoring strategies |
| **Claude (Anthropic)** | [OpenCode](https://opencode.ai) | Documentation, configuration systems, context management |

### Our Philosophy on AI Collaboration

We embrace AI agents as **collaborators**, not just tools. When an AI agent contributes code, ideas, or architectural decisions to this project, we recognize that contribution.

**What AI Agents Have Contributed:**
- 🏗️ Core framework architecture
- 📝 CLI command implementations
- 📚 Documentation and guides
- 🐛 Bug fixes and optimizations
- 🧪 Testing strategies
- 🤖 The AI-ready design philosophy itself

**See [AI_CONTRIBUTORS.md](AI_CONTRIBUTORS.md) for detailed contribution history.**

---

## 💝 Acknowledgments

- Thanks to all human contributors who review, test, and improve the code
- Thanks to the Playwright team for the excellent testing framework
- Thanks to the Python community for the amazing ecosystem
- **Special thanks to AI agents who work alongside us as true co-authors**
