# Configuration Reference

## Configuration File Structure

The `e2e.conf` file uses YAML format:

```yaml
general:
  environment: dev
  timeout: 30000
  user_agent: "MyApp-E2E/1.0"
  verbose: true

services:
  myservice:
    name: my-service
    base_url: http://localhost:8080
    health_endpoint: /health
    timeout: 5000
    auto_start: false
    required: true
```

## General Section

- `environment`: Environment name (dev, staging, prod)
- `timeout`: Default timeout in milliseconds
- `user_agent`: User agent string for requests
- `verbose`: Enable verbose logging

## Services Section

Each service can have:
- `name`: Service display name
- `base_url`: Base URL for the service
- `health_endpoint`: Health check endpoint
- `timeout`: Service-specific timeout
- `auto_start`: Auto-start service before tests
- `required`: Whether service is required

## Environment Variables

Use environment variable substitution:

```yaml
services:
  myapi:
    base_url: ${API_BASE_URL:-http://localhost:8080}
```

## Multiple Environments

You can have multiple configuration files:
- `e2e.conf` - Default
- `e2e.prod.conf` - Production
- `e2e.staging.conf` - Staging

Use `E2E_CONFIG_PATH` to specify a custom config file.
