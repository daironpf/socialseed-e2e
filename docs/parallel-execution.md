# Parallel Test Execution

This document describes the parallel test execution support in socialseed-e2e, including configuration options, thread safety requirements, and best practices.

## Overview

socialseed-e2e supports running tests in parallel to significantly reduce execution time. The framework uses Python's `multiprocessing` module to achieve true process-level isolation, ensuring that tests don't interfere with each other.

## Features

- **Service-level parallelism**: Run different services' tests in parallel
- **Process isolation**: Each worker runs in a separate process with its own Playwright instance
- **Configurable workers**: Auto-detect CPU count or specify exact number
- **Result aggregation**: Combines results from all workers seamlessly
- **Error handling**: Graceful handling of worker failures

## Quick Start

### Command Line

```bash
# Enable parallel execution with auto-detected workers
$ e2e run --parallel

# Specify exact number of workers
$ e2e run --parallel 4

# Auto-detect workers (same as --parallel)
$ e2e run -j auto

# Disable parallel (sequential execution)
$ e2e run --parallel 0
```

### Configuration File

Add to your `e2e.conf`:

```yaml
general:
  environment: dev

parallel:
  enabled: true
  max_workers: 4  # Auto if not specified
  mode: service   # 'service' or 'test'
  isolation_level: process
```

## Configuration Options

### CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--parallel` | `-j` | Enable parallel execution with N workers (0=disabled) | Sequential |
| `--parallel-mode` | - | Execution mode: `service` or `test` | `service` |

### Configuration File Options

```yaml
parallel:
  enabled: true              # Enable/disable parallel execution
  max_workers: 4            # Number of workers (null = auto)
  mode: service             # Parallelization mode
  isolation_level: process  # State isolation level
```

#### `mode` Options

- **`service`** (default): Run different services in parallel. Each service's tests run sequentially within its worker.
  - Best for: Multiple independent services
  - State sharing: Tests within a service share state

- **`test`**: Run individual test modules in parallel.
  - **Note**: Not yet implemented
  - Best for: Large services with many independent tests
  - State sharing: No shared state between tests

#### `isolation_level` Options

- **`process`** (default): Complete process isolation
  - Each worker is a separate Python process
  - No shared memory
  - Safest option, recommended for most use cases

- **`service`**: Service-level isolation
  - Workers can share some resources
  - Tests within same service share context

- **`none`**: No isolation (not recommended)
  - Workers share all state
  - Use only for debugging

## Thread Safety Requirements

When writing tests for parallel execution, follow these guidelines:

### ✅ DO

1. **Use independent test data**
   ```python
   def run(page):
       # Generate unique data for each test
       unique_email = f"user_{page.test_id}@example.com"
       page.post("/users", json={"email": unique_email})
   ```

2. **Avoid shared mutable state**
   ```python
   # Good - each test creates its own data
   def run(page):
       user = create_unique_user(page)
       test_user_operations(page, user)
   ```

3. **Use proper cleanup**
   ```python
   def run(page):
       user = None
       try:
           user = create_user(page)
           # ... test operations ...
       finally:
           if user:
               cleanup_user(page, user)
   ```

4. **Handle external dependencies carefully**
   ```python
   def run(page):
       # Check if service is available
       if not page.check_health():
           pytest.skip("Service unavailable")
   ```

### ❌ DON'T

1. **Don't share state between tests**
   ```python
   # Bad - global state causes race conditions
   shared_counter = 0

   def run(page):
       global shared_counter
       shared_counter += 1  # Race condition!
   ```

2. **Don't assume test order**
   ```python
   # Bad - relies on specific execution order
   def run_01_create(page):
       page.user_id = create_user(page)

   def run_02_update(page):
       # This may run in different worker!
       update_user(page, page.user_id)
   ```

3. **Don't modify shared resources**
   ```python
   # Bad - multiple tests modifying same resource
   def run(page):
       # All workers try to modify admin user simultaneously
       page.put("/admin/settings", json={"key": "value"})
   ```

4. **Don't use static IDs without checking**
   ```python
   # Bad - assumes user exists
   def run(page):
       page.get("/users/123")  # May not exist in parallel run
   ```

## Best Practices

### 1. Design Tests for Independence

Each test should be able to run independently:

```python
# Good - self-contained test
def run(page):
    # Setup
    user = page.create_test_user()

    # Execute
    response = page.get(f"/users/{user.id}")

    # Verify
    page.assert_ok(response)
    assert response.json()["id"] == user.id

    # Cleanup (optional but recommended)
    page.delete(f"/users/{user.id}")
```

### 2. Use Test Fixtures for Common Setup

Create reusable fixtures that provide isolated resources:

```python
# services/users/modules/conftest.py
import pytest

def create_isolated_user(page, suffix):
    """Create a user unique to this test."""
    return page.post("/users", json={
        "email": f"test_{suffix}@example.com",
        "name": f"Test User {suffix}"
    })

def run(page):
    import uuid
    test_id = str(uuid.uuid4())[:8]
    user = create_isolated_user(page, test_id)
    # ... test logic ...
```

### 3. Handle Rate Limits

When running in parallel, you may hit API rate limits:

