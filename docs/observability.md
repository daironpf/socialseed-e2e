# Observability and APM Integration

socialseed-e2e integrates with popular observability and Application Performance Monitoring (APM) tools to provide deep visibility into your E2E test runs.

## Features
- **Test Result Tracking**: Automatically send test status, duration, and metadata to your APM.
- **Distributed Tracing**: Correlate E2E tests with backend traces using Jaeger.
- **Custom Metrics**: Record performance metrics (latency, response size) during test execution.
- **Alerting**: Trigger alerts in your monitoring stack when critical E2E tests fail.

## Supported Providers

### DataDog

```python
from socialseed_e2e.observability.datadog import DataDogProvider

dd_provider = DataDogProvider(api_key="your_api_key")

# The framework will use this to record results
dd_provider.record_test_result("login_test", "passed", 1500)
```

### New Relic

```python
from socialseed_e2e.observability.newrelic import NewRelicProvider

nr_provider = NewRelicProvider(license_key="your_license_key")
nr_provider.record_test_result("checkout_flow", "failed", 5600, {"error": "Timeout"})
```

### Prometheus & Grafana

E2E tests use the **Prometheus Pushgateway** to send metrics.

```python
from socialseed_e2e.observability.prometheus import PrometheusProvider

prom = PrometheusProvider(gateway_url="http://pushgateway:9091")
prom.record_metric("response_latency", 250, {"service": "users-api"})
```

### Jaeger (Distributed Tracing)

```python
from socialseed_e2e.observability.jaeger import JaegerProvider

jaeger = JaegerProvider(service_name="e2e-suite", agent_host="jaeger-collector")

with jaeger.start_span("complex_transaction") as span:
    # Your test logic here
    pass
```

## Using the Observability Manager

You can use multiple providers simultaneously:

```python
from socialseed_e2e.observability import ObservabilityManager
from socialseed_e2e.observability.datadog import DataDogProvider
from socialseed_e2e.observability.newrelic import NewRelicProvider

obs = ObservabilityManager()
obs.add_provider(DataDogProvider(api_key="..."))
obs.add_provider(NewRelicProvider(license_key="..."))

# Record to all providers at once
obs.record_test("integration_test", "passed", 1200)
```

## Installation

Install the required client libraries for your provider:

```bash
pip install datadog          # For DataDog
pip install newrelic         # For New Relic
pip install prometheus_client # For Prometheus
pip install jaeger-client    # For Jaeger
```
