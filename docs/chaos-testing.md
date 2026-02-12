# Chaos Engineering for E2E Testing

socialseed-e2e includes native support for Chaos Engineering, allowing you to test the resilience and stability of your system under adverse conditions.

## Key Concepts

Chaos Engineering is the discipline of experimenting on a system in order to build confidence in the system's capability to withstand turbulent conditions in production.

## Network Chaos

Simulate latency, jitter, and connectivity failures at the API client level.

```python
from socialseed_e2e.chaos import NetworkChaos
from my_app.api import UserServiceClient

chaos = NetworkChaos()
# Inject 500ms latency and 10% failure rate
chaos.configure(latency=500, failure_rate=0.1)

# You can use it as a decorator for your API calls
@chaos.inject
def get_user_data(user_id):
    client = UserServiceClient()
    return client.get_profile(user_id)

# Now every call to get_user_data will have injected chaos
try:
    data = get_user_data(123)
except ConnectionError:
    print("Handled the simulated failure!")
```

## Service Chaos (Docker)

If your services are running in Docker, you can simulate service crashes and restarts.

```python
from socialseed_e2e.chaos import ServiceChaos

chaos = ServiceChaos()

# Kill the database service to see how the API handles it
chaos.stop_service("auth-db-1")

# Verify that the system handles the failure (e.g., returns 503 instead of crashing)
# ... test assertions ...

# Bring it back up
chaos.start_service("auth-db-1")
```

## Resource Chaos

Simulate resource exhaustion like memory leaks or high CPU usage.

```python
from socialseed_e2e.chaos import ResourceChaos

chaos = ResourceChaos()

# Limit auth service to 64MB of RAM
chaos.limit_memory("auth-service-1", "64m")

# Limit to 10% of a CPU core
chaos.limit_cpu("auth-service-1", 10)

# Run performance tests to see degradation
# ... performance assertions ...

# Reset limits
chaos.reset_limits("auth-service-1")
```

## Best Practices

1.  **Define Steady State**: Know what "normal" behavior looks like before injecting chaos.
2.  **Hypothesize**: Predict what will happen when you inject a failure (e.g., "The API should retry twice and then return a 503").
3.  **Blast Radius**: Start small. Don't test everything at once.
4.  **Cleanup**: Always ensure your test suite cleans up chaos injections, especially service stops and resource limits.
