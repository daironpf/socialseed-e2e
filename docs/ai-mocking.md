# Automatic AI Mocking for External Third-Party APIs

**Issue #191** - Air-gapped E2E testing without external dependencies

## Overview

The AI Mocking system automatically detects external API calls in your codebase and generates mock servers, enabling E2E testing in completely isolated environments (air-gapped testing). This eliminates the need for:

- Real API keys (Stripe, Google Maps, AWS, etc.)
- Internet connectivity during tests
- External service availability
- Rate limiting concerns

## Features

✅ **Dependency Identification** - Automatically scans code for external HTTP calls
✅ **Mock Server Generation** - Creates FastAPI-based mock servers with realistic responses
✅ **Contract Testing** - Validates requests/responses against expected schemas
✅ **Multiple Languages** - Supports Python, JavaScript/TypeScript, Java, and more
✅ **Pre-configured Services** - Built-in support for 10+ popular APIs
✅ **Docker Support** - Generate Dockerfiles and docker-compose configurations

## Supported Services

The framework includes pre-configured mocks for:

| Service | Auth Type | Endpoints |
|---------|-----------|-----------|
| **Stripe** | Bearer Token | Customers, Charges, Payment Intents |
| **Google Maps** | API Key | Geocoding, Directions, Places |
| **AWS S3** | AWS Signature | Buckets, Objects, List operations |
| **SendGrid** | Bearer Token | Email sending |
| **Twilio** | Basic Auth | SMS, Calls |
| **GitHub** | Bearer Token | Repositories, Issues |
| **Slack** | Bearer Token | Messages, Users |
| **OpenAI** | Bearer Token | Chat completions, Embeddings |
| **PayPal** | OAuth2 | Orders, Payments |

## Quick Start

### 1. Analyze Your Project

Scan your codebase to detect external API dependencies:

```bash
e2e mock-analyze
```

This will:
- Scan all source files for HTTP calls
- Identify known third-party APIs
- Detect environment variables (API keys)
- Show a summary of findings

### 2. Generate Mock Servers

Create FastAPI mock servers for detected services:

```bash
# Generate mock for a specific service
e2e mock-generate stripe

# Generate all detected mocks
e2e mock-generate --all

# Generate with Docker support
e2e mock-generate stripe --docker
```

### 3. Run Mock Servers

Start the mock servers for testing:

```bash
# Run all configured mocks
e2e mock-run

# Run specific services
e2e mock-run -s stripe,google_maps

# Run in background
e2e mock-run -d
```

### 4. Run E2E Tests

Your tests will now use the mock servers instead of real APIs:

```bash
# Set mock URLs in your environment
export STRIPE_BASE_URL=http://localhost:8001
export GOOGLE_MAPS_BASE_URL=http://localhost:8002

# Run your E2E tests
e2e run
```

## CLI Commands

### `e2e mock-analyze`

Analyze project for external API dependencies.

**Options:**
- `--output, -o` - Output file for results (default: `.e2e/external_apis.json`)
- `--format, -f` - Output format: `table` or `json` (default: `table`)

**Examples:**
```bash
e2e mock-analyze                    # Analyze current directory
e2e mock-analyze /path/to/project   # Analyze specific project
e2e mock-analyze -f json            # Output as JSON
```

### `e2e mock-generate`

Generate mock server for an external API.

**Arguments:**
- `service` - Service name (e.g., `stripe`, `google_maps`)

**Options:**
- `--port, -p` - Port for the mock server (default: `8000`)
- `--output-dir, -o` - Output directory (default: `.e2e/mocks`)
- `--docker` - Also generate Dockerfile and docker-compose.yml
- `--all` - Generate mocks for all detected services

**Examples:**
```bash
e2e mock-generate stripe                    # Generate Stripe mock
e2e mock-generate stripe --port 9000       # Custom port
e2e mock-generate --all                     # Generate all mocks
e2e mock-generate stripe --docker          # With Docker support
```

### `e2e mock-run`

Run mock servers for external APIs.

**Options:**
- `--services, -s` - Comma-separated list of services to mock
- `--config, -c` - Path to mock configuration file
- `--detach, -d` - Run in background (detached mode)
- `--port, -p` - Starting port for mock servers (default: `8000`)

**Examples:**
```bash
e2e mock-run                          # Run all configured mocks
e2e mock-run -s stripe,aws            # Run specific mocks
e2e mock-run -d                       # Run in background
e2e mock-run -p 9000                  # Start at port 9000
```

### `e2e mock-validate`

Validate API contract against mock schema.

**Arguments:**
- `contract_file` - Path to contract file (JSON)

**Options:**
- `--service, -s` - Service name for schema lookup
- `--verbose, -v` - Show detailed validation output

**Examples:**
```bash
e2e mock-validate contracts/stripe.json     # Validate contract
e2e mock-validate contracts.json -s stripe  # Specify service
e2e mock-validate contracts.json -v         # Verbose output
```

## Usage Examples

### Example 1: Testing Payment Flow

```python
# Your production code might use Stripe
import requests
import os

def create_payment(amount: int, currency: str = "usd"):
    response = requests.post(
        f"{os.getenv('STRIPE_BASE_URL')}/v1/payment_intents",
        headers={"Authorization": f"Bearer {os.getenv('STRIPE_SECRET_KEY')}"},
        data={"amount": amount, "currency": currency},
    )
    return response.json()

# In your E2E test
def test_payment_flow(payment_api):
    # This will use the mock server
    result = create_payment(amount=2000, currency="usd")

    assert result["status"] == "requires_confirmation"
    assert "client_secret" in result
```

### Example 2: Geocoding Service

