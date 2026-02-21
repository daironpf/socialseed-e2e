# e2e CLI Commands - Complete Reference Guide

## Overview

socialseed-e2e is a comprehensive E2E testing framework for REST APIs with 47+ commands covering testing, AI orchestration, security, analytics, and more.

---

## Core Commands

### `e2e init [DIRECTORY]`
Initialize a new E2E project with scaffolding.

```bash
e2e init myproject           # Basic init
e2e init . --force          # Overwrite existing
e2e init . --demo           # Include demo APIs
```

**Creates:**
- `services/` directory
- `tests/` directory
- `e2e.conf` configuration
- `pyproject.toml`
- `conftest.py` with fixtures

---

### `e2e run`
Execute E2E tests with various options.

```bash
e2e run                                    # Run all tests
e2e run --service auth                    # Specific service
e2e run -s auth -m 01_login              # Specific module
e2e run --url https://api.example.com     # Override URL
e2e run -v                                # Verbose
e2e run --output html                     # HTML report
e2e run --parallel 4                      # Parallel execution
e2e run --trace                          # Enable traceability
e2e run --debug                          # Debug mode
```

---

### `e2e new-service NAME`
Create a new service with scaffolding.

```bash
e2e new-service users-api
e2e new-service auth --base-url http://localhost:8080
e2e new-service payment --health-endpoint /actuator/health
```

**Creates:**
- `services/<name>/`
- `services/<name>/modules/`
- `services/<name>/data_schema.py`
- `services/<name>/service_page.py`
- `services/<name>/config.py`

---

### `e2e new-test NAME -s SERVICE`
Create a new test module.

```bash
e2e new-test login -s auth
e2e new-test create-user -s users -d "Test user creation"
```

---

### `e2e new-demo NAME`
Create a new demo API using the factory system.

```bash
e2e new-demo myapi --port 5016           # Generic CRUD demo
e2e new-demo blog --preset blog         # Blog preset
e2e new-demo tasks --preset task        # Task management preset
```

**Presets:**
- `crud` - Simple CRUD API
- `blog` - Blog with posts and comments
- `task` - Task management with boards

Creates:
- `demos/<name>/api_<name>_demo.py`
- `services/<name>-demo/` with service page, schema, config, tests

---

### `e2e lint`
Validate test files for common issues.

```bash
e2e lint                    # Validate all services
e2e lint --service auth    # Specific service
```

Checks:
- No relative imports
- Proper module structure
- Correct import paths

---

### `e2e doctor`
Verify installation and dependencies.

```bash
e2e doctor
```

Checks:
- Python version
- Playwright installation
- Pydantic version
- Project structure
- Service connectivity

---

### `e2e config`
Show and validate configuration.

```bash
e2e config
```

Displays:
- Configuration file location
- Environment
- Timeout settings
- Configured services

---

### `e2e set url SERVICE URL`
Configure service URLs.

```bash
e2e set url auth http://localhost:8080
e2e set url api https://api.example.com
e2e set show                           # View all services
```

---

## Demo & Installation Commands

### `e2e install-demo`
Install demo APIs.

```bash
e2e install-demo --force    # Overwrite existing
```

**Demos installed:**
- REST API (port 5000)
- Auth/JWT (port 5003)
- gRPC (port 50051)
- WebSocket (port 50052)
- E-commerce (port 5004)
- Chat (port 5005)
- Booking (port 5006)
- Notifications (port 5007)
- File Storage (port 5008)
- Social Graph (port 5009)
- Payments (port 5010)
- Analytics (port 5011)
- ML Serving (port 5012)
- IoT (port 5013)
- SaaS (port 5014)
- Workflows (port 5015)

---

### `e2e install-extras`
Install optional dependencies.

```bash
e2e install-extras              # Interactive
e2e install-extras tui         # Terminal UI
e2e install-extras rag          # Semantic search
e2e install-extras grpc        # gRPC support
e2e install-extras --all       # All extras
e2e install-extras --list      # Show available
```

---

## Discovery & Analysis Commands

### `e2e observe [DIRECTORY]`
Auto-detect running services and ports.

```bash
e2e observe                           # Scan localhost
e2e observe /path/to/project        # Specific project
e2e observe --host 192.168.1.100    # Remote host
e2e observe --ports 8000-9000        # Custom range
e2e observe --auto-setup            # Docker detection
```

---

### `e2e deep-scan [DIRECTORY]`
Zero-config deep scan for automatic project mapping.

```bash
e2e deep-scan                       # Scan current
e2e deep-scan /path/to/project     # Specific project
e2e deep-scan --auto-config        # Auto-generate e2e.conf
```

Detects:
- Tech stack (FastAPI, Flask, Spring, etc.)
- Endpoints
- Environment configuration

---

### `e2e discover [DIRECTORY]`
Generate AI Discovery Report.

