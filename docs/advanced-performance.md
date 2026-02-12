# Advanced Performance and Load Testing

socialseed-e2e provides a professional-grade load testing engine that goes beyond simple profiling. You can simulate hundreds of concurrent users, define ramp-up patterns, and validate your system against strict SLAs.

## Key Features

- **Concurrent Load Generation**: High-performance asynchronous load generator.
- **Ramp-Up Patterns**: Simulate realistic traffic growth.
- **SLA Validation**: Automatically verify latency and error rate against policies.
- **Visual Reports**: Generate rich HTML dashboards with latency distributions.
- **Integration Ready**: Programmatic API for integration with custom CI/CD pipelines.

## Constant Load Testing

Run a fixed number of concurrent users for a specified duration:

```python
import asyncio
from socialseed_e2e.performance import LoadGenerator, MetricsCollector, PerformanceDashboard

async def my_test_logic():
    # Your API call or interaction here
    pass

async def run_load_test():
    gen = LoadGenerator(target_func=my_test_logic)
    
    # Run 50 concurrent users for 60 seconds
    results = await gen.run_constant_load(users=50, duration_seconds=60)
    
    # Collect metrics
    collector = MetricsCollector(
        latencies=results.latencies,
        total_requests=results.total_requests,
        failed_requests=results.failed_requests
    )
    summary = collector.get_summary()
    print(f"P95 Latency: {summary['p95']}ms")

asyncio.run(run_load_test())
```

## Ramp-Up Traffic

Simulate a system warming up or a peak load event:

```python
# Ramp from 1 to 100 users over 2 minutes, then sustain for 5 minutes
results = await gen.run_ramp_up(
    start_users=1, 
    end_users=100, 
    ramp_duration=120, 
    steady_duration=300
)
```

## SLA Validation

Fail your tests if performance doesn't meet requirements:

```python
from socialseed_e2e.performance import SLAPolicy

policy = SLAPolicy(
    max_avg_latency_ms=200.0,
    p95_latency_ms=500.0,
    max_error_rate=0.01  # Max 1% error rate
)

violations = collector.validate_sla(policy)
if violations:
    for v in violations:
        print(f"SLA Violation: {v}")
```

## Generating Dashboards

Create a visual report for stakeholders:

```python
dashboard = PerformanceDashboard()
report_path = dashboard.generate_html_report(summary, test_name="Checkout API Load Test")
print(f"Report available at: {report_path}")
```

## Best Practices

1.  **Warm-up**: Run a short, light load before your main test to warm up caches and JIT compilers.
2.  **Environment Isolation**: Ensure the target environment is not under external load during tests.
3.  **Resource Monitoring**: Monitor server-side CPU/RAM alongside E2E metrics to identify bottlenecks.
4.  **Gradual Ramp-Up**: Use ramp-up to find the "breaking point" of your application.
