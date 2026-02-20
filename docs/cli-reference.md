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

## AI Features Commands

### `manifest` - Generate AI Project Manifest

Creates a comprehensive knowledge file about your project for AI agents.

```bash
e2e manifest [DIRECTORY] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--force` | Force full scan instead of smart sync |

**Examples:**
```bash
e2e manifest                           # Generate for current project
e2e manifest ../services/auth-service  # Generate for specific service
e2e manifest --force                   # Force full rescan
```

---

### `manifest-query` - Query Project Manifest

Query the generated manifest for project information.

```bash
e2e manifest-query [DIRECTORY] [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--format` | `-f` | Output format: json, markdown |

**Examples:**
```bash
e2e manifest-query auth-service         # Query auth manifest
e2e manifest-query -f markdown user-api # Output as Markdown
```

---

### `manifest-check` - Validate Manifest Freshness

Check if the manifest is up-to-date with source code.

```bash
e2e manifest-check [DIRECTORY]
```

**Examples:**
```bash
e2e manifest-check auth-service
```

---

### `build-index` - Build Vector Index

Build semantic search index for the manifest.

```bash
e2e build-index [DIRECTORY]
```

**Note:** Requires RAG extras: `e2e install-extras rag`

**Examples:**
```bash
e2e build-index auth-service
```

---

### `search` - Semantic Search

Perform semantic search on the project manifest.

```bash
e2e search "QUERY" [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--service` | `-s` | Service name |
| `--top-k` | `-k` | Number of results |
| `--type` | `-t` | Filter by type: endpoint, dto, service |

**Examples:**
```bash
e2e search "authentication endpoints"
e2e search "user DTO" -s user-service --type dto
e2e search "payment" --top-k 10
```

---

### `retrieve` - Retrieve Context

Retrieve relevant context for a specific task.

```bash
e2e retrieve "TASK" [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--service` | `-s` | Service name |
| `--max-chunks` | `-c` | Maximum chunks to retrieve |

**Examples:**
```bash
e2e retrieve "create user authentication tests" -s auth-service
e2e retrieve "test payment flow" --max-chunks 3
```

---

### `watch` - Watch Project Files

Auto-update manifest when files change.

```bash
e2e watch [DIRECTORY]
```

**Examples:**
```bash
e2e watch auth-service
```

---

### `discover` - Generate AI Discovery Report

Create comprehensive project analysis report.

