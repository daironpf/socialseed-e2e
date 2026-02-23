# SocialSeed-E2E Architecture Map

**Version:** 1.0
**Date:** 2026-02-23
**Purpose:** Ground Truth for the SocialSeed-E2E Framework

---

## 1. Core Modules (Framework Foundation)

| Module | Primary Responsibility | Dependencies |
|--------|----------------------|--------------|
| `core/base_page.py` | HTTP abstraction with Playwright | playwright |
| `core/base_grpc_page.py` | gRPC testing abstraction | grpcio, grpcio-tools |
| `core/base_graphql_page.py` | GraphQL testing abstraction | requests |
| `core/base_websocket_page.py` | WebSocket testing | websocket-client |
| `core/config_loader.py` | YAML/JSON configuration management | pyyaml, pydantic |
| `core/test_orchestrator.py` | Test discovery and execution | - |
| `core/test_runner.py` | Test execution engine | playwright |
| `core/parallel_runner.py` | Parallel test execution | concurrent.futures |
| `core/interfaces.py` | Protocol definitions (IServicePage, ITestModule) | - |
| `core/models.py` | Core Pydantic models | pydantic |
| `core/traceability/` | Test traceability and reporting | - |

---

## 2. CLI Commands (`commands/`)

| Command | Responsibility | Module |
|---------|---------------|--------|
| `init` | Initialize E2E project | `init_cmd.py` |
| `install-demo` | Install demo APIs | `install_demo_cmd.py` |
| `run` | Execute tests | `run_cmd.py` |
| `manifest` | Generate AI Project Manifest | `manifest_cmd.py` |
| `discover` | Generate AI Discovery Report | `discover_cmd.py` |
| `community` | Templates & plugins marketplace | `community_cmd.py` |
| `security-test` | Security fuzzing | `security_commands.py` |
| `shadow` | Traffic capture & replay | `shadow_cmd.py` |
| `mock` | Mock server management | `mock_cmd.py` |
| `recorder` | Record & replay sessions | `recorder_cmd.py` |

---

## 3. AI & Intelligence (`agents/`)

| Agent | Responsibility | Key Files |
|-------|---------------|-----------|
| `semantic_analyzer/` | Logic drift detection | `logic_drift_detector.py`, `report_generator.py` |
| `red_team_adversary/` | Security testing | `adversarial_prober.py`, `security_logger.py` |
| `resource_optimizer/` | Resource optimization | `resource_agent.py` |

---

## 4. Project Manifest (`project_manifest/`)

| Module | Responsibility |
|--------|---------------|
| `generator.py` | Generate project_knowledge.json |
| `parsers.py` | AST parsers for Python, Java, JS |
| `deep_scanner.py` | Zero-config tech stack detection |
| `vector_store.py` | Embeddings & semantic search |
| `retrieval.py` | RAG retrieval engine |
| `api.py` | Internal API for manifest queries |

---

## 5. Testing & Quality (`ml/`, `analytics/`)

| Module | Responsibility |
|--------|---------------|
| `ml/test_selector.py` | ML-based test selection |
| `ml/flakiness_detector.py` | Detect flaky tests |
| `ml/impact_analyzer.py` | Analyze code change impact |
| `analytics/` | Test analytics and reporting |

---

## 6. Integration Modules

| Module | Responsibility |
|--------|---------------|
| `database/` | SQL/NoSQL testing adapters |
| `chaos/` | Chaos engineering injection |
| `performance/` | Load testing & profiling |
| `contract_testing/` | CDC testing |
| `visual_testing/` | Visual regression testing |

---

## 7. External Integrations

| Module | Responsibility |
|--------|---------------|
| `cloud/aws/`, `cloud/gcp/`, `cloud/azure/` | Cloud platform integrations |
| `ci_cd/` | CI/CD template generation |
| `importers/` | Postman, OpenAPI, curl importers |
| `ide/vscode.py` | VS Code extension support |

---

## 8. Support Modules

| Module | Responsibility |
|--------|---------------|
| `auth/` | Authentication helpers |
| `mocks/` | Mock server infrastructure |
| `recorder/` | Session recording & replay |
| `telemetry/` | Token usage tracking |
| `security/` | Security testing tools |
| `self_healing/` | Auto-healing test failures |

---

## 9. UI & Dashboard

| Module | Responsibility |
|--------|---------------|
| `dashboard/` | Web dashboard (FastAPI + Vue.js) |
| `tui/` | Terminal UI |

---

## Interdependency Graph

```
cli.py (entry point)
  ├── commands/ (all command modules)
  ├── core/ (framework foundation)
  │     ├── base_page.py
  │     ├── config_loader.py
  │     └── test_orchestrator.py
  ├── agents/ (AI capabilities)
  │     ├── semantic_analyzer/
  │     └── red_team_adversary/
  └── project_manifest/ (manifest & discovery)
        ├── generator.py
        ├── parsers.py
        └── deep_scanner.py
```

---

## Key Protocols

### IServicePage
- `get(path, **kwargs)` - GET request
- `post(path, **kwargs)` - POST request
- `put(path, **kwargs)` - PUT request
- `delete(path, **kwargs)` - DELETE request

### ITestModule
- `run(page: IServicePage)` - Main test function
- Returns `APIResponse` from Playwright

---

## Configuration Flow

1. `e2e.conf` (YAML) → `config_loader.py` → `ApiConfigLoader`
2. Services defined with: name, base_url, health_endpoint
3. BasePage uses config to make HTTP requests

---

*This map serves as the single source of truth for understanding the framework's architecture.*
