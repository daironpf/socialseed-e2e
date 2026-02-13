# Shadow Runner - Behavior-Driven Test Generation

## Overview

Shadow Runner is a middleware/lightweight proxy that captures real application traffic as users interact with the application, then auto-generates test cases based on actual usage patterns.

## Features

- **Traffic Interception**: Middleware that integrates into any application
- **Request/Response Capture**: Records HTTP/gRPC/WebSocket traffic
- **Intelligent Filtering**: Filters out noise (static assets, health checks)
- **Test Generation**: Converts captured traffic to test modules
- **Privacy Protection**: Anonymizes sensitive data (PII, passwords)
- **Session Replay**: Can replay captured user sessions

## Quick Start

### Basic Usage

```python
from socialseed_e2e.shadow_runner import ShadowRunner

# Initialize shadow runner
shadow = ShadowRunner(output_dir="./captured_tests")

# Start capturing
shadow.start_capturing(user_id="user123")

# User interacts with app normally
# ... API calls happen ...

# Stop capturing
stats = shadow.stop_capturing()
print(f"Captured {stats['final_captured']} requests")

# Generate tests from captured traffic
shadow.generate_tests(service_name="my-api")
```

### Flask Integration

```python
from flask import Flask
from socialseed_e2e.shadow_runner import ShadowRunner
from socialseed_e2e.shadow_runner.traffic_interceptor import FlaskMiddleware

app = Flask(__name__)

# Initialize shadow runner
shadow = ShadowRunner(output_dir="./captured_tests")
shadow.start_capturing()

# Create and register middleware
middleware = FlaskMiddleware(shadow.interceptor)
app.before_request(middleware.before_request)
app.after_request(middleware.after_request)

@app.route('/api/users', methods=['GET'])
def get_users():
    return {'users': []}

if __name__ == '__main__':
    app.run()

    # After shutdown
    shadow.stop_capturing()
    shadow.generate_tests(service_name="users-api")
```

### FastAPI Integration

```python
from fastapi import FastAPI
from socialseed_e2e.shadow_runner import ShadowRunner
from socialseed_e2e.shadow_runner.traffic_interceptor import FastAPIMiddleware

app = FastAPI()

# Initialize shadow runner
shadow = ShadowRunner(output_dir="./captured_tests")
shadow.start_capturing()

# Add middleware
app.add_middleware(FastAPIMiddleware, interceptor=shadow.interceptor)

@app.get("/api/users")
async def get_users():
    return {"users": []}
```

## Configuration

### CaptureConfig

```python
from socialseed_e2e.shadow_runner import CaptureConfig

config = CaptureConfig(
    target_url="http://localhost:8080",
    output_path="./captures",
    filter_health_checks=True,
    filter_static_assets=True,
    sanitize_pii=True,
    max_requests=1000,
    duration=3600,  # seconds
)
```

### TestGenerationConfig

```python
from socialseed_e2e.shadow_runner import TestGenerationConfig

config = TestGenerationConfig(
    service_name="users-api",
    output_dir="services",
    template="standard",
    group_by="endpoint",  # or "session" or "none"
    include_auth_patterns=False,
)
```

## Advanced Usage

### Session Recording

```python
from socialseed_e2e.shadow_runner import ShadowRunner

shadow = ShadowRunner(
    output_dir="./sessions",
    enable_session_tracking=True,
)

# Start session
shadow.start_capturing(
    user_id="user@example.com",
    session_metadata={
        "source": "web",
        "browser": "chrome",
    }
)

# Capture interactions...

# Stop and save
shadow.stop_capturing()
shadow.save_capture("user_session.json")

# Replay session later
results = shadow.replay_session(shadow.current_session_id)
```

### Privacy Sanitization