```bash
e2e discover [DIRECTORY] [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output directory |
| `--open` | | Open report after generation |

**Examples:**
```bash
e2e discover
e2e discover --open
```

---

### `generate-tests` - Autonomous Test Generation

Generate test suites automatically.

```bash
e2e generate-tests [DIRECTORY] [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output directory |
| `--service` | `-s` | Generate for specific service |
| `--strategy` | | Strategy: valid, invalid, edge, chaos, all |
| `--dry-run` | | Preview without creating files |
| `--verbose` | `-v` | Verbose output |

**Examples:**
```bash
e2e generate-tests
e2e generate-tests --service users-api
e2e generate-tests --dry-run
```

---

### `plan-strategy` - Generate Test Strategy

Create AI-driven testing strategy.

```bash
e2e plan-strategy [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Strategy name (required) |
| `--description` | `-d` | Strategy description |
| `--services` | `-s` | Comma-separated services |
| `--output` | `-o` | Output path |

**Examples:**
```bash
e2e plan-strategy -n "API Regression"
e2e plan-strategy -n "Critical Path" -s users,payments
```

---

### `autonomous-run` - Run Tests Autonomously

Execute tests with AI orchestration.

```bash
e2e autonomous-run [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--project` | `-p` | Project directory |
| `--strategy-id` | `-s` | Strategy ID (required) |
| `--parallel` | `-j` | Parallel workers |
| `--no-healing` | | Disable self-healing |
| `--auto-fix` | | Auto-apply fixes |
| `--verbose` | `-v` | Verbose output |

**Examples:**
```bash
e2e autonomous-run -s abc123
e2e autonomous-run -s abc123 --parallel 8
```

---

## Testing & Debugging Commands

### `doctor` - Verify Installation

Verify framework installation and dependencies.

```bash
e2e doctor
```

**Examples:**
```bash
e2e doctor
```

---

### `deep-scan` - Zero-Config Project Mapping

Automatically detect tech stack and configuration.

```bash
e2e deep-scan [DIRECTORY]
```

**Examples:**
```bash
e2e deep-scan
e2e deep-scan /path/to/project
e2e deep-scan --auto-config
```

---

### `observe` - Auto-Detect Services

Detect running services and ports.

```bash
e2e observe [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--host` | | Host to scan (default: localhost) |
| `--ports` | | Port range (e.g., 8000-9000) |
| `--docker` | | Include Docker containers |

**Examples:**
```bash
e2e observe
e2e observe --host localhost --ports 8000-9000
e2e observe --docker
```

---

### `debug-execution` - Debug Failed Tests

Analyze and debug failed test executions.

```bash
e2e debug-execution [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--project` | `-p` | Project directory |
| `--execution-id` | `-e` | Execution ID (required) |
| `--apply-fix` | | Auto-apply fix |

**Examples:**
```bash
e2e debug-execution -e exec_20240211_120000
e2e debug-execution -e exec_20240211_120000 --apply-fix
```

---

### `analyze-flaky` - Analyze Flaky Tests

Identify patterns causing flaky tests.

```bash
e2e analyze-flaky [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--project` | `-p` | Project directory |
| `--test-file` | `-f` | Test file to analyze (required) |

**Examples:**
```bash
e2e analyze-flaky -f services/users/modules/test_login.py
```

---

### `healing-stats` - Self-Healing Statistics

View statistics about self-healing test fixes.

```bash
e2e healing-stats
```

**Examples:**
```bash
e2e healing-stats
```

---

### `regression` - AI Regression Analysis

Analyze git changes and run affected tests.

```bash
e2e regression [DIRECTORY] [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--base-ref` | `-b` | Base git reference (default: HEAD~1) |
| `--target-ref` | `-t` | Target git reference (default: HEAD) |
| `--run-tests` | | Run affected tests |
| `--no-run-tests` | | Don't run tests |
| `--output` | `-o` | Output report filename |

**Examples:**
```bash
e2e regression
e2e regression --run-tests
e2e regression -b main -t HEAD
```

---

### `semantic-analyze` - Semantic Drift Detection

Detect logic drift between intended behavior and actual behavior.

```bash
e2e semantic-analyze [COMMAND]
```

**Commands:**
- `run` - Run semantic drift analysis
- `intents` - Extract intent baselines
- `server` - Start gRPC server

**Examples:**
```bash
e2e semantic-analyze run
e2e semantic-analyze intents
```

---

## Performance & Security Commands

### `perf-profile` - Performance Profiling

Profile test execution performance.

```bash
e2e perf-profile [DIRECTORY] [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--service` | `-s` | Service name |
| `--output` | `-o` | Output directory |
| `--threshold` | `-t` | Regression threshold % |
| `--compare-baseline` | | Compare with baseline |
| `--set-baseline` | | Set current as baseline |

**Examples:**
```bash
e2e perf-profile
e2e perf-profile -s demo-api
e2e perf-profile --set-baseline
```

---

### `perf-report` - Performance Report

Generate performance analysis report.

```bash
e2e perf-report [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Reports directory |
| `--baseline` | `-b` | Baseline report path |
| `--threshold` | `-t` | Regression threshold |
| `--format` | `-f` | Format: text, json, markdown |

**Examples:**
```bash
e2e perf-report
e2e perf-report -f markdown
```

---

### `security-test` - Security Fuzzing

Run AI-driven security tests.

```bash
e2e security-test [DIRECTORY] [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--service` | `-s` | Service to test |
| `--max-payloads` | `-m` | Max payloads per field |
| `--output` | `-o` | Output report filename |
| `--attack-types` | `-a` | Attack types: sql, nosql, xss, buffer, all |

**Examples:**
```bash
e2e security-test
e2e security-test --service users
e2e security-test --attack-types sql,nosql
```

---

### `red-team` - Adversarial Security Testing

Run adversarial security assessments.

```bash
e2e red-team [COMMAND]
```

**Commands:**
- `assess` - Run full assessment
- `guardrails` - Discover security guardrails
- `logs` - View attack logs
- `payloads` - List attack payloads

**Examples:**
```bash
e2e red-team assess
e2e red-team guardrails
e2e red-team logs
```

---

## Mocking & Recording Commands

### `mock-analyze` - Analyze External Dependencies

Analyze project for external API dependencies.

```bash
e2e mock-analyze [DIRECTORY]
```

**Examples:**
```bash
e2e mock-analyze
```

---

### `mock-generate` - Generate Mock Server

Generate mock server for external APIs.

```bash
e2e mock-generate SERVICE [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--port` | `-p` | Mock server port |
| `--output-dir` | `-o` | Output directory |
| `--docker` | | Generate Docker files |
| `--all` | | Generate all detected mocks |

**Examples:**
```bash
e2e mock-generate stripe
e2e mock-generate stripe --port 9000
e2e mock-generate --all
```

---

### `mock-run` - Run Mock Servers

Start mock servers for testing.

```bash
e2e mock-run [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--services` | `-s` | Comma-separated services |
| `--config` | `-c` | Config file path |
| `--detach` | `-d` | Run in background |
| `--port` | `-p` | Starting port |

**Examples:**
```bash
e2e mock-run
e2e mock-run -s stripe,aws
e2e mock-run -d
```

---

### `mock-validate` - Validate API Contracts

Validate API contract against mock schema.

```bash
e2e mock-validate CONTRACT_FILE [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--service` | `-s` | Service name |
| `--verbose` | `-v` | Verbose output |

**Examples:**
```bash
e2e mock-validate contracts/stripe.json
e2e mock-validate contracts.json -s stripe
```

---

### `recorder` - Record/Replay Sessions

Commands for recording and replaying API sessions.

```bash
e2e recorder [COMMAND]
```

**Commands:**
- `record` - Record new session
- `replay` - Replay session
- `convert` - Convert to test code

**Examples:**
```bash
e2e recorder record
e2e recorder replay
e2e recorder convert session.json
```

---

### `shadow` - Shadow Runner

Capture production traffic and generate tests.

```bash
e2e shadow [COMMAND]
```

**Commands:**
- `capture` - Capture traffic
- `analyze` - Analyze captured traffic
- `generate` - Generate tests from capture
- `replay` - Replay captured traffic
- `export-middleware` - Export middleware

**Examples:**
```bash
e2e shadow capture myapp -u http://localhost:8000
e2e shadow analyze
e2e shadow generate
```

---

## Import & Export Commands

### `import` - Import External Formats

Import tests from external formats.

```bash
e2e import [COMMAND]
```

**Commands:**
- `postman` - Import Postman collection
- `openapi` - Import OpenAPI spec
- `curl` - Import curl command
- `environment` - Import Postman environment

**Examples:**
```bash
e2e import postman collection.json
e2e import openapi swagger.yaml
e2e import curl "curl -X GET http://api.example.com"
```

---

### `gherkin-translate` - Convert Gherkin

Convert Gherkin feature files to test code.

```bash
e2e gherkin-translate [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--project` | `-p` | Project directory |
| `--feature-file` | `-f` | Gherkin file (required) |
| `--output-dir` | `-o` | Output directory |

**Examples:**
```bash
e2e gherkin-translate -f features/login.feature
e2e gherkin-translate -f features/ --output-dir tests/
```

---

### `translate` - Natural Language to Code

Translate natural language to test code.

```bash
e2e translate [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--project` | `-p` | Project directory |
| `--description` | `-d` | Test description (required) |
| `--service` | `-s` | Target service |
| `--language` | `-l` | Language: en, es, fr, de |
| `--output` | `-o` | Output file path |

**Examples:**
```bash
e2e translate -d "Verify user can login"
e2e translate -d "Verificar inicio de sesión" --language es
```

---

## CI/CD & Community Commands

### `setup-ci` - Generate CI/CD Templates

Generate pipeline templates for various platforms.

```bash
e2e setup-ci [PLATFORM] [OPTIONS]
```

**Platforms:** github, gitlab, jenkins, azure, circleci, travis, bitbucket, all

**Options:**
| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing files |

**Examples:**
```bash
e2e setup-ci github
e2e setup-ci all
e2e setup-ci gitlab --force
```

---

### `community` - Community Hub

Community marketplace commands.

```bash
e2e community [COMMAND]
```

**Commands:**
- `templates` - List available templates
- `plugins` - List plugins
- `install-template` - Install a template
- `install-plugin` - Install a plugin
- `publish-template` - Publish template

**Examples:**
```bash
e2e community templates
e2e community plugins
```

---

## Additional Commands

### `install-demo` - Install Demo APIs

Install demo APIs and example services.

```bash
e2e install-demo [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing files |

**Examples:**
```bash
e2e install-demo
e2e install-demo --force
```

---

### `install-extras` - Install Optional Dependencies

Install optional feature packages.

```bash
e2e install-extras [EXTRA] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--list` | List available extras |
| `--all` | Install all extras |

**Available Extras:**
- `tui` - Terminal User Interface
- `rag` - Semantic search and RAG
- `grpc` - gRPC protocol support
- `full` - All optional features

**Examples:**
```bash
e2e install-extras --list
e2e install-extras rag
e2e install-extras tui
e2e install-extras full
```

---

### `telemetry` - Token Usage Monitoring

Monitor LLM token usage and costs.

```bash
e2e telemetry [COMMAND]
```

**Commands:**
- `baseline` - Save current metrics as baseline
- `budget` - Manage token budgets
- `monitor` - Start monitoring
- `report` - View telemetry report

**Examples:**
```bash
e2e telemetry budget status
e2e telemetry baseline
e2e telemetry report
```

---

### `ai-learning` - AI Learning Feedback

AI learning and feedback loop commands.

```bash
e2e ai-learning [COMMAND]
```

**Commands:**
- `feedback` - View collected feedback
- `train` - Train AI model
- `adapt` - Get adaptation suggestions
- `optimize` - Optimize test order

**Examples:**
```bash
e2e ai-learning feedback
e2e ai-learning train
e2e ai-learning optimize
```

---

### `dashboard` - Launch Web Dashboard

Launch interactive web dashboard.

```bash
e2e dashboard [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--port` | | Port number (default: 8501) |
| `--host` | | Host address |
| `--no-browser` | | Don't open browser |

**Examples:**
```bash
e2e dashboard
e2e dashboard --port 8080
e2e dashboard --no-browser
```

---

### `tui` - Launch Terminal Interface

Launch Rich terminal interface.

```bash
e2e tui
```

**Note:** Requires TUI extras: `e2e install-extras tui`

**Examples:**
```bash
e2e tui
```

---

### `set` - Configuration Management

Manage service configuration.

```bash
e2e set [COMMAND]
```

**Commands:**
- `show` - Show current configuration
- `url` - Set service URL

**Examples:**
```bash
e2e set show
e2e set url auth_service http://localhost:8080
```

---

### `lint` - Validate Test Files

Validate test files for common issues.

```bash
e2e lint [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--project` | `-p` | Project directory |
| `--service` | `-s` | Validate specific service |

**Examples:**
```bash
e2e lint
e2e lint --service auth_service
```

---

### `new-service` - Create Service

Create new service with scaffolding.

```bash
e2e new-service NAME [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--base-url` | | Base URL for service |
| `--force` | | Overwrite existing |

**Examples:**
```bash
e2e new-service users-api
e2e new-service payments --base-url http://localhost:8080
```

---

### `new-test` - Create Test Module

Create new test module.

```bash
e2e new-test NAME [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--service` | `-s` | Target service (required) |
| `--module` | `-m` | Module name |

**Examples:**
```bash
e2e new-test login --service users-api
e2e new-test register -s auth-api -m 02_registration
```

---

### `init` - Initialize Project

Initialize new E2E project.

```bash
e2e init [DIRECTORY] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing files |

**Examples:**
```bash
e2e init
e2e init my-project
e2e init --force
```

---

### `run` - Execute Tests

Run E2E tests.

```bash
e2e run [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--service` | `-s` | Run for specific service |
| `--module` | `-m` | Run specific module |
| `--output` | `-o` | Output format: json, html, junit |
| `--report` | | Generate report |
| `--verbose` | `-v` | Verbose output |
| `--parallel` | `-j` | Parallel workers |
| `--debug` | | Debug mode |
| `--trace` | | Enable traceability |

**Examples:**
```bash
e2e run
e2e run --service users-api
e2e run -s auth-api -m 01_login -v
e2e run --report html
```

---

### `config` - Show Configuration

Display current configuration.

```bash
e2e config
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