```bash
e2e discover                        # Generate report
e2e discover --open                 # Generate and open
```

Creates `DISCOVERY_REPORT.md` with:
- Discovered endpoints
- Technology stack analysis
- Business flows
- Generated test suites

---

## AI Manifest & Search Commands

### `e2e manifest [DIRECTORY]`
Generate AI Project Manifest.

```bash
e2e manifest ../services/auth        # Generate for service
e2e manifest --force               # Force regeneration
```

Generates `project_knowledge.json` for AI context optimization.

---

### `e2e manifest-query [SERVICE]`
Query the AI Project Manifest.

```bash
e2e manifest-query auth            # Query auth service
e2e manifest-query -f markdown     # Output as Markdown
```

---

### `e2e manifest-check [SERVICE]`
Validate manifest freshness.

```bash
e2e manifest-check auth            # Check auth service
```

---

### `e2e search QUERY`
Semantic search on project manifest.

```bash
e2e search "authentication endpoints"
e2e search "user DTO" --type dto
e2e search "payment" --top-k 10
```

---

### `e2e retrieve TASK`
Retrieve context for specific task.

```bash
e2e retrieve "create user tests"
e2e retrieve "test payment flow" --max-chunks 3
```

---

### `e2e build-index [SERVICE]`
Build vector index for semantic search.

```bash
e2e build-index auth              # Build for auth
```

---

### `e2e watch [SERVICE]`
Watch project files and auto-update manifest.

```bash
e2e watch auth                    # Watch auth service
```

---

## Test Generation Commands

### `e2e generate-tests [DIRECTORY]`
Autonomous test suite generation.

```bash
e2e generate-tests                # Generate for project
```

Requires:
- `e2e manifest` to be run first
- Services defined in e2e.conf

---

### `e2e translate`
Translate natural language to test code.

```bash
e2e translate -d "Verify user can login"
e2e translate -d "Comprobar inicio de sesión" --language es
```

---

### `e2e gherkin-translate`
Convert Gherkin to test code.

```bash
e2e gherkin-translate --feature-file features/login.feature
```

---

### `e2e plan-strategy`
Generate AI-driven test strategy.

```bash
e2e plan-strategy --name "API Regression"
e2e plan-strategy --services users-api,orders-api
```

---

### `e2e autonomous-run`
Run tests autonomously with AI.

```bash
e2e autonomous-run --strategy-id abc123
e2e autonomous-run --strategy-id abc123 --auto-fix
```

---

## Recorder & Mock Commands

### `e2e recorder`
Record and replay API sessions.

```bash
e2e recorder record               # Record new session
e2e recorder replay               # Replay session
e2e recorder convert              # Convert to test code
```

---

### `e2e mock-analyze`
Analyze external API dependencies.

```bash
e2e mock-analyze                 # Scan for external APIs
e2e mock-analyze -f json         # JSON output
```

Detects: Stripe, Google Maps, AWS, SendGrid, etc.

---

### `e2e mock-generate SERVICE`
Generate mock server for external API.

```bash
e2e mock-generate stripe
e2e mock-generate stripe --port 9000
e2e mock-generate --all          # Generate all detected
```

---

### `e2e mock-run`
Run mock servers.

```bash
e2e mock-run                     # Run all mocks
e2e mock-run -s stripe,aws      # Specific mocks
```

---

### `e2e mock-validate`
Validate API contracts.

```bash
e2e mock-validate
```

---

## Shadow Runner Commands

### `e2e shadow`
Capture production traffic and auto-generate tests.

```bash
e2e shadow capture               # Capture traffic
e2e shadow generate              # Generate from traffic
e2e shadow replay                # Replay captured
e2e shadow analyze               # Analyze patterns
e2e shadow export-middleware     # Export middleware
```

---

## Security Commands

### `e2e security-test`
AI-driven security fuzzing.

```bash
e2e security-test               # Test all services
e2e security-test --service users # Specific service
e2e security-test --max-payloads 20
```

Tests for:
- SQL Injection
- NoSQL Injection
- XSS
- Command Injection

---

### `e2e red-team`
Adversarial AI security testing.

```bash
e2e red-team assess              # Full assessment
e2e red-team guardrails          # Discover guardrails
e2e red-team logs                # View attack logs
```

---

## Analytics & Performance Commands

### `e2e telemetry`
Token-centric performance monitoring.

```bash
e2e telemetry baseline            # Save baseline
e2e telemetry budget             # Manage budgets
e2e telemetry monitor            # Start monitoring
e2e telemetry report             # View reports
```

---

### `e2e perf-profile`
Performance profiling.

```bash
e2e perf-profile                # Profile tests
```

---

### `e2e perf-report`
Generate performance report.

```bash
e2e perf-report                 # Generate report
```

---

### `e2e regression`
AI Regression Analysis.

