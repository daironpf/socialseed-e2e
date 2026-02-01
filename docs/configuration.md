# Configuration Reference

Complete guide for configuring socialseed-e2e framework.

## Overview

socialseed-e2e uses a YAML-based configuration file (`e2e.conf`) to define test environments, services, and execution parameters. The configuration supports environment variable substitution, multiple profiles, and flexible service definitions.

## Configuration File Location

The framework searches for configuration files in the following order:

1. **Environment variable**: `E2E_CONFIG_PATH`
2. **Current directory**: `./e2e.conf`
3. **Config subdirectory**: `./config/e2e.conf`
4. **Tests subdirectory**: `./tests/e2e.conf`
5. **Global config**: `~/.config/socialseed-e2e/default.conf`

### Creating a Configuration File

```bash
# Initialize with default configuration
e2e init

# Or create manually in a specific location
e2e init /path/to/project
```

## Configuration Structure

```yaml
general:
  # General settings

services:
  # Service definitions

api_gateway:
  # API Gateway configuration

databases:
  # Database connections

test_data:
  # Test data generation settings

security:
  # Security and SSL configuration

reporting:
  # Test reporting options
```

## General Section

The `general` section defines global settings for the test execution.

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `environment` | string | `dev` | Execution environment (dev, staging, production) |
| `timeout` | integer | `30000` | Global timeout for HTTP requests in milliseconds |
| `user_agent` | string | `SocialSeed-E2E-Agent/2.0` | User agent string for HTTP requests |
| `verbose` | boolean | `true` | Enable verbose logging |
| `project.name` | string | `SocialSeed` | Project name |
| `project.version` | string | `0.0.0` | Project version |
| `verification_level` | string | `strict` | Validation strictness (strict, lenient) |

### Example

```yaml
general:
  environment: staging
  timeout: 45000
  user_agent: "MyApp-E2E-Tests/1.0"
  verbose: true
  project:
    name: "MyApplication"
    version: "1.2.0"
```

## Services Configuration

The `services` section defines all microservices to be tested. Each service has its own configuration block.

### Service Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_url` | string | (required) | Base URL for the service |
| `health_endpoint` | string | `/actuator/health` | Health check endpoint |
| `port` | integer | `8080` | Service port |
| `maven_module` | string | `services/{name}` | Maven module path |
| `timeout` | integer | `30000` | Request timeout (overrides global) |
| `headers` | dictionary | `{}` | Default headers for requests |
| `auto_start` | boolean | `true` | Auto-start service before tests |
| `required` | boolean | `true` | Service is required for tests |
| `endpoints` | dictionary | `{}` | Named endpoint definitions |

### Example: Single Service

```yaml
services:
  users-api:
    base_url: "http://localhost:8080"
    health_endpoint: "/health"
    port: 8080
    timeout: 30000
    headers:
      Content-Type: "application/json"
    auto_start: true
    required: true
    endpoints:
      login: "/api/v1/auth/login"
      register: "/api/v1/auth/register"
      profile: "/api/v1/users/profile"
```

### Example: Multiple Services

```yaml
services:
  auth-service:
    base_url: "http://localhost:8081"
    health_endpoint: "/health"
    port: 8081
    required: true
    endpoints:
      login: "/auth/login"
      logout: "/auth/logout"
      refresh: "/auth/refresh"

  users-service:
    base_url: "http://localhost:8082"
    health_endpoint: "/health"
    port: 8082
    required: true
    endpoints:
      list: "/users"
      detail: "/users/{id}"
      create: "/users"
      update: "/users/{id}"

  posts-service:
    base_url: "http://localhost:8083"
    port: 8083
    required: false
    auto_start: false
    endpoints:
      feed: "/posts/feed"
      create: "/posts"
```

## Environment Variables

socialseed-e2e supports environment variable substitution using the syntax `${VAR_NAME}` or `${VAR_NAME:-default_value}`.

### Basic Substitution

```yaml
general:
  environment: ${ENVIRONMENT}
  timeout: ${TIMEOUT}

services:
  api:
    base_url: ${API_BASE_URL}
```

### Default Values

