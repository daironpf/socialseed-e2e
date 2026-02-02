# CLI Reference

Complete reference for the socialseed-e2e command-line interface.

## Overview

The socialseed-e2e CLI provides a complete interface for managing E2E testing projects. It follows a workflow-based approach:

```
init → new-service → new-test → run
```

## Global Options

All commands support these global options:

```bash
e2e [command] [options]
```

### Available Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-V` | Show version number and exit |
| `--help` | `-h` | Show help message and exit |

### Usage Examples

```bash
# Show version
e2e --version

# Get help for specific command
e2e init --help
e2e run --help
```

## Commands Reference

### `init` - Initialize Project

Creates a new E2E testing project with the necessary structure.

#### Syntax

```bash
e2e init [directory] [options]
```

#### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `directory` | No | `.` | Directory where to create the project |

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--force` | - | flag | false | Overwrite existing files |

#### Created Files and Directories

```
<directory>/
├── e2e.conf              # Main configuration file
├── .gitignore           # Git ignore rules
├── services/            # Service modules directory
├── tests/               # Test directory
└── .github/
    └── workflows/       # GitHub Actions workflows
```

#### Examples

```bash
# Initialize in current directory
e2e init

# Initialize in specific directory
e2e init ./my-api-tests

# Force overwrite existing files
e2e init --force
```

#### Output Example

```
🌱 Inicializando proyecto E2E en: /home/user/my-project

  ✓ Creado: services
  ✓ Creado: tests
  ✓ Creado: .github/workflows
  ✓ Creado: e2e.conf
  ✓ Creado: .gitignore

✅ Proyecto inicializado correctamente!

╭──────── 🚀 Empezar ─────────╮
│ 1. Edita e2e.conf para      │
│    configurar tu API        │
│ 2. Ejecuta: e2e new-service │
│    <nombre>                 │
│ 3. Ejecuta: e2e new-test    │
│    <nombre> --service <svc> │
│ 4. Ejecuta: e2e run para    │
│    correr tests             │
╰─────────────────────────────╯
```

---

### `new-service` - Create Service

Creates a new service with complete scaffolding including page class, configuration, and data schema.

#### Syntax

```bash
e2e new-service <name> [options]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Service name (e.g., `users-api`, `auth-service`) |

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--base-url` | - | string | `http://localhost:8080` | Base URL for the service |
| `--health-endpoint` | - | string | `/health` | Health check endpoint |

#### Created Files

```
services/<name>/
├── __init__.py              # Package initialization
├── <name>_page.py          # ServicePage class
├── config.py                # Service configuration
└── data_schema.py           # Data models and DTOs
```

#### Generated Classes

- **ServicePage**: Extends `BasePage` with service-specific HTTP methods
- **ServiceConfig**: Configuration class with base URL, timeouts, etc.
- **Data Models**: Pydantic models for request/response validation

#### Examples

```bash
# Create basic service
e2e new-service users-api

# Create with custom base URL
e2e new-service payment-api --base-url https://api.payments.com/v1

# Create with custom health endpoint
e2e new-service auth-api --health-endpoint /api/health

# Full example
e2e new-service inventory --base-url http://localhost:3000 --health-endpoint /status
```

#### Output Example

```
🔧 Creando servicio: users-api

  ✓ Creado: services/users-api/
  ✓ Creado: services/users-api/modules/
  ✓ Creado: services/users-api/__init__.py
  ✓ Creado: services/users-api/modules/__init__.py
  ✓ Creado: services/users-api/users_api_page.py
  ✓ Creado: services/users-api/config.py
  ✓ Creado: services/users-api/data_schema.py
  ✓ Actualizado: e2e.conf

✅ Servicio 'users-api' creado correctamente!

╭─────── 🚀 Continuar ───────╮
│ 1. Edita                    │
│    services/users-api/data_ │
│    schema.py para definir   │
│    tus DTOs                 │
│ 2. Ejecuta: e2e new-test    │
│    <nombre> --service       │
│    users-api                │
│ 3. Ejecuta: e2e run         │
│    --service users-api      │
╰─────────────────────────────╯
```

