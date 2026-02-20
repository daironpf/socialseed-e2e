# Environment Variables Guide

This document lists all environment variables used by the socialseed-e2e framework.

---

## Framework Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_CONFIG_PATH` | `e2e.conf` | Path to configuration file |
| `E2E_ROOT_DIR` | Current directory | Root directory for E2E tests |
| `E2E_SERVICES_PATH` | `services/` | Path to services directory |
| `E2E_ENV` | `dev` | Environment (dev, staging, prod) |
| `E2E_USER_AGENT` | `E2E-Agent/1.0` | User agent for HTTP requests |
| `PROJECT_VERSION` | `unknown` | Project version for telemetry |

---

## Service Configuration (per service)

For each service named `SERVICE_NAME`, you can configure:

| Variable | Example | Description |
|----------|---------|-------------|
| `SERVICE_NAME_BASE_URL` | `http://localhost:8080` | Base URL for the service |
| `SERVICE_NAME_TIMEOUT` | `30000` | Request timeout in ms |
| `SERVICE_NAME_API_KEY` | `sk-xxx` | API key for authentication |
| `SERVICE_NAME_TOKEN` | `Bearer xxx` | Bearer token |

---

## Mock Server

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_MOCK_PORT` | `8765` | Port for mock API server |
| `E2E_MOCK_HOST` | `localhost` | Host for mock API server |

---

## Testing

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_BROWSER` | `chromium` | Browser for UI tests (chromium, firefox, webkit) |
| `E2E_HEADLESS` | `true` | Run browser in headless mode |
| `E2E_SLOWMO` | `0` | Slow down operations by ms |
| `E2E_TIMEOUT` | `30000` | Default test timeout in ms |

---

## Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_VERBOSE` | `false` | Enable verbose logging |
| `E2E_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `E2E_TRACE` | `false` | Enable Playwright trace on failure |

---

## CI/CD

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub token for CI operations |
| `E2E_REPORT_URL` | URL to upload test reports |
| `E2E_SSH_KEY` | SSH key for remote deployments |

---

## Third-party Integrations

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for AI features |
| `ANTHROPIC_API_KEY` | Anthropic API key for AI features |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications |
| `DATADOG_API_KEY` | DataDog API key for APM |
| `DATADOG_APP_KEY` | DataDog app key for APM |

---

## Demo APIs

### REST Demo
| Variable | Default | Description |
|----------|---------|-------------|
| `REST_DEMO_PORT` | `5000` | Port for REST demo API |

### Auth Demo (JWT)
| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_DEMO_PORT` | `5003` | Port for Auth demo API |
| `JWT_SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing key |

### WebSocket Demo
| Variable | Default | Description |
|----------|---------|-------------|
| `WS_DEMO_PORT` | `50052` | Port for WebSocket demo API |

### gRPC Demo
| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_DEMO_PORT` | `50051` | Port for gRPC demo API |

---

## Usage Examples

### Set service URL via environment
```bash
export MY_SERVICE_BASE_URL=https://api.example.com
e2e run --service my-service
```

### Configure mock server port
```bash
export E2E_MOCK_PORT=9000
python -m socialseed_e2e.mock_server
```

### Enable debug logging
```bash
export E2E_VERBOSE=true
export E2E_LOG_LEVEL=DEBUG
e2e run
```