```yaml
general:
  environment: ${ENVIRONMENT:-dev}
  timeout: ${TIMEOUT:-30000}
  verbose: ${VERBOSE:-true}

services:
  api:
    base_url: ${API_BASE_URL:-http://localhost:8080}
```

### Common Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `E2E_CONFIG_PATH` | Path to configuration file | `/path/to/e2e.conf` |
| `ENVIRONMENT` | Execution environment | `staging`, `production` |
| `API_BASE_URL` | Base URL for services | `http://api.example.com` |
| `TIMEOUT` | Request timeout in ms | `30000` |
| `VERBOSE` | Enable verbose logging | `true`, `false` |

### Setting Environment Variables

**Linux/Mac:**
```bash
export ENVIRONMENT=staging
export API_BASE_URL=https://api.staging.example.com
export TIMEOUT=45000
e2e run
```

**Windows (PowerShell):**
```powershell
$env:ENVIRONMENT = "staging"
$env:API_BASE_URL = "https://api.staging.example.com"
e2e run
```

**Windows (CMD):**
```cmd
set ENVIRONMENT=staging
set API_BASE_URL=https://api.staging.example.com
e2e run
```

## API Gateway Setup

Configure an API Gateway to route requests through a single entry point.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable API Gateway |
| `url` | string | `""` | Gateway base URL |
| `prefix` | string | `""` | URL prefix for services |
| `auth.type` | string | `none` | Authentication type (none, bearer, api_key) |
| `auth.bearer_token` | string | `null` | Bearer token for authentication |
| `auth.api_key_header` | string | `null` | API key header name |
| `auth.api_key_value` | string | `null` | API key value |

### Example: Simple Gateway

```yaml
api_gateway:
  enabled: true
  url: "http://gateway.example.com"
  prefix: "/api/v1"
```

### Example: Gateway with Authentication

```yaml
api_gateway:
  enabled: true
  url: "${GATEWAY_URL}"
  prefix: "/api"
  auth:
    type: bearer
    bearer_token: "${GATEWAY_TOKEN}"

services:
  users:
    base_url: "http://localhost:8080"  # Used as fallback if gateway fails
    required: true
```

### Example: Gateway with API Key

```yaml
api_gateway:
  enabled: true
  url: "https://api.example.com"
  prefix: "/v2"
  auth:
    type: api_key
    api_key_header: "X-API-Key"
    api_key_value: "${API_KEY}"
```

### Service URL Resolution

When API Gateway is enabled, service URLs are resolved as:
```
{gateway_url}{prefix}/{service_name}
```

Example:
- Gateway URL: `http://gateway.example.com`
- Prefix: `/api/v1`
- Service: `users`
- Final URL: `http://gateway.example.com/api/v1/users`

## Database Configuration

Configure database connections for test data validation and setup.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `host` | string | `localhost` | Database host |
| `port` | integer | `5432` | Database port |
| `database` | string | `""` | Database name |
| `username` | string | `""` | Username |
| `password` | string | `""` | Password |
| `enabled` | boolean | `false` | Enable database connection |

### Example: PostgreSQL

```yaml
databases:
  primary:
    host: "localhost"
    port: 5432
    database: "socialseed_test"
    username: "${DB_USER:-testuser}"
    password: "${DB_PASSWORD:-testpass}"
    enabled: true

  analytics:
    host: "${ANALYTICS_DB_HOST:-localhost}"
    port: 5432
    database: "analytics_test"
    username: "${ANALYTICS_DB_USER}"
    password: "${ANALYTICS_DB_PASSWORD}"
    enabled: ${ANALYTICS_ENABLED:-false}
```

## Test Data Configuration

Configure default values for test data generation.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `user.email_domain` | string | `test.socialseed.com` | Domain for test emails |
| `user.password` | string | `StrongPass123!` | Default test password |
| `user.username_prefix` | string | `testuser` | Prefix for test usernames |
| `timing.step_delay` | integer | `100` | Delay between test steps (ms) |
| `timing.async_timeout` | integer | `10000` | Timeout for async operations |
| `retries.max_attempts` | integer | `3` | Maximum retry attempts |
| `retries.backoff_ms` | integer | `1000` | Backoff time between retries |

### Example