```python
# Configure rate limiting in e2e.conf
parallel:
  enabled: true
  max_workers: 4

# In your page class
class UsersPage(BasePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate_limit_config = RateLimitConfig(
            enabled=True,
            requests_per_second=10  # Adjust based on your API
        )
```

### 4. Monitor Resource Usage

Parallel execution increases resource usage:

- **Memory**: Each worker loads its own Python interpreter and Playwright
- **CPU**: Multiple browsers running simultaneously
- **Network**: Concurrent API calls

Adjust workers based on your system:

```bash
# For systems with limited resources
$ e2e run --parallel 2

# For powerful CI/CD runners
$ e2e run --parallel 8
```

## Performance Considerations

### When to Use Parallel Execution

✅ **Good candidates:**
- Multiple independent services
- Tests that don't share data
- Stateless API tests
- Tests with long I/O waits

❌ **Not recommended:**
- Tests with complex shared state
- Single service with few tests
- Tests that modify global configuration
- Tests that can't run concurrently against the API

### Performance Tuning

1. **Optimal worker count**
   ```bash
   # Start with CPU count
   $ e2e run --parallel auto

   # Tune based on results
   $ e2e run --parallel 6  # If 4 is too slow, 8 uses too much memory
   ```

2. **Service grouping**
   ```yaml
   # Group related services to avoid conflicts
   parallel:
     enabled: true
     mode: service
   ```

3. **Resource monitoring**
   ```bash
   # Monitor during test run
   $ e2e run --parallel 4 --verbose
   ```

## Troubleshooting

### Common Issues

#### 1. Tests Failing Only in Parallel

**Symptom**: Tests pass sequentially but fail in parallel

**Cause**: Shared state or resource conflicts

**Solution**:
- Check for global variables
- Ensure tests create unique data
- Verify no hardcoded IDs

#### 2. Memory Errors

**Symptom**: `MemoryError` or system slowdown

**Cause**: Too many workers for available memory

**Solution**:
```bash
# Reduce workers
$ e2e run --parallel 2

# Or disable parallel
$ e2e run --parallel 0
```

#### 3. Port Conflicts

**Symptom**: `Address already in use` errors

**Cause**: Tests trying to bind to same port

**Solution**:
- Use dynamic port allocation
- Ensure tests use different ports
- Check for port leaks in previous runs

#### 4. Database Locks

**Symptom**: Database timeouts or lock errors

**Cause**: Concurrent database access

**Solution**:
- Use separate databases per test
- Implement proper transaction isolation
- Consider test database per worker

### Debugging Parallel Tests

Enable verbose mode to see worker output:

```bash
$ e2e run --parallel 4 --verbose
```

Run specific service in isolation:

```bash
$ e2e run --service users --parallel 0
```

## Examples

### Example 1: Basic Parallel Run

```bash
# Run all services in parallel with 4 workers
$ e2e run --parallel 4

Output:
⚡ Parallel execution enabled
   Workers: 4
   Mode: service

Running tests for service: auth
Running tests for service: users
Running tests for service: orders
Running tests for service: payments

✓ All services passed
```

### Example 2: Configuration File Setup

```yaml
# e2e.conf
general:
  environment: staging
  timeout: 30000

parallel:
  enabled: true
  max_workers: 6
  mode: service
  isolation_level: process

services:
  auth:
    base_url: http://auth-api:8080
  users:
    base_url: http://users-api:8081
  orders:
    base_url: http://orders-api:8082
```

### Example 3: CI/CD Integration

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run E2E Tests
        run: |
          # Use all available CPUs in CI
          e2e run --parallel auto --output html

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: e2e-report
          path: .e2e/reports/
```

### Example 4: Selective Parallelism

```bash
# Run critical services sequentially
$ e2e run --service auth --parallel 0

# Run other services in parallel
$ e2e run --service users --service orders --parallel 4
```

## Migration Guide

### From Sequential to Parallel

1. **Audit your tests** for shared state
2. **Add unique data generation** to each test
3. **Test with 2 workers** initially
4. **Gradually increase** worker count
5. **Monitor for failures**

### Gradual Migration

```python
# Start with parallel disabled for specific services
# e2e.conf
parallel:
  enabled: true
  max_workers: 4

# Tag services that aren't parallel-ready
services:
  legacy-api:
    base_url: http://legacy:8080
    # This service has shared state issues
    # Keep tests sequential for now
```

## API Reference

### ParallelConfig

```python
from socialseed_e2e import ParallelConfig

config = ParallelConfig(
    enabled=True,
    max_workers=4,
    mode="service",
    isolation_level="process"
)
```

### Programmatic Execution

```python
from socialseed_e2e import run_tests_parallel, ParallelConfig

config = ParallelConfig(enabled=True, max_workers=4)
results = run_tests_parallel(
    services_path=Path("services"),
    parallel_config=config,
    verbose=True
)

for service, suite_result in results.items():
    print(f"{service}: {suite_result.passed}/{suite_result.total} passed")
```

## See Also

- [Configuration Guide](configuration.md)
- [CLI Reference](cli-reference.md)
- [Writing Tests](writing-tests.md)
- [Testing Guide](testing-guide.md)