```bash
e2e regression                  # Analyze last commit
e2e regression --base-ref main   # Compare to main
e2e regression --run-tests        # Run affected tests
```

---

### `e2e semantic-analyze`
Semantic drift detection.

```bash
e2e semantic-analyze run        # Run analysis
e2e semantic-analyze intents    # Extract intents
e2e semantic-analyze server     # Start gRPC server
```

---

### `e2e analyze-flaky`
Analyze flaky test patterns.

```bash
e2e analyze-flaky --test-file services/auth/test_login.py
```

---

### `e2e debug-execution`
Debug failed tests with AI.

```bash
e2e debug-execution --execution-id exec_123
e2e debug-execution --execution-id exec_123 --apply-fix
```

---

### `e2e healing-stats`
View self-healing statistics.

```bash
e2e healing-stats
```

---

## CI/CD & Integration Commands

### `e2e setup-ci PLATFORM`
Generate CI/CD pipeline templates.

```bash
e2e setup-ci github              # GitHub Actions
e2e setup-ci gitlab              # GitLab CI
e2e setup-ci jenkins             # Jenkins
e2e setup-ci azure               # Azure Pipelines
e2e setup-ci all                 # All platforms
```

---

### `e2e import`
Import external formats.

```bash
e2e import postman collection.json
e2e import openapi spec.yaml
e2e import curl "curl -X GET ..."
e2e import environment env.json
```

---

## UI Commands

### `e2e dashboard`
Launch web dashboard.

```bash
e2e dashboard                    # Open web UI
```

Features:
- Test Explorer
- One-Click Run
- Rich Request/Response Viewer
- Live Logs

---

### `e2e tui`
Launch Terminal UI.

```bash
e2e tui                         # Open TUI
```

Features:
- Keyboard Navigation
- Quick Actions (r, s, f)
- Split View
- Environment Toggling

---

## Community Commands

### `e2e community`
Community Hub and Test Marketplace.

```bash
e2e community list-plugins       # List available plugins
e2e community install-plugin foo  # Install plugin
e2e community list-templates      # List templates
e2e community install-template bar # Install template
```

---

## Additional Commands

### `e2e --version`
Show version.

```bash
e2e --version
# Output: socialseed-e2e, version 0.1.5
```

---

## Command Summary Table

| Command | Category | Description |
|---------|----------|-------------|
| `init` | Core | Initialize project |
| `run` | Core | Execute tests |
| `new-service` | Core | Create service |
| `new-test` | Core | Create test |
| `lint` | Core | Validate tests |
| `doctor` | Core | Verify installation |
| `config` | Core | Show config |
| `set` | Core | Configure services |
| `install-demo` | Installation | Install demos |
| `install-extras` | Installation | Install extras |
| `observe` | Discovery | Auto-detect services |
| `deep-scan` | Discovery | Zero-config mapping |
| `discover` | Discovery | AI discovery report |
| `manifest` | Manifest | Generate manifest |
| `manifest-query` | Manifest | Query manifest |
| `manifest-check` | Manifest | Validate manifest |
| `search` | Search | Semantic search |
| `retrieve` | Search | Get context |
| `build-index` | Search | Build vector index |
| `watch` | Search | Auto-update manifest |
| `generate-tests` | Generation | Auto-generate tests |
| `translate` | Generation | NL to test |
| `gherkin-translate` | Generation | Gherkin to test |
| `plan-strategy` | Generation | AI strategy |
| `autonomous-run` | Generation | AI orchestration |
| `recorder` | Mock | Record/replay |
| `mock-analyze` | Mock | Analyze APIs |
| `mock-generate` | Mock | Generate mocks |
| `mock-run` | Mock | Run mocks |
| `mock-validate` | Mock | Validate contracts |
| `shadow` | Shadow | Traffic capture |
| `security-test` | Security | Security fuzzing |
| `red-team` | Security | Adversarial testing |
| `telemetry` | Analytics | Token monitoring |
| `perf-profile` | Analytics | Performance profiling |
| `perf-report` | Analytics | Performance reports |
| `regression` | Analytics | Regression analysis |
| `semantic-analyze` | Analytics | Drift detection |
| `analyze-flaky` | Analytics | Flakiness analysis |
| `debug-execution` | Analytics | Debug failed tests |
| `healing-stats` | Analytics | Self-healing stats |
| `setup-ci` | CI/CD | Generate pipelines |
| `import` | Import | Import formats |
| `dashboard` | UI | Web dashboard |
| `tui` | UI | Terminal UI |
| `community` | Community | Marketplace |
| `--version` | Utility | Show version |

---

## Notes

- **Prerequisites:** Some commands require `e2e manifest` to be run first
- **AI Features:** Commands marked as AI require external LLM configuration
- **Parallel Execution:** Use `--parallel N` for faster test execution
- **Reports:** Use `--output html` or `--report junit` for CI/CD integration