```yaml
test_data:
  user:
    email_domain: "test.myapp.com"
    password: "TestPass123!"
    username_prefix: "e2euser"
  
  timing:
    step_delay: 200
    async_timeout: 15000
  
  retries:
    max_attempts: 5
    backoff_ms: 2000
```

## Security Configuration

Configure SSL/TLS and authentication settings.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `verify_ssl` | boolean | `true` | Verify SSL certificates |
| `ssl_cert` | string | `null` | Path to SSL certificate |
| `ssl_key` | string | `null` | Path to SSL private key |
| `ssl_ca` | string | `null` | Path to CA certificate |
| `test_tokens` | dictionary | `{}` | Pre-defined test tokens |

### Example

```yaml
security:
  verify_ssl: true
  ssl_cert: "/path/to/cert.pem"
  ssl_key: "/path/to/key.pem"
  ssl_ca: "/path/to/ca.pem"
  test_tokens:
    admin: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    user: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Disable SSL Verification (Development Only)

```yaml
security:
  verify_ssl: false
```

**⚠️ Warning**: Only disable SSL verification in development environments.

## Reporting Configuration

Configure test reporting and logging options.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `format` | string | `console` | Report format (console, json, html, junit) |
| `save_logs` | boolean | `true` | Save logs to file |
| `log_dir` | string | `./logs` | Directory for log files |
| `include_payloads` | boolean | `false` | Include request/response payloads |
| `screenshot_on_failure` | boolean | `false` | Capture screenshots on failure |

### Example

```yaml
reporting:
  format: "json"
  save_logs: true
  log_dir: "./test-logs"
  include_payloads: true
  screenshot_on_failure: true
```

## Configuration Examples

### Example 1: Development Environment

```yaml
# e2e.conf - Development Configuration
general:
  environment: dev
  timeout: 30000
  user_agent: "MyApp-E2E/dev"
  verbose: true
  project:
    name: "MyApplication"
    version: "1.0.0"

services:
  api:
    base_url: "http://localhost:8080"
    health_endpoint: "/health"
    port: 8080
    auto_start: true
    required: true
    endpoints:
      health: "/health"
      users: "/api/users"
      posts: "/api/posts"

test_data:
  user:
    email_domain: "test.local"
    password: "devpassword123"
```

### Example 2: Staging Environment

```yaml
# e2e.conf - Staging Configuration
general:
  environment: staging
  timeout: 45000
  user_agent: "MyApp-E2E/staging"
  verbose: false
  project:
    name: "MyApplication"
    version: "1.2.0-staging"

api_gateway:
  enabled: true
  url: "${STAGING_GATEWAY_URL}"
  prefix: "/api/v1"
  auth:
    type: bearer
    bearer_token: "${STAGING_TOKEN}"

services:
  auth-service:
    base_url: "${AUTH_SERVICE_URL:-http://localhost:8081}"
    port: 8081
    required: true
    endpoints:
      login: "/auth/login"
      verify: "/auth/verify"

  users-service:
    base_url: "${USERS_SERVICE_URL:-http://localhost:8082}"
    port: 8082
    required: true
    endpoints:
      list: "/users"
      profile: "/users/me"

  posts-service:
    base_url: "${POSTS_SERVICE_URL:-http://localhost:8083}"
    port: 8083
    required: false
    auto_start: false

reporting:
  format: "json"
  save_logs: true
  log_dir: "./staging-logs"
  include_payloads: true
```

### Example 3: Production Environment

```yaml
# e2e.conf - Production (Smoke Tests)
general:
  environment: production
  timeout: 60000
  user_agent: "MyApp-E2E/prod"
  verbose: false
  verification_level: strict

api_gateway:
  enabled: true
  url: "${PROD_GATEWAY_URL}"
  prefix: "/api/v2"
  auth:
    type: api_key
    api_key_header: "X-API-Key"
    api_key_value: "${PROD_API_KEY}"

services:
  api:
    base_url: "${PROD_API_URL}"
    timeout: 60000
    required: true
    auto_start: false
    endpoints:
      health: "/health"
      readiness: "/ready"

security:
  verify_ssl: true
  ssl_ca: "/etc/ssl/certs/ca-bundle.crt"

reporting:
  format: "junit"
  save_logs: true
  log_dir: "/var/log/e2e-tests"
  include_payloads: false
