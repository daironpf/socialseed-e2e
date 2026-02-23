"""Prometheus/Grafana integration for socialseed-e2e."""

from typing import Any, Dict, List, Optional

from socialseed_e2e.observability import ObservabilityProvider

try:
    from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class PrometheusProvider(ObservabilityProvider):
    """Prometheus observability provider (via Pushgateway)."""

    def __init__(self, gateway_url: str, job_name: str = "socialseed_e2e"):
        if not PROMETHEUS_AVAILABLE:
            raise ImportError("prometheus_client library is required. Install it with 'pip install prometheus_client'")

        self.gateway_url = gateway_url
        self.job_name = job_name
        self.registry = CollectorRegistry()

        # Define some basic gauges
        self.test_duration = Gauge('e2e_test_duration_ms', 'Duration of E2E test in ms',
                                   ['test_name', 'status'], registry=self.registry)
        self.test_status = Gauge('e2e_test_status', 'Status of E2E test (1 for pass, 0 for fail)',
                                 ['test_name'], registry=self.registry)

    def record_test_result(self, test_name: str, status: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """Push test results to Prometheus Pushgateway."""
        self.test_duration.labels(test_name=test_name, status=status).set(duration_ms)

        passed = 1 if status.lower() in ['passed', 'ok', 'success'] else 0
        self.test_status.labels(test_name=test_name).set(passed)

        try:
            push_to_gateway(self.gateway_url, job=self.job_name, registry=self.registry)
        except Exception as e:
            # We don't want to fail the test if observability push fails
            print(f"Warning: Failed to push to Prometheus gateway: {e}")

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric in Prometheus."""
        label_names = list(tags.keys()) if tags else []
        label_values = list(tags.values()) if tags else []

        custom_gauge = Gauge(f"e2e_custom_{name}", f"Custom E2E metric: {name}", label_names, registry=self.registry)
        if label_names:
            custom_gauge.labels(*label_values).set(value)
        else:
            custom_gauge.set(value)

        push_to_gateway(self.gateway_url, job=self.job_name, registry=self.registry)