```python
# Production code using Google Maps
import requests
import os

def geocode_address(address: str):
    response = requests.get(
        f"{os.getenv('MAPS_BASE_URL')}/maps/api/geocode/json",
        params={"address": address, "key": os.getenv("GOOGLE_MAPS_API_KEY")},
    )
    return response.json()

# E2E test
def test_geocoding(geo_api):
    result = geocode_address("1600 Amphitheatre Parkway")

    assert result["status"] == "OK"
    assert len(result["results"]) > 0
    assert "geometry" in result["results"][0]
```

### Example 3: Contract Validation

Create a contract file to validate your API usage:

```json
{
  "create_customer": {
    "request": {
      "email": "test@example.com",
      "name": "Test Customer"
    },
    "expected_response": {
      "id": "cus_1234567890",
      "object": "customer",
      "email": "test@example.com"
    },
    "schema": {
      "request": {
        "type": "object",
        "properties": {
          "email": {"type": "string", "format": "email"},
          "name": {"type": "string"}
        },
        "required": ["email"]
      },
      "response": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "object": {"type": "string"},
          "email": {"type": "string"}
        }
      }
    }
  }
}
```

Validate it:
```bash
e2e mock-validate contracts/stripe.json -v
```

## Configuration

### Environment Variables

Configure your application to use mock servers:

```bash
# .env.test
STRIPE_BASE_URL=http://localhost:8001
GOOGLE_MAPS_BASE_URL=http://localhost:8002
AWS_S3_BASE_URL=http://localhost:8003

# Use dummy API keys for mocks
STRIPE_SECRET_KEY=sk_test_mock
GOOGLE_MAPS_API_KEY=mock_key
```

### Mock Configuration File

Create `.e2e/mock-config.yml`:

```yaml
services:
  stripe:
    port: 8001
    auth:
      type: bearer
      token: sk_test_mock
    scenarios:
      - name: success
        probability: 0.8
      - name: error
        probability: 0.2
        status_code: 400

  google_maps:
    port: 8002
    auth:
      type: api_key
      key: mock_key
```

## Advanced Usage

### Custom Mock Responses

Override default responses:

```python
from socialseed_e2e.ai_mocking import MockServerGenerator

generator = MockServerGenerator()

custom_responses = {
    "POST /v1/customers": {
        "id": "cus_custom_123",
        "email": "custom@example.com",
        "metadata": {"custom_field": "value"}
    }
}

server = generator.generate_mock_server(
    "stripe",
    port=8001,
    custom_responses=custom_responses
)
```

### Adding Custom Services

Register custom external services:

```python
from socialseed_e2e.ai_mocking import ExternalServiceRegistry, ExternalServiceDefinition, MockEndpoint

registry = ExternalServiceRegistry()

custom_service = ExternalServiceDefinition(
    name="custom_api",
    base_url="https://api.custom.com",
    description="My Custom API",
    auth_type="api_key",
    endpoints=[
        MockEndpoint(
            path="/v1/resource",
            method="GET",
            response_schema={"type": "object"},
            response_example={"id": 1, "name": "Test"}
        )
    ]
)

registry.register_service(custom_service)
```

### Programmatic API Usage

```python
from socialseed_e2e.ai_mocking import (
    ExternalAPIAnalyzer,
    MockServerGenerator,
    ContractValidator,
)

# Analyze project
analyzer = ExternalAPIAnalyzer("/path/to/project")
detected_apis = analyzer.analyze_project()

for service_name, dependency in detected_apis.items():
    print(f"Detected {service_name}: {len(dependency.detected_calls)} calls")

# Generate mock
generator = MockServerGenerator()
server = generator.generate_mock_server("stripe", port=8001)

# Save to file
file_path = generator.save_mock_server(server)
print(f"Mock server saved to: {file_path}")

# Validate contract
validator = ContractValidator()
result = validator.validate_request(
    request_body={"email": "test@example.com"},
    schema={
        "type": "object",
        "properties": {"email": {"type": "string", "format": "email"}},
        "required": ["email"]
    }
)

if result.is_valid:
    print("✅ Contract valid")
else:
    for error in result.errors:
        print(f"❌ {error.field}: {error.message}")
```

## Docker Integration

### Using Docker Compose

Generate Docker files:

```bash
e2e mock-generate stripe --docker
e2e mock-generate google_maps --docker
```

This creates:
- `Dockerfile.stripe`
- `Dockerfile.google_maps`
- `docker-compose.yml`

Run all mocks:

```bash
cd .e2e/mocks
docker-compose up -d
```

### Health Checks

All mock servers include health check endpoints:

```bash
# Check if mock is running
curl http://localhost:8001/__health

# Get captured requests
curl http://localhost:8001/__requests

# Reset mock state
curl -X POST http://localhost:8001/__reset
```

## Best Practices

1. **Use environment variables** for API URLs and keys
2. **Commit mock configurations** to version control
3. **Use contract validation** to ensure API compatibility
4. **Reset mock state** between test runs
5. **Log requests** for debugging

## Troubleshooting

### Mock server not starting

Check port availability:
```bash
e2e mock-run -p 9000  # Use different port
```

### API not detected

Check the analyzer output:
```bash
e2e mock-analyze -v  # Verbose output
```

### Contract validation failing

Review the validation output:
```bash
e2e mock-validate contracts.json -v
```

## Limitations

- Currently supports HTTP/HTTPS APIs only
- WebSocket mocking not yet supported
- Some complex authentication flows may require manual configuration
- Rate limiting simulation is basic

## Future Enhancements

- [ ] WebSocket mocking support
- [ ] GraphQL API mocking
- [ ] Advanced rate limiting simulation
- [ ] Request/response recording and replay
- [ ] Service virtualization with stateful scenarios