```python
from socialseed_e2e.shadow_runner import ShadowRunner

shadow = ShadowRunner(
    output_dir="./captures",
    enable_sanitization=True,
)

shadow.start_capturing()

# Captured data will be automatically sanitized
# Emails, passwords, tokens, etc. will be redacted

shadow.stop_capturing()

# Get privacy report
report = shadow.get_privacy_report()
print(f"Sanitized {report.get('sanitized_count', 0)} fields")
```

### Custom Filtering

```python
from socialseed_e2e.shadow_runner import ShadowRunner
from socialseed_e2e.shadow_runner.capture_filter import CaptureFilter, FilterRule

# Create custom filter
filter = CaptureFilter()

# Add custom rule
rule = FilterRule(
    name="exclude_admin",
    description="Exclude admin endpoints",
    path_patterns=[re.compile(r"/admin/.*")],
    action="exclude",
)
filter.add_rule(rule)

# Use with ShadowRunner
shadow = ShadowRunner(
    output_dir="./captures",
    enable_filtering=True,
)
shadow.filter = filter
```

## API Reference

### ShadowRunner

Main class for capturing traffic and generating tests.

#### Constructor

```python
ShadowRunner(
    output_dir: str = "./captured_tests",
    enable_filtering: bool = True,
    enable_sanitization: bool = True,
    enable_session_tracking: bool = True,
)
```

#### Methods

- `start_capturing(user_id=None, session_metadata=None)` - Start capturing traffic
- `stop_capturing()` - Stop capturing and return statistics
- `generate_tests(group_by="endpoint", output_format="service", service_name="captured")` - Generate test files
- `save_capture(filename="capture.json")` - Save captured data to file
- `load_capture(filename="capture.json")` - Load captured data from file
- `get_statistics()` - Get capture statistics
- `get_privacy_report()` - Get privacy sanitization report
- `clear_capture()` - Clear all captured data
- `replay_session(session_id, callback=None)` - Replay a captured session

### TrafficInterceptor

Low-level traffic capture.

```python
from socialseed_e2e.shadow_runner.traffic_interceptor import TrafficInterceptor

interceptor = TrafficInterceptor()
interceptor.start_capturing()

# Capture request
request_id = interceptor.capture_request(
    method="GET",
    url="http://api.example.com/users",
    headers={"Authorization": "Bearer token"},
)

# Capture response
interceptor.capture_response(
    request_id=request_id,
    status_code=200,
    body='{"users": []}',
)

interactions = interceptor.stop_capturing()
```

## Output

Generated tests are saved to the output directory:

```
captured_tests/
├── capture.json              # Raw captured data
├── sessions/                 # Session recordings
│   └── session_xxx.json
└── services/                 # Generated tests
    └── captured/
        ├── __init__.py
        ├── captured_page.py
        ├── data_schema.py
        └── modules/
            ├── 01_get_users.py
            ├── 02_create_user.py
            └── 03_update_user.py
```

## Best Practices

1. **Enable Filtering**: Always enable filtering to avoid capturing noise
2. **Privacy First**: Enable sanitization to protect sensitive data
3. **Session Tracking**: Enable for complex user workflows
4. **Test Review**: Always review generated tests before using in CI/CD
5. **Storage**: Store captures securely and consider retention policies

## Troubleshooting

### No interactions captured

- Ensure `start_capturing()` is called before traffic
- Check that filtering isn't too aggressive
- Verify middleware is registered correctly

### Generated tests fail

- Review captured data for missing authentication
- Check for dynamic data (timestamps, IDs) in assertions
- Update generated tests to handle variable data

### Privacy concerns

- Enable `enable_sanitization=True`
- Review privacy report with `get_privacy_report()`
- Add custom sanitization rules if needed

## Examples

See the `examples/` directory for complete working examples:

- `examples/shadow_runner_basic.py` - Basic usage
- `examples/shadow_runner_flask.py` - Flask integration
- `examples/shadow_runner_fastapi.py` - FastAPI integration
- `examples/shadow_runner_session_replay.py` - Session recording and replay