```

### Example 4: Multi-Database Setup

```yaml
# e2e.conf - Multi-Database Configuration
general:
  environment: dev
  timeout: 30000

databases:
  primary:
    host: "localhost"
    port: 5432
    database: "app_test"
    username: "${DB_USER:-postgres}"
    password: "${DB_PASSWORD:-postgres}"
    enabled: true

  cache:
    host: "localhost"
    port: 6379
    database: "0"
    username: ""
    password: ""
    enabled: true

  analytics:
    host: "${ANALYTICS_HOST:-localhost}"
    port: 5432
    database: "analytics_test"
    username: "${ANALYTICS_USER}"
    password: "${ANALYTICS_PASSWORD}"
    enabled: ${ANALYTICS_ENABLED:-false}
```

### Example 5: Microservices with Service Discovery

```yaml
# e2e.conf - Microservices Architecture
general:
  environment: staging
  timeout: 30000

services:
  gateway:
    base_url: "${GATEWAY_URL:-http://localhost:8080}"
    port: 8080
    required: true
    endpoints:
      health: "/actuator/health"
      routes: "/actuator/gateway/routes"

  auth-service:
    base_url: "${AUTH_URL:-http://localhost:8081}"
    port: 8081
    required: true
    endpoints:
      login: "/api/auth/login"
      register: "/api/auth/register"
      oauth: "/api/auth/oauth"

  user-service:
    base_url: "${USER_URL:-http://localhost:8082}"
    port: 8082
    required: true
    endpoints:
      profile: "/api/users/profile"
      settings: "/api/users/settings"
      search: "/api/users/search"

  notification-service:
    base_url: "${NOTIFICATION_URL:-http://localhost:8083}"
    port: 8083
    required: false
    auto_start: false
    endpoints:
      send: "/api/notifications/send"
      history: "/api/notifications/history"

test_data:
  user:
    email_domain: "test.staging.example.com"
    password: "StagingPass123!"
    username_prefix: "staginguser"
  timing:
    step_delay: 150
```

## Advanced Features

### Configuration Validation

The framework validates configuration on load and provides helpful error messages:

```python
from socialseed_e2e import ApiConfigLoader, ConfigError

try:
    config = ApiConfigLoader.load()
except ConfigError as e:
    print(f"Configuration error: {e}")
except FileNotFoundError as e:
    print(f"Configuration file not found: {e}")
```

### Hot Reloading

Reload configuration without restarting:

```python
from socialseed_e2e import ApiConfigLoader

# Initial load
config = ApiConfigLoader.load()

# ... modify e2e.conf file ...

# Reload configuration
config = ApiConfigLoader.reload()
```

### Strict Validation

Enable strict validation for additional warnings:

```python
from socialseed_e2e import ApiConfigLoader

# Load with strict validation
data = {"general": {"environment": "custom"}}
ApiConfigLoader.validate_config(data, strict=True)
```

### Custom Configuration Path

Load configuration from a specific path:

```python
from socialseed_e2e import ApiConfigLoader

# Load specific configuration file
config = ApiConfigLoader.load("/path/to/custom/e2e.conf")
```

Or using environment variable:

```bash
export E2E_CONFIG_PATH=/path/to/custom/e2e.conf
e2e run
```

### Programmatic Configuration Access

```python
from socialseed_e2e import get_config, get_service_config, get_service_url

# Get full configuration
config = get_config()

# Get specific service configuration
auth_config = get_service_config("auth-service")
print(f"Auth service URL: {auth_config.base_url}")

# Get effective URL (with API Gateway support)
url = get_service_url("users-service")
print(f"Users service URL: {url}")

# Check configuration values
if config.verbose:
    print(f"Environment: {config.environment}")
    print(f"Timeout: {config.timeout}ms")
```

### Service Discovery Helpers

```python
from socialseed_e2e import ApiConfigLoader

# Get all required services
required = ApiConfigLoader.get_all_required_services()
print(f"Required services: {required}")

# Get auto-start services
auto_start = ApiConfigLoader.get_auto_start_services()
print(f"Auto-start services: {auto_start}")

# Find service by Maven module
service = ApiConfigLoader.get_service_by_maven_module("services/auth")
if service:
    print(f"Found service: {service.name}")