---

### `new-test` - Create Test Module

Creates a new test module within a service.

#### Syntax

```bash
e2e new-test <name> --service <service> [options]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Test name (e.g., `login`, `create-user`) |

#### Options

| Option | Short | Type | Required | Description |
|--------|-------|------|----------|-------------|
| `--service` | `-s` | string | Yes | Service name where to create the test |
| `--description` | `-d` | string | No | Test description |

#### Test Naming Convention

Tests are automatically numbered with a two-digit prefix to control execution order:

```
modules/
├── 01_setup.py
├── 02_authentication.py
├── 03_create_user.py
└── 04_update_profile.py
```

#### Created File Structure

```python
# services/<service>/modules/XX_<name>_flow.py

"""Test flow for <name>.

<description>
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..<service>_page import <Service>Page


def run(page: '<Service>Page') -> APIResponse:
    """Execute <name> test flow.

    Args:
        page: Service page instance

    Returns:
        APIResponse: Response from the test
    """
    # Implement test logic here
    pass
```

#### Examples

```bash
# Create test for users service
e2e new-test login --service users-api

# Create with description
e2e new-test create-order --service payment-api --description "Test order creation flow"

# Short option form
e2e new-test register -s auth-api -d "User registration test"
```

#### Output Example

```
📝 Creando test: login

  ✓ Creado: services/users-api/modules/01_login_flow.py

✅ Test 'login' creado correctamente!

╭────── 🚀 Implementar ──────╮
│ 1. Edita                    │
│    services/users-api/modul │
│    es/01_login_flow.py      │
│ 2. Implementa la lógica del │
│    test                     │
│ 3. Ejecuta: e2e run         │
│    --service users-api      │
╰─────────────────────────────╯
```

---

### `run` - Execute Tests

Discovers and executes E2E tests.

#### Syntax

```bash
e2e run [options]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--service` | `-s` | string | - | Filter by specific service |
| `--module` | `-m` | string | - | Filter by specific module |
| `--verbose` | `-v` | flag | false | Enable verbose output |
| `--output` | `-o` | choice | `text` | Output format: `text` or `json` |

#### Examples

```bash
# Run all tests
e2e run

# Run tests for specific service
e2e run --service users-api
e2e run -s auth-api

# Run specific module
e2e run --module 01_login
e2e run -m 02_register

# Verbose mode
e2e run -v
e2e run --verbose --service payment-api

# JSON output
e2e run -o json
e2e run --output json --service inventory

# Combined options
e2e run -s users-api -m 01_login -v
```

#### Output Formats

**Text Format (default):**
```
🚀 socialseed-e2e v0.1.0
═══════════════════════════════════

📋 Configuración: /home/user/project/e2e.conf
🌍 Environment: dev

╭──────── Servicios Encontrados ────────╮
│  Servicio      │ Tests │ Estado      │
├────────────────┼───────┼─────────────┤
│  users-api     │   3   │ Ready       │
│  auth-api      │   2   │ Ready       │
│  payment-api   │   0   │ Empty       │
╰────────────────┴───────┴─────────────╯
```

**JSON Format:**
```json
{
  "version": "0.1.0",
  "config": "/home/user/project/e2e.conf",
  "environment": "dev",
  "services": [
    {
      "name": "users-api",
      "tests": 3,
      "status": "ready"
    }
  ]
}
```

---

### `doctor` - Verify Installation

Checks that the installation and dependencies are correctly configured.

#### Syntax

```bash
e2e doctor
```

#### Checks Performed

| Check | Description |
|-------|-------------|
| Python | Version 3.9+ required |
| Playwright | Library installation |
| Playwright CLI | Browser management tools |
| Pydantic | Data validation library |
| Configuration | `e2e.conf` existence |
| Directory Structure | `services/` and `tests/` existence |

#### Examples

```bash
# Run diagnostic
e2e doctor
```

#### Output Example

**Successful Check:**
```
🏥 socialseed-e2e Doctor

╭────────── Verificación del Sistema ──────────╮
│  Componente       │ Versión/Estado │ Estado  │
├───────────────────┼────────────────┼─────────┤
│  Python           │ 3.11.4         │ ✓       │
│  Playwright       │ 1.40.0         │ ✓       │
│  Playwright CLI   │ Disponible     │ ✓       │
│  Pydantic         │ 2.5.0          │ ✓       │
│  Configuración    │ e2e.conf       │ ✓       │
│  Directorio       │ OK             │ ✓       │
│  services/        │                │         │
│  Directorio       │ OK             │ ✓       │
│  tests/           │                │         │
╰───────────────────┴────────────────┴─────────╯

✅ Todo está configurado correctamente!
```

**Failed Checks:**
```
🏥 socialseed-e2e Doctor

╭────────── Verificación del Sistema ──────────╮
│  Componente       │ Versión/Estado │ Estado  │
├───────────────────┼────────────────┼─────────┤
│  Python           │ 3.11.4         │ ✓       │
│  Playwright       │ No instalado   │ ✗       │
│  Playwright CLI   │ No disponible  │ ✗       │
│  Pydantic         │ 2.5.0          │ ✓       │
│  Configuración    │ e2e.conf no    │ ✗       │
│                   │ encontrado     │         │
╰───────────────────┴────────────────┴─────────╯

⚠ Se encontraron algunos problemas

Soluciones sugeridas:
  • Instala Playwright: pip install playwright
  • Instala browsers: playwright install chromium
  • Inicializa proyecto: e2e init
```

---

### `config` - Show Configuration

Displays and validates the current configuration from `e2e.conf`.

#### Syntax

```bash
e2e config
```

#### Displayed Information

- Configuration file path
- Current environment
- Timeout settings
- Verbose mode status
- Configured services table

#### Examples

```bash
# Show configuration
e2e config
```

#### Output Example

```
⚙️  Configuración E2E

📋 Configuración: /home/user/project/e2e.conf
🌍 Environment: dev
Timeout: 30000ms
Verbose: true

╭────────── Servicios Configurados ──────────╮
│  Nombre      │ Base URL              │ ... │
├──────────────┼───────────────────────┼─────┤
│  users-api   │ http://localhost:8080 │ ... │
│  auth-api    │ http://localhost:3000 │ ... │
╰──────────────┴───────────────────────┴─────╯

✅ Configuración válida
```

**Error Output:**
```
❌ Error de configuración: Missing required field: services

Ejecuta: e2e init para crear un proyecto
```

---

## Error Messages and Solutions

### Common Errors

#### E001: Not in E2E Project

```
❌ Error: No se encontró e2e.conf. ¿Estás en un proyecto E2E?
   Ejecuta: e2e init primero
```

**Cause:** Running `new-service`, `new-test`, or `run` outside an E2E project.

**Solution:**
```bash
e2e init
```

#### E002: Service Does Not Exist

```
❌ Error: El servicio 'users-api' no existe.
   Crea el servicio primero: e2e new-service users-api
```

**Cause:** Trying to create a test for a non-existent service.

**Solution:**
```bash
e2e new-service users-api
e2e new-test login --service users-api
```

#### E003: Service Already Exists

```
⚠ El servicio 'users-api' ya existe
¿Deseas continuar y sobrescribir archivos? [y/N]:
```

**Cause:** Attempting to create a service that already exists.

**Solution:**
- Press `y` to overwrite
- Or choose a different service name

#### E004: Configuration Error

```
❌ Error de configuración: <error details>
```

**Common causes:**
- Invalid YAML syntax in `e2e.conf`
- Missing required fields
- Invalid values (e.g., non-integer timeout)

**Solution:**
1. Check `e2e.conf` syntax
2. Run `e2e doctor` for diagnostics
3. Regenerate with `e2e init --force`

#### E005: Missing Dependencies

```
❌ Error: playwright module not found
```

**Solution:**
```bash
pip install socialseed-e2e
playwright install chromium
```

---

## Environment Variables

### Framework Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `E2E_CONFIG_PATH` | Path to configuration file | `e2e.conf` |
| `E2E_ENVIRONMENT` | Override environment | From config |
| `E2E_VERBOSE` | Enable verbose logging | `false` |

### Playwright Variables

| Variable | Description |
|----------|-------------|
| `PLAYWRIGHT_BROWSERS_PATH` | Path to browser binaries |
| `DEBUG` | Enable Playwright debug mode |

### Usage Examples

```bash
# Use custom config file
export E2E_CONFIG_PATH=/path/to/custom.conf
e2e run

# Force verbose mode
export E2E_VERBOSE=true
e2e run

# Set environment
export E2E_ENVIRONMENT=staging
e2e run
```

---

## Command Cheat Sheet

### Quick Reference

```bash
# Project Setup
e2e init                                    # Initialize in current dir
e2e init ./my-project                       # Initialize in specific dir
e2e init --force                           # Overwrite existing

# Service Management
e2e new-service users-api                   # Create service
e2e new-service api --base-url http://...   # With custom URL
e2e new-service svc --health /status        # With custom health endpoint

# Test Creation
e2e new-test login --service users          # Create test
e2e new-test auth -s users -d "Login flow"  # With description

# Test Execution
e2e run                                     # Run all tests
e2e run -s users-api                        # Run specific service
e2e run -m 01_login                        # Run specific module
e2e run -v                                 # Verbose mode
e2e run -o json                            # JSON output

# Diagnostics
e2e doctor                                  # Check installation
e2e config                                  # Show configuration

# Help
e2e --help                                  # Global help
e2e <command> --help                       # Command help
```

### Workflow Examples

#### New Project Workflow

```bash
# 1. Initialize
e2e init my-api-tests
cd my-api-tests

# 2. Configure
echo "Configure e2e.conf with your API details"

# 3. Create services
e2e new-service users-api --base-url https://api.example.com/v1
e2e new-service auth-api --base-url https://auth.example.com

# 4. Create tests
e2e new-test login --service auth-api
e2e new-test get-profile --service users-api

# 5. Run tests
e2e run
```

#### Daily Development Workflow

```bash
# Check setup
e2e doctor

# Run all tests
e2e run

# Run only modified service
e2e run -s users-api

# Debug specific test
e2e run -s users-api -m 03_update -v
```

#### CI/CD Workflow

```bash
# Install
e2e doctor || exit 1

# Run with JSON output for parsing
e2e run -o json > results.json

# Check results
jq '.success' results.json
```

---

## Advanced Usage

### Combining Options

```bash
# Multiple filters
e2e run --service users-api --module 01_login --verbose

# Short form
e2e run -s users-api -m 01_login -v

# JSON output with verbose
e2e run -s payment-api -o json -v
```

### Scripting with CLI

```bash
#!/bin/bash

# Create services in batch
for service in users-api auth-api payment-api; do
    e2e new-service "$service"
done

# Run tests and capture output
if e2e run -o json > /tmp/results.json; then
    echo "Tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

---

## Tips and Best Practices

1. **Always run `e2e doctor`** after installation to verify setup
2. **Use `--force` carefully** - it will overwrite existing files
3. **Name services descriptively** - they become class names
4. **Use verbose mode** (`-v`) when debugging test issues
5. **Check `e2e config`** to verify your configuration is loaded correctly
6. **Use JSON output** for CI/CD integration and automation

---

## See Also

- [Quick Start](quickstart.md) - Get started in 15 minutes
- [Writing Tests](writing-tests.md) - How to write test modules
- [Configuration](configuration.md) - Service configuration options
- [Testing Guide](testing-guide.md) - Pytest configuration and markers