```

### Environment Variable Precedence

When using `${VAR:-default}` syntax, the resolution order is:

1. Environment variable value
2. Default value from syntax
3. Framework default (if applicable)

Example:
```yaml
general:
  timeout: ${TIMEOUT:-30000}  # Uses TIMEOUT env var, or 30000 if not set
```

### Multiple Configuration Profiles

You can maintain multiple configuration files for different environments:

```
project/
├── e2e.conf              # Default (development)
├── e2e.staging.conf      # Staging
├── e2e.production.conf   # Production
└── config/
    └── e2e.ci.conf       # CI/CD
```

**Switching profiles:**

```bash
# Development (default)
e2e run

# Staging
export E2E_CONFIG_PATH=./e2e.staging.conf
e2e run

# Production
export E2E_CONFIG_PATH=./e2e.production.conf
e2e run
```

### Configuration with Secrets

For sensitive data, use environment variables or external secret management:

```yaml
# e2e.conf
api_gateway:
  auth:
    type: bearer
    bearer_token: "${GATEWAY_TOKEN}"  # Never hardcode tokens!

databases:
  production:
    password: "${DB_PASSWORD}"  # Use env var for passwords
```

**Best practices:**
- Never commit secrets to version control
- Use `.env` files with `python-dotenv` for local development
- Use secret management in CI/CD (GitHub Secrets, etc.)
- Rotate tokens regularly

## Troubleshooting

### Configuration Not Found

**Error:** `FileNotFoundError: Could not find configuration file`

**Solutions:**
1. Run `e2e init` to create default configuration
2. Check that `e2e.conf` exists in one of the search locations
3. Set `E2E_CONFIG_PATH` environment variable
4. Verify file permissions

### Invalid Configuration

**Error:** `ConfigError: Configuration validation failed`

**Common issues:**
- Missing required `general` section
- Service missing `base_url`
- Invalid port number (must be 1-65535)
- Invalid timeout value (must be positive integer)

### Environment Variables Not Substituting

**Check:**
1. Variable syntax: Use `${VAR}` or `${VAR:-default}`
2. Variable is set: `echo $VAR_NAME`
3. No spaces in syntax: `${VAR}` not `${ VAR }`
4. YAML syntax is valid

### API Gateway Not Working

**Check:**
1. `api_gateway.enabled: true`
2. `api_gateway.url` is set
3. Service URLs are relative when using gateway
4. Authentication credentials are correct

## Configuration Reference Summary

```yaml
# Complete configuration example with all options
general:
  environment: dev
  timeout: 30000
  user_agent: "SocialSeed-E2E-Agent/2.0"
  verbose: true
  project:
    name: "SocialSeed"
    version: "1.0.0"
  verification_level: strict

services:
  service-name:
    base_url: "http://localhost:8080"
    health_endpoint: "/actuator/health"
    port: 8080
    maven_module: "services/service-name"
    timeout: 30000
    headers:
      Content-Type: "application/json"
    auto_start: true
    required: true
    endpoints:
      endpoint1: "/api/v1/resource1"
      endpoint2: "/api/v1/resource2"

api_gateway:
  enabled: false
  url: ""
  prefix: ""
  auth:
    type: none
    bearer_token: null
    api_key_header: null
    api_key_value: null

databases:
  db-name:
    host: "localhost"
    port: 5432
    database: ""
    username: ""
    password: ""
    enabled: false

test_data:
  user:
    email_domain: "test.socialseed.com"
    password: "StrongPass123!"
    username_prefix: "testuser"
  timing:
    step_delay: 100
    async_timeout: 10000
  retries:
    max_attempts: 3
    backoff_ms: 1000

security:
  verify_ssl: true
  ssl_cert: null
  ssl_key: null
  ssl_ca: null
  test_tokens: {}

reporting:
  format: console
  save_logs: true
  log_dir: "./logs"
  include_payloads: false
  screenshot_on_failure: false
```

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface documentation
- [Writing Tests](writing-tests.md) - How to write E2E tests
- [Mock API](mock-api.md) - Using the mock API for testing
- [Testing Guide](testing-guide.md) - Pytest configuration and best practices
- [Quick Start](quickstart.md) - Get started in 15 minutes
